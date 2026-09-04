// frontend/src/components/exceptions/ExceptionsView.tsx

import React, { useState, useEffect } from "react"
import {
  AlertTriangle,
  RefreshCw,
  ChevronDown,
  ChevronRight,
  Bot,
  Lock,
  Clock,
  Ban,
  CheckCircle2,
  Copy,
} from "lucide-react"
import { api, type ExceptionsResponse } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { toast } from "sonner"

const CAUSE_META: Record<string, { label: string; color: string; bg: string; icon: any }> = {
  BANK_DECLINE: {
    label: "Bank Issuer Decline",
    color: "text-rose-600 dark:text-rose-400",
    bg: "bg-rose-500/10 border-rose-500/20",
    icon: Ban,
  },
  NETWORK_TIMEOUT: {
    label: "Network Switch Timeout",
    color: "text-blue-600 dark:text-blue-400",
    bg: "bg-blue-500/10 border-blue-500/20",
    icon: Clock,
  },
  INSUFFICIENT_FUNDS: {
    label: "Insufficient Account Balance",
    color: "text-amber-600 dark:text-amber-400",
    bg: "bg-amber-500/10 border-amber-500/20",
    icon: AlertTriangle,
  },
  CARD_EXPIRED: {
    label: "Expired Payment Instrument",
    color: "text-purple-600 dark:text-purple-400",
    bg: "bg-purple-500/10 border-purple-500/20",
    icon: Clock,
  },
  FRAUD_FLAG: {
    label: "Fraud / Compliance Lockdown",
    color: "text-red-700 dark:text-red-400",
    bg: "bg-red-500/15 border-red-500/30",
    icon: Lock,
  },
  CHECKOUT_ABANDONED: {
    label: "Checkout Funnel Abandonment",
    color: "text-cyan-600 dark:text-cyan-400",
    bg: "bg-cyan-500/10 border-cyan-500/20",
    icon: AlertTriangle,
  },
  SUBSCRIPTION_FAILED: {
    label: "Recurring Mandate Failure",
    color: "text-pink-600 dark:text-pink-400",
    bg: "bg-pink-500/10 border-pink-500/20",
    icon: Ban,
  },
  OVERDUE_INVOICE: {
    label: "B2B Overdue Receivables",
    color: "text-teal-600 dark:text-teal-400",
    bg: "bg-teal-500/10 border-teal-500/20",
    icon: Clock,
  },
  UNKNOWN: {
    label: "Uncategorized Degradation",
    color: "text-slate-600 dark:text-slate-400",
    bg: "bg-slate-500/10 border-slate-500/20",
    icon: AlertTriangle,
  },
}

interface ExceptionsViewProps {
  onOpenAuditModal?: (payment: any) => void
}

export const ExceptionsView: React.FC<ExceptionsViewProps> = ({ onOpenAuditModal }) => {
  const [data, setData] = useState<ExceptionsResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [expanded, setExpanded] = useState<Record<string, boolean>>({})
  const [copiedId, setCopiedId] = useState<string | null>(null)

  const handleCopy = (id: string) => {
    navigator.clipboard.writeText(id)
    setCopiedId(id)
    toast.success("Payment ID copied", { description: id })
    setTimeout(() => setCopiedId(null), 2000)
  }

  const fetchExceptions = async () => {
    setLoading(true)
    try {
      const res = await api.fetchHonestExceptions()
      setData(res)
      // Auto-expand all categories by default
      const exp: Record<string, boolean> = {}
      res.by_cause.forEach((g) => {
        exp[g.root_cause] = true
      })
      setExpanded(exp)
    } catch (err: any) {
      console.error("[ExceptionsView] Error:", err)
      toast.error(err.message || "Failed to load exception list")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchExceptions()
  }, [])

  const toggleGroup = (cause: string) => {
    setExpanded((prev) => ({ ...prev, [cause]: !prev[cause] }))
  }

  const [selectedCategory, setSelectedCategory] = useState<string>("ALL")

  const filteredGroups = data?.by_cause.filter((g) => {
    if (selectedCategory === "ALL") return true
    return g.root_cause === selectedCategory
  })

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-extrabold tracking-tight text-foreground sm:text-2xl">
              Honest Exception List
            </h1>
            <Badge variant="outline" className="font-mono text-[10px] text-rose-600 dark:text-rose-400 border-rose-500/30">
              {data?.total_exceptions ?? 0} UNRESOLVED
            </Badge>
          </div>
          <p className="text-xs text-muted-foreground">
            Transparently surfaces what the autonomous agent could not resolve, categorized by root cause with financial exposure.
          </p>
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={fetchExceptions}
          disabled={loading}
          className="gap-1.5 text-xs cursor-pointer"
        >
          <RefreshCw className={`size-3.5 ${loading ? "animate-spin text-primary" : ""}`} />
          <span>Refresh</span>
        </Button>
      </div>

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3 sm:gap-4">
        <div className="rounded-xl border border-border bg-card p-4 shadow-xs">
          <span className="text-xs font-mono font-medium text-muted-foreground uppercase tracking-wider">
            Total Unresolved Cases
          </span>
          <p className="mt-2 text-2xl font-bold font-mono text-rose-600 dark:text-rose-400">
            {data?.total_exceptions ?? 0}
          </p>
          <p className="mt-0.5 text-[11px] text-muted-foreground">Escalated to human review / unrecoverable</p>
        </div>

        <div className="rounded-xl border border-border bg-card p-4 shadow-xs">
          <span className="text-xs font-mono font-medium text-muted-foreground uppercase tracking-wider">
            Total Value at Risk
          </span>
          <p className="mt-2 text-2xl font-bold font-mono text-amber-600 dark:text-amber-400">
            ₹{(data?.total_value_at_risk ?? 0).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
          </p>
          <p className="mt-0.5 text-[11px] text-muted-foreground">Across all failed and escalated records</p>
        </div>

        <div className="rounded-xl border border-border bg-card p-4 shadow-xs">
          <span className="text-xs font-mono font-medium text-muted-foreground uppercase tracking-wider">
            Root Cause Categories
          </span>
          <p className="mt-2 text-2xl font-bold font-mono text-foreground">
            {data?.by_cause?.length ?? 0}
          </p>
          <p className="mt-0.5 text-[11px] text-muted-foreground">Distinct failure categories identified by AI</p>
        </div>
      </div>

      {/* Category Filter Tabs */}
      <div className="flex flex-wrap items-center gap-1.5 font-mono text-xs">
        <button
          type="button"
          onClick={() => setSelectedCategory("ALL")}
          className={`px-3 py-1 rounded-lg border text-xs font-semibold cursor-pointer transition-all ${
            selectedCategory === "ALL"
              ? "bg-primary text-primary-foreground border-primary"
              : "bg-card text-muted-foreground border-border hover:text-foreground"
          }`}
        >
          All Causes
        </button>
        {data?.by_cause?.map((g) => (
          <button
            key={g.root_cause}
            type="button"
            onClick={() => setSelectedCategory(g.root_cause)}
            className={`px-3 py-1 rounded-lg border text-xs font-semibold cursor-pointer transition-all ${
              selectedCategory === g.root_cause
                ? "bg-primary text-primary-foreground border-primary"
                : "bg-card text-muted-foreground border-border hover:text-foreground"
            }`}
          >
            {g.root_cause} ({g.count})
          </button>
        ))}
      </div>

      {/* Grouped Accordions */}
      {!data?.by_cause || data.by_cause.length === 0 ? (
        <div className="rounded-xl border border-border/80 bg-card p-12 text-center text-xs text-muted-foreground shadow-xs">
          <CheckCircle2 className="mx-auto size-10 text-emerald-500/70" />
          <p className="mt-3 text-sm font-semibold text-foreground">Zero Unresolved Exceptions</p>
          <p className="mt-1 text-xs">All processed payments have been successfully resolved or recovered!</p>
        </div>
      ) : (
        <div className="flex flex-col gap-4">
          {filteredGroups?.map((group) => {
            const meta = CAUSE_META[group.root_cause] || CAUSE_META.UNKNOWN
            const Icon = meta.icon
            const isExp = expanded[group.root_cause] ?? false

            return (
              <div
                key={group.root_cause}
                className="overflow-hidden rounded-xl border border-border/80 bg-card shadow-xs transition-all"
              >
                {/* Accordion Header */}
                <button
                  type="button"
                  onClick={() => toggleGroup(group.root_cause)}
                  className="flex w-full cursor-pointer items-center justify-between border-b border-border/70 p-4 text-left hover:bg-muted/20"
                >
                  <div className="flex items-center gap-3">
                    <div className={`flex size-8 items-center justify-center rounded-lg border ${meta.bg}`}>
                      <Icon className={`size-4 ${meta.color}`} />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-bold text-foreground">{meta.label}</span>
                        <span className="rounded-md bg-muted px-2 py-0.5 font-mono text-[10px] font-semibold text-muted-foreground">
                          {group.root_cause}
                        </span>
                      </div>
                      <p className="text-xs text-muted-foreground">
                        {group.count} transactions · Value:{" "}
                        <span className="font-semibold text-foreground">
                          ₹{group.total_value.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                        </span>
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <span className="text-xs font-semibold text-rose-600 dark:text-rose-400">
                      {group.count} cases
                    </span>
                    {isExp ? <ChevronDown className="size-4 text-muted-foreground" /> : <ChevronRight className="size-4 text-muted-foreground" />}
                  </div>
                </button>

                {/* Accordion Content */}
                {isExp && (
                  <div className="divide-y divide-border/60 bg-muted/10 p-2">
                    {group.payments.map((p) => (
                      <div key={p.id} className="p-3 text-xs">
                        <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                          <div>
                            <div className="flex flex-wrap items-center gap-2">
                              <div className="flex items-center gap-1.5 font-mono font-bold text-foreground">
                                <span>{p.id}</span>
                                <button
                                  type="button"
                                  onClick={() => handleCopy(p.id)}
                                  className="text-muted-foreground hover:text-foreground transition-colors p-0.5 rounded cursor-pointer"
                                  title="Copy Payment ID"
                                >
                                  {copiedId === p.id ? (
                                    <CheckCircle2 className="size-3 text-emerald-500" />
                                  ) : (
                                    <Copy className="size-3" />
                                  )}
                                </button>
                              </div>
                              <span className="rounded-sm border border-rose-500/30 bg-rose-500/10 px-1.5 py-0.5 text-[10px] font-semibold text-rose-600 dark:text-rose-400">
                                {p.status}
                              </span>
                              <span className="text-muted-foreground">· Customer: {p.customer_email}</span>
                              {onOpenAuditModal && (
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => onOpenAuditModal(p)}
                                  className="h-6 gap-1 px-2 text-[10px] font-semibold text-blue-600 dark:text-blue-400 border-blue-500/30 hover:bg-blue-500/10 ml-auto"
                                >
                                  <span>Audit</span>
                                </Button>
                              )}
                            </div>

                            {/* AI Reasoning Box */}
                            {p.gemini_reasoning && (
                              <div className="mt-2 flex items-start gap-2 rounded-lg border border-border/80 bg-card p-2 text-xs">
                                <Bot className="size-3.5 shrink-0 text-primary mt-0.5" />
                                <div>
                                  <span className="font-semibold text-primary">AI Failure Reasoning:</span>{" "}
                                  <span className="text-foreground">{p.gemini_reasoning}</span>
                                </div>
                              </div>
                            )}

                            {/* Customer Message Draft */}
                            {p.recovery_message && (
                              <div className="mt-1 text-[11px] text-muted-foreground">
                                <span className="font-medium">Hinglish Copy:</span> <em>"{p.recovery_message}"</em>
                              </div>
                            )}
                          </div>

                          <div className="text-right sm:shrink-0">
                            <div className="text-sm font-bold text-foreground">
                              ₹{p.amount.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                            </div>
                            <div className="text-[10px] text-muted-foreground">
                              Retries: {p.retry_count} · {new Date(p.created_at).toLocaleDateString()}
                            </div>
                            <div className="mt-1 text-[10px] text-muted-foreground">
                              Action: <code className="rounded bg-muted px-1">{p.recovery_action}</code>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
