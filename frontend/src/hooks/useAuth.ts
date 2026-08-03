/**
 * src/hooks/useAuth.ts
 *
 * Custom hook wrapping Firebase Auth operations.
 * Returns loading, error, and action functions.
 * All errors converted to user-friendly messages via authErrors.ts.
 *
 * PRD CRITICAL RULE: errors surface inline — never throw to browser.
 */

import { useState } from 'react'
import {
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signInWithPopup,
  updateProfile,
  type AuthError,
} from 'firebase/auth'
import { doc, setDoc, serverTimestamp } from 'firebase/firestore'
import { auth, db, googleProvider } from '@/lib/firebase'
import { getAuthErrorMessage } from '@/lib/authErrors'
import type { UserRole } from '@/types'

export interface UseAuthReturn {
  loading: boolean
  error: string | null
  clearError: () => void
  signIn: (email: string, password: string) => Promise<boolean>
  signInWithGoogle: () => Promise<boolean>
  register: (params: {
    email: string
    password: string
    fullName: string
    organization: string
    role: UserRole
  }) => Promise<boolean>
}

export function useAuth(): UseAuthReturn {
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState<string | null>(null)

  function clearError() { setError(null) }

  // ── Sign in with email/password ────────────────────────────────────────────
  async function signIn(email: string, password: string): Promise<boolean> {
    setLoading(true)
    setError(null)
    try {
      await signInWithEmailAndPassword(auth, email, password)
      return true
    } catch (err) {
      const code = (err as AuthError).code ?? 'auth/internal-error'
      setError(getAuthErrorMessage(code))
      return false
    } finally {
      setLoading(false)
    }
  }

  // ── Google SSO ────────────────────────────────────────────────────────────
  async function signInWithGoogle(): Promise<boolean> {
    setLoading(true)
    setError(null)
    try {
      const result = await signInWithPopup(auth, googleProvider)

      // Create Firestore profile if first-time Google sign-in
      const user = result.user
      const profileRef = doc(db, 'users', user.uid)
      await setDoc(
        profileRef,
        {
          uid:          user.uid,
          email:        user.email,
          display_name: user.displayName ?? user.email,
          organization: '',
          role:         'engineer',
          created_at:   serverTimestamp(),
        },
        { merge: true } // Don't overwrite if profile already exists
      )

      return true
    } catch (err) {
      const code = (err as AuthError).code ?? 'auth/internal-error'
      // Don't show error if user just closed the popup intentionally
      if (code !== 'auth/popup-closed-by-user') {
        setError(getAuthErrorMessage(code))
      }
      return false
    } finally {
      setLoading(false)
    }
  }

  // ── Register with email/password ──────────────────────────────────────────
  async function register({
    email,
    password,
    fullName,
    organization,
    role,
  }: {
    email: string
    password: string
    fullName: string
    organization: string
    role: UserRole
  }): Promise<boolean> {
    setLoading(true)
    setError(null)
    try {
      // Step 1: Create Firebase Auth account
      const credential = await createUserWithEmailAndPassword(auth, email, password)
      const user = credential.user

      // Step 2: Update Firebase display name
      await updateProfile(user, { displayName: fullName })

      // Step 3: Write Firestore user profile document
      // Path: users/{uid}  (org scoping applied in Phase 3 when org is created)
      await setDoc(doc(db, 'users', user.uid), {
        uid:          user.uid,
        email,
        display_name: fullName,
        organization,
        role,
        created_at:   serverTimestamp(),
        updated_at:   serverTimestamp(),
      })

      return true
    } catch (err) {
      const code = (err as AuthError).code ?? 'auth/internal-error'
      setError(getAuthErrorMessage(code))
      return false
    } finally {
      setLoading(false)
    }
  }

  return { loading, error, clearError, signIn, signInWithGoogle, register }
}
