// frontend/src/App.tsx

import { useState, useEffect } from "react"
import { Header } from "@/components/layout/Header"
import { Sidebar } from "@/components/layout/Sidebar"
import { MobileNav } from "@/components/layout/MobileNav"
import { DashboardView } from "@/components/dashboard/DashboardView"
import { CustomersView } from "@/components/customers/CustomersView"
import { AnalyticsView } from "@/components/analytics/AnalyticsView"
import { Toaster } from "@/components/ui/sonner"
import { TooltipProvider } from "@/components/ui/tooltip"

type ViewTab = "dashboard" | "customers" | "analytics"

export function App() {
  const [currentTab, setCurrentTab] = useState<ViewTab>(() => {
    const path = window.location.pathname.toLowerCase()
    if (path.includes("customer")) return "customers"
    if (path.includes("analytic")) return "analytics"
    return "dashboard"
  })

  // Synchronize browser history / navigation
  const handleTabChange = (tab: ViewTab) => {
    setCurrentTab(tab)
    const targetPath = tab === "dashboard" ? "/dashboard" : `/${tab}`
    window.history.pushState(null, "", targetPath)
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
    <TooltipProvider>
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
              <DashboardView onNavigateToAnalytics={() => handleTabChange("analytics")} />
            )}
            {currentTab === "customers" && <CustomersView />}
            {currentTab === "analytics" && <AnalyticsView />}
          </main>
        </div>

        {/* Mobile Bottom Navigation Bar (Phone viewports < 768px) */}
        <MobileNav currentTab={currentTab} onTabChange={handleTabChange} />

        {/* Sonner Toaster Notifications */}
        <Toaster position="bottom-right" richColors closeButton />
      </div>
    </TooltipProvider>
  )
}

export default App
