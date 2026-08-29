// frontend/src/components/analytics/AnalyticsView.tsx

import React, { useState, useEffect, useCallback } from "react"
import {
  RefreshCw,
  Filter,
  AlertCircle,
  CheckCircle2,
  TrendingUp,
  Send,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Spinner } from "@/components/ui/spinner"
import { MetricCard } from "@/components/layout/MetricCard"
import { FunnelWaterfall } from "@/components/analytics/FunnelWaterfall"
import { ChannelRoiMatrix } from "@/components/analytics/ChannelRoiMatrix"
import { DeclineBreakdown } from "@/components/analytics/DeclineBreakdown"
import { api } from "@/lib/api"
import { formatMoney, formatPercent } from "@/lib/utils"
import { toast } from "sonner"
import type { AnalyticsData } from "@/types/api"

export const AnalyticsView: React.FC = () => {
  const [data, setData] = useState<AnalyticsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)

  const loadData = useCallback(async (isSilent = false) => {
    try {
      if (!isSilent) setRefreshing(true)
      const res = await api.getAnalytics()
      setData(res)
    } catch (err) {
      console.error("Failed to load analytics:", err)
      toast.error("Failed to fetch recovery analytics")
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [])

  useEffect(() => {
    loadData()
  }, [loadData])

  const f = data?.funnel

  return (
    <div className="space-y-6">
      {/* Page Header matching inspiration */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="flex size-10 items-center justify-center rounded-xl border border-purple-500/20 bg-purple-500/10 text-purple-600 dark:text-purple-400">
            <Filter className="size-5" />
          </div>
          <div>
            <h2 className="text-xl font-bold tracking-tight text-foreground sm:text-2xl">
              Recovery Funnel & Intelligence
            </h2>
            <p className="text-xs text-muted-foreground sm:text-sm">
              End-to-end conversion analytics, multi-channel attribution, and processor telemetry.
            </p>
          </div>
        </div>

        <Button
          variant="outline"
          size="sm"
          disabled={refreshing}
          onClick={() => loadData(false)}
          className="h-8.5 gap-1.5 rounded-lg border-border/80 text-xs font-semibold shadow-xs"
        >
          {refreshing ? (
            <Spinner data-icon="inline-start" />
          ) : (
            <RefreshCw data-icon="inline-start" className="size-3.5" />
          )}
          Refresh Telemetry
        </Button>
      </div>

      {/* 4 Financial Metric Cards Strip with sparklines */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="TOTAL REVENUE AT RISK"
          value={formatMoney(f?.at_risk_amount)}
          subtitle="Across all payment failures"
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
          title="TOTAL WON BACK"
          value={formatMoney(f?.recovered_amount)}
          subtitle="Closed-loop auto-resolutions"
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
          title="OVERALL WIN-BACK RATE"
          value={formatPercent(f?.recovery_rate_pct)}
          subtitle="Intervention conversion efficiency"
          variant="success"
          sparkline="green"
          loading={loading}
          icon={
            <div className="flex size-6 items-center justify-center rounded-full border border-emerald-500/20 bg-emerald-500/10 text-emerald-500">
              <TrendingUp className="size-3.5" />
            </div>
          }
        />
        <MetricCard
          title="DISPATCHED TOUCHES"
          value={f?.outreach_dispatched || 0}
          subtitle="Email, SMS, Slack, Links"
          variant="primary"
          sparkline="purple"
          loading={loading}
          icon={
            <div className="flex size-6 items-center justify-center rounded-full border border-indigo-500/20 bg-indigo-500/10 text-indigo-500">
              <Send className="size-3.5" />
            </div>
          }
        />
      </div>

      {/* Mid 2-Column Grid: Funnel Waterfall + Channel Matrix */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <FunnelWaterfall funnel={f} loading={loading} />
        <ChannelRoiMatrix channels={data?.channels} gateways={data?.gateways} loading={loading} />
      </div>

      {/* Root Cause Decline Reason Breakdown */}
      <DeclineBreakdown failureCodes={data?.failure_codes} loading={loading} />
    </div>
  )
}
