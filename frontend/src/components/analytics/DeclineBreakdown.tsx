// frontend/src/components/analytics/DeclineBreakdown.tsx

import React from "react"
import {
  ShoppingCart,
  CreditCard,
  Clock,
  Flag,
  Zap,
  ChevronRight,
} from "lucide-react"
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import type { AnalyticsFailureCodes } from "@/types/api"

interface DeclineBreakdownProps {
  failureCodes?: AnalyticsFailureCodes
  loading?: boolean
}

export const DeclineBreakdown: React.FC<DeclineBreakdownProps> = ({
  failureCodes,
  loading = false,
}) => {
  const rows = [
    {
      label: "Checkout Drop-Offs & Abandoned Carts",
      description: "3DS authentication abandonments and cart friction timeouts",
      count: failureCodes?.checkout_drop_off || 0,
      icon: ShoppingCart,
      iconContainer: "bg-rose-50 text-rose-600 border-rose-500/20 dark:bg-rose-950/40 dark:text-rose-400",
    },
    {
      label: "Insufficient Balance (Payday Retries)",
      description: "Transient declines scheduled for 72h payday alignment",
      count: failureCodes?.insufficient_funds || 0,
      icon: CreditCard,
      iconContainer: "bg-blue-50 text-blue-600 border-blue-500/20 dark:bg-blue-950/40 dark:text-blue-400",
    },
    {
      label: "Expired Cards (Payment Update Links)",
      description: "Card validity in past; automated update links dispatched",
      count: failureCodes?.card_expired || 0,
      icon: Clock,
      iconContainer: "bg-amber-50 text-amber-600 border-amber-500/20 dark:bg-amber-950/40 dark:text-amber-400",
    },
    {
      label: "Suspected Fraud / Risk Flags",
      description: "High-risk anomalies escalated directly to human team",
      count: failureCodes?.suspected_fraud || 0,
      icon: Flag,
      iconContainer: "bg-red-50 text-red-600 border-red-500/20 dark:bg-red-950/40 dark:text-red-400",
    },
    {
      label: "Other Gateway Declines / Edge Cases",
      description: "Processor-specific decline codes evaluated via Gemini AI",
      count: failureCodes?.other || 0,
      icon: Zap,
      iconContainer: "bg-purple-50 text-purple-600 border-purple-500/20 dark:bg-purple-950/40 dark:text-purple-400",
    },
  ]

  const totalFailures = rows.reduce((sum, r) => sum + r.count, 0)

  return (
    <Card className="border-border/80 bg-card shadow-xs">
      <CardHeader className="border-b border-border/60 pb-3.5">
        <div className="flex items-center justify-between gap-2">
          <div className="space-y-1">
            <CardTitle className="text-base font-bold">Root Cause Decline Breakdown</CardTitle>
            <CardDescription className="text-xs">
              Diagnostic classification across all ingested payment failure events
            </CardDescription>
          </div>

          <Badge
            variant="secondary"
            className="border border-purple-500/30 bg-purple-50/80 font-mono text-[11px] font-semibold text-purple-700 dark:bg-purple-950/30 dark:text-purple-300"
          >
            {totalFailures} total events
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="p-0">
        {/* Table Column Subheaders */}
        <div className="flex items-center justify-between border-b border-border/60 bg-muted/30 px-5 py-2 font-mono text-[10px] font-semibold tracking-wider text-muted-foreground uppercase">
          <span>Cause Category</span>
          <span>Events</span>
        </div>

        <div className="divide-y divide-border/60">
          {loading ? (
            <div className="space-y-3 p-4">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="flex items-center justify-between py-1">
                  <Skeleton className="h-7 w-56" />
                  <Skeleton className="h-5 w-12" />
                </div>
              ))}
            </div>
          ) : (
            rows.map((row, idx) => {
              const Icon = row.icon
              return (
                <div
                  key={idx}
                  className="flex cursor-pointer items-center justify-between px-5 py-3.5 transition-colors hover:bg-muted/40"
                >
                  <div className="flex items-center gap-3.5">
                    <div
                      className={`flex size-8.5 shrink-0 items-center justify-center rounded-lg border ${row.iconContainer}`}
                    >
                      <Icon className="size-4" />
                    </div>
                    <div>
                      <p className="text-xs font-semibold text-foreground">{row.label}</p>
                      <p className="text-[11px] text-muted-foreground">{row.description}</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <span className="font-mono text-sm font-bold text-foreground">
                      {row.count}
                    </span>
                    <ChevronRight className="size-4 text-muted-foreground/60" />
                  </div>
                </div>
              )
            })
          )}
        </div>
      </CardContent>
    </Card>
  )
}
