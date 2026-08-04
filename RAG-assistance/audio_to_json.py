"""
Optional: transcribes every mp3 in audio/ into a timestamped json chunk file
in json/, using Groq's Whisper API (free tier) instead of running Whisper
locally — avoids the memory/CPU cost of local transcription.

You already have json/ populated, so you can SKIP running this file.
It's here so you can explain the full pipeline (video -> audio -> json)
if an interviewer asks how the json chunks were produced.

Requires: GROQ_API_KEY set in .env
"""

import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

AUDIO_DIR = "audio"
JSON_DIR = "json"
os.makedirs(JSON_DIR, exist_ok=True)

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))


def transcribe(audio_path, title, number):
    with open(audio_path, "rb") as f:
        transcript = client.audio.transcriptions.create(
            file=(os.path.basename(audio_path), f.read()),
            model="whisper-large-v3-turbo",
            response_format="verbose_json",
        )

    chunks = []
    for seg in transcript.segments:
        chunks.append({
            "title": title,
            "number": number,
            "start": seg["start"],
            "end": seg["end"],
            "text": seg["text"],
        })
    return chunks


def main():
    for filename in os.listdir(AUDIO_DIR):
        if not filename.lower().endswith(".mp3"):
            continue
        audio_path = os.path.join(AUDIO_DIR, filename)
        title = os.path.splitext(filename)[0]
        number = title.split("_")[0] if "_" in title else "0"

        print(f"Transcribing {filename}...")
        chunks = transcribe(audio_path, title, number)

        out_path = os.path.join(JSON_DIR, os.path.splitext(filename)[0] + ".json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(chunks, f, indent=2)
        print(f"Saved {out_path}")


if __name__ == "__main__":
    main()