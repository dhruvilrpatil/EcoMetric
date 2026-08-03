/**
 * src/lib/authErrors.ts
 *
 * Maps Firebase Auth error codes to user-friendly inline messages.
 * PRD CRITICAL RULE: errors surface as inline notification cards, never browser alerts.
 */

export const FIREBASE_ERROR_MESSAGES: Record<string, string> = {
  // Email/password errors
  'auth/invalid-credential':          'Incorrect email or password. Please try again.',
  'auth/invalid-email':               'Please enter a valid email address.',
  'auth/user-not-found':              'No account found with this email address.',
  'auth/wrong-password':              'Incorrect password. Please try again.',
  'auth/too-many-requests':           'Too many failed attempts. Please wait a few minutes and try again.',
  'auth/user-disabled':               'This account has been disabled. Contact support.',
  'auth/email-already-in-use':        'An account with this email already exists. Sign in instead.',
  'auth/weak-password':               'Password must be at least 8 characters.',
  'auth/requires-recent-login':       'Please sign in again to continue.',

  // Google SSO errors
  'auth/popup-closed-by-user':        'Sign-in window was closed before completing. Please try again.',
  'auth/popup-blocked':               'Sign-in popup was blocked by your browser. Allow popups for this site.',
  'auth/cancelled-popup-request':     'Only one sign-in window can be open at a time.',
  'auth/account-exists-with-different-credential':
    'An account already exists with this email using a different sign-in method.',

  // Network
  'auth/network-request-failed':      'Network error. Check your connection and try again.',

  // Generic fallback
  'auth/internal-error':              'An internal error occurred. Please try again.',
}

export function getAuthErrorMessage(code: string): string {
  return FIREBASE_ERROR_MESSAGES[code] ?? 'An unexpected error occurred. Please try again.'
}
