/**
 * Type definitions for the application
 */

export interface HealthStatus {
  status: string;
  timestamp: string;
}

export interface Stats {
  retriever: {
    num_documents: number;
    index_exists: boolean;
  };
}

export interface UploadResponse {
  status: string;
  filename: string;
  chunks: number;
  metadata: {
    file_type: string;
    [key: string]: any;
  };
}

export interface QueryResponse {
  answer: string;
  sources: string[];
}

export interface KPIResponse {
  kpis: {
    [key: string]: number | string;
  };
}

export interface RiskResponse {
  market_risks: string[];
  operational_risks: string[];
  financial_risks: string[];
  regulatory_risks: string[];
  competitive_risks: string[];
  other_risks?: string[];
}

export interface MemoResponse {
  memo: string;
  generated_at?: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  sources?: string[];
  timestamp: Date;
}

