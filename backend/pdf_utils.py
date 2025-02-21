import fitz  # PyMuPDF
import nltk
from nltk.tokenize import sent_tokenize
import tiktoken
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure the sentence tokenizer is available
nltk.download('punkt', quiet=True)

def extract_text_from_pdf(file_path: str) -> str:
    """Extracts text from a PDF file."""
    logging.info(f"Extracting text from PDF: {file_path}")
    try:
        doc = fitz.open(file_path)
        text = "".join(page.get_text() for page in doc)
        logging.info("Text extraction successful.")
        return text
    except Exception as e:
        logging.error(f"Error extracting text from PDF: {e}")
        return ""

def semantic_chunk_text(text: str, max_tokens: int = 300, model_name: str = "text-embedding-ada-002") -> list:
    """
    Splits text into semantically coherent chunks using sentence boundaries.
    Accumulates sentences until reaching max_tokens (approximately).
    """
    logging.info("Chunking text...")
    encoding = tiktoken.encoding_for_model(model_name)
    sentences = sent_tokenize(text)
    chunks = []
    current_chunk = ""

    for sentence in sentences:
        tentative = (current_chunk + " " + sentence).strip() if current_chunk else sentence
        token_count = len(encoding.encode(tentative))
        if token_count > max_tokens and current_chunk:
            chunks.append(current_chunk.strip())
            current_chunk = sentence
        else:
            current_chunk = tentative

    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    logging.info("Text chunking successful.")
    return chunks

# For compatibility, expose chunk_text as semantic_chunk_text
def chunk_text(text: str, max_tokens: int = 300, model_name: str = "text-embedding-ada-002") -> list:
    return semantic_chunk_text(text, max_tokens, model_name)
