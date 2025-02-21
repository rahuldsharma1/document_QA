from openai import OpenAI

from dotenv import load_dotenv
import os
import logging

logging.basicConfig(level=logging.INFO)

# Load .env file
load_dotenv()

# Get openAI key
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_embedding(text: str, model: str = "text-embedding-ada-002") -> list:
    """
    Returns an embedding for a given text using OpenAI's API.
    """
    logging.info("Getting embedding...")
    response = client.embeddings.create(input=[text], model=model)
    logging.info("Embedding retrieved successfully.")
    return response.data[0].embedding