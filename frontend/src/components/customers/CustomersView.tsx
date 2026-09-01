// frontend/src/components/customers/CustomersView.tsx

import React, { useState, useEffect, useCallback } from "react"
import { RefreshCw, Search, Users, DollarSign, AlertCircle, ShieldCheck } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Spinner } from "@/components/ui/spinner"
import { MetricCard } from "@/components/layout/MetricCard"
import { SegmentFilter, type SegmentFilterValue } from "@/components/customers/SegmentFilter"
import { CustomerTable } from "@/components/customers/CustomerTable"
import { CustomerDrawer } from "@/components/customers/CustomerDrawer"
import { api } from "@/lib/api"
import { formatMoney } from "@/lib/utils"
import { toast } from "sonner"
import type { CustomerSummary } from "@/types/api"

export const CustomersView: React.FC = () => {
  const [customers, setCustomers] = useState<CustomerSummary[]>([])
  const [selectedCustId, setSelectedCustId] = useState<string | null>(null)
  const [segment, setSegment] = useState<SegmentFilterValue>("all")
  const [search, setSearch] = useState("")
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)

  const loadData = useCallback(async (isSilent = false) => {
    try {
      if (!isSilent) setRefreshing(true)
      const data = await api.getCustomers()
      setCustomers(data)

      setSelectedCustId((prev) => {
        if (prev && data.some((c) => c.customer_id === prev)) return prev
        return data.length > 0 ? data[0].customer_id : null
      })
    } catch (err) {
      console.error("Failed to load customers:", err)
      toast.error("Failed to fetch customer directory")
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [])

  useEffect(() => {
    loadData()
  }, [loadData])

  const handleCartRecovery = async (_customerId: string) => {
    await api.simulateScenario("checkout_drop_off")
    await loadData(true)
  }

  const handleSeedDirectory = async () => {
    try {
      setRefreshing(true)
      await api.seedDatabase()
      toast.success("Demo customer accounts & cases seeded successfully!")
      await loadData(true)
    } catch (err) {
      console.error("Failed to seed:", err)
      toast.error("Failed to seed demo accounts")
    } finally {
      setRefreshing(false)
    }
  }

  // Filter customers by search and segment
  const filteredCustomers = customers.filter((c) => {
    const q = search.toLowerCase()
    const matchQuery =
      c.customer_id.toLowerCase().includes(q) ||
      (c.name && c.name.toLowerCase().includes(q)) ||
      (c.company && c.company.toLowerCase().includes(q))

    if (!matchQuery) return false

    if (segment === "all") return true
    if (segment === "in_recovery") return c.in_progress_count > 0
    return c.segment === segment
  })

  const selectedCustomer =
    customers.find((c) => c.customer_id === selectedCustId) || null

  const totalLtv = customers.reduce((sum, c) => sum + (c.ltv || 0), 0)
  const inRecoveryCount = customers.filter((c) => c.in_progress_count > 0).length
  const totalRecovered = customers.reduce((sum, c) => sum + (c.recovered_amount || 0), 0)

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-border/70 pb-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
            Customer 360° & Risk Intelligence Directory
          </h2>
          <p className="text-xs text-muted-foreground sm:text-sm">
            Holistic account profiling, Lifetime Value (LTV) telemetry, and channel compliance preferences.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {customers.length === 0 && !loading && (
            <Button
              variant="default"
              size="sm"
              disabled={refreshing}
              onClick={handleSeedDirectory}
              className="h-8 text-xs bg-primary text-primary-foreground shadow-xs hover:bg-primary/90"
            >
              {refreshing ? <Spinner data-icon="inline-start" /> : <Users data-icon="inline-start" className="size-3.5" />}
              Seed Demo Directory
            </Button>
          )}

          <Button
            variant="outline"
            size="sm"
            disabled={refreshing}
            onClick={() => loadData(false)}
            className="h-8 text-xs"
          >
            {refreshing ? <Spinner data-icon="inline-start" /> : <RefreshCw data-icon="inline-start" className="size-3.5" />}
            Refresh Directory
          </Button>
        </div>
      </div>

      {/* KPI Metric Strip */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="Managed Accounts"
          value={customers.length}
          subtitle="SaaS & E-Commerce Profiles"
          variant="primary"
          loading={loading}
          icon={<Users className="size-4 text-primary" />}
        />
        <MetricCard
          title="Portfolio Lifetime Value"
          value={formatMoney(totalLtv)}
          subtitle="Cumulative customer value"
          variant="success"
          loading={loading}
          icon={<DollarSign className="size-4 text-emerald-500" />}
        />
        <MetricCard
          title="In-Recovery Accounts"
          value={inRecoveryCount}
          subtitle="Active dunning workflows"
          variant="warning"
          loading={loading}
          icon={<AlertCircle className="size-4 text-amber-500" />}
        />
        <MetricCard
          title="Recovered Lifetime Revenue"
          value={formatMoney(totalRecovered)}
          subtitle="Total won-back cash"
          variant="success"
          loading={loading}
          icon={<ShieldCheck className="size-4 text-emerald-500" />}
        />
      </div>

      {/* Search & Segment Filter Card */}
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-border/80 bg-muted/40 p-3 shadow-xs">
        <div className="relative w-full max-w-sm">
          <Search className="absolute top-1/2 left-2.5 size-3.5 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search customer ID, name, company..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="h-8 bg-background pl-8 text-xs"
          />
        </div>

        <SegmentFilter value={segment} onChange={setSegment} />
      </div>

      {/* Split Grid: Customer Directory Table + Profile Drawer */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1.45fr_1fr]">
        <CustomerTable
          customers={filteredCustomers}
          selectedCustomerId={selectedCustId}
          onSelectCustomer={setSelectedCustId}
          loading={loading}
        />

        <CustomerDrawer
          customer={selectedCustomer}
          onTriggerCartRecovery={handleCartRecovery}
        />
      </div>
    </div>
  )
}
