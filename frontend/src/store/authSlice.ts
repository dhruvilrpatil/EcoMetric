/**
 * Redux auth slice — tracks Firebase auth state in Redux
 */

import { createSlice, type PayloadAction } from '@reduxjs/toolkit'
import type { UserProfile } from '@/types'

interface AuthState {
  user: UserProfile | null
  loading: boolean
  initialized: boolean
  error: string | null
}

const initialState: AuthState = {
  user: null,
  loading: true,
  initialized: false,
  error: null,
}

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    setUser(state, action: PayloadAction<UserProfile | null>) {
      state.user = action.payload
      state.loading = false
      state.initialized = true
      state.error = null
    },
    setLoading(state, action: PayloadAction<boolean>) {
      state.loading = action.payload
    },
    setError(state, action: PayloadAction<string>) {
      state.error = action.payload
      state.loading = false
    },
    clearAuth(state) {
      state.user = null
      state.loading = false
      state.initialized = true   // ← CRITICAL: marks auth check as complete
      state.error = null
    },
  },
})

export const { setUser, setLoading, setError, clearAuth } = authSlice.actions
export default authSlice.reducer
