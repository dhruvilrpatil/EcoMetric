/**
 * src/pages/InventoryPage.tsx
 *
 * Step 2: Inventory & Lifecycle Parameters
 * 1. Bill of Materials (A1–A3)
 * 2. Manufacturing Data & Energy (A3)
 * 3. Operational Energy & Refrigerants (B6 & B1)
 * 4. End-of-Life Scenarios (C1–C4)
 */

import { useEffect, useState, useMemo } from 'react'
import { useParams, useNavigate, useSearchParams } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useProject } from '@/hooks/useProjects'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faPlus,
  faTrash,
  faArrowRight,
  faDatabase,
  faRobot,
  faCheck,
  faTimes,
  faCircleNotch,
  faUpload,
  faBoxes,
  faBolt,
  faPlug,
  faRecycle,
  faSave,
  faSearch,
  faExclamationTriangle
} from '@fortawesome/free-solid-svg-icons'

import { AppLayout } from '@/components/organisms/AppLayout'
import { SearchInput } from '@/components/atoms/SearchInput'
import { Button, ButtonPrimary } from '@/components/atoms/Button'
import { TextInput } from '@/components/atoms/TextInput'
import { BadgeTag } from '@/components/atoms/BadgeTag'
import { NotificationCard } from '@/components/molecules/NotificationCard'
import { useLciSearch } from '@/hooks/useLciSearch'
import { useSaveBom } from '@/hooks/useLcaResults'
import { api } from '@/lib/api'
import type { LCISearchResult, LifecycleModule } from '@/types'

interface Material {
  id: string
  project_id: string
  module: LifecycleModule
  name: string
  quantity: number
  unit: string
  lci_dataset_id: string | null
  lci_dataset_name: string
  lci_dataset_geography: string
  database_version?: string
  process_type?: string
  data_quality: string
}

interface SavedBomRow {
  id: string
  project_id: string
  lc_module: LifecycleModule
  material_name: string
  mass_kg: number
  unit: string
  lci_dataset_id: string | null
  data_quality: string
  is_cut_off: boolean
  cut_off_reason: string | null
  lci_dataset_name?: string | null
  lci_dataset_geography?: string | null
  sort_order?: number
}

interface NlpCandidate {
  ecoinvent_id: string
  ecoinvent_name: string
  geography: string
  database_version?: string
  reference_year: number
  gwp_factor: number | null
  process_type?: string
  intended_module?: string
  match_confidence: number
  confidence_components?: Record<string, number>
}

interface NlpExtractedMaterial {
  material_name: string
  quantity_base: number
  unit_base: string
  material_category: string
  component_category?: string
  intended_context?: string
  module?: string
  data_provenance?: string
  confidence_ner: number
  candidates: NlpCandidate[]
  selected_match: NlpCandidate | null
  match_status?: 'valid_match' | 'low_confidence' | 'not_found'
  status_message?: string
}

interface NlpExtractionResponse {
  extraction_status: 'success' | 'partial' | 'manual_required'
  extracted_materials: NlpExtractedMaterial[]
  extraction_quality_score: number
  warnings: string[]
  requires_manual_review: boolean
}

const LIFECYCLE_MODULES: LifecycleModule[] = ['A1', 'A2', 'A3', 'A4', 'A5', 'B1', 'B6', 'C1', 'C2', 'C3', 'C4']

export default function InventoryPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const { data: project } = useProject(id)

  const activeTab = (searchParams.get('tab') as 'bom' | 'manufacturing' | 'use_phase' | 'end_of_life') || 'bom'

  const [entryMode, setEntryMode] = useState<'manual' | 'nlp'>('manual')
  const [searchQuery, setSearchQuery] = useState('')
  const [bom, setBom] = useState<Material[]>([])
  const [saveError, setSaveError] = useState<string | null>(null)
  const [saveSuccess, setSaveSuccess] = useState<string | null>(null)
  const [isSavingParams, setIsSavingParams] = useState(false)

  // Sub-section parameter states
  const [manufacturing, setManufacturing] = useState({
    electricity_use_kwh: 450.0,
    electricity_grid_region: 'US',
    natural_gas_consumption_mj: 0,
    diesel_consumption_mj: 0,
    manufacturing_waste_kg: 0,
    manufacturing_waste_disposal_route: 'recycling',
    scrap_generated_kg: 0,
    scrap_recycling_rate_pct: 100,
    process_water_consumption_m3: 0,
    compressed_air_energy_mj: 0,
    compressed_air_already_in_electricity: false,
    process_emissions: [] as Array<{ id: string; substance_name: string; emission_kg: number }>,
    manufacturing_energy_mj: 1200.0,
    assembly_process_desc: 'Robotic welding, precision machining, and automated quality testing',
  })

  const totalBomMass = useMemo(() => {
    return (bom || []).reduce((acc, item) => acc + (Number(item.quantity || (item as any).mass_kg) || 0), 0)
  }, [bom])

  const fuQuantity = Number(project?.functional_unit_quantity) || 1
  const fuUnit = project?.functional_unit_unit || 'unit'
  const conversionFactor = fuQuantity > 0 ? totalBomMass / fuQuantity : 0

  const [usePhase, setUsePhase] = useState({
    annual_electricity_kwh: 12500.0,
    electricity_grid_region: 'US',
    refrigerant_type: 'R-1233zd(E)',
    refrigerant_charge_kg: 45.0,
    refrigerant_gwp: 1.0,
  })

  const [endOfLife, setEndOfLife] = useState({
    waste_to_recycling_pct: 60.0,
    waste_to_landfill_pct: 30.0,
    waste_to_incineration_pct: 10.0,
    waste_to_reuse_pct: 0.0,
    refrigerant_recovery_rate_pct: 95.0,
  })

  // NLP scanning states
  const [nlpRawText, setNlpRawText] = useState('')
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [nlpResponse, setNlpResponse] = useState<NlpExtractionResponse | null>(null)
  const [selectedCandidateMap, setSelectedCandidateMap] = useState<Record<number, NlpCandidate>>({})
  const [nlpFeedback, setNlpFeedback] = useState<Record<number, { status: 'correct' | 'incorrect' | null; notes: string }>>({})

  const { data: searchResults = [], isFetching } = useLciSearch(searchQuery)
  const { data: savedBomRows = [] } = useQuery<SavedBomRow[]>({
    queryKey: ['project_bom', id],
    queryFn: () => api.get<SavedBomRow[]>(`/projects/${id}/bom`),
    enabled: !!id,
  })
  const saveBom = useSaveBom(id!)
  const queryClient = useQueryClient()

  useEffect(() => {
    if (!savedBomRows.length || bom.length > 0) return

    setBom(savedBomRows.map((row) => ({
      id: row.id,
      project_id: row.project_id,
      module: row.lc_module,
      name: row.material_name,
      quantity: Number(row.mass_kg),
      unit: row.unit,
      lci_dataset_id: row.lci_dataset_id,
      lci_dataset_name: row.lci_dataset_name || row.material_name,
      lci_dataset_geography: row.lci_dataset_geography || 'GLO',
      data_quality: row.data_quality,
    })))
  }, [bom.length, savedBomRows])

  // Load existing parameters on mount
  useEffect(() => {
    if (!id) return
    api.get<{ manufacturing: any; use_phase: any; end_of_life: any }>(`/projects/${id}/parameters`)
      .then((res) => {
        if (res.manufacturing && Object.keys(res.manufacturing).length > 0) {
          setManufacturing((prev) => ({
            ...prev,
            electricity_use_kwh: Number(res.manufacturing.electricity_use_kwh ?? prev.electricity_use_kwh),
            electricity_grid_region: res.manufacturing.electricity_grid_region || prev.electricity_grid_region,
            natural_gas_consumption_mj: Number(res.manufacturing.natural_gas_consumption_mj ?? prev.natural_gas_consumption_mj),
            diesel_consumption_mj: Number(res.manufacturing.diesel_consumption_mj ?? prev.diesel_consumption_mj),
            manufacturing_waste_kg: Number(res.manufacturing.manufacturing_waste_kg ?? prev.manufacturing_waste_kg),
            manufacturing_waste_disposal_route: res.manufacturing.manufacturing_waste_disposal_route || prev.manufacturing_waste_disposal_route,
            scrap_generated_kg: Number(res.manufacturing.scrap_generated_kg ?? prev.scrap_generated_kg),
            scrap_recycling_rate_pct: Number(res.manufacturing.scrap_recycling_rate_pct ?? prev.scrap_recycling_rate_pct),
            process_water_consumption_m3: Number(res.manufacturing.process_water_consumption_m3 ?? prev.process_water_consumption_m3),
            compressed_air_energy_mj: Number(res.manufacturing.compressed_air_energy_mj ?? prev.compressed_air_energy_mj),
            compressed_air_already_in_electricity: Boolean(res.manufacturing.compressed_air_already_in_electricity ?? prev.compressed_air_already_in_electricity),
            process_emissions: Array.isArray(res.manufacturing.process_emissions) ? res.manufacturing.process_emissions : prev.process_emissions,
            manufacturing_energy_mj: Number(res.manufacturing.manufacturing_energy_mj ?? prev.manufacturing_energy_mj),
            assembly_process_desc: res.manufacturing.assembly_process_desc || prev.assembly_process_desc,
          }))
        }
        if (res.use_phase && Object.keys(res.use_phase).length > 0) {
          setUsePhase((prev) => ({
            ...prev,
            annual_electricity_kwh: Number(res.use_phase.annual_electricity_kwh ?? prev.annual_electricity_kwh),
            electricity_grid_region: res.use_phase.electricity_grid_region || prev.electricity_grid_region,
            refrigerant_type: res.use_phase.refrigerant_type || prev.refrigerant_type,
            refrigerant_charge_kg: Number(res.use_phase.refrigerant_charge_kg ?? prev.refrigerant_charge_kg),
            refrigerant_gwp: Number(res.use_phase.refrigerant_gwp ?? prev.refrigerant_gwp),
          }))
        }
        if (res.end_of_life && Object.keys(res.end_of_life).length > 0) {
          setEndOfLife((prev) => ({
            ...prev,
            waste_to_recycling_pct: Number(res.end_of_life.waste_to_recycling_pct ?? prev.waste_to_recycling_pct),
            waste_to_landfill_pct: Number(res.end_of_life.waste_to_landfill_pct ?? prev.waste_to_landfill_pct),
            waste_to_incineration_pct: Number(res.end_of_life.waste_to_incineration_pct ?? prev.waste_to_incineration_pct),
            waste_to_reuse_pct: Number(res.end_of_life.waste_to_reuse_pct ?? prev.waste_to_reuse_pct),
            refrigerant_recovery_rate_pct: Number(res.end_of_life.refrigerant_recovery_rate_pct ?? prev.refrigerant_recovery_rate_pct),
          }))
        }
      })
      .catch(() => { })
  }, [id])

  const breadcrumbs = [
    { label: 'Projects', to: '/dashboard' },
    { label: 'Inventory & Parameters' },
  ]

  const projectNav = {
    projectId: id || 'new',
    currentStep: 2 as const,
    highestCompletedStep: (bom.length > 0 || savedBomRows.length > 0 ? 2 : 1) as any,
  }

  function handleAddMaterial(
    lci: LCISearchResult | NlpCandidate,
    customQty = 1,
    customName?: string,
    targetModule: LifecycleModule = 'A1',
    processType?: string,
    dbVersion?: string
  ) {
    const isNlpCand = 'ecoinvent_id' in lci
    const dsId = isNlpCand ? lci.ecoinvent_id : lci.id
    const dsName = isNlpCand ? lci.ecoinvent_name : (lci.name || lci.activity_name || lci.id)
    const geo = lci.geography ?? 'GLO'
    const procType = processType || (isNlpCand ? lci.process_type : undefined)
    const databaseVer = dbVersion || (isNlpCand ? lci.database_version : 'ecoinvent 3.12')

    const newMat: Material = {
      id: crypto.randomUUID(),
      project_id: id || '',
      module: targetModule,
      name: customName || dsName,
      quantity: customQty,
      unit: 'kg',
      lci_dataset_id: dsId,
      lci_dataset_name: dsName,
      lci_dataset_geography: geo,
      database_version: databaseVer,
      process_type: procType,
      data_quality: 'SECONDARY',
    }
    setBom(prev => [...prev, newMat])
  }

  function handleRemove(matId: string) {
    setBom(prev => prev.filter(m => m.id !== matId))
  }

  async function handleSaveAll() {
    setSaveError(null)
    setSaveSuccess(null)
    setIsSavingParams(true)

    try {
      if (bom.length > 0) {
        await saveBom.mutateAsync(
          bom.map(m => ({
            material_name: m.name,
            mass_kg: m.quantity,
            unit: m.unit,
            lc_module: m.module,
            lci_dataset_id: m.lci_dataset_id,
            data_quality: m.data_quality.toUpperCase(),
            is_cut_off: false,
          }))
        )
      }
      await api.post(`/projects/${id}/parameters`, {
        manufacturing,
        use_phase: usePhase,
        end_of_life: endOfLife,
      })
      queryClient.invalidateQueries({ queryKey: ['project', id] })
      queryClient.invalidateQueries({ queryKey: ['lca_results', id] })
      setSaveSuccess('All inventory and lifecycle parameters saved successfully!')
      setTimeout(() => setSaveSuccess(null), 4000)
    } catch (err: any) {
      setSaveError(err?.message || 'Failed to save inventory parameters. Please try again.')
    } finally {
      setIsSavingParams(false)
    }
  }

  async function handleNext() {
    await handleSaveAll()
    navigate(`/projects/${id}/transportation`)
  }

  // NLP specific functions
  async function handleNlpScan() {
    if (!nlpRawText.trim()) return
    setIsAnalyzing(true)
    try {
      const res = await api.post<NlpExtractionResponse>(`/projects/${id}/nlp/extract`, {
        raw_text: nlpRawText,
        file_name: 'bom_upload.txt'
      })
      setNlpResponse(res)
      setSelectedCandidateMap({})
      setNlpFeedback({})
    } catch (err: any) {
      setSaveError('AI Extraction failed. Please search manually.')
    } finally {
      setIsAnalyzing(false)
    }
  }

  async function submitFeedback(idx: number, status: 'correct' | 'incorrect', extractedName: string, ecoinventId: string, components: any) {
    setNlpFeedback(prev => ({
      ...prev,
      [idx]: { status, notes: prev[idx]?.notes || '' }
    }))
    try {
      await api.post(`/projects/${id}/nlp/feedback`, {
        extracted_material_name: extractedName,
        selected_ecoinvent_id: ecoinventId,
        user_feedback: status,
        user_notes: nlpFeedback[idx]?.notes || '',
        confidence_components: components
      })
    } catch (err) {
      console.error('Failed to submit active learning feedback:', err)
    }
  }

  function addAllNlpMatches() {
    if (!nlpResponse) return
    let addedCount = 0
    nlpResponse.extracted_materials.forEach((mat, idx) => {
      const activeMatch = selectedCandidateMap[idx] || mat.selected_match
      if (activeMatch && mat.match_status !== 'not_found') {
        handleAddMaterial(
          activeMatch,
          mat.quantity_base,
          mat.material_name,
          (mat.module as LifecycleModule) || 'A1',
          activeMatch.process_type,
          activeMatch.database_version
        )
        addedCount++
      }
    })
    if (addedCount < nlpResponse.extracted_materials.length) {
      setSaveSuccess(`Added ${addedCount} matched items to BOM. ${nlpResponse.extracted_materials.length - addedCount} item(s) require manual selection.`)
    } else {
      setSaveSuccess(`Added all ${addedCount} verified materials to BOM.`)
    }
    setTimeout(() => setSaveSuccess(null), 4000)
  }

  const eolSum = endOfLife.waste_to_recycling_pct + endOfLife.waste_to_landfill_pct + endOfLife.waste_to_incineration_pct + endOfLife.waste_to_reuse_pct

  return (
    <AppLayout breadcrumbs={breadcrumbs} projectNav={projectNav}>
      <div className="w-full max-w-content-max mx-auto px-hero-h py-section">

        {saveError && (
          <div className="mb-lg">
            <NotificationCard variant="error" title="Action Failed">{saveError}</NotificationCard>
          </div>
        )}

        {saveSuccess && (
          <div className="mb-lg bg-surface-soft border-l-4 border-success p-md rounded-sm text-body-sm text-ink font-medium">
            {saveSuccess}
          </div>
        )}

        {/* Top Sub-Navigation Tabs Bar */}
        <div className="flex border border-hairline mb-xl bg-white rounded-sm p-xs shadow-sm gap-xs flex-wrap">
          <button
            className={`flex-1 py-md px-md rounded-sm font-semibold text-body-sm flex items-center justify-center gap-xs transition-all ${activeTab === 'bom' ? 'bg-primary text-white shadow-sm' : 'text-mute hover:bg-surface-soft hover:text-ink'
              }`}
            onClick={() => setSearchParams({ tab: 'bom' })}
          >
            <FontAwesomeIcon icon={faBoxes} />
            1. Bill of Materials (A1–A3)
          </button>

          <button
            className={`flex-1 py-md px-md rounded-sm font-semibold text-body-sm flex items-center justify-center gap-xs transition-all ${activeTab === 'manufacturing' ? 'bg-primary text-white shadow-sm' : 'text-mute hover:bg-surface-soft hover:text-ink'
              }`}
            onClick={() => setSearchParams({ tab: 'manufacturing' })}
          >
            <FontAwesomeIcon icon={faBolt} />
            2. Manufacturing Energy (A3)
          </button>

          <button
            className={`flex-1 py-md px-md rounded-sm font-semibold text-body-sm flex items-center justify-center gap-xs transition-all ${activeTab === 'use_phase' ? 'bg-primary text-white shadow-sm' : 'text-mute hover:bg-surface-soft hover:text-ink'
              }`}
            onClick={() => setSearchParams({ tab: 'use_phase' })}
          >
            <FontAwesomeIcon icon={faPlug} />
            3. Operational Energy (B6)
          </button>

          <button
            className={`flex-1 py-md px-md rounded-sm font-semibold text-body-sm flex items-center justify-center gap-xs transition-all ${activeTab === 'end_of_life' ? 'bg-primary text-white shadow-sm' : 'text-mute hover:bg-surface-soft hover:text-ink'
              }`}
            onClick={() => setSearchParams({ tab: 'end_of_life' })}
          >
            <FontAwesomeIcon icon={faRecycle} />
            4. End-of-Life (C1–C4)
          </button>
        </div>

        {/* TAB 1: BILL OF MATERIALS */}
        {activeTab === 'bom' && (
          <div className="flex flex-col desktop-small:flex-row gap-xxl">

            {/* LEFT PANE: Search / NLP scan */}
            <div className="flex-1 border border-hairline rounded-sm bg-white overflow-hidden flex flex-col h-[750px]">

              {/* Header Tabs */}
              <div className="flex border-b border-hairline bg-surface-soft">
                <button
                  className={`flex-1 py-md text-body-sm font-semibold border-b-2 transition-all ${entryMode === 'manual' ? 'border-primary text-primary' : 'border-transparent text-mute hover:text-ink'}`}
                  onClick={() => setEntryMode('manual')}
                >
                  <FontAwesomeIcon icon={faDatabase} className="mr-sm text-primary" />
                  Manual DB Search
                </button>
                <button
                  className={`flex-1 py-md text-body-sm font-semibold border-b-2 transition-all ${entryMode === 'nlp' ? 'border-primary text-primary' : 'border-transparent text-mute hover:text-ink'}`}
                  onClick={() => setEntryMode('nlp')}
                >
                  <FontAwesomeIcon icon={faRobot} className="mr-sm text-primary" />
                  AI NLP Scanner
                  <span className="ml-xs bg-green-100 text-green-800 text-[10px] px-sm py-xs rounded font-bold uppercase tracking-wider">New</span>
                </button>
              </div>

              {/* TAB CONTENT: MANUAL SEARCH */}
              {entryMode === 'manual' && (
                <div className="flex-1 flex flex-col overflow-hidden">
                  <div className="p-md border-b border-hairline bg-surface-soft">
                    <SearchInput
                      label="Search LCI Data"
                      placeholder="Search materials, processes… (min 2 chars)"
                      onSearch={setSearchQuery}
                      loading={isFetching}
                    />
                  </div>

                  <div className="flex-1 overflow-y-auto p-md flex flex-col gap-sm">
                    {searchQuery.length < 2 && (
                      <div className="text-center text-mute mt-xl text-body-sm">
                        <p className="mb-sm">Type at least 2 characters to search</p>
                        <p className="text-caption-sm">26,000+ Ecoinvent 3.12 processes available</p>
                      </div>
                    )}

                    {searchQuery.length >= 2 && searchResults.length === 0 && !isFetching && (
                      <div className="text-center text-mute mt-xl text-body-sm">
                        No datasets found for &quot;{searchQuery}&quot;.
                      </div>
                    )}

                    {searchResults.map(result => (
                      <div
                        key={result.id}
                        className="border border-hairline p-md rounded-sm flex flex-col gap-xs hover:border-primary hover:shadow-sm transition-all cursor-default"
                      >
                        <div className="flex items-start justify-between gap-sm">
                          <div className="flex-1 min-w-0">
                            <h3 className="text-body-strong text-ink truncate">{result.name || result.activity_name}</h3>
                            <p className="text-caption-sm text-mute leading-tight truncate">{result.activity || result.name}</p>
                          </div>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleAddMaterial(result)}
                            aria-label={`Add ${result.name}`}
                            iconLeft={faPlus}
                          >
                            Add
                          </Button>
                        </div>
                        <div className="flex gap-sm mt-xs flex-wrap">
                          <BadgeTag color="info">{result.geography ?? 'GLO'}</BadgeTag>
                          {result.reference_year && (
                            <span className="text-caption-sm text-mute">{result.reference_year}</span>
                          )}
                          {result.data_quality_score != null && (
                            <span className="text-caption-sm text-mute">DQI: {Number(result.data_quality_score).toFixed(0)}</span>
                          )}
                          {result.gwp_factor != null && result.gwp_factor > 0 && (
                            <span className="text-caption-sm text-green-700 font-medium">
                              GWP: {result.gwp_factor.toFixed(3)} kg CO₂e
                            </span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* TAB CONTENT: NLP SCANNER */}
              {entryMode === 'nlp' && (
                <div className="flex-1 flex flex-col overflow-hidden p-md bg-surface">
                  <div className="flex flex-col gap-sm mb-md shrink-0">
                    <label className="text-body-strong text-ink text-caption-sm font-semibold">Paste raw BOM description text or specifications</label>
                    <textarea
                      className="text-input w-full h-[120px] font-mono text-body-sm p-sm"
                      placeholder="Example:&#10;Steel Frame: 450.5 kg&#10;Copper tube (A1) - 12 kg&#10;Polyethylene insulation: 5.5 kg"
                      value={nlpRawText}
                      onChange={(e) => setNlpRawText(e.target.value)}
                    />
                    <div className="flex justify-between items-center">
                      <span className="text-caption-sm text-mute">Or paste text from equipment data sheets.</span>
                      <ButtonPrimary onClick={handleNlpScan} disabled={isAnalyzing || !nlpRawText.trim()}>
                        {isAnalyzing ? (
                          <>
                            <FontAwesomeIcon icon={faCircleNotch} className="animate-spin mr-sm" />
                            Extracting &amp; Matching…
                          </>
                        ) : (
                          <>
                            <FontAwesomeIcon icon={faUpload} className="mr-sm" />
                            Scan BOM with NLP
                          </>
                        )}
                      </ButtonPrimary>
                    </div>
                  </div>

                  <div className="flex-1 overflow-y-auto flex flex-col gap-md">
                    {nlpResponse && (
                      <div className="bg-white border border-hairline p-md rounded-sm">
                        <div className="flex justify-between items-center mb-md pb-xs border-b border-hairline flex-wrap gap-xs">
                          <div>
                            <h4 className="text-body-strong text-ink font-bold">BOM Analysis Report</h4>
                            <p className="text-caption-sm text-mute">
                              Extraction Quality: <span className="font-bold text-green-600">{nlpResponse.extraction_quality_score}%</span> · {nlpResponse.extracted_materials.length} material(s) identified
                            </p>
                          </div>
                          <Button variant="outline" size="sm" onClick={addAllNlpMatches} iconLeft={faPlus}>
                            Add Verified Items to BOM
                          </Button>
                        </div>

                        {nlpResponse.warnings.map((w, idx) => (
                          <p key={idx} className="text-caption-sm text-orange-700 bg-orange-50 border border-orange-200 p-sm rounded mb-sm flex items-center gap-xs">
                            <FontAwesomeIcon icon={faExclamationTriangle} className="text-orange-600" />
                            {w}
                          </p>
                        ))}

                        <div className="flex flex-col gap-md mt-md">
                          {nlpResponse.extracted_materials.map((mat, idx) => {
                            const activeMatch = selectedCandidateMap[idx] || mat.selected_match
                            const feedback = nlpFeedback[idx]
                            const isFound = !!activeMatch && (mat.match_status !== 'not_found')
                            const isHighConf = activeMatch && (activeMatch.match_confidence >= 70)

                            return (
                              <div key={idx} className="border border-slate-200 p-md rounded-sm bg-slate-50 flex flex-col gap-sm">
                                {/* Header with Material, Mass, Category, and Status */}
                                <div className="flex justify-between items-start gap-sm flex-wrap">
                                  <div>
                                    <div className="flex items-center gap-xs flex-wrap">
                                      <h5 className="text-body-strong text-ink font-bold text-[15px]">{mat.material_name}</h5>
                                      <span className="text-[10px] bg-slate-200 text-slate-700 px-1.5 py-0.5 rounded font-mono uppercase">
                                        {mat.data_provenance || 'Extracted'}
                                      </span>
                                    </div>
                                    <p className="text-caption-sm text-mute mt-0.5">
                                      Qty: <span className="font-semibold text-slate-800">{mat.quantity_base} {mat.unit_base}</span>
                                      {' · '}Category: <span className="capitalize text-slate-700 font-medium">{mat.material_category}</span>
                                      {mat.component_category && (
                                        <span> · Role: <span className="text-slate-600">{mat.component_category}</span></span>
                                      )}
                                    </p>
                                  </div>

                                  {/* Compliance & Confidence Status Badge */}
                                  <div>
                                    {isFound ? (
                                      isHighConf ? (
                                        <span className="text-[11px] px-2.5 py-1 rounded font-semibold bg-emerald-100 text-emerald-800 border border-emerald-300 flex items-center gap-1.5 shadow-2xs">
                                          <span>✓</span> Valid material match ({activeMatch.match_confidence.toFixed(0)}%)
                                        </span>
                                      ) : (
                                        <span className="text-[11px] px-2.5 py-1 rounded font-semibold bg-amber-100 text-amber-800 border border-amber-300 flex items-center gap-1.5 shadow-2xs">
                                          <FontAwesomeIcon icon={faExclamationTriangle} className="text-amber-600 text-[10px]" />
                                          Manual verification recommended ({activeMatch.match_confidence.toFixed(0)}%)
                                        </span>
                                      )
                                    ) : (
                                      <span className="text-[11px] px-2.5 py-1 rounded font-semibold bg-red-100 text-red-800 border border-red-300 flex items-center gap-1.5 shadow-2xs">
                                        <span>❌</span> Dataset not found — manual mapping required
                                      </span>
                                    )}
                                  </div>
                                </div>

                                {/* Dataset Details Box */}
                                {isFound && activeMatch ? (
                                  <div className="border border-slate-200 bg-white p-sm rounded text-caption-sm flex flex-col gap-xs shadow-2xs">
                                    <div className="flex items-start justify-between gap-sm">
                                      <span className="text-body-strong text-slate-900 font-semibold">{activeMatch.ecoinvent_name}</span>
                                    </div>

                                    {/* Metadata Badges */}
                                    <div className="flex flex-wrap gap-xs text-[11px] mt-xs">
                                      <span className="bg-blue-50 text-blue-700 px-1.5 py-0.5 rounded font-mono border border-blue-200">
                                        Geo: {activeMatch.geography}
                                      </span>
                                      <span className="bg-indigo-50 text-indigo-700 px-1.5 py-0.5 rounded font-mono border border-indigo-200">
                                        {activeMatch.database_version || 'ecoinvent 3.12 (cutoff)'}
                                      </span>
                                      <span className="bg-teal-50 text-teal-800 px-1.5 py-0.5 rounded border border-teal-200 font-medium">
                                        {activeMatch.process_type || 'Material Production'}
                                      </span>
                                      <span className="bg-slate-100 text-slate-700 px-1.5 py-0.5 rounded font-mono border border-slate-200">
                                        Module: {mat.module || 'A1'}
                                      </span>
                                      {activeMatch.gwp_factor != null && (
                                        <span className="bg-emerald-50 text-emerald-800 px-1.5 py-0.5 rounded font-semibold border border-emerald-200">
                                          GWP: {activeMatch.gwp_factor.toFixed(3)} kg CO₂e / {mat.unit_base}
                                        </span>
                                      )}
                                    </div>

                                    {/* Disambiguation: Plausible Candidates */}
                                    {mat.candidates && mat.candidates.length > 1 && (
                                      <div className="mt-xs pt-xs border-t border-slate-100">
                                        <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-500 block mb-1">
                                          Plausible Candidates ({mat.candidates.length}):
                                        </span>
                                        <div className="flex flex-col gap-1">
                                          {mat.candidates.map((cand, candIdx) => {
                                            const isSelected = cand.ecoinvent_id === activeMatch.ecoinvent_id
                                            return (
                                              <button
                                                key={candIdx}
                                                type="button"
                                                onClick={() => setSelectedCandidateMap(prev => ({ ...prev, [idx]: cand }))}
                                                className={`text-left text-[11px] p-1.5 rounded transition-all flex items-center justify-between gap-sm ${
                                                  isSelected
                                                    ? 'bg-primary/10 border border-primary text-primary font-medium'
                                                    : 'bg-slate-50 hover:bg-slate-100 border border-slate-200 text-slate-700'
                                                }`}
                                              >
                                                <span className="truncate flex-1">{cand.ecoinvent_name}</span>
                                                <div className="flex items-center gap-1 shrink-0 font-mono text-[10px]">
                                                  <span className="bg-white/80 px-1 rounded">{cand.geography}</span>
                                                  <span className="bg-white/80 px-1 rounded">{cand.process_type}</span>
                                                  <span className="font-semibold text-slate-800">{cand.match_confidence.toFixed(0)}%</span>
                                                </div>
                                              </button>
                                            )
                                          })}
                                        </div>
                                      </div>
                                    )}
                                  </div>
                                ) : (
                                  <div className="border border-red-200 bg-red-50/50 p-sm rounded text-caption-sm flex flex-col gap-xs">
                                    <p className="text-red-700">
                                      No verified material production or procurement dataset was found for <strong className="font-semibold">{mat.material_name}</strong> in the connected database.
                                    </p>
                                    <div className="mt-xs">
                                      <button
                                        type="button"
                                        onClick={() => {
                                          setEntryMode('manual')
                                          setSearchQuery(mat.material_name)
                                        }}
                                        className="bg-white text-slate-800 border border-slate-300 hover:bg-slate-50 text-caption-sm px-md py-xs rounded font-medium shadow-2xs inline-flex items-center gap-xs"
                                      >
                                        <FontAwesomeIcon icon={faSearch} />
                                        Select Dataset Manually
                                      </button>
                                    </div>
                                  </div>
                                )}

                                {/* Action Buttons and Active Learning Feedback */}
                                <div className="flex justify-between items-center mt-xs flex-wrap gap-xs">
                                  {isFound && activeMatch ? (
                                    <div className="flex gap-xs items-center">
                                      <button
                                        onClick={() => submitFeedback(idx, 'correct', mat.material_name, activeMatch.ecoinvent_id, activeMatch.confidence_components)}
                                        className={`px-sm py-xs rounded border text-[11px] transition-all ${feedback?.status === 'correct' ? 'bg-green-50 border-green-400 text-green-700 font-bold' : 'border-hairline text-mute hover:bg-slate-100'}`}
                                      >
                                        <FontAwesomeIcon icon={faCheck} className="mr-xs text-green-500" />
                                        Correct Match
                                      </button>
                                      <button
                                        onClick={() => submitFeedback(idx, 'incorrect', mat.material_name, activeMatch.ecoinvent_id, activeMatch.confidence_components)}
                                        className={`px-sm py-xs rounded border text-[11px] transition-all ${feedback?.status === 'incorrect' ? 'bg-red-50 border-red-400 text-red-700 font-bold' : 'border-hairline text-mute hover:bg-slate-100'}`}
                                      >
                                        <FontAwesomeIcon icon={faTimes} className="mr-xs text-red-500" />
                                        Wrong Material
                                      </button>
                                    </div>
                                  ) : <div />}

                                  {isFound && activeMatch && (
                                    <Button
                                      variant="outline"
                                      size="sm"
                                      onClick={() => handleAddMaterial(
                                        activeMatch,
                                        mat.quantity_base,
                                        mat.material_name,
                                        (mat.module as LifecycleModule) || 'A1',
                                        activeMatch.process_type,
                                        activeMatch.database_version
                                      )}
                                      iconLeft={faPlus}
                                    >
                                      Add to BOM
                                    </Button>
                                  )}
                                </div>

                                {feedback?.status === 'incorrect' && isFound && activeMatch && (
                                  <div className="flex gap-sm mt-xs">
                                    <input
                                      type="text"
                                      placeholder="Add notes for retraining (e.g. requires low-alloyed grade)"
                                      value={feedback.notes}
                                      onChange={(e) => setNlpFeedback(prev => ({
                                        ...prev,
                                        [idx]: { ...prev[idx], notes: e.target.value }
                                      }))}
                                      className="text-input flex-1 text-caption-sm py-xs px-sm"
                                    />
                                    <button
                                      onClick={() => submitFeedback(idx, 'incorrect', mat.material_name, activeMatch.ecoinvent_id, activeMatch.confidence_components)}
                                      className="bg-slate-700 text-white text-caption-sm px-md py-xs rounded font-medium hover:bg-slate-900"
                                    >
                                      Log Notes
                                    </button>
                                  </div>
                                )}
                              </div>
                            )
                          })}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* RIGHT PANE: Active Bill of Materials */}
            <div className="flex-[1.5] border border-hairline rounded-sm bg-white flex flex-col h-[750px]">
              <div className="p-md border-b border-hairline bg-surface-soft flex items-center justify-between">
                <div>
                  <h2 className="text-heading-sm text-ink">Bill of Materials (A1–A3)</h2>
                  <p className="text-caption-sm text-mute">{bom.length} item{bom.length !== 1 ? 's' : ''} · Total Mass: {totalBomMass.toLocaleString()} kg</p>
                </div>
                <div className="flex gap-sm">
                  <Button variant="outline" onClick={handleSaveAll} disabled={isSavingParams}>
                    <FontAwesomeIcon icon={faSave} className="mr-xs" />
                    Save
                  </Button>
                  <ButtonPrimary
                    onClick={handleNext}
                    disabled={bom.length === 0 || saveBom.isPending || isSavingParams}
                    loading={saveBom.isPending || isSavingParams}
                    iconRight={faArrowRight}
                  >
                    Continue
                  </ButtonPrimary>
                </div>
              </div>

              <div className="flex-1 overflow-y-auto p-md flex flex-col gap-md bg-surface">
                {bom.length === 0 ? (
                  <div className="text-center text-mute mt-xxl flex flex-col items-center gap-md">
                    <div className="w-[48px] h-[48px] rounded-full bg-surface-soft flex items-center justify-center">
                      <FontAwesomeIcon icon={faPlus} />
                    </div>
                    <p className="text-body-sm">Your bill of materials is empty.</p>
                    <p className="text-caption-sm">Search and add datasets from the left panel.</p>
                  </div>
                ) : (
                  bom.map((mat, index) => (
                    <div key={mat.id} className="bg-white border border-hairline p-md rounded-sm flex items-center gap-md">
                      <div className="w-[32px] h-[32px] bg-primary/10 text-primary font-bold rounded-sm flex items-center justify-center shrink-0 text-body-sm">
                        {index + 1}
                      </div>
                      <div className="flex-1 min-w-0">
                        <h4 className="text-body-strong text-ink truncate font-semibold">{mat.name}</h4>
                        <p className="text-caption-sm text-slate-700 truncate">{mat.lci_dataset_name}</p>
                        <div className="flex flex-wrap gap-xs text-[10px] mt-xs">
                          <span className="bg-blue-50 text-blue-700 px-1.5 py-0.5 rounded font-mono border border-blue-200">
                            Geo: {mat.lci_dataset_geography}
                          </span>
                          {mat.process_type && (
                            <span className="bg-teal-50 text-teal-800 px-1.5 py-0.5 rounded border border-teal-200 font-medium">
                              {mat.process_type}
                            </span>
                          )}
                          <span className="bg-indigo-50 text-indigo-700 px-1.5 py-0.5 rounded font-mono border border-indigo-200">
                            {mat.database_version || 'ecoinvent 3.12'}
                          </span>
                        </div>
                      </div>
                      <div className="flex gap-sm items-center shrink-0">
                        <div className="w-[90px]">
                          <TextInput
                            label="Qty (kg)"
                            type="number"
                            value={mat.quantity}
                            onChange={(e) => {
                              setBom(prev => {
                                const next = [...prev]
                                next[index] = { ...next[index], quantity: Number(e.target.value) }
                                return next
                              })
                            }}
                          />
                        </div>
                        <div className="w-[70px]">
                          <label className="text-body-strong text-body block mb-xxs text-caption-sm">Module</label>
                          <select
                            className="text-input w-full text-caption-sm"
                            value={mat.module}
                            onChange={(e) => {
                              setBom(prev => {
                                const next = [...prev]
                                next[index] = { ...next[index], module: e.target.value as LifecycleModule }
                                return next
                              })
                            }}
                          >
                            {LIFECYCLE_MODULES.map(m => <option key={m} value={m}>{m}</option>)}
                          </select>
                        </div>
                      </div>
                      <button
                        onClick={() => handleRemove(mat.id)}
                        className="text-mute hover:text-error transition-colors min-h-touch min-w-touch flex items-center justify-center shrink-0"
                        aria-label={`Remove ${mat.name}`}
                      >
                        <FontAwesomeIcon icon={faTrash} />
                      </button>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: MANUFACTURING ENERGY & PROCESSES */}
        {activeTab === 'manufacturing' && (
          <div className="bg-white border border-hairline rounded-sm p-xl shadow-card space-y-xl">
            <div>
              <h2 className="text-heading-md font-bold text-ink flex items-center gap-xs">
                <FontAwesomeIcon icon={faBolt} className="text-primary" />
                Module A3: Manufacturing Energy &amp; Facility Operations
              </h2>
              <p className="text-body-sm text-mute mt-xs">
                Configure direct energy inputs, waste &amp; scrap handling, water usage, compressed air, and process emissions for factory operations.
              </p>
            </div>

            {/* Read-Only Callout: Functional Unit Details */}
            <div className="bg-surface-soft border border-hairline rounded-sm p-md space-y-sm">
              <h3 className="text-body-strong font-bold text-ink text-body-sm">Functional Unit Details (Auto-Calculated)</h3>
              <div className="grid grid-cols-1 tablet:grid-cols-2 gap-md">
                <div className="bg-white p-sm border border-hairline rounded-sm">
                  <span className="text-caption-sm text-mute block font-medium">Mass of one delivered product</span>
                  <span className="text-heading-sm font-bold text-ink font-mono">{totalBomMass.toFixed(2)} kg</span>
                  <p className="text-caption-sm text-mute mt-xs">Sum of all Bill of Materials entries</p>
                </div>
                <div className="bg-white p-sm border border-hairline rounded-sm">
                  <span className="text-caption-sm text-mute block font-medium">Conversion factor</span>
                  <span className="text-heading-sm font-bold text-ink font-mono">{conversionFactor.toFixed(4)} kg/{fuUnit}</span>
                  <p className="text-caption-sm text-mute mt-xs">Auto-calculated: mass ÷ functional unit quantity. Updates automatically if BOM changes.</p>
                </div>
              </div>
            </div>

            {/* Section 1: Manufacturing Energy */}
            <div className="space-y-md border-t border-hairline pt-md">
              <h3 className="text-body-strong font-bold text-ink">Manufacturing Energy</h3>
              <div className="grid grid-cols-1 tablet:grid-cols-2 gap-xl">
                <div>
                  <TextInput
                    label="Electricity Consumption (kWh)"
                    type="number"
                    value={manufacturing.electricity_use_kwh}
                    onChange={(e) => setManufacturing({ ...manufacturing, electricity_use_kwh: parseFloat(e.target.value) || 0 })}
                    hint="Total electricity consumed per functional unit during manufacturing."
                  />
                </div>

                <div>
                  <label className="text-body-strong text-ink block mb-xs text-body-sm font-semibold">
                    Electricity Grid Mix Region
                  </label>
                  <select
                    value={manufacturing.electricity_grid_region}
                    onChange={(e) => setManufacturing({ ...manufacturing, electricity_grid_region: e.target.value })}
                    className="w-full border border-hairline rounded-sm p-sm text-body-sm bg-white font-medium"
                  >
                    <option value="US">🇺🇸 United States (NERC Mix)</option>
                    <option value="GLO">🌍 Global Average (GLO)</option>
                    <option value="DE">🇩🇪 Germany (DE)</option>
                    <option value="FR">🇫🇷 France (FR - Low Carbon Nuclear)</option>
                    <option value="CN">🇨🇳 China (CN)</option>
                    <option value="UK">🇬🇧 United Kingdom (UK)</option>
                    <option value="JP">🇯🇵 Japan (JP)</option>
                  </select>
                  <p className="text-caption-sm text-mute mt-xs">Determines carbon intensity factor for Module A3 grid electricity.</p>
                </div>

                <div>
                  <TextInput
                    label="Natural Gas Consumption (MJ)"
                    type="number"
                    value={manufacturing.natural_gas_consumption_mj}
                    onChange={(e) => setManufacturing({ ...manufacturing, natural_gas_consumption_mj: parseFloat(e.target.value) || 0 })}
                    hint="Natural gas fuel energy consumed in factory thermal equipment."
                  />
                </div>

                <div>
                  <TextInput
                    label="Diesel Consumption (MJ)"
                    type="number"
                    value={manufacturing.diesel_consumption_mj}
                    onChange={(e) => setManufacturing({ ...manufacturing, diesel_consumption_mj: parseFloat(e.target.value) || 0 })}
                    hint="Diesel used in on-site manufacturing equipment only (excluding crane/installation diesel)."
                  />
                </div>
              </div>
            </div>

            {/* Section 2: Manufacturing Waste & Scrap */}
            <div className="space-y-md border-t border-hairline pt-md">
              <h3 className="text-body-strong font-bold text-ink">Manufacturing Waste &amp; Scrap</h3>
              <div className="grid grid-cols-1 tablet:grid-cols-2 gap-xl">
                <div>
                  <TextInput
                    label="Manufacturing Waste (kg)"
                    type="number"
                    value={manufacturing.manufacturing_waste_kg}
                    onChange={(e) => setManufacturing({ ...manufacturing, manufacturing_waste_kg: parseFloat(e.target.value) || 0 })}
                  />
                </div>

                <div>
                  <label className="text-body-strong text-ink block mb-xs text-body-sm font-semibold">
                    Waste Disposal Route
                  </label>
                  <select
                    value={manufacturing.manufacturing_waste_disposal_route}
                    onChange={(e) => setManufacturing({ ...manufacturing, manufacturing_waste_disposal_route: e.target.value })}
                    className="w-full border border-hairline rounded-sm p-sm text-body-sm bg-white font-medium"
                  >
                    <option value="landfill">Landfill</option>
                    <option value="incineration">Incineration</option>
                    <option value="recycling">Recycling</option>
                    <option value="mixed">Mixed Waste Treatment</option>
                  </select>
                </div>

                <div>
                  <TextInput
                    label="Scrap Generated (kg)"
                    type="number"
                    value={manufacturing.scrap_generated_kg}
                    onChange={(e) => setManufacturing({ ...manufacturing, scrap_generated_kg: parseFloat(e.target.value) || 0 })}
                  />
                </div>

                <div>
                  <TextInput
                    label="Scrap Recycling Rate (%)"
                    type="number"
                    min={0}
                    max={100}
                    value={manufacturing.scrap_recycling_rate_pct}
                    onChange={(e) => setManufacturing({ ...manufacturing, scrap_recycling_rate_pct: Math.min(100, Math.max(0, parseFloat(e.target.value) || 0)) })}
                  />
                </div>
              </div>
            </div>

            {/* Section 3: Process Water */}
            <div className="space-y-md border-t border-hairline pt-md">
              <h3 className="text-body-strong font-bold text-ink">Process Water</h3>
              <div className="max-w-md">
                <TextInput
                  label="Process Water Consumption (m³)"
                  type="number"
                  value={manufacturing.process_water_consumption_m3}
                  onChange={(e) => setManufacturing({ ...manufacturing, process_water_consumption_m3: parseFloat(e.target.value) || 0 })}
                />
              </div>
            </div>

            {/* Section 4: Compressed Air (Optional) */}
            <div className="space-y-md border-t border-hairline pt-md">
              <h3 className="text-body-strong font-bold text-ink">Compressed Air (Optional)</h3>
              <div className="p-sm bg-amber-50 border border-amber-200 rounded-sm text-body-sm text-amber-900">
                ⚠️ Only complete this field if compressed air energy is NOT already included in your total electricity consumption above. Most compressors run on electricity already captured there — adding this separately risks double-counting.
              </div>
              <div className="grid grid-cols-1 tablet:grid-cols-2 gap-xl items-end">
                <div>
                  <TextInput
                    label="Compressed Air Energy (MJ)"
                    type="number"
                    value={manufacturing.compressed_air_energy_mj}
                    onChange={(e) => setManufacturing({ ...manufacturing, compressed_air_energy_mj: parseFloat(e.target.value) || 0 })}
                  />
                </div>
                <div className="flex items-center gap-xs pb-xs">
                  <input
                    type="checkbox"
                    id="compressed_air_confirm"
                    checked={manufacturing.compressed_air_already_in_electricity}
                    onChange={(e) => setManufacturing({ ...manufacturing, compressed_air_already_in_electricity: e.target.checked })}
                    className="w-4 h-4 text-primary rounded border-hairline"
                  />
                  <label htmlFor="compressed_air_confirm" className="text-body-sm text-ink font-medium">
                    I confirm this is NOT already included in my electricity consumption figure
                  </label>
                </div>
              </div>
            </div>

            {/* Section 5: Process Emissions (Optional) */}
            <div className="space-y-md border-t border-hairline pt-md">
              <div className="flex items-center justify-between">
                <h3 className="text-body-strong font-bold text-ink">Process Emissions (Optional)</h3>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() =>
                    setManufacturing({
                      ...manufacturing,
                      process_emissions: [
                        ...manufacturing.process_emissions,
                        { id: String(Date.now()), substance_name: '', emission_kg: 0 },
                      ],
                    })
                  }
                >
                  + Add Process Emission
                </Button>
              </div>

              {manufacturing.process_emissions.length === 0 ? (
                <p className="text-caption-sm text-mute italic">No direct process emissions specified.</p>
              ) : (
                <div className="space-y-xs">
                  {manufacturing.process_emissions.map((item, idx) => (
                    <div key={item.id || idx} className="flex items-center gap-md bg-surface-soft p-xs rounded-sm">
                      <div className="flex-1">
                        <TextInput
                          label="Substance Name"
                          value={item.substance_name}
                          onChange={(e) => {
                            const updated = [...manufacturing.process_emissions]
                            updated[idx].substance_name = e.target.value
                            setManufacturing({ ...manufacturing, process_emissions: updated })
                          }}
                        />
                      </div>
                      <div className="w-32">
                        <TextInput
                          label="Emission (kg)"
                          type="number"
                          value={item.emission_kg}
                          onChange={(e) => {
                            const updated = [...manufacturing.process_emissions]
                            updated[idx].emission_kg = parseFloat(e.target.value) || 0
                            setManufacturing({ ...manufacturing, process_emissions: updated })
                          }}
                        />
                      </div>
                      <button
                        type="button"
                        className="text-mute hover:text-error text-xs p-xs mt-md"
                        onClick={() => {
                          const updated = manufacturing.process_emissions.filter((_, i) => i !== idx)
                          setManufacturing({ ...manufacturing, process_emissions: updated })
                        }}
                      >
                        ✕
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Section 6: Assembly Summary */}
            <div className="space-y-md border-t border-hairline pt-md">
              <label className="text-body-strong text-ink block mb-xs text-body-sm font-semibold">
                Assembly &amp; Fabrication Process Summary
              </label>
              <textarea
                value={manufacturing.assembly_process_desc}
                onChange={(e) => setManufacturing({ ...manufacturing, assembly_process_desc: e.target.value })}
                className="w-full border border-hairline rounded-sm p-sm text-body-sm h-[90px]"
                placeholder="Describe machining, welding, casting, or assembly processes..."
              />
            </div>

            <div className="flex justify-end gap-md pt-md border-t border-hairline">
              <Button variant="outline" onClick={handleSaveAll} disabled={isSavingParams}>
                <FontAwesomeIcon icon={faSave} className="mr-xs" /> Save Changes
              </Button>
              <ButtonPrimary onClick={() => setSearchParams({ tab: 'use_phase' })}>
                Next: Operational Energy <FontAwesomeIcon icon={faArrowRight} className="ml-xs" />
              </ButtonPrimary>
            </div>
          </div>
        )}

        {/* TAB 3: OPERATIONAL ENERGY & REFRIGERANT */}
        {activeTab === 'use_phase' && (
          <div className="bg-white border border-hairline rounded-sm p-xl shadow-card space-y-xl">
            <div>
              <h2 className="text-heading-md font-bold text-ink flex items-center gap-xs">
                <FontAwesomeIcon icon={faPlug} className="text-primary" />
                Module B6 &amp; B1: Operational Energy &amp; Refrigerant Use
              </h2>
              <p className="text-body-sm text-mute mt-xs">
                Define annual energy consumption (B6) and refrigerant leakage rates (B1) over the product service life.
              </p>
            </div>

            <div className="grid grid-cols-1 tablet:grid-cols-2 gap-xl">
              <div className="space-y-md border-r border-hairline pr-lg">
                <h3 className="text-body-strong text-ink font-bold border-b border-hairline pb-xs">
                  ⚡ Module B6: Operational Electricity
                </h3>

                <TextInput
                  label="Annual Electricity Demand (kWh / year)"
                  type="number"
                  value={usePhase.annual_electricity_kwh}
                  onChange={(e) => setUsePhase({ ...usePhase, annual_electricity_kwh: parseFloat(e.target.value) || 0 })}
                  hint="Energy consumed per operating year."
                />

                <div>
                  <label className="text-body-strong text-ink block mb-xs text-body-sm font-semibold">
                    Use Phase Grid Mix Region
                  </label>
                  <select
                    value={usePhase.electricity_grid_region}
                    onChange={(e) => setUsePhase({ ...usePhase, electricity_grid_region: e.target.value })}
                    className="w-full border border-hairline rounded-sm p-sm text-body-sm bg-white font-medium"
                  >
                    <option value="US">🇺🇸 United States (NERC Grid)</option>
                    <option value="GLO">🌍 Global Average</option>
                    <option value="DE">🇩🇪 Germany</option>
                    <option value="FR">🇫🇷 France</option>
                    <option value="UK">🇬🇧 United Kingdom</option>
                  </select>
                </div>
              </div>

              <div className="space-y-md">
                <h3 className="text-body-strong text-ink font-bold border-b border-hairline pb-xs">
                  ❄️ Module B1: Refrigerant &amp; Leakage Specs
                </h3>

                <div>
                  <label className="text-body-strong text-ink block mb-xs text-body-sm font-semibold">
                    Refrigerant Type
                  </label>
                  <select
                    value={usePhase.refrigerant_type}
                    onChange={(e) => setUsePhase({ ...usePhase, refrigerant_type: e.target.value })}
                    className="w-full border border-hairline rounded-sm p-sm text-body-sm bg-white font-medium"
                  >
                    <option value="R-1233zd(E)">R-1233zd(E) (Ultra-Low GWP = 1.0)</option>
                    <option value="R-134a">R-134a (GWP = 1430)</option>
                    <option value="R-410A">R-410A (GWP = 2088)</option>
                    <option value="R-32">R-32 (GWP = 675)</option>
                    <option value="R-454B">R-454B (GWP = 466)</option>
                    <option value="R-744 (CO2)">R-744 CO₂ (GWP = 1.0)</option>
                  </select>
                </div>

                <TextInput
                  label="Initial Refrigerant Charge (kg)"
                  type="number"
                  value={usePhase.refrigerant_charge_kg}
                  onChange={(e) => setUsePhase({ ...usePhase, refrigerant_charge_kg: parseFloat(e.target.value) || 0 })}
                  hint="Mass of refrigerant gas filled into system."
                />

                <TextInput
                  label="Refrigerant 100-yr GWP (kg CO₂e / kg)"
                  type="number"
                  value={usePhase.refrigerant_gwp}
                  onChange={(e) => setUsePhase({ ...usePhase, refrigerant_gwp: parseFloat(e.target.value) || 0 })}
                  hint="IPCC AR6 100-year Global Warming Potential."
                />
              </div>
            </div>

            <div className="flex justify-end gap-md pt-md border-t border-hairline">
              <Button variant="outline" onClick={handleSaveAll} disabled={isSavingParams}>
                <FontAwesomeIcon icon={faSave} className="mr-xs" /> Save Changes
              </Button>
              <ButtonPrimary onClick={() => setSearchParams({ tab: 'end_of_life' })}>
                Next: End-of-Life <FontAwesomeIcon icon={faArrowRight} className="ml-xs" />
              </ButtonPrimary>
            </div>
          </div>
        )}

        {/* TAB 4: END-OF-LIFE SCENARIOS */}
        {activeTab === 'end_of_life' && (
          <div className="bg-white border border-hairline rounded-sm p-xl shadow-card space-y-xl">
            <div>
              <h2 className="text-heading-md font-bold text-ink flex items-center gap-xs">
                <FontAwesomeIcon icon={faRecycle} className="text-primary" />
                Modules C1–C4 &amp; D: End-of-Life Waste Disposition Pathways
              </h2>
              <p className="text-body-sm text-mute mt-xs">
                Specify collection and waste processing scenarios at product decommissioning.
              </p>
            </div>

            <div className={`p-md rounded-sm border text-body-sm font-semibold flex items-center justify-between ${eolSum === 100 ? 'bg-green-50 border-green-300 text-green-900' : 'bg-amber-50 border-amber-300 text-amber-900'
              }`}>
              <span>Total Waste Disposition Routing: <strong>{eolSum}%</strong></span>
              <span>{eolSum === 100 ? '✓ Validated (Sum equals 100%)' : '⚠️ Routing percentages must sum to exactly 100%'}</span>
            </div>

            <div className="grid grid-cols-1 tablet:grid-cols-2 gap-xl">
              <div>
                <TextInput
                  label="Waste to Recycling (%)"
                  type="number"
                  value={endOfLife.waste_to_recycling_pct}
                  onChange={(e) => setEndOfLife({ ...endOfLife, waste_to_recycling_pct: parseFloat(e.target.value) || 0 })}
                  hint="Percentage of metals/polymers routed to material recovery (Module C3)."
                />
              </div>

              <div>
                <TextInput
                  label="Waste to Inert Landfill (%)"
                  type="number"
                  value={endOfLife.waste_to_landfill_pct}
                  onChange={(e) => setEndOfLife({ ...endOfLife, waste_to_landfill_pct: parseFloat(e.target.value) || 0 })}
                  hint="Percentage routed to municipal landfilling (Module C4)."
                />
              </div>

              <div>
                <TextInput
                  label="Waste to Thermal Incineration (%)"
                  type="number"
                  value={endOfLife.waste_to_incineration_pct}
                  onChange={(e) => setEndOfLife({ ...endOfLife, waste_to_incineration_pct: parseFloat(e.target.value) || 0 })}
                  hint="Percentage burned with municipal energy recovery (Module C3)."
                />
              </div>

              <div>
                <TextInput
                  label="Waste to Direct Reuse (%)"
                  type="number"
                  value={endOfLife.waste_to_reuse_pct}
                  onChange={(e) => setEndOfLife({ ...endOfLife, waste_to_reuse_pct: parseFloat(e.target.value) || 0 })}
                  hint="Component refurbished for direct secondary product life."
                />
              </div>

              <div className="tablet:col-span-2 border-t border-hairline pt-md">
                <TextInput
                  label="Refrigerant Recovery Rate at Decommissioning (%)"
                  type="number"
                  value={endOfLife.refrigerant_recovery_rate_pct}
                  onChange={(e) => setEndOfLife({ ...endOfLife, refrigerant_recovery_rate_pct: parseFloat(e.target.value) || 0 })}
                  hint="Percentage of working fluid reclaimed prior to dismantling."
                />
              </div>
            </div>

            <div className="flex justify-end gap-md pt-md border-t border-hairline">
              <Button variant="outline" onClick={handleSaveAll} disabled={isSavingParams}>
                <FontAwesomeIcon icon={faSave} className="mr-xs" /> Save Parameters
              </Button>
              <ButtonPrimary onClick={handleNext} disabled={isSavingParams}>
                Save &amp; Continue to Transportation <FontAwesomeIcon icon={faArrowRight} className="ml-xs" />
              </ButtonPrimary>
            </div>
          </div>
        )}

      </div>
    </AppLayout>
  )
}
