"use client";

import {
  IconBell,
  IconBrain,
  IconChartBar,
  IconLayoutDashboard,
  IconSettings,
  IconStar,
  IconWallet,
} from "@tabler/icons-react";
import { Search } from "lucide-react";
import Link from "next/link";
import * as React from "react";

import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";

interface SearchItem {
  title: string;
  url: string;
  group: string;
  icon: React.ComponentType<{ className?: string }>;
}

const searchItems: SearchItem[] = [
  {
    title: "Dashboard",
    url: "/dashboard",
    group: "Market",
    icon: IconLayoutDashboard,
  },
  {
    title: "Coins",
    url: "/coins",
    group: "Market",
    icon: IconChartBar,
  },
  {
    title: "Watchlist",
    url: "/watchlist",
    group: "Personal",
    icon: IconStar,
  },
  {
    title: "Portfolio",
    url: "/portfolio",
    group: "Personal",
    icon: IconWallet,
  },
  {
    title: "Alerts",
    url: "/alerts",
    group: "Personal",
    icon: IconBell,
  },
  {
    title: "AI Assistant",
    url: "/ai-chat",
    group: "Intelligence",
    icon: IconBrain,
  },
  {
    title: "Settings",
    url: "/settings",
    group: "Configuration",
    icon: IconSettings,
  },
];

export function CommandSearch({ open, onOpenChange }: { open: boolean; onOpenChange: (open: boolean) => void }) {
  const groupedItems = React.useMemo(() => {
    return searchItems.reduce(
      (acc, item) => {
        if (!acc[item.group]) {
          acc[item.group] = [];
        }
        acc[item.group].push(item);
        return acc;
      },
      {} as Record<string, SearchItem[]>,
    );
  }, []);

  return (
    <CommandDialog open={open} onOpenChange={onOpenChange}>
      <CommandInput placeholder="Search pages..." />
      <CommandList>
        <CommandEmpty>No results found.</CommandEmpty>
        {Object.entries(groupedItems).map(([group, items]) => (
          <CommandGroup key={group} heading={group}>
            {items.map((item) => {
              const Icon = item.icon;
              return (
                <CommandItem key={item.url} asChild>
                  <Link href={item.url} onClick={() => onOpenChange(false)}>
                    <Icon className="mr-2 size-4 text-muted-foreground" />
                    {item.title}
                  </Link>
                </CommandItem>
              );
            })}
          </CommandGroup>
        ))}
      </CommandList>
    </CommandDialog>
  );
}

export function SearchTrigger({ onClick }: { onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="inline-flex items-center gap-2 rounded-md text-sm font-medium border border-input bg-background shadow-sm hover:bg-accent hover:text-accent-foreground h-8 px-3 relative justify-start text-muted-foreground sm:pr-12 md:w-36 lg:w-56"
    >
      <Search className="size-4" />
      <span className="hidden lg:inline-flex">Search...</span>
      <span className="inline-flex lg:hidden">Search...</span>
      <kbd className="pointer-events-none absolute right-1.5 top-1/2 -translate-y-1/2 hidden h-5 select-none items-center gap-1 rounded border bg-muted px-1.5 font-mono text-[10px] font-medium sm:flex">
        <span className="text-xs">⌘</span>K
      </kbd>
    </button>
  );
}
