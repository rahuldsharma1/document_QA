import os
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)

logging.info("Initializing Pinecone...")

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
    logging.info(f"Creating index: {INDEX_NAME}")
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
    logging.info(f"Upserting embedding for doc_id: {doc_id}, chunk_index: {chunk_index}")
    vector_id = f"{doc_id}_{chunk_index}"
    metadata = {
        "text": text,
        "filename": filename,
        "chunk_index": chunk_index,
    }
    index.upsert(vectors=[(vector_id, embedding, metadata)])
    logging.info("Embedding upserted successfully.")

def query_pinecone(query_embedding: list, top_k: int = 10):
    """
    Queries Pinecone for the top_k most similar vectors.
    """
    logging.info("Querying Pinecone...")
    result = index.query(vector=query_embedding, top_k=top_k, include_metadata=True)
    logging.info("Query successful.")
    return result.get("matches", [])

