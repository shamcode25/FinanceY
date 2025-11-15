"""
Streamlit frontend for FinanceY
"""
import streamlit as st
import requests
import json
from pathlib import Path
import sys
from datetime import datetime
import tempfile
import io

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent))

# Optional imports for visualizations
try:
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
    HAS_VISUALIZATIONS = True
except ImportError:
    HAS_VISUALIZATIONS = False
    # Create dummy functions for when plotly is not available
    pd = None
    px = None
    go = None

st.set_page_config(
    page_title="FinanceY",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        color: #666;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .stProgress > div > div > div > div {
        background-color: #1f77b4;
    }
    .uploaded-file {
        background-color: #e8f5e9;
        padding: 0.5rem;
        border-radius: 0.25rem;
        margin: 0.25rem 0;
    }
    .risk-category {
        padding: 0.75rem;
        margin: 0.5rem 0;
        border-left: 4px solid #ff6b6b;
        background-color: #fff5f5;
    }
    .kpi-value {
        font-size: 1.5rem;
        font-weight: bold;
        color: #1f77b4;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
        border-radius: 5px;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        font-weight: 500;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
    }
    </style>
""", unsafe_allow_html=True)

# API base URL - can be overridden by environment variable
import os
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# Initialize session state
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "kpi_results" not in st.session_state:
    st.session_state.kpi_results = {}
if "risk_results" not in st.session_state:
    st.session_state.risk_results = {}
if "memo_results" not in st.session_state:
    st.session_state.memo_results = {}


def call_api(endpoint: str, method: str = "GET", data: dict = None, files: dict = None):
    """Helper function to call API"""
    try:
        if method == "GET":
            response = requests.get(f"{API_BASE_URL}{endpoint}")
        elif method == "POST":
            if files:
                response = requests.post(f"{API_BASE_URL}{endpoint}", data=data, files=files)
            else:
                response = requests.post(f"{API_BASE_URL}{endpoint}", json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to API. Make sure the backend is running: `uvicorn backend.main:app --reload`")
        return None
    except requests.exceptions.HTTPError as e:
        # Try to get error details from response
        try:
            error_detail = response.json().get("detail", str(e))
            if "OPENAI_API_KEY" in error_detail or "API key" in error_detail:
                st.error(f"🔑 **API Key Required**: {error_detail}")
                st.info("💡 **Solution**: Edit the `.env` file in the project root and add your OpenAI API key:\n```\nOPENAI_API_KEY=your_actual_api_key_here\n```")
            else:
                st.error(f"❌ **API Error**: {error_detail}")
        except:
            st.error(f"❌ **API Error**: {e}")
        return None


# Sidebar
with st.sidebar:
    st.title("📊 FinanceY")
    st.markdown("### AI-Powered Financial Analysis")
    st.markdown("---")
    
    # API Status
    health = call_api("/health")
    if health:
        st.success("✅ **API Connected**")
        if health.get("timestamp"):
            st.caption(f"Last checked: {datetime.now().strftime('%H:%M:%S')}")
    else:
        st.error("❌ **API Disconnected**")
        st.info("Make sure the backend is running")
    
    st.markdown("---")
    
    # Stats
    stats = call_api("/stats")
    if stats:
        st.subheader("📈 Statistics")
        num_docs = stats.get('retriever', {}).get('num_documents', 0)
        index_exists = stats.get('retriever', {}).get('index_exists', False)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Documents", num_docs)
        with col2:
            status = "✅" if index_exists else "❌"
            st.metric("Index", status)
        
        if num_docs > 0:
            st.info(f"📚 {num_docs} document(s) indexed and ready for analysis")
    
    st.markdown("---")
    
    # Quick Actions
    st.subheader("🚀 Quick Actions")
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.chat_history = []
        st.success("Chat history cleared!")
        st.rerun()
    
    if st.button("📊 Clear Results", use_container_width=True):
        st.session_state.kpi_results = {}
        st.session_state.risk_results = {}
        st.session_state.memo_results = {}
        st.success("Results cleared!")
        st.rerun()
    
    st.markdown("---")
    
    # Help Section
    with st.expander("ℹ️ Help & Tips"):
        st.markdown("""
        **Getting Started:**
        1. Upload financial documents (SEC filings, transcripts)
        2. Ask questions or extract KPIs
        3. Generate investment memos
        
        **Supported Formats:**
        - PDF files
        - Text files (.txt)
        
        **Features:**
        - 📊 KPI Extraction
        - ⚠️ Risk Analysis
        - 💬 Q&A with RAG
        - 📝 Investment Memos
        """)
    
    st.markdown("---")
    st.caption("Made with ❤️ using Streamlit")


# Main content
st.markdown('<h1 class="main-header">📊 FinanceY</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">AI-powered financial document analysis • Extract insights from SEC filings, earnings transcripts, and financial news</p>', unsafe_allow_html=True)

# Question input - must be outside tabs for chat_input to work
question = None

# Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📤 Upload Documents",
    "💬 Q&A",
    "📊 Extract KPIs",
    "⚠️ Risk Analysis",
    "📝 Investment Memo"
])

# Tab 1: Upload Documents
with tab1:
    col1, col2 = st.columns([2, 1])
    with col1:
        st.header("📤 Upload Financial Documents")
        st.markdown("Upload SEC filings (10-K, 10-Q, 8-K), earnings transcripts, or news articles for analysis")
    
    with col2:
        if st.session_state.uploaded_files:
            st.markdown("### 📁 Uploaded Files")
            for file in st.session_state.uploaded_files:
                st.markdown(f'<div class="uploaded-file">📄 {file}</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # File upload section
    uploaded_file = st.file_uploader(
        "Choose a file to upload",
        type=["txt", "pdf"],
        help="Supported formats: .txt, .pdf (Max 200MB)"
    )
    
    if uploaded_file:
        file_size = len(uploaded_file.getvalue()) / (1024 * 1024)  # Size in MB
        st.info(f"📄 **File**: {uploaded_file.name} | **Size**: {file_size:.2f} MB | **Type**: {uploaded_file.type}")
    
    col1, col2 = st.columns(2)
    with col1:
        doc_type = st.selectbox(
            "Document Type",
            ["auto", "filing", "transcript", "news"],
            help="Auto-detect or specify document type",
            index=0
        )
    
    with col2:
        st.write("")  # Spacing
        st.write("")  # Spacing
    
    if st.button("🚀 Upload and Process", type="primary", use_container_width=True):
        if uploaded_file is not None:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            status_text.text("Uploading file...")
            progress_bar.progress(20)
            
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
            data = {"doc_type": doc_type}
            
            status_text.text("Processing document and generating embeddings...")
            progress_bar.progress(50)
            
            result = call_api("/upload", method="POST", data=data, files=files)
            
            progress_bar.progress(80)
            
            if result:
                progress_bar.progress(100)
                status_text.text("✅ Complete!")
                
                st.success(f"✅ **Successfully uploaded and processed**: {result.get('filename')}")
                
                # Display results in expandable sections
                with st.expander("📊 Upload Details", expanded=False):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Chunks Created", result.get('chunks', 0))
                    with col2:
                        st.metric("Status", "✅ Processed")
                    with col3:
                        metadata = result.get('metadata', {})
                        st.metric("File Type", metadata.get('file_type', 'Unknown'))
                    
                    st.json(result)
                
                st.session_state.uploaded_files.append(result.get('filename'))
                progress_bar.empty()
                status_text.empty()
                
                # Auto-refresh stats
                st.rerun()
            else:
                progress_bar.empty()
                status_text.empty()
        else:
            st.warning("⚠️ Please select a file to upload")

# Tab 2: Q&A
with tab2:
    col1, col2 = st.columns([3, 1])
    with col1:
        st.header("💬 Ask Questions About Your Documents")
    with col2:
        if st.session_state.chat_history:
            if st.button("🗑️ Clear Chat", use_container_width=True):
                st.session_state.chat_history = []
                st.rerun()
    
    # Check if documents are uploaded
    stats = call_api("/stats")
    num_docs = stats.get('retriever', {}).get('num_documents', 0) if stats else 0
    
    if num_docs == 0:
        st.warning("⚠️ **No documents uploaded yet!** Please upload documents first to ask questions.")
        st.info("💡 Go to the **Upload Documents** tab to upload SEC filings, transcripts, or news articles.")
    else:
        st.success(f"📚 **{num_docs} document(s)** ready for analysis")
    
    st.markdown("---")
    
    # Chat container
    chat_container = st.container()
    
    with chat_container:
        # Display chat history
        if st.session_state.chat_history:
            for i, (role, message) in enumerate(st.session_state.chat_history):
                with st.chat_message(role):
                    if isinstance(message, dict) and "answer" in message:
                        st.markdown(message["answer"])
                        if message.get("sources"):
                            with st.expander(f"📚 Sources ({len(message.get('sources', []))})", expanded=False):
                                for source in message.get("sources", []):
                                    st.markdown(f"📄 {source}")
                    else:
                        st.markdown(message)
        else:
            st.info("💡 **Example questions you can ask:**\n- What was the revenue for the fiscal year?\n- What are the main risks mentioned?\n- How did operating margins change?\n- What is the debt-to-equity ratio?")
    
    st.markdown("---")
    
    # Question input
    col1, col2 = st.columns([4, 1])
    with col1:
        question = st.text_input(
            "Ask a question about your documents...",
            key="qa_input",
            placeholder="e.g., What was the revenue for the fiscal year?"
        )
    with col2:
        ask_button = st.button("🚀 Ask", key="qa_button", use_container_width=True, type="primary")
    
    if ask_button and question:
        if num_docs == 0:
            st.error("⚠️ Please upload documents first!")
        else:
            # Process question immediately
            with st.spinner("🤔 Thinking... Analyzing your documents..."):
                response = call_api("/query", method="POST", data={"question": question})
                
                if response:
                    answer = response.get("answer", "No answer available")
                    sources = response.get("sources", [])
                    
                    # Add to chat history
                    st.session_state.chat_history.append(("user", question))
                    st.session_state.chat_history.append(("assistant", {
                        "answer": answer,
                        "sources": sources
                    }))
                    
                    st.rerun()
                else:
                    st.error("❌ Failed to get answer. Please try again.")

# Tab 3: Extract KPIs
with tab3:
    st.header("📊 Extract Key Performance Indicators")
    st.markdown("Automatically extract key financial metrics from documents")
    
    option = st.radio(
        "Input method",
        ["Upload file", "Paste text"],
        horizontal=True,
        key="kpi_input_method"
    )
    
    st.markdown("---")
    
    if option == "Upload file":
        kpi_file = st.file_uploader("Upload document", type=["txt", "pdf"], key="kpi_file_uploader")
        
        if kpi_file:
            file_size = len(kpi_file.getvalue()) / (1024 * 1024)
            st.info(f"📄 **File**: {kpi_file.name} | **Size**: {file_size:.2f} MB")
        
        if st.button("🚀 Extract KPIs", type="primary", use_container_width=True):
            if kpi_file:
                with st.spinner("🔍 Extracting KPIs from document..."):
                    # Use document text directly instead of file path for better compatibility
                    if kpi_file.type == "application/pdf":
                        # For PDF, we need to extract text first
                        try:
                            import pdfplumber
                            text = ""
                            import io
                            pdf_file = io.BytesIO(kpi_file.getvalue())
                            with pdfplumber.open(pdf_file) as pdf:
                                for page in pdf.pages:
                                    text += page.extract_text() or ""
                            
                            response = call_api(
                                "/extract-kpis",
                                method="POST",
                                data={"document_text": text}
                            )
                        except ImportError:
                            st.error("⚠️ PDF processing requires pdfplumber. Using file path instead.")
                            # Fallback: save to temp location
                            import tempfile
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                                tmp_file.write(kpi_file.getvalue())
                                temp_path = tmp_file.name
                            
                            response = call_api(
                                "/extract-kpis",
                                method="POST",
                                data={"file_path": str(temp_path)}
                            )
                    else:
                        # For text files, use text directly
                        text = kpi_file.getvalue().decode("utf-8", errors="ignore")
                        response = call_api(
                            "/extract-kpis",
                            method="POST",
                            data={"document_text": text}
                        )
                    
                    if response:
                        kpis = response.get("kpis", {})
                        st.session_state.kpi_results = kpis
                        st.rerun()
            else:
                st.warning("⚠️ Please upload a file")
    else:
        text_input = st.text_area("Paste document text", height=200, placeholder="Paste financial document text here...")
        if st.button("🚀 Extract KPIs", type="primary", use_container_width=True):
            if text_input:
                with st.spinner("🔍 Extracting KPIs from text..."):
                    response = call_api(
                        "/extract-kpis",
                        method="POST",
                        data={"document_text": text_input}
                    )
                    
                    if response:
                        kpis = response.get("kpis", {})
                        st.session_state.kpi_results = kpis
                        st.rerun()
            else:
                st.warning("⚠️ Please paste document text")
    
    # Display KPI results
    if st.session_state.kpi_results:
        st.markdown("---")
        st.success("✅ **KPIs Extracted Successfully**")
        
        kpis = st.session_state.kpi_results
        
        # Filter numeric KPIs
        numeric_kpis = {k: v for k, v in kpis.items() if isinstance(v, (int, float)) and not k.startswith("error")}
        text_kpis = {k: v for k, v in kpis.items() if not isinstance(v, (int, float)) or k.startswith("error")}
        
        if numeric_kpis:
            # Main metrics in columns
            st.subheader("📈 Key Financial Metrics")
            
            # Create metrics in a grid
            num_cols = 3
            cols = st.columns(num_cols)
            
            for idx, (key, value) in enumerate(numeric_kpis.items()):
                col = cols[idx % num_cols]
                with col:
                    # Format value
                    if "revenue" in key.lower() or "income" in key.lower() or "cash" in key.lower() or "flow" in key.lower():
                        formatted_value = f"${value:,.2f}"
                        delta = None
                    elif "margin" in key.lower() or "ratio" in key.lower() or "eps" in key.lower():
                        formatted_value = f"{value:.2f}"
                        delta = None
                    else:
                        formatted_value = f"{value:,.2f}"
                        delta = None
                    
                    st.metric(
                        label=key.replace("_", " ").title(),
                        value=formatted_value,
                        delta=delta
                    )
            
            # Create visualization if we have enough data
            if len(numeric_kpis) > 1:
                st.markdown("---")
                st.subheader("📊 KPI Visualization")
                
                if HAS_VISUALIZATIONS:
                    # Prepare data for chart
                    kpi_data = pd.DataFrame([
                        {"Metric": k.replace("_", " ").title(), "Value": abs(v)}
                        for k, v in numeric_kpis.items()
                    ])
                    
                    # Bar chart
                    fig = px.bar(
                        kpi_data,
                        x="Metric",
                        y="Value",
                        title="Extracted KPIs",
                        labels={"Value": "Amount", "Metric": "Key Performance Indicator"},
                        color="Value",
                        color_continuous_scale="Blues"
                    )
                    fig.update_layout(showlegend=False, height=400)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("💡 Install plotly and pandas to see visualizations: `pip install plotly pandas`")
                    
                    # Show simple table as fallback
                    kpi_list = [
                        {"Metric": k.replace("_", " ").title(), "Value": v}
                        for k, v in numeric_kpis.items()
                    ]
                    st.dataframe(kpi_list, use_container_width=True)
            
            # Additional metrics section
            if text_kpis:
                st.markdown("---")
                with st.expander("📋 Additional Information", expanded=False):
                    st.json(text_kpis)
        else:
            st.warning("⚠️ No numeric KPIs were extracted from the document.")
            if text_kpis:
                st.json(text_kpis)
        
        # Raw data section
        with st.expander("🔍 Raw Data", expanded=False):
            st.json(kpis)

# Tab 4: Risk Analysis
with tab4:
    st.header("⚠️ Risk Analysis")
    st.markdown("Identify and categorize risks from financial documents")
    
    option = st.radio(
        "Input method",
        ["Upload file", "Paste text"],
        horizontal=True,
        key="risk_input_method"
    )
    
    st.markdown("---")
    
    if option == "Upload file":
        risk_file = st.file_uploader("Upload document", type=["txt", "pdf"], key="risk_file_uploader")
        
        if risk_file:
            file_size = len(risk_file.getvalue()) / (1024 * 1024)
            st.info(f"📄 **File**: {risk_file.name} | **Size**: {file_size:.2f} MB")
        
        if st.button("🚀 Analyze Risks", type="primary", use_container_width=True):
            if risk_file:
                with st.spinner("🔍 Analyzing risks in document..."):
                    # Use document text directly for better compatibility
                    if risk_file.type == "application/pdf":
                        try:
                            import pdfplumber
                            text = ""
                            import io
                            pdf_file = io.BytesIO(risk_file.getvalue())
                            with pdfplumber.open(pdf_file) as pdf:
                                for page in pdf.pages:
                                    text += page.extract_text() or ""
                            
                            response = call_api(
                                "/summarize-risks",
                                method="POST",
                                data={"document_text": text}
                            )
                        except ImportError:
                            st.error("⚠️ PDF processing requires pdfplumber. Using file path instead.")
                            import tempfile
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                                tmp_file.write(risk_file.getvalue())
                                temp_path = tmp_file.name
                            
                            response = call_api(
                                "/summarize-risks",
                                method="POST",
                                data={"file_path": str(temp_path)}
                            )
                    else:
                        text = risk_file.getvalue().decode("utf-8", errors="ignore")
                        response = call_api(
                            "/summarize-risks",
                            method="POST",
                            data={"document_text": text}
                        )
                    
                    if response:
                        st.session_state.risk_results = response
                        st.rerun()
            else:
                st.warning("⚠️ Please upload a file")
    else:
        text_input = st.text_area("Paste document text", height=200, placeholder="Paste financial document text here...")
        if st.button("🚀 Analyze Risks", type="primary", use_container_width=True):
            if text_input:
                with st.spinner("🔍 Analyzing risks in text..."):
                    response = call_api(
                        "/summarize-risks",
                        method="POST",
                        data={"document_text": text_input}
                    )
                    
                    if response:
                        st.session_state.risk_results = response
                        st.rerun()
            else:
                st.warning("⚠️ Please paste document text")
    
    # Display risk results
    if st.session_state.risk_results:
        st.markdown("---")
        response = st.session_state.risk_results
        st.success("✅ **Risk Analysis Complete**")
        
        # Display risks by category
        categories = {
            "Market Risks": response.get("market_risks", []),
            "Operational Risks": response.get("operational_risks", []),
            "Financial Risks": response.get("financial_risks", []),
            "Regulatory Risks": response.get("regulatory_risks", []),
            "Competitive Risks": response.get("competitive_risks", [])
        }
        
        # Count total risks
        total_risks = sum(len(risks) for risks in categories.values())
        
        if total_risks > 0:
            st.subheader(f"📊 Risk Summary ({total_risks} risks identified)")
            
            # Create risk count chart
            risk_counts = {cat: len(risks) for cat, risks in categories.items() if risks}
            if risk_counts:
                if HAS_VISUALIZATIONS:
                    risk_df = pd.DataFrame([
                        {"Category": cat, "Count": count}
                        for cat, count in risk_counts.items()
                    ])
                    
                    fig = px.pie(
                        risk_df,
                        values="Count",
                        names="Category",
                        title="Risk Distribution by Category",
                        color_discrete_sequence=px.colors.qualitative.Set3
                    )
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    # Show risk counts as metrics if no visualization
                    cols = st.columns(min(len(risk_counts), 5))
                    for idx, (cat, count) in enumerate(risk_counts.items()):
                        with cols[idx % len(cols)]:
                            st.metric(cat, count)
            
            st.markdown("---")
            st.subheader("📋 Risk Details by Category")
            
            # Display risks by category
            for category, risks in categories.items():
                if risks:
                    with st.expander(f"⚠️ {category} ({len(risks)} risks)", expanded=True):
                        for i, risk in enumerate(risks, 1):
                            st.markdown(f"**{i}.** {risk}")
        else:
            st.info("ℹ️ No risks were identified in the document.")
        
        # Raw data
        with st.expander("🔍 Raw Risk Data", expanded=False):
            st.json(response)

# Tab 5: Investment Memo
with tab5:
    st.header("📝 Generate Investment Memo")
    st.markdown("Generate comprehensive investment memos from financial documents")
    
    st.markdown("---")
    
    # Input form
    col1, col2 = st.columns(2)
    with col1:
        company_name = st.text_input(
            "Company Name",
            placeholder="e.g., Apple Inc.",
            help="Enter the company name for the investment memo"
        )
    with col2:
        period = st.text_input(
            "Period",
            placeholder="e.g., Q4 2023",
            help="Enter the reporting period (e.g., Q4 2023, FY 2023)"
        )
    
    st.markdown("---")
    
    # Optional document upload
    st.subheader("📄 Optional: Upload Document")
    st.markdown("Upload a document to extract KPIs and risks automatically")
    
    memo_file = st.file_uploader(
        "Upload document (optional)",
        type=["txt", "pdf"],
        key="memo_file_uploader",
        help="Optional: Upload a financial document to extract KPIs and risks"
    )
    
    if memo_file:
        file_size = len(memo_file.getvalue()) / (1024 * 1024)
        st.info(f"📄 **File**: {memo_file.name} | **Size**: {file_size:.2f} MB")
    
    st.markdown("---")
    
    # Generate memo button
    if st.button("🚀 Generate Investment Memo", type="primary", use_container_width=True):
        if company_name and period:
            with st.spinner("📝 Generating investment memo... This may take a moment."):
                data = {
                    "company_name": company_name,
                    "period": period
                }
                
                if memo_file:
                    # Use tempfile for cross-platform compatibility
                    import tempfile
                    import os
                    suffix = ".pdf" if memo_file.type == "application/pdf" else ".txt"
                    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
                        tmp_file.write(memo_file.getvalue())
                        temp_path = tmp_file.name
                    data["file_path"] = str(temp_path)
                    
                    # Clean up temp file after a delay (in production, this would be handled server-side)
                
                response = call_api("/generate-memo", method="POST", data=data)
                
                if response:
                    memo = response.get("memo", "")
                    st.session_state.memo_results = {
                        "memo": memo,
                        "company_name": company_name,
                        "period": period,
                        "generated_at": response.get("generated_at", datetime.now().isoformat())
                    }
                    st.rerun()
        else:
            st.warning("⚠️ Please provide both company name and period")
    
    # Display memo results
    if st.session_state.memo_results:
        st.markdown("---")
        memo_data = st.session_state.memo_results
        memo = memo_data.get("memo", "")
        company = memo_data.get("company_name", "")
        period = memo_data.get("period", "")
        
        st.success(f"✅ **Investment Memo Generated** for {company} - {period}")
        
        # Memo metadata
        with st.expander("📊 Memo Information", expanded=False):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Company", company)
            with col2:
                st.metric("Period", period)
            with col3:
                gen_time = memo_data.get("generated_at", "")
                if gen_time:
                    try:
                        dt = datetime.fromisoformat(gen_time.replace('Z', '+00:00'))
                        st.metric("Generated", dt.strftime("%Y-%m-%d %H:%M"))
                    except:
                        st.metric("Generated", "Just now")
        
        st.markdown("---")
        st.subheader("📄 Investment Memo")
        
        # Display memo with better formatting
        st.markdown(memo)
        
        st.markdown("---")
        
        # Download and actions
        col1, col2, col3 = st.columns(3)
        with col1:
            st.download_button(
                label="📥 Download as Markdown",
                data=memo,
                file_name=f"{company}_{period}_memo.md",
                mime="text/markdown",
                use_container_width=True
            )
        with col2:
            st.download_button(
                label="📄 Download as Text",
                data=memo,
                file_name=f"{company}_{period}_memo.txt",
                mime="text/plain",
                use_container_width=True
            )
        with col3:
            if st.button("🗑️ Clear Memo", use_container_width=True):
                st.session_state.memo_results = {}
                st.rerun()

