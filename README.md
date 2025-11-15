# FinanceY

An AI-powered financial document analysis platform that reads SEC filings (10-K/10-Q/8-K), earnings transcripts, and news to extract KPIs, summarize risks, compare filings between years, and generate investment memos.

## Features

- 📊 **KPI Extraction**: Automatically extract key performance indicators from financial documents
- ⚠️ **Risk Summarization**: Identify and categorize risks from SEC filings
- 📈 **Filing Comparison**: Compare financial filings between different periods
- 📝 **Investment Memos**: Generate comprehensive investment memos
- 💬 **Q&A**: Answer questions about financial documents using RAG (Retrieval-Augmented Generation)
- 📤 **Document Upload**: Upload PDF and TXT files with drag-and-drop support
- 📊 **Visualizations**: Interactive charts and graphs for KPIs and risk analysis

## Tech Stack

- **Backend**: Python, FastAPI
- **LLM**: OpenAI (gpt-4o) or open-source via Ollama later
- **RAG**: FAISS + OpenAI embeddings
- **Frontend**: React (Material-UI) or Streamlit
- **Infra**: Docker (later), local dev first

## Setup

### Option 1: Local Development

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key
   ```

3. **Run the backend:**
   ```bash
   cd backend
   uvicorn main:app --reload
   ```
   The API will be available at `http://localhost:8000`
   - API docs: `http://localhost:8000/docs`
   - Health check: `http://localhost:8000/health`

4. **Run the frontend (choose one):**

   **Option A: React Frontend (Recommended)**
   ```bash
   cd frontend-react
   npm install
   npm run dev
   ```
   The UI will open in your browser at `http://localhost:5173`

   **Option B: Streamlit Frontend**
   ```bash
   streamlit run frontend/app.py
   ```
   The UI will open in your browser at `http://localhost:8501`

### Option 2: Docker (Recommended for Production)

1. **Create `.env` file:**
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENAI_API_KEY
   ```

2. **Quick start with Docker:**
   ```bash
   ./docker-start.sh
   ```
   
   Or manually:
   ```bash
   docker-compose up -d
   ```

3. **Access the application:**
   - React Frontend: http://localhost:3000 (or http://localhost if using nginx)
   - Streamlit Frontend: http://localhost:8501
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

4. **Production deployment:**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

For detailed Docker deployment instructions, see [DOCKER.md](DOCKER.md) and [DEPLOYMENT.md](DEPLOYMENT.md).

## Usage

1. **Upload Documents**: Go to the "Upload Documents" tab and upload SEC filings, transcripts, or news articles (PDF or TXT format)

2. **Ask Questions**: Use the "Q&A" tab to ask questions about your uploaded documents

3. **Extract KPIs**: Use the "Extract KPIs" tab to automatically extract key performance indicators

4. **Analyze Risks**: Use the "Risk Analysis" tab to identify and categorize risks

5. **Generate Memos**: Use the "Investment Memo" tab to generate comprehensive investment memos

## Project Structure

```
financey/
├── backend/          # FastAPI backend
├── frontend-react/   # React frontend (Recommended)
│   ├── src/
│   │   ├── components/
│   │   ├── services/
│   │   └── types/
│   └── package.json
├── frontend/         # Streamlit frontend
├── eval/             # Evaluation scripts
├── docs/             # Documentation
├── requirements.txt  # Python dependencies
└── README.md
```

## License

MIT

