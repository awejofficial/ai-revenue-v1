// frontend/src/components/landing/LandingNavbar.tsx

import React, { useState, useEffect } from "react"
import { Moon, Sun, Menu, X, ArrowRight } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { useTheme } from "@/components/theme-provider"
import type { NavTab } from "@/components/layout/Header"

interface LandingNavbarProps {
  onNavigate: (tab: NavTab) => void
}

export const LandingNavbar: React.FC<LandingNavbarProps> = ({ onNavigate }) => {
  const { theme, toggleTheme } = useTheme()
  const [scrolled, setScrolled] = useState(false)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20)
    }
    window.addEventListener("scroll", handleScroll)
    return () => window.removeEventListener("scroll", handleScroll)
  }, [])

  const scrollToSection = (id: string) => {
    setMobileMenuOpen(false)
    const element = document.getElementById(id)
    if (element) {
      element.scrollIntoView({ behavior: "smooth" })
    }
  }

  return (
    <header
      className={`sticky top-0 z-50 w-full transition-all duration-200 ${
        scrolled
          ? "border-b border-border/80 bg-background/80 backdrop-blur-xl shadow-xs"
          : "border-b border-transparent bg-transparent"
      }`}
    >
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        {/* Official Brand Logo Lockup */}
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
            className="flex items-center gap-3 text-left group cursor-pointer focus:outline-hidden"
          >
            <img
              src="/logo-horizontal.png"
              alt="Autonomous Revenue Recovery"
              className="h-8 sm:h-9 w-auto object-contain dark:invert transition-opacity group-hover:opacity-90"
            />
            <Badge
              variant="outline"
              className="hidden xl:inline-flex font-mono text-[10px] text-muted-foreground"
            >
              Track 03
            </Badge>
          </button>
        </div>

        {/* Clean Desktop Navigation Links (Zero icon clutter) */}
        <nav className="hidden md:flex items-center gap-8 text-xs font-medium text-muted-foreground">
          <button
            type="button"
            onClick={() => scrollToSection("features")}
            className="transition-colors hover:text-foreground cursor-pointer"
          >
            Platform
          </button>
          <button
            type="button"
            onClick={() => scrollToSection("interactive-showcase")}
            className="transition-colors hover:text-foreground cursor-pointer"
          >
            Scenarios
          </button>
          <button
            type="button"
            onClick={() => scrollToSection("roi-calculator")}
            className="transition-colors hover:text-foreground cursor-pointer"
          >
            ROI Impact
          </button>
          <button
            type="button"
            onClick={() => scrollToSection("razorpay-rails")}
            className="transition-colors hover:text-foreground cursor-pointer"
          >
            Razorpay Rails
          </button>
          <button
            type="button"
            onClick={() => scrollToSection("modules")}
            className="transition-colors hover:text-foreground cursor-pointer"
          >
            Operations
          </button>
        </nav>

        {/* Right Action Bar */}
        <div className="flex items-center gap-3">
          {/* Live System Indicator */}
          <div className="hidden lg:flex items-center gap-2 font-mono text-[11px] text-muted-foreground">
            <span className="size-2 rounded-full bg-emerald-500 animate-pulse" />
            <span>FastAPI Live</span>
          </div>

          {/* Theme Toggle */}
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleTheme}
            className="size-8 rounded-lg text-muted-foreground hover:text-foreground cursor-pointer"
            title={`Toggle Theme (current: ${theme})`}
          >
            {theme === "dark" ? <Sun className="size-4" /> : <Moon className="size-4" />}
          </Button>

          {/* Primary CTA Button */}
          <Button
            size="sm"
            onClick={() => onNavigate("dashboard")}
            className="h-9 gap-1.5 rounded-lg px-4 text-xs font-semibold cursor-pointer"
          >
            <span>Launch Console</span>
            <ArrowRight className="size-3.5" />
          </Button>

          {/* Mobile Hamburger Toggle */}
          <button
            type="button"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="flex md:hidden size-8 items-center justify-center rounded-lg border border-border text-muted-foreground hover:text-foreground cursor-pointer"
            aria-label="Toggle Navigation Menu"
          >
            {mobileMenuOpen ? <X className="size-4" /> : <Menu className="size-4" />}
          </button>
        </div>
      </div>

      {/* Mobile Menu Dropdown */}
      {mobileMenuOpen && (
        <div className="flex flex-col gap-3 border-b border-border bg-background/95 p-4 backdrop-blur-xl md:hidden">
          <div className="flex flex-col gap-2 text-sm font-medium text-muted-foreground">
            <button
              type="button"
              onClick={() => scrollToSection("features")}
              className="text-left py-1 hover:text-foreground cursor-pointer"
            >
              Platform
            </button>
            <button
              type="button"
              onClick={() => scrollToSection("interactive-showcase")}
              className="text-left py-1 hover:text-foreground cursor-pointer"
            >
              Failure Scenarios
            </button>
            <button
              type="button"
              onClick={() => scrollToSection("roi-calculator")}
              className="text-left py-1 hover:text-foreground cursor-pointer"
            >
              ROI Impact Calculator
            </button>
            <button
              type="button"
              onClick={() => scrollToSection("razorpay-rails")}
              className="text-left py-1 hover:text-foreground cursor-pointer"
            >
              Razorpay Rails Ecosystem
            </button>
            <button
              type="button"
              onClick={() => scrollToSection("modules")}
              className="text-left py-1 hover:text-foreground cursor-pointer"
            >
              Operations Console
            </button>
          </div>

          <div className="pt-2 border-t border-border flex items-center justify-between">
            <span className="text-xs text-muted-foreground flex items-center gap-1.5 font-mono">
              <span className="size-1.5 rounded-full bg-emerald-500" />
              Engine Online
            </span>
            <Button
              size="sm"
              onClick={() => {
                setMobileMenuOpen(false)
                onNavigate("dashboard")
              }}
              className="h-8 gap-1.5 text-xs"
            >
              <span>Launch Console</span>
              <ArrowRight className="size-3" />
            </Button>
          </div>
        </div>
      )}
    </header>
  )
}
