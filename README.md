# VocalExtract

VocalExtract is a web application designed to separate vocals from instrumental backgrounds in music recordings, with special optimization for complex musical forms like Qawali. It provides an intuitive user interface for uploading audio/video files, processing them to extract vocals, and downloading the processed results.

## Features

- **Upload Interface**: Drag-and-drop or file browser upload for various audio and video formats
- **Format Support**: MP3, WAV, FLAC, OGG, AAC, M4A, MP4, MOV, AVI, MKV, WEBM
- **Visual Feedback**: Progress indicators and processing stage visualization
- **Audio Preview**: Listen to the extracted vocals before downloading
- **Qawali Optimization**: Special processing tailored for the unique characteristics of Qawali music
- **Responsive Design**: Works on desktop and mobile devices

## Technology Stack

- **Backend**: Python + Flask
- **Frontend**: HTML, CSS, JavaScript
- **Audio Processing**: Spleeter (Deezer's audio source separation library)
- **Additional Processing**: FFmpeg for audio conversion and enhancement

## How It Works

VocalExtract uses Spleeter's 5-stem separation model to isolate vocals from other audio components (bass, drums, piano, other). The process involves:

1. **Upload**: The user uploads an audio or video file through the web interface
2. **Preprocessing**: For video files, audio is extracted using FFmpeg
3. **Vocal Separation**: Spleeter processes the audio to separate vocals from instrumental elements
4. **Post-processing**: Additional processing optimizes the vocal output for clarity
5. **Results**: The user can preview and download the isolated vocals

### Qawali-Specific Optimizations

Qawali music presents unique challenges for vocal separation due to:

- Complex vocal harmonies with multiple singers
- Varied vocal techniques and ornamentations
- Rich instrumental accompaniment with frequencies that overlap vocal ranges

Our solution addresses these challenges by:

- Using the 5-stem separation model for more precise isolation
- Applying custom equalization to preserve the unique tonal qualities of Qawali vocals
- Implementing frequency-specific enhancements to maintain vocal nuances

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- FFmpeg installed on your system
- Sufficient disk space for audio processing (at least 2GB recommended)

### Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/vocalextract.git
   cd vocalextract
   ```

2. Create a virtual environment (recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Run the application:
   ```
   python app.py
   ```

5. Open your browser and navigate to:
   ```
   http://localhost:5000
   ```

### Using Docker

You can also run the application using Docker:

1. Build the Docker image:
   ```
   docker build -t vocalextract .
   ```

2. Run the container:
   ```
   docker run -p 5000:5000 vocalextract
   ```

3. Access the application at:
   ```
   http://localhost:5000
   ```

## Deployment

For production deployment, consider:

1. Using Gunicorn as a WSGI server:
   ```
   gunicorn app:app
   ```

2. Setting up a reverse proxy like Nginx

3. Configuring environment variables for production settings

4. Implementing proper storage solutions for uploaded and processed files

## Performance Considerations

- Processing time depends on file size and complexity
- The first separation might take longer as Spleeter loads models
- For production use, consider implementing a task queue system like Celery

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [Spleeter](https://github.com/deezer/spleeter) by Deezer Research
- [Flask](https://flask.palletsprojects.com/)
- [FFmpeg](https://ffmpeg.org/) 