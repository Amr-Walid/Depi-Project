"use client";

import { ChartAreaInteractive } from "@/features/dashboard/components/chart-area-interactive";
import { DataTable } from "@/features/dashboard/components/data-table";
import { SectionCards } from "@/features/dashboard/components/selection-cards";
import { useCoins, useCoinDetail } from "@/hooks/use-coins";
import { Skeleton } from "@/components/ui/skeleton";

export default function Page() {
  const { coins, isLoading: loadingCoins } = useCoins();
  // Fetch BTC details for the dashboard chart by default
  const { history, summary, isLoading: loadingBTC } = useCoinDetail("BTC");

  return (
    <>
      <div className="px-4 lg:px-6 py-4">
        <div className="flex flex-col gap-2">
          <h1 className="text-2xl font-bold tracking-tight">Market Dashboard</h1>
          <p className="text-muted-foreground">
            Real-time cryptocurrency market overview and analytics.
          </p>
        </div>
      </div>

      <div className="@container/main px-4 lg:px-6 space-y-6">
        <SectionCards />
        
        {loadingBTC ? (
          <Skeleton className="h-[400px] w-full rounded-xl" />
        ) : (
          <ChartAreaInteractive 
            data={history} 
            symbol="BTC" 
            price={summary?.price || 0}
            change={summary?.price_change_pct || 0}
          />
        )}

        <div className="pt-4">
          <h2 className="text-xl font-semibold mb-4">Supported Assets</h2>
          <DataTable data={coins} isLoading={loadingCoins} />
        </div>
      </div>
    </>
  );
}
