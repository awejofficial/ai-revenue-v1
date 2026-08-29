// frontend/src/components/dashboard/SimulationToolbar.tsx

import React from "react"
import {
  ShoppingCart,
  Gem,
  Repeat,
  CreditCard,
  AlertTriangle,
  Clock,
  CheckCircle2,
  Play,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Spinner } from "@/components/ui/spinner"
import type { SimulationScenario } from "@/types/api"

interface SimulationToolbarProps {
  onSimulate: (scenario: SimulationScenario) => Promise<void>
  activeSimulation: string | null
}

export const SimulationToolbar: React.FC<SimulationToolbarProps> = ({
  onSimulate,
  activeSimulation,
}) => {
  const scenarios: {
    id: SimulationScenario
    label: string
    variant: "default" | "secondary" | "outline" | "destructive"
    customClass?: string
    icon: React.ReactNode
  }[] = [
    {
      id: "checkout_drop_off",
      label: "Cart Drop-Off",
      variant: "default",
      icon: <ShoppingCart data-icon="inline-start" className="size-3.5" />,
    },
    {
      id: "high_ltv_insufficient_funds",
      label: "High-LTV Payday Retry",
      variant: "outline",
      icon: <Gem data-icon="inline-start" className="size-3.5 text-blue-600 dark:text-blue-400" />,
    },
    {
      id: "repeat_failure",
      label: "Repeat Offender",
      variant: "outline",
      icon: <Repeat data-icon="inline-start" className="size-3.5 text-muted-foreground" />,
    },
    {
      id: "expired_card",
      label: "Expired Card",
      variant: "outline",
      icon: <CreditCard data-icon="inline-start" className="size-3.5 text-muted-foreground" />,
    },
    {
      id: "fraud",
      label: "Suspected Fraud",
      variant: "outline",
      customClass: "border-rose-500/30 bg-rose-50/80 text-rose-700 hover:bg-rose-100 hover:text-rose-800 dark:bg-rose-950/30 dark:text-rose-300",
      icon: <AlertTriangle data-icon="inline-start" className="size-3.5 text-rose-600 dark:text-rose-400" />,
    },
    {
      id: "trial_user",
      label: "Free Trial",
      variant: "outline",
      icon: <Clock data-icon="inline-start" className="size-3.5 text-muted-foreground" />,
    },
    {
      id: "payment_succeeded",
      label: "Payment Success (Auto-Resolve)",
      variant: "outline",
      customClass: "border-emerald-500/30 text-emerald-700 hover:bg-emerald-50/60 hover:text-emerald-800 dark:text-emerald-300",
      icon: <CheckCircle2 data-icon="inline-start" className="size-3.5 text-emerald-600 dark:text-emerald-400" />,
    },
  ]

  return (
    <Card className="border-border/80 bg-card shadow-xs">
      <CardContent className="flex flex-wrap items-center justify-between gap-3 p-3.5 sm:p-4">
        <div className="flex items-center gap-2 font-mono text-xs font-semibold text-foreground">
          <Play className="size-3.5 fill-primary text-primary" />
          <span>1-Click Test Harness:</span>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {scenarios.map((sc) => {
            const isRunning = activeSimulation === sc.id
            return (
              <Button
                key={sc.id}
                variant={sc.variant}
                size="sm"
                disabled={activeSimulation !== null}
                onClick={() => onSimulate(sc.id)}
                className={`h-7.5 rounded-lg text-xs font-medium shadow-2xs transition-all ${sc.customClass || ""}`}
              >
                {isRunning ? <Spinner data-icon="inline-start" /> : sc.icon}
                {sc.label}
              </Button>
            )
          })}
        </div>
      </CardContent>
    </Card>
  )
}
