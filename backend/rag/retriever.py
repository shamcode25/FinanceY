"""
RAG retriever using FAISS
"""
from typing import List, Dict, Optional
from pathlib import Path
import faiss
import numpy as np
import pickle
import json
from backend.config import settings


class RAGRetriever:
    """Retriever for RAG pipeline using FAISS"""
    
    def __init__(self, vector_db_path: str = None):
        if vector_db_path is None:
            vector_db_path = settings.vector_db_path
        self.vector_db_path = Path(vector_db_path)
        self.vector_db_path.mkdir(parents=True, exist_ok=True)
        
        self.index = None
        self.documents: List[str] = []
        self.metadata: List[Dict] = []
        self.dimension = settings.embedding_dimension
    
    def build_index(self, embeddings: np.ndarray, documents: List[str], metadata: List[Dict] = None):
        """Build FAISS index from embeddings"""
        if len(embeddings) == 0:
            raise ValueError("Cannot build index with empty embeddings")
        
        embeddings_array = np.array(embeddings).astype('float32')
        dimension = embeddings_array.shape[1]
        self.dimension = dimension
        
        # Create FAISS index
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(embeddings_array)
        
        self.documents = documents
        self.metadata = metadata if metadata else [{}] * len(documents)
        
        if len(self.metadata) != len(self.documents):
            self.metadata = [{}] * len(self.documents)
    
    def retrieve(self, query_embedding: np.ndarray, k: int = None) -> List[Dict]:
        """Retrieve top-k similar documents"""
        if self.index is None or len(self.documents) == 0:
            return []
        
        if k is None:
            k = settings.top_k_retrieval
        
        k = min(k, len(self.documents))
        
        query_array = np.array([query_embedding]).astype('float32')
        distances, indices = self.index.search(query_array, k)
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.documents):
                results.append({
                    "text": self.documents[idx],
                    "metadata": self.metadata[idx] if idx < len(self.metadata) else {},
                    "distance": float(distances[0][i])
                })
        
        return results
    
    def add_documents(self, embeddings: np.ndarray, documents: List[str], metadata: List[Dict] = None):
        """Add documents to existing index"""
        if self.index is None:
            self.build_index(embeddings, documents, metadata)
            return
        
        embeddings_array = np.array(embeddings).astype('float32')
        self.index.add(embeddings_array)
        self.documents.extend(documents)
        
        if metadata:
            self.metadata.extend(metadata)
        else:
            self.metadata.extend([{}] * len(documents))
    
    def save(self, path: str = None):
        """Save index and documents to disk"""
        if path is None:
            path = self.vector_db_path / "index"
        else:
            path = Path(path)
        
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        if self.index is not None:
            faiss.write_index(self.index, str(path) + ".faiss")
        
        # Save documents and metadata
        data = {
            "documents": self.documents,
            "metadata": self.metadata,
            "dimension": self.dimension
        }
        
        with open(str(path) + ".pkl", "wb") as f:
            pickle.dump(data, f)
    
    def load(self, path: str = None):
        """Load index and documents from disk"""
        if path is None:
            path = self.vector_db_path / "index"
        else:
            path = Path(path)
        
        index_path = Path(str(path) + ".faiss")
        data_path = Path(str(path) + ".pkl")
        
        if not index_path.exists() or not data_path.exists():
            raise FileNotFoundError(f"Index files not found at {path}")
        
        # Load FAISS index
        self.index = faiss.read_index(str(index_path))
        
        # Load documents and metadata
        with open(str(data_path), "rb") as f:
            data = pickle.load(f)
        
        self.documents = data["documents"]
        self.metadata = data.get("metadata", [{}] * len(self.documents))
        self.dimension = data.get("dimension", settings.embedding_dimension)
    
    def get_stats(self) -> Dict:
        """Get statistics about the index"""
        return {
            "num_documents": len(self.documents),
            "dimension": self.dimension,
            "index_exists": self.index is not None
        }

