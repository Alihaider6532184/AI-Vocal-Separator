import os
import uuid
import time
from flask import Flask, render_template, request, jsonify, send_from_directory, url_for
from werkzeug.utils import secure_filename
import subprocess
import threading
import json
from concurrent.futures import ThreadPoolExecutor

# Initialize the Flask app
app = Flask(__name__, 
            static_folder="app/static",
            template_folder="app/templates")

# Configuration
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'app', 'uploads')
app.config['PROCESSED_FOLDER'] = os.path.join(os.getcwd(), 'app', 'processed')
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500 MB max upload size
app.config['ALLOWED_AUDIO_EXTENSIONS'] = {'mp3', 'wav', 'flac', 'ogg', 'aac', 'm4a'}
app.config['ALLOWED_VIDEO_EXTENSIONS'] = {'mp4', 'mov', 'avi', 'mkv', 'webm'}

# Ensure upload and processed directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)

# Global job tracking
processing_jobs = {}
executor = ThreadPoolExecutor(max_workers=2)  # Adjust based on server capabilities

def allowed_file(filename):
    """Check if the file extension is allowed"""
    audio_ext = app.config['ALLOWED_AUDIO_EXTENSIONS']
    video_ext = app.config['ALLOWED_VIDEO_EXTENSIONS']
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in (audio_ext | video_ext)

def get_file_type(filename):
    """Determine if file is audio or video based on extension"""
    ext = filename.rsplit('.', 1)[1].lower()
    if ext in app.config['ALLOWED_AUDIO_EXTENSIONS']:
        return 'audio'
    elif ext in app.config['ALLOWED_VIDEO_EXTENSIONS']:
        return 'video'
    return None

def process_file(job_id, input_path, output_dir):
    """Process the uploaded file to extract vocals using Spleeter"""
    try:
        # Update job status
        processing_jobs[job_id]['status'] = 'processing'
        processing_jobs[job_id]['progress'] = 10
        
        # Get file information
        filename = os.path.basename(input_path)
        file_type = get_file_type(filename)
        base_name = os.path.splitext(filename)[0]
        
        # If it's a video, extract the audio first
        audio_path = input_path
        if file_type == 'video':
            processing_jobs[job_id]['status'] = 'extracting_audio'
            audio_path = os.path.join(output_dir, f"{base_name}.wav")
            ffmpeg_cmd = [
                'ffmpeg', '-i', input_path, 
                '-vn', '-acodec', 'pcm_s16le', 
                '-ar', '44100', '-ac', '2', audio_path
            ]
            subprocess.run(ffmpeg_cmd, check=True)
            processing_jobs[job_id]['progress'] = 30
        
        # Run Spleeter separation
        processing_jobs[job_id]['status'] = 'separating'
        output_path = os.path.join(output_dir, base_name)
        os.makedirs(output_path, exist_ok=True)
        
        # Using 5-stem separation for better vocal isolation, especially for Qawali
        spleeter_cmd = [
            'spleeter', 'separate', 
            '-p', 'spleeter:5stems', 
            '-o', output_dir,
            audio_path
        ]
        subprocess.run(spleeter_cmd, check=True)
        processing_jobs[job_id]['progress'] = 80
        
        # Get the isolated vocals path
        vocals_path = os.path.join(output_dir, base_name, 'vocals.wav')
        
        # Post-processing for Qawali optimization
        # For Qawali, we might need to enhance vocals and reduce residual instrumental sounds
        processing_jobs[job_id]['status'] = 'post_processing'
        enhanced_vocals_path = os.path.join(output_dir, f"{base_name}_vocals.mp3")
        
        # Example post-processing: convert to MP3 with slight EQ adjustments for vocal clarity
        ffmpeg_pp_cmd = [
            'ffmpeg', '-i', vocals_path,
            '-af', 'equalizer=f=200:width_type=o:width=2:g=-2,equalizer=f=3000:width_type=o:width=1:g=3,loudnorm',
            '-codec:a', 'libmp3lame', '-q:a', '2',
            enhanced_vocals_path
        ]
        subprocess.run(ffmpeg_pp_cmd, check=True)
        
        # Update job status to completed
        processing_jobs[job_id]['status'] = 'completed'
        processing_jobs[job_id]['progress'] = 100
        processing_jobs[job_id]['result_path'] = os.path.basename(enhanced_vocals_path)
        
        # Clean up temporary files
        if file_type == 'video' and os.path.exists(audio_path):
            os.remove(audio_path)
            
    except Exception as e:
        # Handle errors
        processing_jobs[job_id]['status'] = 'error'
        processing_jobs[job_id]['error'] = str(e)
        print(f"Error processing {input_path}: {e}")

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and start processing"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        # Create a unique job ID and secure filename
        job_id = str(uuid.uuid4())
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{job_id}_{filename}")
        
        # Save the uploaded file
        file.save(file_path)
        
        # Create a job record
        processing_jobs[job_id] = {
            'id': job_id,
            'filename': filename,
            'status': 'uploaded',
            'progress': 0,
            'created_at': time.time(),
            'input_path': file_path
        }
        
        # Start processing in a background thread
        executor.submit(
            process_file, 
            job_id, 
            file_path, 
            app.config['PROCESSED_FOLDER']
        )
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'message': 'File uploaded successfully and processing started'
        })
    
    return jsonify({'error': 'File type not allowed'}), 400

@app.route('/status/<job_id>', methods=['GET'])
def job_status(job_id):
    """Get the status of a processing job"""
    if job_id not in processing_jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    job = processing_jobs[job_id]
    response = {
        'id': job['id'],
        'status': job['status'],
        'progress': job['progress'],
        'filename': job['filename']
    }
    
    if job['status'] == 'completed' and 'result_path' in job:
        response['result_url'] = url_for('download_file', filename=job['result_path'])
        
    if job['status'] == 'error' and 'error' in job:
        response['error'] = job['error']
        
    return jsonify(response)

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    """Download a processed file"""
    return send_from_directory(app.config['PROCESSED_FOLDER'], filename)

@app.route('/preview/<job_id>', methods=['GET'])
def preview_file(job_id):
    """Preview a processed file"""
    if job_id not in processing_jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    job = processing_jobs[job_id]
    if job['status'] != 'completed' or 'result_path' not in job:
        return jsonify({'error': 'Processing not completed'}), 400
    
    # Return HTML with audio player
    return render_template('preview.html', job=job)

if __name__ == '__main__':
    app.run(debug=True) 