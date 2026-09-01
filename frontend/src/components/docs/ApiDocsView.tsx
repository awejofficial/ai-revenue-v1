// frontend/src/components/docs/ApiDocsView.tsx

import React, { useState } from "react"
import {
  Zap,
  Copy,
  Check,
  ExternalLink,
  Search,
  Code2,
  Play,
  Shield,
  Activity,
  CreditCard,
  Users,
  BarChart3,
  Terminal,
} from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Spinner } from "@/components/ui/spinner"
import { API_BASE_URL, api } from "@/lib/api"
import { toast } from "sonner"

type EndpointCategory =
  | "all"
  | "webhooks"
  | "operations"
  | "customers"
  | "analytics"
  | "admin"
  | "health"

interface EndpointDoc {
  id: string
  category: "webhooks" | "operations" | "customers" | "analytics" | "admin" | "health"
  method: "GET" | "POST"
  path: string
  title: string
  description: string
  headers?: Record<string, string>
  params?: { name: string; type: string; required: boolean; description: string }[]
  requestBody?: Record<string, unknown>
  responseSample: Record<string, unknown> | unknown[]
  canTryLive?: boolean
  liveAction?: () => Promise<unknown>
}

export const ApiDocsView: React.FC = () => {
  const [category, setCategory] = useState<EndpointCategory>("all")
  const [search, setSearch] = useState("")
  const [copiedId, setCopiedId] = useState<string | null>(null)
  const [executingId, setExecutingId] = useState<string | null>(null)
  const [liveOutputs, setLiveOutputs] = useState<Record<string, string>>({})

  const effectiveBaseUrl = API_BASE_URL || (typeof window !== "undefined" ? window.location.origin : "")
  const swaggerUrl = API_BASE_URL ? `${API_BASE_URL}/docs` : "/docs"

  const handleCopy = (text: string, id: string) => {
    navigator.clipboard.writeText(text)
    setCopiedId(id)
    toast.success("Copied to clipboard!")
    setTimeout(() => setCopiedId(null), 2000)
  }

  const handleRunLive = async (endpoint: EndpointDoc) => {
    if (!endpoint.liveAction) return
    try {
      setExecutingId(endpoint.id)
      const res = await endpoint.liveAction()
      setLiveOutputs((prev) => ({
        ...prev,
        [endpoint.id]: JSON.stringify(res, null, 2),
      }))
      toast.success(`Executed ${endpoint.method} ${endpoint.path}`)
    } catch (err) {
      console.error(err)
      setLiveOutputs((prev) => ({
        ...prev,
        [endpoint.id]: `Error: ${err instanceof Error ? err.message : "Request failed"}`,
      }))
      toast.error("Execution failed")
    } finally {
      setExecutingId(null)
    }
  }

  const endpoints: EndpointDoc[] = [
    {
      id: "health",
      category: "health",
      method: "GET",
      path: "/health",
      title: "Engine Health & Readiness Probe",
      description: "Returns autonomous agent service availability, system version, and dashboard routes.",
      responseSample: {
        message: "Autonomous AI Revenue Recovery Agent is online.",
        status: "healthy",
        version: "1.0.0",
        docs: "/docs",
        dashboard: "/dashboard",
      },
      canTryLive: true,
      liveAction: async () => await api.getHealth(),
    },
    {
      id: "webhooks_psp",
      category: "webhooks",
      method: "POST",
      path: "/webhooks/psp",
      title: "Inbound Payment Gateway Webhook (Stripe & Razorpay)",
      description:
        "Ingests payment failure events (to initiate AI recovery) and payment success events (to auto-resolve open cases).",
      headers: {
        "Content-Type": "application/json",
        "Stripe-Signature": "t=...,v1=...",
      },
      requestBody: {
        id: "evt_3MtwLwLkdIwHu7ix28a3tqPa",
        type: "payment_intent.payment_failed",
        data: {
          object: {
            id: "pi_3MtwLwLkdIwHu7ix28a3tqPa",
            customer: "cus_high_ltv_01",
            amount: 49900,
            currency: "usd",
            last_payment_error: {
              code: "insufficient_funds",
              message: "The card was declined due to insufficient funds in account.",
            },
          },
        },
      },
      responseSample: {
        status: "event_ingested",
        event_id: "evt_3MtwLwLkdIwHu7ix28a3tqPa",
        customer_id: "cus_high_ltv_01",
        event_type: "payment_failed",
        case_id: 18,
      },
    },
    {
      id: "webhooks_billing",
      category: "webhooks",
      method: "POST",
      path: "/webhooks/billing",
      title: "ERP & Overdue Invoice Webhook",
      description: "Ingests aging B2B invoices and overdue billing milestones from ERP, NetSuite, or Chargebee.",
      requestBody: {
        customer_id: "cus_b2b_08",
        invoice_id: "inv_2026_9081",
        amount_due: 4500.0,
        currency: "USD",
        days_overdue: 14,
      },
      responseSample: {
        status: "ingested",
        event_id: "inv_2026_9081",
      },
    },
    {
      id: "dashboard_stats",
      category: "operations",
      method: "GET",
      path: "/dashboard/stats",
      title: "Real-Time Revenue Recovery KPI Ledger",
      description:
        "Calculates cumulative won-back revenue, at-risk capital, recovery rate percentage, and active case breakdown.",
      responseSample: {
        total_cases: 15,
        in_progress_cases: 2,
        resolved_cases: 13,
        escalated_cases: 0,
        at_risk: 640.0,
        recovered: 4358.0,
        escalated: 0.0,
        recovery_rate: 87.2,
      },
      canTryLive: true,
      liveAction: async () => await api.getDashboardStats(),
    },
    {
      id: "dashboard_cases",
      category: "operations",
      method: "GET",
      path: "/dashboard/cases?limit=30",
      title: "Operations Live Case Feed",
      description: "Retrieves prioritized recovery cases with retry count, LLM diagnostic logs, and next scheduled action.",
      params: [
        { name: "limit", type: "integer", required: false, description: "Maximum cases to return (default: 30)" },
      ],
      responseSample: [
        {
          case_id: 15,
          customer_id: "cus_high_ltv_01",
          case_type: "payment_failed",
          status: "retrying",
          amount_usd: 249.0,
          current_retry_count: 1,
          max_retries: 3,
          last_action: "email_dispatched_with_discount",
          scheduled_next_action_at: "2026-09-02T10:00:00Z",
          llm_reasoning: "High LTV account ($8,500). Offered polite 1-click retry link with 24h grace window.",
          created_at: "2026-09-01T08:30:00Z",
        },
      ],
      canTryLive: true,
      liveAction: async () => await api.getDashboardCases(5),
    },
    {
      id: "api_customers",
      category: "customers",
      method: "GET",
      path: "/api/customers",
      title: "Customer 360° Directory & Telemetry",
      description:
        "Fetches all managed accounts with CRM profile, Lifetime Value (LTV), active dunning status, and channel preferences.",
      responseSample: [
        {
          customer_id: "cus_high_ltv_01",
          name: "Ravi Sharma",
          company: "Apex Technologies",
          email: "ravi.sharma@example.com",
          phone: "+919876543210",
          ltv: 8500.0,
          segment: "high_ltv",
          plan: "enterprise_annual",
          country: "IN",
          cart_items: [],
          cart_value: 0.0,
          cases_count: 2,
          resolved_count: 2,
          in_progress_count: 0,
          recovered_amount: 498.0,
          last_status: "resolved",
        },
      ],
      canTryLive: true,
      liveAction: async () => await api.getCustomers(),
    },
    {
      id: "admin_seed",
      category: "customers",
      method: "POST",
      path: "/admin/seed",
      title: "Seed Demo Customer Directory & Test Cases",
      description: "Restores or initializes the customer directory, CRM data, and test failed events for demonstration.",
      responseSample: {
        status: "success",
        message: "Customer directory and demo cases seeded successfully.",
      },
      canTryLive: true,
      liveAction: async () => await api.seedDatabase(),
    },
    {
      id: "api_analytics",
      category: "analytics",
      method: "GET",
      path: "/api/analytics",
      title: "Comprehensive Recovery Funnel & Distribution",
      description:
        "Returns multi-tier funnel metrics (detected, diagnosed, outreach, recovered), channel distribution, and root cause failure breakdown.",
      responseSample: {
        funnel: {
          detected: 15,
          diagnosed: 15,
          outreach_dispatched: 14,
          recovered_cases: 13,
          escalated_cases: 0,
          at_risk_amount: 5000.0,
          recovered_amount: 4358.0,
          recovery_rate_pct: 87.2,
        },
        channels: { email: 8, sms: 3, slack: 2, razorpay: 3, stripe: 1 },
        failure_codes: { insufficient_funds: 6, card_expired: 4, checkout_drop_off: 3, suspected_fraud: 1, other: 1 },
        gateways: {
          stripe: { name: "Stripe US/EU", currency: "USD", status: "online" },
          razorpay: { name: "Razorpay India", currency: "INR", status: "online" },
        },
      },
      canTryLive: true,
      liveAction: async () => await api.getAnalytics(),
    },
    {
      id: "admin_simulate",
      category: "admin",
      method: "POST",
      path: "/admin/simulate?scenario={scenario}",
      title: "1-Click AI Recovery Simulator",
      description:
        "Synthesizes synthetic failure scenarios to trigger autonomous diagnosis, routing, and communication in real-time.",
      params: [
        {
          name: "scenario",
          type: "string",
          required: true,
          description:
            "Options: 'high_ltv_insufficient_funds', 'checkout_drop_off', 'repeat_failure', 'expired_card', 'fraud', 'trial_user'",
        },
      ],
      responseSample: {
        status: "simulated_and_processed",
        scenario: "high_ltv_insufficient_funds",
        event_id: "sim_high_ltv_1725178920",
        customer_id: "cus_high_ltv_01",
      },
      canTryLive: true,
      liveAction: async () => await api.simulateScenario("high_ltv_insufficient_funds"),
    },
    {
      id: "admin_process",
      category: "admin",
      method: "POST",
      path: "/admin/process",
      title: "Trigger Background Orchestrator Pass",
      description: "Forces an immediate background worker cycle to evaluate pending events, retry schedules, and dunning timeouts.",
      responseSample: {
        status: "processing_completed",
      },
      canTryLive: true,
      liveAction: async () => await api.triggerManualProcess(),
    },
    {
      id: "admin_action_logs",
      category: "admin",
      method: "GET",
      path: "/admin/action-logs?limit=50",
      title: "Outbound Communication Audit Logs",
      description: "Immutable compliance ledger recording all dispatched emails, SMS, Slack notifications, and UPI links.",
      params: [
        { name: "limit", type: "integer", required: false, description: "Maximum audit logs to return" },
      ],
      responseSample: [
        {
          id: 42,
          case_id: 15,
          customer_id: "cus_high_ltv_01",
          action_type: "email_sent",
          channel: "email",
          recipient: "ravi.sharma@example.com",
          status: "delivered",
          details: "AI recovery email dispatched with personalized 1-click update link.",
          created_at: "2026-09-01T08:35:00Z",
        },
      ],
      canTryLive: true,
      liveAction: async () => await api.getActionLogs(5),
    },
  ]

  const filteredEndpoints = endpoints.filter((ep) => {
    if (category !== "all" && ep.category !== category) return false
    if (!search.trim()) return true
    const q = search.toLowerCase()
    return (
      ep.title.toLowerCase().includes(q) ||
      ep.path.toLowerCase().includes(q) ||
      ep.description.toLowerCase().includes(q) ||
      ep.method.toLowerCase().includes(q)
    )
  })

  const categories: { id: EndpointCategory; label: string; icon: React.FC<{ className?: string }> }[] = [
    { id: "all", label: "All Endpoints", icon: Code2 },
    { id: "webhooks", label: "Webhooks", icon: CreditCard },
    { id: "operations", label: "Operations Hub", icon: Activity },
    { id: "customers", label: "Customer 360°", icon: Users },
    { id: "analytics", label: "Recovery Funnel", icon: BarChart3 },
    { id: "admin", label: "Worker & Simulator", icon: Terminal },
    { id: "health", label: "System Health", icon: Shield },
  ]

  return (
    <div className="space-y-6">
      {/* Hero Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-border/70 pb-5">
        <div>
          <div className="flex items-center gap-2.5">
            <h2 className="text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
              API & Webhook Documentation
            </h2>
            <Badge variant="outline" className="font-mono text-xs text-primary border-primary/30">
              v1.0.0
            </Badge>
          </div>
          <p className="mt-1 text-xs text-muted-foreground sm:text-sm">
            Complete REST & Webhook interface reference for autonomous dunning, customer intelligence, and PSP integration.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Base URL Pill with Copy */}
          <div className="flex items-center gap-2 rounded-lg border border-border/80 bg-muted/60 px-3 py-1.5 font-mono text-xs text-foreground">
            <span className="text-muted-foreground text-[11px] uppercase">Base:</span>
            <span className="max-w-[220px] truncate sm:max-w-none">{effectiveBaseUrl}</span>
            <button
              onClick={() => handleCopy(effectiveBaseUrl, "base_url")}
              className="ml-1 cursor-pointer text-muted-foreground hover:text-foreground"
              title="Copy Base URL"
            >
              {copiedId === "base_url" ? <Check className="size-3.5 text-emerald-500" /> : <Copy className="size-3.5" />}
            </button>
          </div>

          {/* Swagger UI External Link */}
          <a
            href={swaggerUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 rounded-lg border border-border/80 bg-background px-3 py-1.5 text-xs font-medium text-foreground shadow-2xs hover:bg-muted"
          >
            <Zap className="size-3.5 text-primary" />
            <span>Interactive Swagger UI</span>
            <ExternalLink className="size-3 text-muted-foreground" />
          </a>
        </div>
      </div>

      {/* Search & Category Filter Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-border/80 bg-muted/40 p-3 shadow-xs">
        <div className="relative w-full max-w-sm">
          <Search className="absolute top-1/2 left-2.5 size-3.5 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Filter by endpoint path, method, description..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="h-8 bg-background pl-8 text-xs"
          />
        </div>

        <div className="flex flex-wrap items-center gap-1.5">
          {categories.map((c) => {
            const Icon = c.icon
            const isSelected = category === c.id
            return (
              <Button
                key={c.id}
                variant={isSelected ? "default" : "outline"}
                size="sm"
                onClick={() => setCategory(c.id)}
                className="h-7 gap-1.5 text-xs"
              >
                <Icon className="size-3" />
                <span>{c.label}</span>
              </Button>
            )
          })}
        </div>
      </div>

      {/* Endpoint Cards List */}
      <div className="space-y-4">
        {filteredEndpoints.map((ep) => {
          const isCopied = copiedId === ep.id
          const isExecuting = executingId === ep.id
          const curlSnippet = `curl -X ${ep.method} "${effectiveBaseUrl}${ep.path}" \\
  -H "Content-Type: application/json"${
    ep.requestBody
      ? ` \\
  -d '${JSON.stringify(ep.requestBody)}'`
      : ""
  }`

          return (
            <Card key={ep.id} className="overflow-hidden border-border/80 bg-card shadow-xs">
              <CardHeader className="border-b border-border/60 bg-muted/20 pb-3">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div className="flex flex-wrap items-center gap-2.5">
                    {/* Method Badge */}
                    <span
                      className={`inline-flex items-center rounded-md px-2.5 py-0.5 font-mono text-xs font-bold tracking-wide ${
                        ep.method === "GET"
                          ? "bg-sky-500/15 text-sky-700 dark:bg-sky-500/20 dark:text-sky-300"
                          : "bg-emerald-500/15 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-300"
                      }`}
                    >
                      {ep.method}
                    </span>

                    {/* Path */}
                    <code className="font-mono text-xs font-semibold text-foreground sm:text-sm">
                      {ep.path}
                    </code>

                    {/* Quick Copy Path Button */}
                    <button
                      onClick={() => handleCopy(`${effectiveBaseUrl}${ep.path}`, ep.id)}
                      className="cursor-pointer text-muted-foreground hover:text-foreground"
                      title="Copy full URL"
                    >
                      {isCopied ? <Check className="size-3.5 text-emerald-500" /> : <Copy className="size-3.5" />}
                    </button>
                  </div>

                  <div className="flex items-center gap-2">
                    {/* Copy cURL */}
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleCopy(curlSnippet, `curl_${ep.id}`)}
                      className="h-7 gap-1 text-[11px]"
                    >
                      {copiedId === `curl_${ep.id}` ? (
                        <Check className="size-3 text-emerald-500" />
                      ) : (
                        <Terminal className="size-3" />
                      )}
                      <span>Copy cURL</span>
                    </Button>

                    {/* Try Live Probe (if applicable) */}
                    {ep.canTryLive && (
                      <Button
                        variant="secondary"
                        size="sm"
                        disabled={isExecuting}
                        onClick={() => handleRunLive(ep)}
                        className="h-7 gap-1 text-[11px]"
                      >
                        {isExecuting ? (
                          <Spinner className="size-3" />
                        ) : (
                          <Play className="size-3 fill-current text-primary" />
                        )}
                        <span>Try Request</span>
                      </Button>
                    )}
                  </div>
                </div>

                <div className="mt-2">
                  <CardTitle className="text-sm font-semibold text-foreground">{ep.title}</CardTitle>
                  <CardDescription className="text-xs text-muted-foreground">
                    {ep.description}
                  </CardDescription>
                </div>
              </CardHeader>

              <CardContent className="space-y-4 p-4 text-xs">
                {/* Headers / Params Table */}
                {ep.params && ep.params.length > 0 && (
                  <div>
                    <span className="font-mono text-[11px] font-semibold text-muted-foreground uppercase">
                      Query Parameters
                    </span>
                    <div className="mt-1.5 overflow-x-auto rounded-md border border-border/70">
                      <table className="w-full text-left text-xs">
                        <thead className="border-b border-border/70 bg-muted/40 font-mono text-[11px] text-muted-foreground">
                          <tr>
                            <th className="px-3 py-1.5">Parameter</th>
                            <th className="px-3 py-1.5">Type</th>
                            <th className="px-3 py-1.5">Required</th>
                            <th className="px-3 py-1.5">Description</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-border/60">
                          {ep.params.map((p) => (
                            <tr key={p.name}>
                              <td className="px-3 py-1.5 font-mono font-medium text-foreground">{p.name}</td>
                              <td className="px-3 py-1.5 font-mono text-muted-foreground">{p.type}</td>
                              <td className="px-3 py-1.5">
                                <span className={p.required ? "text-amber-500 font-medium" : "text-muted-foreground"}>
                                  {p.required ? "Yes" : "Optional"}
                                </span>
                              </td>
                              <td className="px-3 py-1.5 text-muted-foreground">{p.description}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* Request Payload JSON (if POST) */}
                {ep.requestBody && (
                  <div>
                    <div className="flex items-center justify-between pb-1">
                      <span className="font-mono text-[11px] font-semibold text-muted-foreground uppercase">
                        Request Body (JSON)
                      </span>
                      <button
                        onClick={() => handleCopy(JSON.stringify(ep.requestBody, null, 2), `req_${ep.id}`)}
                        className="cursor-pointer text-[11px] text-muted-foreground hover:text-foreground"
                      >
                        {copiedId === `req_${ep.id}` ? "Copied" : "Copy Payload"}
                      </button>
                    </div>
                    <pre className="max-h-56 overflow-auto rounded-md border border-border/70 bg-muted/50 p-3 font-mono text-[11px] text-foreground">
                      {JSON.stringify(ep.requestBody, null, 2)}
                    </pre>
                  </div>
                )}

                {/* Live Output (if run) */}
                {liveOutputs[ep.id] && (
                  <div>
                    <div className="flex items-center justify-between pb-1">
                      <span className="flex items-center gap-1 font-mono text-[11px] font-semibold text-emerald-600 dark:text-emerald-400 uppercase">
                        <Activity className="size-3" /> Live Response
                      </span>
                      <button
                        onClick={() => setLiveOutputs((prev) => ({ ...prev, [ep.id]: "" }))}
                        className="cursor-pointer text-[11px] text-muted-foreground hover:text-foreground"
                      >
                        Clear
                      </button>
                    </div>
                    <pre className="max-h-60 overflow-auto rounded-md border border-emerald-500/30 bg-emerald-500/5 p-3 font-mono text-[11px] text-foreground">
                      {liveOutputs[ep.id]}
                    </pre>
                  </div>
                )}

                {/* Response Sample */}
                {!liveOutputs[ep.id] && (
                  <div>
                    <div className="flex items-center justify-between pb-1">
                      <span className="font-mono text-[11px] font-semibold text-muted-foreground uppercase">
                        Response Schema / Example (200 OK)
                      </span>
                      <button
                        onClick={() => handleCopy(JSON.stringify(ep.responseSample, null, 2), `res_${ep.id}`)}
                        className="cursor-pointer text-[11px] text-muted-foreground hover:text-foreground"
                      >
                        {copiedId === `res_${ep.id}` ? "Copied" : "Copy Schema"}
                      </button>
                    </div>
                    <pre className="max-h-56 overflow-auto rounded-md border border-border/70 bg-muted/40 p-3 font-mono text-[11px] text-muted-foreground">
                      {JSON.stringify(ep.responseSample, null, 2)}
                    </pre>
                  </div>
                )}
              </CardContent>
            </Card>
          )
        })}

        {filteredEndpoints.length === 0 && (
          <div className="rounded-lg border border-border/70 bg-card p-12 text-center text-xs text-muted-foreground">
            No endpoints match your filter query.
          </div>
        )}
      </div>
    </div>
  )
}
