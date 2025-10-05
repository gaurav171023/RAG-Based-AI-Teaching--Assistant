import requests
import os
import json
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer

def create_embedding(text_list):
    # https://github.com/ollama/ollama/blob/main/docs/api.md#generate-embeddings
    r = requests.post("http://localhost:11434/api/embed", json={
        "model": "bge-m3",
        "input": text_list
    })

    embedding = r.json()["embeddings"] 
    return embedding


jsons = os.listdir("jsons")  # List all the jsons 
my_dicts = []
chunk_id = 0

if os.path.exists('embeddings.joblib') and '--force' not in os.sys.argv:
    print("embeddings.joblib already exists — skipping preprocessing. Pass --force to regenerate.")
    raise SystemExit(0)

for json_file in jsons:
    with open(f"jsons/{json_file}") as f:
        content = json.load(f)
    print(f"Creating Embeddings for {json_file}")
    texts = [c['text'] for c in content['chunks']]
    # Try Ollama embeddings first, fall back to local TF-IDF
    try:
        embeddings = create_embedding(texts)
    except Exception:
        print("Ollama embeddings not available, falling back to local TF-IDF embeddings")
        vec = TfidfVectorizer()
        tfidf = vec.fit_transform(texts)
        embeddings = [tfidf[i].toarray().flatten() for i in range(tfidf.shape[0])]
        # save the vectorizer for reuse (optional)
        joblib.dump(vec, 'tfidf_vectorizer.joblib')
       
    for i, chunk in enumerate(content['chunks']):
        chunk['chunk_id'] = chunk_id
        chunk['embedding'] = embeddings[i]
        chunk_id += 1
        my_dicts.append(chunk) 

df = pd.DataFrame.from_records(my_dicts)
# Save this dataframe
joblib.dump(df, 'embeddings.joblib')

