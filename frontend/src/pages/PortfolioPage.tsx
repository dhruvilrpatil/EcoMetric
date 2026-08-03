/**
 * src/pages/PortfolioPage.tsx
 *
 * PRD §6.11 Portfolio Dashboard
 *   - Stats header (4-up)
 *   - Regulatory deadline calendar
 *   - Sortable/filterable product catalog table
 */

import { useState } from 'react'
import { Link } from 'react-router-dom'
import { AppLayout } from '@/components/organisms/AppLayout'
import { CalloutStat } from '@/components/molecules/CalloutStat'
import { BadgeTag } from '@/components/atoms/BadgeTag'

// Mock Data for MVP
const MOCK_STATS = [
  { label: 'Total EPDs Published', value: '24', caption: 'Across 5 regions' },
  { label: 'Expiring < 12 mos', value: '3', caption: 'Requires renewal', color: 'warning' as const },
  { label: 'Avg Portfolio GWP', value: '412', caption: 'kg CO2e / unit' },
  { label: 'DPP Registrations', value: '18', caption: 'ESPR Compliant' },
]

const DEADLINES = [
  { name: 'ESPR Battery Directive', date: '2027-01-01', days: 156 },
  { name: 'CPR Updates (Construction)', date: '2029-06-01', days: 1068 },
]

const MOCK_PRODUCTS = [
  { id: '1', name: 'AquaEdge 19DV Chiller', standard: 'EN 15804+A2', gwp: 14500.5, status: 'PUBLISHED', expiry: '2029-10-15' },
  { id: '2', name: 'EcoGlass Double Pane', standard: 'ISO 21930', gwp: 142.3, status: 'IN PROGRESS', expiry: 'N/A' },
  { id: '3', name: 'Steel Beam H-Profile', standard: 'EN 15804+A2', gwp: 3100.0, status: 'PUBLISHED', expiry: '2027-02-10' },
  { id: '4', name: 'Concrete Mix C30/37', standard: 'EN 15804+A2', gwp: 285.5, status: 'EXPIRED', expiry: '2025-11-01' },
]

export default function PortfolioPage() {
  const [filter, setFilter] = useState<'ALL' | 'PUBLISHED' | 'IN PROGRESS' | 'EXPIRED'>('ALL')

  const breadcrumbs = [
    { label: 'Portfolio' }
  ]

  const filteredProducts = MOCK_PRODUCTS.filter(p => filter === 'ALL' || p.status === filter)

  return (
    <AppLayout breadcrumbs={breadcrumbs}>
      <div className="w-full max-w-content-max mx-auto px-hero-h py-section">
        
        <div className="mb-xl">
          <h1 className="text-heading-lg text-ink">Portfolio Overview</h1>
          <p className="text-body-md text-mute">Manage enterprise-wide compliance and EPD lifecycle events.</p>
        </div>

        {/* 4-up Stats */}
        <div className="grid grid-cols-1 mobile:grid-cols-2 desktop-small:grid-cols-4 gap-lg mb-xxl">
          {MOCK_STATS.map((stat, idx) => (
            <CalloutStat
              key={idx}
              value={stat.value}
              caption={stat.caption}
              eyebrow={stat.label}
              valueColor={stat.color}
            />
          ))}
        </div>

        <div className="flex flex-col desktop-small:flex-row gap-xxl mb-xxl">
          
          {/* Main Table */}
          <div className="flex-[2] bg-white border border-hairline rounded-sm flex flex-col">
            <div className="p-md border-b border-hairline bg-surface-soft flex justify-between items-center">
              <h2 className="text-heading-sm text-ink">Product Catalog</h2>
              <div className="flex gap-xs">
                {['ALL', 'PUBLISHED', 'IN PROGRESS', 'EXPIRED'].map(f => (
                  <button 
                    key={f}
                    onClick={() => setFilter(f as any)}
                    className={`px-sm py-xxs rounded-sm text-caption-xs font-bold transition-colors ${
                      filter === f ? 'bg-ink text-white' : 'bg-transparent text-mute hover:text-ink'
                    }`}
                  >
                    {f}
                  </button>
                ))}
              </div>
            </div>
            
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-hairline bg-white">
                    <th className="p-md text-caption-sm text-mute uppercase font-bold">Product</th>
                    <th className="p-md text-caption-sm text-mute uppercase font-bold">Standard</th>
                    <th className="p-md text-caption-sm text-mute uppercase font-bold">GWP-total</th>
                    <th className="p-md text-caption-sm text-mute uppercase font-bold">Status</th>
                    <th className="p-md text-caption-sm text-mute uppercase font-bold">Expiry</th>
                    <th className="p-md text-caption-sm text-mute uppercase font-bold text-right">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredProducts.map((p) => (
                    <tr key={p.id} className="border-b border-hairline hover:bg-surface-soft transition-colors">
                      <td className="p-md text-body-strong text-ink">{p.name}</td>
                      <td className="p-md text-body-sm text-mute">{p.standard}</td>
                      <td className="p-md text-body-sm text-ink font-mono">{p.gwp.toLocaleString()}</td>
                      <td className="p-md">
                        <BadgeTag color={p.status === 'PUBLISHED' ? 'success' : p.status === 'EXPIRED' ? 'error' : 'info'}>
                          {p.status}
                        </BadgeTag>
                      </td>
                      <td className="p-md text-body-sm text-mute">{p.expiry}</td>
                      <td className="p-md text-right">
                        <Link to={`/projects/${p.id}/export`} className="text-link-blue hover:underline text-body-sm">
                          Manage
                        </Link>
                      </td>
                    </tr>
                  ))}
                  {filteredProducts.length === 0 && (
                    <tr>
                      <td colSpan={6} className="p-xl text-center text-mute text-body-sm">
                        No products match the selected filter.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Right Rail: Deadlines */}
          <div className="flex-[1] flex flex-col gap-lg">
            <div className="bg-white border border-hairline rounded-sm p-xl">
              <h2 className="text-heading-sm text-ink mb-md">Regulatory Deadlines</h2>
              <div className="flex flex-col gap-md">
                {DEADLINES.map((d, i) => (
                  <div key={i} className="border border-hairline p-md rounded-sm flex flex-col gap-xs">
                    <div className="flex justify-between items-start">
                      <BadgeTag color="warning">REGULATION</BadgeTag>
                      <span className="text-caption-sm font-bold text-warning">{d.days} Days</span>
                    </div>
                    <h3 className="text-body-strong text-ink">{d.name}</h3>
                    <p className="text-caption-sm text-mute">Effective: {d.date}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>

        </div>
      </div>
    </AppLayout>
  )
}
