"use client";

import { useParams } from "next/navigation";
import { useCoinDetail } from "@/hooks/use-coins";
import { ChartAreaInteractive } from "@/features/dashboard/components/chart-area-interactive";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";

export default function CoinDetailPage() {
  const params = useParams();
  const symbol = params.symbol as string;
  const { summary, history, isLoading, error } = useCoinDetail(symbol);

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
    }).format(value);
  };

  if (isLoading) {
    return (
      <div className="p-6 space-y-6">
        <Skeleton className="h-10 w-48" />
        <Skeleton className="h-[400px] w-full" />
        <div className="grid gap-4 md:grid-cols-3">
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
        </div>
      </div>
    );
  }

  if (error || !summary) {
    return (
      <div className="p-6">
        <div className="bg-destructive/10 text-destructive p-4 rounded-md">
          {error || "Coin not found"}
        </div>
      </div>
    );
  }

  return (
    <div className="px-4 lg:px-6 py-6 space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h1 className="text-3xl font-bold uppercase">{summary.symbol}</h1>
          <Badge variant="outline" className="text-lg py-1">
            {formatCurrency(summary.price)}
          </Badge>
          <span className={summary.price_change_pct >= 0 ? "text-green-500 font-bold" : "text-red-500 font-bold"}>
            {summary.price_change_pct >= 0 ? "+" : ""}{summary.price_change_pct.toFixed(2)}%
          </span>
        </div>
      </div>

      <ChartAreaInteractive 
        data={history} 
        symbol={summary.symbol} 
        price={summary.price}
        change={summary.price_change_pct}
      />

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">24h High</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-500">{formatCurrency(summary.high)}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">24h Low</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-500">{formatCurrency(summary.low)}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Open Price</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(summary.open)}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">24h Volume</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary.volume.toLocaleString()}</div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
