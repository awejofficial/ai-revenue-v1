// frontend/src/components/layout/Sidebar.tsx

import React from "react"
import {
  LayoutGrid,
  Users,
  Filter,
  BarChart3,
  Mail,
  Settings,
  HelpCircle,
} from "lucide-react"
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip"
import { cn } from "@/lib/utils"

interface SidebarProps {
  currentTab: "dashboard" | "customers" | "analytics"
  onTabChange: (tab: "dashboard" | "customers" | "analytics") => void
}

export const Sidebar: React.FC<SidebarProps> = ({ currentTab, onTabChange }) => {
  const navItems = [
    {
      id: "dashboard" as const,
      label: "Operations Hub",
      icon: LayoutGrid,
    },
    {
      id: "customers" as const,
      label: "Customer 360°",
      icon: Users,
    },
    {
      id: "analytics" as const,
      label: "Recovery Funnel",
      icon: Filter,
    },
  ]

  const secondaryItems = [
    { label: "Performance Telemetry", icon: BarChart3, tab: "analytics" as const },
    { label: "Notification Logs", icon: Mail, tab: "dashboard" as const },
    { label: "System Settings", icon: Settings, tab: "dashboard" as const },
  ]

  return (
    <aside className="fixed inset-y-0 left-0 z-40 hidden w-16 flex-col items-center justify-between border-r border-border/70 bg-background/95 py-4 backdrop-blur-md md:flex">
      {/* Top Brand 1:1 Monogram Squircle */}
      <div className="flex flex-col items-center gap-6">
        <div className="flex size-11 items-center justify-center overflow-hidden rounded-xl border border-border/80 bg-card p-1.5 shadow-xs transition-transform hover:scale-105">
          <img
            src="/logo-icon.png"
            alt="Autonomous Revenue Recovery"
            className="h-full w-full object-contain dark:invert"
          />
        </div>

        {/* Navigation Item Icons with Tooltips */}
        <nav className="flex flex-col items-center gap-2">
          {navItems.map((item) => {
            const Icon = item.icon
            const isActive = currentTab === item.id

            return (
              <Tooltip key={item.id}>
                <TooltipTrigger
                  onClick={() => onTabChange(item.id)}
                  className={cn(
                    "flex size-11 items-center justify-center rounded-xl transition-all",
                    isActive
                      ? "bg-purple-500/10 text-purple-700 shadow-xs ring-1 ring-purple-500/20 dark:bg-purple-500/20 dark:text-purple-300"
                      : "text-muted-foreground hover:bg-muted hover:text-foreground"
                  )}
                >
                  <Icon className="size-5" />
                  <span className="sr-only">{item.label}</span>
                </TooltipTrigger>
                <TooltipContent side="right" sideOffset={12}>
                  {item.label}
                </TooltipContent>
              </Tooltip>
            )
          })}

          <div className="my-1 h-px w-8 bg-border/80" />

          {secondaryItems.map((item, i) => {
            const Icon = item.icon
            return (
              <Tooltip key={i}>
                <TooltipTrigger
                  onClick={() => onTabChange(item.tab)}
                  className="flex size-11 items-center justify-center rounded-xl text-muted-foreground/70 transition-colors hover:bg-muted hover:text-foreground"
                >
                  <Icon className="size-5" />
                  <span className="sr-only">{item.label}</span>
                </TooltipTrigger>
                <TooltipContent side="right" sideOffset={12}>
                  {item.label}
                </TooltipContent>
              </Tooltip>
            )
          })}
        </nav>
      </div>

      {/* Bottom Help & Documentation Icon */}
      <div className="flex flex-col items-center">
        <Tooltip>
          <TooltipTrigger
            onClick={() => window.open("/docs", "_blank")}
            className="flex size-10 items-center justify-center rounded-xl text-muted-foreground/70 transition-colors hover:bg-muted hover:text-foreground"
          >
            <HelpCircle className="size-5" />
            <span className="sr-only">Documentation & Help</span>
          </TooltipTrigger>
          <TooltipContent side="right" sideOffset={12}>
            API Docs & Recovery Guide
          </TooltipContent>
        </Tooltip>
      </div>
    </aside>
  )
}
