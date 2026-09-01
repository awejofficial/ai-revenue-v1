// frontend/src/components/dashboard/DashboardView.tsx

import React, { useState, useEffect, useCallback } from "react"
import {
  RefreshCw,
  Play,
  TrendingUp,
  AlertCircle,
  CheckCircle2,
  Clock,
  Users,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Spinner } from "@/components/ui/spinner"
import { MetricCard } from "@/components/layout/MetricCard"
import { SimulationToolbar } from "@/components/dashboard/SimulationToolbar"
import { CasesLedger } from "@/components/dashboard/CasesLedger"
import { AuditDrawer } from "@/components/dashboard/AuditDrawer"
import { RecentLogsCard } from "@/components/dashboard/RecentLogsCard"
import { api } from "@/lib/api"
import { formatMoney, formatPercent } from "@/lib/utils"
import { toast } from "sonner"
import type { DashboardStats, Case, SimulationScenario } from "@/types/api"

interface DashboardViewProps {
  onNavigateToAnalytics?: () => void
  initialSearch?: string
}

export const DashboardView: React.FC<DashboardViewProps> = ({
  initialSearch = "",
}) => {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [cases, setCases] = useState<Case[]>([])
  const [selectedCaseId, setSelectedCaseId] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [runningWorker, setRunningWorker] = useState(false)
  const [activeSimulation, setActiveSimulation] = useState<string | null>(null)

  const loadData = useCallback(async (isSilent = false) => {
    try {
      if (!isSilent) setRefreshing(true)
      const [statsData, casesData] = await Promise.all([
        api.getDashboardStats(),
        api.getDashboardCases(30),
      ])
      setStats(statsData)
      setCases(casesData)

      // Auto-select first case if none selected
      setSelectedCaseId((prev) => {
        if (prev && casesData.some((c) => c.case_id === prev)) return prev
        return casesData.length > 0 ? casesData[0].case_id : null
      })
    } catch (err) {
      console.error("Failed to load dashboard data:", err)
      toast.error("Failed to fetch dashboard telemetry")
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [])

  useEffect(() => {
    loadData()
    const interval = setInterval(() => loadData(true), 15000)
    return () => clearInterval(interval)
  }, [loadData])

  const handleSimulate = async (scenario: SimulationScenario) => {
    try {
      setActiveSimulation(scenario)
      toast.loading(`Simulating: ${scenario.replace(/_/g, " ")}...`, { id: "sim" })
      const res = await api.simulateScenario(scenario)
      toast.success(
        res.status === "simulated_success"
          ? "Payment auto-resolution simulated successfully!"
          : `Scenario executed: ${scenario}`,
        { id: "sim" }
      )
      await loadData(true)
    } catch (err) {
      toast.error(`Simulation failed: ${err instanceof Error ? err.message : "Unknown error"}`, {
        id: "sim",
      })
    } finally {
      setActiveSimulation(null)
    }
  }

  const handleRunWorker = async () => {
    try {
      setRunningWorker(true)
      toast.loading("Running autonomous background cycle...", { id: "worker" })
      await api.triggerManualProcess()
      toast.success("Autonomous processing cycle completed", { id: "worker" })
      await loadData(true)
    } catch (err) {
      console.error("Background worker error:", err)
      toast.error("Background worker failed to execute", { id: "worker" })
    } finally {
      setRunningWorker(false)
    }
  }

  const handleResolveCase = async (caseId: number) => {
    try {
      toast.loading(`Resolving Case #${caseId}...`, { id: "resolve" })
      await api.resolveCaseManually(caseId)
      toast.success(`Case #${caseId} successfully marked as resolved!`, { id: "resolve" })
      await loadData(true)
    } catch (err) {
      console.error("Resolve case error:", err)
      toast.error("Failed to manually resolve case", { id: "resolve" })
    }
  }

  const selectedCase = cases.find((c) => c.case_id === selectedCaseId) || null

  const totalExposure = (stats?.at_risk || 0) + (stats?.recovered || 0)
  const recoveredPct =
    totalExposure > 0 ? ((stats?.recovered || 0) / totalExposure) * 100 : 0

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-foreground sm:text-2xl">
            Operations Hub
          </h2>
          <p className="text-xs text-muted-foreground sm:text-sm">
            Monitor active payment recovery cases, track won-back revenue, and test automated dunning.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            variant="outline"
            size="sm"
            disabled={refreshing}
            onClick={() => loadData(false)}
            className="h-8.5 gap-1.5 rounded-lg border-border/80 text-xs font-semibold shadow-xs"
          >
            {refreshing ? <Spinner data-icon="inline-start" /> : <RefreshCw data-icon="inline-start" className="size-3.5" />}
            Refresh Data
          </Button>

          <Button
            variant="default"
            size="sm"
            disabled={runningWorker}
            onClick={handleRunWorker}
            title="Check overdue cases and process scheduled retries now without waiting for the next cron cycle."
            className="h-8.5 gap-1.5 rounded-lg bg-foreground text-background text-xs font-semibold shadow-xs hover:bg-foreground/90"
          >
            {runningWorker ? <Spinner data-icon="inline-start" /> : <Play data-icon="inline-start" className="size-3.5 fill-current" />}
            Run Recovery Worker
          </Button>
        </div>
      </div>

      {/* 1-Click Simulation Toolbar */}
      <SimulationToolbar
        onSimulate={handleSimulate}
        activeSimulation={activeSimulation}
      />

      {/* 5 KPI Metric Cards Strip with Sparklines */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
        <MetricCard
          title="REVENUE AT RISK"
          value={formatMoney(stats?.at_risk)}
          subtitle={`${stats?.total_cases || 0} total cases`}
          variant="destructive"
          sparkline="red"
          loading={loading}
          icon={
            <div className="flex size-6 items-center justify-center rounded-full border border-rose-500/20 bg-rose-500/10 text-rose-500">
              <AlertCircle className="size-3.5" />
            </div>
          }
        />
        <MetricCard
          title="WON BACK (RECOVERED)"
          value={formatMoney(stats?.recovered)}
          subtitle={`${recoveredPct.toFixed(1)}% conversion`}
          variant="success"
          sparkline="green"
          loading={loading}
          icon={
            <div className="flex size-6 items-center justify-center rounded-full border border-emerald-500/20 bg-emerald-500/10 text-emerald-500">
              <CheckCircle2 className="size-3.5" />
            </div>
          }
        />
        <MetricCard
          title="IN PROGRESS"
          value={stats?.in_progress_cases || 0}
          subtitle="Active outreach & timers"
          variant="primary"
          sparkline="purple"
          loading={loading}
          icon={
            <div className="flex size-6 items-center justify-center rounded-full border border-indigo-500/20 bg-indigo-500/10 text-indigo-500">
              <Clock className="size-3.5" />
            </div>
          }
        />
        <MetricCard
          title="ESCALATED TO OPS"
          value={stats?.escalated_cases || 0}
          subtitle="Slack handoffs dispatched"
          variant="default"
          sparkline="purple"
          loading={loading}
          icon={
            <div className="flex size-6 items-center justify-center rounded-full border border-purple-500/20 bg-purple-500/10 text-purple-500">
              <Users className="size-3.5" />
            </div>
          }
        />
        <MetricCard
          title="RECOVERY RATE"
          value={formatPercent(stats?.recovery_rate)}
          subtitle="Intervention efficiency"
          variant="success"
          sparkline="green"
          loading={loading}
          icon={
            <div className="flex size-6 items-center justify-center rounded-full border border-emerald-500/20 bg-emerald-500/10 text-emerald-500">
              <TrendingUp className="size-3.5" />
            </div>
          }
        />
      </div>

      {/* Split Ledger: Left Column (Live Cases Ledger) | Right Column (Audit Detail Drawer) */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1.35fr_1.1fr]">
        <CasesLedger
          cases={cases}
          selectedCaseId={selectedCaseId}
          onSelectCase={setSelectedCaseId}
          loading={loading}
          initialSearch={initialSearch}
        />

        <AuditDrawer
          selectedCase={selectedCase}
          onResolveCase={handleResolveCase}
        />
      </div>

      {/* Recent Action & Outreach Logs with CSV Export */}
      <RecentLogsCard />
    </div>
  )
}
