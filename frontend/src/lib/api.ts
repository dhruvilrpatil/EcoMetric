/**
 * Axios-equivalent fetch wrapper for the EcoMetric REST API.
 * Always attaches the Firebase ID token as Bearer token.
 * Always renders loading, success, and error states per PRD critical rules.
 */

import { auth } from './firebase'

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1'

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string,
    message: string
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

async function getAuthToken(): Promise<string | null> {
  const user = auth.currentUser
  if (!user) return null
  return user.getIdToken()
}

async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = await getAuthToken()

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  }

  const response = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers,
  })

  if (!response.ok) {
    let errorBody: { detail?: string; code?: string } = {}
    try {
      errorBody = await response.json()
    } catch {
      // ignore parse error
    }
    throw new ApiError(
      response.status,
      errorBody.code ?? 'UNKNOWN_ERROR',
      errorBody.detail ?? `HTTP ${response.status}`
    )
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return undefined as unknown as T
  }

  return response.json() as Promise<T>
}

export const api = {
  get:    <T>(path: string) => apiFetch<T>(path, { method: 'GET' }),
  post:   <T>(path: string, body?: unknown) =>
    apiFetch<T>(path, { method: 'POST', body: JSON.stringify(body) }),
  put:    <T>(path: string, body?: unknown) =>
    apiFetch<T>(path, { method: 'PUT', body: JSON.stringify(body) }),
  patch:  <T>(path: string, body?: unknown) =>
    apiFetch<T>(path, { method: 'PATCH', body: JSON.stringify(body) }),
  delete: <T>(path: string) => apiFetch<T>(path, { method: 'DELETE' }),
}
