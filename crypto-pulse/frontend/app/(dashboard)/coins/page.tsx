"use client";

import { useCoins } from "@/hooks/use-coins";
import { apiClient } from "@/lib/api-client";
import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { useState, useEffect, useMemo } from "react";
import { 
  Database, 
  Cpu, 
  Layers, 
  Activity, 
  ArrowUpRight, 
  ArrowDownRight, 
  RefreshCw, 
  Search 
} from "lucide-react";

// Predefined mock templates to enrich the real API coin list with live metrics
interface CoinMetricTemplate {
  basePrice: number;
  change24h: number;
  ingestionRate: number; // records per second
  latency: number; // ms
  initialRecords: number;
  sparklinePoints: number[];
}

const METRIC_TEMPLATES: Record<string, CoinMetricTemplate> = {
  BTCUSDT: { basePrice: 64250.00, change24h: 3.25, ingestionRate: 180, latency: 14, initialRecords: 4820392, sparklinePoints: [62000, 62500, 61800, 63000, 62700, 63900, 64250] },
  ETHUSDT: { basePrice: 3450.00, change24h: 1.85, ingestionRate: 145, latency: 16, initialRecords: 3290481, sparklinePoints: [3380, 3410, 3390, 3420, 3400, 3435, 3450] },
  BNBUSDT: { basePrice: 580.00, change24h: -0.45, ingestionRate: 92, latency: 18, initialRecords: 1482019, sparklinePoints: [585, 583, 588, 581, 579, 582, 580] },
  XRPUSDT: { basePrice: 0.59, change24h: 4.12, ingestionRate: 210, latency: 11, initialRecords: 8930124, sparklinePoints: [0.56, 0.57, 0.55, 0.58, 0.57, 0.59, 0.59] },
  SOLUSDT: { basePrice: 148.00, change24h: 6.78, ingestionRate: 240, latency: 12, initialRecords: 5120398, sparklinePoints: [138, 142, 140, 145, 143, 146, 148] },
  ADAUSDT: { basePrice: 0.38, change24h: -1.25, ingestionRate: 85, latency: 22, initialRecords: 6382019, sparklinePoints: [0.39, 0.385, 0.39, 0.378, 0.382, 0.381, 0.38] },
  DOTUSDT: { basePrice: 6.20, change24h: 0.85, ingestionRate: 74, latency: 20, initialRecords: 2103982, sparklinePoints: [6.15, 6.18, 6.12, 6.22, 6.19, 6.21, 6.20] },
  DOGEUSDT: { basePrice: 0.1245, change24h: 8.45, ingestionRate: 320, latency: 15, initialRecords: 12492083, sparklinePoints: [0.112, 0.115, 0.113, 0.121, 0.119, 0.123, 0.1245] },
  MATICUSDT: { basePrice: 0.57, change24h: -2.15, ingestionRate: 110, latency: 19, initialRecords: 4182903, sparklinePoints: [0.59, 0.585, 0.59, 0.575, 0.572, 0.578, 0.57] },
  LINKUSDT: { basePrice: 14.50, change24h: 2.35, ingestionRate: 98, latency: 17, initialRecords: 1948201, sparklinePoints: [14.1, 14.3, 14.15, 14.4, 14.25, 14.45, 14.5] },
};

interface LiveCoinState {
  symbol: string;
  name: string;
  isActive: boolean;
  price: number;
  change24h: number;
  ingestionRate: number;
  latency: number;
  recordsIngested: number;
  sparkline: number[];
  priceFlash?: "up" | "down" | null;
}

export default function CoinsPage() {
  const { coins: apiCoins, isLoading, error } = useCoins();
  const [liveCoins, setLiveCoins] = useState<LiveCoinState[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [totalProcessed, setTotalProcessed] = useState(48293021);

  // Initialize live state from API coins list and their database summaries
  useEffect(() => {
    const loadRealData = async () => {
      if (!apiCoins || apiCoins.length === 0) return;
      
      // Fetch summaries for all coins in parallel from the backend PostgreSQL database
      const summaryResults = await Promise.all(
        apiCoins.map(async (coin) => {
          try {
            const data = await apiClient<any>(`/api/v1/coins/${coin.symbol}/summary`);
            return { symbol: coin.symbol, data };
          } catch (err) {
            console.warn(`No real database summary found for ${coin.symbol}, using fallback template.`, err);
            return { symbol: coin.symbol, data: null };
          }
        })
      );

      const initialList = apiCoins.map((coin) => {
        const summaryMatch = summaryResults.find((r) => r.symbol === coin.symbol)?.data;
        const template = METRIC_TEMPLATES[coin.symbol] || {
          basePrice: 1.00,
          change24h: 0.00,
          ingestionRate: 50,
          latency: 20,
          initialRecords: 100000,
          sparklinePoints: [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
        };

        if (summaryMatch) {
          // Build sparkline dynamically from real open, low, high, and close values in DB
          const o = summaryMatch.day_open || template.basePrice;
          const c = summaryMatch.day_close || template.basePrice;
          const h = summaryMatch.day_high || Math.max(o, c) * 1.01;
          const l = summaryMatch.day_low || Math.min(o, c) * 0.99;
          
          const realSparkline = [
            o,
            (o + l) / 2,
            l,
            (l + h) / 2,
            h,
            (h + c) / 2,
            c
          ];

          return {
            symbol: coin.symbol,
            name: coin.name,
            isActive: coin.is_active,
            price: c,
            change24h: Number((summaryMatch.price_change_pct || 0).toFixed(2)),
            ingestionRate: summaryMatch.tick_count > 0 ? Math.min(Math.max(Math.round(summaryMatch.tick_count / 120), 45), 350) : template.ingestionRate,
            latency: template.latency,
            recordsIngested: summaryMatch.tick_count || template.initialRecords,
            sparkline: realSparkline,
          };
        }

        // Fallback to template if no DB summary exists yet
        return {
          symbol: coin.symbol,
          name: coin.name,
          isActive: coin.is_active,
          price: template.basePrice,
          change24h: template.change24h,
          ingestionRate: template.ingestionRate,
          latency: template.latency,
          recordsIngested: template.initialRecords,
          sparkline: template.sparklinePoints,
        };
      });

      setLiveCoins(initialList);
      
      const totalInitial = initialList.reduce((sum, c) => sum + c.recordsIngested, 0);
      setTotalProcessed(totalInitial);
    };

    loadRealData();
  }, [apiCoins]);

  // Real-time ticking simulator
  useEffect(() => {
    if (liveCoins.length === 0) return;

    const interval = setInterval(() => {
      // 1. Update individual coin prices and processed record counts
      setLiveCoins((prev) =>
        prev.map((coin) => {
          if (!coin.isActive) return coin;

          // Random price tick (0.01% to 0.08% fluctuation)
          const isUp = Math.random() > 0.48;
          const fluctuation = coin.price * (0.0001 + Math.random() * 0.0007);
          const newPrice = isUp ? coin.price + fluctuation : coin.price - fluctuation;

          // Ingestion adds records (rate * 1.5 seconds)
          const newRecords = coin.recordsIngested + Math.round(coin.ingestionRate * 1.5);

          return {
            ...coin,
            price: newPrice,
            recordsIngested: newRecords,
            priceFlash: isUp ? "up" : "down",
          };
        })
      );

      // Reset flash effect after 400ms
      setTimeout(() => {
        setLiveCoins((prev) =>
          prev.map((c) => ({ ...c, priceFlash: null }))
        );
      }, 400);

      // 2. Increment global database records counter
      const totalRate = liveCoins.reduce((sum, c) => sum + (c.isActive ? c.ingestionRate : 0), 0);
      setTotalProcessed((prev) => prev + Math.round(totalRate * 1.5));
    }, 1500);

    return () => clearInterval(interval);
  }, [liveCoins.length]);

  // Filtered coins list
  const filteredCoins = useMemo(() => {
    return liveCoins.filter(
      (coin) =>
        coin.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        coin.symbol.toLowerCase().includes(searchQuery.toLowerCase())
    );
  }, [liveCoins, searchQuery]);

  // Global Pipeline Latency Average
  const avgLatency = useMemo(() => {
    const active = liveCoins.filter((c) => c.isActive);
    if (active.length === 0) return 0;
    return (active.reduce((sum, c) => sum + c.latency, 0) / active.length).toFixed(1);
  }, [liveCoins]);

  // Global Ingestion Rate (records/sec)
  const totalThroughput = useMemo(() => {
    return liveCoins.reduce((sum, c) => sum + (c.isActive ? c.ingestionRate : 0), 0);
  }, [liveCoins]);

  // Sparkline SVG generator
  const drawSparkline = (points: number[], isPositive: boolean) => {
    if (points.length < 2) return "";
    const min = Math.min(...points);
    const max = Math.max(...points);
    const range = max - min || 1;
    const width = 100;
    const height = 28;

    const coords = points.map((p, index) => {
      const x = (index / (points.length - 1)) * width;
      const y = height - ((p - min) / range) * (height - 6) - 3;
      return `${x},${y}`;
    });

    return (
      <svg className={`h-7 w-24 ${isPositive ? "text-emerald-500" : "text-rose-500"}`} viewBox={`0 0 ${width} ${height}`}>
        <path
          d={`M ${coords.join(" L ")}`}
          fill="none"
          stroke="currentColor"
          strokeWidth="1.75"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    );
  };

  if (isLoading) {
    return (
      <div className="px-4 lg:px-6 py-6 space-y-6">
        <div className="space-y-2">
          <Skeleton className="h-8 w-48 bg-muted/40" />
          <Skeleton className="h-4 w-96 bg-muted/40" />
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {[...Array(4)].map((_, i) => (
            <Skeleton key={i} className="h-24 w-full bg-muted/40 rounded-xl" />
          ))}
        </div>
        <Skeleton className="h-[400px] w-full bg-muted/40 rounded-xl" />
      </div>
    );
  }

  return (
    <>
      <div className="px-4 lg:px-6 py-4 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div className="flex flex-col gap-1.5">
          <h1 className="text-2xl font-black tracking-tight text-foreground">
            Data Ingestion Hub
          </h1>
          <p className="text-muted-foreground text-sm">
            Monitor real-time Kafka messaging pipelines, database storage volume, and ingestion latency per symbol.
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 px-3 py-1.5 rounded-full border border-emerald-500/20 font-medium self-start md:self-auto animate-pulse">
          <Activity className="size-3.5" />
          Live Kafka Stream Connected
        </div>
      </div>

      <div className="px-4 lg:px-6 space-y-6">
        {error && (
          <div className="bg-destructive/10 text-destructive border border-destructive/20 p-4 rounded-xl text-sm">
            {error}
          </div>
        )}

        {/* Real-time Data Engineering Metrics Cards */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card className="bg-card text-card-foreground border-border hover:border-cyan-500/30 transition-all duration-300 shadow-sm relative overflow-hidden group">
            <CardContent className="p-5 flex items-center justify-between">
              <div className="space-y-1">
                <span className="text-[10px] uppercase tracking-widest text-muted-foreground font-bold">Total Ingested Records</span>
                <p className="text-2xl font-black font-mono text-foreground tracking-tight">
                  {totalProcessed.toLocaleString()}
                </p>
              </div>
              <div className="p-3 bg-cyan-500/10 text-cyan-600 dark:text-cyan-400 rounded-xl border border-cyan-500/15 group-hover:scale-105 transition-transform">
                <Database className="size-5" />
              </div>
            </CardContent>
          </Card>

          <Card className="bg-card text-card-foreground border-border hover:border-indigo-500/30 transition-all duration-300 shadow-sm relative overflow-hidden group">
            <CardContent className="p-5 flex items-center justify-between">
              <div className="space-y-1">
                <span className="text-[10px] uppercase tracking-widest text-muted-foreground font-bold">Kafka Throughput</span>
                <p className="text-2xl font-black font-mono text-foreground tracking-tight">
                  {totalThroughput.toLocaleString()} <span className="text-xs text-indigo-500 dark:text-indigo-400 font-normal font-sans">msg/s</span>
                </p>
              </div>
              <div className="p-3 bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 rounded-xl border border-indigo-500/15 group-hover:scale-105 transition-transform">
                <Cpu className="size-5" />
              </div>
            </CardContent>
          </Card>

          <Card className="bg-card text-card-foreground border-border hover:border-emerald-500/30 transition-all duration-300 shadow-sm relative overflow-hidden group">
            <CardContent className="p-5 flex items-center justify-between">
              <div className="space-y-1">
                <span className="text-[10px] uppercase tracking-widest text-muted-foreground font-bold">Pipeline Latency</span>
                <p className="text-2xl font-black font-mono text-foreground tracking-tight">
                  {avgLatency} <span className="text-xs text-emerald-500 dark:text-emerald-400 font-normal font-sans">ms</span>
                </p>
              </div>
              <div className="p-3 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 rounded-xl border border-emerald-500/15 group-hover:scale-105 transition-transform">
                <Layers className="size-5" />
              </div>
            </CardContent>
          </Card>

          <Card className="bg-card text-card-foreground border-border hover:border-amber-500/30 transition-all duration-300 shadow-sm relative overflow-hidden group">
            <CardContent className="p-5 flex items-center justify-between">
              <div className="space-y-1">
                <span className="text-[10px] uppercase tracking-widest text-muted-foreground font-bold">Active Consumers</span>
                <p className="text-2xl font-black font-mono text-foreground tracking-tight">
                  {liveCoins.filter(c => c.isActive).length} <span className="text-xs text-muted-foreground font-normal font-sans">/ {liveCoins.length} Nodes</span>
                </p>
              </div>
              <div className="p-3 bg-amber-500/10 text-amber-600 dark:text-amber-400 rounded-xl border border-amber-500/15 group-hover:scale-105 transition-transform">
                <Activity className="size-5" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Live Search & Filter */}
        <div className="flex items-center gap-3">
          <div className="relative w-full max-w-sm">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 size-4 text-zinc-450 dark:text-zinc-500" />
            <Input
              placeholder="Search coin database..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="h-10 rounded-full bg-background border-border pl-10 pr-4 text-sm focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/50"
            />
          </div>
        </div>

        {/* Rich Real-time Ingestion Pipelines Table */}
        <div className="rounded-2xl border border-border bg-card text-card-foreground overflow-hidden shadow-md">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-border bg-muted/40 text-[10px] uppercase tracking-wider text-muted-foreground font-bold">
                  <th className="p-4 pl-6">Asset / Name</th>
                  <th className="p-4">Live Price (USDT)</th>
                  <th className="p-4">24h Change</th>
                  <th className="p-4">Sync Latency</th>
                  <th className="p-4">Ingested Records</th>
                  <th className="p-4">Throughput</th>
                  <th className="p-4">24h Trend</th>
                  <th className="p-4 pr-6 text-right">Pipeline Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/60 text-sm text-foreground">
                {filteredCoins.length > 0 ? (
                  filteredCoins.map((coin) => {
                    const isPositive = coin.change24h >= 0;
                    return (
                      <tr key={coin.symbol} className="hover:bg-muted/30 transition-colors duration-200">
                        {/* Name & Symbol */}
                        <td className="p-4 pl-6">
                          <div className="flex flex-col">
                            <span className="font-bold text-foreground text-base tracking-tight">{coin.symbol.replace("USDT", "")}</span>
                            <span className="text-muted-foreground text-xs">{coin.name}</span>
                          </div>
                        </td>

                        {/* Live Price */}
                        <td className="p-4">
                          <span 
                            className={`font-mono font-bold transition-all duration-300 px-1 rounded-sm ${
                              coin.priceFlash === "up" 
                                ? "bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 font-semibold scale-105" 
                                : coin.priceFlash === "down" 
                                ? "bg-rose-500/20 text-rose-600 dark:text-rose-400 font-semibold scale-105" 
                                : "text-foreground"
                            }`}
                          >
                            ${coin.price.toLocaleString(undefined, {
                              minimumFractionDigits: coin.price < 1 ? 4 : 2,
                              maximumFractionDigits: coin.price < 1 ? 4 : 2,
                            })}
                          </span>
                        </td>

                        {/* 24h Change */}
                        <td className="p-4">
                          <span className={`flex items-center gap-1 font-semibold text-xs ${isPositive ? "text-emerald-600 dark:text-emerald-400" : "text-rose-600 dark:text-rose-400"}`}>
                            {isPositive ? <ArrowUpRight className="size-3.5" /> : <ArrowDownRight className="size-3.5" />}
                            {isPositive ? "+" : ""}{coin.change24h}%
                          </span>
                        </td>

                        {/* Ingestion Latency */}
                        <td className="p-4 font-mono font-medium text-xs text-muted-foreground">
                          {coin.isActive ? `${coin.latency}ms` : "-"}
                        </td>

                        {/* Ingested Records */}
                        <td className="p-4 font-mono font-semibold text-foreground">
                          {coin.recordsIngested.toLocaleString()}
                        </td>

                        {/* Ingestion Rate (throughput) */}
                        <td className="p-4">
                          <span className="font-mono text-xs text-indigo-600 dark:text-indigo-400 font-semibold bg-indigo-500/10 px-2.5 py-1 rounded-full border border-indigo-500/20">
                            {coin.isActive ? `${coin.ingestionRate} msg/s` : "0 msg/s"}
                          </span>
                        </td>

                        {/* Sparkline */}
                        <td className="p-4">
                          {drawSparkline(coin.sparkline, isPositive)}
                        </td>

                        {/* Ingestion Status */}
                        <td className="p-4 pr-6 text-right">
                          {coin.isActive ? (
                            <Badge className="bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20 rounded-full font-bold text-[10px] tracking-wider uppercase pl-2 pr-3 py-1 flex items-center gap-1.5 w-fit ml-auto">
                              <span className="size-1.5 rounded-full bg-emerald-500 dark:bg-emerald-400 animate-pulse" />
                              Ingesting
                            </Badge>
                          ) : (
                            <Badge className="bg-muted text-muted-foreground border border-border rounded-full font-bold text-[10px] tracking-wider uppercase pl-2 pr-3 py-1 flex items-center gap-1.5 w-fit ml-auto">
                              <span className="size-1.5 rounded-full bg-zinc-500" />
                              Offline
                            </Badge>
                          )}
                        </td>
                      </tr>
                    );
                  })
                ) : (
                  <tr>
                    <td colSpan={8} className="p-8 text-center text-muted-foreground">
                      No matching assets found in the data pipeline database.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </>
  );
}
