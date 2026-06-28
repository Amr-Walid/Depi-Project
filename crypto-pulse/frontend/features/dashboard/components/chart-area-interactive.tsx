"use client";

import * as React from "react";
import { useState, useMemo } from "react";
import {
  ComposedChart,
  Area,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { useMarket } from "@/hooks/use-market";
import { MarketAnalysisSection } from "./market-analysis-section";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import {
  TrendingUp,
  TrendingDown,
  Activity,
  DollarSign,
  Brain,
  Info,
  Layers,
  BarChart2,
  AlertCircle,
  Zap,
  Compass,
} from "lucide-react";

interface PricePoint {
  timestamp: string;
  open?: number;
  high?: number;
  low?: number;
  close?: number;
  volume?: number;
  price?: number;
}

interface CoinInfo {
  symbol: string;
  name: string;
  is_active: boolean;
}

interface ChartProps {
  data?: PricePoint[];
  coins?: CoinInfo[];
  symbol: string;
  days?: number;
  price?: number;
  change?: number;
  high?: number;
  low?: number;
  volume?: number;
  avgPrice?: number;
  isLoading?: boolean;
  onSymbolChange?: (symbol: string) => void;
  onDaysChange?: (days: number) => void;
  showAnalysis?: boolean;
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    const isUp = data.close >= data.open;
    
    const dateObj = new Date(data.timestamp);
    const formattedDate = dateObj.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });

    return (
      <div className="rounded-xl border border-border bg-popover p-4 shadow-2xl backdrop-blur-md text-xs space-y-2 min-w-[200px] text-popover-foreground">
        <div className="flex items-center justify-between border-b border-border pb-1.5">
          <span className="font-semibold text-foreground">{formattedDate}</span>
          <Badge
            variant="outline"
            className={
              isUp
                ? "border-green-500/30 bg-green-500/10 text-green-600 dark:text-green-400"
                : "border-red-500/30 bg-red-500/10 text-red-600 dark:text-red-400"
            }
          >
            {isUp ? "Bullish" : "Bearish"}
          </Badge>
        </div>
        <div className="grid grid-cols-2 gap-x-4 gap-y-1 pt-1">
          <span className="text-muted-foreground">Open:</span>
          <span className="font-mono text-right text-foreground">${data.open?.toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>
          <span className="text-muted-foreground">High:</span>
          <span className="font-mono text-right text-green-600 dark:text-green-400">${data.high?.toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>
          <span className="text-muted-foreground">Low:</span>
          <span className="font-mono text-right text-red-600 dark:text-red-400">${data.low?.toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>
          <span className="text-muted-foreground font-semibold">Close:</span>
          <span className="font-mono text-right font-bold text-foreground">${data.close?.toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>
          <span className="text-muted-foreground">Volume:</span>
          <span className="font-mono text-right text-muted-foreground">${data.volume?.toLocaleString(undefined, { maximumFractionDigits: 0 })}</span>
          {data.sma7 !== undefined && (
            <>
              <span className="text-amber-600 dark:text-amber-500 font-medium">7-SMA:</span>
              <span className="font-mono text-right text-amber-600 dark:text-amber-400">${data.sma7?.toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>
            </>
          )}
          {data.sma20 !== undefined && (
            <>
              <span className="text-violet-600 dark:text-violet-500 font-medium">20-SMA:</span>
              <span className="font-mono text-right text-violet-600 dark:text-violet-400">${data.sma20?.toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>
            </>
          )}
        </div>
      </div>
    );
  }
  return null;
};

const Candlestick = (props: any) => {
  const { x, width, payload, yAxis } = props;
  if (!payload || !yAxis || !yAxis.scale) return null;

  const yScale = yAxis.scale;
  const open = payload.open ?? payload.close ?? 0;
  const close = payload.close ?? 0;
  const high = payload.high ?? close;
  const low = payload.low ?? close;

  const yOpen = yScale(open);
  const yClose = yScale(close);
  const yHigh = yScale(high);
  const yLow = yScale(low);

  const isUp = close >= open;
  const color = isUp ? "#22c55e" : "#ef4444";

  const w = typeof width === "number" ? width : 8;
  const startX = typeof x === "number" ? x : 0;
  const cx = startX + w / 2;

  return (
    <g>
      <line
        x1={cx}
        y1={yHigh}
        x2={cx}
        y2={yLow}
        stroke={color}
        strokeWidth={1.5}
      />
      <rect
        x={startX}
        y={Math.min(yOpen, yClose)}
        width={w}
        height={Math.max(Math.abs(yOpen - yClose), 1)}
        fill={color}
      />
    </g>
  );
};

export function ChartAreaInteractive({
  data = [],
  coins = [],
  symbol,
  days = 30,
  price = 0,
  change = 0,
  high = 0,
  low = 0,
  volume = 0,
  avgPrice = 0,
  isLoading = false,
  onSymbolChange = () => {},
  onDaysChange = () => {},
  showAnalysis = true,
}: ChartProps) {
  const [chartType, setChartType] = useState<"area" | "candlestick">("area");
  const { sentiment, isLoading: loadingSentiment } = useMarket();
  const [compDays, setCompDays] = useState<number>(30);
  const [compCoins, setCompCoins] = useState<string[]>(["BTC", "ETH", "SOL", "BNB", "XRP"]);
  const [corrBase, setCorrBase] = useState<string>("BTC");

  const processedData = useMemo(() => {
    if (!data || data.length === 0) return [];
    
    const prices = data.map((d: any) => ({
      ...d,
      close: d.close || d.price || 0,
    }));

    for (let i = 0; i < prices.length; i++) {
      if (i >= 6) {
        const sum = prices.slice(i - 6, i + 1).reduce((acc, curr) => acc + curr.close, 0);
        prices[i].sma7 = sum / 7;
      }
      if (i >= 19) {
        const sum = prices.slice(i - 19, i + 1).reduce((acc, curr) => acc + curr.close, 0);
        prices[i].sma20 = sum / 20;
      }

      prices[i].wick = [prices[i].low, prices[i].high];
      prices[i].body = [
        Math.min(prices[i].open, prices[i].close),
        Math.max(prices[i].open, prices[i].close)
      ];
    }
    
    return prices;
  }, [data]);

  const yDomain = useMemo(() => {
    if (!processedData || processedData.length === 0) return ["auto", "auto"];
    const lows = processedData.map((d) => d.low).filter((val) => typeof val === "number" && !isNaN(val));
    const highs = processedData.map((d) => d.high).filter((val) => typeof val === "number" && !isNaN(val));
    
    if (lows.length === 0 || highs.length === 0) return ["auto", "auto"];
    
    const min = Math.min(...lows);
    const max = Math.max(...highs);
    const padding = (max - min) * 0.05 || 10;
    return [Math.max(0, min - padding), max + padding];
  }, [processedData]);

  const technicalVerdict = useMemo(() => {
    if (processedData.length < 2) return { text: "No Data", color: "text-muted-foreground border-border bg-muted/20" };
    const latest = processedData[processedData.length - 1];
    
    if (latest.sma7 && latest.sma20) {
      if (latest.close > latest.sma7 && latest.sma7 > latest.sma20) {
        return { text: "Strong Buy (Bullish Crossover)", color: "text-green-600 border-green-500/20 bg-green-500/5 dark:text-green-400" };
      }
      if (latest.close > latest.sma7) {
        return { text: "Buy (Neutral Bullish)", color: "text-green-500 border-green-500/10 bg-green-500/5 dark:text-green-300" };
      }
      if (latest.close < latest.sma7 && latest.sma7 < latest.sma20) {
        return { text: "Strong Sell (Bearish Crossover)", color: "text-red-600 border-red-500/20 bg-red-500/5 dark:text-red-400" };
      }
      return { text: "Sell (Neutral Bearish)", color: "text-red-500 border-red-500/10 bg-red-500/5 dark:text-red-300" };
    }
    return { text: "Hold (Need More History)", color: "text-amber-600 border-amber-500/10 bg-amber-500/5 dark:text-amber-400" };
  }, [processedData]);

  // Calculate RSI, Volatility, and Distance to High/Low
  const technicalIndicators = useMemo(() => {
    if (processedData.length < 2) {
      return {
        rsiValue: 50,
        rsiStatus: "Neutral",
        rsiColor: "border-zinc-500/20 bg-zinc-500/5 text-zinc-500",
        avgVolatility: 0,
        distToHigh: 0,
        distToLow: 0,
      };
    }

    const prices = processedData.map((p) => p.close);
    const latestPrice = prices[prices.length - 1];

    // 1. Calculate RSI (14)
    let rsiValue = 50;
    const period = 14;
    if (prices.length > period) {
      let gains = 0;
      let losses = 0;
      for (let i = 1; i <= period; i++) {
        const diff = prices[i] - prices[i - 1];
        if (diff > 0) gains += diff;
        else losses -= diff;
      }
      let avgGain = gains / period;
      let avgLoss = losses / period;

      for (let i = period + 1; i < prices.length; i++) {
        const diff = prices[i] - prices[i - 1];
        avgGain = (avgGain * 13 + (diff > 0 ? diff : 0)) / 14;
        avgLoss = (avgLoss * 13 + (diff < 0 ? -diff : 0)) / 14;
      }

      if (avgLoss === 0) {
        rsiValue = 100;
      } else {
        const rs = avgGain / avgLoss;
        rsiValue = 100 - 100 / (1 + rs);
      }
    }

    let rsiStatus = "Neutral";
    let rsiColor = "border-zinc-500/20 bg-zinc-500/5 text-zinc-500";
    if (rsiValue >= 70) {
      rsiStatus = "Overbought";
      rsiColor = "border-red-500/20 bg-red-500/5 text-red-600 dark:text-red-400";
    } else if (rsiValue <= 30) {
      rsiStatus = "Oversold";
      rsiColor = "border-green-500/20 bg-green-500/5 text-green-600 dark:text-green-400";
    } else if (rsiValue > 55) {
      rsiStatus = "Bullish";
      rsiColor = "border-green-500/10 bg-green-500/5 text-green-500 dark:text-green-400";
    } else if (rsiValue < 45) {
      rsiStatus = "Bearish";
      rsiColor = "border-red-500/10 bg-red-500/5 text-red-500 dark:text-red-400";
    }

    // 2. Average Daily Volatility: average of ((high - low)/low)*100
    const volatilities = processedData.map(
      (p) => (p.low > 0 ? ((p.high - p.low) / p.low) * 100 : 0)
    );
    const avgVolatility = volatilities.reduce((sum, v) => sum + v, 0) / volatilities.length;

    // 3. Distance to 30D High/Low
    const highs = processedData.map((p) => p.high);
    const lows = processedData.map((p) => p.low);
    const periodHigh = Math.max(...highs);
    const periodLow = Math.min(...lows);

    const distToHigh = periodHigh > 0 ? ((latestPrice - periodHigh) / periodHigh) * 100 : 0;
    const distToLow = periodLow > 0 ? ((latestPrice - periodLow) / periodLow) * 100 : 0;

    return {
      rsiValue,
      rsiStatus,
      rsiColor,
      avgVolatility,
      distToHigh,
      distToLow,
    };
  }, [processedData]);

  const formattedPrice = new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(price);

  return (
    <div className="space-y-6">
      <div className="grid gap-6 lg:grid-cols-4 items-stretch">
        {/* Left Column (3 Columns) containing Main Chart and Market Analysis Comparison */}
        <div className="lg:col-span-3 space-y-6 self-start">
        {/* Main Chart Section */}
        <Card className="border border-border bg-card text-card-foreground">
        <CardHeader className="flex flex-col space-y-4 border-b border-border p-6 sm:flex-row sm:items-center sm:justify-between sm:space-y-0">
          <div className="flex flex-wrap items-center gap-4">
            <Select value={symbol + "USDT"} onValueChange={onSymbolChange}>
              <SelectTrigger className="w-[180px] bg-background border-input text-foreground font-semibold">
                <SelectValue placeholder="Select coin" />
              </SelectTrigger>
              <SelectContent className="bg-popover border-border text-popover-foreground">
                {coins.map((c) => (
                  <SelectItem key={c.symbol} value={c.symbol}>
                    {c.name} ({c.symbol.replace("USDT", "")})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <ToggleGroup
              type="single"
              value={days.toString()}
              onValueChange={(val) => val && onDaysChange(parseInt(val))}
              className="bg-muted p-0.5 rounded-lg border border-border"
            >
              {[
                { label: "7D", value: "7" },
                { label: "30D", value: "30" },
                { label: "90D", value: "90" },
                { label: "365D", value: "365" },
              ].map((opt) => (
                <ToggleGroupItem
                  key={opt.value}
                  value={opt.value}
                  className="px-3 py-1.5 text-xs text-muted-foreground data-[state=active]:bg-primary data-[state=active]:text-primary-foreground data-[state=active]:shadow-sm rounded-md transition-colors font-medium"
                >
                  {opt.label}
                </ToggleGroupItem>
              ))}
            </ToggleGroup>
          </div>

          <ToggleGroup
            type="single"
            value={chartType}
            onValueChange={(val) => val && setChartType(val as any)}
            className="bg-muted p-0.5 rounded-lg border border-border align-self-end sm:align-self-auto"
          >
            <ToggleGroupItem
              value="area"
              className="px-3 py-1.5 text-xs text-muted-foreground data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-sm rounded-md font-medium"
            >
              <Layers className="size-3.5 me-1.5" />
              Area Chart
            </ToggleGroupItem>
            <ToggleGroupItem
              value="candlestick"
              className="px-3 py-1.5 text-xs text-muted-foreground data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-sm rounded-md font-medium"
            >
              <BarChart2 className="size-3.5 me-1.5" />
              Candlestick
            </ToggleGroupItem>
          </ToggleGroup>
        </CardHeader>

        <CardContent className="p-6">
          {isLoading ? (
            <div className="flex h-[380px] items-center justify-center">
              <div className="flex flex-col items-center gap-3">
                <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
                <span className="text-sm text-muted-foreground">Loading historical data...</span>
              </div>
            </div>
          ) : processedData.length === 0 ? (
            <div className="flex h-[380px] flex-col items-center justify-center text-muted-foreground gap-2 border border-dashed border-border rounded-xl bg-muted/10">
              <AlertCircle className="size-8 text-muted-foreground" />
              <span>No price history available. Run pipeline to fetch data.</span>
            </div>
          ) : (
            <div className="space-y-6">
              {/* 1. Price Chart */}
              <div className="h-[280px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart data={processedData} barGap="-100%">
                    <defs>
                      <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="var(--chart-1)" stopOpacity={0.4} />
                        <stop offset="95%" stopColor="var(--chart-1)" stopOpacity={0.0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid vertical={false} stroke="rgba(120,120,120,0.12)" />
                    <XAxis
                      dataKey="timestamp"
                      tickLine={false}
                      axisLine={false}
                      tickMargin={8}
                      minTickGap={40}
                      tick={{ fill: "#888888", fontSize: 11 }}
                      tickFormatter={(value) => {
                        const date = new Date(value);
                        return date.toLocaleDateString("en-US", {
                          month: "short",
                          day: "numeric",
                        });
                      }}
                    />
                    <YAxis
                      domain={yDomain}
                      width={80}
                      tickLine={false}
                      axisLine={false}
                      tickMargin={8}
                      tick={{ fill: "#888888", fontSize: 11 }}
                      tickFormatter={(val) => `$${val.toLocaleString()}`}
                    />
                    <Tooltip content={<CustomTooltip />} cursor={{ stroke: "rgba(120,120,120,0.15)" }} />
                    
                    {chartType === "area" ? (
                      <Area
                        type="monotone"
                        dataKey="close"
                        stroke="var(--chart-1)"
                        strokeWidth={2}
                        fillOpacity={1}
                        fill="url(#colorPrice)"
                      />
                    ) : (
                      <Bar 
                        dataKey="close" 
                        shape={<Candlestick />} 
                        barSize={8} 
                        tooltipType="none" 
                      />
                    )}

                    <Line
                      type="monotone"
                      dataKey="sma7"
                      stroke="#f59e0b"
                      strokeWidth={1.5}
                      dot={false}
                      activeDot={false}
                    />
                    <Line
                      type="monotone"
                      dataKey="sma20"
                      stroke="#8b5cf6"
                      strokeWidth={1.5}
                      dot={false}
                      activeDot={false}
                    />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>

              {/* 2. Trading Volume Chart */}
              <div className="h-[90px] w-full border-t border-border pt-4">
                <div className="flex items-center gap-1.5 mb-2">
                  <span className="text-[11px] text-muted-foreground uppercase font-semibold">Volume (Daily)</span>
                </div>
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart data={processedData}>
                    <CartesianGrid vertical={false} stroke="rgba(120,120,120,0.08)" />
                    <XAxis dataKey="timestamp" hide />
                    <YAxis
                      tickLine={false}
                      axisLine={false}
                      tick={{ fill: "#888888", fontSize: 9 }}
                      tickFormatter={(val) => `$${(val / 1000000).toFixed(0)}M`}
                    />
                    <Tooltip content={<CustomTooltip />} />
                    <Bar dataKey="volume" barSize={8}>
                      {processedData.map((entry, index) => (
                        <Cell
                          key={`vol-cell-${index}`}
                          fill={entry.close >= entry.open ? "#22c55e25" : "#ef444425"}
                        />
                      ))}
                    </Bar>
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
      {/* Market Analysis Comparative Section */}
      {showAnalysis && (
        <MarketAnalysisSection 
          view="top" 
          days={compDays}
          selectedCoins={compCoins}
          corrBase={corrBase}
          onDaysChange={(val) => setCompDays(val)}
          onCoinsChange={(val) => setCompCoins(val)}
          onCorrBaseChange={(val) => setCorrBase(val)}
        />
      )}
    </div>

      {/* Advanced Financial & Market Sentiment Panel (1 Column) */}
      <div className="lg:col-span-1 flex flex-col h-full space-y-6">
        {/* Coin Statistics Card */}
        <Card className="border border-border bg-card text-card-foreground">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-semibold uppercase text-muted-foreground">Financial Analysis</CardTitle>
            <CardDescription className="text-2xl font-bold text-foreground mt-1">
              {isLoading ? <Skeleton className="h-8 w-32" /> : formattedPrice}
              <span className={`text-xs block font-medium mt-1 ${change >= 0 ? "text-green-600 dark:text-green-400" : "text-red-600 dark:text-red-400"}`}>
                {change >= 0 ? "+" : ""}{change.toFixed(2)}% in 24h
              </span>
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 pt-2 text-xs">
            <div className="space-y-2">
              <div className="flex justify-between py-1 border-b border-border">
                <span className="text-muted-foreground">24h High</span>
                <span className="font-mono text-foreground font-semibold">
                  {isLoading ? <Skeleton className="h-4 w-16" /> : `$${high.toLocaleString(undefined, { minimumFractionDigits: 2 })}`}
                </span>
              </div>
              <div className="flex justify-between py-1 border-b border-border">
                <span className="text-muted-foreground">24h Low</span>
                <span className="font-mono text-foreground font-semibold">
                  {isLoading ? <Skeleton className="h-4 w-16" /> : `$${low.toLocaleString(undefined, { minimumFractionDigits: 2 })}`}
                </span>
              </div>
              <div className="flex justify-between py-1 border-b border-border">
                <span className="text-muted-foreground">Trading Volume</span>
                <span className="font-mono text-foreground font-semibold">
                  {isLoading ? <Skeleton className="h-4 w-16" /> : `$${volume.toLocaleString(undefined, { maximumFractionDigits: 0 })}`}
                </span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-muted-foreground">Average Price</span>
                <span className="font-mono text-foreground font-semibold">
                  {isLoading ? <Skeleton className="h-4 w-16" /> : `$${avgPrice.toLocaleString(undefined, { minimumFractionDigits: 2 })}`}
                </span>
              </div>
            </div>

            <div className="pt-2">
              <span className="text-[10px] text-muted-foreground uppercase font-semibold block mb-2">Technical Verdict</span>
              <div className={`p-3 rounded-xl border text-[11px] font-semibold flex items-center gap-2 ${technicalVerdict.color}`}>
                <Zap className="size-4 shrink-0" />
                {isLoading ? <Skeleton className="h-4 w-32" /> : technicalVerdict.text}
              </div>
            </div>

            <Separator className="my-2" />

            <div className="pt-2">
              <span className="text-[10px] text-muted-foreground uppercase font-semibold block mb-2">Technical Indicators</span>
              <div className="space-y-2">
                <div className="flex justify-between py-1 border-b border-border items-center">
                  <span className="text-muted-foreground">RSI (14)</span>
                  <Badge variant="outline" className={`font-mono text-[10px] font-semibold py-0 px-1.5 ${technicalIndicators.rsiColor}`}>
                    {isLoading ? <Skeleton className="h-4 w-8" /> : `${technicalIndicators.rsiValue.toFixed(1)} (${technicalIndicators.rsiStatus})`}
                  </Badge>
                </div>
                <div className="flex justify-between py-1 border-b border-border">
                  <span className="text-muted-foreground">Volatility</span>
                  <span className="font-mono text-foreground font-semibold">
                    {isLoading ? <Skeleton className="h-4 w-8" /> : `${technicalIndicators.avgVolatility.toFixed(2)}%`}
                  </span>
                </div>
                <div className="flex justify-between py-1 border-b border-border">
                  <span className="text-muted-foreground">Dist. to High</span>
                  <span className="font-mono text-red-600 dark:text-red-400 font-semibold">
                    {isLoading ? <Skeleton className="h-4 w-8" /> : `${technicalIndicators.distToHigh.toFixed(2)}%`}
                  </span>
                </div>
                <div className="flex justify-between py-1">
                  <span className="text-muted-foreground">Dist. to Low</span>
                  <span className="font-mono text-green-600 dark:text-green-400 font-semibold">
                    {isLoading ? <Skeleton className="h-4 w-8" /> : `+${technicalIndicators.distToLow.toFixed(2)}%`}
                  </span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Global Market Sentiment breakdown */}
        <Card className="border border-border bg-card text-card-foreground">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-semibold uppercase text-muted-foreground">Market Mood</CardTitle>
            <CardDescription className="text-xs text-muted-foreground">
              Aggregated FinBERT news sentiment
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 pt-2 text-xs">
            {loadingSentiment ? (
              <div className="space-y-2">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-full" />
              </div>
            ) : (
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Brain className="size-4 text-violet-500" />
                    <span className="font-semibold text-foreground">
                      {sentiment?.overall_label || "Neutral"}
                    </span>
                  </div>
                  <span className="font-mono text-muted-foreground">
                    score: {sentiment?.overall_score?.toFixed(2) || "0.0"}
                  </span>
                </div>
                
                <div className="space-y-2 pt-1">
                  <div>
                    <div className="flex justify-between mb-1 text-[10px] text-muted-foreground">
                      <span>Positive</span>
                      <span className="font-mono text-green-600 dark:text-green-400 font-semibold">{sentiment?.positive_pct || 0}%</span>
                    </div>
                    <div className="h-1.5 w-full bg-secondary rounded-full overflow-hidden">
                      <div
                        className="h-full bg-green-500 transition-all"
                        style={{ width: `${sentiment?.positive_pct || 0}%` }}
                      />
                    </div>
                  </div>
                  
                  <div>
                    <div className="flex justify-between mb-1 text-[10px] text-muted-foreground">
                      <span>Neutral</span>
                      <span className="font-mono text-muted-foreground font-semibold">{sentiment?.neutral_pct || 0}%</span>
                    </div>
                    <div className="h-1.5 w-full bg-secondary rounded-full overflow-hidden">
                      <div
                        className="h-full bg-zinc-400 dark:bg-zinc-500 transition-all"
                        style={{ width: `${sentiment?.neutral_pct || 0}%` }}
                      />
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between mb-1 text-[10px] text-muted-foreground">
                      <span>Negative</span>
                      <span className="font-mono text-red-600 dark:text-red-400 font-semibold">{sentiment?.negative_pct || 0}%</span>
                    </div>
                    <div className="h-1.5 w-full bg-secondary rounded-full overflow-hidden">
                      <div
                        className="h-full bg-red-500 transition-all"
                        style={{ width: `${sentiment?.negative_pct || 0}%` }}
                      />
                    </div>
                  </div>
                </div>

                <div className="text-[10px] text-muted-foreground flex items-center gap-1.5 pt-2">
                  <Info className="size-3 shrink-0" />
                  <span>Analyzed {sentiment?.article_count || 0} news articles.</span>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Market Sentiment Gauge Card */}
        <Card className="border border-border bg-card text-card-foreground flex-grow flex flex-col justify-between">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-semibold uppercase text-muted-foreground flex items-center gap-1.5">
              <Compass className="size-4 text-emerald-500" />
              Sentiment Gauge
            </CardTitle>
            <CardDescription className="text-xs text-muted-foreground">
              Market fear & greed index based on news
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col items-center justify-center p-6 pt-2 flex-grow min-h-[220px]">
            {loadingSentiment ? (
              <Skeleton className="h-32 w-32 rounded-full animate-pulse" />
            ) : (
              <div className="relative w-full max-w-[220px] flex flex-col items-center my-auto">
                <svg viewBox="0 0 100 55" className="w-full">
                  <defs>
                    <linearGradient id="gauge-grad" x1="0" y1="0" x2="1" y2="0">
                      <stop offset="0%" stopColor="#ef4444" /> {/* Red */}
                      <stop offset="50%" stopColor="#eab308" /> {/* Yellow */}
                      <stop offset="100%" stopColor="#22c55e" /> {/* Green */}
                    </linearGradient>
                  </defs>
                  {/* Background Track */}
                  <path
                    d="M 10 50 A 40 40 0 0 1 90 50"
                    fill="none"
                    stroke="rgba(120,120,120,0.1)"
                    strokeWidth="8"
                    strokeLinecap="round"
                  />
                  {/* Filled Track */}
                  <path
                    d="M 10 50 A 40 40 0 0 1 90 50"
                    fill="none"
                    stroke="url(#gauge-grad)"
                    strokeWidth="8"
                    strokeLinecap="round"
                    strokeDasharray="126"
                    strokeDashoffset={126 - (126 * ((sentiment?.overall_score ?? 0) + 1) * 50) / 100}
                    className="transition-all duration-1000 ease-out"
                  />
                </svg>
                {/* Score display in center */}
                <div className="absolute bottom-1 text-center">
                  <span className="text-3xl font-black font-mono tracking-tight text-foreground block">
                    {Math.round(((sentiment?.overall_score ?? 0) + 1) * 50)}
                  </span>
                  <span className={`text-xs font-black uppercase tracking-wider ${
                    (sentiment?.overall_score ?? 0) > 0.2
                      ? "text-green-500"
                      : (sentiment?.overall_score ?? 0) < -0.2
                      ? "text-red-500"
                      : "text-zinc-500"
                  }`}>
                    {sentiment?.overall_label || "Neutral"}
                  </span>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
    {showAnalysis && (
      <MarketAnalysisSection 
        view="bottom" 
        days={compDays}
        selectedCoins={compCoins}
        corrBase={corrBase}
        onDaysChange={(val) => setCompDays(val)}
        onCoinsChange={(val) => setCompCoins(val)}
        onCorrBaseChange={(val) => setCorrBase(val)}
      />
    )}
  </div>
);
}

