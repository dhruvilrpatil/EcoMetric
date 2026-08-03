/**
 * src/pages/TransportationPage.tsx
 *
 * Transportation Module (EN 15804+A2 Modules A2, A4, C2)
 * Pre-fills A2 rows from BOM materials and calculates logistics carbon emissions.
 */

import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faTruck, faArrowRight, faArrowLeft, faSave } from '@fortawesome/free-solid-svg-icons'

import { AppLayout } from '@/components/organisms/AppLayout'
import { Button } from '@/components/atoms/Button'
import { BadgeTag } from '@/components/atoms/BadgeTag'
import { api } from '@/lib/api'

interface TransportSegment {
  material_name?: string
  origin_location: string
  destination_location: string
  transport_mode: 'heavy_truck' | 'rail' | 'ocean_freight' | 'air_freight'
  distance_km: number
  weight_tons: number
  capacity_utilization_pct: number
}

interface ModuleTotals {
  A2: { gwp_total_kgco2e: number }
  A4: { gwp_total_kgco2e: number }
  C2: { gwp_total_kgco2e: number }
}

export default function TransportationPage() {
  const { id: projectId } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const [a2Segments, setA2Segments] = useState<TransportSegment[]>([])
  const [a4Segment, setA4Segment] = useState<TransportSegment>({
    origin_location: 'Factory Plant',
    destination_location: 'Construction Site',
    transport_mode: 'heavy_truck',
    distance_km: 150,
    weight_tons: 1.0,
    capacity_utilization_pct: 75,
  })
  const [c2Segment, setC2Segment] = useState<TransportSegment>({
    origin_location: 'Construction Site',
    destination_location: 'Recycling Facility',
    transport_mode: 'heavy_truck',
    distance_km: 50,
    weight_tons: 1.0,
    capacity_utilization_pct: 65,
  })

  const [moduleTotals, setModuleTotals] = useState<ModuleTotals | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  useEffect(() => {
    if (!projectId) return

    async function loadData() {
      try {
        const stored = await api.get<any>(`/projects/${projectId}/transportation`)
        if (stored && stored.a2_segments && stored.a2_segments.length > 0) {
          setA2Segments(stored.a2_segments)
        } else {
          await fetchMaterialsAndPrefill()
        }
        if (stored && stored.a4_segment) {
          setA4Segment(stored.a4_segment)
        }
        if (stored && stored.c2_segment) {
          setC2Segment(stored.c2_segment)
        }
      } catch {
        await fetchMaterialsAndPrefill()
      } finally {
        setLoading(false)
      }
    }

    async function fetchMaterialsAndPrefill() {
      try {
        const materials = await api.get<any[]>(`/projects/${projectId}/materials`)
        const prefilled: TransportSegment[] = (materials || []).map((mat: any) => ({
          material_name: mat.material_name,
          origin_location: 'Supplier Location',
          destination_location: 'Factory Site',
          transport_mode: 'heavy_truck',
          distance_km: 250,
          weight_tons: mat.quantity_base ? round(mat.quantity_base / 1000, 3) : 0.1,
          capacity_utilization_pct: 70,
        }))
        setA2Segments(prefilled)
      } catch (err) {
        console.error('Failed to load project materials', err)
      }
    }

    loadData()
  }, [projectId])

  const updateA2Segment = (index: number, field: keyof TransportSegment, value: any) => {
    setA2Segments((prev) =>
      prev.map((seg, i) => (i === index ? { ...seg, [field]: value } : seg))
    )
  }

  const queryClient = useQueryClient()

  const handleSave = async () => {
    if (!projectId) return
    setSaving(true)
    setSuccessMessage(null)

    try {
      const response = await api.post<{ status: string; module_totals: ModuleTotals }>(
        `/projects/${projectId}/transportation/save`,
        {
          a2_segments: a2Segments,
          a4_segment: a4Segment,
          c2_segment: c2Segment,
        }
      )
      setModuleTotals(response.module_totals)
      queryClient.invalidateQueries({ queryKey: ['project', projectId] })
      queryClient.invalidateQueries({ queryKey: ['lca_results', projectId] })
      setSuccessMessage('Transportation data calculated and saved successfully!')
      setTimeout(() => setSuccessMessage(null), 4000)
    } catch (err) {
      console.error('Failed to save transportation data', err)
    } finally {
      setSaving(false)
    }
  }

  const handleSaveAndContinue = async () => {
    await handleSave()
    if (projectId) {
      navigate(`/projects/${projectId}/calculate`)
    }
  }

  const breadcrumbs = [
    { label: 'Projects', to: '/dashboard' },
    { label: 'Inventory', to: `/projects/${projectId}/inventory` },
    { label: 'Transportation' },
  ]

  const projectNav = {
    projectId: projectId || 'new',
    currentStep: 3 as const,
    highestCompletedStep: 3 as const,
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-canvas flex items-center justify-center">
        <p className="text-body-md text-mute animate-pulse">Loading Transportation Module...</p>
      </div>
    )
  }

  return (
    <AppLayout breadcrumbs={breadcrumbs} projectNav={projectNav}>
      <div className="w-full max-w-content-max mx-auto px-hero-h py-section space-y-xl">
        
        {/* Page Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-heading-lg text-ink font-bold flex items-center gap-sm">
              <FontAwesomeIcon icon={faTruck} className="text-primary" />
              Transportation &amp; Freight Logistics (Modules A2, A4, C2)
            </h1>
            <p className="text-body-md text-mute mt-xs">
              Configure transport modes, distances, and payloads for EN 15804+A2 supply chain compliance.
            </p>
          </div>
          <BadgeTag color="success">EN 15804+A2 Mandatory</BadgeTag>
        </div>

        {successMessage && (
          <div className="bg-surface-soft border-l-4 border-success p-md rounded-sm text-body-sm text-ink font-medium">
            {successMessage}
          </div>
        )}

        {a2Segments.length === 0 && (
          <div className="bg-amber-50 border border-amber-300 rounded-sm p-md text-amber-900 text-body-sm font-semibold flex items-center gap-sm">
            <span className="text-lg">⚠️</span>
            <span>Zero material transportation segments (Module A2) defined. EN 15804+A2 requires documented transport logistics for raw materials or distribution (Module A4).</span>
          </div>
        )}

        {/* Section 1: Module A2 Raw Material Logistics */}
        <section className="bg-white border border-hairline rounded-sm p-xl shadow-card">
          <div className="flex items-center justify-between mb-md">
            <div>
              <h2 className="text-heading-md font-bold text-ink">Module A2: Material Transport to Factory</h2>
              <p className="text-body-sm text-mute">
                Pre-filled from your BOM. Define how raw materials travel from supplier facilities to your manufacturing plant.
              </p>
            </div>
            <span className="text-caption-sm font-semibold text-stone bg-surface-soft px-sm py-xs rounded-sm">
              {a2Segments.length} BOM Materials
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-body-sm border-collapse">
              <thead>
                <tr className="bg-surface-soft border-b border-hairline text-caption-xs uppercase font-bold text-mute">
                  <th className="p-md">Material</th>
                  <th className="p-md">Origin</th>
                  <th className="p-md">Transport Mode</th>
                  <th className="p-md text-center">Distance (km)</th>
                  <th className="p-md text-center">Weight (t)</th>
                  <th className="p-md text-center">Capacity (%)</th>
                </tr>
              </thead>
              <tbody>
                {a2Segments.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="p-xl text-center text-mute">
                      No materials found in BOM. Add materials in Step 2 Inventory first.
                    </td>
                  </tr>
                ) : (
                  a2Segments.map((seg, idx) => (
                    <tr key={idx} className="border-b border-hairline hover:bg-surface-soft">
                      <td className="p-md font-semibold text-ink">{seg.material_name || `Item ${idx+1}`}</td>
                      <td className="p-md">
                        <input
                          type="text"
                          value={seg.origin_location}
                          onChange={(e) => updateA2Segment(idx, 'origin_location', e.target.value)}
                          placeholder="e.g. Duisburg, DE"
                          className="w-full border border-hairline rounded-sm p-xs text-body-sm"
                        />
                      </td>
                      <td className="p-md">
                        <select
                          value={seg.transport_mode}
                          onChange={(e) => updateA2Segment(idx, 'transport_mode', e.target.value as any)}
                          className="w-full border border-hairline rounded-sm p-xs text-body-sm bg-white"
                        >
                          <option value="heavy_truck">🚛 Heavy Truck (Lorry &gt;32t)</option>
                          <option value="rail">🚆 Freight Rail</option>
                          <option value="ocean_freight">🚢 Ocean Container Vessel</option>
                          <option value="air_freight">✈️ Air Freight (Intercontinental)</option>
                        </select>
                      </td>
                      <td className="p-md text-center">
                        <input
                          type="number"
                          value={seg.distance_km}
                          onChange={(e) => updateA2Segment(idx, 'distance_km', parseFloat(e.target.value) || 0)}
                          className="w-24 border border-hairline rounded-sm p-xs text-center font-mono"
                        />
                      </td>
                      <td className="p-md text-center">
                        <input
                          type="number"
                          step="0.01"
                          value={seg.weight_tons}
                          onChange={(e) => updateA2Segment(idx, 'weight_tons', parseFloat(e.target.value) || 0)}
                          className="w-20 border border-hairline rounded-sm p-xs text-center font-mono"
                        />
                      </td>
                      <td className="p-md text-center">
                        <input
                          type="number"
                          min="0"
                          max="100"
                          value={seg.capacity_utilization_pct}
                          onChange={(e) => updateA2Segment(idx, 'capacity_utilization_pct', parseFloat(e.target.value) || 0)}
                          className="w-16 border border-hairline rounded-sm p-xs text-center font-mono"
                        />
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </section>

        {/* Section 2: Module A4 Product Distribution */}
        <section className="bg-white border border-hairline rounded-sm p-xl shadow-card">
          <h2 className="text-heading-md font-bold text-ink mb-xs">Module A4: Finished Product Distribution</h2>
          <p className="text-body-sm text-mute mb-lg">
            Specify freight parameters for delivering finished products from factory gate to installation site.
          </p>

          <div className="grid grid-cols-1 tablet:grid-cols-3 gap-lg">
            <div>
              <label className="block text-caption-xs font-bold uppercase text-mute mb-xs">Origin (Factory)</label>
              <input
                type="text"
                value={a4Segment.origin_location}
                onChange={(e) => setA4Segment({ ...a4Segment, origin_location: e.target.value })}
                className="w-full border border-hairline rounded-sm p-sm text-body-sm"
              />
            </div>
            <div>
              <label className="block text-caption-xs font-bold uppercase text-mute mb-xs">Destination (Installation Site)</label>
              <input
                type="text"
                value={a4Segment.destination_location}
                onChange={(e) => setA4Segment({ ...a4Segment, destination_location: e.target.value })}
                className="w-full border border-hairline rounded-sm p-sm text-body-sm"
              />
            </div>
            <div>
              <label className="block text-caption-xs font-bold uppercase text-mute mb-xs">Transport Mode</label>
              <select
                value={a4Segment.transport_mode}
                onChange={(e) => setA4Segment({ ...a4Segment, transport_mode: e.target.value as any })}
                className="w-full border border-hairline rounded-sm p-sm text-body-sm bg-white"
              >
                <option value="heavy_truck">🚛 Heavy Truck (Lorry &gt;32t EURO6)</option>
                <option value="rail">🚆 Freight Rail</option>
                <option value="ocean_freight">🚢 Ocean Cargo Vessel</option>
                <option value="air_freight">✈️ Air Freight (Long Haul)</option>
              </select>
            </div>
            <div>
              <label className="block text-caption-xs font-bold uppercase text-mute mb-xs">Distance (km)</label>
              <input
                type="number"
                value={a4Segment.distance_km}
                onChange={(e) => setA4Segment({ ...a4Segment, distance_km: parseFloat(e.target.value) || 0 })}
                className="w-full border border-hairline rounded-sm p-sm text-body-sm font-mono"
              />
            </div>
            <div>
              <label className="block text-caption-xs font-bold uppercase text-mute mb-xs">Total Weight (tons)</label>
              <input
                type="number"
                step="0.01"
                value={a4Segment.weight_tons}
                onChange={(e) => setA4Segment({ ...a4Segment, weight_tons: parseFloat(e.target.value) || 0 })}
                className="w-full border border-hairline rounded-sm p-sm text-body-sm font-mono"
              />
            </div>
            <div>
              <label className="block text-caption-xs font-bold uppercase text-mute mb-xs">
                Capacity Utilization: {a4Segment.capacity_utilization_pct}%
              </label>
              <input
                type="range"
                min="0"
                max="100"
                value={a4Segment.capacity_utilization_pct}
                onChange={(e) => setA4Segment({ ...a4Segment, capacity_utilization_pct: parseFloat(e.target.value) || 0 })}
                className="w-full accent-primary mt-sm"
              />
            </div>
          </div>
        </section>

        {/* Section 3: Live Preview of Calculated Transport Impacts */}
        {moduleTotals && (
          <section className="bg-surface-soft border border-hairline rounded-sm p-xl shadow-card">
            <h3 className="text-heading-sm font-bold text-ink mb-md">Calculated Transport Carbon Footprint (GWP-total)</h3>
            <div className="grid grid-cols-1 tablet:grid-cols-3 gap-lg">
              <div className="bg-white p-lg rounded-sm border border-hairline">
                <span className="text-caption-xs uppercase font-bold text-mute">Module A2 (Raw Materials)</span>
                <p className="text-heading-lg font-mono font-bold text-primary mt-xs">
                  {moduleTotals.A2.gwp_total_kgco2e.toFixed(2)} <span className="text-body-sm text-mute">kg CO₂e</span>
                </p>
              </div>
              <div className="bg-white p-lg rounded-sm border border-hairline">
                <span className="text-caption-xs uppercase font-bold text-mute">Module A4 (Distribution)</span>
                <p className="text-heading-lg font-mono font-bold text-primary mt-xs">
                  {moduleTotals.A4.gwp_total_kgco2e.toFixed(2)} <span className="text-body-sm text-mute">kg CO₂e</span>
                </p>
              </div>
              <div className="bg-white p-lg rounded-sm border border-hairline">
                <span className="text-caption-xs uppercase font-bold text-mute">Module C2 (End-of-Life Transport)</span>
                <p className="text-heading-lg font-mono font-bold text-primary mt-xs">
                  {moduleTotals.C2.gwp_total_kgco2e.toFixed(2)} <span className="text-body-sm text-mute">kg CO₂e</span>
                </p>
              </div>
            </div>
          </section>
        )}

        {/* Action Controls */}
        <div className="flex items-center justify-between pt-md">
          <Button
            variant="outline"
            onClick={() => navigate(`/projects/${projectId}/inventory`)}
          >
            <FontAwesomeIcon icon={faArrowLeft} className="mr-xs" /> Back to Inventory
          </Button>

          <div className="flex items-center gap-md">
            <Button
              variant="outline"
              onClick={handleSave}
              disabled={saving}
            >
              <FontAwesomeIcon icon={faSave} className="mr-xs" />
              {saving ? 'Calculating...' : 'Save Inputs'}
            </Button>

            <Button
              variant="primary"
              onClick={handleSaveAndContinue}
              disabled={saving}
            >
              Save &amp; Continue to Calculate <FontAwesomeIcon icon={faArrowRight} className="ml-xs" />
            </Button>
          </div>
        </div>

      </div>
    </AppLayout>
  )
}

function round(val: number, decimals: number) {
  return Number(Math.round(Number(val + 'e' + decimals)) + 'e-' + decimals)
}
