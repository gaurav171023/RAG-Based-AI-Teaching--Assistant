import json
import os
import sys
import subprocess
import importlib

def ensure_whisper():
    try:
        import whisper  # type: ignore[reportMissingImports]
        return whisper
    except Exception:
        print("'whisper' not found. Attempting to install 'openai-whisper' via pip...")
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'openai-whisper'], check=True)
            # try to also install torch as a best-effort (may fail depending on platform)
            try:
                subprocess.run([sys.executable, '-m', 'pip', 'install', 'torch'], check=True)
            except Exception:
                print("Warning: automatic install of 'torch' failed or is not required; if model loading fails, please install torch manually following https://pytorch.org/")
            # invalidate caches and try to import again
            importlib.invalidate_caches()
            try:
                import whisper  # type: ignore[reportMissingImports]
                return whisper
            except Exception:
                # try alternate installs
                print("Import still failing after installing 'openai-whisper'. Trying alternate install methods...")
                try:
                    subprocess.run([sys.executable, '-m', 'pip', 'install', 'whisper'], check=True)
                except Exception:
                    pass
                try:
                    subprocess.run([sys.executable, '-m', 'pip', 'install', 'git+https://github.com/openai/whisper.git'], check=True)
                except Exception:
                    pass
                importlib.invalidate_caches()
                try:
                    import whisper  # type: ignore[reportMissingImports]
                    return whisper
                except Exception as e:
                    print("Automatic installation of 'openai-whisper' failed to make module importable:", e)
                    print("Please install manually (recommended): pip install openai-whisper")
                    return None
        except Exception as e:
            print("Automatic installation of 'openai-whisper' failed:", e)
            print("Please install manually: pip install openai-whisper")
            return None

whisper = ensure_whisper()
if whisper is not None:
    model = whisper.load_model("large-v2")

AUDIOS_DIR = "audios"
def find_audio_dir():
    # prefer 'audios' if present
    if os.path.isdir(AUDIOS_DIR):
        return AUDIOS_DIR
    # otherwise look for folders that contain 'audio' or 'audios' or 'all_audios'
    for name in os.listdir('.'):
        if os.path.isdir(name) and ('audio' in name.lower() or 'audios' in name.lower()):
            return name
    # fallback to current directory
    return AUDIOS_DIR

AUDIOS_DIR = find_audio_dir()
JSONS_DIR = "jsons"
os.makedirs(JSONS_DIR, exist_ok=True)

if whisper is None:
    print("Warning: 'whisper' package is not installed. Skipping mp3->json conversion. Install with: pip install openai-whisper")
    audios = []
else:
    audios = os.listdir(AUDIOS_DIR)

for audio in audios:
    if ("_" in audio):
        number = audio.split("_")[0]
        title = audio.split("_")[1][:-4]
        print(number, title)
        result = model.transcribe(audio=os.path.join(AUDIOS_DIR, audio),
                                 language="hi",
                                 task="translate",
                                 word_timestamps=False)

        chunks = []
        for segment in result["segments"]:
            chunks.append({"number": number, "title": title, "start": segment["start"], "end": segment["end"], "text": segment["text"]})

        chunks_with_metadata = {"chunks": chunks, "text": result["text"]}

        with open(os.path.join(JSONS_DIR, f"{audio}.json"), "w", encoding="utf-8") as f:
            json.dump(chunks_with_metadata, f, ensure_ascii=False)