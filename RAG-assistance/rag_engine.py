"""
Core RAG logic for the video teaching assistant.
Uses precomputed embeddings.joblib and Groq for answering.
The SentenceTransformer model is loaded lazily on the first request.
"""

import os
import joblib
import numpy as np
from dotenv import load_dotenv
from groq import Groq
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

load_dotenv()

COURSE_NAME = "Web Development"
EMBEDDINGS_FILE = "embeddings.joblib"
GROQ_MODEL = "llama-3.1-8b-instant"

embedder = None
_df = None

groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))


def get_embedder():
    global embedder

    if embedder is None:
        print("=" * 60)
        print("Loading SentenceTransformer model...")
        embedder = SentenceTransformer("all-MiniLM-L6-v2")
        print("SentenceTransformer loaded successfully")
        print("=" * 60)

    return embedder


def embed_texts(text_list):
    model = get_embedder()
    return model.encode(text_list, normalize_embeddings=True)


def load_index():
    global _df

    if _df is None:
        print("=" * 60)
        print("Loading embeddings.joblib...")
        _df = joblib.load(EMBEDDINGS_FILE)
        print(f"Loaded {_df.shape[0]} chunks")
        print("=" * 60)

    return _df


def retrieve(query, top_k=5):
    print("Retrieving relevant chunks...")

    df = load_index()

    query_embedding = embed_texts([query])[0]

    similarities = cosine_similarity(
        np.vstack(df["embedding"]),
        [query_embedding]
    ).flatten()

    top_indices = similarities.argsort()[::-1][:top_k]

    print("Retrieval complete")

    return df.loc[top_indices]


def build_prompt(query, results_df):
    context = results_df[
        ["title", "number", "start", "end", "text"]
    ].to_json(orient="records")

    return f"""
I am teaching a {COURSE_NAME} course.

Here are subtitle chunks:

{context}

--------------------------------

User question:
"{query}"

Answer naturally.

Mention:
- Which video teaches it.
- Approximate timestamps.
- Guide the student to the correct video.

If the question is unrelated to the course,
say you can only answer questions related to this course.
"""


def ask(query, top_k=5):
    print("=" * 60)
    print("STEP 1: ask() called")

    results_df = retrieve(query, top_k)

    print("STEP 2: Retrieval finished")

    prompt = build_prompt(query, results_df)

    print("STEP 3: Prompt built")

    print("STEP 4: Calling Groq...")

    response = groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        temperature=0.3,
    )

    print("STEP 5: Groq response received")

    answer = response.choices[0].message.content

    sources = []

    for _, row in results_df.iterrows():
        sources.append(
            {
                "title": row["title"],
                "number": str(row["number"]),
                "start": float(row["start"]),
                "end": float(row["end"]),
            }
        )

    print("STEP 6: Returning answer")
    print("=" * 60)

    return answer, sources