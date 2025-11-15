"""
FastAPI backend for FinanceY
"""
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional
from pathlib import Path
import shutil
from datetime import datetime
import numpy as np

from backend.config import settings
from backend.llm.agent import FinOpsAgent
from backend.llm.rag_chain import answer_question_with_rag
from backend.llm.kpi_extraction import extract_kpis_from_filing, kpi_dataframe_to_json
from backend.llm.financial_agent import run_financial_agent
from backend.rag.ingest import ingest_document
from backend.rag.retriever import RAGRetriever
from backend.rag.utils import get_embeddings, chunk_text
from backend.models.schemas import (
    # New models
    IngestRequest, QARequest, QAResponse, KPIRequest, KPIResponse,
    RiskRequest, RiskResponse, MemoRequest, MemoResponse, AgentRequest, AgentResponse,
    # Legacy models (for backward compatibility)
    QueryRequest, QueryResponse, KPIExtraction, RiskSummary,
    FilingComparison, InvestmentMemo, ExtractKPIsRequest, SummarizeRisksRequest
)

app = FastAPI(
    title="FinanceY API",
    version="0.1.0",
    description="AI-powered financial document analysis"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
agent = FinOpsAgent()
retriever = RAGRetriever()

# Try to load existing index
try:
    retriever.load()
except FileNotFoundError:
    pass  # Index doesn't exist yet, will be created on first upload


@app.get("/")
async def root():
    """API root endpoint with information about available endpoints"""
    return {
        "message": "FinanceY API",
        "version": "0.1.0",
        "endpoints": {
            "health": "/health",
            "upload": "/upload",
            "query": "/query (legacy)",
            "qa": "/qa (new)",
            "kpis": "/kpis (new)",
            "risks": "/risks (new)",
            "memo": "/memo (new)",
            "agent": "/agent (new)",
            "extract-kpis": "/extract-kpis (legacy)",
            "summarize-risks": "/summarize-risks (legacy)",
            "generate-memo": "/generate-memo (legacy)",
            "stats": "/stats"
        },
        "docs": "/docs"
    }


@app.get("/health", tags=["Health"])
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.post("/upload", tags=["Document Upload"])
async def upload_file(
    file: UploadFile = File(...),
    doc_type: str = Form("auto")
):
    """Upload and ingest a financial document (PDF or TXT format)
    
    - **file**: The document file to upload
    - **doc_type**: Type of document (auto, filing, transcript, news)
    
    Returns status, filename, number of chunks, and metadata.
    """
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        # Save uploaded file
        upload_dir = settings.get_filings_path()
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = upload_dir / file.filename
        
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            raise HTTPException(
                status_code=500, 
                detail=f"Error saving file: {str(e) if str(e) else 'Failed to save file to disk'}"
            )
        
        # Ingest document
        try:
            chunks, metadata = ingest_document(str(file_path), doc_type=doc_type)
        except ImportError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Missing dependency: {str(e)}. Please install required packages: pip install pdfplumber"
            )
        except Exception as e:
            error_msg = str(e) if str(e) else "Unknown error during document ingestion"
            raise HTTPException(
                status_code=500,
                detail=f"Error extracting text from file: {error_msg}. Make sure the file is a valid PDF or text file."
            )
        
        if not chunks:
            raise HTTPException(
                status_code=400, 
                detail="No content extracted from file. The file may be empty, corrupted, or in an unsupported format."
            )
        
        # Generate embeddings
        try:
            embeddings = get_embeddings(chunks)
            embeddings_array = np.array(embeddings)
        except ValueError as e:
            # API key not configured
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            # Other errors (e.g., API errors, network errors)
            error_msg = str(e) if str(e) else "Unknown error during embedding generation"
            error_str = str(e)
            
            # Check for quota errors
            if 'quota' in error_str.lower() or 'insufficient_quota' in error_str.lower() or 'exceeded' in error_str.lower():
                raise HTTPException(
                    status_code=429,
                    detail=f"OpenAI API quota exceeded. {error_msg}. Please check your billing at https://platform.openai.com/account/billing"
                )
            
            raise HTTPException(
                status_code=500, 
                detail=f"Error generating embeddings: {error_msg}. Check your OpenAI API key and network connection."
            )
        
        # Add to retriever
        try:
            metadata_list = [metadata] * len(chunks)
            if retriever.index is None:
                retriever.build_index(embeddings_array, chunks, metadata_list)
            else:
                retriever.add_documents(embeddings_array, chunks, metadata_list)
            
            # Save index
            retriever.save()
        except Exception as e:
            error_msg = str(e) if str(e) else "Unknown error during index update"
            raise HTTPException(
                status_code=500,
                detail=f"Error updating search index: {error_msg}"
            )
        
        return {
            "status": "success",
            "filename": file.filename,
            "chunks": len(chunks),
            "metadata": metadata
        }
    
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Catch-all for unexpected errors
        import traceback
        error_detail = str(e) if str(e) else "Unknown error occurred"
        error_trace = traceback.format_exc()
        print(f"Unexpected error in upload_file: {error_detail}\n{error_trace}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error processing file: {error_detail}. Please check the file format and try again."
        )


@app.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """Ask questions about uploaded documents using RAG"""
    try:
        if retriever.index is None or len(retriever.documents) == 0:
            raise HTTPException(
                status_code=400,
                detail="No documents uploaded. Please upload documents first."
            )
        
        # Get query embedding
        try:
            query_embeddings = get_embeddings([request.question])
        except ValueError as e:
            # API key not configured
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            # Other errors
            raise HTTPException(status_code=500, detail=f"Error generating query embeddings: {str(e)}")
        query_embedding = np.array(query_embeddings[0])
        
        # Retrieve relevant chunks
        results = retriever.retrieve(query_embedding, k=settings.top_k_retrieval)
        
        if not results:
            return QueryResponse(
                answer="No relevant information found in the documents.",
                sources=[]
            )
        
        # Combine retrieved context
        context = "\n\n".join([r["text"] for r in results])
        sources = [r["metadata"].get("filename", "Unknown") for r in results]
        
        # Answer question using agent
        answer = agent.answer_question(request.question, context)
        
        return QueryResponse(
            answer=answer,
            sources=list(set(sources))  # Remove duplicates
        )
    
    except ValueError as e:
        # API key not configured
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        error_detail = str(e) if str(e) else "Unknown error occurred"
        raise HTTPException(status_code=500, detail=f"Error processing query: {error_detail}")


@app.post("/extract-kpis")
async def extract_kpis(request: ExtractKPIsRequest):
    """Extract KPIs from a document"""
    try:
        if request.document_text:
            text = request.document_text
        elif request.file_path:
            from backend.rag.ingest import extract_text_from_file
            text = extract_text_from_file(request.file_path)
        else:
            raise HTTPException(
                status_code=400,
                detail="Either file_path or document_text must be provided"
            )
        
        kpis = agent.extract_kpis(text)
        
        return {
            "status": "success",
            "kpis": kpis
        }
    
    except ValueError as e:
        # API key not configured
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        error_detail = str(e) if str(e) else "Unknown error occurred"
        raise HTTPException(status_code=500, detail=f"Error extracting KPIs: {error_detail}")


@app.post("/summarize-risks", response_model=RiskSummary)
async def summarize_risks(request: SummarizeRisksRequest):
    """Summarize risks from a document"""
    try:
        if request.document_text:
            text = request.document_text
        elif request.file_path:
            from backend.rag.ingest import extract_text_from_file
            text = extract_text_from_file(request.file_path)
        else:
            raise HTTPException(
                status_code=400,
                detail="Either file_path or document_text must be provided"
            )
        
        risks = agent.summarize_risks(text)
        
        return RiskSummary(**risks)
    
    except ValueError as e:
        # API key not configured
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        error_detail = str(e) if str(e) else "Unknown error occurred"
        raise HTTPException(status_code=500, detail=f"Error summarizing risks: {error_detail}")


@app.post("/compare-filings")
async def compare_filings(
    file_path1: str,
    file_path2: str,
    period1: str = "Period 1",
    period2: str = "Period 2"
):
    """Compare two filings"""
    try:
        from backend.rag.ingest import extract_text_from_file
        
        filing1_text = extract_text_from_file(file_path1)
        filing2_text = extract_text_from_file(file_path2)
        
        comparison = agent.compare_filings(
            filing1_text,
            filing2_text,
            period1=period1,
            period2=period2
        )
        
        return {
            "status": "success",
            "comparison": comparison
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error comparing filings: {str(e)}")


@app.post("/generate-memo")
async def generate_memo(
    company_name: str,
    period: str,
    file_path: Optional[str] = None,
    kpis: Optional[dict] = None,
    risks: Optional[dict] = None
):
    """Generate investment memo"""
    try:
        context = {
            "company_name": company_name,
            "period": period,
            "kpis": kpis or {},
            "risks": risks or {},
            "context": ""
        }
        
        # If file_path provided, extract KPIs and risks
        if file_path:
            from backend.rag.ingest import extract_text_from_file
            text = extract_text_from_file(file_path)
            
            if not kpis:
                context["kpis"] = agent.extract_kpis(text)
            if not risks:
                context["risks"] = agent.summarize_risks(text)
            context["context"] = text[:10000]  # First 10k chars for context
        
        memo_text = agent.generate_memo(context)
        
        return {
            "status": "success",
            "memo": memo_text,
            "company_name": company_name,
            "period": period,
            "generated_at": datetime.now().isoformat()
        }
    
    except ValueError as e:
        # API key not configured
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        error_detail = str(e) if str(e) else "Unknown error occurred"
        raise HTTPException(status_code=500, detail=f"Error generating memo: {error_detail}")


@app.get("/stats", tags=["Statistics"])
async def get_stats():
    """Get statistics about the vector database and settings"""
    stats = retriever.get_stats()
    return {
        "retriever": stats,
        "settings": {
            "embedding_model": settings.embedding_model,
            "chunk_size": settings.chunk_size,
            "top_k_retrieval": settings.top_k_retrieval
        }
    }


# New endpoints with structured models and LangChain RAG
@app.post("/qa", response_model=QAResponse, tags=["Q&A"])
async def qa_endpoint(request: QARequest):
    """Answer questions about financial documents using LangChain RAG
    
    - **ticker**: Company ticker symbol (e.g., AAPL)
    - **filing_type**: Type of filing (10-K, 10-Q, 8-K, etc.)
    - **year**: Year of the filing
    - **question**: Question to answer
    - **top_k**: Number of chunks to retrieve (default: 5)
    
    Returns answer with source citations.
    """
    try:
        result = answer_question_with_rag(
            ticker=request.ticker,
            filing_type=request.filing_type,
            year=request.year,
            question=request.question,
            top_k=request.top_k or 5
        )
        
        return QAResponse(**result)
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        error_detail = str(e) if str(e) else "Unknown error occurred"
        raise HTTPException(status_code=500, detail=f"Error processing QA request: {error_detail}")


@app.post("/kpis", response_model=KPIResponse, tags=["KPI Extraction"])
async def kpis_endpoint(request: KPIRequest):
    """Extract KPIs from financial documents using Pandas
    
    - **ticker**: Company ticker symbol (e.g., AAPL)
    - **filing_type**: Type of filing (10-K, 10-Q, 8-K, etc.)
    - **year**: Year of the filing
    
    Returns extracted KPIs as a structured response with metrics.
    """
    try:
        # Extract KPIs using Pandas-based extraction
        df = extract_kpis_from_filing(
            ticker=request.ticker,
            filing_type=request.filing_type,
            year=request.year
        )
        
        # Convert DataFrame to JSON response
        result = kpi_dataframe_to_json(df)
        
        return KPIResponse(
            ticker=request.ticker,
            filing_type=request.filing_type,
            year=request.year,
            kpis=result["kpis"],
            metrics=result["metrics"]
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        error_detail = str(e) if str(e) else "Unknown error occurred"
        raise HTTPException(status_code=500, detail=f"Error extracting KPIs: {error_detail}")


@app.post("/risks", response_model=RiskResponse, tags=["Risk Analysis"])
async def risks_endpoint(request: RiskRequest):
    """Summarize risks from financial documents
    
    - **ticker**: Company ticker symbol (e.g., AAPL)
    - **filing_type**: Type of filing (10-K, 10-Q, 8-K, etc.)
    - **year**: Year of the filing
    
    Returns categorized risks.
    """
    try:
        # Retrieve risk factors section
        from backend.llm.rag_chain import retrieve_filing_section
        from backend.llm.agent import FinOpsAgent
        
        docs = retrieve_filing_section(
            ticker=request.ticker,
            filing_type=request.filing_type,
            year=request.year,
            section_hint="risk factors",
            top_k=5
        )
        
        if not docs:
            raise ValueError(f"No content found for {request.ticker} {request.filing_type} {request.year}")
        
        # Combine document content
        text = "\n\n".join([
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ])
        
        # Summarize risks using agent
        agent = FinOpsAgent()
        risks = agent.summarize_risks(text)
        
        # Format response
        return RiskResponse(
            ticker=request.ticker,
            filing_type=request.filing_type,
            year=request.year,
            risks=risks,
            summary=f"Identified {sum(len(v) for v in risks.values())} risks across {len([k for k, v in risks.items() if v])} categories"
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        error_detail = str(e) if str(e) else "Unknown error occurred"
        raise HTTPException(status_code=500, detail=f"Error summarizing risks: {error_detail}")


@app.post("/memo", response_model=MemoResponse, tags=["Investment Memo"])
async def memo_endpoint(request: MemoRequest):
    """Generate investment memo from financial documents
    
    - **ticker**: Company ticker symbol (e.g., AAPL)
    - **filing_type**: Type of filing (10-K, 10-Q, 8-K, etc.)
    - **year**: Year of the filing
    
    Returns comprehensive investment memo.
    """
    try:
        # Extract KPIs and risks
        from backend.llm.kpi_extraction import extract_kpis_from_filing, kpi_dataframe_to_json
        from backend.llm.rag_chain import retrieve_filing_section
        from backend.llm.agent import FinOpsAgent
        
        # Extract KPIs
        df = extract_kpis_from_filing(
            ticker=request.ticker,
            filing_type=request.filing_type,
            year=request.year
        )
        kpis_result = kpi_dataframe_to_json(df)
        
        # Extract risks
        docs = retrieve_filing_section(
            ticker=request.ticker,
            filing_type=request.filing_type,
            year=request.year,
            section_hint="risk factors",
            top_k=5
        )
        text = "\n\n".join([
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ])
        agent = FinOpsAgent()
        risks = agent.summarize_risks(text)
        
        # Generate memo
        context = {
            "company_name": request.ticker,
            "period": f"{request.year} {request.filing_type}",
            "kpis": kpis_result["metrics"],
            "risks": risks,
            "context": text[:10000]  # First 10k chars for context
        }
        
        memo_text = agent.generate_memo(context)
        
        # Parse memo into sections (simple parsing)
        memo_sections = {
            "executive_summary": "",
            "company_overview": "",
            "financial_performance": "",
            "key_risks": "",
            "investment_thesis": "",
            "recommendation": ""
        }
        
        # Simple section extraction (can be improved)
        sections = memo_text.split("\n\n")
        current_section = "executive_summary"
        for section in sections:
            section_lower = section.lower()
            if "executive summary" in section_lower:
                current_section = "executive_summary"
            elif "company overview" in section_lower or "company" in section_lower:
                current_section = "company_overview"
            elif "financial" in section_lower or "performance" in section_lower:
                current_section = "financial_performance"
            elif "risk" in section_lower:
                current_section = "key_risks"
            elif "thesis" in section_lower or "investment" in section_lower:
                current_section = "investment_thesis"
            elif "recommendation" in section_lower:
                current_section = "recommendation"
            
            if memo_sections[current_section]:
                memo_sections[current_section] += "\n\n" + section
            else:
                memo_sections[current_section] = section
        
        return MemoResponse(
            ticker=request.ticker,
            filing_type=request.filing_type,
            year=request.year,
            memo=memo_sections,
            generated_at=datetime.now()
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        error_detail = str(e) if str(e) else "Unknown error occurred"
        raise HTTPException(status_code=500, detail=f"Error generating memo: {error_detail}")


@app.post("/agent", response_model=AgentResponse, tags=["Agent"])
async def agent_endpoint(request: AgentRequest):
    """Run agentic workflow for financial analysis
    
    - **task**: High-level task description (e.g., "Generate investment memo for AAPL 2023 10-K")
    - **ticker**: Company ticker symbol (e.g., AAPL)
    - **filing_type**: Type of filing (10-K, 10-Q, 8-K, etc.)
    - **year**: Year of the filing
    
    Returns task result and execution steps.
    """
    try:
        result = run_financial_agent(
            task=request.task,
            ticker=request.ticker,
            filing_type=request.filing_type,
            year=request.year
        )
        
        return AgentResponse(**result)
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        error_detail = str(e) if str(e) else "Unknown error occurred"
        raise HTTPException(status_code=500, detail=f"Error running agent: {error_detail}")


# Legacy endpoints (for backward compatibility)
@app.post("/query", response_model=QueryResponse, tags=["Legacy"])
async def query_documents(request: QueryRequest):
    """Ask questions about uploaded documents using RAG (legacy endpoint)"""
    try:
        if retriever.index is None or len(retriever.documents) == 0:
            raise HTTPException(
                status_code=400,
                detail="No documents uploaded. Please upload documents first."
            )
        
        # Get query embedding
        try:
            query_embeddings = get_embeddings([request.question])
        except ValueError as e:
            # API key not configured
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            # Other errors
            raise HTTPException(status_code=500, detail=f"Error generating query embeddings: {str(e)}")
        query_embedding = np.array(query_embeddings[0])
        
        # Retrieve relevant chunks
        results = retriever.retrieve(query_embedding, k=settings.top_k_retrieval)
        
        if not results:
            return QueryResponse(
                answer="No relevant information found in the documents.",
                sources=[]
            )
        
        # Combine retrieved context
        context = "\n\n".join([r["text"] for r in results])
        sources = [r["metadata"].get("filename", "Unknown") for r in results]
        
        # Answer question using agent
        answer = agent.answer_question(request.question, context)
        
        return QueryResponse(
            answer=answer,
            sources=list(set(sources))  # Remove duplicates
        )
    
    except ValueError as e:
        # API key not configured
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        error_detail = str(e) if str(e) else "Unknown error occurred"
        raise HTTPException(status_code=500, detail=f"Error processing query: {error_detail}")


@app.post("/extract-kpis", tags=["Legacy"])
async def extract_kpis(request: ExtractKPIsRequest):
    """Extract KPIs from a document (legacy endpoint)"""
    try:
        if request.document_text:
            text = request.document_text
        elif request.file_path:
            from backend.rag.ingest import extract_text_from_file
            text = extract_text_from_file(request.file_path)
        else:
            raise HTTPException(
                status_code=400,
                detail="Either file_path or document_text must be provided"
            )
        
        kpis = agent.extract_kpis(text)
        
        return {
            "status": "success",
            "kpis": kpis
        }
    
    except ValueError as e:
        # API key not configured
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        error_detail = str(e) if str(e) else "Unknown error occurred"
        raise HTTPException(status_code=500, detail=f"Error extracting KPIs: {error_detail}")


@app.post("/summarize-risks", response_model=RiskSummary, tags=["Legacy"])
async def summarize_risks(request: SummarizeRisksRequest):
    """Summarize risks from a document (legacy endpoint)"""
    try:
        if request.document_text:
            text = request.document_text
        elif request.file_path:
            from backend.rag.ingest import extract_text_from_file
            text = extract_text_from_file(request.file_path)
        else:
            raise HTTPException(
                status_code=400,
                detail="Either file_path or document_text must be provided"
            )
        
        risks = agent.summarize_risks(text)
        
        return RiskSummary(**risks)
    
    except ValueError as e:
        # API key not configured
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        error_detail = str(e) if str(e) else "Unknown error occurred"
        raise HTTPException(status_code=500, detail=f"Error summarizing risks: {error_detail}")


@app.post("/compare-filings", tags=["Legacy"])
async def compare_filings(
    file_path1: str,
    file_path2: str,
    period1: str = "Period 1",
    period2: str = "Period 2"
):
    """Compare two filings (legacy endpoint)"""
    try:
        from backend.rag.ingest import extract_text_from_file
        
        filing1_text = extract_text_from_file(file_path1)
        filing2_text = extract_text_from_file(file_path2)
        
        comparison = agent.compare_filings(
            filing1_text,
            filing2_text,
            period1=period1,
            period2=period2
        )
        
        return {
            "status": "success",
            "comparison": comparison
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error comparing filings: {str(e)}")


@app.post("/generate-memo", tags=["Legacy"])
async def generate_memo(
    company_name: str,
    period: str,
    file_path: Optional[str] = None,
    kpis: Optional[dict] = None,
    risks: Optional[dict] = None
):
    """Generate investment memo (legacy endpoint)"""
    try:
        context = {
            "company_name": company_name,
            "period": period,
            "kpis": kpis or {},
            "risks": risks or {},
            "context": ""
        }
        
        # If file_path provided, extract KPIs and risks
        if file_path:
            from backend.rag.ingest import extract_text_from_file
            text = extract_text_from_file(file_path)
            
            if not kpis:
                context["kpis"] = agent.extract_kpis(text)
            if not risks:
                context["risks"] = agent.summarize_risks(text)
            context["context"] = text[:10000]  # First 10k chars for context
        
        memo_text = agent.generate_memo(context)
        
        return {
            "status": "success",
            "memo": memo_text,
            "company_name": company_name,
            "period": period,
            "generated_at": datetime.now().isoformat()
        }
    
    except ValueError as e:
        # API key not configured
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        error_detail = str(e) if str(e) else "Unknown error occurred"
        raise HTTPException(status_code=500, detail=f"Error generating memo: {error_detail}")

