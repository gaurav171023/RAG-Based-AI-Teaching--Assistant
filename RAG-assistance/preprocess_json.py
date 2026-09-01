import os
import json
import time
import joblib
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

JINA_API_KEY = os.getenv("JINA_API_KEY")

if not JINA_API_KEY:
    raise ValueError("JINA_API_KEY not found.")

HEADERS = {
    "Authorization": f"Bearer {JINA_API_KEY}",
    "Content-Type": "application/json"
}

EMBED_URL = "https://api.jina.ai/v1/embeddings"

json_folder = "json"

records = []

# ----------------------------
# Read every transcript
# ----------------------------

for filename in sorted(os.listdir(json_folder)):

    if not filename.endswith(".json"):
        continue

    path = os.path.join(json_folder, filename)

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for chunk in data["chunks"]:

        records.append({
            "title": chunk["title"],
            "number": chunk["number"],
            "start": chunk["start"],
            "end": chunk["end"],
            "text": chunk["text"]
        })

print(f"Loaded {len(records)} chunks")

# ----------------------------
# Resume support
# ----------------------------

SAVE_FILE = "embeddings_progress.joblib"

if os.path.exists(SAVE_FILE):

    df = joblib.load(SAVE_FILE)

    embeddings = list(df["embedding"])

    start_index = len(embeddings)

    print(f"Resuming from {start_index}")

else:

    embeddings = []

    start_index = 0

texts = [r["text"] for r in records]

BATCH_SIZE = 32

# ----------------------------
# Embed
# ----------------------------

for i in range(start_index, len(texts), BATCH_SIZE):

    batch = texts[i:i+BATCH_SIZE]

    success = False

    for attempt in range(5):

        try:

            response = requests.post(

                EMBED_URL,

                headers=HEADERS,

                json={
                    "model":"jina-embeddings-v3",
                    "input":batch
                },

                timeout=120
            )

            if response.status_code == 200:

                success = True

                break

            print(
                f"Retry {attempt+1}/5 "
                f"Status {response.status_code}"
            )

            time.sleep(5)

        except Exception as e:

            print(e)

            time.sleep(5)

    if not success:

        print("Stopping safely...")

        break

    data = response.json()["data"]

    embeddings.extend(
        [x["embedding"] for x in data]
    )

    temp = pd.DataFrame(records[:len(embeddings)])

    temp["embedding"] = embeddings

    joblib.dump(temp, SAVE_FILE)

    print(f"Embedded {len(embeddings)}/{len(records)}")

# ----------------------------
# Finished
# ----------------------------

if len(embeddings)==len(records):

    df = pd.DataFrame(records)

    df["embedding"] = embeddings

    joblib.dump(df,"embeddings.joblib")

    print("Done!")

    os.remove(SAVE_FILE)

else:

    print("Run again to continue.")  