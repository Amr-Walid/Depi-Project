import { useState, useEffect, useCallback } from "react";
import { apiClient } from "@/lib/api-client";

export interface MarketStats {
  total_market_cap: number;
  total_volume_24h: number;
  active_coins: number;
  btc_dominance: number;
  top_gainers: any[];
  top_losers: any[];
  last_updated: string;
}

export interface MarketSentiment {
  overall_score: number;
  overall_label: string; // Bullish, Bearish, Neutral
  positive_pct: number;
  negative_pct: number;
  neutral_pct: number;
  article_count: number;
  last_updated?: string;
  status?: string;
}

export function useMarket() {
  const [stats, setStats] = useState<MarketStats | null>(null);
  const [sentiment, setSentiment] = useState<MarketSentiment | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchMarketData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [statsData, sentimentData] = await Promise.all([
        apiClient<MarketStats>("/api/v1/market/overview"),
        apiClient<MarketSentiment>("/api/v1/market/sentiment"),
      ]);
      setStats(statsData);
      setSentiment(sentimentData);
    } catch (err: any) {
      setError(err.message || "Failed to fetch market data");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchMarketData();
  }, [fetchMarketData]);

  return { stats, sentiment, isLoading, error, refresh: fetchMarketData };
}
