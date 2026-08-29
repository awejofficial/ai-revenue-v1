// frontend/src/components/layout/MetricCard.tsx

import React from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { cn } from "@/lib/utils"

interface MetricCardProps {
  title: string
  value: string | number
  subtitle?: string
  variant?: "destructive" | "success" | "primary" | "warning" | "default"
  icon?: React.ReactNode
  loading?: boolean
  className?: string
  sparkline?: "red" | "green" | "purple" | "blue"
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  variant = "default",
  icon,
  loading = false,
  className,
  sparkline,
}) => {
  const valueColorMap = {
    destructive: "text-rose-600 dark:text-rose-400",
    success: "text-emerald-600 dark:text-emerald-400",
    primary: "text-indigo-600 dark:text-indigo-400",
    warning: "text-amber-600 dark:text-amber-400",
    default: "text-foreground",
  }

  // Sparkline wave paths and gradients
  const renderSparkline = () => {
    if (!sparkline) return null

    if (sparkline === "red") {
      return (
        <div className="relative mt-2 h-8 w-full overflow-hidden">
          <svg viewBox="0 0 200 40" className="h-full w-full preserve-3d" preserveAspectRatio="none">
            <defs>
              <linearGradient id="spark-red" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#f43f5e" stopOpacity="0.25" />
                <stop offset="100%" stopColor="#f43f5e" stopOpacity="0.0" />
              </linearGradient>
            </defs>
            <path
              d="M0,28 Q25,32 50,22 T100,26 T150,18 T200,24 L200,40 L0,40 Z"
              fill="url(#spark-red)"
            />
            <path
              d="M0,28 Q25,32 50,22 T100,26 T150,18 T200,24"
              fill="none"
              stroke="#f43f5e"
              strokeWidth="2"
              strokeLinecap="round"
            />
          </svg>
        </div>
      )
    }

    if (sparkline === "green") {
      return (
        <div className="relative mt-2 h-8 w-full overflow-hidden">
          <svg viewBox="0 0 200 40" className="h-full w-full preserve-3d" preserveAspectRatio="none">
            <defs>
              <linearGradient id="spark-green" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#10b981" stopOpacity="0.25" />
                <stop offset="100%" stopColor="#10b981" stopOpacity="0.0" />
              </linearGradient>
            </defs>
            <path
              d="M0,32 Q30,34 60,24 T120,20 T170,12 T200,10 L200,40 L0,40 Z"
              fill="url(#spark-green)"
            />
            <path
              d="M0,32 Q30,34 60,24 T120,20 T170,12 T200,10"
              fill="none"
              stroke="#10b981"
              strokeWidth="2"
              strokeLinecap="round"
            />
          </svg>
        </div>
      )
    }

    if (sparkline === "purple" || sparkline === "blue") {
      return (
        <div className="relative mt-2 h-8 w-full overflow-hidden">
          <svg viewBox="0 0 200 40" className="h-full w-full preserve-3d" preserveAspectRatio="none">
            <defs>
              <linearGradient id="spark-purple" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#8b5cf6" stopOpacity="0.25" />
                <stop offset="100%" stopColor="#8b5cf6" stopOpacity="0.0" />
              </linearGradient>
            </defs>
            <path
              d="M0,30 Q20,32 50,26 T100,20 T140,24 T180,16 T200,12 L200,40 L0,40 Z"
              fill="url(#spark-purple)"
            />
            <path
              d="M0,30 Q20,32 50,26 T100,20 T140,24 T180,16 T200,12"
              fill="none"
              stroke="#8b5cf6"
              strokeWidth="2"
              strokeLinecap="round"
            />
          </svg>
        </div>
      )
    }

    return null
  }

  return (
    <Card className={cn("relative flex flex-col justify-between overflow-hidden border-border/80 bg-card shadow-xs transition-all hover:shadow-sm", className)}>
      <CardContent className="flex flex-col justify-between p-5 pb-2">
        <div>
          {/* Header row: Title + Icon */}
          <div className="flex items-center justify-between gap-2">
            <span className="font-mono text-[11px] font-semibold tracking-wider text-muted-foreground uppercase">
              {title}
            </span>
            {icon && <span>{icon}</span>}
          </div>

          {/* Value */}
          <div className="mt-2.5">
            {loading ? (
              <Skeleton className="h-9 w-32" />
            ) : (
              <div className={cn("text-2xl font-bold tracking-tight sm:text-3xl", valueColorMap[variant])}>
                {value}
              </div>
            )}
          </div>

          {/* Subtitle */}
          {subtitle && (
            <div className="mt-1">
              {loading ? (
                <Skeleton className="h-4 w-40" />
              ) : (
                <p className="text-xs text-muted-foreground">{subtitle}</p>
              )}
            </div>
          )}
        </div>

        {/* Bottom Sparkline Wave */}
        {renderSparkline()}
      </CardContent>
    </Card>
  )
}
