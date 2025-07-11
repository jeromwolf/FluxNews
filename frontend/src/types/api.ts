// News types
export interface NewsArticle {
  id: number;
  title: string;
  content: string;
  url: string;
  source: string;
  published_date: string;
  sentiment_score?: number;
  processed: boolean;
}

export interface NewsImpact {
  article_id: number;
  company_id: number;
  impact_score: number;
  confidence_score: number;
  explanation: string;
}

export interface AIAnalysisResponse {
  article_id: number;
  summary: string;
  key_companies: Array<{
    name: string;
    role: string;
    ticker?: string;
  }>;
  impact_analysis: {
    [companyName: string]: {
      impact: 'positive' | 'negative' | 'neutral';
      score: number;
      reason: string;
    };
  };
  sentiment: {
    positive: number;
    negative: number;
    neutral: number;
  };
}

// Company types
export interface Company {
  id: number;
  name: string;
  ticker: string;
  sector: string;
  country: string;
  description?: string;
}

export interface CompanyRelationship {
  id: number;
  company_id_1: number;
  company_id_2: number;
  relationship_type: string;
  description?: string;
}

export interface NetworkNode {
  id: number;
  name: string;
  ticker: string;
  sector: string;
  x?: number;
  y?: number;
}

export interface NetworkEdge {
  source: number;
  target: number;
  type: string;
  weight: number;
}

export interface CompanyNetwork {
  nodes: NetworkNode[];
  edges: NetworkEdge[];
}

// Watchlist types
export interface WatchlistCompany {
  id: number;
  user_id: string;
  company_id: number;
  company_name: string;
  company_ticker: string;
  company_sector: string;
  alert_enabled: boolean;
  alert_threshold?: number;
  created_at: string;
  recent_impact_score?: number;
}

export interface TriggeredAlert {
  company_name: string;
  company_ticker: string;
  impact_score: number;
  threshold: number;
  article_title: string;
  article_date: string;
  explanation: string;
}

// Auth types
export interface LoginResponse {
  access_token: string;
  user: {
    id: string;
    email: string;
    user_metadata?: {
      name?: string;
    };
  };
}

export interface SignupResponse {
  message: string;
  user: {
    id: string;
    email: string;
  };
}