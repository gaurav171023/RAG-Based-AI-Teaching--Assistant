from flask import Flask, render_template, request, jsonify
import joblib
import os
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
import requests
import time
import importlib.util

HAS_GDOWN = importlib.util.find_spec('gdown') is not None



def _download_if_missing(path, url, max_retries=3):
    """Download a file from url to path if it doesn't exist with retry logic."""
    if os.path.exists(path) or not url:
        return
    
    print(f"Downloading {os.path.basename(path)} from {url}...")
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    
    for attempt in range(max_retries):
        try:
            # Extract file_id for Google Drive URLs
            file_id = None
            if 'drive.google.com' in url:
                if '&id=' in url:
                    file_id = url.split('&id=')[1].split('&')[0]
                elif '/d/' in url:
                    file_id = url.split('/d/')[1].split('/')[0]
            
            # Try gdown first for Google Drive URLs (more reliable)
            if HAS_GDOWN and file_id:
                print(f"Attempt {attempt + 1}/{max_retries}: Using gdown for file {file_id}...")
                try:
                    gdown_module = importlib.import_module('gdown')
                    # gdown.download returns the path if successful
                    result = gdown_module.download(f"https://drive.google.com/uc?id={file_id}", path, quiet=False)
                    if result and os.path.exists(path):
                        size_mb = os.path.getsize(path) / (1024 * 1024)
                        print(f"✓ Download complete: {os.path.basename(path)} ({size_mb:.1f}MB)")
                        return
                except Exception as gdown_err:
                    print(f"  gdown failed: {gdown_err}, falling back to manual download...")
            
            # Fallback to manual Google Drive download
            if file_id:
                _download_from_google_drive(file_id, path)
                if os.path.exists(path):
                    size_mb = os.path.getsize(path) / (1024 * 1024)
                    print(f"✓ Download complete: {os.path.basename(path)} ({size_mb:.1f}MB)")
                    return
            else:
                # Standard HTTP download for non-Google Drive URLs
                print(f"Attempt {attempt + 1}/{max_retries}: Direct HTTP download...")
                session = requests.Session()
                session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
                resp = session.get(url, stream=True, timeout=120, allow_redirects=True, verify=False)
                resp.raise_for_status()
                
                total_size = int(resp.headers.get('content-length', 0))
                downloaded = 0
                
                with open(path, 'wb') as f:
                    for chunk in resp.iter_content(chunk_size=32768):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total_size > 0 and downloaded % (1024 * 1024 * 25) == 0:
                                print(f"  Downloaded {downloaded / (1024*1024):.1f}MB / {total_size / (1024*1024):.1f}MB")
                
                if os.path.exists(path):
                    size_mb = os.path.getsize(path) / (1024 * 1024)
                    print(f"✓ Download complete: {os.path.basename(path)} ({size_mb:.1f}MB)")
                    return
            
        except Exception as e:
            print(f"  Download attempt {attempt + 1}/{max_retries} failed: {str(e)[:100]}")
            if os.path.exists(path):
                try:
                    os.remove(path)
                except:
                    pass
            if attempt < max_retries - 1:
                wait_time = 5 * (attempt + 1)
                print(f"  Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                print(f"✗ All download attempts failed for {os.path.basename(path)}")
                raise



def _download_from_google_drive(file_id, path, timeout=120):
    """Download from Google Drive using direct URL with timeout."""
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    session = requests.Session()
    
    response = session.get(url, stream=True, timeout=timeout, allow_redirects=True, verify=False)
    response.raise_for_status()
    
    # Handle virus scan page
    token = None
    for key, value in response.cookies.items():
        if 'download_warning' in key:
            token = value
            break
    
    if token:
        params = {'confirm': token}
        response = session.get(url, params=params, stream=True, timeout=timeout, allow_redirects=True, verify=False)
        response.raise_for_status()
    
    total_size = int(response.headers.get('content-length', 0))
    downloaded = 0
    
    with open(path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=32768):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                if total_size > 0 and downloaded % (1024 * 1024 * 25) == 0:
                    print(f"Downloaded {downloaded / (1024*1024):.1f}MB / {total_size / (1024*1024):.1f}MB")


app = Flask(__name__, template_folder='templates', static_folder='static')

# Get the directory where app.py is located
APP_DIR = os.path.dirname(os.path.abspath(__file__))
EMBEDDINGS_PATH = os.path.join(APP_DIR, 'embeddings.joblib')
VEC_PATH = os.path.join(APP_DIR, 'tfidf_vectorizer.joblib')

# Load embeddings joblib (expects a DataFrame with columns: title, number, start, end, text, embedding)
if not os.path.exists(EMBEDDINGS_PATH):
    print(f'ERROR: embeddings.joblib not found at {EMBEDDINGS_PATH}')
    print('The RAG system cannot function without embeddings.')
    print('Please ensure embeddings are available at startup.')
    raise SystemExit(f'embeddings.joblib not found at {EMBEDDINGS_PATH}. Please place it here before running the web app.')

try:
    df = joblib.load(EMBEDDINGS_PATH)
    if df.empty:
        raise SystemExit('embeddings.joblib is empty.')
except Exception as e:
    print(f"ERROR loading embeddings: {e}")
    raise SystemExit(f"Failed to load embeddings: {e}")

# Prepare TF-IDF vectorizer for fast, local similarity retrieval
if os.path.exists(VEC_PATH):
    vec = joblib.load(VEC_PATH)
else:
    texts = df['text'].astype(str).tolist()
    vec = TfidfVectorizer().fit(texts)
    joblib.dump(vec, VEC_PATH)

doc_tfidf = vec.transform(df['text'].astype(str).tolist())

OLLAMA_URL = os.environ.get('OLLAMA_URL', 'http://localhost:11434')
OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'llama3.2:1b')


def _retrieve_chunks(query, top_k=5):
    qv = vec.transform([query])
    sims = cosine_similarity(doc_tfidf, qv).flatten()
    idx = sims.argsort()[::-1][:top_k]
    results = []
    for i in idx:
        row = df.iloc[i]
        results.append({
            'title': str(row.get('title', '')),
            'number': str(row.get('number', '')),
            'start': float(row.get('start', 0)),
            'end': float(row.get('end', 0)),
            'text': str(row.get('text', '')),
            'score': float(sims[i]),
            'link': None
        })

    for r in results:
        r['link'] = find_video_link(r['number'], r['title'])

    return results


def _format_context(results):
    if not results:
        return 'No retrieved context was found.'

    lines = []
    for idx, r in enumerate(results, start=1):
        lines.append(
            f"[{idx}] Video {r['number']} - {r['title']} @ {int(r['start'])}s to {int(r['end'])}s\n"
            f"    Score: {r['score']:.4f}\n"
            f"    Text: {r['text']}"
        )
    return '\n\n'.join(lines)


def _build_prompt(query, results):
    context = _format_context(results)
    return (
        'You are a course assistant for a web development video course. '
        'Answer the user only using the retrieved context below. '
        'If the context does not contain enough information, say that the answer cannot be found in the course materials. '
        'Always mention the relevant video number/title and timestamps when applicable.\n\n'
        f'RETRIEVED CONTEXT:\n{context}\n\n'
        f'USER QUESTION:\n{query}\n\n'
        'Answer in a clear, helpful way grounded only in the retrieved context.'
    )


def _call_ollama(prompt):
    response = requests.post(
        f'{OLLAMA_URL}/api/generate',
        json={
            'model': OLLAMA_MODEL,
            'prompt': prompt,
            'stream': False,
        },
        timeout=120,
    )
    response.raise_for_status()
    payload = response.json()
    if isinstance(payload, dict):
        if 'response' in payload:
            return str(payload['response'])
        if 'choices' in payload and payload['choices']:
            return str(payload['choices'][0].get('content', payload))
    return str(payload)


def answer_question(query, top_k=5):
    results = _retrieve_chunks(query, top_k=top_k)
    prompt = _build_prompt(query, results)

    print('\n[RAG] Query:', query)
    print('[RAG] Retrieved chunks:')
    for item in results:
        print(
            f"  - video {item['number']} | {item['title']} | {int(item['start'])}s-{int(item['end'])}s | score={item['score']:.4f}"
        )

    try:
        answer = _call_ollama(prompt)
    except Exception as exc:
        print(f'[RAG] Ollama generation failed: {exc}')
        parts = []
        for r in results:
            parts.append(f"Video {r['number']} - {r['title']} (around {int(r['start'])}s): {r['text'][:140]}...")
        answer = (
            "I could not reach the LLM, so here are the most relevant grounded snippets from the course materials.\n\n"
            + "\n\n".join(parts)
            if parts
            else "I couldn't find relevant snippets in the course materials."
        )

    print('[RAG] Final answer:')
    print(answer)
    return answer, results


def find_video_link(number, title):
    # search for video files in repo that contain the video number or title, extract YouTube id in [id]
    exts = {'.webm', '.mp4', '.mkv', '.mov'}
    pattern_num = f"#{number}"
    for root, dirs, files in os.walk('.'): 
        for fname in files:
            _, ext = os.path.splitext(fname)
            if ext.lower() not in exts:
                continue
            lname = fname.lower()
            if pattern_num in fname or (number and (f" {number}_" in fname or fname.startswith(f"{number}_"))) or (title and title.lower() in lname):
                # try to extract [ID]
                m = re.search(r"\[([A-Za-z0-9_-]{6,})\]", fname)
                if m:
                    vid = m.group(1)
                    return f"https://youtu.be/{vid}"
                # otherwise return relative file path
                return os.path.join(root, fname).replace('\\', '/')
    return None


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/ask', methods=['POST'])
def ask():
    data = request.get_json() or {}
    question = data.get('question', '')
    if not question:
        return jsonify({'error': 'missing question'}), 400
    answer, results = answer_question(question, top_k=6)
    return jsonify({'answer': answer, 'results': results})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)
