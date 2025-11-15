"""
LangChain-based RAG chain for financial document Q&A
"""
from typing import List, Dict, Tuple, Optional, Any
from pathlib import Path
import os

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate
from langchain_core.documents import Document

from backend.config import settings


def get_faiss_index_path(ticker: str, filing_type: str, year: int) -> Path:
    """Get path to FAISS index for a specific ticker/filing/year"""
    base_path = settings.get_vector_db_path()
    index_path = base_path / f"{ticker}_{filing_type}_{year}"
    return index_path


def load_faiss_index(ticker: str, filing_type: str, year: int) -> Optional[FAISS]:
    """Load FAISS index for a specific ticker/filing/year"""
    index_path = get_faiss_index_path(ticker, filing_type, year)
    
    if not index_path.exists():
        return None
    
    try:
        # Initialize embeddings
        embeddings = OpenAIEmbeddings(
            openai_api_key=settings.openai_api_key,
            model=settings.embedding_model
        )
        
        # Load FAISS index
        vectorstore = FAISS.load_local(
            str(index_path),
            embeddings,
            allow_dangerous_deserialization=True
        )
        
        return vectorstore
    except Exception as e:
        print(f"Error loading FAISS index: {e}")
        return None


def get_qa_chain(
    ticker: str,
    filing_type: str,
    year: int,
    top_k: int = 5
) -> Optional[RetrievalQA]:
    """Get QA chain for a specific ticker/filing/year"""
    
    # Check if API key is configured
    if not settings.openai_api_key or not settings.openai_api_key.strip():
        raise ValueError("OpenAI API key not configured. Please set OPENAI_API_KEY in .env file")
    
    # Load FAISS index
    vectorstore = load_faiss_index(ticker, filing_type, year)
    if vectorstore is None:
        return None
    
    # Initialize LLM
    llm = ChatOpenAI(
        openai_api_key=settings.openai_api_key,
        model=settings.openai_model,
        temperature=settings.openai_temperature,
        max_tokens=settings.openai_max_tokens
    )
    
    # Create retriever
    retriever = vectorstore.as_retriever(
        search_kwargs={"k": top_k}
    )
    
    # Create QA prompt template
    qa_prompt = PromptTemplate(
        template="""You are a financial analyst assistant. Answer the question based only on the provided context from SEC filings.

Context: {context}

Question: {question}

Answer: Provide a clear, concise answer based solely on the context. If the answer is not in the context, say "I cannot find this information in the provided documents."

""",
        input_variables=["context", "question"]
    )
    
    # Create QA chain
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        chain_type_kwargs={"prompt": qa_prompt},
        return_source_documents=True
    )
    
    return qa_chain


def answer_question_with_rag(
    ticker: str,
    filing_type: str,
    year: int,
    question: str,
    top_k: int = 5
) -> Dict[str, Any]:
    """Answer question using RAG for a specific ticker/filing/year"""
    
    # Get QA chain
    qa_chain = get_qa_chain(ticker, filing_type, year, top_k)
    if qa_chain is None:
        raise ValueError(
            f"No index found for {ticker} {filing_type} {year}. "
            "Please ingest the document first."
        )
    
    # Run QA chain
    result = qa_chain.invoke({"query": question})
    
    # Extract answer and sources
    answer = result.get("result", "")
    source_documents = result.get("source_documents", [])
    
    # Extract source filenames
    sources = []
    for doc in source_documents:
        if hasattr(doc, "metadata") and "source" in doc.metadata:
            source_path = doc.metadata["source"]
            source_filename = Path(source_path).name
            sources.append(source_filename)
    
    return {
        "answer": answer if answer else "No answer generated",
        "sources": list(set(sources)) if sources else [],  # Remove duplicates
        "ticker": ticker,
        "filing_type": filing_type,
        "year": year
    }


def retrieve_filing_section(
    ticker: str,
    filing_type: str,
    year: int,
    section_hint: str,
    top_k: int = 3
) -> List[Document]:
    """Retrieve relevant filing section based on hint"""
    
    # Load FAISS index
    vectorstore = load_faiss_index(ticker, filing_type, year)
    if vectorstore is None:
        return []
    
    # Retrieve relevant documents
    docs = vectorstore.similarity_search(section_hint, k=top_k)
    
    return docs

