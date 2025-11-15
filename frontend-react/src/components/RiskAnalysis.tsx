import { useState, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  TextField,
  Radio,
  RadioGroup,
  FormControlLabel,
  FormControl,
  FormLabel,
  Alert,
  CircularProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  LinearProgress,
} from '@mui/material';
import {
  Warning as WarningIcon,
  CloudUpload as CloudUploadIcon,
  ExpandMore as ExpandMoreIcon,
  InsertDriveFile as InsertDriveFileIcon,
} from '@mui/icons-material';
import { summarizeRisks } from '../services/api';
import type { RiskResponse } from '../types';
import { extractTextFromPDF } from '../utils/pdfExtractor';
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Legend,
  Tooltip,
} from 'recharts';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D'];

export default function RiskAnalysis() {
  const [inputMethod, setInputMethod] = useState<'file' | 'text'>('file');
  const [file, setFile] = useState<File | null>(null);
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingMessage, setLoadingMessage] = useState<string>('');
  const [result, setResult] = useState<RiskResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      setFile(event.target.files[0]);
      setError(null);
      setResult(null);
    }
  };

  const handleFileSelect = useCallback((selectedFile: File) => {
    const validTypes = ['text/plain', 'application/pdf'];
    const validExtensions = ['.txt', '.pdf'];
    const fileName = selectedFile.name.toLowerCase();
    const isValidType = validTypes.includes(selectedFile.type) || 
                       validExtensions.some(ext => fileName.endsWith(ext));
    
    if (!isValidType) {
      setError('Please upload a PDF or TXT file');
      return;
    }

    setFile(selectedFile);
    setError(null);
    setResult(null);
  }, []);

  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const droppedFile = e.dataTransfer.files[0];
      handleFileSelect(droppedFile);
    }
  }, [handleFileSelect]);

  const handleAnalyze = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      let response: RiskResponse;
      if (inputMethod === 'file' && file) {
        // Extract text from file
        let fileText: string;
        if (file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')) {
          // Extract text from PDF
          setLoadingMessage('Extracting text from PDF...');
          fileText = await extractTextFromPDF(file);
          setLoadingMessage('Analyzing document and identifying risks...');
        } else {
          // Read text file
          setLoadingMessage('Reading file...');
          fileText = await file.text();
          setLoadingMessage('Analyzing risks...');
        }
        response = await summarizeRisks(undefined, fileText);
      } else if (inputMethod === 'text' && text.trim()) {
        setLoadingMessage('Analyzing risks from text...');
        response = await summarizeRisks(undefined, text);
      } else {
        setError('Please provide a file or paste text');
        setLoading(false);
        setLoadingMessage('');
        return;
      }
      setResult(response);
      setLoadingMessage('');
    } catch (err: any) {
      let errorMessage = err.detail || err.message || 'Failed to analyze risks';
      
      // Provide helpful context for quota errors
      if (errorMessage.includes('quota') || errorMessage.includes('insufficient_quota') || errorMessage.includes('exceeded')) {
        errorMessage += '\n\n⚠️ OpenAI API Quota Exceeded:\n' +
          '• Check your OpenAI billing at https://platform.openai.com/account/billing\n' +
          '• Upgrade your plan or add payment method\n' +
          '• Wait for quota reset if on a usage-based plan';
      }
      
      setError(errorMessage);
      setLoadingMessage('');
    } finally {
      setLoading(false);
    }
  };

  const riskCategories = result
    ? [
        { name: 'Market Risks', risks: result.market_risks },
        { name: 'Operational Risks', risks: result.operational_risks },
        { name: 'Financial Risks', risks: result.financial_risks },
        { name: 'Regulatory Risks', risks: result.regulatory_risks },
        { name: 'Competitive Risks', risks: result.competitive_risks },
        { name: 'Other Risks', risks: result.other_risks || [] },
      ].filter((cat) => cat.risks.length > 0)
    : [];

  const totalRisks = riskCategories.reduce((sum, cat) => sum + cat.risks.length, 0);

  const chartData = riskCategories.map((cat) => ({
    name: cat.name,
    value: cat.risks.length,
  }));

  return (
    <Box>
      <Typography variant="h4" gutterBottom sx={{ mb: 3, fontWeight: 700 }}>
        ⚠️ Risk Analysis
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        Identify and categorize risks from financial documents
      </Typography>

      <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
        <FormControl component="fieldset" sx={{ mb: 3 }}>
          <FormLabel component="legend">Input Method</FormLabel>
          <RadioGroup
            row
            value={inputMethod}
            onChange={(e) => setInputMethod(e.target.value as 'file' | 'text')}
          >
            <FormControlLabel value="file" control={<Radio />} label="Upload File" />
            <FormControlLabel value="text" control={<Radio />} label="Paste Text" />
          </RadioGroup>
        </FormControl>

        {inputMethod === 'file' ? (
          <Box
            onDragEnter={handleDragEnter}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            sx={{
              border: `2px dashed ${isDragging ? 'primary.main' : 'grey.300'}`,
              borderRadius: 2,
              p: 4,
              textAlign: 'center',
              bgcolor: isDragging ? 'action.hover' : 'background.paper',
              cursor: 'pointer',
              transition: 'all 0.3s ease',
              mb: 2,
              '&:hover': {
                borderColor: 'primary.main',
                bgcolor: 'action.hover',
              },
            }}
          >
            <input
              type="file"
              hidden
              accept=".pdf,.txt"
              onChange={handleFileChange}
              id="risk-file-input"
            />
            <label htmlFor="risk-file-input" style={{ cursor: 'pointer', width: '100%', display: 'block' }}>
              {file ? (
                <Box>
                  <InsertDriveFileIcon sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
                  <Typography variant="h6" gutterBottom>
                    {file.name}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Size: {(file.size / (1024 * 1024)).toFixed(2)} MB
                  </Typography>
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
                    Click to select a different file
                  </Typography>
                </Box>
              ) : (
                <Box>
                  <CloudUploadIcon sx={{ fontSize: 64, color: 'primary.main', mb: 2 }} />
                  <Typography variant="h6" gutterBottom>
                    {isDragging ? 'Drop file here' : 'Drag and drop file here'}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    or click to browse
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Supported formats: PDF, TXT
                  </Typography>
                </Box>
              )}
            </label>
          </Box>
        ) : (
          <TextField
            fullWidth
            multiline
            rows={8}
            placeholder="Paste financial document text here..."
            value={text}
            onChange={(e) => setText(e.target.value)}
            sx={{ mb: 2 }}
          />
        )}

        <Button
          variant="contained"
          size="large"
          onClick={handleAnalyze}
          disabled={loading || (inputMethod === 'file' && !file) || (inputMethod === 'text' && !text.trim())}
          fullWidth
          startIcon={loading ? <CircularProgress size={20} /> : <WarningIcon />}
        >
          {loading ? (loadingMessage || 'Analyzing Risks...') : '🚀 Analyze Risks'}
        </Button>
        {loading && loadingMessage && (
          <Box sx={{ mt: 2 }}>
            <LinearProgress />
            <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
              {loadingMessage}
            </Typography>
          </Box>
        )}
      </Paper>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {result && (
        <>
          <Alert severity="success" sx={{ mb: 2 }}>
            ✅ Risk Analysis Complete
          </Alert>

          {totalRisks > 0 ? (
            <>
              <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
                <Typography variant="h6" gutterBottom>
                  📊 Risk Summary ({totalRisks} risks identified)
                </Typography>
                {chartData.length > 0 && (
                  <ResponsiveContainer width="100%" height={400}>
                    <PieChart>
                      <Pie
                        data={chartData}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ name, percent }) => `${name}: ${percent ? (percent * 100).toFixed(0) : 0}%`}
                        outerRadius={120}
                        fill="#8884d8"
                        dataKey="value"
                      >
                        {chartData.map((_, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip />
                      <Legend />
                    </PieChart>
                  </ResponsiveContainer>
                )}
              </Paper>

              <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
                <Typography variant="h6" gutterBottom>
                  📋 Risk Details by Category
                </Typography>
                {riskCategories.map((category, index) => (
                  <Accordion key={index} defaultExpanded={index === 0}>
                    <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                      <Typography sx={{ fontWeight: 600 }}>
                        ⚠️ {category.name} ({category.risks.length} risks)
                      </Typography>
                    </AccordionSummary>
                    <AccordionDetails>
                      <Box component="ul" sx={{ pl: 2 }}>
                        {category.risks.map((risk, riskIndex) => (
                          <li key={riskIndex}>
                            <Typography variant="body2" sx={{ mb: 1 }}>
                              {risk}
                            </Typography>
                          </li>
                        ))}
                      </Box>
                    </AccordionDetails>
                  </Accordion>
                ))}
              </Paper>
            </>
          ) : (
            <Alert severity="info" sx={{ mb: 2 }}>
              ℹ️ No risks were identified in the document.
            </Alert>
          )}
        </>
      )}
    </Box>
  );
}

