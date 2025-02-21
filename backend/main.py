from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
import shutil, os, uuid
import re  # for parsing citations
from pdf_utils import extract_text_from_pdf, semantic_chunk_text
from embedding_utils import get_embedding
from pinecone_utils import upsert_embedding, query_pinecone, index
from openai import OpenAI
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from pydantic import BaseModel
from fastapi.responses import FileResponse

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        index.delete(deleteAll=True)
        print("Pinecone index cleared on startup.")
    except Exception as e:
        print("Error clearing Pinecone index:", e)
    yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "./uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

uploaded_docs = []

class DeleteRequest(BaseModel):
    doc_id: str


##############################
# Helper: Truncate text to a token limit
##############################
def truncate_text(text: str, max_tokens: int = 200, model_name: str = "text-embedding-ada-002") -> str:
    import tiktoken
    encoding = tiktoken.encoding_for_model(model_name)
    tokens = encoding.encode(text)
    if len(tokens) > max_tokens:
        tokens = tokens[:max_tokens]
    return encoding.decode(tokens)

##############################
# Upload Endpoint
##############################
@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    file_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}_{file.filename}")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    text = extract_text_from_pdf(file_path)
    chunks = semantic_chunk_text(text)
    for i, chunk in enumerate(chunks):
        embedding = get_embedding(chunk)
        upsert_embedding(file_id, i, embedding, chunk, file.filename)
    
    uploaded_docs.append((file_id, file.filename.lower()))
    preview = text[:200]
    return {"status": "success", "file_id": file_id, "chunks": len(chunks), "preview": preview}

##############################
# Delete Endpoint
##############################
@app.delete("/delete")
async def delete_document(delete_req: DeleteRequest):
    doc_id = delete_req.doc_id
    vector_ids = [f"{doc_id}_{i}" for i in range(1000)]
    response = index.delete(ids=vector_ids)
    global uploaded_docs
    uploaded_docs = [doc for doc in uploaded_docs if doc[0] != doc_id]
    return {"status": "deleted", "doc_id": doc_id, "response": response}

##############################
# Download Endpoint
##############################
@app.get("/download")
async def download_file(doc_id: str, filename: str):
    file_path = os.path.join(UPLOAD_DIR, f"{doc_id}_{filename}")
    return FileResponse(file_path, media_type="application/pdf", filename=filename)

##############################
# LLM-based Query Classification
##############################
def classify_query_with_llm(question: str) -> str:
    prompt = f"""
You are a classification system. The user query is: "{question}"
Respond with exactly one word from [general, single, multi, none].
"""
    resp = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a classification system."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.0,
        max_tokens=10
    )
    c = resp.choices[0].message.content.strip().lower()
    if c not in {"general", "single", "multi", "none"}:
        c = "none"
    return c

##############################
# Small Talk Response for General/None Queries
##############################
def small_talk_llm_response(question: str) -> str:
    st_prompt = f"""
You are a friendly AI assistant. The user said: "{question}"
Respond in a natural conversational style.
"""
    resp = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a friendly conversational AI."},
            {"role": "user", "content": st_prompt}
        ],
        temperature=0.7,
        max_tokens=300  # Somewhat higher budget
    )
    return resp.choices[0].message.content.strip()

##############################
# Single Document Retrieval (with New Doc Bonus)
##############################
def single_doc_retrieval(sorted_matches):
    bonus_map = {}
    total = len(uploaded_docs)
    for idx, (doc_id, _) in enumerate(uploaded_docs):
        bonus_map[doc_id] = ((idx + 1) / total) * 0.05 if total > 0 else 0.0
    for match in sorted_matches:
        meta = match.get("metadata", {})
        doc_id = meta.get("doc_id", "")
        match["adjusted_score"] = match.get("score", 0) + bonus_map.get(doc_id, 0)
    sorted_adjusted = sorted(sorted_matches, key=lambda x: x.get("adjusted_score", 0), reverse=True)
    return sorted_adjusted[:5]

##############################
# Multi-document Retrieval (Diverse Results)
##############################
def multi_doc_retrieval(sorted_matches):
    groups = {}
    for match in sorted_matches:
        meta = match.get("metadata", {})
        fname = meta.get("filename", "unknown")
        if fname not in groups or match.get("score", 0) > groups[fname].get("score", 0):
            groups[fname] = match
    return list(groups.values())[:10]

##############################
# Advanced Retrieval Logic
##############################
def advanced_retrieval(query_embedding, classification: str, score_threshold=0.2):
    raw_matches = query_pinecone(query_embedding, top_k=20)
    if not raw_matches:
        return []
    sorted_matches = sorted(raw_matches, key=lambda x: x.get("score", 0), reverse=True)
    if sorted_matches[0].get("score", 0) < score_threshold:
        return []
    if classification == "multi":
        final_matches = multi_doc_retrieval(sorted_matches)
    else:
        final_matches = single_doc_retrieval(sorted_matches)
    return final_matches

##############################
# /query Endpoint
##############################
@app.post("/query")
async def query_document(question: str = Form(...)):
    classification = classify_query_with_llm(question)
    if classification in ["general", "none"]:
        answer = small_talk_llm_response(question)
        return {"answer": answer, "sources": []}
    
    query_emb = get_embedding(question)
    final_matches = advanced_retrieval(query_emb, classification, score_threshold=0.2)
    if not final_matches:
        fallback = small_talk_llm_response(question)
        return {"answer": fallback, "sources": []}
    
    # Build context, truncating each chunk to 200 tokens to avoid large prompts
    chunks = [m["metadata"] for m in final_matches]
    context_lines = []
    for idx, c in enumerate(chunks, start=1):
        truncated_text = truncate_text(c["text"], 200)  # Limit each chunk to 200 tokens
        context_lines.append(f"[{idx}] Source: {truncated_text}")
    context_text = "\n\n".join(context_lines)
    
    doc_prompt = f"""You are an expert assistant with access to the uploaded document excerpts.
You have access to the relevant document(s) as provided below.
Do not disclaim that you don't have access.
Answer the following question using the context provided.
Include inline citations in the format [1], [2], etc.

Context:
{context_text}

Question: {question}

Answer:"""
    
    resp = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You have full access to the provided document excerpts."},
            {"role": "user", "content": doc_prompt}
        ],
        temperature=0.3,
        max_tokens=1500  # Increased budget to reduce truncation
    )
    answer = resp.choices[0].message.content

    # 1) Parse the answer for citations like [1], [2], etc.
    used_citations = set()
    for match in re.findall(r'\[(\d+)\]', answer):
        try:
            used_citations.add(int(match))
        except ValueError:
            pass

    # 2) Filter only those chunks that were actually cited
    used_chunks = []
    for i, chunk in enumerate(chunks, start=1):
        if i in used_citations:
            used_chunks.append(chunk)

    return {"answer": answer, "sources": used_chunks}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
