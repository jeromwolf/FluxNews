import { useState, useEffect, useCallback } from 'react';
import { apiClient } from '@/lib/api/client';
import type { Company, CompanyRelationship, CompanyNetwork } from '@/types/api';

export function useCompanies(sector?: string, limit = 20) {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [offset, setOffset] = useState(0);
  const [hasMore, setHasMore] = useState(true);

  const fetchCompanies = useCallback(async (reset = false) => {
    try {
      setLoading(true);
      const currentOffset = reset ? 0 : offset;
      const data = await apiClient.getCompanies(sector, limit, currentOffset);
      
      if (reset) {
        setCompanies(data);
        setOffset(limit);
      } else {
        setCompanies(prev => [...prev, ...data]);
        setOffset(prev => prev + limit);
      }
      
      setHasMore(data.length === limit);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch companies');
    } finally {
      setLoading(false);
    }
  }, [sector, offset, limit]);

  useEffect(() => {
    fetchCompanies(true);
  }, [sector]);

  const loadMore = () => {
    if (!loading && hasMore) {
      fetchCompanies();
    }
  };

  return {
    companies,
    loading,
    error,
    hasMore,
    loadMore,
  };
}

export function useCompany(companyId: number) {
  const [company, setCompany] = useState<Company | null>(null);
  const [relationships, setRelationships] = useState<CompanyRelationship[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchCompanyData = async () => {
      try {
        setLoading(true);
        const [companyData, relationshipsData] = await Promise.all([
          apiClient.getCompany(companyId),
          apiClient.getCompanyRelationships(companyId),
        ]);
        
        setCompany(companyData);
        setRelationships(relationshipsData);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch company');
      } finally {
        setLoading(false);
      }
    };

    if (companyId) {
      fetchCompanyData();
    }
  }, [companyId]);

  return {
    company,
    relationships,
    loading,
    error,
  };
}

export function useCompanyNetwork(sector?: string, maxCompanies = 50) {
  const [network, setNetwork] = useState<CompanyNetwork | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchNetwork = async () => {
      try {
        setLoading(true);
        const data = await apiClient.getCompanyNetwork(sector, maxCompanies);
        setNetwork(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch network');
      } finally {
        setLoading(false);
      }
    };

    fetchNetwork();
  }, [sector, maxCompanies]);

  return {
    network,
    loading,
    error,
  };
}

export function useCompanySearch() {
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const searchCompanies = async (query: string, limit = 10): Promise<Company[]> => {
    try {
      setSearching(true);
      setError(null);
      const results = await apiClient.searchCompanies(query, limit);
      return results;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to search companies');
      return [];
    } finally {
      setSearching(false);
    }
  };

  return {
    searchCompanies,
    searching,
    error,
  };
}