from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
import shutil, os, uuid
from pdf_utils import extract_text_from_pdf, chunk_text
from embedding_utils import get_embedding
from pinecone_utils import upsert_embedding, query_pinecone, index
from openai import OpenAI

client = OpenAI()
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Enable CORS for your frontend URL
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
    # Save file locally
    file_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}_{file.filename}")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Extract text and chunk it
    text = extract_text_from_pdf(file_path)
    chunks = chunk_text(text)

    # For each chunk, generate its embedding and upsert to Pinecone
    for i, chunk in enumerate(chunks):
        embedding = get_embedding(chunk)
        upsert_embedding(file_id, i, embedding, chunk, file.filename)

    return {"status": "success", "file_id": file_id, "chunks": len(chunks)}


@app.post("/query")
async def query_document(question: str = Form(...)):
    # Check for general conversation
    if question.lower().startswith("how are you"):
        return {"answer": "I'm an AI-powered Q&A agent ready to help you with your documents!", "sources": []}

    # Generate the query embedding
    query_embedding = get_embedding(question)
    
    # Retrieve a larger set of candidates to allow for diversity (e.g. top 10)
    top_k = 15
    matches = query_pinecone(query_embedding, top_k=top_k)
    
    # Group matches by document using the 'filename' field in metadata.
    # This ensures that we pick the best chunk from each document.
    groups = {}
    for match in matches:
        metadata = match.get("metadata", {})
        filename = metadata.get("filename", "unknown")
        # If this document hasn't been seen or this match has a higher score, keep it.
        if filename not in groups or match.get("score", 0) > groups[filename].get("score", 0):
            groups[filename] = match

    # Our diverse matches come from each distinct document.
    diverse_matches = list(groups.values())

    # If we have fewer than the desired number of chunks (e.g., 7), then fill up using the highest scoring remaining chunks.
    desired = 10
    if len(diverse_matches) < desired:
        # Sort all matches by score (highest first)
        sorted_matches = sorted(matches, key=lambda x: x.get("score", 0), reverse=True)
        seen_filenames = set(match["metadata"].get("filename", "unknown") for match in diverse_matches)
        for match in sorted_matches:
            filename = match.get("metadata", {}).get("filename", "unknown")
            if filename not in seen_filenames:
                diverse_matches.append(match)
                seen_filenames.add(filename)
            if len(diverse_matches) >= desired:
                break

    # Extract metadata from the diverse matches for the prompt context.
    diverse_chunks = [match["metadata"] for match in diverse_matches]

    # Build the context by concatenating the text from each chunk.
    context_text = "\n\n".join([f"Source: {chunk['text']}" for chunk in diverse_chunks])
    prompt = f"""You are an expert assistant. Answer the following question based on the context provided below. Cite the source passages used.

Context:
{context_text}

Question: {question}

Answer:"""

    # Query the LLM (using OpenAI ChatCompletion)
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
    return {"answer": answer, "sources": diverse_chunks}



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
