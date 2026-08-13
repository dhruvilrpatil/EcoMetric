/**
 * src/hooks/useProjects.ts
 *
 * Hook to fetch projects list and create projects via FastAPI RDS backend.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'

export interface ProjectSummary {
  id: string
  product_name: string
  epd_standard: string
  system_boundary: string
  functional_unit_quantity: number
  functional_unit_unit: string
  created_at: string
  bom_count: number
  gwp_total: number | null
  status: string
}

export interface CreateProjectPayload {
  product: {
    product_name: string
    manufacturer_name?: string
    manufacturing_country?: string
    product_lifetime_years: number
    functional_unit_quantity: number
    functional_unit_unit: string
  }
  lca_config?: {
    epd_standard: string
    system_boundary: string
    lcia_method: string
    lci_database: string
    active_modules: string[]
  }
  bom?: unknown[]
}

export function useProjects() {
  return useQuery<ProjectSummary[]>({
    queryKey: ['projects'],
    queryFn: () => api.get<ProjectSummary[]>('/projects'),
    staleTime: 1000 * 60 * 2, // 2 minutes
  })
}

export function useCreateProject() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: CreateProjectPayload) =>
      api.post<{ project_id: string; status: string }>('/projects', payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
    },
  })
}

export function useProject(id?: string) {
  return useQuery({
    queryKey: ['project', id],
    queryFn: () => api.get<any>(`/projects/${id}`),
    enabled: !!id && id !== 'new',
    staleTime: 1000 * 60 * 2,
  })
}

export function useUpdateProject(id: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: CreateProjectPayload) =>
      api.put<{ project_id: string; status: string }>(`/projects/${id}`, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      queryClient.invalidateQueries({ queryKey: ['project', id] })
    },
  })
}

export function useDeleteProject() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) =>
      api.delete<{ project_id: string; status: string }>(`/projects/${id}`),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      queryClient.removeQueries({ queryKey: ['project', id] })
    },
  })
}

