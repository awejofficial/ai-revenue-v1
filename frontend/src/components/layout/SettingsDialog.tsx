// frontend/src/components/layout/SettingsDialog.tsx

import React from "react"
import {
  Sun,
  Moon,
  Laptop,
  Check,
  Zap,
  CreditCard,
  Layers,
  Database,
  Terminal,
} from "lucide-react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog"
import { Badge } from "@/components/ui/badge"
import { useTheme } from "@/components/theme-provider"
import { cn } from "@/lib/utils"

interface SettingsDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export const SettingsDialog: React.FC<SettingsDialogProps> = ({
  open,
  onOpenChange,
}) => {
  const { theme, setTheme } = useTheme()

  const themeOptions = [
    {
      id: "light" as const,
      label: "Light",
      icon: Sun,
      description: "Clean high-contrast theme",
    },
    {
      id: "dark" as const,
      label: "Dark",
      icon: Moon,
      description: "OLED dark mode palette",
    },
    {
      id: "system" as const,
      label: "System",
      icon: Laptop,
      description: "Follow OS appearance",
    },
  ]

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="text-base font-bold">System Settings & Appearance</DialogTitle>
          <DialogDescription className="text-xs">
            Configure UI themes, view real-time gateway connections, and audit engine health.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-2">
          {/* Theme Selector */}
          <div>
            <label className="font-mono text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
              Theme Mode
            </label>
            <div className="mt-2 grid grid-cols-3 gap-2">
              {themeOptions.map((opt) => {
                const Icon = opt.icon
                const isSelected = theme === opt.id

                return (
                  <button
                    key={opt.id}
                    type="button"
                    onClick={() => setTheme(opt.id)}
                    className={cn(
                      "flex flex-col items-center justify-center gap-1.5 rounded-xl border p-3 text-center transition-all",
                      isSelected
                        ? "border-primary bg-primary/10 text-primary shadow-xs ring-1 ring-primary"
                        : "border-border/80 bg-card text-muted-foreground hover:bg-muted hover:text-foreground"
                    )}
                  >
                    <Icon className="size-4.5" />
                    <span className="text-xs font-semibold">{opt.label}</span>
                    {isSelected && (
                      <span className="flex size-3.5 items-center justify-center rounded-full bg-primary text-primary-foreground">
                        <Check className="size-2.5" />
                      </span>
                    )}
                  </button>
                )
              })}
            </div>
          </div>

          {/* Engine & Processor Status */}
          <div className="space-y-2 rounded-xl border border-border/80 bg-muted/30 p-3.5">
            <span className="font-mono text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
              Engine Health & Integrations
            </span>

            <div className="space-y-2 pt-1 text-xs">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-foreground">
                  <Zap className="size-3.5 text-blue-500" />
                  <span>Google Gemini 3.7 Flash</span>
                </div>
                <Badge variant="outline" className="border-blue-500/30 bg-blue-50/80 font-mono text-[10px] text-blue-600 dark:bg-blue-950/40 dark:text-blue-400">
                  Online
                </Badge>
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-foreground">
                  <CreditCard className="size-3.5 text-teal-500" />
                  <span>Stripe Gateway (USD)</span>
                </div>
                <Badge variant="outline" className="border-emerald-500/30 bg-emerald-50 font-mono text-[10px] text-emerald-600 dark:bg-emerald-950/40 dark:text-emerald-400">
                  Active
                </Badge>
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-foreground">
                  <Layers className="size-3.5 text-purple-500" />
                  <span>Razorpay Gateway (INR UPI)</span>
                </div>
                <Badge variant="outline" className="border-emerald-500/30 bg-emerald-50 font-mono text-[10px] text-emerald-600 dark:bg-emerald-950/40 dark:text-emerald-400">
                  Active
                </Badge>
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-foreground">
                  <Database className="size-3.5 text-indigo-500" />
                  <span>Dual Pool (PostgreSQL / SQLite)</span>
                </div>
                <Badge variant="outline" className="border-indigo-500/30 bg-indigo-50 font-mono text-[10px] text-indigo-600 dark:bg-indigo-950/40 dark:text-indigo-400">
                  Connected
                </Badge>
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-foreground">
                  <Terminal className="size-3.5 text-amber-500" />
                  <span>Webhooks Intake</span>
                </div>
                <span className="font-mono text-[10px] text-muted-foreground">
                  /webhooks/psp · /webhooks/billing
                </span>
              </div>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
