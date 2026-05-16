"use client";

import { usePortfolio } from "@/hooks/use-portfolio";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Wallet, Plus, Trash2, TrendingUp } from "lucide-react";
import { useState } from "react";

export default function PortfolioPage() {
  const { positions, isLoading, error, addPosition, deletePosition } = usePortfolio();
  const [newPosition, setNewPosition] = useState({ symbol: "", quantity: 0, avg_buy_price: 0 });

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newPosition.symbol) return;
    try {
      await addPosition(newPosition);
      setNewPosition({ symbol: "", quantity: 0, avg_buy_price: 0 });
    } catch (err) {
      alert("Failed to add position");
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
        <Wallet className="size-6 text-primary" />
        <h1 className="text-2xl font-bold tracking-tight">Investment Portfolio</h1>
      </div>

      <Card className="border-primary/20 bg-primary/5">
        <CardHeader>
          <CardTitle className="text-lg">Add New Position</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleAdd} className="grid gap-4 md:grid-cols-4 items-end">
            <div className="space-y-2">
              <label className="text-sm font-medium">Symbol (e.g. BTC)</label>
              <Input 
                placeholder="BTC" 
                value={newPosition.symbol} 
                onChange={e => setNewPosition({...newPosition, symbol: e.target.value.toUpperCase()})}
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Quantity</label>
              <Input 
                type="number" 
                step="any"
                value={newPosition.quantity} 
                onChange={e => {
                  const val = parseFloat(e.target.value);
                  setNewPosition({...newPosition, quantity: isNaN(val) ? 0 : val});
                }}
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Avg. Buy Price</label>
              <Input 
                type="number" 
                step="any"
                value={newPosition.avg_buy_price} 
                onChange={e => {
                  const val = parseFloat(e.target.value);
                  setNewPosition({...newPosition, avg_buy_price: isNaN(val) ? 0 : val});
                }}
              />
            </div>
            <Button type="submit">
              <Plus className="size-4 mr-2" /> Add Position
            </Button>
          </form>
        </CardContent>
      </Card>

      <div className="space-y-4">
        <h2 className="text-xl font-semibold">Your Holdings</h2>
        {error && <div className="text-destructive">{error}</div>}
        
        {positions.length === 0 ? (
          <div className="text-center py-10 text-muted-foreground border rounded-xl border-dashed">
            No positions added yet.
          </div>
        ) : (
          <div className="grid gap-4">
            {positions.map((pos) => (
              <Card key={pos.id} className="hover:border-primary/30 transition-colors">
                <CardContent className="p-4 flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="bg-primary/10 p-2 rounded-full">
                      <TrendingUp className="size-5 text-primary" />
                    </div>
                    <div>
                      <h3 className="font-bold text-lg uppercase">{pos.symbol}</h3>
                      <p className="text-sm text-muted-foreground">
                        {pos.quantity} units @ ${pos.avg_buy_price}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-6">
                    <div className="text-right hidden sm:block">
                      <p className="text-sm text-muted-foreground font-medium">Total Cost</p>
                      <p className="font-bold">${(pos.quantity * pos.avg_buy_price).toLocaleString()}</p>
                    </div>
                    <Button 
                      variant="ghost" 
                      size="icon" 
                      className="text-muted-foreground hover:text-destructive"
                      onClick={() => deletePosition(pos.id)}
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
