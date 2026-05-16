"use client";

import { useAlerts } from "@/hooks/use-alerts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Switch } from "@/components/ui/switch";
import { Bell, Plus, Trash2, ArrowUp, ArrowDown } from "lucide-react";
import { useState } from "react";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

export default function AlertsPage() {
  const { alerts, isLoading, error, createAlert, toggleAlert, deleteAlert } = useAlerts();
  const [newAlert, setNewAlert] = useState({ symbol: "", condition: "above", threshold: 0 });

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newAlert.symbol) return;
    try {
      await createAlert(newAlert);
      setNewAlert({ symbol: "", condition: "above", threshold: 0 });
    } catch (err) {
      alert("Failed to create alert");
    }
  };

  if (isLoading) {
    return (
      <div className="p-6 space-y-6">
        <Skeleton className="h-10 w-48" />
        <Skeleton className="h-40 w-full" />
        <div className="space-y-4">
          {[1, 2].map((i) => (
            <Skeleton key={i} className="h-20 w-full" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="px-4 lg:px-6 py-6 space-y-8">
      <div className="flex items-center gap-2">
        <Bell className="size-6 text-primary" />
        <h1 className="text-2xl font-bold tracking-tight">Price Alerts</h1>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Set New Alert</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleCreate} className="grid gap-4 md:grid-cols-4 items-end">
            <div className="space-y-2">
              <label className="text-sm font-medium">Symbol</label>
              <Input 
                placeholder="BTC" 
                value={newAlert.symbol} 
                onChange={e => setNewAlert({...newAlert, symbol: e.target.value.toUpperCase()})}
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Condition</label>
              <Select 
                value={newAlert.condition} 
                onValueChange={v => setNewAlert({...newAlert, condition: v})}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Condition" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="above">Price Above</SelectItem>
                  <SelectItem value="below">Price Below</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Target Price ($)</label>
              <Input 
                type="number" 
                step="any"
                value={newAlert.threshold} 
                onChange={e => {
                  const val = parseFloat(e.target.value);
                  setNewAlert({...newAlert, threshold: isNaN(val) ? 0 : val});
                }}
              />
            </div>
            <Button type="submit">
              <Plus className="size-4 mr-2" /> Set Alert
            </Button>
          </form>
        </CardContent>
      </Card>

      <div className="space-y-4">
        <h2 className="text-xl font-semibold">Active Alerts</h2>
        {error && <div className="text-destructive">{error}</div>}
        
        {alerts.length === 0 ? (
          <div className="text-center py-10 text-muted-foreground border rounded-xl border-dashed">
            No alerts set yet.
          </div>
        ) : (
          <div className="grid gap-4">
            {alerts.map((alert) => (
              <Card key={alert.id} className={alert.is_active ? "border-primary/20" : "opacity-60"}>
                <CardContent className="p-4 flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="bg-primary/10 p-2 rounded-full">
                      {alert.condition === "above" ? 
                        <ArrowUp className="size-5 text-green-500" /> : 
                        <ArrowDown className="size-5 text-red-500" />
                      }
                    </div>
                    <div>
                      <h3 className="font-bold text-lg uppercase">{alert.symbol}</h3>
                      <p className="text-sm text-muted-foreground">
                        Notify when price goes {alert.condition} ${alert.threshold}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <Switch 
                      checked={alert.is_active} 
                      onCheckedChange={(checked) => toggleAlert(alert.id, checked)}
                    />
                    <Button 
                      variant="ghost" 
                      size="icon" 
                      className="text-muted-foreground hover:text-destructive"
                      onClick={() => deleteAlert(alert.id)}
                    >
                      <Trash2 className="size-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
