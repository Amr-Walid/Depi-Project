"use client";

import { DataTable } from "@/features/dashboard/components/data-table";
import { useCoins } from "@/hooks/use-coins";
import { Skeleton } from "@/components/ui/skeleton";

export default function CoinsPage() {
  const { coins, isLoading, error } = useCoins();

  return (
    <>
      <div className="px-4 lg:px-6 py-4">
        <div className="flex flex-col gap-2">
          <h1 className="text-2xl font-bold tracking-tight">Coins Market</h1>
          <p className="text-muted-foreground">
            Browse all supported cryptocurrencies and their current status.
          </p>
        </div>
      </div>

      <div className="px-4 lg:px-6">
        {error && (
          <div className="bg-destructive/10 text-destructive p-4 rounded-md mb-6">
            {error}
          </div>
        )}
        
        <DataTable data={coins} isLoading={isLoading} />
      </div>
    </>
  );
}
