// frontend/src/components/dashboard/AuditDrawer.tsx

import React, { useState } from "react"
import {
  ShieldAlert,
  Search,
  Send,
  Check,
  AlertTriangle,
  Clock,
  MoreVertical,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Sparkles,
} from "lucide-react"
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Spinner } from "@/components/ui/spinner"
import { formatMoney, formatDate, cn } from "@/lib/utils"
import type { Case, CaseStatus } from "@/types/api"

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

function getInspectorStatusBadge(status: CaseStatus) {
  switch (status) {
    case "resolved":
      return (
        <Badge
          variant="outline"
          className="rounded-full border-emerald-500/30 bg-emerald-50 px-2.5 py-0.5 font-mono text-[11px] font-semibold text-emerald-600 dark:bg-emerald-950/40 dark:text-emerald-400"
        >
          Recovered
        </Badge>
      )
    case "escalated":
      return (
        <Badge
          variant="destructive"
          className="rounded-full bg-destructive/15 px-2.5 py-0.5 font-mono text-[11px] font-semibold text-destructive"
        >
          Escalated
        </Badge>
      )
    case "retrying":
      return (
        <Badge
          variant="outline"
          className="rounded-full border-amber-500/30 bg-amber-50/80 px-2.5 py-0.5 font-mono text-[11px] font-semibold text-amber-700 dark:bg-amber-950/40 dark:text-amber-300"
        >
          Retrying
        </Badge>
      )
    case "awaiting_input":
      return (
        <Badge
          variant="outline"
          className="rounded-full border-amber-500/30 bg-amber-50/80 px-2.5 py-0.5 font-mono text-[11px] font-semibold text-amber-700 dark:bg-amber-950/40 dark:text-amber-300"
        >
          Awaiting Action
        </Badge>
      )
    case "diagnosing":
      return (
        <Badge
          variant="secondary"
          className="rounded-full border-border bg-muted px-2.5 py-0.5 font-mono text-[11px] font-semibold text-muted-foreground"
        >
          Diagnosing
        </Badge>
      )
    default:
      return (
        <Badge variant="outline" className="rounded-full border-border font-mono text-[11px] text-muted-foreground">
          {status}
        </Badge>
      )
  }
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

  // Build Timeline Nodes with Circular Icons matching design
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
        selectedCase.last_action || `Payment update dispatched for ${selectedCase.customer_id}`,
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
          <div>
            <div className="flex flex-wrap items-center gap-2.5">
              <CardTitle className="text-lg font-bold text-foreground sm:text-xl">
                {selectedCase.customer_id}
              </CardTitle>
              {getInspectorStatusBadge(selectedCase.status)}
            </div>
            <CardDescription className="mt-1 font-mono text-xs text-muted-foreground">
              Case #{selectedCase.case_id} · {selectedCase.case_type} ·{" "}
              {formatMoney(selectedCase.amount_usd)}
            </CardDescription>
          </div>

          <Button
            variant="ghost"
            size="icon"
            className="size-8 rounded-lg text-muted-foreground hover:text-foreground"
            aria-label="More Options"
          >
            <MoreVertical className="size-4" />
          </Button>
        </div>
      </CardHeader>

      <CardContent className="space-y-4 p-4 sm:p-5">
        {/* 4-Column Specifications Matrix matching inspiration */}
        <div className="grid grid-cols-2 gap-3 rounded-xl border border-border/80 p-4 sm:grid-cols-4 sm:gap-0 sm:divide-x sm:divide-border/60">
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
            <p className="mt-1 text-xs font-bold text-foreground truncate max-w-full sm:text-sm">
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
            <p className="mt-1 text-xs font-bold text-foreground truncate max-w-full sm:text-sm">
              {formatDate(selectedCase.updated_at)}
            </p>
            <div className="mt-1 flex items-center gap-1.5 text-[11px] text-muted-foreground">
              <span className="size-1.5 rounded-full bg-muted-foreground/60" />
              <span>Live sync</span>
            </div>
          </div>
        </div>

        {/* AI Diagnostic Intelligence Callout */}
        {selectedCase.llm_reasoning && (
          <div className="flex items-start gap-3.5 rounded-xl border border-blue-500/20 bg-blue-50/40 p-4 dark:bg-blue-950/20">
            <div className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-blue-100/70 text-blue-600 dark:bg-blue-900/40 dark:text-blue-400">
              <Sparkles className="size-4.5" />
            </div>
            <div className="space-y-1">
              <h4 className="text-xs font-bold text-blue-600 dark:text-blue-400">
                AI Diagnostic Intelligence & Policy Bounds
              </h4>
              <p className="text-xs text-foreground/90 leading-relaxed">
                {selectedCase.llm_reasoning}
              </p>
            </div>
          </div>
        )}

        {/* Lifecycle Audit Stream Header */}
        <div className="pt-2">
          <div className="flex items-center justify-between pb-3">
            <h4 className="text-base font-bold text-foreground">Lifecycle Audit Stream</h4>

            <Button
              variant="ghost"
              size="sm"
              onClick={() => setExpandedAll(!expandedAll)}
              className="h-7 gap-1 rounded-md px-2 text-xs font-medium text-muted-foreground hover:text-foreground"
            >
              {expandedAll ? <ChevronUp className="size-3.5" /> : <ChevronDown className="size-3.5" />}
              <span>{expandedAll ? "Collapse all" : "Expand all"}</span>
            </Button>
          </div>

          {/* Timeline Nodes with Circular Icons on Vertical Track */}
          <div className="relative ml-3 space-y-6 border-l-2 border-border/80 pl-6">
            {timelineNodes.map((node) => {
              const NodeIcon = node.icon
              return (
                <div key={node.id} className="relative group">
                  {/* Circular Node Icon on Timeline Line */}
                  <span
                    className={cn(
                      "absolute -left-[35px] top-0.5 flex size-6.5 items-center justify-center rounded-full shadow-2xs ring-4 ring-background",
                      node.iconStyle
                    )}
                  >
                    <NodeIcon className="size-3.5" />
                  </span>

                  <div className="space-y-0.5">
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-mono text-[11px] font-medium text-muted-foreground">
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
                      <p className="text-xs text-muted-foreground leading-relaxed pt-0.5">
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
        <div className="mt-3 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-border/80 bg-card p-4 shadow-2xs">
          <div>
            <p className="text-xs font-bold text-foreground">
              {isResolved ? "Case Resolved Successfully" : "Case Active in Dunning Cycle"}
            </p>
            <p className="mt-0.5 text-[11px] text-muted-foreground">
              {isResolved
                ? "Inbound revenue recovered and customer retained."
                : "Monitoring autonomous touchpoints and webhook events."}
            </p>
          </div>

          {!isResolved && (
            <Button
              variant="default"
              size="sm"
              disabled={resolving}
              onClick={handleResolve}
              className="h-9 gap-1.5 rounded-lg bg-emerald-600 px-4 text-xs font-semibold text-white shadow-xs hover:bg-emerald-700"
            >
              {resolving ? (
                <Spinner data-icon="inline-start" />
              ) : (
                <CheckCircle2 data-icon="inline-start" className="size-4" />
              )}
              Mark Resolved
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
