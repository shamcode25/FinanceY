import { useState, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  TextField,
  MenuItem,
  Alert,
  LinearProgress,
  Card,
  CardContent,
  Chip,
} from '@mui/material';
import {
  CloudUpload as CloudUploadIcon,
  Description as DescriptionIcon,
  InsertDriveFile as InsertDriveFileIcon,
} from '@mui/icons-material';
import { uploadFile } from '../services/api';
import type { UploadResponse } from '../types';

export default function UploadDocuments() {
  const [file, setFile] = useState<File | null>(null);
  const [docType, setDocType] = useState('auto');
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<UploadResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [uploadedFiles, setUploadedFiles] = useState<string[]>([]);
  const [isDragging, setIsDragging] = useState(false);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      setFile(event.target.files[0]);
      setError(null);
      setResult(null);
    }
  };

  const handleFileSelect = useCallback((selectedFile: File) => {
    // Validate file type
    const validTypes = ['application/pdf', 'text/plain'];
    const validExtensions = ['.pdf', '.txt'];
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

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file to upload');
      return;
    }

    setUploading(true);
    setError(null);
    setResult(null);

    try {
      const response = await uploadFile(file, docType);
      setResult(response);
      setUploadedFiles([...uploadedFiles, response.filename]);
      setFile(null);
      // Reset file input
      const fileInput = document.getElementById('file-input') as HTMLInputElement;
      if (fileInput) fileInput.value = '';
    } catch (err: any) {
      // Extract error message
      let errorMessage = 'Failed to upload file';
      
      if (err?.detail) {
        errorMessage = err.detail;
      } else if (err?.message) {
        errorMessage = err.message;
      } else if (typeof err === 'string') {
        errorMessage = err;
      } else if (err?.response?.data?.detail) {
        errorMessage = err.response.data.detail;
      }
      
      // Provide helpful context for common errors
      if (errorMessage.includes('quota') || errorMessage.includes('insufficient_quota') || errorMessage.includes('exceeded')) {
        errorMessage += '\n\n⚠️ OpenAI API Quota Exceeded:\n' +
          '• Check your OpenAI billing at https://platform.openai.com/account/billing\n' +
          '• Upgrade your plan or add payment method\n' +
          '• Wait for quota reset if on a usage-based plan';
      } else if (errorMessage.includes('OPENAI_API_KEY') || errorMessage.includes('API key')) {
        errorMessage += '\n\n💡 Please set your OPENAI_API_KEY in the .env file to enable document processing.';
      } else if (errorMessage.includes('pdfplumber')) {
        errorMessage += '\n\n💡 Please install pdfplumber: pip install pdfplumber';
      } else if (errorMessage.includes('No content extracted')) {
        errorMessage += '\n\n💡 The file may be empty, corrupted, or in an unsupported format. Try a different file.';
      }
      
      setError(errorMessage);
      console.error('Upload error:', err);
    } finally {
      setUploading(false);
    }
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom sx={{ mb: 3, fontWeight: 700 }}>
        📤 Upload Financial Documents
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        Upload SEC filings (10-K, 10-Q, 8-K), earnings transcripts, or news articles for analysis
      </Typography>

      <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
          <TextField
            sx={{ width: '100%', maxWidth: 400 }}
            select
            label="Document Type"
            value={docType}
            onChange={(e) => setDocType(e.target.value)}
            helperText="Auto-detect or specify document type"
          >
            <MenuItem value="auto">Auto-detect</MenuItem>
            <MenuItem value="filing">SEC Filing</MenuItem>
            <MenuItem value="transcript">Earnings Transcript</MenuItem>
            <MenuItem value="news">News Article</MenuItem>
          </TextField>

          {/* Drag and Drop Zone */}
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
              '&:hover': {
                borderColor: 'primary.main',
                bgcolor: 'action.hover',
              },
            }}
          >
            <input
              id="file-input"
              type="file"
              hidden
              accept=".pdf,.txt"
              onChange={handleFileChange}
            />
            <label htmlFor="file-input" style={{ cursor: 'pointer', width: '100%', display: 'block' }}>
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
                    Supported formats: PDF, TXT (Max 200MB)
                  </Typography>
                </Box>
              )}
            </label>
          </Box>
        </Box>

        {uploading && (
          <Box sx={{ mt: 2 }}>
            <LinearProgress />
            <Typography variant="caption" color="text.secondary" sx={{ mt: 1 }}>
              Processing document and generating embeddings...
            </Typography>
          </Box>
        )}

        <Box sx={{ mt: 3 }}>
          <Button
            variant="contained"
            size="large"
            onClick={handleUpload}
            disabled={!file || uploading}
            fullWidth
          >
            {uploading ? 'Uploading...' : '🚀 Upload and Process'}
          </Button>
        </Box>
      </Paper>

      {error && (
        <Alert severity="error" sx={{ mb: 2, whiteSpace: 'pre-wrap' }}>
          {error}
        </Alert>
      )}

      {result && (
        <Alert severity="success" sx={{ mb: 2 }}>
          ✅ Successfully uploaded and processed: {result.filename}
        </Alert>
      )}

      {result && (
        <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Upload Details
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mt: 1 }}>
            <Card variant="outlined" sx={{ flex: 1, minWidth: 150 }}>
              <CardContent>
                <Typography variant="h4">{result.chunks}</Typography>
                <Typography variant="body2" color="text.secondary">
                  Chunks Created
                </Typography>
              </CardContent>
            </Card>
            <Card variant="outlined" sx={{ flex: 1, minWidth: 150 }}>
              <CardContent>
                <Typography variant="h4">✅</Typography>
                <Typography variant="body2" color="text.secondary">
                  Status
                </Typography>
              </CardContent>
            </Card>
            <Card variant="outlined" sx={{ flex: 1, minWidth: 150 }}>
              <CardContent>
                <Typography variant="h4">
                  {result.metadata.file_type || 'Unknown'}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  File Type
                </Typography>
              </CardContent>
            </Card>
          </Box>
        </Paper>
      )}

      {uploadedFiles.length > 0 && (
        <Paper elevation={2} sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            📁 Uploaded Files
          </Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 2 }}>
            {uploadedFiles.map((filename, index) => (
              <Chip
                key={index}
                icon={<DescriptionIcon />}
                label={filename}
                color="success"
                variant="outlined"
              />
            ))}
          </Box>
        </Paper>
      )}
    </Box>
  );
}

