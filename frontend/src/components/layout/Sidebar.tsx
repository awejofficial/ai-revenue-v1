import React, { useState } from "react"
import {
  LayoutGrid,
  CreditCard,
  BarChart3,
  Mail,
  Settings,
  HelpCircle,
  Sun,
  Moon,
  Radar,
  ShieldAlert,
  Home,
} from "lucide-react"
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip"
import { SettingsDialog } from "@/components/layout/SettingsDialog"
import { useTheme } from "@/components/theme-provider"
import { cn } from "@/lib/utils"
import type { NavTab } from "@/components/layout/Header"

export type { NavTab }

interface SidebarProps {
  currentTab: NavTab
  onTabChange: (tab: NavTab) => void
}

export const Sidebar: React.FC<SidebarProps> = ({ currentTab, onTabChange }) => {
  const [settingsOpen, setSettingsOpen] = useState(false)
  const { theme, toggleTheme } = useTheme()

  const navItems = [
    {
      id: "landing" as const,
      label: "Home",
      icon: Home,
    },
    {
      id: "dashboard" as const,
      label: "Overview",
      icon: LayoutGrid,
    },
    {
      id: "payments" as const,
      label: "Payments",
      icon: CreditCard,
    },
    {
      id: "exceptions" as const,
      label: "Exceptions",
      icon: ShieldAlert,
    },
    {
      id: "detector" as const,
      label: "Live Detect",
      icon: Radar,
    },
  ]

  const secondaryItems = [
    {
      label: "Performance Telemetry",
      icon: BarChart3,
      action: () => onTabChange("analytics"),
    },
    {
      label: "Notification Logs",
      icon: Mail,
      action: () => onTabChange("exceptions"),
    },
    {
      label: "System Settings",
      icon: Settings,
      action: () => setSettingsOpen(true),
    },
  ]

  return (
    <>
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
                      "flex size-11 items-center justify-center rounded-xl transition-all cursor-pointer",
                      isActive
                        ? "bg-primary/10 text-primary shadow-xs ring-1 ring-primary/25 dark:bg-primary/20 dark:text-primary"
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
                    onClick={item.action}
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

        {/* Bottom Theme Switcher & Documentation Icons */}
        <div className="flex flex-col items-center gap-2">
          {/* Quick Theme Toggle Button */}
          <Tooltip>
            <TooltipTrigger
              onClick={toggleTheme}
              className="flex size-10 items-center justify-center rounded-xl text-muted-foreground/70 transition-colors hover:bg-muted hover:text-foreground"
            >
              {theme === "dark" ? (
                <Sun className="size-5 text-amber-400" />
              ) : (
                <Moon className="size-5 text-indigo-400" />
              )}
              <span className="sr-only">Toggle Theme</span>
            </TooltipTrigger>
            <TooltipContent side="right" sideOffset={12}>
              Toggle Theme ({theme === "dark" ? "Light Mode" : "Dark Mode"})
            </TooltipContent>
          </Tooltip>

          {/* Documentation Link */}
          <Tooltip>
            <TooltipTrigger
              onClick={() => window.open("http://127.0.0.1:8000/docs", "_blank")}
              className="flex size-10 items-center justify-center rounded-xl text-muted-foreground/70 transition-colors hover:bg-muted hover:text-foreground cursor-pointer"
            >
              <HelpCircle className="size-5" />
              <span className="sr-only">Documentation & Help</span>
            </TooltipTrigger>
            <TooltipContent side="right" sideOffset={12}>
              FastAPI Swagger Docs & Telemetry
            </TooltipContent>
          </Tooltip>
        </div>
      </aside>

      {/* Settings Modal */}
      <SettingsDialog
        open={settingsOpen}
        onOpenChange={setSettingsOpen}
      />
    </>
  )
}
