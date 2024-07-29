from flask import Flask, request, send_file, jsonify, send_from_directory
from flask_cors import CORS
import os
import cv2
import yt_dlp
from moviepy.editor import VideoFileClip, AudioFileClip
from werkzeug.utils import secure_filename
import ffmpeg
import subprocess
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from dotenv import load_dotenv
from worker import process_videos

load_dotenv()

# STORAGE_CONNECTION_STRING = os.getenv("STORAGE_CONNECTION_STRING")
# CONTAINER_NAME = os.getenv('CONTAINER_NAME')

# blob_service_client = BlobServiceClient.from_connection_string(STORAGE_CONNECTION_STRING)
# container_client = blob_service_client.get_container_client(CONTAINER_NAME)

app = Flask(__name__)
CORS(app)
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
app.config['TRIMMED_FOLDER'] = os.path.join(os.path.dirname(__file__), 'trimmed')
app.config['DOWNLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'downloads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['TRIMMED_FOLDER'], exist_ok=True)
os.makedirs(app.config['DOWNLOAD_FOLDER'],exist_ok=True)

downloadedVideo = 'output.mp4'
trimmedVideo = 'trimmed.mp4'
croppedVideo = 'cropped.mp4'
finalVideo = 'final.mp4'


def combine_video_and_audio():
    try:
        video_file = next((file for file in os.listdir(app.config['DOWNLOAD_FOLDER']) if file.startswith('video')), None)
        audio_file = next((file for file in os.listdir(app.config['DOWNLOAD_FOLDER']) if file.startswith('audio')), None)

        if not video_file or not audio_file:
            print("Could not find video or audio file.")
            return

        video_file_path = os.path.join(app.config['DOWNLOAD_FOLDER'], video_file)
        audio_file_path = os.path.join(app.config['DOWNLOAD_FOLDER'], audio_file)
        output_file = os.path.join(app.config['DOWNLOAD_FOLDER'], downloadedVideo)

        # ffmpeg command to combine video and audio
        command = [
            'ffmpeg',
            '-i', video_file_path,
            '-i', audio_file_path,
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-strict', 'experimental',
            output_file
        ]

        # Run the ffmpeg command
        subprocess.run(command, check=True)

        print(f"Output file created: {output_file}")

    except subprocess.CalledProcessError as e:
        print(f"An error occurred during combining: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def download_video_and_audio(url):
    try:
        audio_path = os.path.join(app.config['DOWNLOAD_FOLDER'],'audio.webm')
        video_path = os.path.join(app.config['DOWNLOAD_FOLDER'],'video.mp4')
        output_path= os.path.join(app.config['DOWNLOAD_FOLDER'],downloadedVideo)

        if(os.path.exists(video_path)):
            os.remove(video_path)

        if(os.path.exists(audio_path)):
            os.remove(audio_path)

        if(os.path.exists(output_path)):
            os.remove(output_path)

        ydl_opts_video = {
            'format': 'bestvideo[height>=1080]/best',
            'outtmpl': os.path.join(app.config['DOWNLOAD_FOLDER'], 'video.%(ext)s'),
            'noplaylist': True,
        }
        ydl_opts_audio = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(app.config['DOWNLOAD_FOLDER'], 'audio.%(ext)s'),
            'noplaylist': True,
        }

        print("Downloading video...")
        with yt_dlp.YoutubeDL(ydl_opts_video) as ydl:
            ydl.download([url])

        print("Downloading audio...")
        with yt_dlp.YoutubeDL(ydl_opts_audio) as ydl:
            ydl.download([url])

    except Exception as e:
        print(f"An error occurred during download: {e}")

def crop_center_square(frame):
    height, width, _ = frame.shape
    min_dimension = min(width, height)
    
    start_x = (width - min_dimension) // 2
    start_y = (height - min_dimension) // 2
    
    cropped_frame = frame[start_y:start_y + min_dimension, start_x:start_x + min_dimension]
    return cropped_frame

def crop_video_to_square(input_path, output_path):
    cap = cv2.VideoCapture(input_path)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    min_dimension = min(width, height)

    out = cv2.VideoWriter(output_path, fourcc, fps, (min_dimension, min_dimension))

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        cropped_frame = crop_center_square(frame)
        out.write(cropped_frame)

    cap.release()
    out.release()

def merge_videos_ffmpeg(video1_path, video2_path, output_path):
    temp_video2_path = "temp_cropped_video.mp4"
    crop_video_to_square(video2_path, temp_video2_path)
    combined_path = os.path.join(app.config['DOWNLOAD_FOLDER'], finalVideo)
    if os.path.exists(combined_path):
        os.remove(combined_path)
    
    process_videos(video1_path=video1_path,temp_video2_path=temp_video2_path,output_path=output_path)
    # ffmpeg_command = [
    #     'ffmpeg',
    #     '-i', video1_path,
    #     '-i', temp_video2_path,
    #     '-filter_complex', '[0:v]scale=1080:-1,pad=1080:1920:0:0[bg];[1:v]scale=1080:-1[fg];[bg][fg]overlay=0:H/2',
    #     '-c:a', 'copy',
    #     '-c:v', 'libx264',
    #     '-preset', 'fast',
    #     '-crf', '18',
    #     '-t', '00:01:00',
    #     output_path
    # ]

    # ffmpeg_command = [
    #     'ffmpeg',
    #     '-i', video1_path,
    #     '-i', temp_video2_path,
    #     '-filter_complex', (
    #         '[0:v]scale=1080:-2[upper];'
    #         '[1:v]scale=1080:-2[lower];'
    #         'color=s=1080x1920:c=black[bg];'
    #         '[bg][upper]overlay=shortest=1:y=0[bg+upper];'
    #         '[bg+upper][lower]overlay=shortest=1:y=960'
    #     ),
    #     '-c:a', 'copy',
    #     '-c:v', 'libx264',
    #     '-preset', 'fast',
    #     '-crf', '18',
    #     '-t', '00:01:00',
    #     output_path
    # ]
    # subprocess.run(ffmpeg_command)
    # os.remove(temp_video2_path)

@app.route('/downloadmerged/<filename>')
def download_merged(filename):
    filepath = os.path.join(app.config['DOWNLOAD_FOLDER'], filename)
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True, mimetype='video/mp4')
    else:
        return "File not found", 404

@app.route('/merge', methods=['POST'])
def merge_videos():
    video1_path = os.path.join(app.config['UPLOAD_FOLDER'], croppedVideo)
    video2_path = os.path.join(app.config['TRIMMED_FOLDER'], trimmedVideo)
    output_path = os.path.join(app.config['DOWNLOAD_FOLDER'], finalVideo)
    merge_videos_ffmpeg(video1_path, video2_path, output_path)
    return jsonify({"message": "videos merged successfully"}), 200

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['DOWNLOAD_FOLDER'], filename)

@app.route('/download', methods=['POST'])
def download():
    data = request.json
    yt_url = data.get('ytUrl')
    if yt_url:
        try:
            download_video_and_audio(yt_url)  # You need to implement this function
            combine_video_and_audio()        # You need to implement this function
            return jsonify({"message": "Download and combination initiated successfully"}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": "Invalid input"}), 400

@app.route('/downloadblob/<filename>')
def download_src(filename):
    filepath = os.path.join(app.config['DOWNLOAD_FOLDER'], filename)
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True, mimetype='video/mp4')
    else:
        return "File not found", 404

@app.route('/trimmedblob/<filename>')
def donwload_trimmed(filename):
    filepath = os.path.join(app.config['TRIMMED_FOLDER'], filename)
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True, mimetype='video/mp4')
    else:
        return "File not found", 404    

@app.route('/upload', methods=['POST'])
def upload_video():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file:
        filename = file.filename
        # filepath = os.path.join(UPLOAD_FOLDER, filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return jsonify({"filename": filename, "filepath": filepath}), 200

@app.route('/crop', methods=['POST'])
def crop_video():
    data = request.json
    input_path = data['filepath']
    x = data['x']
    y = data['y']
    width = data['width']
    height = data['height']

    # Verify if the file exists
    if not os.path.exists(input_path):
        return jsonify({'error': 'File not found'}), 404

    output_path = os.path.join(app.config['UPLOAD_FOLDER'], croppedVideo)

    try:
        # Use ffmpeg to crop the video and retain audio
        video = ffmpeg.input(input_path)
        audio = ffmpeg.input(input_path).audio
        video = ffmpeg.crop(video, x, y, width, height)
        ffmpeg.output(video, audio, output_path, vcodec='libx264', acodec='aac', strict='experimental').run(overwrite_output=True)
    except ffmpeg.Error as e:
        return jsonify({'error': str(e)}), 500
    

    return send_file(output_path, as_attachment=True,mimetype='video/mp4')

@app.route('/uploadtrim', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if file:
        filename = file.filename
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return jsonify({"filepath": filepath}), 200

@app.route('/trim', methods=['POST'])
def trim_video():
    data = request.json
    filepath = os.path.join(app.config['DOWNLOAD_FOLDER'], downloadedVideo)
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    if not filepath or not start_time or not end_time:
        return jsonify({"error": "Missing data"}), 400
    filename = os.path.basename(filepath)
    trimmed_path = os.path.join(app.config['TRIMMED_FOLDER'], trimmedVideo)
    # Check if the trimmed file already exists and remove it
    if os.path.exists(trimmed_path):
        os.remove(trimmed_path)
    (
        ffmpeg
        .input(filepath, ss=start_time, to=end_time)
        .output(trimmed_path, codec='copy')
        .run(overwrite_output=True)
    )
    return jsonify({"trimmed_path":trimmedVideo}), 200

@app.route('/trimmed/<filename>', methods=['GET'])
def get_trimmed_video(filename):
    return send_from_directory(app.config['TRIMMED_FOLDER'], filename)  


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)