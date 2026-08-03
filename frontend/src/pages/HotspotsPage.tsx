/**
 * src/pages/HotspotsPage.tsx
 *
 * PRD §6.7 Step 4: Hotspot Analysis
 * Fetches LCA results from FastAPI → AWS RDS. Visualizes per-module GWP breakdown.
 */

import { useParams, useNavigate } from 'react-router-dom'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
  PieChart, Pie, Legend,
} from 'recharts'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faArrowRight, faLeaf, faFire, faWater, faRecycle } from '@fortawesome/free-solid-svg-icons'

import { AppLayout } from '@/components/organisms/AppLayout'
import { ButtonPrimary } from '@/components/atoms/Button'
import { NotificationCard } from '@/components/molecules/NotificationCard'
import { useLcaResults } from '@/hooks/useLcaResults'

const MODULE_COLORS: Record<string, string> = {
  A1: '#16a34a', A2: '#22c55e', A3: '#4ade80',
  A4: '#f59e0b', A5: '#fbbf24',
  B1: '#3b82f6', B6: '#60a5fa',
  C1: '#8b5cf6', C2: '#a78bfa', C3: '#c4b5fd', C4: '#ede9fe',
  D: '#ef4444',
}

function parseModuleValues(jsonb: Record<string, number> | string | null): { module: string; value: number }[] {
  if (!jsonb) return []
  let dictObj: Record<string, number> = {}
  if (typeof jsonb === 'string') {
    try {
      dictObj = JSON.parse(jsonb)
    } catch {
      return []
    }
  } else {
    dictObj = jsonb
  }
  return Object.entries(dictObj)
    .filter(([k]) => k !== 'total')
    .map(([module, value]) => ({ module, value: Number(Number(value).toFixed(4)) }))
    .filter(({ value }) => value !== 0)
    .sort((a, b) => Math.abs(b.value) - Math.abs(a.value))
}

function parseHotspots(hotspotsData: any): any[] {
  if (!hotspotsData) return []
  if (typeof hotspotsData === 'string') {
    try {
      return JSON.parse(hotspotsData)
    } catch {
      return []
    }
  }
  return Array.isArray(hotspotsData) ? hotspotsData : []
}

export default function HotspotsPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const { data: result, isLoading, error } = useLcaResults(id!)

  const breadcrumbs = [
    { label: 'Projects', to: '/dashboard' },
    { label: 'Inventory', to: `/projects/${id}/inventory` },
    { label: 'Calculation', to: `/projects/${id}/calculate` },
    { label: 'Hotspots' },
  ]

  const projectNav = {
    projectId: id || 'new',
    currentStep: 5 as const,
    highestCompletedStep: 5 as const,
  }

  if (isLoading) {
    return (
      <AppLayout breadcrumbs={breadcrumbs} projectNav={projectNav}>
        <div className="flex justify-center items-center min-h-[400px]">
          <p className="text-mute">Loading hotspot analysis from AWS RDS…</p>
        </div>
      </AppLayout>
    )
  }

  if (error || !result) {
    return (
      <AppLayout breadcrumbs={breadcrumbs} projectNav={projectNav}>
        <div className="w-full max-w-content-max mx-auto px-hero-h py-section">
          <NotificationCard variant="error" title="No Results Found">
            No LCA results found. Please complete the calculation step first.
          </NotificationCard>
          <div className="mt-lg">
            <ButtonPrimary onClick={() => navigate(`/projects/${id}/calculate`)}>
              Go to Calculation
            </ButtonPrimary>
          </div>
        </div>
      </AppLayout>
    )
  }

  const gwpModuleData = parseModuleValues(result.gwp_total_kg_co2e)
  const hotspotsList = parseHotspots(result.hotspots)
  const totalGwp = result.carbon_footprint_kg_co2e ?? 0

  // Pie data: top modules by absolute GWP contribution
  const pieData = gwpModuleData.slice(0, 6).map(d => ({
    name: d.module,
    value: Math.abs(d.value),
    color: MODULE_COLORS[d.module] ?? '#94a3b8',
  }))

  const penreTotal = typeof result.penre_mj === 'string'
    ? JSON.parse(result.penre_mj)?.total
    : result.penre_mj?.total

  const fwTotal = typeof result.fw_m3 === 'string'
    ? JSON.parse(result.fw_m3)?.total
    : result.fw_m3?.total

  // Summary cards
  const summaryCards = [
    {
      icon: faLeaf,
      label: 'Total GWP',
      value: `${totalGwp.toFixed(2)}`,
      unit: 'kg CO₂e',
      color: 'text-green-600',
      bg: 'bg-green-50',
    },
    {
      icon: faFire,
      label: 'Non-Renewable Energy',
      value: penreTotal != null ? Number(penreTotal).toFixed(1) : '—',
      unit: 'MJ',
      color: 'text-orange-600',
      bg: 'bg-orange-50',
    },
    {
      icon: faWater,
      label: 'Freshwater Use',
      value: fwTotal != null ? Number(fwTotal).toFixed(3) : '—',
      unit: 'm³',
      color: 'text-blue-600',
      bg: 'bg-blue-50',
    },
    {
      icon: faRecycle,
      label: 'Material Recycled',
      value: result.waste_to_recycling_kg != null ? Number(result.waste_to_recycling_kg).toFixed(1) : '—',
      unit: 'kg',
      color: 'text-purple-600',
      bg: 'bg-purple-50',
    },
  ]

  return (
    <AppLayout breadcrumbs={breadcrumbs} projectNav={projectNav}>
      <div className="w-full max-w-content-max mx-auto px-hero-h py-section">

        {/* Header */}
        <div className="flex items-center justify-between mb-xl">
          <div>
            <h1 className="text-heading-lg text-ink">Hotspot Analysis</h1>
            <p className="text-body-md text-mute">
              Lifecycle impact breakdown — sourced from Ecoinvent 3.12 (AWS RDS)
            </p>
          </div>
          <ButtonPrimary iconRight={faArrowRight} onClick={() => navigate(`/projects/${id}/export`)}>
            Next: Export EPD
          </ButtonPrimary>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-2 tablet:grid-cols-4 gap-lg mb-xxl">
          {summaryCards.map(card => (
            <div key={card.label} className="bg-white border border-hairline rounded-sm p-lg flex flex-col gap-xs">
              <div className={`w-[40px] h-[40px] rounded-full ${card.bg} flex items-center justify-center`}>
                <FontAwesomeIcon icon={card.icon} className={card.color} />
              </div>
              <p className="text-caption-sm text-mute">{card.label}</p>
              <p className="text-heading-md text-ink font-bold leading-tight">
                {card.value}
                <span className="text-body-sm text-mute font-normal ml-xs">{card.unit}</span>
              </p>
            </div>
          ))}
        </div>

        {/* Charts Row */}
        <div className="flex flex-col tablet:flex-row gap-lg mb-xxl">

          {/* Bar Chart: GWP by Module */}
          <div className="flex-[2] bg-white border border-hairline rounded-sm p-xl">
            <h3 className="text-heading-sm text-ink mb-lg">Global Warming Potential by Lifecycle Module</h3>
            {gwpModuleData.length === 0 ? (
              <p className="text-mute text-body-sm text-center py-xxl">No per-module data available</p>
            ) : (
              <div className="h-[280px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={gwpModuleData} margin={{ top: 10, right: 10, left: 0, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
                    <XAxis dataKey="module" tick={{ fill: '#6b7280', fontSize: 12 }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fill: '#6b7280', fontSize: 11 }} axisLine={false} tickLine={false} width={70} />
                    <Tooltip
                      cursor={{ fill: '#f9fafb' }}
                      contentStyle={{ borderRadius: '6px', border: '1px solid #e5e7eb', boxShadow: '0 2px 8px rgba(0,0,0,0.06)' }}
                      formatter={(value: number) => [`${value.toFixed(4)} kg CO₂e`, 'GWP']}
                    />
                    <Bar dataKey="value" radius={[4, 4, 0, 0]} barSize={36}>
                      {gwpModuleData.map((entry) => (
                        <Cell key={entry.module} fill={MODULE_COLORS[entry.module] ?? '#94a3b8'} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>

          {/* Pie/Donut: Module contribution % */}
          <div className="flex-1 bg-white border border-hairline rounded-sm p-xl">
            <h3 className="text-heading-sm text-ink mb-lg">Module Contribution (%)</h3>
            {pieData.length === 0 ? (
              <p className="text-mute text-body-sm text-center py-xxl">No data</p>
            ) : (
              <div className="h-[280px] relative">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={pieData}
                      cx="50%"
                      cy="45%"
                      innerRadius={65}
                      outerRadius={95}
                      paddingAngle={2}
                      dataKey="value"
                    >
                      {pieData.map((entry, i) => (
                        <Cell key={`cell-${i}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{ borderRadius: '6px', border: '1px solid #e5e7eb' }}
                      formatter={(v: number) => [`${v.toFixed(4)} kg CO₂e`, '']}
                    />
                    <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: 12 }} />
                  </PieChart>
                </ResponsiveContainer>
                {/* Center label */}
                <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none" style={{ top: '-24px' }}>
                  <span className="text-heading-md font-bold text-ink leading-none">
                    {totalGwp.toFixed(1)}
                  </span>
                  <span className="text-caption-sm text-mute">kg CO₂e total</span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Itemized Hotspots Table */}
        {hotspotsList.length > 0 && (
          <div className="bg-white border border-hairline rounded-sm p-xl mb-xxl">
            <h3 className="text-heading-sm text-ink mb-lg">Top Impact Contributors (Hotspots)</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-body-sm">
                <thead>
                  <tr className="border-b border-hairline text-mute">
                    <th className="py-sm px-md font-semibold">Rank</th>
                    <th className="py-sm px-md font-semibold">Module</th>
                    <th className="py-sm px-md font-semibold">Item / Driver</th>
                    <th className="py-sm px-md font-semibold">Description</th>
                    <th className="py-sm px-md font-semibold text-right">GWP Impact (kg CO₂e)</th>
                    <th className="py-sm px-md font-semibold text-right">Share (%)</th>
                  </tr>
                </thead>
                <tbody>
                  {hotspotsList.map((item, idx) => (
                    <tr key={idx} className="border-b border-hairline hover:bg-slate-50">
                      <td className="py-sm px-md font-bold text-slate-400">#{idx + 1}</td>
                      <td className="py-sm px-md">
                        <span className="inline-block px-sm py-xs rounded text-caption-sm font-semibold text-white" style={{ backgroundColor: MODULE_COLORS[item.module] || '#64748b' }}>
                          {item.module}
                        </span>
                      </td>
                      <td className="py-sm px-md font-medium text-ink">{item.material_name}</td>
                      <td className="py-sm px-md text-mute">{item.description}</td>
                      <td className="py-sm px-md font-mono text-right text-ink">{item.gwp_kg_co2e?.toFixed(4)}</td>
                      <td className="py-sm px-md font-mono text-right font-bold text-ink">{item.percentage?.toFixed(1)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Compliance Summary */}
        {result.compliance_summary && (
          <div className="bg-white border border-hairline rounded-sm p-xl">
            <h3 className="text-heading-sm text-ink mb-lg">Compliance &amp; Standards</h3>
            <div className="flex flex-wrap gap-md">
              {Object.entries(result.compliance_summary).map(([std, status]) => (
                <div key={std} className="flex items-center gap-sm border border-hairline rounded-sm px-lg py-sm">
                  <span className={`w-[8px] h-[8px] rounded-full ${status === 'PASS' ? 'bg-green-500' : 'bg-gray-300'}`} />
                  <span className="text-body-sm text-ink font-medium">{std}</span>
                  <span className={`text-body-sm font-bold ${status === 'PASS' ? 'text-green-600' : 'text-mute'}`}>{status}</span>
                </div>
              ))}
            </div>
          </div>
        )}

      </div>
    </AppLayout>
  )
}

