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
  apiKey:            import.meta.env.VITE_FIREBASE_API_KEY || 'demo-api-key-placeholder',
  authDomain:        import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || 'ecometric-mock.firebaseapp.com',
  projectId:         import.meta.env.VITE_FIREBASE_PROJECT_ID || 'ecometric-mock',
  storageBucket:     import.meta.env.VITE_FIREBASE_STORAGE_BUCKET || 'ecometric-mock.appspot.com',
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID || '123456789012',
  appId:             import.meta.env.VITE_FIREBASE_APP_ID || '1:123456789012:web:abcdef123456',
}

// ── Warn clearly in dev if Firebase config is missing ─────────────────────────
const isPlaceholder = !import.meta.env.VITE_FIREBASE_API_KEY ||
  import.meta.env.VITE_FIREBASE_API_KEY === 'placeholder-api-key' ||
  import.meta.env.VITE_FIREBASE_PROJECT_ID === 'placeholder-project-id'

if (isPlaceholder && import.meta.env.DEV) {
  console.info(
    '[EcoMetric] Running with local/mock credentials. ' +
    'To connect to a live Firebase project, copy frontend/.env.example to frontend/.env and fill in real values.'
  )
}

// ── Initialize app (prevent double-init in HMR environments) ──────────────────
let app: FirebaseApp
try {
  app = getApps().length === 0 ? initializeApp(firebaseConfig) : getApp()
} catch (err) {
  console.warn('[EcoMetric] Firebase initialization warning:', err)
  app = getApps().length > 0 ? getApp() : initializeApp({ apiKey: 'mock', projectId: 'mock' })
}

export const auth:           Auth           = getAuth(app)
export const db:             Firestore      = getFirestore(app)
export const storage:        FirebaseStorage = getStorage(app)
export const googleProvider: GoogleAuthProvider = new GoogleAuthProvider()

export default app
