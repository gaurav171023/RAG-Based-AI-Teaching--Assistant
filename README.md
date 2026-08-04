# Video RAG Teaching Assistant

## Overview

Video RAG Teaching Assistant is a Retrieval-Augmented Generation (RAG) application designed to help users ask questions about a video-based course and receive grounded answers with relevant timestamps. The system uses semantic search over transcript chunks and generates responses with the help of Groq Llama 3.1, making it well-suited for interactive learning and course navigation.

## Features

- Video-to-audio conversion using MoviePy and FFmpeg
- Speech-to-text transcription with Whisper
- Transcript preprocessing and chunking
- SentenceTransformer embeddings using all-MiniLM-L6-v2
- Cosine similarity-based retrieval
- Retrieval-Augmented Generation (RAG)
- Groq Llama 3.1 API integration
- FastAPI backend for API serving
- Timestamp-based answer navigation
- Simple browser-based web interface

## Project Architecture

The application follows this end-to-end pipeline:

Videos
↓
MoviePy + FFmpeg
↓
Whisper Transcription
↓
JSON Transcript Chunks
↓
Sentence Transformers
↓
Embeddings
↓
Cosine Similarity Search
↓
Groq Llama 3.1
↓
FastAPI
↓
Browser

## Folder Structure

```text
RAG-Project/
├── .gitignore
├── README.md
└── RAG-assistance/
    ├── app.py
    ├── audio_to_json.py
    ├── embeddings.joblib
    ├── preprocess_json.py
    ├── rag_engine.py
    ├── requirements.txt
    ├── video_to_mp3.py
    ├── audio/
    ├── json/
    ├── static/
    └── videos/
```

## Installation

1. Create a virtual environment:

```bash
python -m venv venv
```

2. Activate it:

Windows:

```bash
venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create your environment file:

```bash
copy .env.example .env
```

5. Add your Groq API key to the `.env` file:

```env
GROQ_API_KEY=your_api_key
```

6. Generate the processed transcript data:

```bash
python preprocess_json.py
```

7. Start the application:

```bash
python app.py
```

## Usage

Open the web interface in your browser and ask questions about the course content. The assistant searches the transcript for the most relevant sections, retrieves supporting context, and returns an answer grounded in the video material, including relevant timestamps so you can jump directly to the source content.

## Tech Stack

- Python
- FastAPI
- Sentence Transformers
- Groq API
- MoviePy
- FFmpeg
- Whisper
- Scikit-learn
- Pandas
- Joblib

## Future Improvements

Potential enhancements for this project include:

- FAISS or Chroma vector database integration
- Streaming responses for a more interactive experience
- Improved ranking and retrieval quality
- Authentication and user management
- Docker deployment
- Cloud deployment

## License

This project is licensed under the MIT License.
