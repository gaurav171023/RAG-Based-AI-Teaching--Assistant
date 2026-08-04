"""
Core RAG logic for the video teaching assistant.
Same shape as your original script (embed -> cosine similarity -> prompt -> Groq),
just with Ollama's local embed endpoint swapped for sentence-transformers
(runs in-process, no server to keep alive, no memory issues).
"""

import os
import numpy as np
import joblib
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# Edit this to match whatever course/video set you load into json/
COURSE_NAME = "Web Development"

EMBEDDINGS_FILE = "embeddings.joblib"

embedder = SentenceTransformer("all-MiniLM-L6-v2")
groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
GROQ_MODEL = "llama-3.1-8b-instant"  # check console.groq.com/docs/models if this is retired

_df = None  # cached in-memory copy of embeddings.joblib


def embed_texts(text_list):
    """Same role as your original create_embedding() — now local, no Ollama server needed."""
    return embedder.encode(text_list, normalize_embeddings=True)


def load_index():
    global _df
    if _df is None:
        _df = joblib.load(EMBEDDINGS_FILE)  # raises FileNotFoundError if preprocess hasn't run
    return _df


def retrieve(query, top_k=5):
    df = load_index()
    query_embedding = embed_texts([query])[0]
    similarities = cosine_similarity(np.vstack(df["embedding"]), [query_embedding]).flatten()
    top_indices = similarities.argsort()[::-1][:top_k]
    return df.loc[top_indices]


def build_prompt(query, results_df):
    context = results_df[["title", "number", "start", "end", "text"]].to_json(orient="records")
    return f'''I am teaching a {COURSE_NAME} course. Here are video subtitle chunks containing video title, video number, start time in seconds, end time in seconds, and the text at that time:

{context}
---------------------------------
"{query}"
The user asked this question related to the video chunks. Answer in a natural, human way (don't mention the format above, it's just for you) explaining where and how much content is taught, in which video and at what timestamp, and guide the user to go to that particular video. If the question is unrelated to the course, say you can only answer questions related to the course.'''


def ask(query, top_k=5):
    results_df = retrieve(query, top_k=top_k)
    prompt = build_prompt(query, results_df)

    response = groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    answer = response.choices[0].message.content

    sources = [
        {
            "title": row["title"],
            "number": str(row["number"]),
            "start": float(row["start"]),
            "end": float(row["end"]),
        }
        for _, row in results_df.iterrows()
    ]
    return answer, sources