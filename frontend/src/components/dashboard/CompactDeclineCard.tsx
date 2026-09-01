// frontend/src/components/dashboard/CompactDeclineCard.tsx

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

interface CompactDeclineCardProps {
  failureCodes?: AnalyticsFailureCodes
  loading?: boolean
  onViewFullBreakdown?: () => void
}

export const CompactDeclineCard: React.FC<CompactDeclineCardProps> = ({
  failureCodes,
  loading = false,
  onViewFullBreakdown,
}) => {
  const c = failureCodes || {
    checkout_drop_off: 4,
    insufficient_funds: 37,
    card_expired: 17,
    suspected_fraud: 17,
    other: 10,
  }

  const total =
    c.checkout_drop_off +
    c.insufficient_funds +
    c.card_expired +
    c.suspected_fraud +
    c.other

  const getPercent = (count: number) => {
    if (total === 0) return "0.0%"
    return `${((count / total) * 100).toFixed(1)}%`
  }

  const rows = [
    {
      label: "Checkout Drop-Offs & Abandoned Carts",
      count: c.checkout_drop_off,
      pct: getPercent(c.checkout_drop_off),
      icon: ShoppingCart,
      iconContainer: "bg-rose-50 text-rose-600 border-rose-500/20 dark:bg-rose-950/40 dark:text-rose-400",
    },
    {
      label: "Insufficient Balance (Payday Retries)",
      count: c.insufficient_funds,
      pct: getPercent(c.insufficient_funds),
      icon: CreditCard,
      iconContainer: "bg-blue-50 text-blue-600 border-blue-500/20 dark:bg-blue-950/40 dark:text-blue-400",
    },
    {
      label: "Expired Cards (Payment Update Links)",
      count: c.card_expired,
      pct: getPercent(c.card_expired),
      icon: Clock,
      iconContainer: "bg-amber-50 text-amber-600 border-amber-500/20 dark:bg-amber-950/40 dark:text-amber-400",
    },
    {
      label: "Suspected Fraud / Risk Flags",
      count: c.suspected_fraud,
      pct: getPercent(c.suspected_fraud),
      icon: Flag,
      iconContainer: "bg-red-50 text-red-600 border-red-500/20 dark:bg-red-950/40 dark:text-red-400",
    },
    {
      label: "Other Gateway Declines / Edge Cases",
      count: c.other,
      pct: getPercent(c.other),
      icon: Zap,
      iconContainer: "bg-purple-50 text-purple-600 border-purple-500/20 dark:bg-purple-950/40 dark:text-purple-400",
    },
  ]

  return (
    <Card className="flex flex-col border-border/80 bg-card shadow-xs">
      <CardHeader className="border-b border-border/60 pb-3">
        <div className="flex items-center justify-between gap-2">
          <div className="space-y-0.5">
            <CardTitle className="text-base font-bold">Payment Failure Reasons</CardTitle>
            <CardDescription className="text-xs">
              Breakdown of why payments failed across all gateways
            </CardDescription>
          </div>

          <Badge
            variant="secondary"
            className="border border-purple-500/30 bg-purple-50/80 font-mono text-[11px] font-semibold text-purple-700 dark:bg-purple-950/30 dark:text-purple-300"
          >
            {total} total failures
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="p-0">
        <div className="divide-y divide-border/60">
          {loading ? (
            <div className="space-y-3 p-4">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="flex items-center justify-between py-1">
                  <Skeleton className="h-6 w-48" />
                  <Skeleton className="h-4 w-12" />
                </div>
              ))}
            </div>
          ) : (
            rows.map((row, idx) => {
              const Icon = row.icon
              return (
                <div
                  key={idx}
                  className="flex items-center justify-between px-4 py-2.5 transition-colors hover:bg-muted/40"
                >
                  <div className="flex items-center gap-3">
                    <div
                      className={`flex size-7 shrink-0 items-center justify-center rounded-lg border ${row.iconContainer}`}
                    >
                      <Icon className="size-3.5" />
                    </div>
                    <span className="text-xs font-semibold text-foreground">{row.label}</span>
                  </div>

                  <span className="font-mono text-xs font-bold text-foreground">
                    {row.count} <span className="text-[11px] font-normal text-muted-foreground">({row.pct})</span>
                  </span>
                </div>
              )
            })
          )}
        </div>

        {/* Footer: View full breakdown */}
        <div className="border-t border-border/60 p-2.5">
          <button
            type="button"
            onClick={onViewFullBreakdown}
            className="flex w-full items-center justify-between rounded-md px-3 py-1.5 text-xs font-semibold text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
          >
            <span>View full breakdown</span>
            <ChevronRight className="size-3.5" />
          </button>
        </div>
      </CardContent>
    </Card>
  )
}
