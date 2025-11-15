import { useState, useRef, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Alert,
  CircularProgress,
  Avatar,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  Chip,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import {
  Send as SendIcon,
  Person as PersonIcon,
  SmartToy as SmartToyIcon,
  ExpandMore as ExpandMoreIcon,
  Description as DescriptionIcon,
} from '@mui/icons-material';
import { queryDocuments, getStats } from '../services/api';
import type { ChatMessage } from '../types';

export default function QAChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [numDocuments, setNumDocuments] = useState(0);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadStats();
    // Poll for stats every 30 seconds
    const interval = setInterval(loadStats, 30000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const loadStats = async () => {
    try {
      const stats = await getStats();
      setNumDocuments(stats.retriever.num_documents);
    } catch (error) {
      console.error('Failed to load stats:', error);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim() || loading) return;

    if (numDocuments === 0) {
      setError('No documents uploaded yet! Please upload documents first.');
      return;
    }

    const userMessage: ChatMessage = {
      role: 'user',
      content: question,
      timestamp: new Date(),
    };

    setMessages([...messages, userMessage]);
    setQuestion('');
    setLoading(true);
    setError(null);

    try {
      const response = await queryDocuments(question);
      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: response.answer,
        sources: response.sources,
        timestamp: new Date(),
      };
      setMessages([...messages, userMessage, assistantMessage]);
    } catch (err: any) {
      let errorMessage = err.detail || err.message || 'Failed to get answer';
      
      // Provide helpful context for quota errors
      if (errorMessage.includes('quota') || errorMessage.includes('insufficient_quota') || errorMessage.includes('exceeded')) {
        errorMessage += '\n\n⚠️ OpenAI API Quota Exceeded:\n' +
          '• Check your OpenAI billing at https://platform.openai.com/account/billing\n' +
          '• Upgrade your plan or add payment method\n' +
          '• Wait for quota reset if on a usage-based plan';
      }
      
      setError(errorMessage);
      // Remove the user message if there was an error
      setMessages(messages);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom sx={{ mb: 3, fontWeight: 700 }}>
        💬 Ask Questions About Your Documents
      </Typography>
      
      {numDocuments === 0 ? (
        <Alert severity="warning" sx={{ mb: 2 }}>
          ⚠️ No documents uploaded yet! Please upload documents first to ask questions.
        </Alert>
      ) : (
        <Alert severity="success" sx={{ mb: 2 }}>
          📚 {numDocuments} document(s) ready for analysis
        </Alert>
      )}

      {numDocuments > 0 && (
        <>
          {/* Chat Messages */}
          <Paper
            elevation={2}
            sx={{
              p: 2,
              mb: 2,
              minHeight: '400px',
              maxHeight: '600px',
              overflowY: 'auto',
              bgcolor: 'background.default',
            }}
          >
            {messages.length === 0 ? (
              <Box sx={{ textAlign: 'center', py: 4, color: 'text.secondary' }}>
                <Typography variant="body1" gutterBottom>
                  💡 Example questions you can ask:
                </Typography>
                <Typography variant="body2" component="div" sx={{ mt: 2 }}>
                  <ul style={{ textAlign: 'left', display: 'inline-block' }}>
                    <li>What was the revenue for the fiscal year?</li>
                    <li>What are the main risks mentioned?</li>
                    <li>How did operating margins change?</li>
                    <li>What is the debt-to-equity ratio?</li>
                  </ul>
                </Typography>
              </Box>
            ) : (
              <List>
                {messages.map((message, index) => (
                  <ListItem
                    key={index}
                    sx={{
                      flexDirection: message.role === 'user' ? 'row-reverse' : 'row',
                      alignItems: 'flex-start',
                    }}
                  >
                    <ListItemAvatar>
                      <Avatar
                        sx={{
                          bgcolor: message.role === 'user' ? 'primary.main' : 'secondary.main',
                        }}
                      >
                        {message.role === 'user' ? <PersonIcon /> : <SmartToyIcon />}
                      </Avatar>
                    </ListItemAvatar>
                    <ListItemText
                      primary={
                        <Box
                          sx={{
                            bgcolor:
                              message.role === 'user' ? 'primary.light' : 'grey.200',
                            p: 2,
                            borderRadius: 2,
                            maxWidth: '70%',
                            ml: message.role === 'user' ? 'auto' : 0,
                            mr: message.role === 'user' ? 0 : 'auto',
                          }}
                        >
                          <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                            {message.content}
                          </Typography>
                          {message.sources && message.sources.length > 0 && (
                            <Accordion sx={{ mt: 2, boxShadow: 'none' }}>
                              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                                <Typography variant="caption">
                                  📚 Sources ({message.sources.length})
                                </Typography>
                              </AccordionSummary>
                              <AccordionDetails>
                                {message.sources.map((source, idx) => (
                                  <Chip
                                    key={idx}
                                    icon={<DescriptionIcon />}
                                    label={source}
                                    size="small"
                                    sx={{ mr: 1, mb: 1 }}
                                  />
                                ))}
                              </AccordionDetails>
                            </Accordion>
                          )}
                          <Typography
                            variant="caption"
                            color="text.secondary"
                            sx={{ display: 'block', mt: 1 }}
                          >
                            {message.timestamp.toLocaleTimeString()}
                          </Typography>
                        </Box>
                      }
                    />
                  </ListItem>
                ))}
                {loading && (
                  <ListItem>
                    <ListItemAvatar>
                      <Avatar sx={{ bgcolor: 'secondary.main' }}>
                        <SmartToyIcon />
                      </Avatar>
                    </ListItemAvatar>
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                          <CircularProgress size={20} />
                          <Typography variant="body2" color="text.secondary">
                            Thinking...
                          </Typography>
                        </Box>
                      }
                    />
                  </ListItem>
                )}
                <div ref={messagesEndRef} />
              </List>
            )}
          </Paper>

          {/* Input Form */}
          <Paper elevation={2} sx={{ p: 2 }}>
            <form onSubmit={handleSubmit}>
              <Box sx={{ display: 'flex', gap: 2 }}>
                <TextField
                  fullWidth
                  multiline
                  rows={2}
                  placeholder="Ask a question about your documents..."
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  disabled={loading}
                />
                <Button
                  type="submit"
                  variant="contained"
                  size="large"
                  disabled={!question.trim() || loading}
                  startIcon={loading ? <CircularProgress size={20} /> : <SendIcon />}
                  sx={{ minWidth: 120 }}
                >
                  {loading ? 'Asking...' : 'Ask'}
                </Button>
              </Box>
            </form>
          </Paper>
        </>
      )}

      {error && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {error}
        </Alert>
      )}
    </Box>
  );
}

