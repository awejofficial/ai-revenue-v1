// frontend/src/components/dashboard/RecentLogsCard.tsx

import React, { useState, useEffect, useMemo, useRef, useCallback } from "react"
import {
  Download,
  Search,
  RefreshCw,
  FileText,
  Mail,
  MessageSquare,
  Send,
  CreditCard,
  CheckCircle2,
  AlertCircle,
  Clock,
  Filter,
  X,
} from "lucide-react"
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Spinner } from "@/components/ui/spinner"
import { api } from "@/lib/api"
import { formatDate, cn } from "@/lib/utils"
import { toast } from "sonner"
import type { ActionLog } from "@/types/api"

interface RecentLogsCardProps {
  className?: string
}

const CHANNELS = [
  { id: "all", label: "All Channels" },
  { id: "email", label: "Email" },
  { id: "sms", label: "SMS" },
  { id: "slack", label: "Slack" },
  { id: "stripe", label: "Stripe" },
  { id: "razorpay", label: "Razorpay" },
]

/**
 * Sanitizes a field against CSV Formula Injection (DDE injection in Excel / LibreOffice).
 * Strips or prefixes dangerous formula triggers (=, +, -, @, tab, return).
 */
function escapeAndSanitizeCsv(val: unknown): string {
  if (val === null || val === undefined) return '""'
  let str = String(val)
  // Prevent CSV Formula Injection
  if (/^[=+\-@\t\r]/.test(str)) {
    str = `'${str}`
  }
  return `"${str.replace(/"/g, '""')}"`
}

/**
 * Safely parses and formats log details into a human-readable string.
 */
function formatLogDetails(details: unknown, fallbackChannel: string, recipient?: string | null): string {
  if (!details) {
    return `Dispatched via ${fallbackChannel}${recipient ? ` to ${recipient}` : ""}`
  }

  if (typeof details === "string") {
    try {
      const parsed = JSON.parse(details)
      if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
        return Object.entries(parsed)
          .filter(([, v]) => v !== undefined && v !== null && v !== "")
          .map(([k, v]) => `${k.replace(/_/g, " ")}: ${typeof v === "object" ? JSON.stringify(v) : v}`)
          .join(" • ")
      }
    } catch {
      // Plain text string
      return details
    }
    return details
  }

  if (typeof details === "object" && !Array.isArray(details)) {
    return Object.entries(details as Record<string, unknown>)
      .filter(([, v]) => v !== undefined && v !== null && v !== "")
      .map(([k, v]) => `${k.replace(/_/g, " ")}: ${typeof v === "object" ? JSON.stringify(v) : v}`)
      .join(" • ")
  }

  return String(details)
}

export const RecentLogsCard: React.FC<RecentLogsCardProps> = ({ className }) => {
  const [logs, setLogs] = useState<ActionLog[]>([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState("")
  const [channelFilter, setChannelFilter] = useState<string>("all")

  const abortControllerRef = useRef<AbortController | null>(null)

  const fetchLogs = useCallback(async (isSilent = false) => {
    // Abort previous in-flight request to avoid race conditions
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }
    abortControllerRef.current = new AbortController()

    try {
      if (!isSilent) setRefreshing(true)
      setError(null)
      const data = await api.getActionLogs(100)
      setLogs(data)
    } catch (err) {
      if (err instanceof Error && err.name === "AbortError") {
        return
      }
      console.error("Failed to load action logs:", err)
      setError("Unable to sync recent communications.")
      if (!isSilent) toast.error("Failed to fetch recent communication logs")
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [])

  // Page Visibility API aware polling: pauses when tab is hidden to conserve resources
  useEffect(() => {
    fetchLogs(true)

    let interval: ReturnType<typeof setInterval> | null = null

    const startInterval = () => {
      if (!interval) {
        interval = setInterval(() => {
          if (document.visibilityState === "visible") {
            fetchLogs(true)
          }
        }, 15000)
      }
    }

    const handleVisibilityChange = () => {
      if (document.visibilityState === "visible") {
        fetchLogs(true)
        startInterval()
      } else if (interval) {
        clearInterval(interval)
        interval = null
      }
    }

    startInterval()
    document.addEventListener("visibilitychange", handleVisibilityChange)

    return () => {
      if (interval) clearInterval(interval)
      if (abortControllerRef.current) abortControllerRef.current.abort()
      document.removeEventListener("visibilitychange", handleVisibilityChange)
    }
  }, [fetchLogs])

  // Filter logs by search query and channel
  const filteredLogs = useMemo(() => {
    const searchLower = searchTerm.trim().toLowerCase()

    return logs.filter((log) => {
      const matchesChannel =
        channelFilter === "all" ||
        (log.channel && log.channel.toLowerCase().includes(channelFilter.toLowerCase()))

      if (!matchesChannel) return false
      if (!searchLower) return true

      const formattedDetails = formatLogDetails(log.details, log.channel, log.recipient).toLowerCase()

      return (
        log.customer_id.toLowerCase().includes(searchLower) ||
        (log.action_type && log.action_type.toLowerCase().includes(searchLower)) ||
        (log.recipient && log.recipient.toLowerCase().includes(searchLower)) ||
        (log.channel && log.channel.toLowerCase().includes(searchLower)) ||
        (log.status && log.status.toLowerCase().includes(searchLower)) ||
        formattedDetails.includes(searchLower) ||
        (log.case_id !== null && log.case_id.toString().includes(searchLower))
      )
    })
  }, [logs, searchTerm, channelFilter])

  // Memory-safe, formula-injection-hardened CSV export via Blob
  const handleExportCSV = useCallback(() => {
    if (filteredLogs.length === 0) {
      toast.info("No logs available to export for the current filters.")
      return
    }

    try {
      const headers = [
        "Log ID",
        "Case ID",
        "Customer ID",
        "Action Type",
        "Channel",
        "Recipient",
        "Status",
        "Details",
        "Timestamp",
      ]

      const csvRows = [
        headers.join(","),
        ...filteredLogs.map((log) => {
          const detailsText = formatLogDetails(log.details, log.channel, log.recipient)

          return [
            escapeAndSanitizeCsv(log.id),
            escapeAndSanitizeCsv(log.case_id),
            escapeAndSanitizeCsv(log.customer_id),
            escapeAndSanitizeCsv(log.action_type),
            escapeAndSanitizeCsv(log.channel),
            escapeAndSanitizeCsv(log.recipient),
            escapeAndSanitizeCsv(log.status),
            escapeAndSanitizeCsv(detailsText),
            escapeAndSanitizeCsv(log.created_at),
          ].join(",")
        }),
      ]

      const csvContent = csvRows.join("\r\n")
      const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" })
      const url = URL.createObjectURL(blob)

      const link = document.createElement("a")
      link.setAttribute("href", url)
      const filename = `recovery_action_logs_${new Date().toISOString().slice(0, 10)}.csv`
      link.setAttribute("download", filename)
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)

      toast.success(`Exported ${filteredLogs.length} audit logs to ${filename}`)
    } catch (err) {
      console.error("Export CSV error:", err)
      toast.error("Failed to generate CSV export file.")
    }
  }, [filteredLogs])

  const getChannelIcon = (channel: string) => {
    const ch = channel.toLowerCase()
    if (ch.includes("email") || ch.includes("sendgrid")) {
      return <Mail className="size-3.5" />
    }
    if (ch.includes("sms") || ch.includes("twilio")) {
      return <MessageSquare className="size-3.5" />
    }
    if (ch.includes("slack")) {
      return <Send className="size-3.5" />
    }
    if (ch.includes("stripe") || ch.includes("razorpay")) {
      return <CreditCard className="size-3.5" />
    }
    return <FileText className="size-3.5" />
  }

  const getStatusBadge = (status: string) => {
    const st = status.toLowerCase()
    if (st.includes("sent") || st.includes("delivered") || st.includes("success") || st.includes("created")) {
      return (
        <Badge
          variant="outline"
          className="border-primary/20 bg-primary/5 text-[10px] font-semibold text-foreground"
        >
          <CheckCircle2 data-icon="inline-start" className="size-2.5" />
          {status}
        </Badge>
      )
    }
    if (st.includes("failed") || st.includes("error") || st.includes("undelivered")) {
      return (
        <Badge
          variant="destructive"
          className="text-[10px] font-semibold"
        >
          <AlertCircle data-icon="inline-start" className="size-2.5" />
          {status}
        </Badge>
      )
    }
    return (
      <Badge variant="secondary" className="text-[10px] font-semibold">
        <Clock data-icon="inline-start" className="size-2.5" />
        {status}
      </Badge>
    )
  }

  return (
    <Card className={cn("border-border bg-card shadow-xs", className)}>
      <CardHeader className="border-b border-border/60 p-4 sm:p-5">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <FileText className="size-4.5 text-foreground" />
              <CardTitle className="text-base font-bold tracking-tight text-foreground sm:text-lg">
                Outreach & Notification Logs
              </CardTitle>
            </div>
            <CardDescription className="text-xs text-muted-foreground">
              Real-time audit log of dispatched emails, SMS messages, Slack alerts, and payment links.
            </CardDescription>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => fetchLogs(false)}
              disabled={refreshing}
              aria-label="Refresh operational logs"
              className="h-8.5 min-h-[34px] gap-1.5 rounded-lg border-border text-xs font-semibold"
            >
              {refreshing ? <Spinner data-icon="inline-start" /> : <RefreshCw data-icon="inline-start" className="size-3.5" />}
              Refresh
            </Button>

            <Button
              variant="default"
              size="sm"
              onClick={handleExportCSV}
              disabled={filteredLogs.length === 0}
              aria-label={`Export ${filteredLogs.length} logs to CSV`}
              className="h-8.5 min-h-[34px] gap-1.5 rounded-lg bg-foreground text-background text-xs font-semibold shadow-xs hover:bg-foreground/90"
            >
              <Download data-icon="inline-start" className="size-3.5" />
              Export CSV ({filteredLogs.length})
            </Button>
          </div>
        </div>

        {/* Search & Channel Filter Controls */}
        <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center">
          {/* Accessible Search Input */}
          <div className="relative min-w-[200px] flex-1">
            <Search className="absolute left-2.5 top-1/2 size-3.5 -translate-y-1/2 text-muted-foreground pointer-events-none" />
            <Input
              id="recent-logs-search"
              aria-label="Search logs by customer ID, case number, recipient, or details"
              placeholder="Search by customer, case #, recipient, details..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="h-8.5 pl-8 text-xs min-h-[34px]"
            />
            {searchTerm && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setSearchTerm("")}
                aria-label="Clear search query"
                className="absolute right-1 top-1/2 size-6 -translate-y-1/2 p-0 text-muted-foreground hover:text-foreground"
              >
                <X className="size-3" />
              </Button>
            )}
          </div>

          {/* Accessible Channel Filter Chips */}
          <div
            role="group"
            aria-label="Filter logs by communication channel"
            className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0"
          >
            <Filter className="size-3 text-muted-foreground shrink-0 mr-0.5" />
            {CHANNELS.map((ch) => {
              const isSelected = channelFilter === ch.id
              return (
                <Button
                  key={ch.id}
                  variant={isSelected ? "default" : "outline"}
                  size="sm"
                  aria-pressed={isSelected}
                  onClick={() => setChannelFilter(ch.id)}
                  className={cn(
                    "h-8 min-h-[32px] px-2.5 text-[11px] font-medium capitalize rounded-md transition-colors",
                    isSelected
                      ? "bg-foreground text-background shadow-2xs"
                      : "border-border text-muted-foreground hover:text-foreground hover:bg-muted"
                  )}
                >
                  {ch.label}
                </Button>
              )
            })}
          </div>
        </div>
      </CardHeader>

      <CardContent className="p-0">
        {loading ? (
          <div className="flex h-48 flex-col items-center justify-center gap-2 text-muted-foreground">
            <Spinner className="size-6" />
            <span className="text-xs">Loading operational logs...</span>
          </div>
        ) : error ? (
          <div className="flex h-48 flex-col items-center justify-center p-6 text-center text-muted-foreground">
            <AlertCircle className="size-8 text-destructive mb-2 opacity-80" />
            <p className="text-xs font-semibold text-foreground">{error}</p>
            <p className="text-[11px] text-muted-foreground mt-0.5 mb-3">
              Unable to establish real-time sync with database.
            </p>
            <Button
              variant="outline"
              size="sm"
              onClick={() => fetchLogs(false)}
              className="h-8 gap-1.5 text-xs font-semibold"
            >
              <RefreshCw data-icon="inline-start" className="size-3.5" />
              Retry Connection
            </Button>
          </div>
        ) : filteredLogs.length === 0 ? (
          <div className="flex h-48 flex-col items-center justify-center p-6 text-center text-muted-foreground">
            <FileText className="size-8 opacity-40 mb-2" />
            <p className="text-xs font-semibold text-foreground">No logs match your criteria</p>
            <p className="text-[11px] text-muted-foreground mt-0.5">
              {searchTerm || channelFilter !== "all"
                ? "Try adjusting your search keywords or channel filters."
                : "Trigger a recovery simulation above to generate live communication entries."}
            </p>
          </div>
        ) : (
          <div
            tabIndex={0}
            role="region"
            aria-label="Recent activity logs stream"
            className="max-h-[380px] overflow-y-auto focus-visible:outline-hidden focus-visible:ring-1 focus-visible:ring-ring"
          >
            <ul role="list" className="divide-y divide-border/60">
              {filteredLogs.map((log) => {
                const detailsText = formatLogDetails(log.details, log.channel, log.recipient)

                return (
                  <li
                    key={log.id}
                    className="flex flex-col gap-2 p-3.5 transition-colors hover:bg-muted/40 sm:flex-row sm:items-center sm:justify-between"
                  >
                    <div className="flex items-start gap-3 min-w-0 flex-1">
                      <div className="mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-lg border border-border/80 bg-muted/60 text-foreground">
                        {getChannelIcon(log.channel)}
                      </div>

                      <div className="space-y-0.5 min-w-0 flex-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="font-mono text-xs font-bold text-foreground">
                            {log.customer_id}
                          </span>
                          {log.case_id && (
                            <Badge variant="outline" className="border-border text-[10px] font-mono text-muted-foreground">
                              Case #{log.case_id}
                            </Badge>
                          )}
                          <span className="text-xs font-medium text-foreground">
                            {log.action_type.replace(/_/g, " ")}
                          </span>
                          {getStatusBadge(log.status)}
                        </div>

                        <p className="text-[11px] text-muted-foreground line-clamp-2 max-w-2xl">
                          {detailsText}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center justify-between sm:flex-col sm:items-end sm:justify-center shrink-0">
                      <span className="font-mono text-[10px] text-muted-foreground">
                        {formatDate(log.created_at)}
                      </span>
                      <span className="text-[10px] text-muted-foreground capitalize font-medium">
                        {log.channel}
                      </span>
                    </div>
                  </li>
                )
              })}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
