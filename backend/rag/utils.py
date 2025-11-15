"""
RAG utility functions
"""
from typing import List
import openai
import tiktoken
from backend.config import settings


def get_embeddings(texts: List[str], model: str = None) -> List[List[float]]:
    """Get embeddings for a list of texts using OpenAI"""
    if model is None:
        model = settings.embedding_model
    
    # Check if API key is provided
    api_key = settings.openai_api_key
    if not api_key or not api_key.strip():
        raise ValueError("OpenAI API key not configured. Please set OPENAI_API_KEY in .env file")
    
    # Only pass api_key parameter if it's valid
    client = openai.OpenAI(api_key=api_key.strip())
    
    # Process in batches to handle rate limits
    embeddings = []
    batch_size = 100
    
    try:
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            response = client.embeddings.create(
                model=model,
                input=batch
            )
            batch_embeddings = [item.embedding for item in response.data]
            embeddings.extend(batch_embeddings)
        
        return embeddings
    except Exception as e:
        error_str = str(e)
        # Check for quota errors
        if 'quota' in error_str.lower() or 'insufficient_quota' in error_str.lower() or 'exceeded' in error_str.lower():
            raise ValueError(f"OpenAI API quota exceeded. Please check your billing at https://platform.openai.com/account/billing. Error: {error_str}")
        # Re-raise other errors
        raise


def chunk_text_by_tokens(
    text: str,
    chunk_size: int = 800,
    overlap: int = 100,
    model_name: str = "gpt-4o"
) -> List[str]:
    """Split text into overlapping chunks using tiktoken for token-based chunking"""
    try:
        # Get the encoding for the model
        encoding = tiktoken.encoding_for_model(model_name)
    except KeyError:
        # Fallback to cl100k_base encoding (used by GPT-4)
        encoding = tiktoken.get_encoding("cl100k_base")
    
    # Encode text into tokens
    tokens = encoding.encode(text)
    
    # Split into chunks
    chunks = []
    start_idx = 0
    
    while start_idx < len(tokens):
        # Get chunk tokens
        end_idx = min(start_idx + chunk_size, len(tokens))
        chunk_tokens = tokens[start_idx:end_idx]
        
        # Decode chunk tokens back to text
        chunk_text = encoding.decode(chunk_tokens)
        chunks.append(chunk_text)
        
        # Move start index with overlap
        start_idx += chunk_size - overlap
        
        # Prevent infinite loop
        if start_idx >= len(tokens):
            break
    
    return chunks


def chunk_text(text: str, chunk_size: int = None, overlap: int = None) -> List[str]:
    """Split text into overlapping chunks (using token-based chunking)"""
    if chunk_size is None:
        chunk_size = settings.chunk_size
    if overlap is None:
        overlap = settings.chunk_overlap
    
    # Use token-based chunking for better quality
    model_name = settings.openai_model
    try:
        return chunk_text_by_tokens(text, chunk_size, overlap, model_name)
    except Exception as e:
        # Fallback to character-based chunking if tiktoken fails
        print(f"Warning: Token-based chunking failed, using character-based: {e}")
        return _chunk_text_characters(text, chunk_size, overlap)


def _chunk_text_characters(text: str, chunk_size: int, overlap: int) -> List[str]:
    """Fallback character-based chunking"""
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        
        # Try to break at sentence boundary if not at end
        if end < len(text):
            # Look for sentence endings
            for punct in ['. ', '.\n', '! ', '!\n', '? ', '?\n']:
                last_punct = chunk.rfind(punct)
                if last_punct > chunk_size * 0.5:  # Only break if we're past halfway
                    chunk = chunk[:last_punct + 1]
                    end = start + len(chunk)
                    break
        
        chunks.append(chunk.strip())
        start = end - overlap  # Overlap for context
    
    return chunks
