from fastapi import FastAPI, File, UploadFile, Form, Body
from fastapi.middleware.cors import CORSMiddleware
import shutil, os, uuid
from pdf_utils import extract_text_from_pdf, semantic_chunk_text
from embedding_utils import get_embedding
from pinecone_utils import upsert_embedding, query_pinecone, index
from openai import OpenAI
from dotenv import load_dotenv
from pydantic import BaseModel
from fastapi.responses import FileResponse

load_dotenv()

class DeleteRequest(BaseModel):
    doc_id: str

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "./uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    file_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}_{file.filename}")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Now use the new sentence-based chunking
    text = extract_text_from_pdf(file_path)
    chunks = semantic_chunk_text(text)

    # For each chunk, embed and store
    for i, chunk in enumerate(chunks):
        embedding = get_embedding(chunk)
        upsert_embedding(file_id, i, embedding, chunk, file.filename)

    preview = text[:200]
    return {"status": "success", "file_id": file_id, "chunks": len(chunks), "preview": preview}

def is_compare_query(query: str) -> bool:
    """
    Simple heuristic: if the query contains words like 'compare', 'difference',
    or multiple doc references, we assume cross-doc.
    """
    query_lower = query.lower()
    compare_keywords = ["compare", "difference", "versus", "vs", "both documents"]
    return any(kw in query_lower for kw in compare_keywords)

def advanced_retrieval(query_embedding, user_query, top_k=20, final_k=10):
    """
    1. Retrieve a large set (top_k=20) from Pinecone by similarity.
    2. Sort by score (descending).
    3. If user wants a comparison, ensure at least one chunk per doc.
    4. Otherwise, pick top chunks from the highest doc(s).
    5. Return final_k chunks total.
    """
    raw_matches = query_pinecone(query_embedding, top_k=top_k)
    sorted_matches = sorted(raw_matches, key=lambda x: x.get("score", 0), reverse=True)

    if is_compare_query(user_query):
        # Ensure we pick at least one chunk from each doc
        results = ensure_diversity(sorted_matches, desired=final_k)
    else:
        # Just pick top final_k from sorted list
        results = sorted_matches[:final_k]

    return results

def ensure_diversity(matches, desired=10):
    """
    1. Group by filename, keep the highest score from each doc first.
    2. If we still need more chunks, fill from the sorted list.
    """
    from collections import defaultdict
    groups = defaultdict(lambda: None)

    for m in matches:
        meta = m.get("metadata", {})
        fname = meta.get("filename", "unknown")
        if groups[fname] is None:  # not yet picked from this doc
            groups[fname] = m

    # Start with one chunk from each doc
    picks = list(groups.values())
    picks = [p for p in picks if p is not None]

    if len(picks) >= desired:
        # If we already have enough, sort them by score and truncate
        picks.sort(key=lambda x: x["score"], reverse=True)
        return picks[:desired]
    else:
        # Fill remaining slots from the highest scoring matches
        needed = desired - len(picks)
        picked_ids = set(id(x) for x in picks)
        for m in matches:
            if id(m) not in picked_ids:
                picks.append(m)
                picked_ids.add(id(m))
                if len(picks) >= desired:
                    break
        return picks

@app.post("/query")
async def query_document(question: str = Form(...)):
    if question.lower().startswith("how are you"):
        return {"answer": "I'm an AI-powered Q&A agent ready to help you with your documents!", "sources": []}

    query_embedding = get_embedding(question)

    # Retrieve up to top 20, then produce final 10 chunks
    matches = advanced_retrieval(query_embedding, question, top_k=20, final_k=10)
    # Build the context
    sorted_matches = sorted(matches, key=lambda x: x.get("score", 0), reverse=True)
    chunks = [m["metadata"] for m in sorted_matches]

    context_text = "\n\n".join([f"Source: {c['text']}" for c in chunks])
    prompt = f"""You are an expert assistant. Answer the following question based on the context provided below. Cite the source passages used.

Context:
{context_text}

Question: {question}

Answer:"""

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You answer questions using the provided context and cite sources."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=300
    )
    answer = response.choices[0].message.content
    # Return the final sorted chunks
    return {"answer": answer, "sources": chunks}

@app.delete("/delete")
async def delete_document(delete_req: DeleteRequest):
    doc_id = delete_req.doc_id
    vector_ids = [f"{doc_id}_{i}" for i in range(1000)]
    response = index.delete(ids=vector_ids)
    return {"status": "deleted", "doc_id": doc_id, "response": response}

@app.get("/download")
async def download_file(doc_id: str, filename: str):
    file_path = os.path.join(UPLOAD_DIR, f"{doc_id}_{filename}")
    return FileResponse(file_path, media_type="application/pdf", filename=filename)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
