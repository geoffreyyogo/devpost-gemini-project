/**
 * BetterAuth Client
 * 
 * Client-side auth instance for React components.
 * Provides hooks: useSession, signIn, signUp, signOut
 */
import { createAuthClient } from 'better-auth/react'

export const authClient = createAuthClient({
  baseURL: process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000',
})

// Export typed hooks and methods
export const {
  useSession,
  signIn,
  signUp,
  signOut,
} = authClient
