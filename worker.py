import subprocess
import os

def process_videos(video1_path, temp_video2_path, output_path):
    ffmpeg_command = [
        'ffmpeg',
        '-i', video1_path,
        '-i', temp_video2_path,
        '-filter_complex', (
            '[0:v]scale=1080:-2[upper];'
            '[1:v]scale=1080:-2[lower];'
            'color=s=1080x1920:c=black[bg];'
            '[bg][upper]overlay=shortest=1:y=0[bg+upper];'
            '[bg+upper][lower]overlay=shortest=1:y=960'
        ),
        '-c:a', 'copy',
        '-c:v', 'libx264',
        '-preset', 'fast',
        '-crf', '18',
        '-t', '00:01:00',
        output_path
    ]
    subprocess.run(ffmpeg_command)
    os.remove(temp_video2_path)