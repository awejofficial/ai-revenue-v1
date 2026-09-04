import React, { useState, useEffect, useCallback } from "react"
import { ExternalLink, Zap, LayoutGrid, CreditCard, RefreshCw, Radar, ShieldAlert, Home } from "lucide-react"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Button } from "@/components/ui/button"
import { toast } from "sonner"
import { api, API_BASE_URL } from "@/lib/api"

export type NavTab =
  | "landing"
  | "dashboard"
  | "overview"
  | "payments"
  | "exceptions"
  | "detector"
  | "showcase"
  | "customers"
  | "analytics"
  | "docs"

interface HeaderProps {
  currentTab: NavTab
  onTabChange: (tab: NavTab) => void
}

type EngineStatus = "checking" | "active" | "offline"

export const Header: React.FC<HeaderProps> = ({ currentTab, onTabChange }) => {
  const [status, setStatus] = useState<EngineStatus>("checking")
  const [isProbing, setIsProbing] = useState(false)
  const [isSyncing, setIsSyncing] = useState(false)

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

  const handleSyncPaidLinks = async () => {
    setIsSyncing(true)
    try {
      const res = await api.syncPaidLinks()
      if (res.newly_recovered > 0) {
        toast.success(`Loop Closed! Verified ${res.newly_recovered} paid link(s). ₹${res.money_recovered.toLocaleString("en-IN")} recovered!`)
      } else {
        toast.info(`Checked ${res.links_checked} link(s). All in-flight links are pending payment.`)
      }
    } catch (err: any) {
      toast.error(`Sync failed: ${err.message}`)
    } finally {
      setIsSyncing(false)
    }
  }

  const swaggerUrl = API_BASE_URL ? `${API_BASE_URL}/docs` : "/docs"

  return (
    <header className="sticky top-0 z-30 border-b border-border/70 bg-background/95 backdrop-blur-md">
      <div className="flex h-16 items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
        {/* Brand Lockup */}
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => onTabChange("landing")}
            aria-label="Go to PayBack AI Home"
            className="cursor-pointer transition-transform hover:opacity-95"
          >
            <img
              src="/logo-horizontal.png"
              alt="PayBack AI — Autonomous Revenue Recovery"
              className="h-9 sm:h-10 w-auto max-w-[190px] sm:max-w-[320px] object-contain dark:invert"
            />
          </button>
        </div>

        {/* Center Nav Tabs: Strictly 5 Pages (Image 2 & 3 Match) */}
        <div className="hidden lg:block">
          <Tabs
            value={currentTab === "overview" ? "dashboard" : currentTab}
            onValueChange={(val) => onTabChange(val as NavTab)}
          >
            <TabsList className="h-9 rounded-lg border border-border/70 bg-muted/50 p-1">
              <TabsTrigger
                value="landing"
                className="gap-1.5 rounded-md px-3 py-1 text-xs font-semibold data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-xs"
              >
                <Home className="size-3.5" />
                <span>Home</span>
              </TabsTrigger>
              <TabsTrigger
                value="dashboard"
                className="gap-1.5 rounded-md px-3 py-1 text-xs font-semibold data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-xs"
              >
                <LayoutGrid className="size-3.5" />
                <span>Overview</span>
              </TabsTrigger>
              <TabsTrigger
                value="payments"
                className="gap-1.5 rounded-md px-3 py-1 text-xs font-semibold data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-xs"
              >
                <CreditCard className="size-3.5 text-blue-500" />
                <span>Payments</span>
              </TabsTrigger>
              <TabsTrigger
                value="exceptions"
                className="gap-1.5 rounded-md px-3 py-1 text-xs font-semibold data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-xs"
              >
                <ShieldAlert className="size-3.5 text-rose-500" />
                <span>Exceptions</span>
              </TabsTrigger>
              <TabsTrigger
                value="detector"
                className="gap-1.5 rounded-md px-3 py-1 text-xs font-semibold data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-xs"
              >
                <Radar className="size-3.5 text-emerald-500" />
                <span>Live Detect</span>
              </TabsTrigger>
            </TabsList>
          </Tabs>
        </div>

        {/* Right Actions Pill & Docs */}
        <div className="flex items-center gap-2.5">
          {/* Sync Paid Links Button */}
          <Button
            size="sm"
            variant="outline"
            onClick={handleSyncPaidLinks}
            disabled={isSyncing}
            className="h-8 gap-1.5 border-emerald-500/30 bg-emerald-500/10 text-xs font-semibold text-emerald-700 hover:bg-emerald-500/20 dark:text-emerald-400"
            title="Polls Razorpay test API to verify if any pending recovery links have been paid"
          >
            <RefreshCw className={`size-3.5 ${isSyncing ? "animate-spin text-emerald-600" : "text-emerald-600 dark:text-emerald-400"}`} />
            <span className="hidden sm:inline">{isSyncing ? "Syncing..." : "Sync Paid Links"}</span>
            <span className="sm:hidden">Sync</span>
          </Button>
          {/* Real-time Dynamic Backend Engine Status */}
          {status === "active" && (
            <button
              type="button"
              onClick={probeHealth}
              disabled={isProbing}
              title="Engine is active & reachable. Click to refresh health probe."
              aria-label="Engine is active. Click to refresh health probe."
              className="flex cursor-pointer items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-xs font-medium text-emerald-600 transition-all hover:bg-emerald-500/20 dark:text-emerald-400"
            >
              <span className="relative flex size-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
                <span className="relative inline-flex size-2 rounded-full bg-emerald-500" />
              </span>
              <span className="hidden sm:inline">Engine Active · Razorpay Track 03</span>
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
              aria-label="Engine offline. Click to retry connection."
              className="flex cursor-pointer items-center gap-2 rounded-full border border-rose-500/40 bg-rose-500/15 px-3 py-1 text-xs font-medium text-rose-600 transition-all hover:bg-rose-500/25 dark:text-rose-400"
            >
              <span className="size-2 rounded-full bg-rose-500" />
              <span className="hidden sm:inline">Engine Offline · Click to Retry</span>
              <span className="sm:hidden">Offline · Retry</span>
              {isProbing && <RefreshCw className="size-2.5 animate-spin text-rose-600 dark:text-rose-400" />}
            </button>
          )}

          {/* Quick API Docs Button (Direct Swagger Open) */}
          <button
            type="button"
            onClick={() => window.open(swaggerUrl, "_blank")}
            title="Open live OpenAPI / Swagger documentation in new tab"
            aria-label="Open FastAPI Swagger documentation in a new tab"
            className="hidden items-center gap-1.5 rounded-lg px-2.5 py-1 font-mono text-xs font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground md:inline-flex cursor-pointer"
          >
            <Zap className="size-3.5 text-primary" />
            <span>API Docs</span>
          </button>

          {/* Direct link to Swagger UI */}
          <a
            href={swaggerUrl}
            target="_blank"
            rel="noopener noreferrer"
            title="Open OpenAPI / Swagger UI on backend"
            aria-label="Open OpenAPI / Swagger UI on backend in a new tab"
            className="hidden items-center p-1 text-muted-foreground hover:text-foreground md:inline-flex"
          >
            <ExternalLink className="size-3.5" />
          </a>
        </div>
      </div>
    </header>
  )
}
