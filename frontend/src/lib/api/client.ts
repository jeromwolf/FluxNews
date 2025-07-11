import { createClientComponentClient } from '@supabase/auth-helpers-nextjs';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export interface ApiError {
  detail: string;
  status?: number;
}

class ApiClient {
  private supabase = createClientComponentClient();

  private async getAuthToken(): Promise<string | null> {
    const { data: { session } } = await this.supabase.auth.getSession();
    return session?.access_token || null;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const token = await this.getAuthToken();
    
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const error: ApiError = await response.json();
      throw new Error(error.detail || 'API request failed');
    }

    return response.json();
  }

  // Auth endpoints
  async login(email: string, password: string) {
    return this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
  }

  async signup(email: string, password: string, name: string) {
    return this.request('/auth/signup', {
      method: 'POST',
      body: JSON.stringify({ email, password, name }),
    });
  }

  async logout() {
    return this.request('/auth/logout', {
      method: 'POST',
    });
  }

  // News endpoints
  async getNewsFeed(limit = 20, offset = 0, processedOnly = true) {
    const params = new URLSearchParams({
      limit: limit.toString(),
      offset: offset.toString(),
      processed_only: processedOnly.toString(),
    });
    return this.request(`/news?${params}`);
  }

  async getArticle(articleId: number) {
    return this.request(`/news/${articleId}`);
  }

  async getArticleImpacts(articleId: number) {
    return this.request(`/news/${articleId}/impacts`);
  }

  async getCompanyNews(companyId: number, limit = 20, offset = 0) {
    const params = new URLSearchParams({
      limit: limit.toString(),
      offset: offset.toString(),
    });
    return this.request(`/news/company/${companyId}?${params}`);
  }

  async analyzeArticle(articleId: number, userId: string) {
    return this.request('/news/analyze', {
      method: 'POST',
      body: JSON.stringify({ article_id: articleId, user_id: userId }),
    });
  }

  // Company endpoints
  async getCompanies(sector?: string, limit = 20, offset = 0) {
    const params = new URLSearchParams({
      limit: limit.toString(),
      offset: offset.toString(),
    });
    if (sector) {
      params.append('sector', sector);
    }
    return this.request(`/companies?${params}`);
  }

  async getCompany(companyId: number) {
    return this.request(`/companies/${companyId}`);
  }

  async getCompanyRelationships(companyId: number) {
    return this.request(`/companies/${companyId}/relationships`);
  }

  async getCompanyNetwork(sector?: string, maxCompanies = 50) {
    const params = new URLSearchParams({
      max_companies: maxCompanies.toString(),
    });
    if (sector) {
      params.append('sector', sector);
    }
    return this.request(`/companies/network?${params}`);
  }

  async searchCompanies(query: string, limit = 10) {
    const params = new URLSearchParams({
      q: query,
      limit: limit.toString(),
    });
    return this.request(`/companies/search?${params}`);
  }

  // Watchlist endpoints
  async getUserWatchlist(userId: string) {
    return this.request(`/watchlist?user_id=${userId}`);
  }

  async addToWatchlist(userId: string, companyId: number, alertEnabled = false, alertThreshold?: number) {
    return this.request(`/watchlist?user_id=${userId}`, {
      method: 'POST',
      body: JSON.stringify({
        company_id: companyId,
        alert_enabled: alertEnabled,
        alert_threshold: alertThreshold,
      }),
    });
  }

  async updateWatchlistItem(watchlistId: number, userId: string, alertEnabled?: boolean, alertThreshold?: number) {
    return this.request(`/watchlist/${watchlistId}?user_id=${userId}`, {
      method: 'PUT',
      body: JSON.stringify({
        alert_enabled: alertEnabled,
        alert_threshold: alertThreshold,
      }),
    });
  }

  async removeFromWatchlist(watchlistId: number, userId: string) {
    return this.request(`/watchlist/${watchlistId}?user_id=${userId}`, {
      method: 'DELETE',
    });
  }

  async getTriggeredAlerts(userId: string) {
    return this.request(`/watchlist/alerts?user_id=${userId}`);
  }
}

export const apiClient = new ApiClient();