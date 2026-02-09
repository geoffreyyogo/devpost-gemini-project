/**
 * BetterAuth Server Configuration
 * 
 * Uses PostgreSQL as the session/user store.
 * This is the server-side auth instance — used in API routes and server components.
 */
import { betterAuth } from 'better-auth'

export const auth = betterAuth({
  database: {
    type: 'postgres',
    url: process.env.DATABASE_URL || 'postgresql://geoffreyyogo:och13ng@localhost:5432/smart-shamba',
  },

  // Session configuration
  session: {
    expiresIn: 60 * 60 * 24, // 24 hours in seconds
    updateAge: 60 * 60,       // refresh session every hour
    cookieCache: {
      enabled: true,
      maxAge: 5 * 60, // 5 min cache
    },
  },

  // Email + password auth (primary for farmers)
  emailAndPassword: {
    enabled: true,
    requireEmailVerification: false, // farmers may not have email
  },

  // User model extensions for farmer fields
  user: {
    additionalFields: {
      phone: {
        type: 'string',
        required: true,
        unique: true,
      },
      county: {
        type: 'string',
        required: false,
      },
      sub_county: {
        type: 'string',
        required: false,
      },
      region: {
        type: 'string',
        required: false,
      },
      farm_size: {
        type: 'number',
        required: false,
      },
      language: {
        type: 'string',
        required: false,
        defaultValue: 'en',
      },
      role: {
        type: 'string',
        required: false,
        defaultValue: 'farmer',
      },
    },
  },

  // Rate limiting
  rateLimit: {
    window: 60, // 1 minute window
    max: 10,    // 10 requests per window
  },

  // Trusted origins
  trustedOrigins: [
    'http://localhost:3000',
    'http://localhost:8000',
    process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000',
  ],
})

export type Session = typeof auth.$Infer.Session
export type User = typeof auth.$Infer.Session.user
