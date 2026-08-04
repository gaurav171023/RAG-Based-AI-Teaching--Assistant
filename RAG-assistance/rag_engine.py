import os
import joblib
import requests
import numpy as np
from dotenv import load_dotenv
from groq import Groq
from sklearn.metrics.pairwise import cosine_similarity

load_dotenv()

COURSE_NAME = "Web Development"
EMBEDDINGS_FILE = "embeddings.joblib"
GROQ_MODEL = "llama-3.1-8b-instant"

JINA_API_KEY = os.getenv("JINA_API_KEY")

if not JINA_API_KEY:
    raise ValueError("JINA_API_KEY not found")

HEADERS = {
    "Authorization": f"Bearer {JINA_API_KEY}",
    "Content-Type": "application/json"
}

EMBED_URL = "https://api.jina.ai/v1/embeddings"

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

_df = None


def embed_texts(texts):
    response = requests.post(
        EMBED_URL,
        headers=HEADERS,
        json={
            "model": "jina-embeddings-v3",
            "input": texts
        },
        timeout=60
    )

    response.raise_for_status()

    data = response.json()["data"]

    return np.array([x["embedding"] for x in data])


def load_index():
    global _df

    if _df is None:
        print("Loading embeddings.joblib...")
        _df = joblib.load(EMBEDDINGS_FILE)
        print(f"Loaded {_df.shape[0]} chunks")

    return _df


def retrieve(query, top_k=5):

    df = load_index()

    query_embedding = embed_texts([query])[0]

    similarities = cosine_similarity(
        np.vstack(df["embedding"]),
        [query_embedding]
    ).flatten()

    top_indices = similarities.argsort()[::-1][:top_k]

    return df.loc[top_indices]


def build_prompt(query, results_df):

    context = results_df[
        ["title", "number", "start", "end", "text"]
    ].to_json(orient="records")

    return f"""
I am teaching a {COURSE_NAME} course.

Video subtitle chunks:

{context}

----------------------------

User Question:
{query}

Answer naturally.

Mention:

- Which video teaches it.
- Approximate timestamps.
- Guide the student to the correct video.

If unrelated to the course,
say you can only answer questions related to this course.
"""


def ask(query, top_k=5):

    print("=" * 60)
    print("Retrieving...")

    results_df = retrieve(query, top_k)

    print("Calling Groq...")

    prompt = build_prompt(query, results_df)

    response = groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.3,
    )

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

    return answer, sources