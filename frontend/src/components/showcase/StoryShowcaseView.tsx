// frontend/src/components/showcase/StoryShowcaseView.tsx

import React, { useState } from "react"
import {
  Sparkles,
  Volume2,
  VolumeX,
  CheckCircle2,
  ShieldCheck,
  Zap,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { api, type SimulationScenario } from "@/lib/api"
import { toast } from "sonner"

interface ScenarioStory {
  id: string
  title: string
  persona: string
  merchant: string
  city: string
  amount: number
  category: string
  categoryColor: string
  categoryBg: string
  scenarioKey: SimulationScenario
  problemTitle: string
  problemText: string
  solutionTitle: string
  solutionText: string
  errorCode: string
  rootCause: string
  hinglishCopy: string
  outcome: string
  complianceRule: string
  voiceUtterance: string
}

const STORIES: ScenarioStory[] = [
  {
    id: "insufficient_funds",
    title: "Low Balance on UPI",
    persona: "Priya Sharma",
    merchant: "The Souled Store",
    city: "Mumbai",
    amount: 4499,
    category: "UPI / Account Balance",
    categoryColor: "text-amber-600 dark:text-amber-400",
    categoryBg: "bg-amber-500/10 border-amber-500/20",
    scenarioKey: "high_ltv_insufficient_funds",
    problemTitle: "Bank Account Just ₹180 Short at Checkout",
    problemText: "Priya clicked 'Pay' with her primary SBI UPI account, but her balance was ₹180 short of the ₹4,499 total. The payment failed instantly, leaving her frustrated at the final step.",
    solutionTitle: "Personalized Hinglish WhatsApp Recovery Link",
    solutionText: "The AI agent diagnoses the decline as an account balance threshold, preserves her reserved cart, and dispatches a multi-rail Razorpay link so Priya can pay seamlessly via PhonePe, GPay, or a credit card.",
    errorCode: "BAD_REQUEST_INSUFFICIENT_FUNDS",
    rootCause: "INSUFFICIENT_FUNDS",
    hinglishCopy: "Hi Priya! Aapka ₹4,499 ka order complete nahi ho paya. Kisi doosre account ya alternate UPI app se turant payment complete karne ke liye is link par tap karein: https://rzp.io/i/plink_PriyaUPI",
    outcome: "₹4,499 Recovered (Priya completed payment via PhonePe in 3.8 minutes)",
    complianceRule: "Auto-retries blocked to prevent customer bank NSF bounce charges.",
    voiceUtterance: "Namaste Priya! The Souled Store se aapka ₹4,499 ka order balance ki wajah se ruk gaya tha. Please alternate UPI app se payment complete karne ke liye hamare link par tap karein.",
  },
  {
    id: "network_timeout",
    title: "HDFC Switch Timeout",
    persona: "Rahul Verma",
    merchant: "Zepto Quick Commerce",
    city: "Bengaluru",
    amount: 12850,
    category: "Gateway Downtime Glitch",
    categoryColor: "text-blue-600 dark:text-blue-400",
    categoryBg: "bg-blue-500/10 border-blue-500/20",
    scenarioKey: "repeat_failure",
    problemTitle: "Bank Switch Timeout at 2FA Step",
    problemText: "Rahul entered his OTP, but the bank switch timed out after 30 seconds due to an evening traffic spike. Rahul stared at a blank screen wondering if his money was deducted.",
    solutionTitle: "Autonomous Idempotent Switch Retry",
    solutionText: "The AI agent recognizes an upstream network glitch, verifies idempotency headers to prevent double-charging, and automatically re-routes the authorization to a secondary clearing rail in under 820ms.",
    errorCode: "GATEWAY_ERROR_TIMED_OUT",
    rootCause: "NETWORK_TIMEOUT",
    hinglishCopy: "Hi Rahul! Bank server me temporary delay ki wajah se transaction ruk gaya tha. Humne bina kisi extra charge ke auto-retry kar ke aapka order confirm kar diya hai!",
    outcome: "₹12,850 Recovered (Re-authorized on fallback switch in 820ms)",
    complianceRule: "Circuit breaker active: batch halts immediately if 2 consecutive bank failures occur.",
    voiceUtterance: "Namaste Rahul! Zepto order ke bank switch me temporary delay tha. Humne bina kisi extra charge ke order confirm kar diya hai.",
  },
  {
    id: "checkout_abandoned",
    title: "Magic Checkout Cart Drop-off",
    persona: "Ananya Sen",
    merchant: "Lenskart Online",
    city: "Kolkata",
    amount: 2299,
    category: "Funnel Abandonment",
    categoryColor: "text-cyan-600 dark:text-cyan-400",
    categoryBg: "bg-cyan-500/10 border-cyan-500/20",
    scenarioKey: "checkout_drop_off",
    problemTitle: "Cart Dropped at OTP Screen",
    problemText: "Ananya auto-filled her prescription and shipping address on Razorpay Magic Checkout, but closed her mobile browser before entering the OTP when interrupted by a call.",
    solutionTitle: "1-Click WhatsApp Cart Hold with VIP Incentive",
    solutionText: "The AI agent reserves her frames for 45 minutes and sends a friendly 1-click WhatsApp cart recovery notification with a personalized 10% VIP coupon code (RECOVER10).",
    errorCode: "CHECKOUT_ABANDONED_STEP_OTP",
    rootCause: "CHECKOUT_ABANDONED",
    hinglishCopy: "Hi Ananya! Aapka cart reserve kar diya gaya hai! Sirf 1-tap me bina dobara details bhare apna order complete karein (Applied 10% off code RECOVER10): https://rzp.io/i/cart_Ananya",
    outcome: "₹2,299 Recovered (Ananya completed checkout via WhatsApp in 5.4 minutes)",
    complianceRule: "Strict frequency capping: maximum 1 reminder per checkout session.",
    voiceUtterance: "Hi Ananya! Lenskart par aapka cart reserve kar diya gaya hai. Sirf ek tap me bina dobara details bhare apna order complete karein.",
  },
  {
    id: "fraud_flag",
    title: "Suspicious Velocity Spike",
    persona: "Untrusted Device (Proxy Pool)",
    merchant: "Apple Premium Reseller",
    city: "Frankfurt Proxy",
    amount: 89500,
    category: "Compliance Lockdown",
    categoryColor: "text-red-700 dark:text-red-400",
    categoryBg: "bg-red-500/15 border-red-500/30",
    scenarioKey: "fraud",
    problemTitle: "4 Rapid International Card Attempts from VPN Proxy",
    problemText: "An untrusted IP pool attempted 4 rapid high-value transactions for iPhone 16 Pro using masked BINs within 90 seconds. Traditional dunning tools would blindly spam SMS/retries.",
    solutionTitle: "Instant Human Escalation & Complete Outreach Lockout",
    solutionText: "The AI agent enforces an immediate shutdown of all auto-retries, blocks all outgoing customer notifications to prevent card-probing, and pushes the alert to the Slack risk queue.",
    errorCode: "FRAUD_SUSPECTED_VELOCITY_SPIKE",
    rootCause: "FRAUD_FLAG",
    hinglishCopy: "[OUTBOUND COMMUNICATION BLOCKED FOR SECURITY — ESCALATED TO HUMAN COMPLIANCE OFFICER]",
    outcome: "100% Chargeback Protected. ₹89,500 Fraud Attempt Neutralized.",
    complianceRule: "Strict Zero-Auto-Retry policy on FRAUD_FLAG. No automated retries allowed.",
    voiceUtterance: "Security alert. Suspicious proxy activity detected. Autonomous outreach locked. Transaction routed to fraud compliance officer.",
  },
  {
    id: "overdue_invoice",
    title: "B2B Enterprise Invoice Overdue",
    persona: "Apex Technologies Ltd",
    merchant: "CloudScale SaaS",
    city: "Gurugram",
    amount: 115000,
    category: "B2B Receivables",
    categoryColor: "text-teal-600 dark:text-teal-400",
    categoryBg: "bg-teal-500/10 border-teal-500/20",
    scenarioKey: "high_ltv_insufficient_funds",
    problemTitle: "Net-30 Invoice Past Terms with No Response",
    problemText: "Annual software subscription invoice #INV-2025-084 for ₹1,15,000 remained unpaid 14 days past the Net-30 deadline. Manual email follow-ups were lost in accounts payable inboxes.",
    solutionTitle: "B2B Dunning Sequencer with 7-Day Grace Window",
    solutionText: "The AI agent initiates progressive dunning with an official Razorpay settlement link, sets automated payment reminders, and schedules an automatic escalation to the Finance VP if unpaid by Day 7.",
    errorCode: "INVOICE_OVERDUE_NET30",
    rootCause: "OVERDUE_INVOICE",
    hinglishCopy: "Dear Accounts Team, Outstanding invoice #INV-2025-084 for ₹1,15,000 is past net terms. Please clear via this secure Razorpay link: https://rzp.io/i/plink_B2B_Apex",
    outcome: "₹1,15,000 Recovered (Days Sales Outstanding reduced by 14 days)",
    complianceRule: "Promise-to-Pay tracking window with automated Finance VP escalation on Day 7.",
    voiceUtterance: "Dear Accounts Team, Outstanding annual invoice for ₹1,15,000 is past terms. Please settle securely via the official Razorpay link sent to your registered email.",
  },
]

export const StoryShowcaseView: React.FC = () => {
  const [activeStory, setActiveStory] = useState<ScenarioStory>(STORIES[0])
  const [isPlaying, setIsPlaying] = useState(false)
  const [isSimulating, setIsSimulating] = useState(false)

  const handlePlayVoice = (text: string) => {
    if (!("speechSynthesis" in window)) {
      toast.error("Speech Synthesis API not supported in your browser.")
      return
    }

    if (isPlaying) {
      window.speechSynthesis.cancel()
      setIsPlaying(false)
      return
    }

    const utterance = new SpeechSynthesisUtterance(text)
    utterance.rate = 0.95
    utterance.pitch = 1.05

    // Try to pick an Indian English or female voice if available
    const voices = window.speechSynthesis.getVoices()
    const indianVoice = voices.find((v) => v.lang.includes("IN") || v.name.includes("India"))
    if (indianVoice) {
      utterance.voice = indianVoice
    }

    utterance.onend = () => setIsPlaying(false)
    utterance.onerror = () => setIsPlaying(false)

    setIsPlaying(true)
    window.speechSynthesis.speak(utterance)
  }

  const handleTestScenario = async () => {
    setIsSimulating(true)
    try {
      await api.simulateScenario(activeStory.scenarioKey)
      toast.success(`Simulated scenario: "${activeStory.title}" processed through AI orchestrator!`)
    } catch (err: any) {
      toast.error(`Simulation failed: ${err.message}`)
    } finally {
      setIsSimulating(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="rounded-2xl border border-primary/20 bg-gradient-to-r from-primary/10 via-purple-500/10 to-background p-6 shadow-xs sm:p-8">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 rounded-full border border-primary/30 bg-primary/10 px-3 py-1 text-xs font-semibold text-primary">
              <Sparkles className="size-3.5" />
              <span>Razorpay AI Buildathon 2026 · Track 03</span>
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
              PayBack AI Story Simulator
            </h1>
            <p className="max-w-2xl text-xs text-muted-foreground sm:text-sm">
              Explore how PayBack AI diagnoses real-world Indian BFSI payment failures, executes bounded interventions, generates high-converting Hinglish copy, and enforces compliance guardrails.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Button
              onClick={handleTestScenario}
              disabled={isSimulating}
              className="gap-2 bg-primary text-xs font-medium text-primary-foreground shadow-xs hover:bg-primary/90"
            >
              <Zap className={`size-3.5 ${isSimulating ? "animate-spin" : ""}`} />
              {isSimulating ? "Executing AI Pipeline..." : "Test Scenario Live"}
            </Button>
          </div>
        </div>

        {/* Persona Selector Tabs */}
        <div className="mt-6 flex flex-wrap gap-2">
          {STORIES.map((s) => {
            const isSelected = activeStory.id === s.id
            return (
              <button
                key={s.id}
                type="button"
                onClick={() => {
                  if (isPlaying) {
                    window.speechSynthesis.cancel()
                    setIsPlaying(false)
                  }
                  setActiveStory(s)
                }}
                className={`flex cursor-pointer items-center gap-2 rounded-xl border px-3 py-2 text-xs font-medium transition-all ${
                  isSelected
                    ? "border-primary bg-primary/15 text-primary shadow-xs ring-1 ring-primary/30"
                    : "border-border/80 bg-card/80 text-muted-foreground hover:bg-muted/50 hover:text-foreground"
                }`}
              >
                <span className={`size-2 rounded-full ${isSelected ? "bg-primary animate-ping" : "bg-muted-foreground/50"}`} />
                <span>{s.title}</span>
                <span className="text-[11px] opacity-70">₹{s.amount.toLocaleString("en-IN")}</span>
              </button>
            )
          })}
        </div>
      </div>

      {/* Main Persona Interactive Showcase Card */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Left Col: Persona & The Problem */}
        <div className="space-y-4 rounded-xl border border-border/80 bg-card p-5 shadow-xs">
          <div className="flex items-center justify-between border-b border-border/70 pb-3">
            <div>
              <span className={`inline-block rounded-md border px-2 py-0.5 text-[10px] font-semibold ${activeStory.categoryBg} ${activeStory.categoryColor}`}>
                {activeStory.category}
              </span>
              <h2 className="mt-1 text-base font-bold text-foreground">{activeStory.persona}</h2>
              <p className="text-xs text-muted-foreground">{activeStory.merchant} · {activeStory.city}</p>
            </div>
            <div className="text-right">
              <span className="text-xs text-muted-foreground">Amount</span>
              <p className="text-lg font-bold text-foreground">₹{activeStory.amount.toLocaleString("en-IN")}</p>
            </div>
          </div>

          <div className="space-y-2">
            <span className="text-xs font-bold uppercase tracking-wider text-rose-600 dark:text-rose-400">
              The Problem in Plain English
            </span>
            <h3 className="text-sm font-semibold text-foreground">{activeStory.problemTitle}</h3>
            <p className="text-xs leading-relaxed text-muted-foreground">
              {activeStory.problemText}
            </p>
          </div>

          <div className="rounded-lg border border-border/80 bg-muted/30 p-3 text-xs">
            <div className="text-[11px] font-semibold text-muted-foreground">RAW GATEWAY SIGNAL:</div>
            <div className="mt-1 font-mono text-[11px] text-foreground">{activeStory.errorCode}</div>
            <div className="mt-1 text-[10px] text-muted-foreground">Root Cause Classification: <strong>{activeStory.rootCause}</strong></div>
          </div>
        </div>

        {/* Center Col: Autonomous AI Intervention */}
        <div className="space-y-4 rounded-xl border border-primary/30 bg-card p-5 shadow-xs lg:col-span-2">
          <div className="flex items-center justify-between border-b border-border/70 pb-3">
            <div className="flex items-center gap-2">
              <div className="flex size-7 items-center justify-center rounded-lg bg-primary/10 text-primary">
                <Zap className="size-4" />
              </div>
              <h2 className="text-sm font-bold text-foreground">How PayBack AI Autonomous Recovery Steps In</h2>
            </div>

            {/* Voice Preview Button */}
            <Button
              variant="outline"
              size="sm"
              onClick={() => handlePlayVoice(activeStory.voiceUtterance)}
              className="gap-1.5 text-xs"
            >
              {isPlaying ? (
                <>
                  <VolumeX className="size-3.5 text-rose-500 animate-pulse" />
                  <span>Stop Voice Call</span>
                </>
              ) : (
                <>
                  <Volume2 className="size-3.5 text-primary" />
                  <span>Play Voice Recovery Audio</span>
                </>
              )}
            </Button>
          </div>

          <div className="space-y-2">
            <h3 className="text-sm font-semibold text-foreground">{activeStory.solutionTitle}</h3>
            <p className="text-xs leading-relaxed text-muted-foreground">
              {activeStory.solutionText}
            </p>
          </div>

          {/* Hinglish Copy Preview Card */}
          <div className="rounded-xl border border-primary/20 bg-primary/5 p-4 text-xs">
            <div className="flex items-center justify-between text-primary">
              <span className="font-semibold uppercase tracking-wider text-[11px]">AI-Generated Hinglish Recovery Copy:</span>
              <span className="text-[10px] font-mono">Tailored for Indian Shoppers</span>
            </div>
            <p className="mt-2 text-xs italic font-medium leading-relaxed text-foreground">
              "{activeStory.hinglishCopy}"
            </p>
          </div>

          {/* Outcome & Compliance Guardrails Grid */}
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 pt-2">
            <div className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 p-3 text-xs">
              <div className="flex items-center gap-1.5 font-semibold text-emerald-700 dark:text-emerald-400">
                <CheckCircle2 className="size-4" />
                <span>Verified Business Impact</span>
              </div>
              <p className="mt-1 text-[11px] text-emerald-800 dark:text-emerald-300">
                {activeStory.outcome}
              </p>
            </div>

            <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-3 text-xs">
              <div className="flex items-center gap-1.5 font-semibold text-amber-700 dark:text-amber-400">
                <ShieldCheck className="size-4" />
                <span>Stopping Rule & Compliance Rule</span>
              </div>
              <p className="mt-1 text-[11px] text-amber-800 dark:text-amber-300">
                {activeStory.complianceRule}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
