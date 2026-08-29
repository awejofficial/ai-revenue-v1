// frontend/src/components/layout/Header.tsx

import React from "react"
import { ExternalLink, Zap, LayoutGrid, Users, TrendingUp } from "lucide-react"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"

interface HeaderProps {
  currentTab: "dashboard" | "customers" | "analytics"
  onTabChange: (tab: "dashboard" | "customers" | "analytics") => void
}

export const Header: React.FC<HeaderProps> = ({ currentTab, onTabChange }) => {
  return (
    <header className="sticky top-0 z-30 border-b border-border/70 bg-background/95 backdrop-blur-md">
      <div className="flex h-16 items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
        {/* Brand Lockup: 3.5:1 Horizontal Brand Lockup */}
        <div className="flex items-center gap-3">
          <img
            src="/logo-horizontal.png"
            alt="Autonomous Revenue Recovery — Intelligent Dunning & Win-Back Agent"
            className="h-9 sm:h-10 w-auto max-w-[190px] sm:max-w-[320px] object-contain transition-transform hover:opacity-95 dark:invert"
          />
        </div>

        {/* Center Nav Tabs with Lucide Icons */}
        <div className="hidden sm:block">
          <Tabs
            value={currentTab}
            onValueChange={(val) => onTabChange(val as "dashboard" | "customers" | "analytics")}
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
            </TabsList>
          </Tabs>
        </div>

        {/* Right Status Pill & Docs */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1 text-xs font-medium text-emerald-600 dark:text-emerald-400">
            <span className="size-2 rounded-full bg-emerald-500" />
            <span className="hidden sm:inline">Engine Active · Stripe + Razorpay</span>
            <span className="sm:hidden">Active</span>
          </div>

          <a
            href="/docs"
            target="_blank"
            rel="noopener noreferrer"
            className="hidden items-center gap-1.5 font-mono text-xs font-medium text-muted-foreground transition-colors hover:text-foreground md:inline-flex"
          >
            <Zap className="size-3.5 text-primary" />
            <span>API Docs</span>
            <ExternalLink className="size-3 text-muted-foreground" />
          </a>
        </div>
      </div>
    </header>
  )
}
