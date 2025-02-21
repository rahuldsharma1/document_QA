import fitz  # PyMuPDF
import nltk
from nltk.tokenize import sent_tokenize
import tiktoken

nltk.download('punkt', quiet=True)  # Ensure 'punkt' is downloaded
nltk.download('punkt_tab')

def extract_text_from_pdf(file_path: str) -> str:
    """Extracts text from a PDF file."""
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def semantic_chunk_text(text: str, max_tokens: int = 300, model_name: str = "text-embedding-ada-002") -> list:
    """
    Splits text into semantically coherent chunks by sentences,
    ensuring each chunk is at most max_tokens (approx).
    """
    encoding = tiktoken.encoding_for_model(model_name)
    sentences = sent_tokenize(text)
    chunks = []
    current_chunk = ""

    for sentence in sentences:
        tentative = (current_chunk + " " + sentence).strip() if current_chunk else sentence
        token_count = len(encoding.encode(tentative))
        if token_count > max_tokens and current_chunk:
            # finalize the current chunk
            chunks.append(current_chunk.strip())
            current_chunk = sentence  # start a new chunk
        else:
            current_chunk = tentative

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks
