// frontend/src/App.tsx

import React, { useState, useEffect, Component, type ErrorInfo } from "react"
import { Header } from "@/components/layout/Header"
import { Sidebar } from "@/components/layout/Sidebar"
import { MobileNav } from "@/components/layout/MobileNav"
import { DashboardView } from "@/components/dashboard/DashboardView"
import { CustomersView } from "@/components/customers/CustomersView"
import { AnalyticsView } from "@/components/analytics/AnalyticsView"
import { ThemeProvider } from "@/components/theme-provider"
import { Toaster } from "@/components/ui/sonner"
import { TooltipProvider } from "@/components/ui/tooltip"
import { AlertCircle, RefreshCw } from "lucide-react"
import { Button } from "@/components/ui/button"

type ViewTab = "dashboard" | "customers" | "analytics"

interface ErrorBoundaryProps {
  children: React.ReactNode
}

interface ErrorBoundaryState {
  hasError: boolean
  error: Error | null
}

class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("Uncaught application error:", error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-screen flex-col items-center justify-center bg-background p-6 text-center text-foreground">
          <div className="flex size-14 items-center justify-center rounded-2xl border border-destructive/30 bg-destructive/10 text-destructive shadow-sm">
            <AlertCircle className="size-7" />
          </div>
          <h2 className="mt-4 text-xl font-bold">Something went wrong</h2>
          <p className="mt-1.5 max-w-md text-xs text-muted-foreground">
            {this.state.error?.message || "An unexpected error occurred while rendering the interface."}
          </p>
          <Button
            variant="outline"
            size="sm"
            onClick={() => window.location.reload()}
            className="mt-5 gap-1.5"
          >
            <RefreshCw className="size-3.5" /> Reload Application
          </Button>
        </div>
      )
    }

    return this.props.children
  }
}

export function App() {
  const [currentTab, setCurrentTab] = useState<ViewTab>(() => {
    const path = window.location.pathname.toLowerCase()
    if (path.includes("customer")) return "customers"
    if (path.includes("analytic")) return "analytics"
    return "dashboard"
  })

  const [dashboardFilter, setDashboardFilter] = useState<string>("")

  // Synchronize browser history / navigation
  const handleTabChange = (tab: ViewTab) => {
    setCurrentTab(tab)
    const targetPath = tab === "dashboard" ? "/dashboard" : `/${tab}`
    window.history.pushState(null, "", targetPath)
  }

  const handleNavigateWithFilter = (filterQuery: string) => {
    setDashboardFilter(filterQuery)
    handleTabChange("dashboard")
  }

  useEffect(() => {
    const handlePopState = () => {
      const path = window.location.pathname.toLowerCase()
      if (path.includes("customer")) setCurrentTab("customers")
      else if (path.includes("analytic")) setCurrentTab("analytics")
      else setCurrentTab("dashboard")
    }

    window.addEventListener("popstate", handlePopState)
    return () => window.removeEventListener("popstate", handlePopState)
  }, [])

  return (
    <ThemeProvider defaultTheme="system" storageKey="vite-ui-theme">
      <TooltipProvider>
        <ErrorBoundary>
          <div className="min-h-screen bg-background text-foreground antialiased">
            {/* Left Vertical Navigation Rail (Desktop & Tablet) */}
            <Sidebar currentTab={currentTab} onTabChange={handleTabChange} />

            {/* Content Wrapper */}
            <div className="flex min-h-screen flex-col md:pl-16">
              {/* Top Header with live status and view tabs */}
              <Header currentTab={currentTab} onTabChange={handleTabChange} />

              {/* Main Content Area */}
              <main className="mx-auto w-full max-w-7xl px-4 pt-4 pb-24 sm:px-6 sm:py-8 lg:px-8">
                {currentTab === "dashboard" && (
                  <DashboardView
                    onNavigateToAnalytics={() => handleTabChange("analytics")}
                    initialSearch={dashboardFilter}
                  />
                )}
                {currentTab === "customers" && <CustomersView />}
                {currentTab === "analytics" && (
                  <AnalyticsView
                    onNavigateToDashboardWithFilter={handleNavigateWithFilter}
                  />
                )}
              </main>
            </div>

            {/* Mobile Bottom Navigation Bar (Phone viewports < 768px) */}
            <MobileNav currentTab={currentTab} onTabChange={handleTabChange} />

            {/* Sonner Toaster Notifications */}
            <Toaster position="bottom-right" richColors closeButton />
          </div>
        </ErrorBoundary>
      </TooltipProvider>
    </ThemeProvider>
  )
}

export default App
