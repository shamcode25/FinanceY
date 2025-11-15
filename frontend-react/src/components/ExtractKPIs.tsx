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
  Card,
  CardContent,
  Chip,
  LinearProgress,
} from '@mui/material';
import {
  Assessment as AssessmentIcon,
  CloudUpload as CloudUploadIcon,
  InsertDriveFile as InsertDriveFileIcon,
} from '@mui/icons-material';
import { extractKPIs } from '../services/api';
import type { KPIResponse } from '../types';
import { extractTextFromPDF } from '../utils/pdfExtractor';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

export default function ExtractKPIs() {
  const [inputMethod, setInputMethod] = useState<'file' | 'text'>('file');
  const [file, setFile] = useState<File | null>(null);
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingMessage, setLoadingMessage] = useState<string>('');
  const [result, setResult] = useState<KPIResponse | null>(null);
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

  const handleExtract = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      let response: KPIResponse;
      if (inputMethod === 'file' && file) {
        // Extract text from file
        let fileText: string;
        if (file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')) {
          // Extract text from PDF
          setLoadingMessage('Extracting text from PDF...');
          fileText = await extractTextFromPDF(file);
          setLoadingMessage('Analyzing document and extracting KPIs...');
        } else {
          // Read text file
          setLoadingMessage('Reading file...');
          fileText = await file.text();
          setLoadingMessage('Extracting KPIs...');
        }
        response = await extractKPIs(undefined, fileText);
      } else if (inputMethod === 'text' && text.trim()) {
        setLoadingMessage('Extracting KPIs from text...');
        response = await extractKPIs(undefined, text);
      } else {
        setError('Please provide a file or paste text');
        setLoading(false);
        setLoadingMessage('');
        return;
      }
      setResult(response);
      setLoadingMessage('');
    } catch (err: any) {
      let errorMessage = err.detail || err.message || 'Failed to extract KPIs';
      
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

  const numericKPIs = result
    ? Object.entries(result.kpis).filter(([_, value]) => typeof value === 'number')
    : [];
  const textKPIs = result
    ? Object.entries(result.kpis).filter(([_, value]) => typeof value !== 'number')
    : [];

  const chartData = numericKPIs.map(([key, value]) => ({
    name: key.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase()),
    value: Math.abs(value as number),
  }));

  return (
    <Box>
      <Typography variant="h4" gutterBottom sx={{ mb: 3, fontWeight: 700 }}>
        📊 Extract Key Performance Indicators
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        Automatically extract key financial metrics from documents
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
              id="kpi-file-input"
            />
            <label htmlFor="kpi-file-input" style={{ cursor: 'pointer', width: '100%', display: 'block' }}>
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
          onClick={handleExtract}
          disabled={loading || (inputMethod === 'file' && !file) || (inputMethod === 'text' && !text.trim())}
          fullWidth
          startIcon={loading ? <CircularProgress size={20} /> : <AssessmentIcon />}
        >
          {loading ? (loadingMessage || 'Extracting KPIs...') : '🚀 Extract KPIs'}
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
            ✅ KPIs Extracted Successfully
          </Alert>

          {numericKPIs.length > 0 && (
            <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
              <Typography variant="h6" gutterBottom>
                📈 Key Financial Metrics
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, mt: 1 }}>
                {numericKPIs.map(([key, value]) => (
                  <Box key={key} sx={{ minWidth: 200, flex: '1 1 300px' }}>
                    <Card variant="outlined">
                      <CardContent>
                        <Typography variant="h5" color="primary">
                          {typeof value === 'number'
                            ? (key.toLowerCase().includes('revenue') ||
                              key.toLowerCase().includes('income') ||
                              key.toLowerCase().includes('cash') ||
                              key.toLowerCase().includes('flow'))
                              ? `$${value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
                              : value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
                            : value}
                        </Typography>
                        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                          {key.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())}
                        </Typography>
                    </CardContent>
                  </Card>
                  </Box>
                ))}
              </Box>
            </Paper>
          )}

          {chartData.length > 0 && (
            <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
              <Typography variant="h6" gutterBottom>
                📊 KPI Visualization
              </Typography>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="value" fill="#1976d2" />
                </BarChart>
              </ResponsiveContainer>
            </Paper>
          )}

          {textKPIs.length > 0 && (
            <Paper elevation={2} sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                📋 Additional Information
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 2 }}>
                {textKPIs.map(([key, value]) => (
                  <Chip
                    key={key}
                    label={`${key}: ${value}`}
                    variant="outlined"
                  />
                ))}
              </Box>
            </Paper>
          )}
        </>
      )}
    </Box>
  );
}

