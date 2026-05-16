import type { SidebarData } from "@/lib/types";
import {
  IconBrain,
  IconChartBar,
  IconLayoutDashboard,
  IconSettings,
  IconStar,
  IconWallet,
  IconBell,
} from "@tabler/icons-react";
import { Command } from "lucide-react";

export const sidebarData: SidebarData = {
  teams: [
    {
      name: "CryptoPulse",
      logo: Command,
      plan: "Pro Analytics",
    },
  ],
  navGroups: [
    {
      title: "Market",
      items: [
        {
          title: "Dashboard",
          url: "/dashboard",
          icon: IconLayoutDashboard,
        },
        {
          title: "Coins",
          url: "/coins",
          icon: IconChartBar,
        },
      ],
    },
    {
      title: "Personal",
      items: [
        {
          title: "Watchlist",
          url: "/watchlist",
          icon: IconStar,
        },
        {
          title: "Portfolio",
          url: "/portfolio",
          icon: IconWallet,
        },
        {
          title: "Alerts",
          url: "/alerts",
          icon: IconBell,
        },
      ],
    },
    {
      title: "Intelligence",
      items: [
        {
          title: "AI Assistant",
          url: "/ai-chat",
          icon: IconBrain,
          badge: "New",
          badgeColor: "green",
        },
      ],
    },
    {
      title: "Configuration",
      items: [
        {
          title: "Settings",
          url: "/settings",
          icon: IconSettings,
        },
      ],
    },
  ],
};
