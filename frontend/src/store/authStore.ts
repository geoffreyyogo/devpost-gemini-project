/**
 * Authentication State Management with Zustand
 */

import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'
import type { Farmer } from '@/types'
import { api } from '@/lib/api'

interface AuthState {
  farmer: Farmer | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
  hasHydrated: boolean
  
  // Actions
  setFarmer: (farmer: Farmer | null) => void
  setHasHydrated: (hydrated: boolean) => void
  login: (phone: string, password: string) => Promise<boolean>
  register: (data: any) => Promise<boolean>
  logout: () => Promise<void>
  verifySession: () => Promise<void>
  updateProfile: (data: any) => Promise<boolean>
  clearError: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      farmer: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
      hasHydrated: false,

      setHasHydrated: (hydrated) => set({ hasHydrated: hydrated }),

      setFarmer: (farmer) =>
        set({
          farmer,
          isAuthenticated: !!farmer,
        }),

      login: async (phone, password) => {
        set({ isLoading: true, error: null })
        try {
          const response = await api.login({ phone, password })
          
          if (response.success && response.farmer) {
            set({
              farmer: response.farmer,
              isAuthenticated: true,
              isLoading: false,
            })
            return true
          } else {
            set({
              error: response.message || 'Login failed',
              isLoading: false,
            })
            return false
          }
        } catch (error) {
          const message = error instanceof Error ? error.message : 'Login failed'
          set({ error: message, isLoading: false })
          return false
        }
      },

      register: async (data) => {
        set({ isLoading: true, error: null })
        try {
          const response = await api.register(data)
          
          if (response.success && response.farmer) {
            set({
              farmer: response.farmer,
              isAuthenticated: true,
              isLoading: false,
            })
            return true
          } else {
            set({
              error: response.message || 'Registration failed',
              isLoading: false,
            })
            return false
          }
        } catch (error) {
          const message = error instanceof Error ? error.message : 'Registration failed'
          set({ error: message, isLoading: false })
          return false
        }
      },

      logout: async () => {
        try {
          await api.logout()
        } catch (error) {
          console.error('Logout error:', error)
        } finally {
          set({
            farmer: null,
            isAuthenticated: false,
            error: null,
          })
        }
      },

      verifySession: async () => {
        set({ isLoading: true })
        try {
          const farmer = await api.verifySession()
          
          if (farmer) {
            set({
              farmer,
              isAuthenticated: true,
              isLoading: false,
            })
          } else {
            set({
              farmer: null,
              isAuthenticated: false,
              isLoading: false,
            })
          }
        } catch (error) {
          set({
            farmer: null,
            isAuthenticated: false,
            isLoading: false,
          })
        }
      },

      updateProfile: async (data) => {
        set({ isLoading: true, error: null })
        try {
          const response = await api.updateProfile(data)
          
          if (response.success) {
            // Refresh farmer data
            await get().verifySession()
            return true
          } else {
            set({
              error: response.message || 'Update failed',
              isLoading: false,
            })
            return false
          }
        } catch (error) {
          const message = error instanceof Error ? error.message : 'Update failed'
          set({ error: message, isLoading: false })
          return false
        }
      },

      clearError: () => set({ error: null }),
    }),
    {
      name: 'auth-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        farmer: state.farmer,
        isAuthenticated: state.isAuthenticated,
      }),
      onRehydrateStorage: () => (state) => {
        state?.setHasHydrated(true)
      },
    }
  )
)

