/**
 * src/hooks/useLcaResults.ts
 *
 * Hooks for triggering LCA calculations and fetching results from FastAPI / AWS RDS.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'

import { LCIAMatrixResponse } from '@/types'

export interface HotspotItem {
  module: string
  material_name: string
  gwp_kg_co2e: number
  percentage: number
  description: string
}

export interface LcaResultRow {
  id: string
  project_id: string
  run_id: string
  lcia_method: string
  is_final: boolean
  functional_unit: string
  carbon_footprint_kg_co2e: number | null
  gwp_total_kg_co2e: Record<string, number> | null
  gwp_fossil_kg_co2e: Record<string, number> | null
  compliance_summary: Record<string, string> | null
  hotspots?: HotspotItem[] | string | null
  run_timestamp: string
  // Full LCIA Matrix
  matrix?: LCIAMatrixResponse
  // Resource use
  penre_mj: Record<string, number> | null
  pere_mj: Record<string, number> | null
  fw_m3: Record<string, number> | null
  // Waste
  nhwd_kg: Record<string, number> | null
  mfr_kg: Record<string, number> | null
  // Operational
  annual_electricity_kwh: number | null
  lifetime_electricity_kwh: number | null
  waste_to_landfill_kg: number | null
  waste_to_recycling_kg: number | null
}


export interface JobStatusResponse {
  status: 'queued' | 'running' | 'complete' | 'failed'
  progress: number
  job_id: string
  carbon_footprint_kg_co2e?: number
  error_message?: string
}

/** Trigger LCA calculation for a project */
export function useCalculateLca(projectId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () =>
      api.post<{ job_id: string; run_id: string; status: string }>(
        `/projects/${projectId}/calculate`
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['lca_results', projectId] })
    },
  })
}

/** Poll job status by job_id */
export function useJobStatus(projectId: string, jobId: string | null, enabled: boolean) {
  const queryClient = useQueryClient()
  return useQuery<JobStatusResponse>({
    queryKey: ['job_status', projectId, jobId],
    queryFn: async () => {
      const res = await api.get<JobStatusResponse>(`/projects/${projectId}/jobs/${jobId}`)
      if (res.status === 'complete') {
        queryClient.invalidateQueries({ queryKey: ['lca_results', projectId] })
      }
      return res
    },
    enabled: enabled && !!jobId,
    refetchInterval: (query) => {
      const status = query.state.data?.status
      if (status === 'complete' || status === 'failed') return false
      return 1500 // poll every 1.5s while running
    },
    staleTime: 0,
  })
}

/** Fetch final LCA results for a project */
export function useLcaResults(projectId: string, enabled = true) {
  return useQuery<LcaResultRow>({
    queryKey: ['lca_results', projectId],
    queryFn: () => api.get<LcaResultRow>(`/projects/${projectId}/results`),
    enabled: enabled && !!projectId,
    staleTime: 0,
    retry: false,
  })
}

/** Fetch full LCIA Matrix (with fallback preview if needed) */
export function useLciaMatrix(projectId: string, methodology = 'EN_15804_A2', enabled = true) {
  return useQuery<LCIAMatrixResponse>({
    queryKey: ['lcia_matrix', projectId, methodology],
    queryFn: () => api.get<LCIAMatrixResponse>(`/projects/${projectId}/matrix?methodology=${methodology}`),
    enabled: enabled && !!projectId,
    staleTime: 0,
    retry: false,
  })
}

/** Save / replace BOM items for a project */
export function useSaveBom(projectId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (items: BomPayloadItem[]) =>
      api.post(`/projects/${projectId}/bom`, items),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['project_bom', projectId] })
      queryClient.invalidateQueries({ queryKey: ['lca_results', projectId] })
      queryClient.invalidateQueries({ queryKey: ['project', projectId] })
    },
  })
}

export interface BomPayloadItem {
  material_name: string
  mass_kg: number
  unit: string
  lc_module: string
  lci_dataset_id?: string | null
  data_quality: string
  is_cut_off: boolean
  cut_off_reason?: string | null
}
