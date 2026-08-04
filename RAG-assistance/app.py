import os
from fastapi import FastAPI, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

import rag_engine

app = FastAPI(title="RAG Teaching Assistant")

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/videos", StaticFiles(directory="videos"), name="videos")


@app.get("/")
def home():
    return FileResponse("static/index.html")


@app.post("/ask")
async def ask(question: str = Form(...)):
    try:
        answer, sources = rag_engine.ask(question)
    except FileNotFoundError:
        return JSONResponse(
            {"error": "embeddings.joblib not found. Run: python preprocess_json.py"},
            status_code=400,
        )
    return JSONResponse({"answer": answer, "sources": sources})


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)