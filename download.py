import os
import yt_dlp
from moviepy.editor import VideoFileClip, AudioFileClip

def download_video_and_audio(url):
    try:
        ydl_opts_video = {
            'format': 'bestvideo[height>=1080]/best',
            'outtmpl': 'video.%(ext)s',
            'noplaylist': True,
        }
        ydl_opts_audio = {
            'format': 'bestaudio/best',
            'outtmpl': 'audio.%(ext)s',
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

def combine_video_and_audio():
    try:
        video_file = next((file for file in os.listdir() if file.startswith('video')), None)
        audio_file = next((file for file in os.listdir() if file.startswith('audio')), None)

        if not video_file or not audio_file:
            print("Could not find video or audio file.")
            return

        video_clip = VideoFileClip(video_file)
        audio_clip = AudioFileClip(audio_file)

        output_file = "output.mp4"
        video_clip = video_clip.set_audio(audio_clip)
        video_clip.write_videofile(output_file, codec='libx264')

        print(f"Output file created: {output_file}")

    except Exception as e:
        print(f"An error occurred during combining: {e}")

if __name__ == "__main__":
    video_url = input("Enter the video URL: ")
    download_video_and_audio(video_url)
    combine_video_and_audio()
