import React, { useState, useEffect } from "react"
import { Search, Inbox } from "lucide-react"
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card"
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Skeleton } from "@/components/ui/skeleton"
import { formatMoney, formatDate, cn } from "@/lib/utils"
import type { Case, CaseStatus } from "@/types/api"

interface CasesLedgerProps {
  cases: Case[]
  selectedCaseId: number | null
  onSelectCase: (caseId: number) => void
  loading?: boolean
  initialSearch?: string
}

export function getStatusBadge(status: CaseStatus) {
  switch (status) {
    case "resolved":
      return (
        <Badge
          variant="outline"
          className="border-emerald-500/30 bg-emerald-50 font-mono text-[10px] font-semibold text-emerald-600 dark:bg-emerald-950/40 dark:text-emerald-400"
        >
          Recovered
        </Badge>
      )
    case "escalated":
      return (
        <Badge
          variant="destructive"
          className="bg-destructive/15 font-mono text-[10px] font-semibold text-destructive"
        >
          Escalated
        </Badge>
      )
    case "retrying":
      return (
        <Badge
          variant="outline"
          className="border-amber-500/30 bg-amber-50 font-mono text-[10px] font-semibold text-amber-600 dark:bg-amber-950/40 dark:text-amber-400"
        >
          Retrying
        </Badge>
      )
    case "awaiting_input":
      return (
        <Badge
          variant="secondary"
          className="border-border bg-muted font-mono text-[10px] font-semibold text-muted-foreground"
        >
          Awaiting Action
        </Badge>
      )
    case "diagnosing":
      return (
        <Badge
          variant="secondary"
          className="border-border bg-muted font-mono text-[10px] font-semibold text-muted-foreground"
        >
          Diagnosing
        </Badge>
      )
    default:
      return (
        <Badge variant="outline" className="border-border font-mono text-[10px] text-muted-foreground">
          {status}
        </Badge>
      )
  }
}

export const CasesLedger: React.FC<CasesLedgerProps> = ({
  cases,
  selectedCaseId,
  onSelectCase,
  loading = false,
  initialSearch = "",
}) => {
  const [search, setSearch] = useState(initialSearch)

  useEffect(() => {
    if (initialSearch) {
      setSearch(initialSearch)
    }
  }, [initialSearch])

  const filteredCases = cases.filter((c) => {
    const q = search.toLowerCase()
    return (
      c.case_id.toString().includes(q) ||
      c.customer_id.toLowerCase().includes(q) ||
      c.case_type.toLowerCase().includes(q) ||
      c.status.toLowerCase().includes(q) ||
      (c.llm_reasoning && c.llm_reasoning.toLowerCase().includes(q))
    )
  })

  return (
    <Card className="flex flex-col border-border/80 bg-card shadow-xs">
      <CardHeader className="border-b border-border/60 pb-3.5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <CardTitle className="text-base font-bold">Recovery Cases Feed</CardTitle>
            <CardDescription className="text-xs">
              Live stream of payment recovery cases with automated retry schedules and AI insights.
            </CardDescription>
          </div>
          <Badge variant="secondary" className="border border-border/80 font-mono text-xs font-semibold">
            {cases.length} Total Cases
          </Badge>
        </div>

        {/* Search Bar */}
        <div className="relative mt-2">
          <Search className="absolute top-1/2 left-2.5 size-3.5 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search by ID, customer, status, or failure reason..."
            aria-label="Search cases by ID, customer name, or status"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="h-8.5 bg-muted/30 pl-8 text-xs shadow-2xs"
          />
        </div>
      </CardHeader>

      <CardContent className="p-0">
        <div className="max-h-[560px] overflow-auto">
          <Table className="min-w-[640px]">
            <TableHeader className="sticky top-0 z-10 bg-muted/90 backdrop-blur-xs">
              <TableRow>
                <TableHead className="w-16 font-mono text-[11px] font-bold">Case #</TableHead>
                <TableHead className="font-mono text-[11px] font-bold">Customer & Type</TableHead>
                <TableHead className="font-mono text-[11px] font-bold">Amount</TableHead>
                <TableHead className="font-mono text-[11px] font-bold">Status</TableHead>
                <TableHead className="font-mono text-[11px] font-bold">AI Diagnostics / Action</TableHead>
                <TableHead className="font-mono text-[11px] font-bold">Next Action</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                [...Array(6)].map((_, i) => (
                  <TableRow key={i}>
                    <TableCell><Skeleton className="h-4 w-10" /></TableCell>
                    <TableCell><Skeleton className="h-4 w-28" /></TableCell>
                    <TableCell><Skeleton className="h-4 w-14" /></TableCell>
                    <TableCell><Skeleton className="h-5 w-20" /></TableCell>
                    <TableCell><Skeleton className="h-4 w-48" /></TableCell>
                    <TableCell><Skeleton className="h-4 w-24" /></TableCell>
                  </TableRow>
                ))
              ) : filteredCases.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="h-32 text-center">
                    <div className="flex flex-col items-center justify-center gap-1.5 text-muted-foreground">
                      <Inbox className="size-6 text-muted-foreground/50" />
                      <p className="text-xs font-medium">No matching cases in ledger.</p>
                    </div>
                  </TableCell>
                </TableRow>
              ) : (
                filteredCases.map((c) => {
                  const isSelected = c.case_id === selectedCaseId
                  return (
                    <TableRow
                      key={c.case_id}
                      tabIndex={0}
                      role="button"
                      aria-selected={isSelected}
                      onClick={() => onSelectCase(c.case_id)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter" || e.key === " ") {
                          e.preventDefault()
                          onSelectCase(c.case_id)
                        }
                      }}
                      className={cn(
                        "cursor-pointer transition-colors hover:bg-muted/50 focus-visible:outline-hidden focus-visible:bg-muted/70",
                        isSelected && "bg-muted/80 font-medium"
                      )}
                    >
                      <TableCell className="font-mono text-xs font-bold text-muted-foreground">
                        #{c.case_id}
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-col">
                          <span className="font-bold text-xs text-foreground">{c.customer_id}</span>
                          <span className="text-[11px] text-muted-foreground">{c.case_type}</span>
                        </div>
                      </TableCell>
                      <TableCell className="font-mono text-xs font-bold text-foreground">
                        {formatMoney(c.amount_usd)}
                      </TableCell>
                      <TableCell>
                        {getStatusBadge(c.status)}
                      </TableCell>
                      <TableCell className="max-w-[260px] truncate text-xs text-muted-foreground">
                        {c.llm_reasoning || c.last_action || "—"}
                      </TableCell>
                      <TableCell className="font-mono text-[11px] text-muted-foreground whitespace-nowrap">
                        {formatDate(c.scheduled_next_action_at)}
                      </TableCell>
                    </TableRow>
                  )
                })
              )}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  )
}
