"use client";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { useMarket } from "@/hooks/use-market";
import {
  Activity,
  ArrowUpRight,
  DollarSign,
  TrendingDown,
  TrendingUp,
  Coins,
  Brain,
} from "lucide-react";

export function SectionCards() {
  const { stats, sentiment, isLoading } = useMarket();

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      notation: "compact",
      maximumFractionDigits: 2,
    }).format(value);
  };

  if (isLoading) {
    return (
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[1, 2, 3, 4].map((i) => (
          <Card key={i} className="border">
            <CardContent className="space-y-4 p-6">
              <Skeleton className="h-6 w-6 rounded-full" />
              <div className="space-y-2">
                <Skeleton className="h-4 w-24" />
                <Skeleton className="h-8 w-32" />
                <Skeleton className="h-4 w-20" />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  const metrics = [
    {
      title: "Total Market Cap",
      value: formatCurrency(stats?.total_market_cap || 0),
      change: stats?.market_cap_change_24h || 0,
      icon: DollarSign,
      footer: "last 24 hours",
    },
    {
      title: "24h Trading Volume",
      value: formatCurrency(stats?.total_volume_24h || 0),
      icon: Activity,
      footer: "Across all exchanges",
    },
    {
      title: "Active Coins",
      value: stats?.active_coins_count || 0,
      icon: Coins,
      footer: "Tracked by CryptoPulse",
    },
    {
      title: "Market Sentiment",
      value: sentiment?.sentiment_label || "Neutral",
      sentimentScore: sentiment?.sentiment_score || 50,
      icon: Brain,
      footer: sentiment?.description || "Market mood",
    },
  ];

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {metrics.map((metric, index) => (
        <Card key={index} className="border transition-all hover:shadow-md">
          <CardContent className="space-y-4 p-6">
            <div className="flex items-center justify-between">
              <metric.icon className="text-muted-foreground size-6" />
              {metric.change !== undefined && (
                <Badge
                  variant="outline"
                  className={cn(
                    metric.change >= 0
                      ? "border-green-200 bg-green-50 text-green-700 dark:border-green-800 dark:bg-green-950/20 dark:text-green-400"
                      : "border-red-200 bg-red-50 text-red-700 dark:border-red-800 dark:bg-red-950/20 dark:text-red-400",
                  )}
                >
                  {metric.change >= 0 ? (
                    <>
                      <TrendingUp className="me-1 size-3" />+{metric.change}%
                    </>
                  ) : (
                    <>
                      <TrendingDown className="me-1 size-3" />
                      {metric.change}%
                    </>
                  )}
                </Badge>
              )}
              {metric.sentimentScore !== undefined && (
                <Badge
                  variant="outline"
                  className={cn(
                    metric.value === "Bullish"
                      ? "border-green-200 bg-green-50 text-green-700"
                      : metric.value === "Bearish"
                      ? "border-red-200 bg-red-50 text-red-700"
                      : "border-yellow-200 bg-yellow-50 text-yellow-700",
                  )}
                >
                  {metric.value}
                </Badge>
              )}
            </div>

            <div className="space-y-2">
              <p className="text-muted-foreground text-sm font-medium">
                {metric.title}
              </p>
              <div className="text-2xl font-bold">{metric.value}</div>
              <div className="text-muted-foreground flex items-center gap-2 text-sm">
                <span>{metric.footer}</span>
                {metric.change !== undefined && <ArrowUpRight className="size-3" />}
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
