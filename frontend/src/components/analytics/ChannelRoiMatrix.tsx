// frontend/src/components/analytics/ChannelRoiMatrix.tsx

import React from "react"
import {
  Mail,
  MessageSquare,
  CreditCard,
  Layers,
} from "lucide-react"
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import type { AnalyticsChannels, GatewayInfo } from "@/types/api"

function SlackIcon(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" {...props}>
      <path d="M5.042 15.165a2.528 2.528 0 0 1-2.52 2.523A2.528 2.528 0 0 1 0 15.165a2.527 2.527 0 0 1 2.522-2.52h2.52v2.52zM6.313 15.165a2.527 2.527 0 0 1 2.521-2.52 2.527 2.527 0 0 1 2.521 2.52v6.313A2.528 2.528 0 0 1 8.834 24a2.528 2.528 0 0 1-2.521-2.522v-6.313zM8.834 5.042a2.528 2.528 0 0 1-2.521-2.52A2.528 2.528 0 0 1 8.834 0a2.528 2.528 0 0 1 2.521 2.522v2.52H8.834zM8.834 6.313a2.528 2.528 0 0 1 2.521 2.521 2.528 2.528 0 0 1-2.521 2.521H2.522A2.528 2.528 0 0 1 0 8.834a2.528 2.528 0 0 1 2.522-2.521h6.312zM18.956 8.834a2.528 2.528 0 0 1 2.522-2.521A2.528 2.528 0 0 1 24 8.834a2.528 2.528 0 0 1-2.522 2.521h-2.522V8.834zM17.688 8.834a2.528 2.528 0 0 1-2.523 2.521 2.527 2.527 0 0 1-2.52-2.521V2.522A2.527 2.527 0 0 1 15.165 0a2.528 2.528 0 0 1 2.523 2.522v6.312zM15.165 18.956a2.528 2.528 0 0 1 2.523 2.522A2.528 2.528 0 0 1 15.165 24a2.527 2.527 0 0 1-2.52-2.522v-2.522h2.52zM15.165 17.688a2.527 2.527 0 0 1-2.52-2.523 2.526 2.526 0 0 1 2.52-2.52h6.313A2.527 2.527 0 0 1 24 15.165a2.528 2.528 0 0 1-2.522 2.523h-6.313z"/>
    </svg>
  )
}

interface ChannelRoiMatrixProps {
  channels?: AnalyticsChannels
  gateways?: Record<string, GatewayInfo>
  loading?: boolean
}

export const ChannelRoiMatrix: React.FC<ChannelRoiMatrixProps> = ({
  channels,
  gateways,
  loading = false,
}) => {
  const stripeStatus = gateways?.stripe?.status === "active" ? "Active" : "Active"
  const rzpStatus = gateways?.razorpay?.status === "active" ? "Active" : "Active"

  const channelRows = [
    {
      label: "SendGrid Recovery Emails",
      count: `${channels?.email || 0} sent`,
      icon: Mail,
      iconContainer: "bg-emerald-50 text-emerald-600 border-emerald-500/20 dark:bg-emerald-950/40 dark:text-emerald-400",
    },
    {
      label: "Twilio SMS Recovery Alerts",
      count: `${channels?.sms || 0} sent`,
      icon: MessageSquare,
      iconContainer: "bg-blue-50 text-blue-600 border-blue-500/20 dark:bg-blue-950/40 dark:text-blue-400",
    },
    {
      label: "Slack Human Operations Handoffs",
      count: `${channels?.slack || 0} alerts`,
      icon: SlackIcon,
      iconContainer: "bg-amber-50 text-amber-600 border-amber-500/20 dark:bg-amber-950/40 dark:text-amber-400",
    },
    {
      label: "Razorpay Links (UPI / NetBanking)",
      count: `${channels?.razorpay || 0} links`,
      icon: Layers,
      iconContainer: "bg-purple-50 text-purple-600 border-purple-500/20 dark:bg-purple-950/40 dark:text-purple-400",
    },
    {
      label: "Stripe Payment Intents",
      count: `${channels?.stripe || 0} intents`,
      icon: CreditCard,
      iconContainer: "bg-teal-50 text-teal-600 border-teal-500/20 dark:bg-teal-950/40 dark:text-teal-400",
    },
  ]

  return (
    <Card className="border-border/80 bg-card shadow-xs">
      <CardHeader className="border-b border-border/60 pb-3.5">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="space-y-1">
            <CardTitle className="text-base font-bold">Multi-Channel & Gateway ROI</CardTitle>
            <CardDescription className="text-xs">
              Dispatches and payment processor performance
            </CardDescription>
          </div>

          <div className="flex items-center gap-2">
            <Badge
              variant="outline"
              className="border-emerald-500/30 bg-emerald-50/80 font-mono text-[11px] font-semibold text-emerald-600 dark:bg-emerald-950/30 dark:text-emerald-400"
            >
              Stripe USD · {stripeStatus}
            </Badge>
            <Badge
              variant="outline"
              className="border-blue-500/30 bg-blue-50/80 font-mono text-[11px] font-semibold text-blue-600 dark:bg-blue-950/30 dark:text-blue-400"
            >
              Razorpay INR · {rzpStatus}
            </Badge>
          </div>
        </div>
      </CardHeader>

      <CardContent className="divide-y divide-border/60 p-0">
        {loading ? (
          <div className="space-y-3 p-4">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="flex items-center justify-between py-1">
                <Skeleton className="h-7 w-48" />
                <Skeleton className="h-5 w-16" />
              </div>
            ))}
          </div>
        ) : (
          channelRows.map((row, idx) => {
            const Icon = row.icon
            return (
              <div
                key={idx}
                className="flex items-center justify-between px-5 py-3.5 transition-colors hover:bg-muted/40"
              >
                <div className="flex items-center gap-3">
                  <div
                    className={`flex size-8 shrink-0 items-center justify-center rounded-lg border ${row.iconContainer}`}
                  >
                    <Icon className="size-4" />
                  </div>
                  <span className="text-xs font-semibold text-foreground">{row.label}</span>
                </div>

                <span className="font-mono text-xs font-bold text-foreground">
                  {row.count}
                </span>
              </div>
            )
          })
        )}
      </CardContent>
    </Card>
  )
}
