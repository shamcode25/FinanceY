# FinanceY Product Specification

## Problem Statement

Manual financial research is slow and time-consuming. Financial analysts, portfolio managers, and risk teams spend hours reading through lengthy SEC filings (10-K, 10-Q, 8-K), earnings transcripts, and financial news to:
- Extract key performance indicators (KPIs)
- Identify and assess risks
- Compare financial performance across periods
- Generate investment memos and research reports

This manual process is error-prone, inconsistent, and doesn't scale with the volume of financial information available.

## Target Users

1. **Financial Analysts**: Need to quickly analyze companies and extract insights from filings
2. **Portfolio Managers**: Require fast synthesis of financial information for investment decisions
3. **Risk Teams**: Must identify and assess risks across multiple companies and filings
4. **Research Teams**: Generate investment memos and research reports efficiently

## v1 Features

### 1. Upload SEC Filings
- **Format**: Support PDF and text file uploads
- **Types**: 10-K (annual reports), 10-Q (quarterly reports), 8-K (current reports)
- **Storage**: Documents stored locally with metadata (company, filing date, type)

### 2. Ask Questions Over a Filing
- **Interface**: Natural language Q&A interface
- **Capability**: Answer questions about specific filings using RAG (Retrieval-Augmented Generation)
- **Examples**:
  - "What was the revenue growth rate?"
  - "What are the main risks mentioned in Item 1A?"
  - "How did operating margins change year-over-year?"

### 3. Extract KPIs from a Filing
- **Automated Extraction**: Identify and extract key financial metrics
- **KPIs Include**:
  - Revenue and revenue growth
  - Net income and EPS
  - Operating margin
  - Debt-to-equity ratio
  - Free cash flow
  - Other relevant financial metrics
- **Output**: Structured JSON/table format

### 4. Generate 1-Page Investment Memo
- **Input**: Company filing(s) and optional user context
- **Output**: Concise 1-page investment memo including:
  - Executive summary
  - Company overview
  - Financial performance highlights
  - Key risks
  - Investment thesis
  - Recommendation
- **Format**: Markdown/text that can be exported

## Non-Goals (Out of Scope for v1)

- ❌ **Real-time Trading**: No trading execution or trading signals
- ❌ **Price Predictions**: No stock price forecasting or target price generation
- ❌ **Market Data Integration**: No real-time market data feeds
- ❌ **Multi-company Comparison**: Focus on single-company analysis in v1
- ❌ **Historical Backtesting**: No performance backtesting capabilities
- ❌ **Regulatory Compliance Tools**: Not a compliance monitoring system

## Technical Architecture

- **Backend**: FastAPI (Python)
- **LLM**: OpenAI GPT-4o (with option to switch to open-source via Ollama later)
- **RAG**: FAISS vector database + OpenAI embeddings
- **Frontend**: Streamlit (fast prototyping)
- **Infrastructure**: Docker (later), local development first

## API Endpoints (v1)

- `GET /` - Root endpoint
- `GET /health` - Health check
- `POST /upload` - Upload SEC filing
- `POST /query` - Ask questions about uploaded filings
- `POST /extract-kpis` - Extract KPIs from a filing
- `POST /generate-memo` - Generate investment memo

## Success Metrics

- **Time Savings**: Reduce time to analyze a filing from hours to minutes
- **Accuracy**: KPI extraction accuracy > 90%
- **User Satisfaction**: Positive feedback on memo quality and Q&A relevance

