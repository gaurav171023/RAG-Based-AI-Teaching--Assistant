import os
import shutil
import requests

ROOT = os.path.dirname(__file__)

def check_ffmpeg():
    return shutil.which("ffmpeg") is not None

def check_folders():
    expected = ["videos", "audios", "jsons"]
    missing = [d for d in expected if not os.path.exists(os.path.join(ROOT, d))]
    return missing

def check_ollama():
    try:
        r = requests.get("http://localhost:11434/health", timeout=1)
        return r.status_code == 200
    except Exception:
        return False

if __name__ == '__main__':
    print("FFmpeg installed:", check_ffmpeg())
    print("Missing folders:", check_folders())
    print("Ollama running on localhost:11434:", check_ollama())
