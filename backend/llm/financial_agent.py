"""
LangChain-based agentic workflow for financial analysis
"""
from typing import Dict, List, Any, Optional
from langchain.agents import initialize_agent, AgentType
from langchain.tools import Tool
from langchain_openai import ChatOpenAI
from langchain.schema import Document

from backend.config import settings
from backend.llm.rag_chain import retrieve_filing_section
from backend.llm.kpi_extraction import extract_kpis_from_filing, kpi_dataframe_to_json
from backend.llm.agent import FinOpsAgent


def retrieve_filing_section_tool(ticker: str, filing_type: str, year: int, section_hint: str) -> str:
    """Tool to retrieve filing section"""
    try:
        docs = retrieve_filing_section(ticker, filing_type, year, section_hint, top_k=3)
        if not docs:
            return f"No content found for section: {section_hint}"
        
        # Combine document content
        content = "\n\n".join([
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ])
        
        return content
    except Exception as e:
        return f"Error retrieving section: {str(e)}"


def extract_kpis_from_text_tool(text: str) -> str:
    """Tool to extract KPIs from text"""
    try:
        agent = FinOpsAgent()
        kpis = agent.extract_kpis(text)
        
        # Convert to JSON string
        import json
        if isinstance(kpis, dict):
            return json.dumps(kpis, indent=2)
        elif isinstance(kpis, str):
            return kpis
        else:
            return str(kpis)
    except Exception as e:
        return f"Error extracting KPIs: {str(e)}"


def summarize_risks_from_text_tool(text: str) -> str:
    """Tool to summarize risks from text"""
    try:
        agent = FinOpsAgent()
        risks = agent.summarize_risks(text)
        
        # Convert to JSON string
        import json
        if isinstance(risks, dict):
            return json.dumps(risks, indent=2)
        elif isinstance(risks, str):
            return risks
        else:
            return str(risks)
    except Exception as e:
        return f"Error summarizing risks: {str(e)}"


def generate_investment_memo_tool(kpi_json: str, risk_summary: str, context_text: str) -> str:
    """Tool to generate investment memo"""
    try:
        agent = FinOpsAgent()
        
        # Parse KPI JSON
        import json
        try:
            kpis = json.loads(kpi_json) if isinstance(kpi_json, str) else kpi_json
        except:
            kpis = {}
        
        # Combine all context
        full_context = f"""
KPIs:
{json.dumps(kpis, indent=2)}

Risks:
{risk_summary}

Context:
{context_text}
"""
        
        memo = agent.generate_memo(full_context)
        return memo
    except Exception as e:
        return f"Error generating memo: {str(e)}"


def run_financial_agent(
    task: str,
    ticker: str,
    filing_type: str,
    year: int
) -> Dict[str, Any]:
    """
    Run agentic workflow for financial analysis
    
    Args:
        task: High-level task description (e.g., "Generate investment memo for AAPL 2023 10-K")
        ticker: Company ticker symbol
        filing_type: Type of filing (10-K, 10-Q, etc.)
        year: Year of the filing
        
    Returns:
        Dictionary with task result and execution steps
    """
    # Check if API key is configured
    if not settings.openai_api_key or not settings.openai_api_key.strip():
        raise ValueError("OpenAI API key not configured. Please set OPENAI_API_KEY in .env file")
    
    # Initialize LLM
    llm = ChatOpenAI(
        openai_api_key=settings.openai_api_key,
        model=settings.openai_model,
        temperature=settings.openai_temperature,
        max_tokens=settings.openai_max_tokens
    )
    
    # Create tools
    tools = [
        Tool(
            name="retrieve_filing_section",
            func=lambda section_hint: retrieve_filing_section_tool(ticker, filing_type, year, section_hint),
            description=f"Retrieve a section from {ticker} {filing_type} {year} filing. Input should be a section hint like 'Results of Operations' or 'Risk Factors'."
        ),
        Tool(
            name="extract_kpis_from_text",
            func=extract_kpis_from_text_tool,
            description="Extract key performance indicators (KPIs) from financial text. Input should be the text to analyze."
        ),
        Tool(
            name="summarize_risks_from_text",
            func=summarize_risks_from_text_tool,
            description="Summarize risks from financial text. Input should be the text to analyze."
        ),
        Tool(
            name="generate_investment_memo",
            func=lambda kpi_json, risk_summary, context_text: generate_investment_memo_tool(kpi_json, risk_summary, context_text),
            description="Generate an investment memo from KPIs, risks, and context. Input should be three strings: KPI JSON, risk summary, and context text."
        )
    ]
    
    # Initialize agent
    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True
    )
    
    # Run agent
    try:
        result = agent.run(task)
        
        # Extract execution steps (if available)
        steps = []
        if hasattr(agent, "intermediate_steps"):
            for step in agent.intermediate_steps:
                steps.append(str(step))
        
        return {
            "task": task,
            "ticker": ticker,
            "filing_type": filing_type,
            "year": year,
            "result": {
                "output": result,
                "steps": steps
            },
            "steps": steps
        }
    except Exception as e:
        raise ValueError(f"Error running agent: {str(e)}")

