import { useState, useEffect, useCallback } from "react";
import { apiClient } from "@/lib/api-client";

export interface PortfolioPosition {
  id: number;
  symbol: string;
  quantity: number;
  avg_buy_price: number;
  created_at: string;
}

export function usePortfolio() {
  const [positions, setPositions] = useState<PortfolioPosition[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchPortfolio = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await apiClient<PortfolioPosition[]>("/api/v1/portfolios");
      setPositions(data);
    } catch (err: any) {
      setError(err.message || "Failed to fetch portfolio");
    } finally {
      setIsLoading(false);
    }
  }, []);

  const addPosition = async (data: { symbol: string; quantity: number; avg_buy_price: number }) => {
    try {
      await apiClient("/api/v1/portfolios", {
        method: "POST",
        body: JSON.stringify(data),
      });
      fetchPortfolio();
    } catch (err: any) {
      throw new Error(err.message || "Failed to add position");
    }
  };

  const updatePosition = async (id: number, data: { quantity?: number; avg_buy_price?: number }) => {
    try {
      await apiClient(`/api/v1/portfolios/${id}`, {
        method: "PUT",
        body: JSON.stringify(data),
      });
      fetchPortfolio();
    } catch (err: any) {
      throw new Error(err.message || "Failed to update position");
    }
  };

  const deletePosition = async (id: number) => {
    try {
      await apiClient(`/api/v1/portfolios/${id}`, {
        method: "DELETE",
      });
      setPositions((prev) => prev.filter((p) => p.id !== id));
    } catch (err: any) {
      throw new Error(err.message || "Failed to delete position");
    }
  };

  useEffect(() => {
    fetchPortfolio();
  }, [fetchPortfolio]);

  return { positions, isLoading, error, addPosition, updatePosition, deletePosition, refresh: fetchPortfolio };
}
