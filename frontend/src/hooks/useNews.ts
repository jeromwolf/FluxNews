import { useState, useEffect, useCallback } from 'react';
import { apiClient } from '@/lib/api/client';
import type { NewsArticle, NewsImpact, AIAnalysisResponse } from '@/types/api';

export function useNewsFeed(initialLimit = 20) {
  const [articles, setArticles] = useState<NewsArticle[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(true);
  const [offset, setOffset] = useState(0);

  const fetchArticles = useCallback(async (reset = false) => {
    try {
      setLoading(true);
      const currentOffset = reset ? 0 : offset;
      const data = await apiClient.getNewsFeed(initialLimit, currentOffset);
      
      if (reset) {
        setArticles(data);
        setOffset(initialLimit);
      } else {
        setArticles(prev => [...prev, ...data]);
        setOffset(prev => prev + initialLimit);
      }
      
      setHasMore(data.length === initialLimit);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch news');
    } finally {
      setLoading(false);
    }
  }, [offset, initialLimit]);

  useEffect(() => {
    fetchArticles(true);
  }, []);

  const loadMore = () => {
    if (!loading && hasMore) {
      fetchArticles();
    }
  };

  const refresh = () => {
    setOffset(0);
    fetchArticles(true);
  };

  return {
    articles,
    loading,
    error,
    hasMore,
    loadMore,
    refresh,
  };
}

export function useArticle(articleId: number) {
  const [article, setArticle] = useState<NewsArticle | null>(null);
  const [impacts, setImpacts] = useState<NewsImpact[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchArticleData = async () => {
      try {
        setLoading(true);
        const [articleData, impactsData] = await Promise.all([
          apiClient.getArticle(articleId),
          apiClient.getArticleImpacts(articleId),
        ]);
        
        setArticle(articleData);
        setImpacts(impactsData);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch article');
      } finally {
        setLoading(false);
      }
    };

    if (articleId) {
      fetchArticleData();
    }
  }, [articleId]);

  return {
    article,
    impacts,
    loading,
    error,
  };
}

export function useAIAnalysis() {
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const analyzeArticle = async (articleId: number, userId: string): Promise<AIAnalysisResponse | null> => {
    try {
      setAnalyzing(true);
      setError(null);
      const analysis = await apiClient.analyzeArticle(articleId, userId);
      return analysis;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to analyze article');
      return null;
    } finally {
      setAnalyzing(false);
    }
  };

  return {
    analyzeArticle,
    analyzing,
    error,
  };
}

export function useCompanyNews(companyId: number, limit = 20) {
  const [articles, setArticles] = useState<NewsArticle[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [offset, setOffset] = useState(0);
  const [hasMore, setHasMore] = useState(true);

  const fetchCompanyNews = useCallback(async (reset = false) => {
    try {
      setLoading(true);
      const currentOffset = reset ? 0 : offset;
      const data = await apiClient.getCompanyNews(companyId, limit, currentOffset);
      
      if (reset) {
        setArticles(data);
        setOffset(limit);
      } else {
        setArticles(prev => [...prev, ...data]);
        setOffset(prev => prev + limit);
      }
      
      setHasMore(data.length === limit);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch company news');
    } finally {
      setLoading(false);
    }
  }, [companyId, offset, limit]);

  useEffect(() => {
    fetchCompanyNews(true);
  }, [companyId]);

  const loadMore = () => {
    if (!loading && hasMore) {
      fetchCompanyNews();
    }
  };

  return {
    articles,
    loading,
    error,
    hasMore,
    loadMore,
  };
}