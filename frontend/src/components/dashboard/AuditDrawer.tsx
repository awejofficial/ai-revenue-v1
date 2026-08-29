// frontend/src/components/dashboard/AuditDrawer.tsx

import React, { useState } from "react"
import {
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  Clock,
  MoreVertical,
  Check,
  Sparkles,
  SlidersHorizontal,
  Expand,
  Search,
  Send,
  CheckCircle2,
  ChevronDown,
  Trophy,
  ExternalLink,
} from "lucide-react"
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Spinner } from "@/components/ui/spinner"
import { getStatusBadge } from "./CasesLedger"
import { formatMoney, formatDate, cn } from "@/lib/utils"
import type { Case } from "@/types/api"

interface AuditDrawerProps {
  selectedCase: Case | null
  onResolveCase: (caseId: number) => Promise<void>
}

interface TimelineNode {
  id: string
  time: string
  title: string
  description: string
  icon: React.ElementType
  iconStyle: string
  badge?: string
}

export const AuditDrawer: React.FC<AuditDrawerProps> = ({
  selectedCase,
  onResolveCase,
}) => {
  const [resolving, setResolving] = useState(false)
  const [expandedAll, setExpandedAll] = useState(true)

  if (!selectedCase) {
    return (
      <Card className="flex h-full min-h-[460px] flex-col items-center justify-center border-border/80 bg-card p-8 text-center shadow-xs">
        <div className="flex size-12 items-center justify-center rounded-full bg-muted text-muted-foreground">
          <Clock className="size-6" />
        </div>
        <CardTitle className="mt-4 text-base font-bold">No Case Selected</CardTitle>
        <CardDescription className="mt-1 max-w-xs text-xs">
          Click any case from the ledger on the left to inspect AI diagnostics, customer telemetry, and execution logs.
        </CardDescription>
      </Card>
    )
  }

  const handleResolve = async () => {
    try {
      setResolving(true)
      await onResolveCase(selectedCase.case_id)
    } finally {
      setResolving(false)
    }
  }

  const isResolved = selectedCase.status === "resolved"
  const isEscalated = selectedCase.status === "escalated"

  // Build Timeline Nodes matching inspiration screenshot
  const timelineNodes: TimelineNode[] = [
    {
      id: "node_detected",
      time: formatDate(selectedCase.created_at),
      title: "Payment Degradation Detected",
      description: `Failure event ingested into raw_events. Amount at risk: ${formatMoney(selectedCase.amount_usd)}.`,
      icon: ShieldAlert,
      iconStyle: "bg-foreground text-background",
    },
    {
      id: "node_diagnosis",
      time: formatDate(selectedCase.updated_at),
      title: "Diagnosis & Policy Check",
      description:
        selectedCase.llm_reasoning || "Deterministic rule matched with customer context.",
      icon: Search,
      iconStyle: "bg-foreground text-background",
    },
    {
      id: "node_outreach",
      time: formatDate(selectedCase.updated_at),
      title: "Autonomous Outreach Dispatched",
      description:
        selectedCase.last_action || `Payment verified via ${selectedCase.case_type}`,
      icon: Send,
      iconStyle: "bg-foreground text-background",
    },
  ]

  if (isResolved) {
    timelineNodes.push({
      id: "node_resolved",
      time: formatDate(selectedCase.updated_at),
      title: "Inbound Revenue Recovered",
      description: `Inbound payment verified. ${formatMoney(selectedCase.amount_usd)} won back. Case closed.`,
      icon: Check,
      iconStyle: "bg-emerald-600 text-white",
      badge: "Success",
    })
  } else if (isEscalated) {
    timelineNodes.push({
      id: "node_escalated",
      time: formatDate(selectedCase.updated_at),
      title: "Escalated to Human Operations",
      description: "Policy safety bound exceeded. Escalated to Ops team via Slack.",
      icon: AlertTriangle,
      iconStyle: "bg-destructive text-destructive-foreground",
      badge: "Escalated",
    })
  }

  const retryPercentage = Math.round(
    (selectedCase.current_retry_count / (selectedCase.max_retries || 3)) * 100
  )

  return (
    <Card className="border-border/80 bg-card shadow-xs">
      {/* Card Header matching inspiration */}
      <CardHeader className="border-b border-border/60 p-4 sm:p-5">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-3">
            {/* Top Left Icon Container */}
            <div
              className={cn(
                "flex size-10 items-center justify-center rounded-xl border",
                isResolved
                  ? "border-emerald-500/30 bg-emerald-50 text-emerald-600 dark:bg-emerald-950/40 dark:text-emerald-400"
                  : isEscalated
                  ? "border-rose-500/30 bg-rose-50 text-rose-600 dark:bg-rose-950/40 dark:text-rose-400"
                  : "border-blue-500/30 bg-blue-50 text-blue-600 dark:bg-blue-950/40 dark:text-blue-400"
              )}
            >
              {isResolved ? (
                <ShieldCheck className="size-5" />
              ) : isEscalated ? (
                <AlertTriangle className="size-5" />
              ) : (
                <Clock className="size-5" />
              )}
            </div>

            <div>
              <div className="flex flex-wrap items-center gap-2">
                <CardTitle className="text-base font-bold sm:text-lg">
                  {selectedCase.customer_id}
                </CardTitle>
                {getStatusBadge(selectedCase.status)}
              </div>
              <CardDescription className="font-mono text-xs text-muted-foreground">
                Case #{selectedCase.case_id} · {selectedCase.case_type} ·{" "}
                {formatMoney(selectedCase.amount_usd)}
              </CardDescription>
            </div>
          </div>

          <Button
            variant="outline"
            size="icon"
            className="size-8 rounded-lg border-border/80 text-muted-foreground hover:text-foreground"
            aria-label="More Options"
          >
            <MoreVertical className="size-4" />
          </Button>
        </div>
      </CardHeader>

      <CardContent className="space-y-4 p-4 sm:p-5">
        {/* 4-Column Specifications Matrix with Dividers and Subtext */}
        <div className="grid grid-cols-2 gap-3 rounded-xl border border-border/80 p-3 sm:grid-cols-4 sm:gap-0 sm:divide-x sm:divide-border/60">
          {/* RETRIES */}
          <div className="flex flex-col items-center justify-center px-2 text-center">
            <span className="font-mono text-[10px] font-semibold tracking-wider text-muted-foreground uppercase">
              Retries
            </span>
            <p className="mt-1 font-mono text-base font-bold text-foreground">
              {selectedCase.current_retry_count} / {selectedCase.max_retries || 3}
            </p>
            <div className="mt-1 flex items-center gap-1 font-mono text-[11px] text-emerald-600 dark:text-emerald-400">
              <Check className="size-3" />
              <span>{retryPercentage}% used</span>
            </div>
          </div>

          {/* NEXT ACTION */}
          <div className="flex flex-col items-center justify-center px-2 text-center">
            <span className="font-mono text-[10px] font-semibold tracking-wider text-muted-foreground uppercase">
              Next Action
            </span>
            <p className="mt-1 text-sm font-bold text-foreground truncate max-w-full">
              {selectedCase.scheduled_next_action_at
                ? formatDate(selectedCase.scheduled_next_action_at)
                : "N/A"}
            </p>
            <span className="mt-1 text-[11px] text-muted-foreground">
              {selectedCase.scheduled_next_action_at ? "Auto-scheduled" : "No action required"}
            </span>
          </div>

          {/* AMOUNT */}
          <div className="flex flex-col items-center justify-center px-2 text-center">
            <span className="font-mono text-[10px] font-semibold tracking-wider text-muted-foreground uppercase">
              Amount
            </span>
            <p className="mt-1 font-mono text-base font-bold text-foreground">
              {formatMoney(selectedCase.amount_usd)}
            </p>
            <div className="mt-1 flex items-center gap-1 font-mono text-[11px] text-emerald-600 dark:text-emerald-400">
              <Check className="size-3" />
              <span>{isResolved ? "Recovered" : "At risk"}</span>
            </div>
          </div>

          {/* UPDATED */}
          <div className="flex flex-col items-center justify-center px-2 text-center">
            <span className="font-mono text-[10px] font-semibold tracking-wider text-muted-foreground uppercase">
              Updated
            </span>
            <p className="mt-1 text-xs font-semibold text-foreground truncate max-w-full">
              {formatDate(selectedCase.updated_at)}
            </p>
            <div className="mt-1 flex items-center gap-1 text-[11px] text-muted-foreground">
              <Clock className="size-3" />
              <span>Live sync</span>
            </div>
          </div>
        </div>

        {/* AI Diagnostic Intelligence Callout */}
        {selectedCase.llm_reasoning && (
          <div className="flex items-start gap-3 rounded-xl border border-blue-500/25 bg-blue-50/50 p-3.5 dark:bg-blue-950/25">
            <div className="flex size-8 shrink-0 items-center justify-center rounded-full bg-blue-500/15 text-blue-600 dark:bg-blue-500/20 dark:text-blue-400">
              <Sparkles className="size-4" />
            </div>
            <div className="space-y-0.5">
              <h4 className="text-xs font-bold text-blue-700 dark:text-blue-400">
                AI Diagnostic Intelligence & Policy Bounds
              </h4>
              <p className="text-xs text-foreground/90 leading-relaxed">
                {selectedCase.llm_reasoning}
              </p>
            </div>
          </div>
        )}

        {/* Lifecycle Audit Stream Header */}
        <div className="pt-1">
          <div className="flex items-center justify-between pb-3">
            <div className="flex items-center gap-2">
              <SlidersHorizontal className="size-4 text-foreground" />
              <h4 className="text-sm font-bold text-foreground">Lifecycle Audit Stream</h4>
            </div>

            <Button
              variant="ghost"
              size="sm"
              onClick={() => setExpandedAll(!expandedAll)}
              className="h-7 gap-1 rounded-md px-2 text-[11px] font-medium text-muted-foreground hover:text-foreground"
            >
              <Expand className="size-3" />
              <span>{expandedAll ? "Collapse all" : "Expand all"}</span>
            </Button>
          </div>

          {/* Timeline Nodes Connected with Vertical Guide */}
          <div className="relative ml-3 space-y-6 border-l-2 border-border/80 pl-6">
            {timelineNodes.map((node) => {
              const NodeIcon = node.icon
              return (
                <div key={node.id} className="relative group">
                  {/* Circular Node Icon on Line */}
                  <span
                    className={cn(
                      "absolute -left-[35px] top-0 flex size-6.5 items-center justify-center rounded-full shadow-2xs ring-4 ring-background",
                      node.iconStyle
                    )}
                  >
                    <NodeIcon className="size-3.5" />
                  </span>

                  <div className="space-y-1">
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-mono text-[10px] font-medium text-muted-foreground">
                        {node.time}
                      </span>
                      <ChevronDown className="size-3.5 text-muted-foreground/60 transition-transform group-hover:text-foreground" />
                    </div>

                    <div className="flex items-center gap-2">
                      <h5 className="text-xs font-bold text-foreground">{node.title}</h5>
                      {node.badge && (
                        <Badge
                          variant="outline"
                          className="border-emerald-500/30 bg-emerald-50 px-1.5 py-0 font-mono text-[9px] font-semibold text-emerald-600 dark:bg-emerald-950/40 dark:text-emerald-400"
                        >
                          {node.badge}
                        </Badge>
                      )}
                    </div>

                    {expandedAll && (
                      <p className="text-xs text-muted-foreground leading-relaxed">
                        {node.description}
                      </p>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Bottom Banner matching inspiration */}
        <div
          className={cn(
            "mt-2 flex flex-wrap items-center justify-between gap-3 rounded-xl border p-3.5",
            isResolved
              ? "border-emerald-500/30 bg-emerald-50/50 dark:bg-emerald-950/20"
              : "border-border/80 bg-muted/30"
          )}
        >
          <div className="flex items-center gap-3">
            <div
              className={cn(
                "flex size-9 items-center justify-center rounded-xl",
                isResolved
                  ? "bg-emerald-500/15 text-emerald-600 dark:bg-emerald-500/20 dark:text-emerald-400"
                  : "bg-muted text-muted-foreground"
              )}
            >
              <Trophy className="size-4.5" />
            </div>

            <div>
              <p
                className={cn(
                  "text-xs font-bold",
                  isResolved
                    ? "text-emerald-900 dark:text-emerald-300"
                    : "text-foreground"
                )}
              >
                {isResolved ? "Case Resolved Successfully" : "Case Active in Dunning Cycle"}
              </p>
              <p className="text-[11px] text-muted-foreground">
                {isResolved
                  ? "Inbound revenue recovered and customer retained."
                  : "Monitoring autonomous touchpoints and webhook events."}
              </p>
            </div>
          </div>

          {isResolved ? (
            <Button
              variant="outline"
              size="sm"
              className="h-8 gap-1.5 rounded-lg border-border/80 text-xs font-semibold shadow-2xs"
            >
              <span>View Case Details</span>
              <ExternalLink className="size-3" />
            </Button>
          ) : (
            <Button
              variant="default"
              size="sm"
              disabled={resolving}
              onClick={handleResolve}
              className="h-8 gap-1.5 rounded-lg bg-emerald-600 text-white text-xs font-semibold hover:bg-emerald-700 shadow-2xs"
            >
              {resolving ? (
                <Spinner data-icon="inline-start" />
              ) : (
                <CheckCircle2 data-icon="inline-start" className="size-3.5" />
              )}
              Mark Resolved
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
