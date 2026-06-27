"use client";

import * as React from "react";
import { useEffect, useState, useMemo } from "react";
import {
  LineChart, Line, BarChart, Bar, RadarChart, Radar,
  PolarGrid, PolarAngleAxis, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Legend,
} from "recharts";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { useMarket } from "@/hooks/use-market";
import { apiClient } from "@/lib/api-client";
import { TrendingUp, TrendingDown, ArrowUpRight, ArrowDownRight, BarChart2, Activity, Layers, Radio, Filter, RefreshCw } from "lucide-react";

// ─── Types ──────────────────────────────────────────────────
interface OHLCVPoint { timestamp: string; open: number; high: number; low: number; close: number; volume: number; }
interface PerformanceDataPoint { date: string; [key: string]: any; }
interface VolumeDataPoint { date: string; [key: string]: any; }
interface RadarDataPoint { metric: string; [key: string]: any; }

// ─── Constants ──────────────────────────────────────────────
const coinColors: Record<string, string> = { BTC: "#f59e0b", ETH: "#8b5cf6", SOL: "#0d9488", BNB: "#eab308", XRP: "#3b82f6" };
const SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT"];

// ─── Custom Tooltips ─────────────────────────────────────────
function PctTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-xl border border-border bg-popover p-3 shadow-2xl text-xs space-y-1.5 min-w-[140px] text-popover-foreground">
      <p className="font-semibold text-foreground border-b border-border pb-1 mb-1">{label}</p>
      {payload.map((p: any) => (
        <div key={p.name} className="flex justify-between items-center gap-3">
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full" style={{ backgroundColor: p.color }} />
            <span className="text-muted-foreground">{p.name}</span>
          </span>
          <span className={`font-mono font-bold ${p.value >= 0 ? "text-green-500" : "text-red-500"}`}>
            {p.value >= 0 ? "+" : ""}{p.value.toFixed(2)}%
          </span>
        </div>
      ))}
    </div>
  );
}

function VolumeTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-xl border border-border bg-popover p-3 shadow-2xl text-xs space-y-1.5 min-w-[140px] text-popover-foreground">
      <p className="font-semibold text-foreground border-b border-border pb-1 mb-1">{label}</p>
      {payload.map((p: any) => (
        <div key={p.name} className="flex justify-between items-center gap-3">
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full" style={{ backgroundColor: p.fill }} />
            <span className="text-muted-foreground">{p.name}</span>
          </span>
          <span className="font-mono font-bold text-foreground">{(p.value / 1000).toFixed(1)}K</span>
        </div>
      ))}
    </div>
  );
}

function RadarTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-xl border border-border bg-popover p-3 shadow-xl text-xs min-w-[130px] text-popover-foreground">
      <p className="font-semibold border-b border-border pb-1 mb-1">{label}</p>
      {payload.map((p: any) => (
        <div key={p.name} className="flex justify-between gap-3">
          <span style={{ color: p.color }}>{p.name}</span>
          <span className="font-mono font-bold text-foreground">{Number(p.value).toFixed(0)}</span>
        </div>
      ))}
    </div>
  );
}

// ─── Helper ──────────────────────────────────────────────────
function norm(value: number, min: number, max: number, outMin = 0, outMax = 100) {
  if (max === min) return outMin;
  return ((value - min) / (max - min)) * (outMax - outMin) + outMin;
}

// ─── Loading Skeleton ─────────────────────────────────────────
function LoadingSkeleton() {
  return (
    <div className="flex h-[180px] items-center justify-center">
      <div className="flex flex-col items-center gap-3">
        <div className="h-7 w-7 animate-spin rounded-full border-4 border-primary border-t-transparent" />
        <span className="text-xs text-muted-foreground">Loading chart data...</span>
      </div>
    </div>
  );
}

// ─── Main Component ──────────────────────────────────────────
export function MarketAnalysisSection({
  view = "all",
  days: propDays,
  selectedCoins: propSelectedCoins,
  corrBase: propCorrBase,
  onDaysChange,
  onCoinsChange,
  onCorrBaseChange,
}: {
  view?: "all" | "top" | "bottom";
  days?: number;
  selectedCoins?: string[];
  corrBase?: string;
  onDaysChange?: (days: number) => void;
  onCoinsChange?: (coins: string[]) => void;
  onCorrBaseChange?: (base: string) => void;
}) {
  const { stats, isLoading: loadingMarket } = useMarket();
  const [perfData, setPerfData] = useState<PerformanceDataPoint[]>([]);
  const [volData, setVolData] = useState<VolumeDataPoint[]>([]);
  const [radarData, setRadarData] = useState<RadarDataPoint[]>([]);
  const [allPrices, setAllPrices] = useState<Record<string, OHLCVPoint[]>>({});
  const [loading, setLoading] = useState(true);

  // Synced state handlers
  const [internalDays, setInternalDays] = useState(30);
  const [internalCoins, setInternalCoins] = useState(["BTC", "ETH", "SOL", "BNB", "XRP"]);
  const [internalCorrBase, setInternalCorrBase] = useState("BTC");

  const days = propDays !== undefined ? propDays : internalDays;
  const selectedCoins = propSelectedCoins !== undefined ? propSelectedCoins : internalCoins;
  const corrBase = propCorrBase !== undefined ? propCorrBase : internalCorrBase;

  const setDays = onDaysChange || setInternalDays;
  const setCoins = onCoinsChange || setInternalCoins;
  const setCorrBase = onCorrBaseChange || setInternalCorrBase;

  useEffect(() => {
    const fetchAll = async () => {
      setLoading(true);
      try {
        const responses = await Promise.all(
          SYMBOLS.map((sym) =>
            apiClient<{ prices: OHLCVPoint[] }>(`/api/v1/coins/${sym}/prices?days=${days}`).catch(() => ({ prices: [] }))
          )
        );
        const bySymbol: Record<string, OHLCVPoint[]> = {};
        SYMBOLS.forEach((sym, idx) => { bySymbol[sym.replace("USDT", "")] = responses[idx].prices || []; });
        setAllPrices(bySymbol);

        // ── Performance ──
        const firstPrices: Record<string, number> = {};
        const datesMap: Record<string, Record<string, number>> = {};
        Object.keys(bySymbol).forEach((coin) => {
          const prices = bySymbol[coin];
          if (prices.length > 0) {
            firstPrices[coin] = prices[0].close;
            prices.forEach((p) => {
              const dk = p.timestamp.slice(0, 10);
              if (!datesMap[dk]) datesMap[dk] = {};
              const base = firstPrices[coin];
              datesMap[dk][coin] = base > 0 ? +((p.close - base) / base * 100).toFixed(2) : 0;
            });
          }
        });
        setPerfData(Object.keys(datesMap).sort().map((date) => {
          const point: PerformanceDataPoint = {
            date: new Date(date).toLocaleDateString("en-US", { month: "short", day: "numeric" }),
          };
          Object.keys(bySymbol).forEach((coin) => {
            point[coin] = datesMap[date]?.[coin] ?? 0;
          });
          return point;
        }));

        // ── Volume (Map all 5 coins) ──
        const allDates = [...new Set(Object.keys(bySymbol).flatMap((c) => (bySymbol[c] || []).map((p) => p.timestamp.slice(0, 10))))].sort().slice(-14);
        setVolData(allDates.map((date) => {
          const point: VolumeDataPoint = {
            date: new Date(date).toLocaleDateString("en-US", { month: "short", day: "numeric" }),
          };
          Object.keys(bySymbol).forEach((coin) => {
            point[coin] = +(bySymbol[coin]?.find((p) => p.timestamp.slice(0, 10) === date)?.volume ?? 0).toFixed(0);
          });
          return point;
        }));

        // ── Radar (Compute all 5 coins) ──
        const metrics = (coin: string) => {
          const prices = bySymbol[coin] || [];
          if (!prices.length) return { volatility: 0, momentum: 0, trend: 0, stability: 0 };
          const closes = prices.map((p) => p.close);
          const volatility = prices.reduce((s, p) => s + (p.low > 0 ? ((p.high - p.low) / p.low) * 100 : 0), 0) / prices.length;
          const momentum = ((closes[closes.length - 1] - closes[0]) / (closes[0] || 1)) * 100;
          const trend = (prices.filter((p) => p.close >= p.open).length / prices.length) * 100;
          const mean = closes.reduce((s, v) => s + v, 0) / closes.length;
          const stddev = Math.sqrt(closes.reduce((s, v) => s + Math.pow(v - mean, 2), 0) / closes.length);
          const stability = Math.max(0, 100 - (mean > 0 ? (stddev / mean) * 100 : 0) * 3);
          return { volatility, momentum, trend, stability };
        };
        const coinsList = ["BTC", "ETH", "SOL", "BNB", "XRP"];
        const metricsMap = coinsList.reduce((acc, c) => ({ ...acc, [c]: metrics(c) }), {} as Record<string, ReturnType<typeof metrics>>);
        const momVals = coinsList.map(c => metricsMap[c].momentum);
        const volVals = coinsList.map(c => metricsMap[c].volatility);
        const normMom = (v: number) => +(norm(v, Math.min(...momVals), Math.max(...momVals), 10, 100)).toFixed(1);
        const normVol = (v: number) => +(norm(v, Math.min(...volVals), Math.max(...volVals), 20, 100)).toFixed(1);

        setRadarData([
          { metric: "Momentum", BTC: normMom(metricsMap["BTC"].momentum), ETH: normMom(metricsMap["ETH"].momentum), SOL: normMom(metricsMap["SOL"].momentum), BNB: normMom(metricsMap["BNB"].momentum), XRP: normMom(metricsMap["XRP"].momentum) },
          { metric: "Trend", BTC: +metricsMap["BTC"].trend.toFixed(1), ETH: +metricsMap["ETH"].trend.toFixed(1), SOL: +metricsMap["SOL"].trend.toFixed(1), BNB: +metricsMap["BNB"].trend.toFixed(1), XRP: +metricsMap["XRP"].trend.toFixed(1) },
          { metric: "Volatility", BTC: normVol(metricsMap["BTC"].volatility), ETH: normVol(metricsMap["ETH"].volatility), SOL: normVol(metricsMap["SOL"].volatility), BNB: normVol(metricsMap["BNB"].volatility), XRP: normVol(metricsMap["XRP"].volatility) },
          { metric: "Stability", BTC: +metricsMap["BTC"].stability.toFixed(1), ETH: +metricsMap["ETH"].stability.toFixed(1), SOL: +metricsMap["SOL"].stability.toFixed(1), BNB: +metricsMap["BNB"].stability.toFixed(1), XRP: +metricsMap["XRP"].stability.toFixed(1) },
          { metric: "Bull Days", BTC: +metricsMap["BTC"].trend.toFixed(1), ETH: +metricsMap["ETH"].trend.toFixed(1), SOL: +metricsMap["SOL"].trend.toFixed(1), BNB: +metricsMap["BNB"].trend.toFixed(1), XRP: +metricsMap["XRP"].trend.toFixed(1) },
        ]);
      } catch (err) {
        console.error("MarketAnalysisSection fetch error:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchAll();
  }, [days]);

  // ── Correlation (Dynamic base corrBase) ────────────────────────
  const correlationData = useMemo(() => {
    if (!allPrices[corrBase] || allPrices[corrBase].length < 5) return [];
    const baseCloses = allPrices[corrBase].map((p) => p.close);
    const coinsList = ["BTC", "ETH", "SOL", "BNB", "XRP"].filter(c => c !== corrBase);

    return coinsList.map((coin) => {
      const data = allPrices[coin] || [];
      if (data.length < 5) return { coin, correlation: 0 };
      const closes = data.slice(0, baseCloses.length).map((p) => p.close);
      const n = Math.min(baseCloses.length, closes.length);
      const meanBase = baseCloses.slice(0, n).reduce((s, v) => s + v, 0) / n;
      const meanCoin = closes.slice(0, n).reduce((s, v) => s + v, 0) / n;
      let num = 0, denBase = 0, denCoin = 0;
      for (let i = 0; i < n; i++) {
        const db = baseCloses[i] - meanBase, dc = closes[i] - meanCoin;
        num += db * dc; denBase += db * db; denCoin += dc * dc;
      }
      return { coin, correlation: +(denBase && denCoin ? num / Math.sqrt(denBase * denCoin) : 0).toFixed(3) };
    });
  }, [allPrices, corrBase]);

  const toggleCoin = (coin: string) => {
    if (selectedCoins.includes(coin)) {
      if (selectedCoins.length > 1) {
        setCoins(selectedCoins.filter((c) => c !== coin));
      }
    } else {
      setCoins([...selectedCoins, coin]);
    }
  };

  // ─── Render ──────────────────────────────────────────────────
  return (
    <div className="space-y-4" data-view={view}>
      {(view === "all" || view === "top") && (
        <div className="space-y-4">
          
          {/* ─── FILTERS CONTROLS PANEL ─── */}
          <Card className="border border-border bg-card/60 backdrop-blur-md p-4 flex flex-col md:flex-row md:items-center md:justify-between gap-4 shadow-sm">
            
            {/* 1. Time Range Selector */}
            <div className="flex flex-col gap-1.5">
              <span className="text-[10px] uppercase font-bold text-muted-foreground tracking-wider flex items-center gap-1">
                <Filter className="size-3" /> Time Period
              </span>
              <ToggleGroup type="single" value={days.toString()} onValueChange={(val) => val && setDays(parseInt(val))} className="bg-muted p-0.5 rounded-lg border border-border">
                {[
                  { label: "7D", value: "7" },
                  { label: "14D", value: "14" },
                  { label: "30D", value: "30" },
                  { label: "90D", value: "90" },
                ].map((opt) => (
                  <ToggleGroupItem
                    key={opt.value}
                    value={opt.value}
                    className="px-3 py-1.5 text-xs text-muted-foreground data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-sm rounded-md font-semibold"
                  >
                    {opt.label}
                  </ToggleGroupItem>
                ))}
              </ToggleGroup>
            </div>

            {/* 2. Assets Selector */}
            <div className="flex flex-col gap-1.5 flex-1 max-w-lg">
              <span className="text-[10px] uppercase font-bold text-muted-foreground tracking-wider">
                Compare Assets (Click to toggle)
              </span>
              <div className="flex flex-wrap gap-1.5">
                {Object.entries(coinColors).map(([coin, color]) => {
                  const isActive = selectedCoins.includes(coin);
                  return (
                    <Badge
                      key={coin}
                      variant="outline"
                      onClick={() => toggleCoin(coin)}
                      style={{
                        borderColor: isActive ? color : "transparent",
                        backgroundColor: isActive ? `${color}15` : "transparent",
                        color: isActive ? color : "var(--muted-foreground)",
                      }}
                      className="cursor-pointer font-bold text-xs px-2.5 py-1 transition-all hover:scale-105 active:scale-95 select-none"
                    >
                      <span className="w-1.5 h-1.5 rounded-full me-1.5" style={{ backgroundColor: color }} />
                      {coin}
                    </Badge>
                  );
                })}
              </div>
            </div>

            {/* 3. Base Correlation Coin Selector */}
            <div className="flex flex-col gap-1.5">
              <span className="text-[10px] uppercase font-bold text-muted-foreground tracking-wider">
                Correlation Index Base
              </span>
              <Select value={corrBase} onValueChange={setCorrBase}>
                <SelectTrigger className="w-[120px] bg-background border-input font-bold text-xs h-9">
                  <SelectValue placeholder="Base Asset" />
                </SelectTrigger>
                <SelectContent className="bg-popover text-popover-foreground border-border">
                  {["BTC", "ETH", "SOL", "BNB", "XRP"].map((coin) => (
                    <SelectItem key={coin} value={coin} className="text-xs font-semibold">
                      {coin} Index
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

          </Card>

          {/* ─── ROW 1: Performance + Winners ─── */}
          <div className="grid gap-4 lg:grid-cols-3">

            {/* Performance Chart */}
            <Card className="lg:col-span-2 border border-border bg-card h-full flex flex-col">
              <CardHeader className="pb-2">
                <CardTitle className="text-base flex items-center gap-2">
                  <BarChart2 className="size-4 text-violet-500" />
                  {days}D Performance Comparison (%)
                </CardTitle>
                <CardDescription>Relative % return of selected assets from day 0 of the period.</CardDescription>
              </CardHeader>
              <CardContent className="p-4 pt-0 flex-1 flex flex-col justify-between">
                {loading ? <LoadingSkeleton /> : (
                  <ResponsiveContainer width="100%" height={210}>
                    <LineChart data={perfData}>
                      <CartesianGrid vertical={false} stroke="rgba(120,120,120,0.08)" />
                      <XAxis dataKey="date" tickLine={false} axisLine={false} tick={{ fill: "#888", fontSize: 9 }} minTickGap={30} />
                      <YAxis tickLine={false} axisLine={false} tick={{ fill: "#888", fontSize: 9 }} tickFormatter={(v) => `${v}%`} width={36} />
                      <Tooltip content={<PctTooltip />} />
                      <Legend iconType="circle" wrapperStyle={{ fontSize: 10, paddingTop: 6 }} />
                      {Object.entries(coinColors).map(([coin, color]) => (
                        selectedCoins.includes(coin) && (
                          <Line key={coin} type="monotone" dataKey={coin} stroke={color} strokeWidth={2} dot={false} activeDot={{ r: 3 }} />
                        )
                      ))}
                    </LineChart>
                  </ResponsiveContainer>
                )}
                {!loading && perfData.length > 0 && (() => {
                  const last = perfData[perfData.length - 1];
                  const coins30d = Object.entries(last).filter(([k]) => k !== "date" && selectedCoins.includes(k)) as [string, number][];
                  return (
                    <div className="mt-3 pt-3 border-t border-border">
                      <p className="text-[10px] font-semibold uppercase text-muted-foreground tracking-wider mb-2">{days}D Total Return</p>
                      <div className="grid grid-cols-5 gap-1">
                        {coins30d.map(([coin, pct]) => (
                          <div key={coin} className="flex flex-col items-center p-1.5 rounded-lg bg-muted/30 border border-border/40">
                            <span className="text-[9px] font-bold" style={{ color: coinColors[coin] }}>{coin}</span>
                            <span className={`text-[10px] font-mono font-black mt-0.5 ${pct >= 0 ? "text-green-500" : "text-red-500"}`}>
                              {pct >= 0 ? "+" : ""}{pct.toFixed(1)}%
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  );
                })()}
              </CardContent>
            </Card>

            {/* Winners & Losers */}
            <Card className="border border-border bg-card h-full flex flex-col">
              <CardHeader className="pb-2">
                <CardTitle className="text-base flex items-center gap-2">
                  <Activity className="size-4 text-emerald-500" />
                  Market Winners &amp; Losers
                </CardTitle>
                <CardDescription>Top performing and underperforming assets today.</CardDescription>
              </CardHeader>
              <CardContent className="p-4 pt-0 space-y-4 flex-1 flex flex-col justify-between">
                <div className="space-y-1.5">
                  <h3 className="text-[10px] font-bold uppercase tracking-wider text-green-600 dark:text-green-400 flex items-center gap-1.5">
                    <TrendingUp className="size-3" /> Top Gainers
                  </h3>
                  {loadingMarket ? [1,2,3].map((i) => <Skeleton key={i} className="h-7 w-full" />) : (
                    (stats?.top_gainers || []).slice(0, 4).map((coin: any) => (
                      <div key={coin.symbol} className="flex items-center justify-between px-2 py-1 rounded-lg bg-muted/30 border border-border/50 text-xs">
                        <div>
                          <span className="font-semibold text-foreground">{coin.name}</span>
                          <span className="text-[10px] text-muted-foreground block leading-tight">{coin.symbol.replace("USDT", "")}</span>
                        </div>
                        <Badge variant="outline" className="border-green-500/20 bg-green-500/10 text-green-600 dark:text-green-400 font-mono font-semibold text-[10px] gap-0.5">
                          <ArrowUpRight className="size-2.5" />+{coin.change_pct}%
                        </Badge>
                      </div>
                    ))
                  )}
                </div>
                <div className="space-y-1.5">
                  <h3 className="text-[10px] font-bold uppercase tracking-wider text-red-600 dark:text-red-400 flex items-center gap-1.5">
                    <TrendingDown className="size-3" /> Top Losers
                  </h3>
                  {loadingMarket ? [1,2,3].map((i) => <Skeleton key={i} className="h-7 w-full" />) : (
                    (stats?.top_losers || []).slice(0, 4).map((coin: any) => (
                      <div key={coin.symbol} className="flex items-center justify-between px-2 py-1 rounded-lg bg-muted/30 border border-border/50 text-xs">
                        <div>
                          <span className="font-semibold text-foreground">{coin.name}</span>
                          <span className="text-[10px] text-muted-foreground block leading-tight">{coin.symbol.replace("USDT", "")}</span>
                        </div>
                        <Badge variant="outline" className="border-red-500/20 bg-red-500/10 text-red-600 dark:text-red-400 font-mono font-semibold text-[10px] gap-0.5">
                          <ArrowDownRight className="size-2.5" />{coin.change_pct}%
                        </Badge>
                      </div>
                    ))
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {(view === "all" || view === "bottom") && (
        <div className="grid gap-4 grid-cols-1 md:grid-cols-3">

          {/* 14D Volume */}
          <Card className="border border-border bg-card h-full flex flex-col">
            <CardHeader className="p-3 pb-1">
              <CardTitle className="text-sm flex items-center gap-1.5">
                <Layers className="size-3.5 text-blue-500" />
                {days}D Volume comparison
              </CardTitle>
            </CardHeader>
            <CardContent className="p-3 pt-0 space-y-2 flex-1 flex flex-col justify-between">
              {loading ? <div className="h-[140px] flex items-center justify-center"><div className="h-5 w-5 animate-spin rounded-full border-2 border-primary border-t-transparent" /></div> : (
                <ResponsiveContainer width="100%" height={140}>
                  <BarChart data={volData} barSize={8}>
                    <CartesianGrid vertical={false} stroke="rgba(120,120,120,0.08)" />
                    <XAxis dataKey="date" tickLine={false} axisLine={false} tick={{ fill: "#888", fontSize: 8 }} minTickGap={25} />
                    <YAxis tickLine={false} axisLine={false} tick={{ fill: "#888", fontSize: 8 }} tickFormatter={(v) => `${(v / 1000).toFixed(0)}K`} width={30} />
                    <Tooltip content={<VolumeTooltip />} />
                    {selectedCoins.slice(0, 4).map((coin, idx) => (
                      <Bar
                        key={coin}
                        dataKey={coin}
                        stackId="a"
                        fill={coinColors[coin]}
                        radius={idx === Math.min(selectedCoins.length, 4) - 1 ? [3,3,0,0] : [0,0,0,0]}
                      />
                    ))}
                  </BarChart>
                </ResponsiveContainer>
              )}
              {!loading && (
                <div className="pt-1.5 border-t border-border space-y-1">
                  {selectedCoins.slice(0, 3).map((coin) => {
                    const pts = allPrices[coin] || [];
                    const avg = pts.length > 0 ? pts.reduce((s, p) => s + p.volume, 0) / pts.length : 0;
                    const max = pts.length > 0 ? Math.max(...pts.map((p) => p.volume)) : 1;
                    const pct = max > 0 ? (avg / max) * 100 : 0;
                    return (
                      <div key={coin} className="space-y-0.5">
                        <div className="flex justify-between text-[9px]">
                          <span className="font-semibold" style={{ color: coinColors[coin] }}>{coin}</span>
                          <span className="font-mono text-muted-foreground">{avg >= 1000 ? `${(avg / 1000).toFixed(1)}K` : avg.toFixed(0)}</span>
                        </div>
                        <div className="h-1.5 w-full bg-secondary rounded-full overflow-hidden">
                          <div className="h-full rounded-full" style={{ width: `${pct}%`, backgroundColor: coinColors[coin] }} />
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Asset Strength Radar */}
          <Card className="border border-border bg-card h-full flex flex-col">
            <CardHeader className="p-3 pb-1">
              <CardTitle className="text-sm flex items-center gap-1.5">
                <Radio className="size-3.5 text-rose-500" />
                Asset Strength Radar
              </CardTitle>
            </CardHeader>
            <CardContent className="p-3 pt-0 space-y-2 flex-1 flex flex-col justify-between">
              {loading ? <div className="h-[140px] flex items-center justify-center"><div className="h-5 w-5 animate-spin rounded-full border-2 border-primary border-t-transparent" /></div> : (
                <ResponsiveContainer width="100%" height={140}>
                  <RadarChart cx="50%" cy="50%" outerRadius="65%" data={radarData}>
                    <PolarGrid stroke="rgba(120,120,120,0.15)" />
                    <PolarAngleAxis dataKey="metric" tick={{ fill: "#888", fontSize: 8 }} />
                    <Tooltip content={<RadarTooltip />} />
                    {selectedCoins.slice(0, 3).map((coin) => (
                      <Radar
                        key={coin}
                        name={coin}
                        dataKey={coin}
                        stroke={coinColors[coin]}
                        fill={coinColors[coin]}
                        fillOpacity={0.15}
                        strokeWidth={1.5}
                      />
                    ))}
                    <Legend iconType="circle" wrapperStyle={{ fontSize: 9 }} />
                  </RadarChart>
                </ResponsiveContainer>
              )}
              {!loading && radarData.length > 0 && (
                <div className="pt-1.5 border-t border-border">
                  <div className="grid grid-cols-4 gap-x-1 gap-y-0.5 text-[8px]">
                    <span className="text-muted-foreground font-semibold">Metric</span>
                    {selectedCoins.slice(0, 3).map((c) => (
                      <span key={c} className="font-bold text-center" style={{ color: coinColors[c] }}>{c}</span>
                    ))}
                    {radarData.slice(0, 4).map((row) => (
                      <React.Fragment key={row.metric}>
                        <span className="text-muted-foreground truncate">{row.metric}</span>
                        {selectedCoins.slice(0, 3).map((c) => (
                          <span key={c} className="font-mono text-center text-foreground">{row[c] ?? "-"}</span>
                        ))}
                      </React.Fragment>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* BTC Correlation */}
          <Card className="border border-border bg-card h-full flex flex-col">
            <CardHeader className="p-3 pb-1">
              <CardTitle className="text-sm flex items-center gap-1.5">
                <Activity className="size-3.5 text-cyan-500" />
                {corrBase} Correlation ({days}D)
              </CardTitle>
            </CardHeader>
            <CardContent className="p-3 pt-0 space-y-2 flex-1 flex flex-col justify-between">
              {loading ? [1,2,3,4].map((i) => <Skeleton key={i} className="h-6 w-full" />) : (
                <>
                  {correlationData.filter(({ coin }) => selectedCoins.includes(coin)).map(({ coin, correlation }) => {
                    const pct = Math.abs(correlation) * 100;
                    const barColor = correlation > 0.7 ? "#22c55e" : correlation > 0.4 ? "#eab308" : "#ef4444";
                    return (
                      <div key={coin} className="space-y-0.5">
                        <div className="flex items-center justify-between text-[10px]">
                          <span className="font-semibold text-foreground flex items-center gap-1">
                            <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: coinColors[coin] || "#888" }} />
                            {coin}/{corrBase}
                          </span>
                          <span className={`font-mono font-bold ${correlation > 0.6 ? "text-green-500" : correlation < 0.2 ? "text-red-500" : "text-amber-500"}`}>
                            {correlation > 0 ? "+" : ""}{correlation.toFixed(3)}
                          </span>
                        </div>
                        <div className="h-1.5 w-full bg-secondary rounded-full overflow-hidden">
                          <div className="h-full rounded-full transition-all duration-700" style={{ width: `${pct}%`, backgroundColor: barColor }} />
                        </div>
                      </div>
                    );
                  })}
                  {correlationData.length > 0 && (
                    <div className="pt-2 border-t border-border">
                      <p className="text-[9px] text-muted-foreground">
                        Avg: <span className="font-mono font-bold text-foreground">
                          {(correlationData.reduce((s, d) => s + d.correlation, 0) / correlationData.length).toFixed(3)}
                        </span>
                        {" "}— {correlationData.reduce((s, d) => s + d.correlation, 0) / correlationData.length > 0.7 ? "Highly coupled" : "Partially decoupled"}
                      </p>
                    </div>
                  )}
                </>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}