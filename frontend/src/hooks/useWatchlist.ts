import { useState, useEffect, useCallback } from 'react';
import { apiClient } from '@/lib/api/client';
import { useAuth } from '@/hooks/useAuth';
import type { WatchlistCompany, TriggeredAlert } from '@/types/api';

export function useWatchlist() {
  const { user } = useAuth();
  const [watchlist, setWatchlist] = useState<WatchlistCompany[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchWatchlist = useCallback(async () => {
    if (!user) return;
    
    try {
      setLoading(true);
      const data = await apiClient.getUserWatchlist(user.id);
      setWatchlist(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch watchlist');
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => {
    fetchWatchlist();
  }, [fetchWatchlist]);

  const addToWatchlist = async (companyId: number, alertEnabled = false, alertThreshold?: number) => {
    if (!user) throw new Error('User not authenticated');
    
    try {
      await apiClient.addToWatchlist(user.id, companyId, alertEnabled, alertThreshold);
      await fetchWatchlist(); // Refresh the list
      return true;
    } catch (err) {
      throw new Error(err instanceof Error ? err.message : 'Failed to add to watchlist');
    }
  };

  const updateWatchlistItem = async (
    watchlistId: number, 
    alertEnabled?: boolean, 
    alertThreshold?: number
  ) => {
    if (!user) throw new Error('User not authenticated');
    
    try {
      await apiClient.updateWatchlistItem(watchlistId, user.id, alertEnabled, alertThreshold);
      await fetchWatchlist(); // Refresh the list
      return true;
    } catch (err) {
      throw new Error(err instanceof Error ? err.message : 'Failed to update watchlist item');
    }
  };

  const removeFromWatchlist = async (watchlistId: number) => {
    if (!user) throw new Error('User not authenticated');
    
    try {
      await apiClient.removeFromWatchlist(watchlistId, user.id);
      await fetchWatchlist(); // Refresh the list
      return true;
    } catch (err) {
      throw new Error(err instanceof Error ? err.message : 'Failed to remove from watchlist');
    }
  };

  return {
    watchlist,
    loading,
    error,
    addToWatchlist,
    updateWatchlistItem,
    removeFromWatchlist,
    refresh: fetchWatchlist,
  };
}

export function useWatchlistAlerts() {
  const { user } = useAuth();
  const [alerts, setAlerts] = useState<TriggeredAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAlerts = async () => {
      if (!user) return;
      
      try {
        setLoading(true);
        const data = await apiClient.getTriggeredAlerts(user.id);
        setAlerts(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch alerts');
      } finally {
        setLoading(false);
      }
    };

    fetchAlerts();
  }, [user]);

  return {
    alerts,
    loading,
    error,
  };
}