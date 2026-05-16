import { useState, useEffect, useCallback } from "react";
import { apiClient } from "@/lib/api-client";

export interface AlertItem {
  id: number;
  symbol: string;
  condition: "above" | "below";
  threshold: number;
  is_active: boolean;
  created_at: string;
}

export function useAlerts() {
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAlerts = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await apiClient<AlertItem[]>("/api/v1/alerts");
      setAlerts(data);
    } catch (err: any) {
      setError(err.message || "Failed to fetch alerts");
    } finally {
      setIsLoading(false);
    }
  }, []);

  const createAlert = async (data: { symbol: string; condition: string; threshold: number }) => {
    try {
      await apiClient("/api/v1/alerts", {
        method: "POST",
        body: JSON.stringify(data),
      });
      fetchAlerts();
    } catch (err: any) {
      throw new Error(err.message || "Failed to create alert");
    }
  };

  const toggleAlert = async (id: number, is_active: boolean) => {
    try {
      await apiClient(`/api/v1/alerts/${id}`, {
        method: "PUT",
        body: JSON.stringify({ is_active }),
      });
      setAlerts((prev) =>
        prev.map((a) => (a.id === id ? { ...a, is_active } : a))
      );
    } catch (err: any) {
      throw new Error(err.message || "Failed to toggle alert");
    }
  };

  const deleteAlert = async (id: number) => {
    try {
      await apiClient(`/api/v1/alerts/${id}`, {
        method: "DELETE",
      });
      setAlerts((prev) => prev.filter((a) => a.id !== id));
    } catch (err: any) {
      throw new Error(err.message || "Failed to delete alert");
    }
  };

  useEffect(() => {
    fetchAlerts();
  }, [fetchAlerts]);

  return { alerts, isLoading, error, createAlert, toggleAlert, deleteAlert, refresh: fetchAlerts };
}
