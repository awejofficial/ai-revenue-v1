import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatMoney(
  amount: number | string | null | undefined,
  currency: string = "INR"
): string {
  const num = typeof amount === "string" ? parseFloat(amount) : Number(amount || 0)
  if (isNaN(num)) return "₹0.00"

  if (currency === "INR" || !currency) {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(num)
  }

  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(num)
}

export function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return "N/A"
  try {
    const d = new Date(dateStr)
    if (isNaN(d.getTime())) return "N/A"
    return d.toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    })
  } catch {
    return dateStr
  }
}

export function formatPercent(val: number | string | null | undefined): string {
  const num = typeof val === "string" ? parseFloat(val) : Number(val || 0)
  if (isNaN(num)) return "0%"
  return `${num.toFixed(1)}%`
}
