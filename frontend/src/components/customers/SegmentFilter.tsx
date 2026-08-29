// frontend/src/components/customers/SegmentFilter.tsx

import React from "react"
import { Users, Gem, Building2, Zap, Clock, AlertTriangle } from "lucide-react"
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group"

export type SegmentFilterValue =
  | "all"
  | "high_ltv"
  | "enterprise"
  | "standard"
  | "trial"
  | "in_recovery"

interface SegmentFilterProps {
  value: SegmentFilterValue
  onChange: (value: SegmentFilterValue) => void
}

export const SegmentFilter: React.FC<SegmentFilterProps> = ({ value, onChange }) => {
  const options: {
    value: SegmentFilterValue
    label: string
    icon: React.ReactNode
  }[] = [
    {
      value: "all",
      label: "All Accounts",
      icon: <Users data-icon="inline-start" className="size-3.5" />,
    },
    {
      value: "high_ltv",
      label: "High-LTV ($5K+)",
      icon: <Gem data-icon="inline-start" className="size-3.5 text-blue-500" />,
    },
    {
      value: "enterprise",
      label: "Enterprise",
      icon: <Building2 data-icon="inline-start" className="size-3.5 text-indigo-500" />,
    },
    {
      value: "standard",
      label: "Standard",
      icon: <Zap data-icon="inline-start" className="size-3.5 text-amber-500" />,
    },
    {
      value: "trial",
      label: "Free Trial",
      icon: <Clock data-icon="inline-start" className="size-3.5 text-muted-foreground" />,
    },
    {
      value: "in_recovery",
      label: "In Recovery",
      icon: <AlertTriangle data-icon="inline-start" className="size-3.5 text-rose-500" />,
    },
  ]

  return (
    <ToggleGroup
      value={[value]}
      onValueChange={(vals: string[]) => {
        if (vals && vals.length > 0) {
          const selected = vals[vals.length - 1] as SegmentFilterValue
          onChange(selected)
        }
      }}
      className="flex flex-wrap gap-1"
    >
      {options.map((opt) => (
        <ToggleGroupItem
          key={opt.value}
          value={opt.value}
          size="sm"
          className="h-7.5 gap-1.5 rounded-md px-2.5 text-xs font-medium data-[state=on]:bg-primary data-[state=on]:text-primary-foreground"
        >
          {opt.icon}
          <span>{opt.label}</span>
        </ToggleGroupItem>
      ))}
    </ToggleGroup>
  )
}
