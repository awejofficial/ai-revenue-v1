// frontend/src/types/api.ts

/**
 * System Health Response
 */
export interface HealthStatusResponse {
  message: string
  status: string
  version: string
  docs: string
  dashboard: string
}

/**
 * Real-time Dashboard KPI Ledger
 */
export interface DashboardStats {
  total_cases: number
  in_progress_cases: number
  resolved_cases: number
  escalated_cases: number
  at_risk: number
  recovered: number
  escalated: number
  recovery_rate: number
}

/**
 * Case Lifecycle State
 */
export type CaseStatus =
  | "new"
  | "diagnosing"
  | "retrying"
  | "awaiting_input"
  | "resolved"
  | "escalated"
  | string

/**
 * Case Record
 */
export interface Case {
  case_id: number
  event_id?: string
  payment_id?: string
  customer_id: string
  case_type: string
  status: CaseStatus
  amount_usd: number
  currency?: string
  root_cause?: string | null
  recovery_action?: string | null
  payment_link_id?: string | null
  recovery_message?: string | null
  current_retry_count: number
  max_retries: number
  last_action: string | null
  scheduled_next_action_at: string | null
  llm_reasoning: string | null
  created_at: string
  updated_at: string
}

/**
 * Payment Transaction Record (Image 3)
 */
export interface PaymentTransaction {
  id: string
  payment_id: string
  case_id: number
  customer_email: string
  amount: number
  currency: string
  status: string
  root_cause: string
  recovery_action: string
  gemini_reasoning: string
  recovery_message: string
  payment_link_id?: string | null
  retry_count: number
  created_at: string | null
}

/**
 * Customer Segment Type
 */
export type CustomerSegment =
  | "high_ltv"
  | "enterprise"
  | "standard"
  | "trial"
  | string

/**
 * Customer 360 Summary Record
 */
export interface CustomerSummary {
  customer_id: string
  name: string
  company: string
  email: string | null
  phone: string | null
  ltv: number
  segment: CustomerSegment
  plan: string
  country: string
  cart_items: string[]
  cart_value: number
  cases_count: number
  resolved_count: number
  in_progress_count: number
  recovered_amount: number
  last_status: string
  contact_preferences?: {
    email?: boolean
    sms?: boolean
    slack?: boolean
  } | null
}

/**
 * Funnel Stage Telemetry
 */
export interface AnalyticsFunnel {
  detected: number
  diagnosed: number
  outreach_dispatched: number
  recovered_cases: number
  escalated_cases: number
  at_risk_amount: number
  recovered_amount: number
  recovery_rate_pct: number
}

/**
 * Channel Distribution Counts
 */
export interface AnalyticsChannels {
  email: number
  sms: number
  slack: number
  razorpay: number
  stripe: number
}

/**
 * Failure Code Root Cause Counts
 */
export interface AnalyticsFailureCodes {
  insufficient_funds: number
  card_expired: number
  checkout_drop_off: number
  suspected_fraud: number
  other: number
  [key: string]: number
}

/**
 * Gateway Configuration Status
 */
export interface GatewayInfo {
  name: string
  currency: string
  status: string
}

/**
 * Aggregated Analytics Payload
 */
export interface AnalyticsData {
  funnel: AnalyticsFunnel
  channels: AnalyticsChannels
  failure_codes: AnalyticsFailureCodes
  gateways: {
    stripe: GatewayInfo
    razorpay: GatewayInfo
    [key: string]: GatewayInfo
  }
}

/**
 * Action Audit Log Entry
 */
export interface ActionLog {
  id: number
  case_id: number | null
  customer_id: string
  action_type: string
  channel: string
  recipient: string | null
  status: string
  details: string | Record<string, unknown> | null
  created_at: string
}

/**
 * Case Resolution Result
 */
export interface CaseResolutionResult {
  success: boolean
  case_id?: number
  recovered_amount?: number
  reason?: string
}

/**
 * PSP Ingestion Response
 */
export interface PSPWebhookResponse {
  status: "auto_resolved" | "success_event_recorded" | "ingested" | string
  resolution?: CaseResolutionResult
  message?: string
  event_id?: string
  customer_id?: string
}

/**
 * Billing Overdue Invoice Webhook Payload
 */
export interface BillingWebhookPayload {
  customer_id: string
  invoice_id: string
  amount_due: number
  currency?: string
  days_overdue?: number
}

/**
 * Billing Webhook Response
 */
export interface BillingWebhookResponse {
  status: "ingested" | string
  event_id: string
}

/**
 * 1-Click Simulation Scenario Options
 */
export type SimulationScenario =
  | "high_ltv_insufficient_funds"
  | "checkout_drop_off"
  | "repeat_failure"
  | "expired_card"
  | "fraud"
  | "trial_user"
  | "payment_succeeded"

/**
 * Simulation Response
 */
export interface SimulateScenarioResponse {
  status: "simulated_and_processed" | "simulated_success" | "no_open_cases" | string
  scenario?: string
  event_id?: string
  customer_id?: string
  message?: string
  result?: CaseResolutionResult
}

/**
 * Manual Process Trigger Response
 */
export interface ManualProcessResponse {
  status: "processing_completed" | string
}

/**
 * Razorpay Live Detector Models
 */
export interface FailedPayment {
  id: string
  amount: number
  currency: string
  status: string
  error_code: string
  error_description: string
  email: string
  contact: string
  method: string
  created_at: string
}

export interface AtRiskPayment {
  id: string
  amount: number
  currency: string
  status: string
  risk: string
  method: string
  created_at: string
}

export interface DetectorData {
  source: string
  polled_at: string
  hours_back: number
  total_fetched: number
  failed_count: number
  authorized_not_captured: number
  captured_count: number
  failed_payments: FailedPayment[]
  at_risk_payments: AtRiskPayment[]
  error?: string
  note?: string
}

/**
 * Honest Exception List Models
 */
export interface ExceptionPayment {
  id: string
  case_id: number
  amount: number
  currency: string
  status: string
  recovery_action: string
  gemini_reasoning: string
  recovery_message: string
  payment_link_id?: string | null
  retry_count: number
  customer_email: string
  created_at: string
}

export interface ExceptionGroup {
  root_cause: string
  count: number
  total_value: number
  payments: ExceptionPayment[]
}

export interface ExceptionsResponse {
  total_exceptions: number
  total_value_at_risk: number
  by_cause: ExceptionGroup[]
}

/**
 * Batch Run Record
 */
export interface BatchRun {
  run_id: string
  total: number
  recovered: number
  escalated: number
  failed: number
  skipped: number
  money_recovered: number
  recovery_rate: number
  stopped_early: boolean
  stopped_at_index: number | null
  started_at: string
  completed_at: string | null
}

export interface BatchRunResponse {
  run_id: string
  total: number
  recovered: number
  escalated: number
  failed: number
  skipped: number
  money_recovered: number
  recovery_rate: number
  stopped_early: boolean
  stopped_at_index: number | null
}

