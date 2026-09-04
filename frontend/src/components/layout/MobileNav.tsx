import { LayoutGrid, CreditCard, Radar, ShieldAlert, Home } from "lucide-react"
import { cn } from "@/lib/utils"
import type { NavTab } from "@/components/layout/Header"

export type { NavTab }

interface MobileNavProps {
  currentTab: NavTab
  onTabChange: (tab: NavTab) => void
}

export const MobileNav: React.FC<MobileNavProps> = ({ currentTab, onTabChange }) => {
  const items = [
    {
      id: "landing" as const,
      label: "Home",
      icon: Home,
    },
    {
      id: "dashboard" as const,
      label: "Overview",
      icon: LayoutGrid,
    },
    {
      id: "payments" as const,
      label: "Payments",
      icon: CreditCard,
    },
    {
      id: "exceptions" as const,
      label: "Exceptions",
      icon: ShieldAlert,
    },
    {
      id: "detector" as const,
      label: "Live Detect",
      icon: Radar,
    },
  ]

  return (
    <nav
      aria-label="Mobile Navigation"
      className="fixed inset-x-0 bottom-0 z-40 flex h-16 items-center justify-around border-t border-border/80 bg-background/95 px-2 backdrop-blur-md md:hidden"
    >
      {items.map((item) => {
        const Icon = item.icon
        const isActive = currentTab === item.id

        return (
          <button
            key={item.id}
            type="button"
            onClick={() => onTabChange(item.id)}
            className={cn(
              "flex min-w-[64px] flex-col items-center justify-center gap-1 rounded-xl py-1.5 transition-all",
              isActive
                ? "font-semibold text-primary"
                : "text-muted-foreground hover:text-foreground active:scale-95"
            )}
          >
            <div
              className={cn(
                "flex size-8 items-center justify-center rounded-lg transition-colors",
                isActive
                  ? "bg-primary/15 text-primary dark:bg-primary/25 dark:text-primary"
                  : "text-muted-foreground"
              )}
            >
              <Icon className="size-4.5" />
            </div>
            <span className="text-[10px] tracking-tight">{item.label}</span>
          </button>
        )
      })}
    </nav>
  )
}
