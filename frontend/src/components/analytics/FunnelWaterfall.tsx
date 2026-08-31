// frontend/src/components/analytics/FunnelWaterfall.tsx

import React from "react"
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import type { AnalyticsFunnel } from "@/types/api"

interface FunnelWaterfallProps {
  funnel?: AnalyticsFunnel
  loading?: boolean
}

export const FunnelWaterfall: React.FC<FunnelWaterfallProps> = ({
  funnel,
  loading = false,
}) => {
  const detected = funnel?.detected || 0
  const diagnosed = funnel?.diagnosed || 0
  const touches = funnel?.outreach_dispatched || 0
  const recoveredCases = funnel?.recovered_cases || 0
  const recoveryRate = funnel?.recovery_rate_pct || 0

  const outreachPct = detected > 0 ? Math.min(100, Math.max(15, Math.round((touches / detected) * 100))) : 0

  const steps = [
    {
      num: "1",
      badgeStyle: "border-blue-500/30 bg-blue-50 text-blue-600 dark:bg-blue-950/40 dark:text-blue-400",
      label: "Payment Degradations & Drop-Offs",
      count: `${detected} Cases (100%)`,
      percent: 100,
      barColor: "bg-blue-600",
      subtext: "100% Ingested",
    },
    {
      num: "2",
      badgeStyle: "border-indigo-500/30 bg-indigo-50 text-indigo-600 dark:bg-indigo-950/40 dark:text-indigo-400",
      label: "Context & Gemini AI Diagnostics",
      count: `${diagnosed} Cases (100%)`,
      percent: 100,
      barColor: "bg-indigo-600",
      subtext: "100% Evaluated",
    },
    {
      num: "3",
      badgeStyle: "border-orange-500/30 bg-orange-50 text-orange-600 dark:bg-orange-950/40 dark:text-orange-400",
      label: "Bounded Outreach Dispatched",
      count: `${touches} Touches Sent`,
      percent: outreachPct,
      barColor: "bg-orange-500",
      subtext: "Outreach Active",
    },
    {
      num: "4",
      badgeStyle: "border-emerald-500/30 bg-emerald-50 text-emerald-600 dark:bg-emerald-950/40 dark:text-emerald-400",
      label: "Verified Revenue Recovered",
      count: `${recoveredCases} Cases (${recoveryRate}%)`,
      percent: Math.min(100, Math.max(15, recoveryRate)),
      barColor: "bg-emerald-500",
      subtext: "Auto-Resolved",
    },
  ]

  return (
    <Card className="border-border/80 bg-card shadow-xs">
      <CardHeader className="border-b border-border/60 pb-3.5">
        <div className="space-y-1">
          <CardTitle className="text-base font-bold">Autonomous Recovery Funnel</CardTitle>
          <CardDescription className="text-xs">
            Conversion flow from degradation detection to verified recovery
          </CardDescription>
        </div>
      </CardHeader>

      <CardContent className="space-y-4 p-5">
        {loading ? (
          <div className="space-y-4">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="space-y-2">
                <Skeleton className="h-4 w-48" />
                <Skeleton className="h-8 w-full rounded-md" />
              </div>
            ))}
          </div>
        ) : (
          steps.map((step, idx) => (
            <div key={idx} className="space-y-1.5">
              {/* Step Header with numbered badge */}
              <div className="flex items-center justify-between text-xs font-semibold">
                <div className="flex items-center gap-2">
                  <span
                    className={`flex size-5.5 items-center justify-center rounded-md border font-mono text-[11px] font-bold ${step.badgeStyle}`}
                  >
                    {step.num}
                  </span>
                  <span className="text-foreground">{step.label}</span>
                </div>
                <span className="font-mono text-muted-foreground">{step.count}</span>
              </div>

              {/* Progress Bar with rounded track */}
              <div className="h-7 w-full overflow-hidden rounded-md bg-muted/70 p-0.5">
                <div
                  className={`flex h-full items-center rounded-sm px-3 font-mono text-[11px] font-bold text-white transition-all duration-700 ease-out ${step.barColor}`}
                  style={{ width: `${step.percent}%` }}
                >
                  {step.subtext}
                </div>
              </div>
            </div>
          ))
        )}
      </CardContent>
    </Card>
  )
}
