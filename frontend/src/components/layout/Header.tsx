// frontend/src/components/layout/Header.tsx

import React, { useState, useEffect, useCallback } from "react"
import { ExternalLink, Zap, LayoutGrid, Users, TrendingUp, FileCode2, RefreshCw } from "lucide-react"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { api, API_BASE_URL } from "@/lib/api"

export type NavTab = "dashboard" | "customers" | "analytics" | "docs"

interface HeaderProps {
  currentTab: NavTab
  onTabChange: (tab: NavTab) => void
}

type EngineStatus = "checking" | "active" | "offline"

export const Header: React.FC<HeaderProps> = ({ currentTab, onTabChange }) => {
  const [status, setStatus] = useState<EngineStatus>("checking")
  const [isProbing, setIsProbing] = useState(false)

  const probeHealth = useCallback(async () => {
    try {
      setIsProbing(true)
      const res = await api.getHealth()
      if (res && (res.status === "healthy" || res.status === "ok")) {
        setStatus("active")
      } else {
        setStatus("offline")
      }
    } catch (err) {
      console.warn("[Header] Engine health probe failed:", err)
      setStatus("offline")
    } finally {
      setIsProbing(false)
    }
  }, [])

  useEffect(() => {
    probeHealth()
    const interval = setInterval(probeHealth, 25000)
    return () => clearInterval(interval)
  }, [probeHealth])

  const swaggerUrl = API_BASE_URL ? `${API_BASE_URL}/docs` : "/docs"

  return (
    <header className="sticky top-0 z-30 border-b border-border/70 bg-background/95 backdrop-blur-md">
      <div className="flex h-16 items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
        {/* Brand Lockup: 3.5:1 Horizontal Brand Lockup */}
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => onTabChange("dashboard")}
            className="cursor-pointer transition-transform hover:opacity-95"
          >
            <img
              src="/logo-horizontal.png"
              alt="Autonomous Revenue Recovery — Intelligent Dunning & Win-Back Agent"
              className="h-9 sm:h-10 w-auto max-w-[190px] sm:max-w-[320px] object-contain dark:invert"
            />
          </button>
        </div>

        {/* Center Nav Tabs with Lucide Icons */}
        <div className="hidden sm:block">
          <Tabs
            value={currentTab}
            onValueChange={(val) => onTabChange(val as NavTab)}
          >
            <TabsList className="h-9 rounded-lg border border-border/70 bg-muted/50 p-1">
              <TabsTrigger
                value="dashboard"
                className="gap-1.5 rounded-md px-3.5 py-1 text-xs font-medium data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-xs"
              >
                <LayoutGrid data-icon="inline-start" className="size-3.5" />
                <span>Operations Hub</span>
              </TabsTrigger>
              <TabsTrigger
                value="customers"
                className="gap-1.5 rounded-md px-3.5 py-1 text-xs font-medium data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-xs"
              >
                <Users data-icon="inline-start" className="size-3.5" />
                <span>Customer 360°</span>
              </TabsTrigger>
              <TabsTrigger
                value="analytics"
                className="gap-1.5 rounded-md px-3.5 py-1 text-xs font-medium data-[state=active]:border-primary/20 data-[state=active]:bg-background data-[state=active]:text-primary data-[state=active]:shadow-xs"
              >
                <TrendingUp data-icon="inline-start" className="size-3.5" />
                <span>Recovery Funnel</span>
              </TabsTrigger>
              <TabsTrigger
                value="docs"
                className="gap-1.5 rounded-md px-3.5 py-1 text-xs font-medium data-[state=active]:border-primary/20 data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-xs"
              >
                <FileCode2 data-icon="inline-start" className="size-3.5" />
                <span>API Docs</span>
              </TabsTrigger>
            </TabsList>
          </Tabs>
        </div>

        {/* Right Status Pill & Docs */}
        <div className="flex items-center gap-3">
          {/* Real-time Dynamic Backend Engine Status */}
          {status === "active" && (
            <button
              type="button"
              onClick={probeHealth}
              disabled={isProbing}
              title="Engine is active & reachable on Render. Click to refresh health probe."
              className="flex cursor-pointer items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-xs font-medium text-emerald-600 transition-all hover:bg-emerald-500/20 dark:text-emerald-400"
            >
              <span className="relative flex size-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
                <span className="relative inline-flex size-2 rounded-full bg-emerald-500" />
              </span>
              <span className="hidden sm:inline">Engine Active · Stripe + Razorpay</span>
              <span className="sm:hidden">Active</span>
              {isProbing && <RefreshCw className="size-2.5 animate-spin text-emerald-600 dark:text-emerald-400" />}
            </button>
          )}

          {status === "checking" && (
            <div
              className="flex items-center gap-2 rounded-full border border-amber-500/30 bg-amber-500/10 px-3 py-1 text-xs font-medium text-amber-600 dark:text-amber-400"
              title="Connecting to AI Revenue Recovery Engine..."
            >
              <span className="size-2 rounded-full bg-amber-400 animate-pulse" />
              <span className="hidden sm:inline">Connecting Engine...</span>
              <span className="sm:hidden">Connecting</span>
            </div>
          )}

          {status === "offline" && (
            <button
              type="button"
              onClick={probeHealth}
              disabled={isProbing}
              title="Backend engine is offline or unreachable. Click to retry connection."
              className="flex cursor-pointer items-center gap-2 rounded-full border border-rose-500/40 bg-rose-500/15 px-3 py-1 text-xs font-medium text-rose-600 transition-all hover:bg-rose-500/25 dark:text-rose-400"
            >
              <span className="size-2 rounded-full bg-rose-500" />
              <span className="hidden sm:inline">Engine Offline · Click to Retry</span>
              <span className="sm:hidden">Offline · Retry</span>
              {isProbing && <RefreshCw className="size-2.5 animate-spin text-rose-600 dark:text-rose-400" />}
            </button>
          )}

          {/* Quick API Docs Button */}
          <button
            type="button"
            onClick={() => onTabChange("docs")}
            className={`hidden items-center gap-1.5 rounded-lg px-2.5 py-1 font-mono text-xs font-medium transition-colors md:inline-flex ${
              currentTab === "docs"
                ? "bg-primary/10 text-primary"
                : "text-muted-foreground hover:bg-muted hover:text-foreground"
            }`}
          >
            <Zap className="size-3.5 text-primary" />
            <span>API Docs</span>
          </button>

          {/* Direct link to Render Swagger */}
          <a
            href={swaggerUrl}
            target="_blank"
            rel="noopener noreferrer"
            title="Open OpenAPI / Swagger UI on Render backend"
            className="hidden items-center p-1 text-muted-foreground hover:text-foreground md:inline-flex"
          >
            <ExternalLink className="size-3.5" />
          </a>
        </div>
      </div>
    </header>
  )
}
