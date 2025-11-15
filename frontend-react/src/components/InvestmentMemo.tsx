import { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  TextField,
  Alert,
  CircularProgress,
  Card,
  CardContent,
  Divider,
} from '@mui/material';
import {
  Description as DescriptionIcon,
  Download as DownloadIcon,
} from '@mui/icons-material';
import { generateMemo } from '../services/api';
import type { MemoResponse } from '../types';

export default function InvestmentMemo() {
  const [companyName, setCompanyName] = useState('');
  const [period, setPeriod] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<MemoResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleGenerate = async () => {
    if (!companyName.trim() || !period.trim()) {
      setError('Please provide both company name and period');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      // Generate memo without file - backend will use uploaded documents if available
      const response = await generateMemo(companyName, period);
      setResult(response);
    } catch (err: any) {
      let errorMessage = err.detail || err.message || 'Failed to generate memo';
      
      // Provide helpful context for quota errors
      if (errorMessage.includes('quota') || errorMessage.includes('insufficient_quota') || errorMessage.includes('exceeded')) {
        errorMessage += '\n\n⚠️ OpenAI API Quota Exceeded:\n' +
          '• Check your OpenAI billing at https://platform.openai.com/account/billing\n' +
          '• Upgrade your plan or add payment method\n' +
          '• Wait for quota reset if on a usage-based plan';
      }
      
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = (format: 'markdown' | 'text') => {
    if (!result || !result.memo) return;

    const blob = new Blob([result.memo], {
      type: format === 'markdown' ? 'text/markdown' : 'text/plain',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${companyName}_${period}_memo.${format === 'markdown' ? 'md' : 'txt'}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom sx={{ mb: 3, fontWeight: 700 }}>
        📝 Generate Investment Memo
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        Generate comprehensive investment memos from financial documents
      </Typography>

      <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
            <TextField
              sx={{ flex: 1, minWidth: 200 }}
              label="Company Name"
              placeholder="e.g., Apple Inc."
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              helperText="Enter the company name for the investment memo"
            />
            <TextField
              sx={{ flex: 1, minWidth: 200 }}
              label="Period"
              placeholder="e.g., Q4 2023"
              value={period}
              onChange={(e) => setPeriod(e.target.value)}
              helperText="Enter the reporting period (e.g., Q4 2023, FY 2023)"
            />
          </Box>
          <Alert severity="info">
            💡 <strong>Tip:</strong> Upload documents first using the Upload Documents page to include KPIs and risks in the memo automatically.
          </Alert>
        </Box>

        <Box sx={{ mt: 3 }}>
          <Button
            variant="contained"
            size="large"
            onClick={handleGenerate}
            disabled={loading || !companyName.trim() || !period.trim()}
            fullWidth
            startIcon={loading ? <CircularProgress size={20} /> : <DescriptionIcon />}
          >
            {loading ? 'Generating Memo...' : '🚀 Generate Investment Memo'}
          </Button>
        </Box>
      </Paper>

      {error && (
        <Alert severity="error" sx={{ mb: 2, whiteSpace: 'pre-wrap' }}>
          {error}
        </Alert>
      )}

      {result && (
        <>
          <Alert severity="success" sx={{ mb: 2 }}>
            ✅ Investment Memo Generated for {companyName} - {period}
          </Alert>

          <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
            <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mb: 2 }}>
              <Card variant="outlined" sx={{ flex: 1, minWidth: 200 }}>
                <CardContent>
                  <Typography variant="h6">{companyName}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Company
                  </Typography>
                </CardContent>
              </Card>
              <Card variant="outlined" sx={{ flex: 1, minWidth: 200 }}>
                <CardContent>
                  <Typography variant="h6">{period}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Period
                  </Typography>
                </CardContent>
              </Card>
              <Card variant="outlined" sx={{ flex: 1, minWidth: 200 }}>
                <CardContent>
                  <Typography variant="h6">
                    {result.generated_at
                      ? new Date(result.generated_at).toLocaleString()
                      : 'Just now'}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Generated
                  </Typography>
                </CardContent>
              </Card>
            </Box>
          </Paper>

          <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              📄 Investment Memo
            </Typography>
            <Divider sx={{ my: 2 }} />
            <Box
              sx={{
                whiteSpace: 'pre-wrap',
                fontFamily: 'monospace',
                bgcolor: 'background.default',
                p: 2,
                borderRadius: 1,
                maxHeight: '600px',
                overflowY: 'auto',
              }}
            >
              <Typography variant="body1">{result.memo}</Typography>
            </Box>
          </Paper>

          <Paper elevation={2} sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Download Memo
            </Typography>
            <Box sx={{ display: 'flex', gap: 2, mt: 2 }}>
              <Button
                variant="outlined"
                startIcon={<DownloadIcon />}
                onClick={() => handleDownload('markdown')}
                fullWidth
              >
                📥 Download as Markdown
              </Button>
              <Button
                variant="outlined"
                startIcon={<DownloadIcon />}
                onClick={() => handleDownload('text')}
                fullWidth
              >
                📄 Download as Text
              </Button>
            </Box>
          </Paper>
        </>
      )}
    </Box>
  );
}

