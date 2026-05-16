"use client";

import { useWatchlist } from "@/hooks/use-watchlist";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Trash2, Star, TrendingUp } from "lucide-react";
import Link from "next/link";

export default function WatchlistPage() {
  const { items, isLoading, error, removeFromWatchlist } = useWatchlist();

  if (isLoading) {
    return (
      <div className="p-6 space-y-4">
        <Skeleton className="h-10 w-48" />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-24 w-full" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="px-4 lg:px-6 py-6 space-y-6">
      <div className="flex items-center gap-2">
        <Star className="size-6 text-yellow-500 fill-yellow-500" />
        <h1 className="text-2xl font-bold tracking-tight">Your Watchlist</h1>
      </div>

      {error && (
        <div className="bg-destructive/10 text-destructive p-4 rounded-md">
          {error}
        </div>
      )}

      {items.length === 0 ? (
        <div className="text-center py-20 border-2 border-dashed rounded-xl">
          <p className="text-muted-foreground">Your watchlist is empty.</p>
          <Button asChild className="mt-4" variant="outline">
            <Link href="/coins">Browse Coins</Link>
          </Button>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {items.map((item) => (
            <Card key={item.id} className="group hover:border-primary/50 transition-colors">
              <CardContent className="p-4 flex items-center justify-between">
                <Link href={`/coins/${item.symbol}`} className="flex items-center gap-3 flex-1">
                  <div className="bg-primary/10 p-2 rounded-lg group-hover:bg-primary/20 transition-colors">
                    <TrendingUp className="size-5 text-primary" />
                  </div>
                  <div>
                    <h3 className="font-bold uppercase">{item.symbol}</h3>
                    <p className="text-xs text-muted-foreground">Added {new Date(item.created_at).toLocaleDateString()}</p>
                  </div>
                </Link>
                <Button 
                  variant="ghost" 
                  size="icon" 
                  className="text-muted-foreground hover:text-destructive"
                  onClick={() => removeFromWatchlist(item.id)}
                >
                  <Trash2 className="size-4" />
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
