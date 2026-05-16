import { useState, useEffect, useCallback } from "react";
import { apiClient } from "@/lib/api-client";

export interface WatchlistItem {
  id: number;
  symbol: string;
  created_at: string;
}

export function useWatchlist() {
  const [items, setItems] = useState<WatchlistItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchWatchlist = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await apiClient<WatchlistItem[]>("/api/v1/watchlists");
      setItems(data);
    } catch (err: any) {
      setError(err.message || "Failed to fetch watchlist");
    } finally {
      setIsLoading(false);
    }
  }, []);

  const addToWatchlist = async (symbol: string) => {
    try {
      await apiClient("/api/v1/watchlists", {
        method: "POST",
        body: JSON.stringify({ symbol }),
      });
      fetchWatchlist(); // Refresh list
    } catch (err: any) {
      throw new Error(err.message || "Failed to add to watchlist");
    }
  };

  const removeFromWatchlist = async (id: number) => {
    try {
      await apiClient(`/api/v1/watchlists/${id}`, {
        method: "DELETE",
      });
      setItems((prev) => prev.filter((item) => item.id !== id));
    } catch (err: any) {
      throw new Error(err.message || "Failed to remove from watchlist");
    }
  };

  useEffect(() => {
    fetchWatchlist();
  }, [fetchWatchlist]);

  return { items, isLoading, error, addToWatchlist, removeFromWatchlist, refresh: fetchWatchlist };
}
