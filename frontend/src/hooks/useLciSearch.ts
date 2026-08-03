/**
 * src/hooks/useLciSearch.ts
 *
 * Hook to search the Ecoinvent LCI database via the FastAPI backend.
 * Uses TanStack Query for caching, debouncing is handled by the SearchInput component.
 */

import { useQuery } from '@tanstack/react-query'
import type { LCISearchResult } from '@/types'

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1'

export function useLciSearch(query: string, category?: string) {
  return useQuery<LCISearchResult[]>({
    queryKey: ['lci_search', query, category],
    queryFn: async () => {
      if (!query || query.length < 2) return []
      
      const params = new URLSearchParams({ q: query })
      if (category) params.append('category', category)
      
      const res = await fetch(`${API_BASE}/lci/search?${params.toString()}`)
      if (!res.ok) {
        throw new Error('Failed to fetch LCI data')
      }
      return res.json()
    },
    // Only run query if there's an actual search term (min 2 chars per backend spec)
    enabled: query.length >= 2,
    staleTime: 1000 * 60 * 5, // 5 minutes cache
  })
}
