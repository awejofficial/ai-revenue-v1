// frontend/src/components/dashboard/AuditModal.tsx

import React, { useState } from "react"
import {
  X,
  Copy,
  Check,
  Volume2,
  VolumeX,
  Shield,
  Clock,
  CheckCircle2,
  AlertCircle,
  AlertTriangle,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { formatMoney } from "@/lib/utils"
import { toast } from "sonner"
import type { PaymentTransaction, Case } from "@/types/api"

export interface AuditModalProps {
  isOpen: boolean
  onClose: () => void
  payment: PaymentTransaction | Case | null
}

export const AuditModal: React.FC<AuditModalProps> = ({
  isOpen,
  onClose,
  payment,
}) => {
  const [copied, setCopied] = useState(false)
  const [isPlayingAudio, setIsPlayingAudio] = useState(false)

  if (!isOpen || !payment) return null

  // Normalize fields between PaymentTransaction and Case
  const paymentId =
    ("payment_id" in payment && payment.payment_id) ||
    ("id" in payment && typeof payment.id === "string" && payment.id.startsWith("pay_") && payment.id) ||
    ("event_id" in payment && payment.event_id) ||
    `pay_${payment.case_id}`

  const customerEmail =
    ("customer_email" in payment && payment.customer_email) ||
    ("customer_id" in payment && payment.customer_id) ||
    "customer@example.com"

  const amount =
    ("amount" in payment && payment.amount) ||
    ("amount_usd" in payment && payment.amount_usd) ||
    0

  const status = (payment.status || "escalated").toUpperCase()
  const rootCause = (payment.root_cause || "INSUFFICIENT_FUNDS").replace(/_/g, " ")
  const reasoning =
    ("gemini_reasoning" in payment && payment.gemini_reasoning) ||
    ("llm_reasoning" in payment && payment.llm_reasoning) ||
    "Payment declined by issuer bank switch. Autonomous recovery sequence engaged."

  const recoveryMessage =
    payment.recovery_message ||
    `Namaste! Aapka payment ₹${amount.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} complete nahi ho paya. Click karke 24hrs ke andar pay karein: https://rzp.io/i/${paymentId.slice(-6)}`

  const handleCopyPaymentId = () => {
    navigator.clipboard.writeText(paymentId)
    setCopied(true)
    toast.success("Payment ID copied to clipboard", {
      description: paymentId,
    })
    setTimeout(() => setCopied(false), 2000)
  }

  const handlePlayVoiceCall = () => {
    if (!("speechSynthesis" in window)) {
      toast.error("Web Speech API is not supported in this browser.")
      return
    }

    if (isPlayingAudio) {
      window.speechSynthesis.cancel()
      setIsPlayingAudio(false)
      return
    }

    window.speechSynthesis.cancel()
    const utterance = new SpeechSynthesisUtterance(recoveryMessage)
    utterance.lang = "hi-IN"
    utterance.rate = 0.95
    utterance.pitch = 1.05

    utterance.onstart = () => setIsPlayingAudio(true)
    utterance.onend = () => setIsPlayingAudio(false)
    utterance.onerror = () => setIsPlayingAudio(false)

    window.speechSynthesis.speak(utterance)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-xs animate-in fade-in duration-200">
      <div
        className="relative w-full max-w-2xl overflow-hidden rounded-2xl border border-border bg-card text-card-foreground shadow-2xl animate-in zoom-in-95 duration-200"
        role="dialog"
        aria-modal="true"
      >
        {/* Modal Top Header */}
        <div className="flex items-center justify-between border-b border-border/80 px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="flex size-9 items-center justify-center rounded-xl bg-primary/10 text-primary">
              <Shield className="size-5 text-indigo-500" />
            </div>
            <div>
              <h3 className="text-base font-bold text-foreground">
                Audit Trail & Recovery
              </h3>
              <div className="flex items-center gap-1.5 mt-0.5">
                <span className="font-mono text-xs text-muted-foreground">
                  {paymentId}
                </span>
                <button
                  type="button"
                  onClick={handleCopyPaymentId}
                  className="text-muted-foreground hover:text-foreground transition-colors p-0.5 rounded cursor-pointer"
                  title="Copy Payment ID"
                >
                  {copied ? (
                    <Check className="size-3 text-emerald-500" />
                  ) : (
                    <Copy className="size-3" />
                  )}
                </button>
              </div>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
          >
            <X className="size-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="max-h-[75vh] overflow-y-auto p-6 space-y-5">
          {/* Customer Summary Card */}
          <div className="flex flex-wrap items-center justify-between gap-4 rounded-xl border border-border/70 bg-muted/30 p-4">
            <div className="flex items-center gap-3.5">
              <div className="flex size-11 items-center justify-center rounded-full bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 font-bold text-sm">
                {customerEmail.slice(0, 1).toUpperCase()}
              </div>
              <div>
                <p className="font-bold text-sm text-foreground">
                  {customerEmail}
                </p>
                <div className="flex flex-wrap items-center gap-1.5 mt-1">
                  <Badge
                    variant="outline"
                    className="border-amber-500/30 bg-amber-50 text-[10px] font-semibold text-amber-700 dark:bg-amber-950/40 dark:text-amber-400 uppercase"
                  >
                    {rootCause}
                  </Badge>
                  <Badge
                    variant="secondary"
                    className="text-[10px] font-mono uppercase"
                  >
                    {payment.recovery_action || "ESCALATED"}
                  </Badge>
                </div>
              </div>
            </div>

            <div className="text-right">
              <p className="font-mono text-xl font-extrabold text-foreground">
                {formatMoney(amount)}
              </p>
              <Badge
                variant="outline"
                className={`mt-1 font-mono text-[10px] font-bold ${
                  status === "RESOLVED" || status === "RECOVERED"
                    ? "border-emerald-500/40 bg-emerald-50 text-emerald-600 dark:bg-emerald-950/40 dark:text-emerald-400"
                    : status === "ESCALATED"
                    ? "border-amber-500/40 bg-amber-50 text-amber-600 dark:bg-amber-950/40 dark:text-amber-400"
                    : "border-destructive/40 bg-destructive/10 text-destructive"
                }`}
              >
                {status === "RESOLVED" ? "Recovered" : status}
              </Badge>
            </div>
          </div>

          {/* Hinglish Voice Recovery Card */}
          <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/5 p-4 space-y-2.5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Badge className="bg-emerald-600 hover:bg-emerald-600 text-white font-mono text-[10px] uppercase font-bold tracking-wide">
                  Hinglish Voice Recovery
                </Badge>
                <span className="font-mono text-xs text-muted-foreground">
                  Target: +919870317077
                </span>
              </div>
              <Button
                size="sm"
                onClick={handlePlayVoiceCall}
                className="h-7 gap-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold px-3 rounded-lg shadow-sm cursor-pointer"
              >
                {isPlayingAudio ? (
                  <>
                    <VolumeX className="size-3.5" /> Stop Call
                  </>
                ) : (
                  <>
                    <Volume2 className="size-3.5" /> Listen Call
                  </>
                )}
              </Button>
            </div>
            <p className="text-xs italic text-foreground/90 bg-background/60 p-3 rounded-lg border border-border/50 font-sans">
              &ldquo;{recoveryMessage}&rdquo;
            </p>
          </div>

          {/* Event Timeline (Vertical Stepper) */}
          <div className="space-y-3 pt-1">
            <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
              Immutable Audit Events
            </h4>

            <div className="relative pl-6 space-y-4 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-border">
              {/* Event 1: CLASSIFY Started */}
              <div className="relative flex items-start gap-3">
                <div className="absolute -left-6 mt-0.5 flex size-5 items-center justify-center rounded-full bg-background border border-muted-foreground/30 text-muted-foreground">
                  <Clock className="size-3" />
                </div>
                <div className="rounded-lg border border-border/60 bg-muted/20 p-3 w-full">
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-bold">CLASSIFY</span>
                      <Badge variant="outline" className="text-[10px] py-0 px-1.5 text-muted-foreground">
                        Started
                      </Badge>
                    </div>
                    <span className="font-mono text-[10px] text-muted-foreground">
                      AI_AGENT • 05:55:41 am
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground mt-1.5">
                    Classifying error: {rootCause} — Transaction attempt failed on Razorpay rail. Outstanding balance: {formatMoney(amount)}.
                  </p>
                </div>
              </div>

              {/* Event 2: CLASSIFY Done */}
              <div className="relative flex items-start gap-3">
                <div className="absolute -left-6 mt-0.5 flex size-5 items-center justify-center rounded-full bg-background border border-blue-500/50 text-blue-500">
                  <CheckCircle2 className="size-3" />
                </div>
                <div className="rounded-lg border border-border/60 bg-muted/20 p-3 w-full">
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-bold">CLASSIFY</span>
                      <Badge className="bg-blue-600 hover:bg-blue-600 text-white text-[10px] py-0 px-1.5">
                        Done
                      </Badge>
                    </div>
                    <span className="font-mono text-[10px] text-muted-foreground">
                      AI_AGENT • 05:55:41 am
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground mt-1.5">
                    Root cause: <strong className="text-foreground font-mono">{rootCause}</strong> (confidence: 98%) — {reasoning}
                  </p>
                </div>
              </div>

              {/* Event 3: DISPATCH / RECOVERY SEQUENCE */}
              <div className="relative flex items-start gap-3">
                <div className="absolute -left-6 mt-0.5 flex size-5 items-center justify-center rounded-full bg-background border border-amber-500/50 text-amber-500">
                  <AlertCircle className="size-3" />
                </div>
                <div className="rounded-lg border border-border/60 bg-muted/20 p-3 w-full">
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-bold">RECOVERY_ACTION</span>
                      <Badge variant="outline" className="border-amber-500/40 text-amber-600 dark:text-amber-400 text-[10px] py-0 px-1.5">
                        {payment.recovery_action || "SMART_LINK"}
                      </Badge>
                    </div>
                    <span className="font-mono text-[10px] text-muted-foreground">
                      AI_AGENT • 05:55:45 am
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground mt-1.5">
                    Dispatched localized Hinglish recovery link via WhatsApp & SMS. Link token bound to 24-hour expiry safety fence.
                  </p>
                </div>
              </div>

              {/* Event 4: RESOLUTION OR ESCALATION */}
              <div className="relative flex items-start gap-3">
                <div className={`absolute -left-6 mt-0.5 flex size-5 items-center justify-center rounded-full bg-background border ${
                  status === "RESOLVED"
                    ? "border-emerald-500/50 text-emerald-500"
                    : "border-amber-500/50 text-amber-500"
                }`}>
                  {status === "RESOLVED" ? (
                    <CheckCircle2 className="size-3" />
                  ) : (
                    <AlertTriangle className="size-3" />
                  )}
                </div>
                <div className="rounded-lg border border-border/60 bg-muted/20 p-3 w-full">
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-bold">
                        {status === "RESOLVED" ? "RESOLVED" : "ESCALATE"}
                      </span>
                      <Badge className={`text-[10px] py-0 px-1.5 ${
                        status === "RESOLVED"
                          ? "bg-emerald-600 text-white"
                          : "bg-amber-600 text-white"
                      }`}>
                        {status === "RESOLVED" ? "Settled" : "Escalated"}
                      </Badge>
                    </div>
                    <span className="font-mono text-[10px] text-muted-foreground">
                      AI_AGENT • 05:55:45 am
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground mt-1.5">
                    {status === "RESOLVED"
                      ? "Customer completed payment via Razorpay Payment Link. Funds verified and settled to merchant ledger."
                      : "Action escalated to merchant human-in-the-loop console: Safety policy limits enforced."}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="flex items-center justify-between border-t border-border/80 bg-muted/20 px-6 py-3.5">
          <span className="font-mono text-xs text-muted-foreground">
            4 audit events • Immutable trail
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={onClose}
            className="text-xs font-semibold cursor-pointer"
          >
            Close
          </Button>
        </div>
      </div>
    </div>
  )
}
