/**
 * BetterAuth API Route Handler
 * 
 * Catches all auth routes: /api/auth/*
 * BetterAuth handles: sign-in, sign-up, sign-out, session, etc.
 */
import { auth } from '@/lib/auth'
import { toNextJsHandler } from 'better-auth/next-js'

export const { GET, POST } = toNextJsHandler(auth)
