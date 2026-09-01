// frontend/src/components/layout/MobileNav.tsx

import React from "react"
import { LayoutGrid, Users, TrendingUp, FileCode2 } from "lucide-react"
import { cn } from "@/lib/utils"

export type NavTab = "dashboard" | "customers" | "analytics" | "docs"

interface MobileNavProps {
  currentTab: NavTab
  onTabChange: (tab: NavTab) => void
}

export const MobileNav: React.FC<MobileNavProps> = ({ currentTab, onTabChange }) => {
  const items = [
    {
      id: "dashboard" as const,
      label: "Operations",
      icon: LayoutGrid,
    },
    {
      id: "customers" as const,
      label: "Customers",
      icon: Users,
    },
    {
      id: "analytics" as const,
      label: "Funnel",
      icon: TrendingUp,
    },
    {
      id: "docs" as const,
      label: "API Docs",
      icon: FileCode2,
    },
  ]

  return (
    <nav
      aria-label="Mobile Navigation"
      className="fixed inset-x-0 bottom-0 z-40 flex h-16 items-center justify-around border-t border-border/80 bg-background/95 px-2 backdrop-blur-md md:hidden"
    >
      {items.map((item) => {
        const Icon = item.icon
        const isActive = currentTab === item.id

        return (
          <button
            key={item.id}
            type="button"
            onClick={() => onTabChange(item.id)}
            className={cn(
              "flex min-w-[64px] flex-col items-center justify-center gap-1 rounded-xl py-1.5 transition-all",
              isActive
                ? "font-semibold text-primary"
                : "text-muted-foreground hover:text-foreground active:scale-95"
            )}
          >
            <div
              className={cn(
                "flex size-8 items-center justify-center rounded-lg transition-colors",
                isActive
                  ? "bg-purple-500/15 text-purple-700 dark:bg-purple-500/20 dark:text-purple-300"
                  : "text-muted-foreground"
              )}
            >
              <Icon className="size-4.5" />
            </div>
            <span className="text-[10px] tracking-tight">{item.label}</span>
          </button>
        )
      })}
    </nav>
  )
}
