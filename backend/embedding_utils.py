from openai import OpenAI

from dotenv import load_dotenv
import os

# Load .env file
load_dotenv()

# Get openAI key
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_embedding(text: str, model: str = "text-embedding-ada-002") -> list:
    """
    Returns an embedding for a given text using OpenAI's API.
    """
    response = client.embeddings.create(input=[text], model=model)
    return response.data[0].embedding