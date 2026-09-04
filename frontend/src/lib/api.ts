// frontend/src/lib/api.ts

import type {
  HealthStatusResponse,
  DashboardStats,
  Case,
  CustomerSummary,
  AnalyticsData,
  AnalyticsFailureCodes,
  ActionLog,
  PSPWebhookResponse,
  BillingWebhookPayload,
  BillingWebhookResponse,
  SimulationScenario,
  SimulateScenarioResponse,
  ManualProcessResponse,
  CaseResolutionResult,
} from "@/types/api"

export * from "@/types/api"

export class ApiError extends Error {
  status: number
  statusText: string
  details?: unknown

  constructor(status: number, statusText: string, message: string, details?: unknown) {
    super(message)
    this.name = "ApiError"
    this.status = status
    this.statusText = statusText
    this.details = details
  }
}

/**
 * Base API URL. In development, Vite proxies requests to http://127.0.0.1:8000.
 * In production, uses VITE_API_BASE_URL or automatically falls back to the live Render backend.
 */
function getApiBaseUrl(): string {
  // If running locally, route through Vite proxy to local backend
  if (
    typeof window !== "undefined" &&
    (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1")
  ) {
    return ""
  }
  const envUrl = import.meta.env.VITE_API_BASE_URL
  if (envUrl && typeof envUrl === "string" && envUrl.trim().length > 0) {
    return envUrl.replace(/\/$/, "")
  }
  // Automatic production fallback: If hosted on Vercel or cloud domain, route to deployed Render backend
  if (
    typeof window !== "undefined" &&
    (window.location.hostname.includes("vercel.app") ||
      (window.location.hostname !== "localhost" && window.location.hostname !== "127.0.0.1"))
  ) {
    return "https://ai-revenue-backend-t1nh.onrender.com"
  }
  return ""
}

export const API_BASE_URL = getApiBaseUrl()

/**
 * Generic request helper with robust error handling
 */
async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${path}`
  const headers = new Headers(options?.headers)

  if (options?.body && !(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json")
  }

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    })

    if (!response.ok) {
      let errorDetails: unknown = null
      let errorMessage = `HTTP Error ${response.status}: ${response.statusText}`

      try {
        errorDetails = await response.json()
        if (typeof errorDetails === "object" && errorDetails !== null) {
          const det = errorDetails as { detail?: string; message?: string }
          if (det.detail) {
            errorMessage = typeof det.detail === "string" ? det.detail : JSON.stringify(det.detail)
          } else if (det.message) {
            errorMessage = det.message
          }
        }
      } catch {
        // Response was not JSON
      }

      throw new ApiError(response.status, response.statusText, errorMessage, errorDetails)
    }

    // Handle 204 No Content
    if (response.status === 204) {
      return {} as T
    }

    // Safety guard: If server sent HTML (e.g. index.html SPA rewrite), throw explicit error
    const contentType = response.headers.get("content-type") || ""
    if (contentType.includes("text/html")) {
      throw new ApiError(
        response.status,
        "HtmlResponseError",
        `Expected JSON response from ${path}, but received an HTML document. The backend API endpoint may be unreachable or routing improperly.`
      )
    }

    return (await response.json()) as T
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }
    const message = error instanceof Error ? error.message : "Network request failed"
    throw new ApiError(0, "NetworkError", message, error)
  }
}

// ============================================================
// 1. HEALTH CHECKS
// ============================================================

/**
 * Health check: GET /health
 */
export async function getHealth(): Promise<HealthStatusResponse> {
  return request<HealthStatusResponse>("/health")
}

/**
 * Health check: GET /api/health
 */
export async function getApiHealth(): Promise<HealthStatusResponse> {
  return request<HealthStatusResponse>("/api/health")
}

// ============================================================
// 2. DASHBOARD & CASES
// ============================================================

/**
 * Live KPI ledger: GET /dashboard/stats
 */
export async function getDashboardStats(): Promise<DashboardStats> {
  return request<DashboardStats>("/dashboard/stats")
}

/**
 * Latest cases feed: GET /dashboard/cases?limit={limit}
 */
export async function getDashboardCases(limit: number = 30): Promise<Case[]> {
  return request<Case[]>(`/dashboard/cases?limit=${encodeURIComponent(limit)}`)
}

// ============================================================
// 3. CUSTOMER 360° DIRECTORY
// ============================================================

/**
 * Customers list with CRM and recovery stats: GET /api/customers
 */
export async function getCustomers(): Promise<CustomerSummary[]> {
  return request<CustomerSummary[]>("/api/customers")
}

// ============================================================
// 4. RECOVERY FUNNEL & ANALYTICS
// ============================================================

/**
 * Aggregated funnel, channels, gateways, and failure codes: GET /api/analytics
 */
export async function getAnalytics(): Promise<AnalyticsData> {
  return request<AnalyticsData>("/api/analytics")
}

/**
 * Analytics summary stats: GET /api/analytics/summary
 */
export async function getAnalyticsSummary(): Promise<DashboardStats> {
  return request<DashboardStats>("/api/analytics/summary")
}

/**
 * Failure breakdown by root cause: GET /api/analytics/by-reason
 */
export async function getAnalyticsByReason(): Promise<AnalyticsFailureCodes> {
  return request<AnalyticsFailureCodes>("/api/analytics/by-reason")
}

// ============================================================
// 5. AUDIT LOGS & ADMIN CONTROLS
// ============================================================

/**
 * Outbound communication audit logs: GET /admin/action-logs?limit={limit}
 */
export async function getActionLogs(limit: number = 50): Promise<ActionLog[]> {
  return request<ActionLog[]>(`/admin/action-logs?limit=${encodeURIComponent(limit)}`)
}

/**
 * 1-Click Simulation trigger: POST /admin/simulate?scenario={scenario}
 */
export async function simulateScenario(
  scenario: SimulationScenario = "high_ltv_insufficient_funds"
): Promise<SimulateScenarioResponse> {
  return request<SimulateScenarioResponse>(
    `/admin/simulate?scenario=${encodeURIComponent(scenario)}`,
    {
      method: "POST",
    }
  )
}

/**
 * Trigger background worker cycle: POST /admin/process
 */
export async function triggerManualProcess(): Promise<ManualProcessResponse> {
  return request<ManualProcessResponse>("/admin/process", {
    method: "POST",
  })
}

/**
 * Manually mark case as resolved: POST /admin/resolve/{case_id}
 */
export async function resolveCaseManually(caseId: number): Promise<CaseResolutionResult> {
  return request<CaseResolutionResult>(`/admin/resolve/${encodeURIComponent(caseId)}`, {
    method: "POST",
  })
}

/**
 * Trigger simulated recovery: POST /api/simulate/recovery?scenario={scenario}
 */
export async function simulateRecovery(
  scenario: string = "payment_succeeded"
): Promise<SimulateScenarioResponse> {
  return request<SimulateScenarioResponse>(
    `/api/simulate/recovery?scenario=${encodeURIComponent(scenario)}`,
    {
      method: "POST",
    }
  )
}

// ============================================================
// 6. INBOUND WEBHOOKS
// ============================================================

/**
 * Ingest PSP webhook (Stripe & Razorpay): POST /webhooks/psp
 */
export async function ingestPSPWebhook(
  payload: Record<string, unknown>
): Promise<PSPWebhookResponse> {
  return request<PSPWebhookResponse>("/webhooks/psp", {
    method: "POST",
    body: JSON.stringify(payload),
  })
}

/**
 * Ingest ERP / billing invoice webhook: POST /webhooks/billing
 */
export async function ingestBillingWebhook(
  payload: BillingWebhookPayload
): Promise<BillingWebhookResponse> {
  return request<BillingWebhookResponse>("/webhooks/billing", {
    method: "POST",
    body: JSON.stringify(payload),
  })
}

/**
 * Seed database with sample customer directory and demo scenarios: POST /admin/seed
 */
export async function seedDatabase(): Promise<{ status: string; message: string }> {
  return request<{ status: string; message: string }>("/admin/seed", {
    method: "POST",
  })
}

// ============================================================
// 7. TRACK 03: RAZORPAY DETECTOR, BATCH RUNNER & EXCEPTIONS
// ============================================================

/**
 * Poll live Razorpay test-mode API: GET /payments/detect?hours_back={hours}
 */
export async function detectLivePayments(hours: number = 24): Promise<import("@/types/api").DetectorData> {
  return request<import("@/types/api").DetectorData>(`/payments/detect?hours_back=${hours}`)
}

/**
 * Ingest live payment from detector feed and execute autonomous recovery: POST /payments/ingest-live
 */
export async function ingestLivePayment(paymentData: Record<string, unknown>): Promise<any> {
  return request<any>("/payments/ingest-live", {
    method: "POST",
    body: JSON.stringify(paymentData),
  })
}

/**
 * Sync status of all pending Razorpay links: POST /payments/sync-links
 */
export async function syncPaidLinks(): Promise<{
  links_checked: number
  newly_recovered: number
  money_recovered: number
}> {
  return request<{
    links_checked: number
    newly_recovered: number
    money_recovered: number
  }>("/payments/sync-links", {
    method: "POST",
  })
}

/**
 * Fetch Honest Exception List: GET /payments/exceptions
 */
export async function fetchHonestExceptions(): Promise<import("@/types/api").ExceptionsResponse> {
  return request<import("@/types/api").ExceptionsResponse>("/payments/exceptions")
}

/**
 * Run autonomous recovery batch with stopping rules: POST /agent/run-batch?count={count}
 */
export async function runBatchRecovery(count: number = 60): Promise<import("@/types/api").BatchRunResponse> {
  return request<import("@/types/api").BatchRunResponse>(`/agent/run-batch?count=${count}`, {
    method: "POST",
  })
}

/**
 * Fetch historical batch runs: GET /agent/runs
 */
export async function fetchBatchRuns(): Promise<import("@/types/api").BatchRun[]> {
  return request<import("@/types/api").BatchRun[]>("/agent/runs")
}

/**
 * Fetch specific batch run details: GET /agent/runs/{run_id}
 */
export async function fetchBatchRunDetails(runId: string): Promise<import("@/types/api").BatchRun> {
  return request<import("@/types/api").BatchRun>(`/agent/runs/${runId}`)
}

/**
 * 1-Click single payment recovery: POST /payments/{id}/recover
 */
export async function recoverPayment(id: string): Promise<any> {
  return request<any>(`/payments/${id}/recover`, {
    method: "POST",
  })
}

/**
 * Fetch payments transaction ledger: GET /payments/
 */
export async function fetchPaymentsList(
  status?: string,
  search?: string,
  limit: number = 150
): Promise<import("@/types/api").PaymentTransaction[]> {
  const params = new URLSearchParams()
  if (status && status !== "ALL") params.append("status", status)
  if (search && search.trim()) params.append("search", search.trim())
  if (limit) params.append("limit", limit.toString())
  const qs = params.toString() ? `?${params.toString()}` : ""
  return request<import("@/types/api").PaymentTransaction[]>(`/payments/${qs}`)
}

/**
 * Default grouped export for ergonomic consumption
 */
export const api = {
  getHealth,
  getApiHealth,
  getDashboardStats,
  getDashboardCases,
  getCustomers,
  getAnalytics,
  getAnalyticsSummary,
  getAnalyticsByReason,
  getActionLogs,
  simulateScenario,
  triggerManualProcess,
  resolveCaseManually,
  simulateRecovery,
  ingestPSPWebhook,
  ingestBillingWebhook,
  seedDatabase,
  detectLivePayments,
  ingestLivePayment,
  syncPaidLinks,
  fetchHonestExceptions,
  runBatchRecovery,
  fetchBatchRuns,
  fetchBatchRunDetails,
  recoverPayment,
  fetchPaymentsList,
}

