# RAG-Based-AI Teaching Assistant

Small toolkit to convert course videos to normalized MP3 filenames, run Whisper-based speech‑to‑text/translation, and support retrieval‑augmented workflows. Large media and model artifacts are intentionally excluded from the repository.

## Highlights
- Consistent audio filenames: `<number>_<Title>.mp3` (e.g., `1_Installing VS Code & How Websites Work.mp3`)
- Video → MP3 conversion script (uses ffmpeg)
- Whisper-based transcription/translation scripts (model configurable)
- Minimal, reproducible setup instructions

## Prerequisites
- Windows (PowerShell examples)
- Python 3.8+
- ffmpeg (in PATH)
- pip
- Recommended: create & use a virtual environment
- Optional: Git LFS (if you plan to store large media in the remote)

## Quick start (PowerShell)
1. Clone the repo:
```powershell
git clone https://github.com/gaurav171023/RAG-Based-AI-Teaching--Assistant.git
cd RAG-Based-AI-Teaching--Assistant
```

2. Create and activate a venv:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

3. Install Python deps:
```powershell
pip install -r requirements.txt
# For CPU PyTorch (example)
python -m pip install --index-url https://download.pytorch.org/whl/cpu torch torchvision torchaudio
```

4. Ensure ffmpeg is installed:
```powershell
winget install --id Gyan.FFmpeg -e --source winget
# or choco install ffmpeg -y
```

## Typical usage
- Convert videos in `videos/` to `audios/`:
```powershell
python .\process_videos.py
```
- Transcribe or translate an audio file:
```powershell
python .\stt.py
```
- Inspect other scripts for RAG functionality and usage examples.

## File layout (important files)
- process_videos.py — normalizes names and extracts MP3 using ffmpeg
- stt.py — runs Whisper transcription/translation (model configurable)
- videos/ — input MP4s (not tracked in remote)
- audios/ — generated MP3s (not tracked in remote)
- requirements.txt — Python dependencies

## Media & models (important)
- Large media (mp4/mp3) and model artifacts are excluded from the repo (.gitignore).
- To reproduce results:
  - Place your MP4s in `videos/` and run `process_videos.py`.
  - Use smaller Whisper models (e.g., `base`, `small`) on low‑RAM machines.
- If you want media in the GitHub repo, use Git LFS (tracks large files and avoids GitHub limits).

## Troubleshooting
- "Import 'whisper' could not be resolved": ensure VS Code uses the same Python interpreter where dependencies are installed.
- ffmpeg errors: verify ffmpeg is installed and available in PATH (`ffmpeg -version`).
- Model load OOM: select a smaller Whisper model or run on a machine with more RAM/GPU.
- Pushing large files fails: remove them from commits or enable Git LFS before committing.

## Contributing
- Open issues or PRs for bug reports and enhancements.
- Do not commit large media files directly; use Git LFS or provide download instructions.

## License
- Add a LICENSE file if you have a preferred license. Default: no license in this repo.

## Notes for maintainers
- To show git-ignored files in VS Code Explorer: disable "Explorer: Exclude Git Ignored Files" in settings.
- To add large media safely:
  - Install git-lfs, run `git lfs track "<pattern>"`, commit `.gitattributes`, then add & push media.
