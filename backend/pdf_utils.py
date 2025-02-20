import fitz  # PyMuPDF
import tiktoken

def extract_text_from_pdf(file_path: str) -> str:
    """Extracts text from a PDF file."""
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text


# NEED TO FIX THIS TO SEMANTICALLY CHUNK TEXT, FOR NOW WE LEAVE WITH JUST SPLITTING BY PARAGRAPH
def chunk_text(text: str, max_tokens: int = 300, model_name: str = "text-embedding-ada-002") -> list:
    encoding = tiktoken.encoding_for_model(model_name)
    tokens = encoding.encode(text)
    chunks = []
    current_tokens = []
    
    for token in tokens:
        if len(current_tokens) + 1 > max_tokens:
            chunk_str = encoding.decode(current_tokens)
            if chunk_str.strip():
                chunks.append(chunk_str.strip())
            current_tokens = [token]
        else:
            current_tokens.append(token)
    
    if current_tokens:
        chunk_str = encoding.decode(current_tokens)
        if chunk_str.strip():
            chunks.append(chunk_str.strip())
    
    return chunks
