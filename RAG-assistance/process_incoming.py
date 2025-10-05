import pandas as pd 
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np 
import joblib 
import requests
import sys
from sklearn.feature_extraction.text import TfidfVectorizer
import os


def create_embedding(text_list):
    # https://github.com/ollama/ollama/blob/main/docs/api.md#generate-embeddings
    r = requests.post("http://localhost:11434/api/embed", json={
        "model": "bge-m3",
        "input": text_list
    })

    embedding = r.json()["embeddings"] 
    return embedding

def inference(prompt):
    r = requests.post("http://localhost:11434/api/generate", json={
        # "model": "deepseek-r1",
        "model": "llama3.2",
        "prompt": prompt,
        "stream": False
    })

    response = r.json()
    # Try to extract a human-readable response, but fall back to raw JSON
    try:
        if isinstance(response, dict) and 'response' in response:
            return response['response']
        # some Ollama installs return {'choices':[{'content': '...'}]}
        if isinstance(response, dict) and 'choices' in response and len(response['choices'])>0:
            return response['choices'][0].get('content', str(response))
        return str(response)
    except Exception:
        return str(response)

if not os.path.exists('embeddings.joblib'):
    print("Error: embeddings.joblib not found. Run preprocess_json.py to create it first.")
    raise SystemExit(1)

df = joblib.load('embeddings.joblib')

if df.empty:
    print('Error: embeddings.joblib loaded but contains no data.')
    raise SystemExit(1)


incoming_query = input("Ask a Question: ")
# Try to get an embedding from Ollama; fall back to TF-IDF vectorizer if not available
try:
    question_embedding = create_embedding([incoming_query])[0]
    use_ollama = True
except Exception:
    print("Ollama not available — falling back to local TF-IDF for query embedding")
    use_ollama = False
    # Load vectorizer if present, otherwise fit a new one on existing texts
    try:
        vec = joblib.load('tfidf_vectorizer.joblib')
    except Exception:
        texts = df['text'].tolist()
        vec = TfidfVectorizer().fit(texts)
        joblib.dump(vec, 'tfidf_vectorizer.joblib')
    question_embedding = vec.transform([incoming_query]).toarray()[0]

# Find similarities of question_embedding with other embeddings
# print(np.vstack(df['embedding'].values))
# print(np.vstack(df['embedding']).shape)
similarities = cosine_similarity(np.vstack(df['embedding']), [question_embedding]).flatten()
# print(similarities)
top_results = 5
max_indx = similarities.argsort()[::-1][0:top_results]
# print(max_indx)
new_df = df.loc[max_indx] 
if new_df.empty:
    print('No matching chunks found for the query.')
    raise SystemExit(0)
# print(new_df[["title", "number", "text"]])

prompt = f'''I am teaching web development in my Sigma web development course. Here are video subtitle chunks containing video title, video number, start time in seconds, end time in seconds, the text at that time:

{new_df[["title", "number", "start", "end", "text"]].to_json(orient="records")}
---------------------------------
"{incoming_query}"
User asked this question related to the video chunks, you have to answer in a human way (dont mention the above format, its just for you) where and how much content is taught in which video (in which video and at what timestamp) and guide the user to go to that particular video. If user asks unrelated question, tell him that you can only answer questions related to the course
'''
with open("prompt.txt", "w") as f:
    f.write(prompt)
if use_ollama:
    raw = inference(prompt)
    # raw may be a dict (various shapes) or a string; normalize to string
    if isinstance(raw, dict):
        if 'response' in raw:
            response = raw['response']
        elif 'choices' in raw and len(raw['choices']) > 0:
            response = raw['choices'][0].get('content', str(raw))
        else:
            # fallback to any printable field or full dict
            response = str(raw)
    else:
        response = str(raw)

    print(response)
    with open("response.txt", "w", encoding="utf-8") as f:
        f.write(response)
else:
    # Simple offline answer: list top chunks and form a concise reply
    top_snippets = new_df.sort_values(by=['start']).head(5)
    lines = []
    for _, item in top_snippets.iterrows():
        lines.append(f"(Video {item['number']} @ {item['start']}s) {item['text']}")
    reply = "\n".join(lines)
    print("(Offline answer - top matching chunks):\n", reply)
    with open("response.txt", "w", encoding="utf-8") as f:
        f.write(reply)
# for index, item in new_df.iterrows():
#     print(index, item["title"], item["number"], item["text"], item["start"], item["end"])