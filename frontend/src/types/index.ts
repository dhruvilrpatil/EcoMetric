/**
 * EcoMetric — Core TypeScript type definitions
 * Sourced directly from PRD Section 9 (Data Models & Schema)
 */

import type { Timestamp } from 'firebase/firestore'

// ─────────────────────────────────────────────────────────────────────────────
// §9.1 Project Document
// ─────────────────────────────────────────────────────────────────────────────

export type EPDStandard = 'EN_15804_A2' | 'ISO_21930' | 'ISO_14025'

export type ProjectStatus =
  | 'draft'
  | 'in_progress'
  | 'pending_verification'
  | 'published'

export type ProjectStep = 1 | 2 | 3 | 4 | 5 | 6 | 7

export type LifecycleModule =
  | 'A1' | 'A2' | 'A3' | 'A4' | 'A5'
  | 'B1' | 'B2' | 'B3' | 'B4' | 'B5' | 'B6' | 'B7'
  | 'C1' | 'C2' | 'C3' | 'C4'
  | 'D'

export interface ProjectSetup {
  product_name: string
  sku: string
  cpc_code: string
  manufacturer: string
  manufacturer_country: string
  standard: EPDStandard
  program_operator: string
  pcr_id: string
  pcr_version: string
  functional_unit: {
    quantity: number
    unit: string
    description: string
  }
  rsl: {
    value: number
    unit: 'years' | 'cycles'
  }
  active_modules: LifecycleModule[]
}

export interface Project {
  id: string
  org_id: string
  created_by: string
  created_at: Timestamp
  updated_at: Timestamp
  status: ProjectStatus
  current_step: ProjectStep
  setup: ProjectSetup
}

// ─────────────────────────────────────────────────────────────────────────────
// §9.2 Material Document
// ─────────────────────────────────────────────────────────────────────────────

export type DataQuality = 'primary' | 'secondary' | 'proxy'

export interface Material {
  id: string
  project_id: string
  module: LifecycleModule
  name: string
  quantity: number
  unit: string
  lci_dataset_id: string
  lci_dataset_name: string
  lci_dataset_geography: string
  lci_dataset_reference_year: number
  data_quality: DataQuality
  is_omitted_cutoff: boolean
  cutoff_justification?: string
  sensitivity_coefficient?: number
  // Optimistic locking version field (PRD §14.3)
  version: number
}

// ─────────────────────────────────────────────────────────────────────────────
// §9.3 LCA Result Document
// ─────────────────────────────────────────────────────────────────────────────

export type AllocationMethod = 'none' | 'mass' | 'economic' | 'energy'
export type LCIAMethodology = 'EF_3_1' | 'TRACI_2_1' | 'ReCiPe_2016'

export type ModuleValue = number | 'ND'

export interface ImpactCategoryResult {
  unit: string
  values: Record<string, ModuleValue>
  total: number
}

export interface HotspotEntry {
  material_id: string
  sensitivity_coefficient: number
  gwp_contribution_pct: number
  mass_contribution_pct: number
}

export type IndicatorCategory = 'core' | 'additional' | 'resource_use' | 'waste_output'

export interface IndicatorRow {
  code: string
  name: string
  unit: string
  category: IndicatorCategory
  methodology: string
  modules: Record<string, number | null>
  module_flags?: Record<string, string> // e.g. "ND", "MND"
  total: number
  source_trace?: Record<string, {
    inputs?: Record<string, any>
    data_source?: string
    formula?: string
  }>
}

export interface FunctionalUnitSpec {
  value: number
  unit: string
  type: string
}

export interface LCIAMatrixResponse {
  functional_unit: FunctionalUnitSpec
  methodology: string
  epd_standard: string
  indicators: IndicatorRow[]
}

export interface LCAResult {
  id: string
  project_id: string
  run_timestamp: Timestamp
  run_by: string
  is_final: boolean

  // Matrix dimensions for audit trace
  matrix_A_dimensions: [number, number]
  matrix_B_dimensions: [number, number]
  functional_unit: string
  allocation_method: AllocationMethod
  lcia_methodology: LCIAMethodology

  // Impact results nested by category and module
  impact_results: Record<string, ImpactCategoryResult>

  // Full LCIA Matrix
  matrix?: LCIAMatrixResponse

  // Raw inventory vector g (audit trace)
  inventory_vector: Record<string, number>

  // Hotspot analysis
  hotspots: HotspotEntry[]
}

// ─────────────────────────────────────────────────────────────────────────────
// §9.4 Export Document
// ─────────────────────────────────────────────────────────────────────────────

export interface ExportDocument {
  id: string
  project_id: string
  lca_result_id: string
  generated_at: Timestamp
  generated_by: string

  public_epd: {
    pdf_url: string
    pdf_sha256: string
    format: 'EN_15942'
  }

  background_report: {
    pdf_url: string
    pdf_sha256: string
  }

  machine_readable: {
    ilcd_epd_xml_url?: string
    open_epd_json_url?: string
  }

  verifier_token?: string
  verifier_email?: string
  verifier_accessed_at?: Timestamp
}

// ─────────────────────────────────────────────────────────────────────────────
// API response types
// ─────────────────────────────────────────────────────────────────────────────

export type JobStatus = 'queued' | 'running' | 'complete' | 'failed'

export interface ComputeJobResponse {
  job_id: string
  status: JobStatus
}

export interface JobPollResponse {
  status: JobStatus
  progress_pct: number
  result_id?: string
  error_message?: string
}

export interface LCISearchResult {
  id: string
  name: string
  activity: string
  geography: string
  reference_year: number
  data_quality_score: number
  unit?: string
  activity_name?: string
  gwp_factor?: number
}

// ─────────────────────────────────────────────────────────────────────────────
// WebSocket event types (PRD §10.3)
// ─────────────────────────────────────────────────────────────────────────────

export interface CutoffStatus {
  individual_max_pct: number
  aggregate_pct: number
  compliant: boolean
  violations: Array<{
    material_name: string
    pct: number
    type: 'individual' | 'aggregate'
  }>
}

export type WebSocketEvent =
  | { type: 'material_updated'; payload: Material }
  | { type: 'cutoff_check'; payload: CutoffStatus }
  | { type: 'validation_warning'; payload: { field: string; message: string; severity: 'error' | 'warning' | 'info' } }
  | { type: 'calculation_progress'; payload: { step: string; pct: number } }
  | { type: 'calculation_complete'; payload: { result_id: string } }

// ─────────────────────────────────────────────────────────────────────────────
// User / Auth types
// ─────────────────────────────────────────────────────────────────────────────

export type UserRole = 'org_admin' | 'engineer' | 'consultant' | 'verifier' | 'viewer'

export interface UserProfile {
  uid: string
  email: string
  display_name: string
  organization: string
  role: UserRole
  created_at: Timestamp
}

// ─────────────────────────────────────────────────────────────────────────────
// Portfolio types
// ─────────────────────────────────────────────────────────────────────────────

export interface PortfolioSummary {
  total_published: number
  expiring_within_12_months: number
  average_gwp: number
  dpp_registrations_complete: number
}

export interface ComplianceDeadline {
  regulation: string
  description: string
  deadline_date: string
  days_remaining: number
  badge_label: string
}
