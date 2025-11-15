/**
 * API service for communicating with the FastAPI backend
 */
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      // Server responded with error
      const errorData = error.response.data;
      // Ensure we always have a detail field
      if (typeof errorData === 'string') {
        return Promise.reject({ detail: errorData });
      } else if (errorData && errorData.detail) {
        return Promise.reject(errorData);
      } else {
        return Promise.reject({ 
          detail: errorData?.message || errorData || `Server error: ${error.response.status}` 
        });
      }
    } else if (error.request) {
      // Request made but no response
      return Promise.reject({ detail: 'Cannot connect to API. Make sure the backend is running on http://localhost:8000' });
    } else {
      // Something else happened
      return Promise.reject({ detail: error.message || 'An unexpected error occurred' });
    }
  }
);

// Health check
export const checkHealth = async () => {
  const response = await api.get('/health');
  return response.data;
};

// Get statistics
export const getStats = async () => {
  const response = await api.get('/stats');
  return response.data;
};

// Upload file
export const uploadFile = async (file: File, docType: string = 'auto') => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('doc_type', docType);
  
  const response = await api.post('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

// Query documents
export const queryDocuments = async (question: string) => {
  const response = await api.post('/query', { question });
  return response.data;
};

// Extract KPIs
export const extractKPIs = async (file?: File, documentText?: string, filePath?: string) => {
  if (file) {
    // For text files, extract text
    if (file.type === 'text/plain' || file.name.endsWith('.txt')) {
      const text = await file.text();
      const response = await api.post('/extract-kpis', { document_text: text });
      return response.data;
    } else if (file.type === 'application/pdf' || file.name.endsWith('.pdf')) {
      // For PDF, create a temporary file and send file_path
      // In a real app, you might want to upload the file first
      // For now, we'll extract text if possible, or show an error
      throw new Error('PDF files need to be uploaded first. Please use the Upload Documents page.');
    } else {
      // Try to extract as text
      try {
        const text = await file.text();
        const response = await api.post('/extract-kpis', { document_text: text });
        return response.data;
      } catch (error) {
        throw new Error('Unsupported file type. Please upload a text file or paste text.');
      }
    }
  } else if (documentText) {
    const response = await api.post('/extract-kpis', { document_text: documentText });
    return response.data;
  } else if (filePath) {
    const response = await api.post('/extract-kpis', { file_path: filePath });
    return response.data;
  } else {
    throw new Error('Either file, documentText, or filePath must be provided');
  }
};

// Summarize risks
export const summarizeRisks = async (file?: File, documentText?: string, filePath?: string) => {
  if (file) {
    // For text files, extract text
    if (file.type === 'text/plain' || file.name.endsWith('.txt')) {
      const text = await file.text();
      const response = await api.post('/summarize-risks', { document_text: text });
      return response.data;
    } else if (file.type === 'application/pdf' || file.name.endsWith('.pdf')) {
      throw new Error('PDF files need to be uploaded first. Please use the Upload Documents page.');
    } else {
      try {
        const text = await file.text();
        const response = await api.post('/summarize-risks', { document_text: text });
        return response.data;
      } catch (error) {
        throw new Error('Unsupported file type. Please upload a text file or paste text.');
      }
    }
  } else if (documentText) {
    const response = await api.post('/summarize-risks', { document_text: documentText });
    return response.data;
  } else if (filePath) {
    const response = await api.post('/summarize-risks', { file_path: filePath });
    return response.data;
  } else {
    throw new Error('Either file, documentText, or filePath must be provided');
  }
};

// Generate investment memo
export const generateMemo = async (
  companyName: string,
  period: string,
  file?: File,
  filePath?: string
) => {
  const data: any = {
    company_name: companyName,
    period: period,
  };
  
  if (file) {
    // For text files, we can extract text, but the backend expects file_path
    // For now, we'll show an error for files - they should be uploaded first
    if (file.type === 'application/pdf' || file.name.endsWith('.pdf')) {
      throw new Error('PDF files need to be uploaded first. Please use the Upload Documents page.');
    } else {
      // For text files, we can extract text but backend might need file_path
      // Let's try without file for now - the memo generation can work without it
      // If file is provided, user should upload it first
      throw new Error('Please upload the file first using the Upload Documents page, then generate the memo.');
    }
  } else if (filePath) {
    data.file_path = filePath;
  }
  
  const response = await api.post('/generate-memo', data);
  return response.data;
};

export default api;

