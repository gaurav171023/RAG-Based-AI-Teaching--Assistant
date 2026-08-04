"""
Reads every transcript-chunk json file in json/, embeds each chunk's text,
and saves the result as embeddings.joblib for rag_engine.py to load.

You already have your json/ folder populated, so you just need to run:
    python preprocess_json.py
"""

import glob
import json
import os
import pandas as pd
import joblib

from rag_engine import embed_texts

JSON_DIR = "json"


def load_chunks():
    chunks = []

    for path in glob.glob(os.path.join(JSON_DIR, "*.json")):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

            if isinstance(data, dict) and "chunks" in data:
                chunks.extend(data["chunks"])
            elif isinstance(data, list):
                chunks.extend(data)
            else:
                print(f"Skipping unexpected JSON format: {path}")

    return chunks


def main():
    chunks = load_chunks()
    if not chunks:
        print(f"No chunks found in {JSON_DIR}/. Add your transcript json files there first.")
        return

    df = pd.DataFrame(chunks)
    print(f"Loaded {len(df)} chunks from {JSON_DIR}/")

    texts = df["text"].tolist()
    embeddings = embed_texts(texts)
    df["embedding"] = list(embeddings)

    joblib.dump(df, "embeddings.joblib")
    print(f"Saved embeddings.joblib ({len(df)} chunks)")


if __name__ == "__main__":
    main()