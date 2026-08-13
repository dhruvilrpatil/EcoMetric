/**
 * Firebase configuration & initialization
 * Uses VITE_ env vars — never hardcode credentials.
 * Gracefully handles missing / placeholder credentials in local dev.
 */

import { initializeApp, getApps, getApp, type FirebaseApp } from 'firebase/app'
import { getAuth, GoogleAuthProvider, type Auth } from 'firebase/auth'
import { getFirestore, type Firestore } from 'firebase/firestore'
import { getStorage, type FirebaseStorage } from 'firebase/storage'

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
}

// ── Warn clearly in dev if Firebase config is missing ─────────────────────────
const isPlaceholder = !firebaseConfig.apiKey ||
  firebaseConfig.apiKey === 'placeholder-api-key' ||
  firebaseConfig.projectId === 'placeholder-project-id'

if (isPlaceholder && import.meta.env.DEV) {
  console.warn(
    '[EcoMetric] Firebase config not set. ' +
    'Copy frontend/.env.example to frontend/.env and fill in your Firebase project values. ' +
    'Authentication will not work until then.'
  )
}

// ── Initialize app (prevent double-init in HMR environments) ──────────────────
let app: FirebaseApp
try {
  app = getApps().length === 0 ? initializeApp(firebaseConfig) : getApp()
} catch (err) {
  console.error('[EcoMetric] Firebase initialization failed:', err)
  // Re-throw so the error is visible, but avoid silent blank screen
  throw err
}

export const auth: Auth = getAuth(app)
export const db: Firestore = getFirestore(app)
export const storage: FirebaseStorage = getStorage(app)
export const googleProvider: GoogleAuthProvider = new GoogleAuthProvider()

export default app
