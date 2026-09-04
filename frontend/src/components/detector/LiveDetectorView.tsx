// frontend/src/components/detector/LiveDetectorView.tsx

import React, { useState, useEffect, useCallback } from "react"
import {
  Radar,
  RefreshCw,
  AlertTriangle,
  Clock,
  ShieldCheck,
  Zap,
  CheckCircle2,
  Copy,
  ExternalLink,
  ShieldAlert,
} from "lucide-react"
import { api, type DetectorData, type FailedPayment } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"
import { toast } from "sonner"

export const LiveDetectorView: React.FC = () => {
  const [data, setData] = useState<DetectorData | null>(null)
  const [loading, setLoading] = useState(true)
  const [hours, setHours] = useState<number>(24)
  const [recoveringMap, setRecoveringMap] = useState<Record<string, { status: "loading" | "done" | "error"; action?: string; link?: string; error?: string }>>({})
  const [copiedId, setCopiedId] = useState<string | null>(null)

  const fetchData = useCallback(async () => {
    setLoading(true)
    try {
      const res = await api.detectLivePayments(hours)
      setData(res)
    } catch (err: any) {
      console.error("[LiveDetector] Error polling Razorpay:", err)
      toast.error(err.message || "Failed to poll Razorpay live API")
    } finally {
      setLoading(false)
    }
  }, [hours])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  const handleCopy = (id: string) => {
    navigator.clipboard.writeText(id)
    setCopiedId(id)
    toast.success(`Copied ID: ${id}`)
    setTimeout(() => setCopiedId(null), 2000)
  }

  const handleIngestAndRecover = async (payment: FailedPayment) => {
    setRecoveringMap((prev) => ({ ...prev, [payment.id]: { status: "loading" } }))
    try {
      const res = await api.ingestLivePayment({
        id: payment.id,
        amount: payment.amount,
        currency: payment.currency,
        error_code: payment.error_code,
        error_description: payment.error_description,
        email: payment.email,
        contact: payment.contact,
        method: payment.method,
      })

      const actionText = res?.action || res?.recovery_action || "RECOVERED"
      setRecoveringMap((prev) => ({
        ...prev,
        [payment.id]: {
          status: "done",
          action: actionText,
          link: res?.payment_link_id ? `https://rzp.io/i/${res.payment_link_id}` : undefined,
        },
      }))
      toast.success(`Autonomous recovery dispatched: ${actionText}`)
    } catch (err: any) {
      setRecoveringMap((prev) => ({
        ...prev,
        [payment.id]: { status: "error", error: err.message },
      }))
      toast.error(`Recovery failed: ${err.message}`)
    }
  }

  const [countdown, setCountdown] = useState<number>(30)

  useEffect(() => {
    const timer = setInterval(() => {
      if (typeof document !== "undefined" && document.visibilityState !== "visible") {
        return
      }
      setCountdown((prev) => {
        if (prev <= 1) {
          fetchData()
          return 30
        }
        return prev - 1
      })
    }, 1000)
    return () => clearInterval(timer)
  }, [fetchData])

  return (
    <div className="flex flex-col gap-6">
      {/* Header Section */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-extrabold tracking-tight text-foreground sm:text-2xl">
              Live Razorpay Failure Radar
            </h1>
            <Badge variant="outline" className="font-mono text-[10px] text-emerald-600 dark:text-emerald-400 border-emerald-500/30">
              <span className="size-1.5 rounded-full bg-emerald-500 animate-ping mr-1.5" />
              POLLING ACTIVE
            </Badge>
          </div>
          <p className="text-xs text-muted-foreground">
            Real-time active polling of Razorpay API feed for payment drop-offs and at-risk pre-authorizations
          </p>
        </div>

        {/* Controls */}
        <div className="flex items-center gap-2 font-mono text-xs">
          <span className="text-muted-foreground hidden sm:inline text-[11px]">
            Refresh in {countdown}s
          </span>

          <select
            value={hours}
            onChange={(e) => {
              setHours(Number(e.target.value))
              setCountdown(30)
            }}
            className="h-9 rounded-lg border border-border bg-card px-3 text-xs font-medium text-foreground shadow-xs focus:outline-hidden cursor-pointer"
          >
            <option value={6}>Last 6 Hours</option>
            <option value={12}>Last 12 Hours</option>
            <option value={24}>Last 24 Hours</option>
            <option value={48}>Last 48 Hours</option>
          </select>

          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              fetchData()
              setCountdown(30)
            }}
            disabled={loading}
            className="gap-1.5 text-xs cursor-pointer"
          >
            <RefreshCw className={cn("size-3.5", loading && "animate-spin text-primary")} />
            <span>Poll Now</span>
          </Button>
        </div>
      </div>

      {/* API Notice or Warning */}
      {data?.error && (
        <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-4 text-xs text-amber-800 dark:text-amber-300">
          <div className="flex items-start gap-3">
            <AlertTriangle className="size-5 shrink-0 text-amber-600 dark:text-amber-400" />
            <div>
              <p className="font-semibold">{data.error}</p>
              {data.note && <p className="mt-1 text-muted-foreground">{data.note}</p>}
            </div>
          </div>
        </div>
      )}

      {/* KPI Cards Row */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 sm:gap-4">
        <div className="rounded-xl border border-border/80 bg-card p-4 shadow-xs">
          <div className="flex items-center justify-between text-muted-foreground">
            <span className="text-xs font-medium uppercase tracking-wider">Total Fetched</span>
            <Radar className="size-4 text-blue-500" />
          </div>
          <p className="mt-2 text-2xl font-bold text-foreground">{data?.total_fetched ?? 0}</p>
          <p className="mt-0.5 text-[11px] text-muted-foreground">Across last {hours}h window</p>
        </div>

        <div className="rounded-xl border border-border/80 bg-card p-4 shadow-xs">
          <div className="flex items-center justify-between text-muted-foreground">
            <span className="text-xs font-medium uppercase tracking-wider">Failed Payments</span>
            <AlertTriangle className="size-4 text-rose-500" />
          </div>
          <p className="mt-2 text-2xl font-bold text-rose-600 dark:text-rose-400">
            {data?.failed_count ?? 0}
          </p>
          <p className="mt-0.5 text-[11px] text-muted-foreground">Requires AI recovery</p>
        </div>

        <div className="rounded-xl border border-border/80 bg-card p-4 shadow-xs">
          <div className="flex items-center justify-between text-muted-foreground">
            <span className="text-xs font-medium uppercase tracking-wider">Authorized (At Risk)</span>
            <Clock className="size-4 text-amber-500" />
          </div>
          <p className="mt-2 text-2xl font-bold text-amber-600 dark:text-amber-400">
            {data?.authorized_not_captured ?? 0}
          </p>
          <p className="mt-0.5 text-[11px] text-muted-foreground">Pre-auth uncaptured</p>
        </div>

        <div className="rounded-xl border border-border/80 bg-card p-4 shadow-xs">
          <div className="flex items-center justify-between text-muted-foreground">
            <span className="text-xs font-medium uppercase tracking-wider">Captured / Settled</span>
            <ShieldCheck className="size-4 text-emerald-500" />
          </div>
          <p className="mt-2 text-2xl font-bold text-emerald-600 dark:text-emerald-400">
            {data?.captured_count ?? 0}
          </p>
          <p className="mt-0.5 text-[11px] text-muted-foreground">Successfully collected</p>
        </div>
      </div>

      {/* Main Failed Payments Table */}
      <div className="rounded-xl border border-border/80 bg-card shadow-xs">
        <div className="flex items-center justify-between border-b border-border/70 p-4">
          <div className="flex items-center gap-2">
            <ShieldAlert className="size-4 text-rose-500" />
            <h2 className="text-sm font-semibold text-foreground">
              Detected Failed Payments from Razorpay Feed
            </h2>
            <span className="rounded-full bg-rose-500/10 px-2 py-0.5 text-xs font-medium text-rose-600 dark:text-rose-400">
              {data?.failed_payments?.length ?? 0}
            </span>
          </div>
          <p className="text-[11px] text-muted-foreground">
            Last polled: {data?.polled_at ? new Date(data.polled_at).toLocaleTimeString() : "—"}
          </p>
        </div>

        {!data?.failed_payments || data.failed_payments.length === 0 ? (
          <div className="p-8 text-center text-xs text-muted-foreground">
            <CheckCircle2 className="mx-auto size-8 text-emerald-500/60" />
            <p className="mt-2 font-medium">No failed payments detected in the last {hours} hours</p>
            <p className="mt-1 text-[11px]">
              Trigger a test failure on your Razorpay dashboard with test cards (e.g. 4000 0000 0000 0002) and refresh!
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-border/70 bg-muted/30 text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
                <tr>
                  <th className="p-3 pl-4">Payment ID</th>
                  <th className="p-3">Amount</th>
                  <th className="p-3">Error Code</th>
                  <th className="p-3">Gateway Description</th>
                  <th className="p-3">Customer Contact</th>
                  <th className="p-3">Detected At</th>
                  <th className="p-3 pr-4 text-right">Autonomous Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/60">
                {data.failed_payments.map((p) => {
                  const state = recoveringMap[p.id]
                  return (
                    <tr key={p.id} className="transition-colors hover:bg-muted/20">
                      <td className="p-3 pl-4 font-mono font-medium text-foreground">
                        <div className="flex items-center gap-1.5">
                          <span>{p.id.slice(0, 12)}…</span>
                          <button
                            type="button"
                            onClick={() => handleCopy(p.id)}
                            className="text-muted-foreground hover:text-foreground"
                            title="Copy Payment ID"
                          >
                            {copiedId === p.id ? (
                              <CheckCircle2 className="size-3 text-emerald-500" />
                            ) : (
                              <Copy className="size-3" />
                            )}
                          </button>
                        </div>
                      </td>
                      <td className="p-3 font-semibold text-foreground">
                        ₹{p.amount.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                      </td>
                      <td className="p-3">
                        <span className="inline-flex rounded-md border border-border/80 bg-muted px-2 py-0.5 font-mono text-[11px] font-medium text-foreground">
                          {p.error_code}
                        </span>
                      </td>
                      <td className="p-3 max-w-[260px] truncate text-muted-foreground" title={p.error_description}>
                        {p.error_description}
                      </td>
                      <td className="p-3 text-muted-foreground">
                        <div>{p.email}</div>
                        <div className="text-[10px] text-muted-foreground/80">{p.contact}</div>
                      </td>
                      <td className="p-3 text-muted-foreground whitespace-nowrap">
                        {new Date(p.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </td>
                      <td className="p-3 pr-4 text-right">
                        {state?.status === "loading" ? (
                          <Button size="sm" variant="outline" disabled className="h-7 text-xs gap-1">
                            <RefreshCw className="size-3 animate-spin text-primary" />
                            Diagnosing...
                          </Button>
                        ) : state?.status === "done" ? (
                          <div className="flex items-center justify-end gap-1.5">
                            <span className="inline-flex items-center gap-1 rounded-md bg-emerald-500/10 px-2 py-1 text-[11px] font-semibold text-emerald-600 dark:text-emerald-400">
                              <CheckCircle2 className="size-3" />
                              {state.action}
                            </span>
                            {state.link && (
                              <a
                                href={state.link}
                                target="_blank"
                                rel="noreferrer"
                                className="inline-flex items-center rounded-md border border-border p-1 hover:bg-muted"
                                title="Open Generated Recovery Link"
                              >
                                <ExternalLink className="size-3" />
                              </a>
                            )}
                          </div>
                        ) : (
                          <Button
                            size="sm"
                            onClick={() => handleIngestAndRecover(p)}
                            className="h-7 gap-1 bg-primary text-xs font-medium text-primary-foreground shadow-xs hover:bg-primary/90"
                          >
                            <Zap className="size-3" />
                            Recover
                          </Button>
                        )}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* At-Risk Authorizations Section */}
      {data?.at_risk_payments && data.at_risk_payments.length > 0 && (
        <div className="rounded-xl border border-amber-500/30 bg-card p-4 shadow-xs">
          <div className="flex items-center gap-2 text-amber-600 dark:text-amber-400">
            <Clock className="size-4" />
            <h3 className="text-sm font-bold">At-Risk Payments: Authorized but Uncaptured ({data.at_risk_payments.length})</h3>
          </div>
          <p className="mt-1 text-xs text-muted-foreground">
            These payments are authorized on the customer card/UPI rail but have not been captured by merchant backend. If uncaptured within 5 days, Razorpay releases the authorization back to the issuer bank.
          </p>
          <div className="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-3">
            {data.at_risk_payments.map((ap) => (
              <div key={ap.id} className="flex items-center justify-between rounded-lg border border-border/80 bg-muted/30 p-2.5 text-xs">
                <div>
                  <span className="font-mono font-semibold">{ap.id.slice(0, 14)}…</span>
                  <p className="text-[10px] text-muted-foreground">{new Date(ap.created_at).toLocaleDateString()}</p>
                </div>
                <div className="text-right">
                  <span className="font-bold text-amber-600 dark:text-amber-400">₹{ap.amount.toLocaleString("en-IN")}</span>
                  <span className="block text-[10px] uppercase text-muted-foreground">Expiring</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
