/**
 * Admin Dashboard State Management
 */

import { create } from 'zustand'
import type { Farmer, Statistics } from '@/types'
import { api } from '@/lib/api'

interface AdminState {
  farmers: Farmer[]
  statistics: Statistics | null
  recentRegistrations: Farmer[]
  isLoading: boolean
  error: string | null
  
  // Actions
  fetchFarmers: (query?: Record<string, any>) => Promise<void>
  fetchStatistics: () => Promise<void>
  fetchRecentRegistrations: (days?: number) => Promise<void>
  deleteFarmer: (farmerId: string) => Promise<boolean>
  sendAlert: (data: any) => Promise<boolean>
  refreshAll: () => Promise<void>
  clearError: () => void
}

export const useAdminStore = create<AdminState>((set, get) => ({
  farmers: [],
  statistics: null,
  recentRegistrations: [],
  isLoading: false,
  error: null,

  fetchFarmers: async (query = {}) => {
    set({ isLoading: true, error: null })
    try {
      const farmers = await api.getFarmers(query)
      set({ farmers, isLoading: false })
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to fetch farmers'
      set({ error: message, isLoading: false })
    }
  },

  fetchStatistics: async () => {
    try {
      const statistics = await api.getStatistics()
      set({ statistics })
    } catch (error) {
      console.error('Failed to fetch statistics:', error)
    }
  },

  fetchRecentRegistrations: async (days = 7) => {
    try {
      const recentRegistrations = await api.getRecentRegistrations(days)
      set({ recentRegistrations })
    } catch (error) {
      console.error('Failed to fetch recent registrations:', error)
    }
  },

  deleteFarmer: async (farmerId) => {
    set({ isLoading: true, error: null })
    try {
      const response = await api.deleteFarmer(farmerId)
      
      if (response.success) {
        // Remove farmer from local state
        set((state) => ({
          farmers: state.farmers.filter((f) => f._id !== farmerId),
          isLoading: false,
        }))
        return true
      } else {
        set({
          error: response.message || 'Failed to delete farmer',
          isLoading: false,
        })
        return false
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to delete farmer'
      set({ error: message, isLoading: false })
      return false
    }
  },

  sendAlert: async (data) => {
    set({ isLoading: true, error: null })
    try {
      const response = await api.sendAlert(data)
      
      if (response.success) {
        set({ isLoading: false })
        return true
      } else {
        set({
          error: response.message || 'Failed to send alert',
          isLoading: false,
        })
        return false
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to send alert'
      set({ error: message, isLoading: false })
      return false
    }
  },

  refreshAll: async () => {
    const { fetchFarmers, fetchStatistics, fetchRecentRegistrations } = get()
    await Promise.all([
      fetchFarmers(),
      fetchStatistics(),
      fetchRecentRegistrations(),
    ])
  },

  clearError: () => set({ error: null }),
}))

