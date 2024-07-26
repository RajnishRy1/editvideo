import cv2
import subprocess
import os

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

    ffmpeg_command = [
        'ffmpeg',
        '-i', video1_path,
        '-i', temp_video2_path,
        '-filter_complex', '[0:v]scale=1080:-1,pad=1080:1920:0:0[bg];[1:v]scale=1080:-1[fg];[bg][fg]overlay=0:H/2',
        '-c:a', 'copy',
        '-c:v', 'libx264',
        '-preset', 'fast',
        '-crf', '18',
        '-t', '00:01:00',
        output_path
    ]

    subprocess.run(ffmpeg_command)
    os.remove(temp_video2_path)

if __name__ == "__main__":
    video1_path = "output_video.avi"
    video2_path = "output.mp4"
    output_path = "combined_video.mp4"

    merge_videos_ffmpeg(video1_path, video2_path, output_path)
    print("Videos merged successfully.")