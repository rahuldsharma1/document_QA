import os
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Retrieve environment variables
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = "document-embeddings"
EMBEDDING_DIM = 1536  # Adjust based on your embedding model

# Initialize Pinecone instance using the new API
pc = Pinecone(api_key=PINECONE_API_KEY)

# Check if the index exists; if not, create it.
# The new API returns an object with a .names() method.
if INDEX_NAME not in pc.list_indexes().names():
    pc.create_index(
        name=INDEX_NAME,
        dimension=EMBEDDING_DIM,
        metric="cosine",  # or "euclidean" / "dotproduct" depending on your use case
        spec=ServerlessSpec(cloud="aws", region="us-east-1")
    )

# Connect to the index using the new client
index = pc.Index(INDEX_NAME)

def upsert_embedding(doc_id: str, chunk_index: int, embedding: list, text: str, filename: str):
    """
    Upserts an embedding into the Pinecone index.
    """
    vector_id = f"{doc_id}_{chunk_index}"
    metadata = {
        "text": text,
        "filename": filename,
        "chunk_index": chunk_index,
    }
    index.upsert(vectors=[(vector_id, embedding, metadata)])

def query_pinecone(query_embedding: list, top_k: int = 10):
    """
    Queries Pinecone for the top_k most similar vectors.
    """
    result = index.query(vector=query_embedding, top_k=top_k, include_metadata=True)
    return result.get("matches", [])

