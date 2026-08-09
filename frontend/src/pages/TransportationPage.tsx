/**
 * src/pages/TransportationPage.tsx
 *
 * Transport to Building Site (Module A4)
 * PCR, ISO 21930 & EN 15804+A2 compliant structured scenario form and live EPD preview.
 */

import { useState, useEffect, useMemo } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faTruck,
  faArrowLeft,
  faSave,
  faRobot,
  faInfoCircle,
  faExclamationTriangle,
  faCheckCircle,
  faSync,
} from '@fortawesome/free-solid-svg-icons'

import { AppLayout } from '@/components/organisms/AppLayout'
import { Button } from '@/components/atoms/Button'
import { TextInput } from '@/components/atoms/TextInput'
import { api } from '@/lib/api'
import { useProject } from '@/hooks/useProjects'

interface TransportScenarioState {
  vehicle_type: string
  payload_capacity: number
  fuel_type: string
  fuel_efficiency: number
  road_distance: number
  ocean_distance: number
  rail_distance: number
  air_distance: number
  product_weight: number
  gross_density: number
  capacity_utilization: number
  capacity_volume_factor: string
}

const VEHICLE_OPTIONS = [
  { label: '>32000 kg payload Flatbed Truck', value: '>32000 kg payload Flatbed Truck', payload: 32000, fuel: 36.3, fuelType: 'Diesel' },
  { label: 'Flatbed Truck (>32 ton)', value: 'Flatbed Truck (>32 ton)', payload: 32000, fuel: 36.3, fuelType: 'Diesel' },
  { label: 'Heavy Truck', value: 'Heavy Truck', payload: 24000, fuel: 32.0, fuelType: 'Diesel' },
  { label: 'Medium Truck', value: 'Medium Truck', payload: 12000, fuel: 22.0, fuelType: 'Diesel' },
  { label: 'Container Truck', value: 'Container Truck', payload: 28000, fuel: 34.5, fuelType: 'Diesel' },
  { label: 'Rail', value: 'Rail', payload: 500000, fuel: 5.0, fuelType: 'Electric' },
  { label: 'Ocean Vessel', value: 'Ocean Vessel', payload: 10000000, fuel: 2.5, fuelType: 'LNG' },
]

export default function TransportationPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { data: project } = useProject(id)

  const [scenario, setScenario] = useState<TransportScenarioState>({
    vehicle_type: '>32000 kg payload Flatbed Truck',
    payload_capacity: 32000,
    fuel_type: 'Diesel',
    fuel_efficiency: 36.3,
    road_distance: 500,
    ocean_distance: 0,
    rail_distance: 0,
    air_distance: 0,
    product_weight: 15455.7,
    gross_density: 369,
    capacity_utilization: 24,
    capacity_volume_factor: '<1',
  })

  const [isSaving, setIsSaving] = useState(false)
  const [isAiLoading, setIsAiLoading] = useState(false)
  const [aiRationale, setAiRationale] = useState<string | null>(null)
  const [validationErrors, setValidationErrors] = useState<string[]>([])
  const [saveSuccess, setSaveSuccess] = useState(false)

  // Fetch BOM rows for live weight calculation if needed
  const { data: bom = [] } = useQuery({
    queryKey: ['project_bom', id],
    queryFn: () => api.get<any[]>(`/projects/${id}/bom`),
    enabled: !!id,
  })

  const calculatedBomWeight = useMemo(() => {
    return bom.reduce((sum, item) => sum + (Number(item.mass_kg || item.quantity) || 0), 0)
  }, [bom])

  // Load existing transport scenario
  useEffect(() => {
    if (!id) return
    api.get<any>(`/projects/${id}/transportation`)
      .then((data) => {
        if (data && Object.keys(data).length > 0) {
          setScenario((prev) => ({
            ...prev,
            vehicle_type: data.vehicle_type || prev.vehicle_type,
            payload_capacity: Number(data.payload_capacity ?? prev.payload_capacity),
            fuel_type: data.fuel_type || prev.fuel_type,
            fuel_efficiency: Number(data.fuel_efficiency ?? prev.fuel_efficiency),
            road_distance: Number(data.road_distance ?? prev.road_distance),
            ocean_distance: Number(data.ocean_distance ?? prev.ocean_distance),
            rail_distance: Number(data.rail_distance ?? prev.rail_distance),
            air_distance: Number(data.air_distance ?? prev.air_distance),
            product_weight: Number(data.product_weight || calculatedBomWeight || prev.product_weight),
            gross_density: Number(data.gross_density ?? prev.gross_density),
            capacity_utilization: Number(data.capacity_utilization ?? prev.capacity_utilization),
            capacity_volume_factor: data.capacity_volume_factor || prev.capacity_volume_factor,
          }))
        }
      })
      .catch((err) => console.error('Failed to load transport scenario:', err))
  }, [id, calculatedBomWeight])

  // Auto update vehicle defaults when Vehicle Type changes
  const handleVehicleChange = (vType: string) => {
    const matched = VEHICLE_OPTIONS.find((opt) => opt.value === vType)
    if (matched) {
      setScenario((prev) => ({
        ...prev,
        vehicle_type: matched.value,
        payload_capacity: matched.payload,
        fuel_efficiency: matched.fuel,
        fuel_type: matched.fuelType,
      }))
    } else {
      setScenario((prev) => ({ ...prev, vehicle_type: vType }))
    }
  }

  // Validate form inputs against PCR rules
  const validateForm = (): string[] => {
    const errors: string[] = []
    if (scenario.road_distance < 0) errors.push('Road distance must be ≥ 0 km.')
    if (scenario.ocean_distance < 0) errors.push('Ocean distance must be ≥ 0 km.')
    if (scenario.rail_distance < 0) errors.push('Rail distance must be ≥ 0 km.')
    if (scenario.air_distance < 0) errors.push('Air distance must be ≥ 0 km.')
    if (scenario.fuel_efficiency <= 0) errors.push('Fuel efficiency must be > 0 L/100 km.')
    if (scenario.capacity_utilization < 1 || scenario.capacity_utilization > 100) {
      errors.push('Capacity utilization must be between 1% and 100%.')
    }
    if (scenario.product_weight <= 0) errors.push('Product weight must be > 0 kg.')
    return errors
  }

  // Save handler
  const handleSave = async () => {
    const errors = validateForm()
    setValidationErrors(errors)
    if (errors.length > 0) return

    setIsSaving(true)
    setSaveSuccess(false)

    try {
      await api.post(`/projects/${id}/transportation/save`, scenario)
      setSaveSuccess(true)
      queryClient.invalidateQueries({ queryKey: ['project', id] })
      setTimeout(() => setSaveSuccess(false), 3000)
    } catch (err: any) {
      setValidationErrors([err.message || 'Failed to save transport scenario'])
    } finally {
      setIsSaving(false)
    }
  }

  // AI Suggestion Handler
  const handleAiSuggest = async () => {
    setIsAiLoading(true)
    setAiRationale(null)
    try {
      const res = await api.post<any>(`/projects/${id}/transportation/ai-suggest`, {
        product_weight: scenario.product_weight || calculatedBomWeight,
      })
      if (res) {
        setScenario((prev) => ({
          ...prev,
          vehicle_type: res.suggested_vehicle_type || prev.vehicle_type,
          payload_capacity: res.payload_capacity || prev.payload_capacity,
          fuel_type: res.suggested_fuel_type || prev.fuel_type,
          fuel_efficiency: res.suggested_fuel_efficiency || prev.fuel_efficiency,
          gross_density: res.suggested_gross_density || prev.gross_density,
          capacity_utilization: res.suggested_capacity_utilization || 24,
          road_distance: res.suggested_road_distance ?? prev.road_distance,
          ocean_distance: res.suggested_ocean_distance ?? prev.ocean_distance,
          capacity_volume_factor: res.suggested_capacity_volume_factor || prev.capacity_volume_factor,
        }))
        setAiRationale(res.rationale || 'AI recommendation applied based on product mass and PCR benchmarks.')
      }
    } catch (err) {
      console.error('AI suggest error:', err)
    } finally {
      setIsAiLoading(false)
    }
  }

  return (
    <AppLayout
      breadcrumbs={[
        { label: 'Projects', to: '/projects' },
        { label: project?.name || 'Project Details', to: `/projects/${id}` },
        { label: 'Step 3: Transportation' },
      ]}
      projectNav={id ? {
        projectId: id,
        currentStep: 3,
        highestCompletedStep: 3,
      } : undefined}
    >
      <div className="max-w-6xl mx-auto space-y-xl py-md">

        {/* Header Strip */}
        <div className="flex flex-col tablet:flex-row justify-between items-start tablet:items-center gap-md bg-white p-lg rounded-sm border border-hairline shadow-sm">
          <div>
            <span className="text-caption-sm font-bold uppercase tracking-wider text-primary">Module A4</span>
            <h1 className="text-heading-md font-bold text-ink">Transport to Building Site Scenario</h1>
            <p className="text-body-sm text-mute mt-xs">
              Configure standard-compliant Module A4 logistics for EPD publication (EN 15804+A2 &amp; PCR compliant).
            </p>
          </div>
          <div className="flex gap-sm">
            <Button variant="outline" onClick={handleAiSuggest} disabled={isAiLoading}>
              <FontAwesomeIcon icon={isAiLoading ? faSync : faRobot} className={`mr-xs ${isAiLoading ? 'animate-spin' : 'text-primary'}`} />
              {isAiLoading ? 'Analyzing...' : 'AI Transport Suggestion'}
            </Button>
            <Button variant="primary" onClick={handleSave} disabled={isSaving}>
              <FontAwesomeIcon icon={faSave} className="mr-xs" />
              {isSaving ? 'Saving...' : 'Save Scenario'}
            </Button>
          </div>
        </div>

        {/* Alerts & Notifications */}
        {validationErrors.length > 0 && (
          <div className="bg-red-50 border border-red-200 text-red-800 p-md rounded-sm space-y-xs">
            <div className="font-bold flex items-center gap-xs">
              <FontAwesomeIcon icon={faExclamationTriangle} /> Validation Errors
            </div>
            <ul className="list-disc pl-md text-body-sm space-y-xs">
              {validationErrors.map((err, idx) => (
                <li key={idx}>{err}</li>
              ))}
            </ul>
          </div>
        )}

        {saveSuccess && (
          <div className="bg-emerald-50 border border-emerald-200 text-emerald-800 p-md rounded-sm flex items-center gap-xs font-semibold text-body-sm">
            <FontAwesomeIcon icon={faCheckCircle} className="text-emerald-600" /> Transport scenario saved successfully!
          </div>
        )}

        {aiRationale && (
          <div className="bg-blue-50 border border-blue-200 text-blue-900 p-md rounded-sm flex items-start gap-sm text-body-sm">
            <FontAwesomeIcon icon={faRobot} className="text-primary mt-xs text-lg" />
            <div>
              <span className="font-bold block">AI Recommendation Applied</span>
              <p>{aiRationale}</p>
            </div>
          </div>
        )}

        {/* Main Grid: Form & Live EPD Preview */}
        <div className="grid grid-cols-1 desktop:grid-cols-12 gap-xl">

          {/* LEFT: Structured Form (7 Cols) */}
          <div className="desktop:col-span-7 bg-white border border-hairline rounded-sm p-xl shadow-card space-y-xl">

            {/* SECTION 1: Transport Vehicle */}
            <div className="space-y-md">
              <h2 className="text-body-strong font-bold text-ink flex items-center gap-xs border-b border-hairline pb-xs">
                <FontAwesomeIcon icon={faTruck} className="text-primary" /> Section 1: Transport Vehicle
              </h2>

              <div className="grid grid-cols-1 tablet:grid-cols-2 gap-md">
                <div>
                  <label className="text-body-strong text-ink block mb-xs text-body-sm font-semibold">
                    Vehicle Type
                  </label>
                  <select
                    value={scenario.vehicle_type}
                    onChange={(e) => handleVehicleChange(e.target.value)}
                    className="w-full border border-hairline rounded-sm p-sm text-body-sm bg-white font-medium"
                  >
                    {VEHICLE_OPTIONS.map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <TextInput
                    label="Payload Capacity (kg)"
                    type="number"
                    value={scenario.payload_capacity}
                    readOnly
                    hint="Auto-filled from vehicle type database"
                  />
                </div>

                <div>
                  <label className="text-body-strong text-ink block mb-xs text-body-sm font-semibold">
                    Fuel Type
                  </label>
                  <select
                    value={scenario.fuel_type}
                    onChange={(e) => setScenario({ ...scenario, fuel_type: e.target.value })}
                    className="w-full border border-hairline rounded-sm p-sm text-body-sm bg-white font-medium"
                  >
                    <option value="Diesel">Diesel</option>
                    <option value="Petrol">Petrol</option>
                    <option value="LNG">LNG</option>
                    <option value="Electric">Electric</option>
                  </select>
                </div>

                <div>
                  <TextInput
                    label="Fuel Efficiency (L/100 km)"
                    type="number"
                    step="0.1"
                    value={scenario.fuel_efficiency}
                    onChange={(e) => setScenario({ ...scenario, fuel_efficiency: parseFloat(e.target.value) || 0 })}
                  />
                </div>
              </div>
            </div>

            {/* SECTION 2: Transport Distances */}
            <div className="space-y-md border-t border-hairline pt-md">
              <h2 className="text-body-strong font-bold text-ink border-b border-hairline pb-xs">
                Section 2: Transport Distances
              </h2>
              <p className="text-caption-sm text-mute">
                Enter distances for active logistics legs. Zero-distance modes are omitted from published EPD tables.
              </p>

              <div className="grid grid-cols-1 tablet:grid-cols-2 gap-md">
                <TextInput
                  label="Road Distance (km)"
                  type="number"
                  value={scenario.road_distance}
                  onChange={(e) => setScenario({ ...scenario, road_distance: parseFloat(e.target.value) || 0 })}
                />

                <TextInput
                  label="Ocean Freight Distance (km)"
                  type="number"
                  value={scenario.ocean_distance}
                  onChange={(e) => setScenario({ ...scenario, ocean_distance: parseFloat(e.target.value) || 0 })}
                />

                <TextInput
                  label="Rail Freight Distance (km)"
                  type="number"
                  value={scenario.rail_distance}
                  onChange={(e) => setScenario({ ...scenario, rail_distance: parseFloat(e.target.value) || 0 })}
                />

                <TextInput
                  label="Air Freight Distance (km)"
                  type="number"
                  value={scenario.air_distance}
                  onChange={(e) => setScenario({ ...scenario, air_distance: parseFloat(e.target.value) || 0 })}
                />
              </div>
            </div>

            {/* SECTION 3: Product Information */}
            <div className="space-y-md border-t border-hairline pt-md">
              <h2 className="text-body-strong font-bold text-ink border-b border-hairline pb-xs">
                Section 3: Product Information (Auto-Loaded)
              </h2>
              <div className="bg-surface-soft p-md rounded-sm grid grid-cols-1 tablet:grid-cols-2 gap-md">
                <div>
                  <span className="text-caption-sm text-mute block font-medium">Product Weight</span>
                  <span className="text-heading-sm font-bold text-ink font-mono">{scenario.product_weight.toFixed(1)} kg</span>
                  <p className="text-caption-sm text-mute mt-xs">Auto-synced from Product Setup / BOM</p>
                </div>

                <div>
                  <span className="text-caption-sm text-mute block font-medium">Functional Unit</span>
                  <span className="text-body-strong font-semibold text-ink">
                    {project?.functional_unit_quantity || 1} {project?.functional_unit_unit || 'unit'}
                  </span>
                </div>
              </div>
            </div>

            {/* SECTION 4: Capacity Utilization */}
            <div className="space-y-md border-t border-hairline pt-md">
              <h2 className="text-body-strong font-bold text-ink border-b border-hairline pb-xs">
                Section 4: Capacity Utilization
              </h2>
              <div className="max-w-md">
                <TextInput
                  label="Capacity Utilization (%)"
                  type="number"
                  min={1}
                  max={100}
                  value={scenario.capacity_utilization}
                  onChange={(e) => setScenario({ ...scenario, capacity_utilization: Math.min(100, Math.max(1, parseFloat(e.target.value) || 1)) })}
                  hint="Percentage of vehicle payload occupied by the transported product (Default: 24%)."
                />
              </div>
            </div>

            {/* SECTION 5: Gross Density */}
            <div className="space-y-md border-t border-hairline pt-md">
              <h2 className="text-body-strong font-bold text-ink border-b border-hairline pb-xs">
                Section 5: Gross Density
              </h2>
              <div className="max-w-md">
                <TextInput
                  label="Gross Density of Products Transported (kg/m³)"
                  type="number"
                  value={scenario.gross_density}
                  onChange={(e) => setScenario({ ...scenario, gross_density: parseFloat(e.target.value) || 0 })}
                  hint="Auto-calculated or manually overridden per product package specifications."
                />
              </div>
            </div>

            {/* SECTION 6: Capacity Utilization Volume Factor */}
            <div className="space-y-md border-t border-hairline pt-md">
              <h2 className="text-body-strong font-bold text-ink border-b border-hairline pb-xs">
                Section 6: Capacity Utilization Volume Factor
              </h2>
              <div className="max-w-md">
                <label className="text-body-strong text-ink block mb-xs text-body-sm font-semibold">
                  Capacity Volume Factor
                </label>
                <select
                  value={scenario.capacity_volume_factor}
                  onChange={(e) => setScenario({ ...scenario, capacity_volume_factor: e.target.value })}
                  className="w-full border border-hairline rounded-sm p-sm text-body-sm bg-white font-medium"
                >
                  <option value="<1">&lt;1 (Volume constrained before mass limit)</option>
                  <option value="1">1 (Mass and volume limits reached simultaneously)</option>
                  <option value=">1">&gt;1 (Mass constrained before volume limit)</option>
                </select>
              </div>
            </div>

            {/* Form Action Footer */}
            <div className="flex justify-between items-center pt-md border-t border-hairline">
              <Button variant="outline" onClick={() => navigate(`/projects/${id}/inventory`)}>
                <FontAwesomeIcon icon={faArrowLeft} className="mr-xs" /> Back to Inventory
              </Button>
              <Button variant="primary" onClick={handleSave} disabled={isSaving}>
                <FontAwesomeIcon icon={faSave} className="mr-xs" /> Save &amp; Continue
              </Button>
            </div>

          </div>

          {/* RIGHT: Certified EPD Report Preview (5 Cols) */}
          <div className="desktop:col-span-5 space-y-md">
            <div className="bg-white border border-hairline rounded-sm p-lg shadow-card sticky top-6 space-y-md">

              <div className="flex items-center justify-between border-b border-hairline pb-sm">
                <h3 className="text-body-strong font-bold text-ink flex items-center gap-xs">
                  <FontAwesomeIcon icon={faInfoCircle} className="text-primary" /> EPD Table Preview
                </h3>
                <span className="text-caption-sm bg-blue-50 text-blue-800 font-semibold px-xs py-0.5 rounded">
                  PCR Compliant
                </span>
              </div>

              <p className="text-caption-sm text-mute">
                Live rendering of Section 4.1 in published EPD reports (Carrier / Daikin / UL Solutions format):
              </p>

              {/* Styled EPD Table matching PDF output */}
              <div className="border border-hairline rounded-sm overflow-hidden text-body-sm shadow-xs">
                <div className="bg-[#1B2A4A] text-white p-xs font-bold text-caption-sm text-center">
                  Table: Transport to Building Site (A4) per Functional Unit
                </div>
                <table className="w-full text-left text-body-sm border-collapse">
                  <thead>
                    <tr className="bg-[#1B2A4A] text-white border-b border-hairline text-caption-sm">
                      <th className="p-sm font-bold border-r border-hairline/20">Parameter</th>
                      <th className="p-sm font-bold border-r border-hairline/20">Value</th>
                      <th className="p-sm font-bold">Unit</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-hairline font-sans text-caption-sm text-ink">
                    <tr className="hover:bg-surface-soft">
                      <td className="p-sm font-medium">Vehicle Type</td>
                      <td className="p-sm font-mono">{scenario.vehicle_type}</td>
                      <td className="p-sm text-mute">—</td>
                    </tr>
                    <tr className="hover:bg-surface-soft">
                      <td className="p-sm font-medium">Product Weight</td>
                      <td className="p-sm font-mono">{scenario.product_weight.toFixed(1)}</td>
                      <td className="p-sm text-mute">kg</td>
                    </tr>
                    <tr className="hover:bg-surface-soft">
                      <td className="p-sm font-medium">Fuel Efficiency</td>
                      <td className="p-sm font-mono">{scenario.fuel_efficiency.toFixed(1)}</td>
                      <td className="p-sm text-mute">L/100 km</td>
                    </tr>
                    <tr className="hover:bg-surface-soft">
                      <td className="p-sm font-medium">Fuel Type</td>
                      <td className="p-sm font-mono">{scenario.fuel_type}</td>
                      <td className="p-sm text-mute">—</td>
                    </tr>
                    <tr className="hover:bg-surface-soft">
                      <td className="p-sm font-medium">Distance</td>
                      <td className="p-sm font-mono">{scenario.road_distance.toFixed(0)}</td>
                      <td className="p-sm text-mute">km</td>
                    </tr>

                    {scenario.ocean_distance > 0 && (
                      <tr className="hover:bg-surface-soft">
                        <td className="p-sm font-medium">Additional Ocean Freight Distance</td>
                        <td className="p-sm font-mono">{scenario.ocean_distance.toFixed(0)}</td>
                        <td className="p-sm text-mute">km</td>
                      </tr>
                    )}

                    {scenario.rail_distance > 0 && (
                      <tr className="hover:bg-surface-soft">
                        <td className="p-sm font-medium">Additional Rail Freight Distance</td>
                        <td className="p-sm font-mono">{scenario.rail_distance.toFixed(0)}</td>
                        <td className="p-sm text-mute">km</td>
                      </tr>
                    )}

                    {scenario.air_distance > 0 && (
                      <tr className="hover:bg-surface-soft">
                        <td className="p-sm font-medium">Additional Air Freight Distance</td>
                        <td className="p-sm font-mono">{scenario.air_distance.toFixed(0)}</td>
                        <td className="p-sm text-mute">km</td>
                      </tr>
                    )}

                    <tr className="hover:bg-surface-soft">
                      <td className="p-sm font-medium">Capacity Utilization</td>
                      <td className="p-sm font-mono">{scenario.capacity_utilization.toFixed(0)}</td>
                      <td className="p-sm text-mute">%</td>
                    </tr>
                    <tr className="hover:bg-surface-soft">
                      <td className="p-sm font-medium">Gross Density of Products Transported</td>
                      <td className="p-sm font-mono">{scenario.gross_density.toFixed(0)}</td>
                      <td className="p-sm text-mute">kg/m³</td>
                    </tr>
                    <tr className="hover:bg-surface-soft">
                      <td className="p-sm font-medium">Capacity Utilization Volume Factor</td>
                      <td className="p-sm font-mono">{scenario.capacity_volume_factor}</td>
                      <td className="p-sm text-mute">—</td>
                    </tr>
                  </tbody>
                </table>
              </div>

            </div>
          </div>

        </div>

      </div>
    </AppLayout>
  )
}
