# FinanceY - React Frontend

A modern, interactive React-based frontend for FinanceY, an AI-powered financial document analysis platform.

## Features

- 📤 **Upload Documents**: Upload SEC filings, earnings transcripts, and news articles
- 💬 **Q&A Chat**: Ask questions about uploaded documents with RAG-powered responses
- 📊 **Extract KPIs**: Automatically extract key performance indicators from documents
- ⚠️ **Risk Analysis**: Identify and categorize risks from financial documents
- 📝 **Investment Memo**: Generate comprehensive investment memos

## Tech Stack

- **React 19** with TypeScript
- **Vite** for fast development and building
- **Material-UI (MUI)** for modern UI components
- **React Router** for navigation
- **Recharts** for data visualizations
- **Axios** for API communication

## Getting Started

### Prerequisites

- Node.js 20+ and npm
- Backend API running on http://localhost:8000

### Installation

```bash
cd frontend-react
npm install
```

### Configuration

Create a `.env` file in the `frontend-react` directory:

```env
VITE_API_BASE_URL=http://localhost:8000
```

### Development

```bash
npm run dev
```

The app will be available at http://localhost:5173

### Build

```bash
npm run build
```

The built files will be in the `dist` directory.

### Preview Production Build

```bash
npm run preview
```

## Project Structure

```
frontend-react/
├── src/
│   ├── components/       # React components
│   │   ├── Layout.tsx    # Main layout with sidebar
│   │   ├── UploadDocuments.tsx
│   │   ├── QAChat.tsx
│   │   ├── ExtractKPIs.tsx
│   │   ├── RiskAnalysis.tsx
│   │   └── InvestmentMemo.tsx
│   ├── services/         # API service layer
│   │   └── api.ts        # API client
│   ├── types/            # TypeScript type definitions
│   │   └── index.ts
│   ├── App.tsx           # Main app component
│   └── main.tsx          # Entry point
├── public/               # Static assets
└── package.json
```

## Features in Detail

### Upload Documents
- Drag and drop file upload
- Support for PDF and text files
- Real-time progress indicators
- Document type selection

### Q&A Chat
- Real-time chat interface
- RAG-powered responses
- Source citations
- Chat history

### Extract KPIs
- Automatic KPI extraction
- Visual charts and graphs
- Metric cards display
- Export capabilities

### Risk Analysis
- Risk categorization
- Pie chart visualization
- Expandable risk details
- Risk count summaries

### Investment Memo
- Memo generation
- Company and period input
- Download as Markdown or Text
- Memo metadata display

## API Integration

The frontend communicates with the FastAPI backend through the API service layer. All API calls are centralized in `src/services/api.ts`.

## Development Notes

- Uses Material-UI v7 for components
- TypeScript for type safety
- Responsive design with mobile support
- Error handling and loading states
- Real-time API status monitoring

## License

MIT
