"""
Document ingestion for RAG pipeline
"""
from typing import List, Dict, Tuple
from pathlib import Path
import re
from backend.rag.utils import chunk_text


def extract_text_from_file(file_path: str) -> str:
    """Extract text from file (supports .txt and basic .pdf)"""
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if path.suffix.lower() == '.txt':
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
            if not text.strip():
                raise ValueError("File appears to be empty")
            return text
        except Exception as e:
            raise ValueError(f"Error reading text file: {str(e)}")
    elif path.suffix.lower() == '.pdf':
        try:
            import pdfplumber
            text = ""
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text() or ""
                    text += page_text
            if not text.strip():
                raise ValueError("PDF appears to be empty or contains no extractable text")
            return text
        except ImportError:
            raise ImportError("pdfplumber is required for PDF processing. Install with: pip install pdfplumber")
        except Exception as e:
            error_msg = str(e) if str(e) else "Unknown error"
            raise ValueError(f"Error extracting text from PDF: {error_msg}")
    else:
        # Try as text file
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
            if not text.strip():
                raise ValueError(f"File appears to be empty or unsupported format: {path.suffix}")
            return text
        except Exception as e:
            raise ValueError(f"Error reading file: {str(e)}")


def clean_text(text: str) -> str:
    """Clean extracted text"""
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove special characters that might interfere
    text = re.sub(r'\x00', '', text)
    return text.strip()


def ingest_sec_filing(file_path: str, chunk_size: int = None, overlap: int = None) -> Tuple[List[str], Dict]:
    """Ingest SEC filing and split into chunks"""
    text = extract_text_from_file(file_path)
    text = clean_text(text)
    
    # Extract metadata from filename or text
    path = Path(file_path)
    metadata = {
        "filename": path.name,
        "file_type": "SEC_FILING",
        "source": str(path)
    }
    
    # Try to extract company name and filing type from filename
    # Common pattern: COMPANY_10-K_2023.txt
    filename_parts = path.stem.split('_')
    if len(filename_parts) >= 2:
        metadata["filing_type"] = filename_parts[1] if filename_parts[1] in ['10-K', '10-Q', '8-K'] else "UNKNOWN"
    
    chunks = chunk_text(text, chunk_size=chunk_size, overlap=overlap)
    return chunks, metadata


def ingest_transcript(file_path: str, chunk_size: int = None, overlap: int = None) -> Tuple[List[str], Dict]:
    """Ingest earnings transcript"""
    text = extract_text_from_file(file_path)
    text = clean_text(text)
    
    path = Path(file_path)
    metadata = {
        "filename": path.name,
        "file_type": "TRANSCRIPT",
        "source": str(path)
    }
    
    chunks = chunk_text(text, chunk_size=chunk_size, overlap=overlap)
    return chunks, metadata


def ingest_news(file_path: str, chunk_size: int = None, overlap: int = None) -> Tuple[List[str], Dict]:
    """Ingest news articles"""
    text = extract_text_from_file(file_path)
    text = clean_text(text)
    
    path = Path(file_path)
    metadata = {
        "filename": path.name,
        "file_type": "NEWS",
        "source": str(path)
    }
    
    chunks = chunk_text(text, chunk_size=chunk_size, overlap=overlap)
    return chunks, metadata


def ingest_document(file_path: str, doc_type: str = "auto", chunk_size: int = None, overlap: int = None) -> Tuple[List[str], Dict]:
    """Ingest document with automatic type detection"""
    if doc_type == "auto":
        path = Path(file_path)
        filename_lower = path.name.lower()
        if any(x in filename_lower for x in ['10-k', '10-q', '8-k', 'filing']):
            doc_type = "filing"
        elif any(x in filename_lower for x in ['transcript', 'earnings', 'call']):
            doc_type = "transcript"
        else:
            doc_type = "news"
    
    if doc_type == "filing":
        return ingest_sec_filing(file_path, chunk_size, overlap)
    elif doc_type == "transcript":
        return ingest_transcript(file_path, chunk_size, overlap)
    else:
        return ingest_news(file_path, chunk_size, overlap)

