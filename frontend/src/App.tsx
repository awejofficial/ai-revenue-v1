// frontend/src/App.tsx

import React, { useState, useEffect, Component, type ErrorInfo } from "react"
import { Header, type NavTab } from "@/components/layout/Header"
import { Sidebar } from "@/components/layout/Sidebar"
import { MobileNav } from "@/components/layout/MobileNav"
import { LandingPageView } from "@/components/landing/LandingPageView"
import { OverviewView } from "@/components/dashboard/OverviewView"
import { PaymentsView } from "@/components/payments/PaymentsView"
import { LiveDetectorView } from "@/components/detector/LiveDetectorView"
import { ExceptionsView } from "@/components/exceptions/ExceptionsView"
import { AuditModal } from "@/components/dashboard/AuditModal"
import { ThemeProvider } from "@/components/theme-provider"
import { Toaster } from "@/components/ui/sonner"
import { TooltipProvider } from "@/components/ui/tooltip"
import { AlertCircle, RefreshCw } from "lucide-react"
import { Button } from "@/components/ui/button"

type ViewTab = NavTab

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
    if (path.includes("dashboard") || path.includes("overview") || path.includes("ops") || path.includes("analytics")) return "dashboard"
    if (path.includes("payment")) return "payments"
    if (path.includes("detector") || path.includes("radar")) return "detector"
    if (path.includes("exception")) return "exceptions"
    return "landing"
  })

  // Global Audit Trail & Recovery Modal state
  const [auditModalOpen, setAuditModalOpen] = useState(false)
  const [auditPayment, setAuditPayment] = useState<any>(null)

  const handleOpenAudit = (payment: any) => {
    setAuditPayment(payment)
    setAuditModalOpen(true)
  }

  // Synchronize browser history / navigation
  const handleTabChange = (tab: ViewTab) => {
    // If tab is analytics, map smoothly to dashboard
    const resolvedTab = tab === "analytics" ? "dashboard" : tab
    setCurrentTab(resolvedTab)
    const targetPath = resolvedTab === "landing" ? "/" : `/${resolvedTab}`
    window.history.pushState(null, "", targetPath)
  }

  useEffect(() => {
    const handlePopState = () => {
      const path = window.location.pathname.toLowerCase()
      if (path === "/" || path === "" || path.includes("home") || path.includes("landing")) setCurrentTab("landing")
      else if (path.includes("dashboard") || path.includes("overview") || path.includes("ops") || path.includes("analytics")) setCurrentTab("dashboard")
      else if (path.includes("payment")) setCurrentTab("payments")
      else if (path.includes("detector") || path.includes("radar")) setCurrentTab("detector")
      else if (path.includes("exception")) setCurrentTab("exceptions")
      else setCurrentTab("landing")
    }

    window.addEventListener("popstate", handlePopState)
    return () => window.removeEventListener("popstate", handlePopState)
  }, [])

  return (
    <ThemeProvider defaultTheme="system" storageKey="vite-ui-theme">
      <TooltipProvider>
        <ErrorBoundary>
          <div className="min-h-screen bg-background text-foreground antialiased">
            {currentTab === "landing" ? (
              /* Standalone Marketing Landing Page with its own dedicated navbar */
              <LandingPageView
                onNavigate={handleTabChange}
                onOpenAudit={(id) =>
                  handleOpenAudit({
                    payment_id: id || "pay_2694WD",
                    case_id: 105,
                    amount: 4499,
                    status: "RESOLVED",
                    root_cause: "INSUFFICIENT_FUNDS",
                  })
                }
              />
            ) : (
              /* Internal SaaS Console: Strictly 4 Operations Pages with Sidebar & Header */
              <>
                {/* Left Vertical Navigation Rail (Desktop & Tablet) */}
                <Sidebar currentTab={currentTab} onTabChange={handleTabChange} />

                {/* Content Wrapper */}
                <div className="flex min-h-screen flex-col md:pl-16">
                  {/* Top Header with live status and view tabs */}
                  <Header currentTab={currentTab} onTabChange={handleTabChange} />

                  {/* Main Content Area */}
                  <main className="mx-auto w-full max-w-7xl px-4 pt-4 pb-24 sm:px-6 sm:py-8 lg:px-8">
                    {(currentTab === "dashboard" || currentTab === "overview" || currentTab === "analytics") && (
                      <OverviewView
                        onNavigateToPayments={() => handleTabChange("payments")}
                        onOpenAuditModal={(id) =>
                          handleOpenAudit({
                            payment_id: id || "pay_c1dc092568_4226",
                            case_id: 102,
                            amount: 103609.7,
                            status: "ESCALATED",
                            root_cause: "OVERDUE_INVOICE",
                          })
                        }
                      />
                    )}
                    {currentTab === "payments" && (
                      <PaymentsView onOpenAuditModal={handleOpenAudit} />
                    )}
                    {currentTab === "exceptions" && (
                      <ExceptionsView onOpenAuditModal={handleOpenAudit} />
                    )}
                    {currentTab === "detector" && <LiveDetectorView />}
                  </main>
                </div>

                {/* Mobile Bottom Navigation Bar (Phone viewports < 768px) */}
                <MobileNav currentTab={currentTab} onTabChange={handleTabChange} />
              </>
            )}

            {/* Global Audit Trail & Recovery Modal (Image 4 Match) */}
            <AuditModal
              isOpen={auditModalOpen}
              onClose={() => setAuditModalOpen(false)}
              payment={auditPayment}
            />

            {/* Sonner Toaster Notifications */}
            <Toaster position="bottom-right" richColors closeButton />
          </div>
        </ErrorBoundary>
      </TooltipProvider>
    </ThemeProvider>
  )
}

export default App
