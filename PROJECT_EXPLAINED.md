# PROJECT_EXPLAINED

## 1) The Goal
This project builds a course assistant that answers questions using your own course videos, not generic internet text.

In plain terms:
- You give it course videos.
- It converts videos to audio.
- It transcribes audio into timestamped text.
- It stores that text in a searchable form.
- When a user asks a question, it retrieves the most relevant transcript pieces first.
- It then asks an LLM to answer using those retrieved pieces.
- The final answer points to video/timestamp context.

That pattern is called RAG (Retrieval-Augmented Generation): retrieve first, generate second.

---

## 2) Folder Structure (Current, After Cleanup)

### Project Root
- .git/: Git history and metadata for version control.
- .gitattributes: Git file handling rules.
- .gitignore: Files/folders Git should ignore.
- .python-version: Python version marker for tools like pyenv.
- .venv/: Local virtual environment with installed Python packages.
- preflight.py: Startup helper that ensures model artifacts exist before launching server.
- Procfile: Process command used by Render/Heroku-style platforms.
- PROJECT_EXPLAINED.md: This beginner-level project explanation file.
- RAG-assistance/: Main application and data folder.
- render.yaml: Render deployment config for build/start commands.
- requirements.txt: Root Python dependencies for deployment/runtime.
- runtime.txt: Runtime hint (Python runtime version on some platforms).
- verify_setup.py: Local health/validation script for startup and RAG basics.
- wsgi.py: WSGI entrypoint used by Gunicorn to serve Flask app.

### RAG-assistance
- .gitignore: Ignore rules specific to this subfolder.
- 1758903138109-rag_sample-videos/: Source video folder used in the preprocessing pipeline.
- 1758903342221-rag_all_audios/: Source audio folder used in the preprocessing pipeline.
- __pycache__/: Python bytecode cache (auto-generated).
- app.py: Main Flask backend, retrieval logic, prompt building, and LLM call.
- embeddings.joblib: Saved DataFrame containing transcript chunks and embedding vectors.
- jsons/: Timestamped transcript chunks (one JSON per lecture/video).
- mp3_to_json.py: Transcribes audio to JSON with timestamps using Whisper.
- preprocess_json.py: Builds/updates embeddings.joblib and tfidf_vectorizer.joblib.
- requirements.txt: Python dependencies specific to this app folder.
- static/: Frontend JS/CSS assets.
- templates/: Frontend HTML template.
- tfidf_vectorizer.joblib: Saved TF-IDF vectorizer used for retrieval.
- video_to_mp3.py: Converts raw video files into MP3 audio using ffmpeg.

### RAG-assistance/static
- app.js: Browser logic for sending questions and rendering answers/sources.
- styles.css: Chat UI styling.

### RAG-assistance/templates
- index.html: Chat page structure.

### RAG-assistance/jsons
- 01_Installing VS Code & How Websites Work.mp3.json: Transcript chunks for video 1.
- 02_Your First HTML Website.mp3.json: Transcript chunks for video 2.
- 03_Basic Structure of an HTML Website.mp3.json: Transcript chunks for video 3.
- 04_Heading, Paragraphs and Links.mp3.json: Transcript chunks for video 4.
- 05_Image, Lists, and Tables in HTML.mp3.json: Transcript chunks for video 5.
- 06_SEO and Core Web Vitals in HTML.mp3.json: Transcript chunks for video 6.
- 07_Forms and input tags in HTML.mp3.json: Transcript chunks for video 7.
- 08_Inline & Block Elements in HTML.mp3.json: Transcript chunks for video 8.
- 09_Id & Classes in HTML.mp3.json: Transcript chunks for video 9.
- 10_Video, Audio & Media in HTML.mp3.json: Transcript chunks for video 10.
- 11_Semantic Tags  in HTML.mp3.json: Transcript chunks for video 11.
- 12_Exercise 1 - Pure HTML Media Player.mp3.json: Transcript chunks for video 12.
- 13_Entities, Code tag and more on HTML.mp3.json: Transcript chunks for video 13.
- 14_Introduction to CSS.mp3.json: Transcript chunks for video 14.
- 15_Inline, Internal & External CSS.mp3.json: Transcript chunks for video 15.
- 16_Exercise 1 - Solution & Shoutouts.mp3.json: Transcript chunks for video 16.
- 17_CSS Selectors MasterClass.mp3.json: Transcript chunks for video 17.
- 18_CSS Box Model - Margin, Padding & Borders.mp3.json: Transcript chunks for video 18.

---

## 3) Step-by-Step Build Order (From Zero)

## Step A: Convert raw videos to MP3 (video_to_mp3.py)
File: RAG-assistance/video_to_mp3.py

What this script does, line-by-line in plain English:

```python
import os
import subprocess
import shutil
```
- os: file and folder operations.
- subprocess: run shell programs from Python.
- shutil: utility functions, here used to detect ffmpeg in PATH.

```python
def find_videos_dir():
    if os.path.isdir('videos'):
        return 'videos'
    for name in os.listdir('.'):
        if os.path.isdir(name) and ('video' in name.lower() or 'videos' in name.lower() or 'webm' in name.lower()):
            return name
    return 'videos'
```
- Looks for input video folder automatically.
- Uses videos/ if present.
- Otherwise picks a folder whose name looks like video content.

```python
VIDEOS_DIR = find_videos_dir()
AUDIOS_DIR = 'audios'
os.makedirs(AUDIOS_DIR, exist_ok=True)
```
- Sets source and destination folders.
- Creates audios/ if missing.

```python
if not os.path.isdir(VIDEOS_DIR):
    raise SystemExit(1)
```
- Stops early if no valid video folder exists.

```python
if shutil.which('ffmpeg') is None:
    raise SystemExit(1)
```
- Stops early if ffmpeg is not installed.

```python
files = os.listdir(VIDEOS_DIR)
for file in files:
    ...
    subprocess.run(['ffmpeg', '-y', '-i', src, dst])
```
- Loops through each video file.
- Builds an output MP3 filename.
- Calls ffmpeg to extract audio and save MP3.

Why ffmpeg is used:
- ffmpeg is the standard reliable tool for media conversion.
- It supports almost every video format.
- It is fast and script-friendly.

---

## Step B: Convert MP3 audio to timestamped JSON (mp3_to_json.py)
File: RAG-assistance/mp3_to_json.py

What Whisper is:
- Whisper is an OpenAI speech-to-text model.
- It turns spoken audio into text and returns time-aligned segments.

Core flow in this script:

```python
def ensure_whisper():
    try:
        import whisper
        return whisper
    except Exception:
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'openai-whisper'], check=True)
        ...
```
- Tries to import whisper.
- If missing, tries to install it automatically.

```python
model = whisper.load_model("large-v2")
```
- Loads the large-v2 transcription model for better accuracy.

```python
result = model.transcribe(
    audio=os.path.join(AUDIOS_DIR, audio),
    language="hi",
    task="translate",
    word_timestamps=False
)
```
- Transcribes each audio file.
- language="hi" and task="translate" means Hindi speech is translated to English text.

```python
chunks.append({
  "number": number,
  "title": title,
  "start": segment["start"],
  "end": segment["end"],
  "text": segment["text"]
})
```
- Converts Whisper segments into the project chunk format.
- Each chunk has video metadata + timestamp + text.

```python
chunks_with_metadata = {"chunks": chunks, "text": result["text"]}
json.dump(chunks_with_metadata, f, ensure_ascii=False)
```
- Saves one JSON per audio file in jsons/.

Real output structure example from this project:

```json
{
  "chunks": [
    {
      "number": "1",
      "title": "Installing VS Code & How Websites Work",
      "start": 0.0,
      "end": 3.5,
      "text": " From today's video, we will start the Sigma Web Development course."
    }
  ],
  "text": "...full transcript..."
}
```

---

## Step C: Turn transcripts into searchable units (preprocess_json.py)
File: RAG-assistance/preprocess_json.py

What chunking means:
- Chunking means splitting long text into smaller pieces so retrieval can match specific parts.

How this project chunks:
- This project does not add a second custom splitter in preprocess_json.py.
- It directly reuses Whisper segments already present in content["chunks"].
- So chunk size is variable (whatever Whisper segment length is).
- Overlap is 0 (no overlap between adjacent chunks).

Relevant code:

```python
with open(f"jsons/{json_file}") as f:
    content = json.load(f)
texts = [c['text'] for c in content['chunks']]
...
for i, chunk in enumerate(content['chunks']):
    chunk['chunk_id'] = chunk_id
    chunk['embedding'] = embeddings[i]
    my_dicts.append(chunk)
```

Why chunking is necessary:
- Retrieval works best on smaller focused text pieces.
- If you search over giant full transcripts, matches become noisy and less precise.

---

## Step D: Convert chunks to vectors using TF-IDF
Files: RAG-assistance/preprocess_json.py and RAG-assistance/app.py

What TF-IDF means in plain English:
- TF (Term Frequency): how often a word appears in one chunk.
- IDF (Inverse Document Frequency): how rare that word is across all chunks.
- Combined TF-IDF gives more weight to words that are important for one chunk and not common everywhere.

How text becomes numbers:
- The vectorizer builds a vocabulary of words.
- Each chunk becomes a numeric vector where each position is a weighted word score.

Why this project uses TF-IDF instead of neural embeddings for retrieval in app.py:
- It is lightweight, local, and fast on CPU.
- It needs no large embedding service at query time.
- It keeps deployment simple.

Important note about this codebase:
- preprocess_json.py tries Ollama embeddings first, then falls back to TF-IDF embeddings when Ollama embed API is unavailable.
- app.py retrieval itself uses TF-IDF vectors built from df['text'] and saved tfidf_vectorizer.joblib.

---

## Step E: Save artifacts with joblib
Files: RAG-assistance/preprocess_json.py and RAG-assistance/app.py

What joblib is:
- joblib is a Python library for saving/loading Python objects to disk quickly.

How artifacts are created:

```python
df = pd.DataFrame.from_records(my_dicts)
joblib.dump(df, 'embeddings.joblib')
```
- Saves all chunk records and vectors into embeddings.joblib.

```python
vec = TfidfVectorizer().fit(texts)
joblib.dump(vec, 'tfidf_vectorizer.joblib')
```
- Saves the trained TF-IDF vocabulary/model.

How they are loaded in app.py:

```python
df = joblib.load(EMBEDDINGS_PATH)
vec = joblib.load(VEC_PATH)
```

---

## Step F: How app.py handles one user question (exact sequence)
File: RAG-assistance/app.py

1. Flask receives a POST request on /ask.
```python
@app.route('/ask', methods=['POST'])
def ask():
    data = request.get_json() or {}
    question = data.get('question', '')
```

2. It calls answer_question(question, top_k=6).
```python
answer, results = answer_question(question, top_k=6)
```

3. answer_question starts retrieval first (always).
```python
results = _retrieve_chunks(query, top_k=top_k)
```

4. Retrieval scoring uses cosine similarity between:
- all document vectors (doc_tfidf)
- question vector (qv)

```python
qv = vec.transform([query])
sims = cosine_similarity(doc_tfidf, qv).flatten()
idx = sims.argsort()[::-1][:top_k]
```

Cosine similarity in plain English:
- Imagine each text is an arrow in space.
- If two arrows point in almost the same direction, they are semantically similar.
- Cosine similarity measures that directional closeness.
- Higher score means the chunk is more relevant to the question.

5. Top chunks are selected by sorting scores descending.
```python
idx = sims.argsort()[::-1][:top_k]
```

6. The prompt is built from those retrieved chunks.
```python
prompt = _build_prompt(query, results)
```
- _format_context(results) turns chunks into a readable context block.
- _build_prompt inserts context + user question with strict grounding instructions.

7. Ollama is called for generation.
```python
response = requests.post(
    f'{OLLAMA_URL}/api/generate',
    json={'model': OLLAMA_MODEL, 'prompt': prompt, 'stream': False},
    timeout=120,
)
```

8. If Ollama fails, app.py returns grounded fallback snippets instead of crashing.
```python
except Exception as exc:
    answer = (
      "I could not reach the LLM, so here are the most relevant grounded snippets..."
    )
```

9. API response returns both:
- answer (LLM answer or fallback)
- results (retrieved chunks and metadata)

```python
return jsonify({'answer': answer, 'results': results})
```

10. Server logs show query, retrieved chunks, and final answer for verification.
```python
print('[RAG] Retrieved chunks:')
print('[RAG] Final answer:')
```

---

## Step G: How the app is run and deployed

### Flask, WSGI, Gunicorn in simple terms
- Flask: your Python web framework that defines routes like / and /ask.
- WSGI: a standard interface that lets production servers run Python web apps.
- Gunicorn: a production WSGI server process that runs your Flask app.
- Deployment: putting your app on a cloud server so others can access it.

### Actual files and roles
- wsgi.py: imports app from RAG-assistance/app.py so Gunicorn can serve it.
- Procfile: says web: gunicorn wsgi:app --bind 0.0.0.0:$PORT.
- render.yaml: tells Render how to build (pip install -r requirements.txt) and start (gunicorn wsgi:app ...).
- preflight.py: optional pre-start script that can download embeddings/vectorizer if env URLs are configured.
- verify_setup.py: local safety check before deployment.

---

## Step H: Frontend question flow (index.html + app.js + styles.css)

1. index.html renders a simple chat UI and loads /static/app.js.
2. User types question and submits form.
3. app.js intercepts submit event in browser JavaScript.
4. It sends a fetch request to backend:

```javascript
const res = await fetch('/ask', {
  method:'POST',
  headers:{'Content-Type':'application/json'},
  body: JSON.stringify({question:q})
});
```

What a fetch/API call means in plain English:
- fetch is browser code that sends an HTTP request to your backend.
- API call means the frontend asks backend logic for data and gets JSON back.

5. app.js reads JSON response and displays:
- main answer
- top source snippets (with optional watch links)

6. styles.css controls chat look and feel.

---

## 4) Key Terms Glossary (Specific to This Project)
- RAG: A method where this app retrieves transcript chunks first, then generates an answer from that retrieved context.
- Retrieval: Finding the most relevant transcript chunks for a user question.
- Embedding: A numeric representation of text stored per chunk in embeddings.joblib.
- Vectorization: Converting text into numeric vectors so math can compare relevance.
- TF-IDF: A word-weighting method that scores words by local importance and global rarity across all chunks.
- Cosine similarity: A score measuring how similarly two text vectors point in vector space.
- Chunking: Splitting transcript text into smaller timestamped pieces to improve retrieval precision.
- LLM: The language model (via Ollama) that writes final natural-language answers.
- Prompt: The instruction text sent to the LLM, including retrieved chunks and the user question.
- Endpoint: A URL route in backend, like /ask, that handles a specific request.
- API: Rules and routes the frontend uses to talk to backend and exchange JSON.
- JSON: A text data format used for transcript files and API request/response payloads.
- Flask: The Python framework hosting routes, request handling, and responses.
- WSGI: The interface standard that lets Gunicorn run Flask in production.
- Virtual environment: An isolated Python package environment in .venv so dependencies do not conflict globally.

---

## 5) Honest Limitations of This Implementation
1. Retrieval quality is TF-IDF based in runtime app.py, so semantic matching is weaker than modern neural embedding retrievers.
2. There is no reranker stage, so top-k chunk order depends only on first-pass cosine similarity scores.
3. Storage is local/in-memory + joblib files, not a production vector database with filtering, scaling, or distributed indexing.
4. Final generation depends on a local Ollama server being up; if not, the app falls back to snippet summaries instead of true LLM generation.

---

## Quick Reality Check of Current Behavior
- Retrieval is enforced before generation in app.py.
- Prompt is always built from retrieved context.
- Logs show retrieved chunks and final answer.
- If Ollama is down, user still gets grounded snippet-based fallback output.
