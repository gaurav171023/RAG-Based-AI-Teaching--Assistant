# Converts the videos to mp3
import os
import subprocess
import shutil

def find_videos_dir():
    # prefer 'videos' if present
    if os.path.isdir('videos'):
        return 'videos'
    # otherwise pick a directory that looks like it contains sample videos
    for name in os.listdir('.'):
        if os.path.isdir(name) and ('video' in name.lower() or 'videos' in name.lower() or 'webm' in name.lower()):
            return name
    return 'videos'

VIDEOS_DIR = find_videos_dir()
AUDIOS_DIR = 'audios'

os.makedirs(AUDIOS_DIR, exist_ok=True)

if not os.path.isdir(VIDEOS_DIR):
    print(f"Videos directory '{VIDEOS_DIR}' not found. Please create it and add your .webm/.mp4 files.")
    raise SystemExit(1)

if shutil.which('ffmpeg') is None:
    print('ffmpeg not found in PATH. Please install ffmpeg before running this script.')
    raise SystemExit(1)

files = os.listdir(VIDEOS_DIR)
for file in files:
    # best-effort parsing; keep original behavior if format matches
    try:
        tutorial_number = file.split(' [')[0].split(' #')[1]
    except Exception:
        tutorial_number = ''
    file_name = file.split(' ｜ ')[0] if ' ｜ ' in file else os.path.splitext(file)[0]
    out_name = f"{tutorial_number}_{file_name}.mp3" if tutorial_number else f"{file_name}.mp3"
    print('Converting:', file, '->', out_name)
    src = os.path.join(VIDEOS_DIR, file)
    dst = os.path.join(AUDIOS_DIR, out_name)
    subprocess.run(['ffmpeg', '-y', '-i', src, dst])