// frontend/src/components/customers/CustomerTable.tsx

import React from "react"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { formatMoney, cn } from "@/lib/utils"
import type { CustomerSummary, CustomerSegment } from "@/types/api"

interface CustomerTableProps {
  customers: CustomerSummary[]
  selectedCustomerId: string | null
  onSelectCustomer: (customerId: string) => void
  loading?: boolean
}

export function getSegmentBadge(segment: CustomerSegment) {
  switch (segment) {
    case "high_ltv":
      return (
        <Badge variant="outline" className="border-emerald-500/30 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
          High LTV
        </Badge>
      )
    case "enterprise":
      return (
        <Badge variant="secondary" className="border-blue-500/30 bg-blue-500/10 text-blue-600 dark:text-blue-400">
          Enterprise
        </Badge>
      )
    case "standard":
      return (
        <Badge variant="outline" className="border-border text-foreground">
          Standard
        </Badge>
      )
    case "trial":
      return (
        <Badge variant="outline" className="border-amber-500/30 bg-amber-500/10 text-amber-600 dark:text-amber-400">
          Free Trial
        </Badge>
      )
    default:
      return <Badge variant="outline">{segment}</Badge>
  }
}

export const CustomerTable: React.FC<CustomerTableProps> = ({
  customers,
  selectedCustomerId,
  onSelectCustomer,
  loading = false,
}) => {
  return (
    <Card className="flex flex-col border-border/80 bg-card shadow-xs">
      <CardHeader className="border-b border-border/60 pb-3">
        <div className="flex items-center justify-between gap-2">
          <div>
            <CardTitle className="text-base font-semibold">Customer Accounts Directory</CardTitle>
            <CardDescription className="text-xs">
              Directory list with failure risk and LTV classification
            </CardDescription>
          </div>
          <Badge variant="secondary" className="font-mono text-xs">
            {customers.length} accounts
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="p-0">
        <div className="max-h-[580px] overflow-auto">
          <Table className="min-w-[620px]">
            <TableHeader className="sticky top-0 z-10 bg-muted/80 backdrop-blur-xs">
              <TableRow className="hover:bg-transparent">
                <TableHead className="font-mono text-xs font-semibold">Customer</TableHead>
                <TableHead className="font-mono text-xs font-semibold">Segment</TableHead>
                <TableHead className="font-mono text-xs font-semibold">LTV</TableHead>
                <TableHead className="font-mono text-xs font-semibold">Plan</TableHead>
                <TableHead className="font-mono text-xs font-semibold text-center">Compliance / DND</TableHead>
                <TableHead className="font-mono text-xs font-semibold text-right">Recovered</TableHead>
              </TableRow>
            </TableHeader>

            <TableBody>
              {loading ? (
                [...Array(6)].map((_, i) => (
                  <TableRow key={i}>
                    <TableCell><Skeleton className="h-4 w-28" /></TableCell>
                    <TableCell><Skeleton className="h-5 w-16" /></TableCell>
                    <TableCell><Skeleton className="h-4 w-14" /></TableCell>
                    <TableCell><Skeleton className="h-4 w-16" /></TableCell>
                    <TableCell className="text-center"><Skeleton className="mx-auto h-5 w-16" /></TableCell>
                    <TableCell className="text-right"><Skeleton className="ml-auto h-4 w-14" /></TableCell>
                  </TableRow>
                ))
              ) : customers.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="py-12 text-center text-xs text-muted-foreground">
                    No matching customer accounts found.
                  </TableCell>
                </TableRow>
              ) : (
                customers.map((c) => {
                  const isSelected = c.customer_id === selectedCustomerId
                  const isSmsDnd = c.contact_preferences?.sms === false

                  return (
                    <TableRow
                      key={c.customer_id}
                      tabIndex={0}
                      role="button"
                      aria-selected={isSelected}
                      onClick={() => onSelectCustomer(c.customer_id)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter" || e.key === " ") {
                          e.preventDefault()
                          onSelectCustomer(c.customer_id)
                        }
                      }}
                      className={cn(
                        "cursor-pointer transition-colors hover:bg-muted/50 focus-visible:outline-hidden focus-visible:bg-muted/70",
                        isSelected && "border-l-4 border-l-primary bg-muted/70 font-medium"
                      )}
                    >
                      <TableCell className="py-3">
                        <div className="flex flex-col">
                          <span className="text-xs font-semibold text-foreground">{c.name}</span>
                          <span className="font-mono text-[11px] text-muted-foreground">
                            {c.customer_id} · {c.company}
                          </span>
                        </div>
                      </TableCell>

                      <TableCell className="py-3">
                        {getSegmentBadge(c.segment)}
                      </TableCell>

                      <TableCell className="py-3 font-mono text-xs font-semibold text-foreground">
                        {formatMoney(c.ltv)}
                      </TableCell>

                      <TableCell className="py-3 font-mono text-xs text-muted-foreground">
                        {c.plan}
                      </TableCell>

                      <TableCell className="py-3 text-center">
                        {isSmsDnd ? (
                          <Badge variant="outline" className="border-amber-500/30 bg-amber-500/10 text-amber-600 dark:text-amber-400">
                            SMS DND
                          </Badge>
                        ) : (
                          <Badge variant="outline" className="border-emerald-500/30 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
                            ALL OK
                          </Badge>
                        )}
                      </TableCell>

                      <TableCell className="py-3 text-right font-mono text-xs font-semibold text-emerald-600 dark:text-emerald-400">
                        {formatMoney(c.recovered_amount)}
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
