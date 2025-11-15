"""
KPI extraction from financial documents using LLM and Pandas
"""
from typing import Dict, List, Optional
import pandas as pd
import json
from pathlib import Path

from backend.config import settings
from backend.llm.rag_chain import retrieve_filing_section
from backend.llm.agent import FinOpsAgent


def extract_kpis_from_filing(
    ticker: str,
    filing_type: str,
    year: int
) -> pd.DataFrame:
    """
    Extract KPIs from a filing and return as Pandas DataFrame
    
    Args:
        ticker: Company ticker symbol
        filing_type: Type of filing (10-K, 10-Q, etc.)
        year: Year of the filing
        
    Returns:
        DataFrame with columns: metric_name, value, unit, period, source_page, raw_text_snippet
    """
    # Initialize agent
    agent = FinOpsAgent()
    
    # Retrieve relevant sections (Results of Operations, MD&A)
    section_hints = [
        "Results of Operations",
        "Management Discussion and Analysis",
        "Financial Statements",
        "Revenue",
        "Net Income",
        "Earnings Per Share"
    ]
    
    # Collect text from relevant sections
    all_text = []
    for hint in section_hints:
        docs = retrieve_filing_section(ticker, filing_type, year, hint, top_k=2)
        for doc in docs:
            if hasattr(doc, "page_content"):
                all_text.append(doc.page_content)
            elif isinstance(doc, str):
                all_text.append(doc)
    
    # Combine text
    combined_text = "\n\n".join(all_text)
    
    if not combined_text.strip():
        # Fallback: try to get any text from the filing
        docs = retrieve_filing_section(ticker, filing_type, year, "financial metrics", top_k=5)
        combined_text = "\n\n".join([doc.page_content if hasattr(doc, "page_content") else str(doc) for doc in docs])
    
    if not combined_text.strip():
        raise ValueError(f"No content found for {ticker} {filing_type} {year}")
    
    # Extract KPIs using LLM
    kpis_json = agent.extract_kpis(combined_text)
    
    # Parse JSON response
    if isinstance(kpis_json, dict):
        kpis_data = kpis_json
    elif isinstance(kpis_json, str):
        try:
            kpis_data = json.loads(kpis_json)
        except json.JSONDecodeError:
            # Try to extract JSON from text
            import re
            json_match = re.search(r'\{.*\}', kpis_json, re.DOTALL)
            if json_match:
                kpis_data = json.loads(json_match.group())
            else:
                raise ValueError("Failed to parse KPI JSON response")
    else:
        raise ValueError(f"Unexpected KPI response type: {type(kpis_json)}")
    
    # Convert to DataFrame
    kpi_records = []
    
    # Process standard KPIs
    standard_kpis = {
        "revenue": "Revenue",
        "net_income": "Net Income",
        "eps": "Earnings Per Share",
        "operating_margin": "Operating Margin",
        "debt_to_equity": "Debt to Equity",
        "free_cash_flow": "Free Cash Flow"
    }
    
    for key, metric_name in standard_kpis.items():
        if key in kpis_data and kpis_data[key] is not None:
            value = kpis_data[key]
            unit = _infer_unit(metric_name, value)
            kpi_records.append({
                "metric_name": metric_name,
                "value": float(value) if isinstance(value, (int, float, str)) and str(value).replace('.', '').replace('-', '').isdigit() else None,
                "unit": unit,
                "period": f"{year}",
                "source_page": "N/A",
                "raw_text_snippet": f"{metric_name}: {value}"
            })
    
    # Process additional metrics
    if "additional_metrics" in kpis_data:
        for metric_name, value in kpis_data["additional_metrics"].items():
            unit = _infer_unit(metric_name, value)
            kpi_records.append({
                "metric_name": metric_name,
                "value": float(value) if isinstance(value, (int, float, str)) and str(value).replace('.', '').replace('-', '').isdigit() else None,
                "unit": unit,
                "period": f"{year}",
                "source_page": "N/A",
                "raw_text_snippet": f"{metric_name}: {value}"
            })
    
    # Create DataFrame
    df = pd.DataFrame(kpi_records)
    
    # If DataFrame is empty, create a placeholder
    if df.empty:
        df = pd.DataFrame(columns=["metric_name", "value", "unit", "period", "source_page", "raw_text_snippet"])
    
    return df


def _infer_unit(metric_name: str, value: any) -> str:
    """Infer unit from metric name and value"""
    metric_lower = metric_name.lower()
    
    if "revenue" in metric_lower or "income" in metric_lower or "cash flow" in metric_lower:
        return "USD"
    elif "margin" in metric_lower or "ratio" in metric_lower or "percent" in metric_lower:
        return "%"
    elif "per share" in metric_lower:
        return "USD/share"
    elif "debt" in metric_lower or "equity" in metric_lower:
        return "ratio"
    else:
        return "N/A"


def kpi_dataframe_to_json(df: pd.DataFrame) -> Dict:
    """Convert KPI DataFrame to JSON response"""
    # Convert DataFrame to records
    records = df.to_dict('records')
    
    # Extract numeric metrics
    metrics = {}
    for record in records:
        if record.get("value") is not None:
            metrics[record["metric_name"]] = record["value"]
    
    return {
        "kpis": records,
        "metrics": metrics
    }

