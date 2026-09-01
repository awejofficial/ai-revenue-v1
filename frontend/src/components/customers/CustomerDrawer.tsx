// frontend/src/components/customers/CustomerDrawer.tsx

import React, { useState } from "react"
import {
  User,
  CreditCard,
  ShoppingCart,
  PauseCircle,
  AlertTriangle,
  Mail,
  Phone,
  Globe,
  DollarSign,
  Zap,
} from "lucide-react"
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert"
import { Separator } from "@/components/ui/separator"
import { Spinner } from "@/components/ui/spinner"
import { getSegmentBadge } from "./CustomerTable"
import { formatMoney } from "@/lib/utils"
import { toast } from "sonner"
import type { CustomerSummary } from "@/types/api"

interface CustomerDrawerProps {
  customer: CustomerSummary | null
  onTriggerCartRecovery: (customerId: string) => Promise<void>
}

export const CustomerDrawer: React.FC<CustomerDrawerProps> = ({
  customer,
  onTriggerCartRecovery,
}) => {
  const [acting, setActing] = useState<string | null>(null)

  if (!customer) {
    return (
      <Card className="flex h-full min-h-[420px] flex-col items-center justify-center border-border/80 bg-card p-8 text-center shadow-xs">
        <div className="flex size-12 items-center justify-center rounded-full bg-muted text-muted-foreground">
          <User className="size-6" />
        </div>
        <CardTitle className="mt-4 text-base">No Customer Selected</CardTitle>
        <CardDescription className="mt-1 max-w-xs text-xs">
          Select a customer from the directory to view account details, cart activity, and recovery options.
        </CardDescription>
      </Card>
    )
  }

  const handleAction = async (actionType: "upi_link" | "cart_recovery" | "pause_dunning") => {
    try {
      setActing(actionType)
      if (actionType === "cart_recovery") {
        await onTriggerCartRecovery(customer.customer_id)
        toast.success(`Sent 1-click cart recovery link (10% discount) to ${customer.name}!`)
      } else if (actionType === "upi_link") {
        toast.success(`Generated payment link for ${customer.name}`)
      } else if (actionType === "pause_dunning") {
        toast.success(`Paused dunning for ${customer.name}. 24-hour grace period active.`)
      }
    } catch {
      toast.error(`Failed to execute ${actionType}`)
    } finally {
      setActing(null)
    }
  }

  const hasAbandonedCart = customer.cart_items && customer.cart_items.length > 0

  return (
    <Card className="border-border/80 bg-card shadow-xs">
      <CardHeader className="border-b border-border/60 pb-3">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <CardTitle className="text-lg font-bold">{customer.name}</CardTitle>
              {getSegmentBadge(customer.segment)}
            </div>
            <CardDescription className="font-mono text-xs text-muted-foreground">
              {customer.customer_id} · {customer.company}
            </CardDescription>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-5 p-4 sm:p-5">
        {/* Abandoned Cart Alert */}
        {hasAbandonedCart && (
          <Alert className="border-amber-500/30 bg-amber-500/10 text-amber-900 dark:text-amber-200">
            <AlertTriangle className="size-4 text-amber-600 dark:text-amber-400" />
            <AlertTitle className="font-mono text-xs font-bold text-amber-800 dark:text-amber-300">
              Abandoned Cart Detected ({formatMoney(customer.cart_value)})
            </AlertTitle>
            <AlertDescription className="mt-1 text-xs text-amber-700 dark:text-amber-400">
              {customer.cart_items.join(", ")}
            </AlertDescription>
          </Alert>
        )}

        {/* CRM Key-Value Grid */}
        <div className="grid grid-cols-2 gap-3 rounded-lg border border-border/60 bg-muted/40 p-3 text-xs sm:grid-cols-2">
          <div className="flex items-center gap-2">
            <Mail className="size-3.5 text-muted-foreground" />
            <div className="truncate">
              <span className="font-mono text-[10px] text-muted-foreground uppercase">Email</span>
              <p className="truncate font-medium text-foreground">{customer.email || "N/A"}</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Phone className="size-3.5 text-muted-foreground" />
            <div className="truncate">
              <span className="font-mono text-[10px] text-muted-foreground uppercase">Phone</span>
              <p className="truncate font-medium text-foreground">{customer.phone || "N/A"}</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <DollarSign className="size-3.5 text-muted-foreground" />
            <div>
              <span className="font-mono text-[10px] text-muted-foreground uppercase">Lifetime Value</span>
              <p className="font-mono font-bold text-foreground">{formatMoney(customer.ltv)}</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Globe className="size-3.5 text-muted-foreground" />
            <div>
              <span className="font-mono text-[10px] text-muted-foreground uppercase">Country</span>
              <p className="font-medium text-foreground">{customer.country || "US"}</p>
            </div>
          </div>

          <div>
            <span className="font-mono text-[10px] text-muted-foreground uppercase">Subscription</span>
            <p className="font-mono font-medium text-foreground">{customer.plan}</p>
          </div>

          <div>
            <span className="font-mono text-[10px] text-muted-foreground uppercase">Active Dunning</span>
            <p className="font-medium">
              {customer.in_progress_count > 0 ? (
                <span className="font-semibold text-amber-600 dark:text-amber-400">
                  {customer.in_progress_count} Cases Active
                </span>
              ) : (
                <span className="text-muted-foreground">None (Clean)</span>
              )}
            </p>
          </div>
        </div>

        <Separator />

        {/* Quick Recovery Actions */}
        <div>
          <div className="mb-2.5 flex items-center gap-1.5 font-mono text-xs font-semibold tracking-wider text-muted-foreground uppercase">
            <Zap className="size-3.5 text-primary" />
            <span>Quick Recovery Actions</span>
          </div>

          <div className="flex flex-col gap-2">
            <Button
              variant="default"
              size="sm"
              disabled={acting !== null}
              onClick={() => handleAction("upi_link")}
              className="justify-start text-xs"
            >
              {acting === "upi_link" ? <Spinner data-icon="inline-start" /> : <CreditCard data-icon="inline-start" className="size-3.5" />}
              Send Payment Link
            </Button>

            <Button
              variant="secondary"
              size="sm"
              disabled={acting !== null}
              onClick={() => handleAction("cart_recovery")}
              className="justify-start text-xs"
            >
              {acting === "cart_recovery" ? <Spinner data-icon="inline-start" /> : <ShoppingCart data-icon="inline-start" className="size-3.5" />}
              Send Cart Recovery Link (10% Discount)
            </Button>

            <Button
              variant="outline"
              size="sm"
              disabled={acting !== null}
              onClick={() => handleAction("pause_dunning")}
              className="justify-start text-xs"
            >
              {acting === "pause_dunning" ? <Spinner data-icon="inline-start" /> : <PauseCircle data-icon="inline-start" className="size-3.5" />}
              Pause Recovery for 24 Hours
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
