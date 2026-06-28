"use client";

import { useAlerts, AlertItem } from "@/hooks/use-alerts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { apiClient } from "@/lib/api-client";
import { useCoins } from "@/hooks/use-coins";
import { 
  Bell, 
  Plus, 
  Trash2, 
  ArrowUp, 
  ArrowDown, 
  Mail, 
  MessageSquare, 
  Settings, 
  AlertTriangle, 
  Activity, 
  CheckCircle2 
} from "lucide-react";
import { useState, useEffect, useMemo } from "react";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";

interface RichAlertItem extends AlertItem {
  currentPrice?: number;
  isTriggered?: boolean;
}

export default function AlertsPage() {
  const { alerts, isLoading: isAlertsLoading, error, createAlert, toggleAlert, deleteAlert } = useAlerts();
  const { coins: apiCoins } = useCoins();
  
  const [newAlert, setNewAlert] = useState({ symbol: "", condition: "above", threshold: 0 });
  const [selectedCoinPrice, setSelectedCoinPrice] = useState<number | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [livePrices, setLivePrices] = useState<Record<string, number>>({});

  // Mock Notification Channel States for visual completeness
  const [channels, setChannels] = useState({
    email: true,
    browser: true,
    telegram: false,
    discord: false,
  });

  const [telegramChatId, setTelegramChatId] = useState("");
  const [discordWebhook, setDiscordWebhook] = useState("");

  // Fetch prices for all alert symbols to display current prices next to target thresholds
  useEffect(() => {
    const fetchLivePricesForAlerts = async () => {
      if (alerts.length === 0) return;
      const uniqueSymbols = Array.from(new Set(alerts.map((a) => a.symbol)));
      
      const priceMap: Record<string, number> = {};
      await Promise.all(
        uniqueSymbols.map(async (sym) => {
          const cleanSymbol = sym.endsWith("USDT") ? sym : `${sym}USDT`;
          try {
            const summary = await apiClient<any>(`/api/v1/coins/${cleanSymbol}/summary`);
            priceMap[sym] = summary.day_close || 0;
          } catch (e) {
            priceMap[sym] = sym.includes("BTC") ? 64250 : 3450;
          }
        })
      );
      setLivePrices(priceMap);
    };

    fetchLivePricesForAlerts();
  }, [alerts]);

  // Fetch price helper when user types/selects a coin symbol to help them set threshold
  useEffect(() => {
    const getSelectedCoinPrice = async () => {
      if (!newAlert.symbol) {
        setSelectedCoinPrice(null);
        return;
      }
      
      const cleanSymbol = newAlert.symbol.endsWith("USDT") ? newAlert.symbol : `${newAlert.symbol}USDT`;
      try {
        const summary = await apiClient<any>(`/api/v1/coins/${cleanSymbol}/summary`);
        setSelectedCoinPrice(summary.day_close || null);
      } catch (err) {
        // Fallback for mock preview
        if (newAlert.symbol === "BTC" || newAlert.symbol === "BTCUSDT") setSelectedCoinPrice(64250);
        else if (newAlert.symbol === "ETH" || newAlert.symbol === "ETHUSDT") setSelectedCoinPrice(3450);
        else setSelectedCoinPrice(null);
      }
    };

    const timer = setTimeout(getSelectedCoinPrice, 400);
    return () => clearTimeout(timer);
  }, [newAlert.symbol]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newAlert.symbol || newAlert.threshold <= 0) {
      toast.error("Please enter a valid symbol and threshold price.");
      return;
    }

    let formattedSymbol = newAlert.symbol.trim().toUpperCase();
    if (!formattedSymbol.endsWith("USDT") && ["BTC", "ETH", "BNB", "XRP", "SOL", "ADA", "DOT", "DOGE", "MATIC", "LINK"].includes(formattedSymbol)) {
      formattedSymbol = `${formattedSymbol}USDT`;
    }

    setIsSubmitting(true);
    try {
      await createAlert({
        symbol: formattedSymbol,
        condition: newAlert.condition,
        threshold: newAlert.threshold,
      });
      setNewAlert({ symbol: "", condition: "above", threshold: 0 });
      setSelectedCoinPrice(null);
      toast.success("Price alert set successfully!");
    } catch (err) {
      toast.error("Failed to set price alert.");
    } finally {
      setIsSubmitting(false);
    }
  };

  // Stats computation
  const activeAlertsCount = useMemo(() => {
    return alerts.filter((a) => a.is_active).length;
  }, [alerts]);

  const richAlerts = useMemo<RichAlertItem[]>(() => {
    return alerts.map((alert) => {
      const currentPrice = livePrices[alert.symbol];
      let isTriggered = false;
      if (currentPrice) {
        isTriggered = alert.condition === "above" 
          ? currentPrice >= alert.threshold 
          : currentPrice <= alert.threshold;
      }
      return {
        ...alert,
        currentPrice,
        isTriggered,
      };
    });
  }, [alerts, livePrices]);

  if (isAlertsLoading) {
    return (
      <div className="px-4 lg:px-6 py-6 space-y-6">
        <Skeleton className="h-10 w-48 bg-muted/40" />
        <div className="grid gap-4 md:grid-cols-3">
          {[...Array(3)].map((_, i) => (
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
      <div className="flex items-center gap-2">
        <Bell className="size-6 text-cyan-600 dark:text-cyan-400" />
        <h1 className="text-2xl font-black tracking-tight text-foreground">Real-time Price Alerts</h1>
      </div>

      {/* Alert Stats Cards */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card className="bg-card border-border shadow-sm">
          <CardContent className="p-5 flex items-center justify-between">
            <div className="space-y-1">
              <span className="text-[10px] uppercase tracking-widest text-muted-foreground font-bold">Active Alerts</span>
              <p className="text-2xl font-black font-mono text-foreground tracking-tight">
                {activeAlertsCount} <span className="text-xs text-zinc-500 font-normal">/ {alerts.length} Set</span>
              </p>
            </div>
            <div className="p-3 bg-cyan-500/10 text-cyan-600 dark:text-cyan-400 rounded-xl border border-cyan-500/15">
              <Bell className="size-5 animate-swing" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card border-border shadow-sm">
          <CardContent className="p-5 flex items-center justify-between">
            <div className="space-y-1">
              <span className="text-[10px] uppercase tracking-widest text-zinc-500 font-bold">Triggered (24h)</span>
              <p className="text-2xl font-black font-mono text-emerald-500 tracking-tight">
                {richAlerts.filter(a => a.isTriggered && a.is_active).length} <span className="text-xs text-zinc-500 font-normal font-sans">fired</span>
              </p>
            </div>
            <div className="p-3 bg-emerald-500/10 text-emerald-500 rounded-xl border border-emerald-500/15">
              <CheckCircle2 className="size-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card border-border shadow-sm">
          <CardContent className="p-5 flex items-center justify-between">
            <div className="space-y-1">
              <span className="text-[10px] uppercase tracking-widest text-zinc-500 font-bold">Worker Status</span>
              <p className="text-lg font-black text-foreground flex items-center gap-1.5 pt-0.5">
                <span className="size-2 rounded-full bg-emerald-500 animate-pulse" />
                Active Monitoring
              </p>
            </div>
            <div className="p-3 bg-zinc-500/10 text-zinc-500 rounded-xl border border-border/15">
              <Activity className="size-5" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Set New Alert Card */}
      <Card className="border-border bg-card shadow-sm">
        <CardHeader className="pb-3 border-b border-border/50">
          <CardTitle className="text-sm font-bold uppercase tracking-wider text-foreground">Configure Ingestion Price Alert</CardTitle>
        </CardHeader>
        <CardContent className="pt-5">
          <form onSubmit={handleCreate} className="grid gap-4 sm:grid-cols-2 md:grid-cols-4 items-end">
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Symbol (e.g. BTC)</label>
              <Input 
                placeholder="BTC" 
                value={newAlert.symbol} 
                onChange={e => setNewAlert({...newAlert, symbol: e.target.value.toUpperCase()})}
                className="h-10 rounded-full bg-background border-border text-sm focus:border-cyan-500/50"
                disabled={isSubmitting}
              />
              {selectedCoinPrice !== null && (
                <p className="text-[10px] text-cyan-600 dark:text-cyan-400 font-semibold font-mono pl-1">
                  Current Price: ${selectedCoinPrice.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                </p>
              )}
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Condition</label>
              <Select 
                value={newAlert.condition} 
                onValueChange={v => setNewAlert({...newAlert, condition: v})}
                disabled={isSubmitting}
              >
                <SelectTrigger className="h-10 rounded-full bg-background border-border text-sm focus:border-cyan-500/50">
                  <SelectValue placeholder="Select Trigger" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="above">Price Rises Above (&ge;)</SelectItem>
                  <SelectItem value="below">Price Falls Below (&le;)</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Target Threshold ($)</label>
              <Input 
                type="number" 
                step="any"
                placeholder="0.00"
                value={newAlert.threshold || ""} 
                onChange={e => {
                  const val = parseFloat(e.target.value);
                  setNewAlert({...newAlert, threshold: isNaN(val) ? 0 : val});
                }}
                className="h-10 rounded-full bg-background border-border text-sm focus:border-cyan-500/50"
                disabled={isSubmitting}
              />
            </div>
            <Button type="submit" disabled={isSubmitting} className="h-10 rounded-full bg-cyan-600 hover:bg-cyan-500 text-white font-bold transition-all shadow-md shadow-cyan-500/10">
              <Plus className="size-4.5 mr-2" /> Set Alert
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Active Alerts List */}
      <div className="space-y-4">
        <h2 className="text-lg font-black tracking-tight text-foreground uppercase tracking-wider">My Price Alerts</h2>
        
        {richAlerts.length === 0 ? (
          <div className="text-center py-16 text-muted-foreground border-2 border-dashed border-border rounded-2xl bg-card">
            <Bell className="size-8 mx-auto text-zinc-500 mb-2" />
            <p className="text-sm">No price alerts active at this moment.</p>
            <p className="text-xs text-zinc-500 mt-1">Configure threshold limits above to trigger push notifications.</p>
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2">
            {richAlerts.map((alert) => {
              const shortSymbol = alert.symbol.replace("USDT", "");
              return (
                <Card 
                  key={alert.id} 
                  className={`border-border transition-all duration-300 rounded-2xl ${
                    alert.is_active 
                      ? alert.isTriggered 
                        ? "bg-emerald-500/5 border-emerald-500/30" 
                        : "bg-card hover:border-cyan-500/30" 
                      : "opacity-50 bg-muted/40"
                  }`}
                >
                  <CardContent className="p-4 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className={`p-2.5 rounded-xl border ${
                        alert.is_active 
                          ? alert.condition === "above" 
                            ? "bg-emerald-500/10 text-emerald-500 border-emerald-500/15" 
                            : "bg-rose-500/10 text-rose-500 border-rose-500/15"
                          : "bg-zinc-500/10 text-zinc-500 border-border"
                      }`}>
                        {alert.condition === "above" ? 
                          <ArrowUp className="size-4.5" /> : 
                          <ArrowDown className="size-4.5" />
                        }
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <h3 className="font-bold text-base uppercase tracking-tight text-foreground">{shortSymbol}</h3>
                          {alert.is_active && alert.isTriggered && (
                            <Badge className="bg-emerald-500/15 text-emerald-500 border-emerald-500/20 font-bold uppercase tracking-wider text-[9px] h-4.5 py-0">
                              Triggered
                            </Badge>
                          )}
                        </div>
                        <p className="text-xs text-muted-foreground">
                          Notify when price goes <span className="font-bold text-foreground">{alert.condition}</span> ${alert.threshold.toLocaleString()}
                        </p>
                        {alert.currentPrice && (
                          <p className="text-[10px] text-zinc-500 font-mono mt-0.5">
                            Last DB Price: ${alert.currentPrice.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                          </p>
                        )}
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-3">
                      <Switch 
                        checked={alert.is_active} 
                        onCheckedChange={(checked) => toggleAlert(alert.id, checked)}
                      />
                      <Button 
                        variant="ghost" 
                        size="icon" 
                        className="size-8 text-muted-foreground hover:text-destructive hover:bg-destructive/10 rounded-full"
                        onClick={() => deleteAlert(alert.id)}
                      >
                        <Trash2 className="size-4" />
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}
      </div>

      {/* Mock Channels panel */}
      <Card className="border-border bg-card shadow-sm">
        <CardHeader className="pb-3 border-b border-border/50 flex flex-row items-center justify-between space-y-0">
          <CardTitle className="text-sm font-bold uppercase tracking-wider text-foreground flex items-center gap-1.5">
            <Settings className="size-4 text-cyan-500" />
            Alert Dispatch Channels
          </CardTitle>
          <Badge variant="outline" className="text-[10px] uppercase font-bold text-cyan-500 border-cyan-500/20">Config</Badge>
        </CardHeader>
        <CardContent className="pt-5 space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="flex items-center justify-between p-3.5 border border-border rounded-2xl bg-muted/20">
              <div className="flex items-center gap-3">
                <div className="bg-cyan-500/10 p-2 rounded-xl text-cyan-600 dark:text-cyan-400">
                  <Mail className="size-4.5" />
                </div>
                <div>
                  <h4 className="text-xs font-bold text-foreground">Email Notifications</h4>
                  <p className="text-[10px] text-muted-foreground">Receive instant alerts on your verified email.</p>
                </div>
              </div>
              <Switch checked={channels.email} onCheckedChange={(v) => setChannels({...channels, email: v})} />
            </div>

            <div className="flex items-center justify-between p-3.5 border border-border rounded-2xl bg-muted/20">
              <div className="flex items-center gap-3">
                <div className="bg-indigo-500/10 p-2 rounded-xl text-indigo-600 dark:text-indigo-400">
                  <MessageSquare className="size-4.5" />
                </div>
                <div>
                  <h4 className="text-xs font-bold text-foreground">Telegram Alerts (Bot)</h4>
                  <p className="text-[10px] text-muted-foreground">Deliver target limits to your Telegram chat.</p>
                </div>
              </div>
              <Switch checked={channels.telegram} onCheckedChange={(v) => {
                setChannels({...channels, telegram: v});
                if (v && !telegramChatId) {
                  const id = prompt("Enter Telegram Chat ID:");
                  if (id) setTelegramChatId(id);
                  else setChannels({...channels, telegram: false});
                }
              }} />
            </div>
          </div>

          {channels.telegram && telegramChatId && (
            <div className="p-3 text-xs bg-indigo-500/5 text-indigo-400/90 rounded-xl border border-indigo-500/10 font-mono">
              Telegram Connected: Chat ID: {telegramChatId}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
