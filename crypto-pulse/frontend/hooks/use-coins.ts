import { useState, useEffect, useCallback } from "react";
import { apiClient } from "@/lib/api-client";

export interface CoinInfo {
  symbol: string;
  name: string;
  is_active: boolean;
}

export interface CoinSummary {
  symbol: string;
  trading_date: string;
  day_open: number;
  day_close: number;
  day_high: number;
  day_low: number;
  total_volume: number;
  avg_price: number;
  price_change_pct: number;
  tick_count: number;
  // Computed values for convenience
  price?: number;
}

export interface PricePoint {
  timestamp: string;
  price: number;
  volume: number;
}

export function useCoins() {
  const [coins, setCoins] = useState<CoinInfo[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchCoins = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await apiClient<CoinInfo[]>("/api/v1/coins");
      setCoins(data);
    } catch (err: any) {
      setError(err.message || "Failed to fetch coins");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCoins();
  }, [fetchCoins]);

  return { coins, isLoading, error, refresh: fetchCoins };
}

export function useCoinDetail(symbol: string) {
  const [summary, setSummary] = useState<CoinSummary | null>(null);
  const [history, setHistory] = useState<PricePoint[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDetail = useCallback(async () => {
    if (!symbol) return;
    setIsLoading(true);
    setError(null);
    try {
      const [summaryData, historyData] = await Promise.all([
        apiClient<CoinSummary>(`/api/v1/coins/${symbol}/summary`),
        apiClient<{ prices: PricePoint[] }>(`/api/v1/coins/${symbol}/prices?days=30`),
      ]);
      // Add computed price field for backwards compatibility with UI components
      const enhancedSummary = {
        ...summaryData,
        price: summaryData.day_close,
      };
      setSummary(enhancedSummary);
      const mappedHistory = (historyData.prices || []).map((p: any) => ({
        ...p,
        price: p.close || p.price || 0,
      }));
      setHistory(mappedHistory);
    } catch (err: any) {
      setError(err.message || "Failed to fetch coin details");
    } finally {
      setIsLoading(false);
    }
  }, [symbol]);

  useEffect(() => {
    fetchDetail();
  }, [fetchDetail]);

  return { summary, history, isLoading, error, refresh: fetchDetail };
}
