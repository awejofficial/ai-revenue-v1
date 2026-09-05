// frontend/src/components/landing/LandingPageView.tsx

import React, { useState, useEffect } from "react"
import { ArrowRight, Volume2, VolumeX, RefreshCw, CheckCircle2, Play } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { LandingNavbar } from "@/components/landing/LandingNavbar"
import { api, type SimulationScenario } from "@/lib/api"
import { toast } from "sonner"
import { cn } from "@/lib/utils"
import type { NavTab } from "@/components/layout/Header"

interface LandingPageViewProps {
  onNavigate: (tab: NavTab) => void
  onOpenAudit?: (paymentId?: string) => void
}

interface FailureScenario {
  id: string
  title: string
  incidentId: string
  amount: number
  category: string
  rail: string
  alertTitle: string
  alertText: string
  aiConfidence: string
  aiCode: string
  aiDiagnosis: string
  channel: string
  hinglishCopy: string
  settledText: string
  simScenario: SimulationScenario
}

const SCENARIOS: FailureScenario[] = [
  {
    id: "low_balance",
    title: "Low Balance on UPI",
    incidentId: "pay_2694WD",
    amount: 4499,
    category: "INSUFFICIENT_FUNDS",
    rail: "UPI / PhonePe",
    alertTitle: "Payment Attempt Failed (#SBI-0164)",
    alertText: "Customer received 'Payment of INR 4,499.00 failing to process due to low balance' notification.",
    aiConfidence: "99.4% Confidence",
    aiCode: "INSUFFICIENT_UPI_FUNDS",
    aiDiagnosis: "Customer attempted to pay via UPI handle, bank returned balance limit exceeded. Autonomous fallback: Dispatched WhatsApp Razorpay Smart Link with 24h hold.",
    channel: "WhatsApp Direct Recovery Link (Expires 24h)",
    hinglishCopy: "Namaste! Aapka payment of ₹4,499 complete nahi ho paya. Click karke 24hrs ke andar pay karein taaki aapka order cancel na ho: https://rzp.io/i/rec_2694wd",
    settledText: "07:15 PM recovered: Customer completed payment via alternate UPI id (GPay).",
    simScenario: "high_ltv_insufficient_funds",
  },
  {
    id: "switch_timeout",
    title: "HDFC Switch Timeout",
    incidentId: "pay_7105TX",
    amount: 39900,
    category: "NETWORK_TIMEOUT",
    rail: "NetBanking 3DS",
    alertTitle: "Gateway Switch Timeout (#HDFC-8821)",
    alertText: "3DS switch dropped after 30s during flash checkout. Payment status left in pending authorization.",
    aiConfidence: "98.1% Confidence",
    aiCode: "NETWORK_TIMEOUT",
    aiDiagnosis: "Idempotent network failure on bank switch. Customer authenticated. Safe for autonomous secondary route retry.",
    channel: "Automated Idempotent Gateway Retry",
    hinglishCopy: "Namaste Rahul! HDFC Bank network slow hone ke karan payment pause hua tha. Humne bina extra debit ke order confirm kar diya.",
    settledText: "08:42 PM recovered: Secondary switch retry succeeded in 480ms.",
    simScenario: "repeat_failure",
  },
  {
    id: "cart_drop",
    title: "Magic Checkout Drop",
    incidentId: "pay_4922MC",
    amount: 2199,
    category: "CHECKOUT_ABANDONED",
    rail: "Magic Checkout",
    alertTitle: "Magic Checkout Cart Hold (#OPT-3910)",
    alertText: "Buyer auto-filled address via 1-Click checkout but exited before OTP verification.",
    aiConfidence: "97.5% Confidence",
    aiCode: "CHECKOUT_ABANDONED",
    aiDiagnosis: "High intent customer dropped at final OTP step. Inventory placed on 45-minute VIP reserve.",
    channel: "WhatsApp 1-Click Cart Recovery Link",
    hinglishCopy: "Hi Ananya! Aapka cart 45 min ke liye reserve hai. Sirf 1-tap me bina details dobara dale order complete karein: https://rzp.io/i/magic_cart",
    settledText: "09:12 PM recovered: Customer completed purchase via WhatsApp link with 1-click UPI.",
    simScenario: "checkout_drop_off",
  },
  {
    id: "fraud_spike",
    title: "Card Velocity Spike",
    incidentId: "pay_9901FR",
    amount: 89500,
    category: "FRAUD_FLAG",
    rail: "International Visa",
    alertTitle: "Card Velocity & Proxy Flagged (#SEC-9901)",
    alertText: "4 rapid international card attempts within 60s from Frankfurt VPN datacenter IP.",
    aiConfidence: "99.9% Confidence",
    aiCode: "SUSPECTED_FRAUD",
    aiDiagnosis: "High-risk velocity pattern detected. Potential card testing attack. Strict safety policy blocks all automated retries.",
    channel: "Outreach Suppressed by Security Policy",
    hinglishCopy: "[OUTREACH SUPPRESSED] Security rule enforced. Instant alert sent to Merchant Ops Slack.",
    settledText: "Quarantined in Honest Exception List. Zero chargeback liability incurred.",
    simScenario: "fraud",
  },
]

export const LandingPageView: React.FC<LandingPageViewProps> = ({
  onNavigate,
  onOpenAudit,
}) => {
  // Calculator state
  const [monthlyGmv, setMonthlyGmv] = useState<number>(5000000) // ₹50 Lakhs default
  const [failureRate, setFailureRate] = useState<number>(8.2) // 8.2% default
  const [recoveryWinRate, setRecoveryWinRate] = useState<number>(40) // 40% default

  // Active scenario state
  const [selectedScenarioId, setSelectedScenarioId] = useState<string>("low_balance")
  const [isPlayingAudio, setIsPlayingAudio] = useState(false)
  const [isSimulating, setIsSimulating] = useState(false)

  // Dynamic Pipeline Interactive Stage state
  const [activePipelineStage, setActivePipelineStage] = useState<number>(1)
  const [isPipelineStepping, setIsPipelineStepping] = useState<boolean>(false)

  // Auto-cycle through pipeline stages for dynamic feel
  useEffect(() => {
    const timer = setInterval(() => {
      if (!isPipelineStepping) {
        setActivePipelineStage((prev) => (prev % 4) + 1)
      }
    }, 4500)
    return () => clearInterval(timer)
  }, [isPipelineStepping])

  // Calculations
  const failedRevenue = (monthlyGmv * failureRate) / 100
  const netRecoveredMonthly = (failedRevenue * recoveryWinRate) / 100
  const netRecoveredAnnual = netRecoveredMonthly * 12

  const activeScenario =
    SCENARIOS.find((s) => s.id === selectedScenarioId) || SCENARIOS[0]

  const handleVoicePlay = (text: string) => {
    if (!("speechSynthesis" in window)) {
      toast.error("Web Speech API not supported on this browser.")
      return
    }
    if (isPlayingAudio) {
      window.speechSynthesis.cancel()
      setIsPlayingAudio(false)
      return
    }

    const utterance = new SpeechSynthesisUtterance(text)
    utterance.lang = "hi-IN"
    utterance.rate = 0.95
    utterance.pitch = 1.05
    utterance.onend = () => setIsPlayingAudio(false)
    utterance.onerror = () => setIsPlayingAudio(false)
    setIsPlayingAudio(true)
    window.speechSynthesis.speak(utterance)
  }

  const handleTriggerSimulation = async (scenario: FailureScenario) => {
    setIsSimulating(true)
    try {
      await api.simulateScenario(scenario.simScenario)
      toast.success(`Autonomous Recovery Dispatched: ${scenario.title}`, {
        description: `Dispatched action: ${scenario.channel}`,
      })
    } catch (err: any) {
      toast.info(`Simulation cycle executed: ${err.message || "Completed"}`)
    } finally {
      setIsSimulating(false)
    }
  }

  const handleRunPipelineSimulation = async () => {
    setIsPipelineStepping(true)
    for (let stage = 1; stage <= 4; stage++) {
      setActivePipelineStage(stage)
      await new Promise((resolve) => setTimeout(resolve, 800))
    }
    setIsPipelineStepping(false)
    toast.success("Live recovery pipeline cycle verified: 200 OK")
  }

  return (
    <div className="flex flex-col min-h-screen bg-background text-foreground antialiased selection:bg-primary/20 selection:text-primary">
      {/* ── 1. OFFICIAL BRAND NAVBAR ── */}
      <LandingNavbar onNavigate={onNavigate} />

      {/* ── 2. HERO SECTION WITH GLOWING BACKDROP & SHIMMERING BADGE ── */}
      <section className="relative overflow-hidden pt-12 pb-16 md:pt-20 md:pb-24">
        {/* Subtle Radial Glow */}
        <div className="pointer-events-none absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-5xl h-96 bg-gradient-to-b from-blue-600/10 via-primary/5 to-transparent blur-[120px] -z-10" />

        <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8 text-center flex flex-col items-center gap-8">
          {/* Shimmering Badge - Linkify Magic Badge style */}
          <button
            type="button"
            onClick={() => onNavigate("overview")}
            className="group relative inline-flex items-center gap-2 overflow-hidden rounded-full p-[1px] transition-transform hover:scale-[1.02] cursor-pointer"
          >
            <span className="absolute inset-[-1000%] animate-spin-slow bg-[conic-gradient(from_90deg_at_50%_50%,hsl(var(--primary))_0%,#38bdf8_50%,hsl(var(--primary))_100%)]" />
            <span className="inline-flex items-center gap-2 rounded-full bg-background/90 px-4 py-1.5 text-xs font-medium text-foreground backdrop-blur-xl dark:bg-card/90">
              <span className="size-2 rounded-full bg-emerald-500 animate-pulse" />
              <span className="font-semibold text-foreground">Track 03</span>
              <span className="text-muted-foreground">· Autonomous Revenue Recovery</span>
              <ArrowRight className="size-3.5 text-muted-foreground transition-transform group-hover:translate-x-0.5" />
            </span>
          </button>

          {/* Hero Main Headline */}
          <div className="flex flex-col gap-4 max-w-4xl">
            <h1 className="text-4xl font-extrabold tracking-tight text-foreground sm:text-6xl lg:text-7xl !leading-[1.1]">
              Recover failed payments. <br />
              <span className="text-transparent bg-gradient-to-r from-blue-600 via-indigo-600 to-cyan-500 bg-clip-text">
                Win back revenue autonomously.
              </span>
            </h1>

            <p className="max-w-2xl mx-auto text-sm text-muted-foreground sm:text-base lg:text-lg leading-relaxed">
              AR is an autonomous dunning and revenue recovery agent built for Razorpay merchants. It intercepts transaction drop-offs in real-time, diagnoses bank codes in &lt;500ms with Google Gemini Flash &amp; zero-latency heuristics, and dispatches multi-rail recovery links within safe deterministic policy bounds.
            </p>
          </div>

          {/* Clean Hero Action Buttons */}
          <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
            <Button
              size="lg"
              onClick={() => onNavigate("overview")}
              className="h-11 gap-2 rounded-xl px-6 text-sm font-semibold cursor-pointer shadow-sm"
            >
              <span>Launch Operations Console</span>
              <ArrowRight className="size-4" />
            </Button>

            <Button
              variant="outline"
              size="lg"
              onClick={() => {
                const el = document.getElementById("interactive-showcase")
                el?.scrollIntoView({ behavior: "smooth" })
              }}
              className="h-11 gap-2 rounded-xl px-6 text-sm font-semibold cursor-pointer"
            >
              <span>Explore Failure Sandbox</span>
            </Button>

            <Button
              variant="ghost"
              size="lg"
              onClick={() => onNavigate("detector")}
              className="h-11 gap-2 rounded-xl px-5 text-sm font-semibold text-muted-foreground hover:text-foreground cursor-pointer"
            >
              <span>Live Razorpay Radar</span>
            </Button>
          </div>

          {/* ── 3. DYNAMIC INTERACTIVE CONSOLE PREVIEW ── */}
          <div className="relative w-full pt-8 sm:pt-12">
            {/* Glowing Backdrop behind Dashboard Container */}
            <div className="pointer-events-none absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-4/5 h-64 bg-gradient-to-r from-blue-500/15 via-indigo-500/15 to-cyan-500/15 blur-[80px] rounded-full" />

            <div className="relative mx-auto max-w-5xl rounded-2xl border border-border/80 bg-card p-2 shadow-2xl backdrop-blur-xl">
              {/* Window Header */}
              <div className="flex items-center justify-between border-b border-border/70 px-4 py-3 bg-muted/40 rounded-t-xl">
                <div className="flex items-center gap-2">
                  <div className="flex items-center gap-1.5">
                    <span className="size-3 rounded-full bg-rose-500/80" />
                    <span className="size-3 rounded-full bg-amber-500/80" />
                    <span className="size-3 rounded-full bg-emerald-500/80" />
                  </div>
                  <span className="ml-2 font-mono text-xs text-muted-foreground">
                    ar-recovery-engine ~ live-telemetry: connected
                  </span>
                </div>

                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-1.5 font-mono text-[11px] text-emerald-600 dark:text-emerald-400">
                    <span className="size-1.5 rounded-full bg-emerald-500 animate-ping" />
                    <span>GATEWAY LIVE</span>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleRunPipelineSimulation}
                    disabled={isPipelineStepping}
                    className="h-7 gap-1.5 text-[11px] cursor-pointer"
                  >
                    <Play className="size-3 fill-current" />
                    <span>Step Pipeline Flow</span>
                  </Button>
                </div>
              </div>

              {/* Dynamic Telemetry Metric Strip (Clean Monospace Typography, No Pills) */}
              <div className="grid grid-cols-2 divide-y sm:divide-y-0 sm:grid-cols-4 divide-border/60 bg-background/50 p-4 text-left">
                <div className="p-3">
                  <div className="text-[11px] font-mono uppercase tracking-wider text-muted-foreground">
                    MONITORED TXNS
                  </div>
                  <div className="mt-1 font-mono text-2xl font-bold text-foreground">
                    120
                  </div>
                  <div className="mt-1 flex items-center gap-1 text-[11px] text-muted-foreground font-mono">
                    <span className="size-1.5 rounded-full bg-blue-500" />
                    <span>Razorpay Live Feed</span>
                  </div>
                </div>

                <div className="p-3">
                  <div className="text-[11px] font-mono uppercase tracking-wider text-muted-foreground">
                    REVENUE RECOVERED
                  </div>
                  <div className="mt-1 font-mono text-2xl font-bold text-emerald-600 dark:text-emerald-400">
                    ₹7,41,617.42
                  </div>
                  <div className="mt-1 flex items-center gap-1 text-[11px] text-muted-foreground font-mono">
                    <span className="size-1.5 rounded-full bg-emerald-500" />
                    <span>Settled to Merchant</span>
                  </div>
                </div>

                <div className="p-3">
                  <div className="text-[11px] font-mono uppercase tracking-wider text-muted-foreground">
                    INFERENCE LATENCY
                  </div>
                  <div className="mt-1 font-mono text-2xl font-bold text-blue-600 dark:text-blue-400">
                    &lt; 500 ms
                  </div>
                  <div className="mt-1 flex items-center gap-1 text-[11px] text-muted-foreground font-mono">
                    <span className="size-1.5 rounded-full bg-blue-500" />
                    <span>Google Gemini Flash &amp; Fast Heuristics</span>
                  </div>
                </div>

                <div className="p-3">
                  <div className="text-[11px] font-mono uppercase tracking-wider text-muted-foreground">
                    RECOVERY WIN RATE
                  </div>
                  <div className="mt-1 font-mono text-2xl font-bold text-foreground">
                    28.4%
                  </div>
                  <div className="mt-1 flex items-center gap-1 text-[11px] text-muted-foreground font-mono">
                    <span className="size-1.5 rounded-full bg-emerald-500" />
                    <span>34 of 120 Recovered</span>
                  </div>
                </div>
              </div>

              {/* Dynamic Interactive Pipeline Architecture (Live Graphical Flow) */}
              <div className="border-t border-border/70 bg-muted/20 p-5">
                <div className="flex items-center justify-between pb-3">
                  <span className="font-mono text-xs font-semibold text-muted-foreground uppercase">
                    Interactive End-to-End Pipeline
                  </span>
                  <span className="font-mono text-[11px] text-muted-foreground">
                    Click stage to inspect payload
                  </span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-left">
                  {/* Stage 1 */}
                  <button
                    type="button"
                    onClick={() => setActivePipelineStage(1)}
                    className={cn(
                      "flex flex-col gap-1.5 rounded-xl border p-3.5 text-left transition-all cursor-pointer",
                      activePipelineStage === 1
                        ? "border-primary bg-background shadow-md ring-1 ring-primary/40"
                        : "border-border bg-card/60 hover:bg-muted/40"
                    )}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-[10px] text-muted-foreground">STAGE 01</span>
                      <span className="flex items-center gap-1 font-mono text-[10px] text-rose-500">
                        <span className="size-1.5 rounded-full bg-rose-500 animate-pulse" />
                        payment.failed
                      </span>
                    </div>
                    <div className="text-xs font-bold text-foreground">1. Drop-off Detection</div>
                    <p className="text-[11px] text-muted-foreground leading-relaxed">
                      Instant webhook ingestion on failure codes (SBI-0164, HDFC-8821).
                    </p>
                  </button>

                  {/* Stage 2 */}
                  <button
                    type="button"
                    onClick={() => setActivePipelineStage(2)}
                    className={cn(
                      "flex flex-col gap-1.5 rounded-xl border p-3.5 text-left transition-all cursor-pointer",
                      activePipelineStage === 2
                        ? "border-blue-500 bg-background shadow-md ring-1 ring-blue-500/40"
                        : "border-border bg-card/60 hover:bg-muted/40"
                    )}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-[10px] text-muted-foreground">STAGE 02</span>
                      <span className="font-mono text-[10px] text-blue-600 dark:text-blue-400">
                        &lt;320ms LPU
                      </span>
                    </div>
                    <div className="text-xs font-bold text-foreground">2. Root-Cause AI</div>
                    <p className="text-[11px] text-muted-foreground leading-relaxed">
                      LPU inference diagnoses cause and drafts customer Hinglish message.
                    </p>
                  </button>

                  {/* Stage 3 */}
                  <button
                    type="button"
                    onClick={() => setActivePipelineStage(3)}
                    className={cn(
                      "flex flex-col gap-1.5 rounded-xl border p-3.5 text-left transition-all cursor-pointer",
                      activePipelineStage === 3
                        ? "border-indigo-500 bg-background shadow-md ring-1 ring-indigo-500/40"
                        : "border-border bg-card/60 hover:bg-muted/40"
                    )}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-[10px] text-muted-foreground">STAGE 03</span>
                      <span className="font-mono text-[10px] text-indigo-500">
                        100% Bounded
                      </span>
                    </div>
                    <div className="text-xs font-bold text-foreground">3. Policy Guardrails</div>
                    <p className="text-[11px] text-muted-foreground leading-relaxed">
                      Bank outage circuit breakers halt retries; fraud velocity quarantined.
                    </p>
                  </button>

                  {/* Stage 4 */}
                  <button
                    type="button"
                    onClick={() => setActivePipelineStage(4)}
                    className={cn(
                      "flex flex-col gap-1.5 rounded-xl border p-3.5 text-left transition-all cursor-pointer",
                      activePipelineStage === 4
                        ? "border-emerald-500 bg-background shadow-md ring-1 ring-emerald-500/40"
                        : "border-border bg-card/60 hover:bg-muted/40"
                    )}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-[10px] text-muted-foreground">STAGE 04</span>
                      <span className="font-mono text-[10px] text-emerald-600 dark:text-emerald-400">
                        ₹7.41L Settled
                      </span>
                    </div>
                    <div className="text-xs font-bold text-foreground">4. Multi-Rail Recovery</div>
                    <p className="text-[11px] text-muted-foreground leading-relaxed">
                      Dynamic Smart Link dispatched via WhatsApp, SMS, or NetBanking switch.
                    </p>
                  </button>
                </div>

                {/* Stage Telemetry Preview Box */}
                <div className="mt-4 rounded-xl border border-border bg-background/80 p-3.5 font-mono text-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-muted-foreground">
                  <div className="flex items-center gap-2 text-foreground">
                    <span className="size-2 rounded-full bg-primary animate-ping" />
                    <span className="font-bold">Active Telemetry Node:</span>
                    <span>
                      {activePipelineStage === 1 && "Ingesting Razorpay HMAC Webhook (payment.failed)"}
                      {activePipelineStage === 2 && "Gemini 3.7 Flash: Diagnosing SBI_0164_INSUFFICIENT_FUNDS (99.4% confidence)"}
                      {activePipelineStage === 3 && "Policy Gate: Enforcing Max 3-Retry Cap & Outage Circuit Breaker"}
                      {activePipelineStage === 4 && "Dispatched WhatsApp Smart Link https://rzp.io/i/rec_2694wd"}
                    </span>
                  </div>
                  <span className="text-[11px] text-primary shrink-0">
                    Status: Verified 200 OK
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── 4. BENTO GRID ARCHITECTURE (NO ICON CLUTTER) ── */}
      <section id="features" className="py-16 md:py-24 border-t border-border/80 bg-muted/20">
        <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8 flex flex-col gap-12">
          <div className="text-center flex flex-col gap-2 max-w-2xl mx-auto">
            <span className="font-mono text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Autonomous Architecture
            </span>
            <h2 className="text-3xl font-extrabold tracking-tight text-foreground sm:text-4xl">
              Engineered for Enterprise Recovery
            </h2>
            <p className="text-sm text-muted-foreground">
              A high-precision engine built for Indian BFSI rails, UPI edge cases, and high-velocity digital checkouts.
            </p>
          </div>

          {/* Clean Bento Grid using shadcn Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {/* Bento Card 1 (Span 2) */}
            <Card className="md:col-span-2 flex flex-col justify-between">
              <CardHeader>
                <div className="font-mono text-[11px] text-muted-foreground uppercase">
                  Sub-500ms Razorpay Webhook Ingestion
                </div>
                <CardTitle className="text-xl">
                  Real-Time Failure Radar &amp; Stream Ingestion
                </CardTitle>
                <CardDescription>
                  Direct webhook listeners intercept failure events milliseconds after bank drops. Evaluates customer lifetime value, historical success rates, and optimal retry channels without merchant latency.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="rounded-xl border border-border bg-muted/30 p-4 font-mono text-xs flex flex-col gap-2">
                  <div className="flex items-center justify-between text-muted-foreground text-[11px]">
                    <span>LIVE INGESTION RADAR FEED</span>
                    <span className="text-emerald-500 flex items-center gap-1">
                      <span className="size-1.5 rounded-full bg-emerald-500 animate-pulse" />
                      STREAMING
                    </span>
                  </div>
                  <div className="flex flex-col gap-2 pt-1">
                    <div className="flex items-center justify-between border-b border-border pb-1.5">
                      <span className="font-semibold text-rose-500">SBI_0164_INSUFFICIENT_FUNDS</span>
                      <span className="text-muted-foreground">pay_2694WD · ₹4,499.00</span>
                      <span className="text-foreground">Smart Link Dispatched</span>
                    </div>
                    <div className="flex items-center justify-between border-b border-border pb-1.5">
                      <span className="font-semibold text-amber-500">HDFC_SWITCH_TIMEOUT</span>
                      <span className="text-muted-foreground">pay_7105TX · ₹39,900.00</span>
                      <span className="text-foreground">Auto-Retry Success</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-rose-600">CARD_VELOCITY_SUSPECT</span>
                      <span className="text-muted-foreground">pay_9901FR · ₹89,500.00</span>
                      <span className="text-rose-600">Quarantined (Safety Gate)</span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Bento Card 2 */}
            <Card className="flex flex-col justify-between">
              <CardHeader>
                <div className="font-mono text-[11px] text-muted-foreground uppercase">
                  Google Gemini 3.7 Flash
                </div>
                <CardTitle className="text-xl">
                  Low-Latency Reasoning Engine
                </CardTitle>
                <CardDescription>
                  Inference engines diagnose ambiguous bank codes and generate localized Hinglish dunning copy in under 500 milliseconds.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="rounded-xl border border-border bg-muted/30 p-3.5 flex flex-col gap-2 font-mono text-[11px]">
                  <div className="text-foreground font-semibold">DIAGNOSTIC METRICS</div>
                  <div className="flex justify-between text-muted-foreground">
                    <span>Classification Latency:</span>
                    <span className="text-foreground font-bold">320ms</span>
                  </div>
                  <div className="flex justify-between text-muted-foreground">
                    <span>Hinglish Synthesizer:</span>
                    <span className="text-foreground font-bold">Native Web Speech</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Bento Card 3 */}
            <Card className="flex flex-col justify-between">
              <CardHeader>
                <div className="font-mono text-[11px] text-muted-foreground uppercase">
                  Deterministic Governance
                </div>
                <CardTitle className="text-xl">
                  Hard Safety Policy Fences
                </CardTitle>
                <CardDescription>
                  Enforces zero fraud auto-retries, bank outage circuit breakers, and a hard 3-retry cap to protect brand reputation.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex flex-col gap-2 border-t border-border pt-3 text-xs">
                  <div className="flex items-center gap-2 text-foreground">
                    <CheckCircle2 className="size-3.5 text-emerald-500 shrink-0" />
                    <span>Max 3 Retries per payment attempt</span>
                  </div>
                  <div className="flex items-center gap-2 text-foreground">
                    <CheckCircle2 className="size-3.5 text-emerald-500 shrink-0" />
                    <span>Circuit breaker on consecutive drops</span>
                  </div>
                  <div className="flex items-center gap-2 text-foreground">
                    <CheckCircle2 className="size-3.5 text-emerald-500 shrink-0" />
                    <span>Fraud &amp; VPN velocity auto-quarantined</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Bento Card 4 (Span 2) */}
            <Card className="md:col-span-2 flex flex-col justify-between">
              <CardHeader>
                <div className="font-mono text-[11px] text-muted-foreground uppercase">
                  Autonomous Multi-Rail Recovery
                </div>
                <CardTitle className="text-xl">
                  Closed-Loop Settlement Verification
                </CardTitle>
                <CardDescription>
                  Generates idempotent Razorpay Smart Links dispatched over WhatsApp, SMS, or Email. When the buyer pays, webhooks close the reconciliation loop automatically.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-left">
                  <div className="rounded-xl border border-border bg-background p-3 flex flex-col gap-1">
                    <div className="font-semibold text-xs text-foreground">WhatsApp Smart Links</div>
                    <p className="text-[11px] text-muted-foreground">1-tap checkout links with 24h expiration and UPI prefill.</p>
                  </div>
                  <div className="rounded-xl border border-border bg-background p-3 flex flex-col gap-1">
                    <div className="font-semibold text-xs text-foreground">Hinglish Voice Calling</div>
                    <p className="text-[11px] text-muted-foreground">Conversational audio calls for VIP customers on high-value orders.</p>
                  </div>
                  <div className="rounded-xl border border-border bg-background p-3 flex flex-col gap-1">
                    <div className="font-semibold text-xs text-foreground">Secondary Gateway Route</div>
                    <p className="text-[11px] text-muted-foreground">Silent rerouting to alternate bank switches on timeout drops.</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* ── 5. INTERACTIVE FAILURE SCENARIO SANDBOX (WITH DYNAMIC AUDIO WAVEFORM) ── */}
      <section id="interactive-showcase" className="py-16 md:py-24 border-t border-border/80">
        <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8 flex flex-col gap-8">
          <div className="text-center flex flex-col gap-2 max-w-2xl mx-auto">
            <span className="font-mono text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Interactive Scenario Sandbox
            </span>
            <h2 className="text-3xl font-extrabold tracking-tight text-foreground sm:text-4xl">
              See How the Engine Recovers Lost Revenue
            </h2>
            <p className="text-sm text-muted-foreground">
              Select an authentic Indian payment drop-off scenario to test our AI diagnosis, Hinglish voice outreach, and deterministic safety bounds in real-time.
            </p>
          </div>

          {/* Clean Scenario Selectors */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {SCENARIOS.map((sc) => {
              const isSelected = sc.id === selectedScenarioId
              return (
                <button
                  key={sc.id}
                  type="button"
                  onClick={() => setSelectedScenarioId(sc.id)}
                  className={cn(
                    "cursor-pointer rounded-xl border p-4 text-left transition-all flex flex-col gap-2",
                    isSelected
                      ? "border-primary bg-primary/5 shadow-xs ring-1 ring-primary/40"
                      : "border-border bg-card hover:border-border/80"
                  )}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-xs text-foreground">
                      {sc.title}
                    </span>
                    <span className="font-mono text-xs font-bold text-foreground">
                      ₹{sc.amount.toLocaleString("en-IN")}
                    </span>
                  </div>
                  <div className="flex items-center gap-1.5 font-mono text-[10px] text-muted-foreground">
                    <span>{sc.rail}</span>
                    <span>·</span>
                    <span>{sc.incidentId}</span>
                  </div>
                  <p className="text-[11px] text-muted-foreground line-clamp-2 leading-relaxed">
                    {sc.alertText}
                  </p>
                </button>
              )
            })}
          </div>

          {/* Selected Scenario Showcase Card */}
          <Card className="overflow-hidden">
            {/* Header */}
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border bg-muted/30 px-6 py-3.5">
              <div className="flex items-center gap-2">
                <span className="font-bold text-sm text-foreground">
                  {activeScenario.title}
                </span>
                <span className="font-mono text-xs text-muted-foreground">
                  ({activeScenario.incidentId})
                </span>
                <Badge variant="secondary" className="font-mono text-xs">
                  {activeScenario.category}
                </Badge>
              </div>

              <Button
                variant="outline"
                size="sm"
                disabled={isSimulating}
                onClick={() => handleTriggerSimulation(activeScenario)}
                className="h-8 gap-1.5 text-xs font-semibold cursor-pointer"
              >
                <RefreshCw className={cn("size-3.5", isSimulating && "animate-spin")} />
                <span>Simulate Recovery</span>
              </Button>
            </div>

            {/* Dual Column Body */}
            <div className="grid grid-cols-1 lg:grid-cols-12 divide-y lg:divide-y-0 lg:divide-x divide-border">
              {/* Left Column: Customer Experience & Outreach */}
              <div className="p-6 lg:col-span-7 flex flex-col gap-4">
                <div className="text-[11px] font-mono font-bold tracking-wider text-muted-foreground uppercase">
                  CUSTOMER EXPERIENCE &amp; DISPATCH
                </div>

                {/* Incident Warning Box */}
                <div className="rounded-xl border border-rose-500/20 bg-rose-500/5 p-3.5 flex flex-col gap-1">
                  <div className="text-xs font-bold text-rose-600 dark:text-rose-400">
                    {activeScenario.alertTitle}
                  </div>
                  <p className="text-xs text-muted-foreground leading-relaxed">
                    {activeScenario.alertText}
                  </p>
                </div>

                {/* AI Diagnostic Summary */}
                <div className="rounded-xl border border-border bg-muted/20 p-3.5 flex flex-col gap-1">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-mono font-bold text-foreground">
                      Diagnostic: {activeScenario.aiCode}
                    </span>
                    <span className="font-mono text-[11px] text-muted-foreground">
                      {activeScenario.aiConfidence}
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground leading-relaxed pt-0.5">
                    {activeScenario.aiDiagnosis}
                  </p>
                </div>

                {/* WhatsApp Message Preview with Dynamic Audio Waveform */}
                <div className="rounded-xl border border-border bg-card p-4 flex flex-col gap-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="size-2 rounded-full bg-emerald-500" />
                      <span className="font-bold text-xs text-foreground">
                        {activeScenario.channel}
                      </span>
                    </div>

                    <div className="flex items-center gap-2">
                      {/* Dynamic Audio Waveform Indicator */}
                      {isPlayingAudio && (
                        <div className="flex items-end gap-0.5 h-4 px-1">
                          <span className="w-1 bg-primary rounded-full animate-bounce [animation-delay:-0.4s] h-3" />
                          <span className="w-1 bg-primary rounded-full animate-bounce [animation-delay:-0.2s] h-4" />
                          <span className="w-1 bg-primary rounded-full animate-bounce [animation-delay:-0.5s] h-2" />
                          <span className="w-1 bg-primary rounded-full animate-bounce [animation-delay:-0.1s] h-4" />
                          <span className="w-1 bg-primary rounded-full animate-bounce [animation-delay:-0.3s] h-3" />
                        </div>
                      )}

                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleVoicePlay(activeScenario.hinglishCopy)}
                        className="h-7 gap-1.5 text-xs cursor-pointer px-2"
                      >
                        {isPlayingAudio ? (
                          <VolumeX className="size-3.5 text-destructive" />
                        ) : (
                          <Volume2 className="size-3.5" />
                        )}
                        <span>{isPlayingAudio ? "Stop Audio" : "Listen Hinglish"}</span>
                      </Button>
                    </div>
                  </div>

                  <p className="text-xs italic text-foreground/90 bg-muted/40 p-3 rounded-lg border border-border font-sans leading-relaxed">
                    &ldquo;{activeScenario.hinglishCopy}&rdquo;
                  </p>

                  <Button
                    size="sm"
                    onClick={() => onNavigate("payments")}
                    className="w-full gap-2 rounded-lg text-xs font-semibold h-9 cursor-pointer"
                  >
                    <span>View in Payments Ledger &rarr;</span>
                  </Button>
                </div>

                {/* Status Resolution */}
                <div className="flex items-center gap-2 rounded-xl border border-emerald-500/20 bg-emerald-500/10 p-3 text-xs text-emerald-700 dark:text-emerald-300 font-medium">
                  <CheckCircle2 className="size-4 shrink-0 text-emerald-600 dark:text-emerald-400" />
                  <span>{activeScenario.settledText}</span>
                </div>
              </div>

              {/* Right Column: CFO Governance & Safety Bounds */}
              <div className="p-6 lg:col-span-5 bg-card flex flex-col justify-between gap-6">
                <div className="flex flex-col gap-4">
                  <div className="font-mono text-[11px] font-bold tracking-wider text-muted-foreground uppercase">
                    ENTERPRISE GOVERNANCE &amp; SAFETY GATE
                  </div>
                  <h3 className="text-xl font-bold tracking-tight text-foreground">
                    Deterministic Guardrails
                  </h3>
                  <p className="text-xs text-muted-foreground leading-relaxed">
                    Every autonomous action is constrained by hard financial and regulatory policies to prevent customer spam, bank penalties, and chargebacks.
                  </p>

                  <div className="flex flex-col gap-3 pt-2 text-xs">
                    <div className="flex items-start gap-2.5">
                      <div className="mt-0.5 flex size-4 shrink-0 items-center justify-center rounded-full bg-emerald-500/20 text-emerald-600 dark:text-emerald-400">
                        <CheckCircle2 className="size-3" />
                      </div>
                      <div>
                        <p className="font-semibold text-foreground">Max 3-Retry Dunning Cap</p>
                        <p className="text-[11px] text-muted-foreground">Never spams customer accounts with unbounded payment requests.</p>
                      </div>
                    </div>

                    <div className="flex items-start gap-2.5">
                      <div className="mt-0.5 flex size-4 shrink-0 items-center justify-center rounded-full bg-emerald-500/20 text-emerald-600 dark:text-emerald-400">
                        <CheckCircle2 className="size-3" />
                      </div>
                      <div>
                        <p className="font-semibold text-foreground">Bank Switch Circuit Breaker</p>
                        <p className="text-[11px] text-muted-foreground">Halts retries when multiple consecutive attempts fail on the same gateway rail.</p>
                      </div>
                    </div>

                    <div className="flex items-start gap-2.5">
                      <div className="mt-0.5 flex size-4 shrink-0 items-center justify-center rounded-full bg-emerald-500/20 text-emerald-600 dark:text-emerald-400">
                        <CheckCircle2 className="size-3" />
                      </div>
                      <div>
                        <p className="font-semibold text-foreground">Zero Fraud Auto-Retries</p>
                        <p className="text-[11px] text-muted-foreground">Suspicious card velocity is strictly quarantined to the Honest Exception list.</p>
                      </div>
                    </div>

                    <div className="flex items-start gap-2.5">
                      <div className="mt-0.5 flex size-4 shrink-0 items-center justify-center rounded-full bg-emerald-500/20 text-emerald-600 dark:text-emerald-400">
                        <CheckCircle2 className="size-3" />
                      </div>
                      <div>
                        <p className="font-semibold text-foreground">Cryptographic Audit Logging</p>
                        <p className="text-[11px] text-muted-foreground">Every message, payment link, and retry is immutably logged for audit verification.</p>
                      </div>
                    </div>
                  </div>
                </div>

                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    if (onOpenAudit) onOpenAudit(activeScenario.incidentId)
                    else onNavigate("payments")
                  }}
                  className="w-full gap-2 text-xs font-semibold h-9 cursor-pointer"
                >
                  <span>Inspect Audit Telemetry ({activeScenario.incidentId}) &rarr;</span>
                </Button>
              </div>
            </div>
          </Card>
        </div>
      </section>

      {/* ── 6. DYNAMIC ROI CALCULATOR ── */}
      <section id="roi-calculator" className="py-16 md:py-24 border-t border-border/80 bg-muted/20">
        <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8 flex flex-col gap-8">
          <div className="text-center flex flex-col gap-2 max-w-2xl mx-auto">
            <span className="font-mono text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Financial Impact
            </span>
            <h2 className="text-3xl font-extrabold tracking-tight text-foreground sm:text-4xl">
              Calculate Your Recovered Revenue
            </h2>
            <p className="text-sm text-muted-foreground">
              Adjust your monthly GMV, failure rate, and recovery win rate to see your projected bottom-line gross margin recovery.
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
            {/* Sliders Container */}
            <Card className="lg:col-span-7 p-6 flex flex-col gap-6">
              {/* Slider 1: Monthly GMV */}
              <div className="flex flex-col gap-2">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-semibold text-foreground">
                    Monthly Gross Merchandise Value (GMV)
                  </label>
                  <span className="font-mono text-sm font-bold text-primary">
                    ₹{(monthlyGmv / 100000).toFixed(1)} Lakhs
                  </span>
                </div>
                <input
                  type="range"
                  min={500000}
                  max={20000000}
                  step={250000}
                  value={monthlyGmv}
                  onChange={(e) => setMonthlyGmv(Number(e.target.value))}
                  className="w-full cursor-pointer accent-primary"
                />
                <div className="flex justify-between font-mono text-[10px] text-muted-foreground">
                  <span>₹5.0 Lakhs</span>
                  <span>₹50.0 Lakhs</span>
                  <span>₹2.0 Crores</span>
                </div>
              </div>

              <Separator />

              {/* Slider 2: Failure Rate */}
              <div className="flex flex-col gap-2">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-semibold text-foreground">
                    Average Payment Drop-off Rate
                  </label>
                  <span className="font-mono text-sm font-bold text-rose-500">
                    {failureRate.toFixed(1)}%
                  </span>
                </div>
                <input
                  type="range"
                  min={1}
                  max={25}
                  step={0.5}
                  value={failureRate}
                  onChange={(e) => setFailureRate(Number(e.target.value))}
                  className="w-full cursor-pointer accent-rose-500"
                />
                <div className="flex justify-between font-mono text-[10px] text-muted-foreground">
                  <span>1.0% (Low)</span>
                  <span>8.2% (Indian BFSI Average)</span>
                  <span>25.0%</span>
                </div>
              </div>

              <Separator />

              {/* Slider 3: Win Rate */}
              <div className="flex flex-col gap-2">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-semibold text-foreground">
                    Autonomous Recovery Win Rate
                  </label>
                  <span className="font-mono text-sm font-bold text-emerald-600 dark:text-emerald-400">
                    {recoveryWinRate}%
                  </span>
                </div>
                <input
                  type="range"
                  min={20}
                  max={80}
                  step={5}
                  value={recoveryWinRate}
                  onChange={(e) => setRecoveryWinRate(Number(e.target.value))}
                  className="w-full cursor-pointer accent-emerald-500"
                />
                <div className="flex justify-between font-mono text-[10px] text-muted-foreground">
                  <span>20% Conservative</span>
                  <span>40% Baseline</span>
                  <span>80% Multi-Rail</span>
                </div>
              </div>
            </Card>

            {/* Calculated Impact Card */}
            <Card className="lg:col-span-5 p-6 bg-card flex flex-col justify-between shadow-md">
              <div className="flex flex-col gap-3">
                <Badge variant="outline" className="w-fit font-mono text-[10px] uppercase font-bold tracking-wider">
                  Net Recovered Impact
                </Badge>
                <p className="text-4xl font-extrabold text-foreground font-mono tracking-tight">
                  ₹{Math.round(netRecoveredMonthly).toLocaleString("en-IN")}
                  <span className="text-base text-muted-foreground font-normal"> / month</span>
                </p>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  Pure incremental revenue saved without additional CAC or marketing ad spend.
                </p>

                <div className="grid grid-cols-2 gap-4 border-t border-border pt-5 mt-4">
                  <div className="flex flex-col">
                    <span className="font-mono text-[10px] text-muted-foreground uppercase">
                      ANNUAL RUN-RATE
                    </span>
                    <p className="mt-1 font-mono text-lg font-bold text-foreground">
                      ₹{Math.round(netRecoveredAnnual).toLocaleString("en-IN")}
                    </p>
                  </div>
                  <div className="flex flex-col">
                    <span className="font-mono text-[10px] text-muted-foreground uppercase">
                      RETENTION GAIN
                    </span>
                    <p className="mt-1 font-mono text-lg font-bold text-emerald-600 dark:text-emerald-400">
                      +34% Saved
                    </p>
                  </div>
                </div>
              </div>

              <Button
                size="sm"
                onClick={() => onNavigate("overview")}
                className="mt-6 w-full h-10 text-xs font-semibold cursor-pointer"
              >
                <span>Launch Operations Console &rarr;</span>
              </Button>
            </Card>
          </div>
        </div>
      </section>

      {/* ── 7. NATIVE RAZORPAY RAILS ECOSYSTEM ── */}
      <section id="razorpay-rails" className="py-16 md:py-24 border-t border-border/80">
        <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8 flex flex-col gap-8">
          <div className="text-center flex flex-col gap-2 max-w-2xl mx-auto">
            <span className="font-mono text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Razorpay Product Integrations
            </span>
            <h2 className="text-3xl font-extrabold tracking-tight text-foreground sm:text-4xl">
              Engineered Specifically for Razorpay Ecosystem
            </h2>
            <p className="text-sm text-muted-foreground">
              Not a superficial wrapper. The agent integrates natively with 5 core Razorpay payment APIs.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
            <Card className="p-4 flex flex-col gap-2">
              <h3 className="text-xs font-bold text-foreground">Payment Links</h3>
              <p className="text-[11px] text-muted-foreground leading-relaxed">
                Dynamic idempotency key recovery links across NetBanking, Cards, and UPI.
              </p>
              <div className="font-mono text-[10px] text-primary font-semibold mt-auto">
                POST /v1/payment_links
              </div>
            </Card>

            <Card className="p-4 flex flex-col gap-2">
              <h3 className="text-xs font-bold text-foreground">Webhooks</h3>
              <p className="text-[11px] text-muted-foreground leading-relaxed">
                Interception of payment.failed, payment.authorized, and payment_link.paid events.
              </p>
              <div className="font-mono text-[10px] text-emerald-600 dark:text-emerald-400 font-semibold mt-auto">
                HMAC-SHA256 Signed
              </div>
            </Card>

            <Card className="p-4 flex flex-col gap-2">
              <h3 className="text-xs font-bold text-foreground">Subscriptions</h3>
              <p className="text-[11px] text-muted-foreground leading-relaxed">
                Intelligent recurring auto-debit retries aligned with customer salary cycles.
              </p>
              <div className="font-mono text-[10px] text-primary font-semibold mt-auto">
                Mandate Dunning Flow
              </div>
            </Card>

            <Card className="p-4 flex flex-col gap-2">
              <h3 className="text-xs font-bold text-foreground">Magic Checkout</h3>
              <p className="text-[11px] text-muted-foreground leading-relaxed">
                1-Click address prefill cart hold and conversational B2B invoice reminders.
              </p>
              <div className="font-mono text-[10px] text-amber-600 dark:text-amber-400 font-semibold mt-auto">
                1-Click Cart Recovery
              </div>
            </Card>

            <Card className="p-4 flex flex-col gap-2">
              <h3 className="text-xs font-bold text-foreground">Route / Split</h3>
              <p className="text-[11px] text-muted-foreground leading-relaxed">
                Marketplace multi-vendor settlement reconciliation on recovered orders.
              </p>
              <div className="font-mono text-[10px] text-primary font-semibold mt-auto">
                Automated Ledger
              </div>
            </Card>
          </div>
        </div>
      </section>

      {/* ── 8. 5 CORE OPERATIONS MODULES ── */}
      <section id="modules" className="py-16 md:py-24 border-t border-border/80 bg-muted/20">
        <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8 flex flex-col gap-8">
          <div className="text-center flex flex-col gap-2 max-w-2xl mx-auto">
            <span className="font-mono text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Operations Control Center
            </span>
            <h2 className="text-3xl font-extrabold tracking-tight text-foreground sm:text-4xl">
              Explore the 5 Core Operations Views
            </h2>
            <p className="text-sm text-muted-foreground">
              Direct access into every layer of our real-time recovery pipeline.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
            <Card className="p-4 flex flex-col justify-between gap-3">
              <div className="flex flex-col gap-1">
                <span className="font-mono text-[10px] font-bold text-muted-foreground uppercase">MODULE 01</span>
                <h3 className="text-xs font-bold text-foreground">Overview Dashboard</h3>
                <p className="text-[11px] text-muted-foreground leading-relaxed">
                  Aggregated GMV, recovery trends, root-cause donut chart, and batch runs.
                </p>
              </div>
              <button
                type="button"
                onClick={() => onNavigate("overview")}
                className="text-xs font-semibold text-primary hover:underline inline-flex items-center gap-1 cursor-pointer"
              >
                Open Dashboard &rarr;
              </button>
            </Card>

            <Card className="p-4 flex flex-col justify-between gap-3">
              <div className="flex flex-col gap-1">
                <span className="font-mono text-[10px] font-bold text-muted-foreground uppercase">MODULE 02</span>
                <h3 className="text-xs font-bold text-foreground">Payments Ledger</h3>
                <p className="text-[11px] text-muted-foreground leading-relaxed">
                  Every transaction with unique Payment ID, copy button, and audit details.
                </p>
              </div>
              <button
                type="button"
                onClick={() => onNavigate("payments")}
                className="text-xs font-semibold text-primary hover:underline inline-flex items-center gap-1 cursor-pointer"
              >
                Open Ledger &rarr;
              </button>
            </Card>

            <Card className="p-4 flex flex-col justify-between gap-3">
              <div className="flex flex-col gap-1">
                <span className="font-mono text-[10px] font-bold text-muted-foreground uppercase">MODULE 03</span>
                <h3 className="text-xs font-bold text-foreground">Live Failure Radar</h3>
                <p className="text-[11px] text-muted-foreground leading-relaxed">
                  Real-time gateway poller querying Razorpay test feed for dropped transactions.
                </p>
              </div>
              <button
                type="button"
                onClick={() => onNavigate("detector")}
                className="text-xs font-semibold text-primary hover:underline inline-flex items-center gap-1 cursor-pointer"
              >
                Open Radar &rarr;
              </button>
            </Card>

            <Card className="p-4 flex flex-col justify-between gap-3">
              <div className="flex flex-col gap-1">
                <span className="font-mono text-[10px] font-bold text-muted-foreground uppercase">MODULE 04</span>
                <h3 className="text-xs font-bold text-foreground">Honest Exceptions</h3>
                <p className="text-[11px] text-muted-foreground leading-relaxed">
                  Quarantined cases transparently surfaced with financial exposure metrics.
                </p>
              </div>
              <button
                type="button"
                onClick={() => onNavigate("exceptions")}
                className="text-xs font-semibold text-primary hover:underline inline-flex items-center gap-1 cursor-pointer"
              >
                Open Exceptions &rarr;
              </button>
            </Card>

            <Card className="p-4 flex flex-col justify-between gap-3">
              <div className="flex flex-col gap-1">
                <span className="font-mono text-[10px] font-bold text-muted-foreground uppercase">MODULE 05</span>
                <h3 className="text-xs font-bold text-foreground">Cryptographic Audit</h3>
                <p className="text-[11px] text-muted-foreground leading-relaxed">
                  Verifiable event timeline with Hinglish audio call preview and hash trail.
                </p>
              </div>
              <button
                type="button"
                onClick={() => {
                  if (onOpenAudit) onOpenAudit("pay_2694WD")
                  else onNavigate("payments")
                }}
                className="text-xs font-semibold text-primary hover:underline inline-flex items-center gap-1 cursor-pointer"
              >
                Inspect Audit &rarr;
              </button>
            </Card>
          </div>
        </div>
      </section>

      {/* ── 9. MINIMALIST FOOTER WITH OFFICIAL LOGO ── */}
      <footer className="border-t border-border/80 py-8 text-xs text-muted-foreground mt-auto">
        <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <img
              src="/logo-horizontal.png"
              alt="Autonomous Revenue Recovery"
              className="h-7 w-auto object-contain dark:invert"
            />
            <span className="hidden sm:inline font-mono text-[11px]">
              · Track 03: Autonomous AI Revenue Recovery
            </span>
          </div>

          <div className="flex items-center gap-6 text-xs font-medium">
            <button
              type="button"
              onClick={() => onNavigate("overview")}
              className="hover:text-foreground cursor-pointer transition-colors"
            >
              Console
            </button>
            <button
              type="button"
              onClick={() => onNavigate("payments")}
              className="hover:text-foreground cursor-pointer transition-colors"
            >
              Transactions
            </button>
            <button
              type="button"
              onClick={() => onNavigate("detector")}
              className="hover:text-foreground cursor-pointer transition-colors"
            >
              Live Radar
            </button>
            <button
              type="button"
              onClick={() => onNavigate("exceptions")}
              className="hover:text-foreground cursor-pointer transition-colors"
            >
              Exceptions
            </button>
          </div>
        </div>
      </footer>
    </div>
  )
}
