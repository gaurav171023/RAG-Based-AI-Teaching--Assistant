from flask import Flask, render_template, request, jsonify
import joblib
import os
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
import requests


def _download_if_missing(path, url):
    """Download a file from url to path if it doesn't exist."""
    if os.path.exists(path) or not url:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    resp = requests.get(url, stream=True, timeout=300)
    resp.raise_for_status()
    with open(path, 'wb') as f:
        for chunk in resp.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)

app = Flask(__name__, template_folder='templates', static_folder='static')

# Get the directory where app.py is located
APP_DIR = os.path.dirname(os.path.abspath(__file__))
EMBEDDINGS_PATH = os.path.join(APP_DIR, 'embeddings.joblib')
VEC_PATH = os.path.join(APP_DIR, 'tfidf_vectorizer.joblib')

# Optionally download large artifacts if provided via environment URLs
_download_if_missing(EMBEDDINGS_PATH, os.getenv('EMBEDDINGS_URL'))
_download_if_missing(VEC_PATH, os.getenv('TFIDF_VECTORIZER_URL'))

# Load embeddings joblib (expects a DataFrame with columns: title, number, start, end, text, embedding)
if not os.path.exists(EMBEDDINGS_PATH):
    raise SystemExit(f'embeddings.joblib not found at {EMBEDDINGS_PATH}. Please place it here before running the web app.')

df = joblib.load(EMBEDDINGS_PATH)
if df.empty:
    raise SystemExit('embeddings.joblib is empty.')

# Prepare TF-IDF vectorizer for fast, local similarity retrieval
if os.path.exists(VEC_PATH):
    vec = joblib.load(VEC_PATH)
else:
    texts = df['text'].astype(str).tolist()
    vec = TfidfVectorizer().fit(texts)
    joblib.dump(vec, VEC_PATH)

doc_tfidf = vec.transform(df['text'].astype(str).tolist())


def answer_question(query, top_k=5):
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

    # try to fill in links
    for r in results:
        link = find_video_link(r['number'], r['title'])
        r['link'] = link

    # Compose a short human-friendly answer: say which videos and timestamps to check
    if not results:
        answer = "I couldn't find relevant snippets in the course materials."
    else:
        parts = []
        used = set()
        for r in results:
            key = (r['number'], r['title'])
            if key in used:
                continue
            used.add(key)
            parts.append(f"Video {r['number']} – {r['title']} (around {int(r['start'])}s): {r['text'][:140]}...")
        answer = "\n\n".join(parts)

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
