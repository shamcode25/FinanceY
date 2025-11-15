import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme, CssBaseline } from '@mui/material';
import Layout from './components/Layout';
import UploadDocuments from './components/UploadDocuments';
import QAChat from './components/QAChat';
import ExtractKPIs from './components/ExtractKPIs';
import RiskAnalysis from './components/RiskAnalysis';
import InvestmentMemo from './components/InvestmentMemo';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
  typography: {
    fontFamily: [
      '-apple-system',
      'BlinkMacSystemFont',
      '"Segoe UI"',
      'Roboto',
      '"Helvetica Neue"',
      'Arial',
      'sans-serif',
    ].join(','),
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Layout>
          <Routes>
            <Route path="/" element={<UploadDocuments />} />
            <Route path="/qa" element={<QAChat />} />
            <Route path="/kpis" element={<ExtractKPIs />} />
            <Route path="/risks" element={<RiskAnalysis />} />
            <Route path="/memo" element={<InvestmentMemo />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Layout>
      </Router>
    </ThemeProvider>
  );
}

export default App;
