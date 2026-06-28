"use client";

import { usePortfolio, PortfolioPosition } from "@/hooks/use-portfolio";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { apiClient } from "@/lib/api-client";
import { Wallet, Plus, Trash2, ArrowUpRight, ArrowDownRight, Briefcase, TrendingUp, PieChart } from "lucide-react";
import { useState, useEffect, useMemo } from "react";
import { toast } from "sonner";

interface RichPortfolioPosition extends PortfolioPosition {
  currentPrice: number;
  currentValue: number;
  totalCost: number;
  netProfitLoss: number;
  profitLossPct: number;
  priceFlash?: "up" | "down" | null;
}

export default function PortfolioPage() {
  const { positions, isLoading: isPortfolioLoading, error, addPosition, deletePosition } = usePortfolio();
  const [richPositions, setRichPositions] = useState<RichPortfolioPosition[]>([]);
  const [newPosition, setNewPosition] = useState({ symbol: "", quantity: 0, avg_buy_price: 0 });
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Fetch summaries for held assets in parallel to calculate real P&L
  useEffect(() => {
    const loadPortfolioMetrics = async () => {
      if (positions.length === 0) {
        setRichPositions([]);
        return;
      }

      try {
        const results = await Promise.all(
          positions.map(async (pos) => {
            // Check if symbol ends with USDT (backend records might just be symbol name)
            const cleanSymbol = pos.symbol.endsWith("USDT") ? pos.symbol : `${pos.symbol}USDT`;
            try {
              const summary = await apiClient<any>(`/api/v1/coins/${cleanSymbol}/summary`);
              const currentPrice = summary.day_close || pos.avg_buy_price;
              const totalCost = pos.quantity * pos.avg_buy_price;
              const currentValue = pos.quantity * currentPrice;
              const netProfitLoss = currentValue - totalCost;
              const profitLossPct = totalCost > 0 ? (netProfitLoss / totalCost) * 100 : 0;

              return {
                ...pos,
                currentPrice,
                currentValue,
                totalCost,
                netProfitLoss,
                profitLossPct,
              };
            } catch (err) {
              // Fallback mockup template price if no DB summary exists yet
              const isBtc = pos.symbol.includes("BTC");
              const currentPrice = isBtc ? 64250 : 3450;
              const totalCost = pos.quantity * pos.avg_buy_price;
              const currentValue = pos.quantity * currentPrice;
              const netProfitLoss = currentValue - totalCost;
              const profitLossPct = totalCost > 0 ? (netProfitLoss / totalCost) * 100 : 0;

              return {
                ...pos,
                currentPrice,
                currentValue,
                totalCost,
                netProfitLoss,
                profitLossPct,
              };
            }
          })
        );
        setRichPositions(results);
      } catch (err) {
        console.error("Failed to load portfolio details", err);
      }
    };

    loadPortfolioMetrics();
  }, [positions]);

  // Real-time ticking price simulator
  useEffect(() => {
    if (richPositions.length === 0) return;

    const interval = setInterval(() => {
      setRichPositions((prev) =>
        prev.map((pos) => {
          // Random price tick (0.01% to 0.05% fluctuation)
          const isUp = Math.random() > 0.48;
          const fluctuation = pos.currentPrice * (0.0001 + Math.random() * 0.0004);
          const newPrice = isUp ? pos.currentPrice + fluctuation : pos.currentPrice - fluctuation;

          const totalCost = pos.quantity * pos.avg_buy_price;
          const currentValue = pos.quantity * newPrice;
          const netProfitLoss = currentValue - totalCost;
          const profitLossPct = totalCost > 0 ? (netProfitLoss / totalCost) * 100 : 0;

          return {
            ...pos,
            currentPrice: newPrice,
            currentValue,
            netProfitLoss,
            profitLossPct,
            priceFlash: isUp ? "up" : "down",
          };
        })
      );

      // Reset flash effect after 400ms
      setTimeout(() => {
        setRichPositions((prev) =>
          prev.map((c) => ({ ...c, priceFlash: null }))
        );
      }, 400);
    }, 2000);

    return () => clearInterval(interval);
  }, [richPositions.length]);

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newPosition.symbol || newPosition.quantity <= 0 || newPosition.avg_buy_price <= 0) {
      toast.error("Please provide valid asset details.");
      return;
    }
    
    // Ensure standard symbol format (e.g. BTCUSDT or BTC)
    let formattedSymbol = newPosition.symbol.trim().toUpperCase();
    if (!formattedSymbol.endsWith("USDT") && ["BTC", "ETH", "BNB", "XRP", "SOL", "ADA", "DOT", "DOGE", "MATIC", "LINK"].includes(formattedSymbol)) {
      formattedSymbol = `${formattedSymbol}USDT`;
    }

    setIsSubmitting(true);
    try {
      await addPosition({
        symbol: formattedSymbol,
        quantity: newPosition.quantity,
        avg_buy_price: newPosition.avg_buy_price,
      });
      setNewPosition({ symbol: "", quantity: 0, avg_buy_price: 0 });
      toast.success("Position added successfully!");
    } catch (err) {
      toast.error("Failed to add portfolio position.");
    } finally {
      setIsSubmitting(false);
    }
  };

  // Portfolio Totals & Statistics
  const portfolioStats = useMemo(() => {
    const totalCost = richPositions.reduce((sum, p) => sum + p.totalCost, 0);
    const totalValue = richPositions.reduce((sum, p) => sum + p.currentValue, 0);
    const totalProfit = totalValue - totalCost;
    const profitPct = totalCost > 0 ? (totalProfit / totalCost) * 100 : 0;

    // Find best performer
    let best = null;
    if (richPositions.length > 0) {
      best = [...richPositions].sort((a, b) => b.profitLossPct - a.profitLossPct)[0];
    }

    return {
      totalCost,
      totalValue,
      totalProfit,
      profitPct,
      best,
    };
  }, [richPositions]);

  // Asset allocation percentages
  const allocation = useMemo(() => {
    if (portfolioStats.totalValue === 0) return [];
    return richPositions.map((pos) => ({
      symbol: pos.symbol.replace("USDT", ""),
      percentage: (pos.currentValue / portfolioStats.totalValue) * 100,
    })).sort((a, b) => b.percentage - a.percentage);
  }, [richPositions, portfolioStats.totalValue]);

  // Predefined colored bars for allocation visual (up to 5 colors, fallback to gray)
  const ALLOCATION_COLORS = ["bg-cyan-500", "bg-indigo-500", "bg-emerald-500", "bg-amber-500", "bg-rose-500"];

  if (isPortfolioLoading) {
    return (
      <div className="px-4 lg:px-6 py-6 space-y-6">
        <Skeleton className="h-10 w-48 bg-muted/40" />
        <div className="grid gap-4 md:grid-cols-4">
          {[...Array(4)].map((_, i) => (
            <Skeleton key={i} className="h-24 w-full bg-muted/40 rounded-xl" />
          ))}
        </div>
        <Skeleton className="h-44 w-full bg-muted/40 rounded-xl" />
        <Skeleton className="h-64 w-full bg-muted/40 rounded-xl" />
      </div>
    );
  }

  return (
    <div className="px-4 lg:px-6 py-6 space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Briefcase className="size-6 text-cyan-600 dark:text-cyan-400" />
          <h1 className="text-2xl font-black tracking-tight text-foreground">Investment Portfolio</h1>
        </div>
      </div>

      {/* Portfolio Performance Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card className="bg-card border-border shadow-sm">
          <CardContent className="p-5 flex items-center justify-between">
            <div className="space-y-1">
              <span className="text-[10px] uppercase tracking-widest text-muted-foreground font-bold">Portfolio Value</span>
              <p className="text-2xl font-black font-mono text-foreground tracking-tight">
                ${portfolioStats.totalValue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </p>
            </div>
            <div className="p-3 bg-cyan-500/10 text-cyan-600 dark:text-cyan-400 rounded-xl border border-cyan-500/15">
              <Wallet className="size-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card border-border shadow-sm">
          <CardContent className="p-5 flex items-center justify-between">
            <div className="space-y-1">
              <span className="text-[10px] uppercase tracking-widest text-muted-foreground font-bold">Total Investment</span>
              <p className="text-2xl font-black font-mono text-foreground tracking-tight">
                ${portfolioStats.totalCost.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </p>
            </div>
            <div className="p-3 bg-zinc-500/10 text-zinc-500 rounded-xl border border-border/15">
              <Briefcase className="size-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card border-border shadow-sm">
          <CardContent className="p-5 flex items-center justify-between">
            <div className="space-y-1">
              <span className="text-[10px] uppercase tracking-widest text-muted-foreground font-bold">Total Net P&L</span>
              <div className="flex flex-col">
                <p className={`text-xl font-black font-mono tracking-tight ${portfolioStats.totalProfit >= 0 ? "text-emerald-600 dark:text-emerald-400" : "text-rose-600 dark:text-rose-400"}`}>
                  {portfolioStats.totalProfit >= 0 ? "+" : ""}${portfolioStats.totalProfit.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </p>
                <span className={`text-xs font-bold ${portfolioStats.totalProfit >= 0 ? "text-emerald-500" : "text-rose-500"}`}>
                  {portfolioStats.totalProfit >= 0 ? "+" : ""}{portfolioStats.profitPct.toFixed(2)}%
                </span>
              </div>
            </div>
            <div className={`p-3 rounded-xl border ${portfolioStats.totalProfit >= 0 ? "bg-emerald-500/10 text-emerald-500 border-emerald-500/15" : "bg-rose-500/10 text-rose-500 border-rose-500/15"}`}>
              <TrendingUp className="size-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card border-border shadow-sm">
          <CardContent className="p-5 flex items-center justify-between">
            <div className="space-y-1">
              <span className="text-[10px] uppercase tracking-widest text-muted-foreground font-bold">Best Performer</span>
              {portfolioStats.best ? (
                <div>
                  <p className="text-lg font-black uppercase text-foreground">
                    {portfolioStats.best.symbol.replace("USDT", "")}
                  </p>
                  <span className="text-xs font-bold text-emerald-500">
                    +{portfolioStats.best.profitLossPct.toFixed(2)}% Return
                  </span>
                </div>
              ) : (
                <p className="text-sm font-semibold text-muted-foreground">No assets held</p>
              )}
            </div>
            <div className="p-3 bg-amber-500/10 text-amber-500 rounded-xl border border-amber-500/15">
              <ArrowUpRight className="size-5" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Asset Allocation progress visualizer */}
      {allocation.length > 0 && (
        <Card className="bg-card border-border shadow-sm">
          <CardContent className="p-5 space-y-4">
            <div className="flex items-center gap-1.5">
              <PieChart className="size-4 text-cyan-500" />
              <h3 className="text-xs uppercase tracking-wider text-muted-foreground font-bold">Asset Allocation</h3>
            </div>
            
            {/* Visual allocation block */}
            <div className="h-3.5 w-full rounded-full bg-muted overflow-hidden flex">
              {allocation.map((item, idx) => (
                <div 
                  key={item.symbol} 
                  className={`h-full ${ALLOCATION_COLORS[idx % ALLOCATION_COLORS.length]}`} 
                  style={{ width: `${item.percentage}%` }}
                  title={`${item.symbol}: ${item.percentage.toFixed(1)}%`}
                />
              ))}
            </div>

            {/* Labels grid */}
            <div className="flex flex-wrap gap-x-5 gap-y-2 pt-1.5">
              {allocation.map((item, idx) => (
                <div key={item.symbol} className="flex items-center gap-2 text-xs">
                  <div className={`size-2.5 rounded-full ${ALLOCATION_COLORS[idx % ALLOCATION_COLORS.length]}`} />
                  <span className="font-bold text-foreground">{item.symbol}</span>
                  <span className="text-muted-foreground font-mono">{item.percentage.toFixed(1)}%</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Add New Position Panel */}
      <Card className="border-border bg-card shadow-sm">
        <CardHeader className="pb-3 border-b border-border/50">
          <CardTitle className="text-sm font-bold uppercase tracking-wider text-foreground">Add New Holding Position</CardTitle>
        </CardHeader>
        <CardContent className="pt-5">
          <form onSubmit={handleAdd} className="grid gap-4 sm:grid-cols-2 md:grid-cols-4 items-end">
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Asset Symbol</label>
              <Input 
                placeholder="e.g. BTC" 
                value={newPosition.symbol} 
                onChange={e => setNewPosition({...newPosition, symbol: e.target.value.toUpperCase()})}
                className="h-10 rounded-full bg-background border-border text-sm focus:border-cyan-500/50"
                disabled={isSubmitting}
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Buy Quantity</label>
              <Input 
                type="number" 
                step="any"
                placeholder="0.00"
                value={newPosition.quantity || ""} 
                onChange={e => {
                  const val = parseFloat(e.target.value);
                  setNewPosition({...newPosition, quantity: isNaN(val) ? 0 : val});
                }}
                className="h-10 rounded-full bg-background border-border text-sm focus:border-cyan-500/50"
                disabled={isSubmitting}
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Avg. Buy Price ($)</label>
              <Input 
                type="number" 
                step="any"
                placeholder="0.00"
                value={newPosition.avg_buy_price || ""} 
                onChange={e => {
                  const val = parseFloat(e.target.value);
                  setNewPosition({...newPosition, avg_buy_price: isNaN(val) ? 0 : val});
                }}
                className="h-10 rounded-full bg-background border-border text-sm focus:border-cyan-500/50"
                disabled={isSubmitting}
              />
            </div>
            <Button type="submit" disabled={isSubmitting} className="h-10 rounded-full bg-cyan-600 hover:bg-cyan-500 text-white font-bold transition-all shadow-md shadow-cyan-500/10">
              <Plus className="size-4.5 mr-2" /> Add Position
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Holdings List */}
      <div className="space-y-4">
        <h2 className="text-lg font-black tracking-tight text-foreground uppercase tracking-wider">Asset Holdings</h2>
        {error && <div className="text-destructive text-sm bg-destructive/10 p-3 rounded-xl border border-destructive/20">{error}</div>}
        
        {richPositions.length === 0 ? (
          <div className="text-center py-16 text-muted-foreground border-2 border-dashed border-border rounded-2xl bg-card">
            <Briefcase className="size-8 mx-auto text-zinc-500 mb-2" />
            <p className="text-sm">No investment positions held in your portfolio yet.</p>
            <p className="text-xs text-zinc-500 mt-1">Add positions above to start tracking your net returns.</p>
          </div>
        ) : (
          <div className="rounded-2xl border border-border bg-card text-card-foreground overflow-hidden shadow-md">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-border bg-muted/40 text-[10px] uppercase tracking-wider text-muted-foreground font-bold">
                    <th className="p-4 pl-6">Asset / Holdings</th>
                    <th className="p-4">Holdings Quantity</th>
                    <th className="p-4">Avg. Buy Price</th>
                    <th className="p-4">Current Price</th>
                    <th className="p-4">Total Cost</th>
                    <th className="p-4">Current Value</th>
                    <th className="p-4">Net P&L Return</th>
                    <th className="p-4 pr-6 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/60 text-sm text-foreground">
                  {richPositions.map((pos) => {
                    const isPosProfit = pos.netProfitLoss >= 0;
                    const shortSymbol = pos.symbol.replace("USDT", "");
                    return (
                      <tr key={pos.id} className="hover:bg-muted/30 transition-colors duration-250">
                        {/* Symbol */}
                        <td className="p-4 pl-6 font-bold uppercase tracking-tight text-base text-foreground">
                          {shortSymbol}
                        </td>

                        {/* Quantity */}
                        <td className="p-4 font-mono font-medium">
                          {pos.quantity}
                        </td>

                        {/* Avg Buy */}
                        <td className="p-4 font-mono text-zinc-500 dark:text-zinc-400">
                          ${pos.avg_buy_price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </td>

                        {/* Current Market Price */}
                        <td className="p-4">
                          <span 
                            className={`font-mono font-bold transition-all duration-300 px-1 rounded-sm ${
                              pos.priceFlash === "up" 
                                ? "bg-emerald-500/20 text-emerald-600 dark:text-emerald-400" 
                                : pos.priceFlash === "down" 
                                ? "bg-rose-500/20 text-rose-600 dark:text-rose-400" 
                                : "text-foreground"
                            }`}
                          >
                            ${pos.currentPrice.toLocaleString(undefined, {
                              minimumFractionDigits: pos.currentPrice < 1 ? 4 : 2,
                              maximumFractionDigits: pos.currentPrice < 1 ? 4 : 2,
                            })}
                          </span>
                        </td>

                        {/* Total Cost */}
                        <td className="p-4 font-mono text-zinc-500 dark:text-zinc-400">
                          ${pos.totalCost.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                        </td>

                        {/* Current Value */}
                        <td className="p-4 font-mono font-semibold text-foreground">
                          ${pos.currentValue.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                        </td>

                        {/* P&L Return */}
                        <td className="p-4">
                          <div className="flex flex-col justify-center">
                            <span className={`font-mono font-bold text-xs ${isPosProfit ? "text-emerald-600 dark:text-emerald-400" : "text-rose-600 dark:text-rose-400"}`}>
                              {isPosProfit ? "+" : ""}${pos.netProfitLoss.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                            </span>
                            <span className={`text-[10px] font-bold ${isPosProfit ? "text-emerald-500" : "text-rose-500"}`}>
                              {isPosProfit ? "+" : ""}{pos.profitLossPct.toFixed(2)}%
                            </span>
                          </div>
                        </td>

                        {/* Action delete */}
                        <td className="p-4 pr-6 text-right">
                          <Button 
                            variant="ghost" 
                            size="icon" 
                            className="size-8 text-muted-foreground hover:text-destructive hover:bg-destructive/10 rounded-full"
                            onClick={() => deletePosition(pos.id)}
                          >
                            <Trash2 className="size-4" />
                          </Button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
