"""
Optional: extracts audio from every video in videos/ into audio/ as mp3.
You only need this if you add new raw video files later — since you already
have json/ populated, you can skip this and audio_to_json.py entirely.

Requires: pip install moviepy
"""

import os
from moviepy import VideoFileClip

VIDEO_DIR = "videos"
AUDIO_DIR = "audio"

os.makedirs(AUDIO_DIR, exist_ok=True)


def convert_all():
    for filename in os.listdir(VIDEO_DIR):
        if not filename.lower().endswith((".mp4", ".mkv", ".mov")):
            continue
        video_path = os.path.join(VIDEO_DIR, filename)
        audio_path = os.path.join(AUDIO_DIR, os.path.splitext(filename)[0] + ".mp3")
        print(f"Converting {filename} -> {audio_path}")
        clip = VideoFileClip(video_path)
        clip.audio.write_audiofile(audio_path)
        clip.close()


if __name__ == "__main__":
    convert_all()