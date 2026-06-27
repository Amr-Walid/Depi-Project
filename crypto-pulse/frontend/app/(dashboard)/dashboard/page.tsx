"use client";

import { ChartAreaInteractive } from "@/features/dashboard/components/chart-area-interactive";
import { SectionCards } from "@/features/dashboard/components/selection-cards";
import { useCoins, useCoinDetail } from "@/hooks/use-coins";
import { useState } from "react";

export default function Page() {
  const { coins } = useCoins();
  const [selectedSymbol, setSelectedSymbol] = useState("BTCUSDT");
  const [selectedDays, setSelectedDays] = useState(30);
  
  const { history, summary, isLoading: loadingDetail } = useCoinDetail(selectedSymbol, selectedDays);

  // Handle conversion of symbol name (e.g., BTC to BTCUSDT)
  const handleSymbolChange = (symbol: string) => {
    if (!symbol.endsWith("USDT")) {
      setSelectedSymbol(`${symbol}USDT`);
    } else {
      setSelectedSymbol(symbol);
    }
  };

  const activeSymbolShort = selectedSymbol.replace("USDT", "");

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
        
        <ChartAreaInteractive 
          data={history} 
          coins={coins}
          symbol={activeSymbolShort} 
          days={selectedDays}
          price={summary?.price || summary?.day_close || 0}
          change={summary?.price_change_pct || 0}
          high={summary?.day_high || 0}
          low={summary?.day_low || 0}
          volume={summary?.total_volume || 0}
          avgPrice={summary?.avg_price || 0}
          isLoading={loadingDetail}
          onSymbolChange={handleSymbolChange}
          onDaysChange={setSelectedDays}
        />
      </div>
    </>
  );
}
