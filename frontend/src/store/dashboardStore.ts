/**
 * Dashboard State Management
 */

import { create } from 'zustand'
import type { BloomEvent, Alert, DashboardData } from '@/types'
import { api } from '@/lib/api'

interface DashboardState {
  data: DashboardData | null
  bloomEvents: BloomEvent[]
  alerts: Alert[]
  isLoading: boolean
  error: string | null
  
  // Actions
  fetchDashboardData: () => Promise<void>
  fetchBloomEvents: (region?: string) => Promise<void>
  fetchAlerts: (limit?: number) => Promise<void>
  refreshAll: () => Promise<void>
  clearError: () => void
}

export const useDashboardStore = create<DashboardState>((set, get) => ({
  data: null,
  bloomEvents: [],
  alerts: [],
  isLoading: false,
  error: null,

  fetchDashboardData: async () => {
    set({ isLoading: true, error: null })
    try {
      const data = await api.getDashboardData()
      set({ data, isLoading: false })
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to fetch dashboard data'
      set({ error: message, isLoading: false })
    }
  },

  fetchBloomEvents: async (region) => {
    try {
      const bloomEvents = await api.getBloomEvents(region)
      set({ bloomEvents })
    } catch (error) {
      console.error('Failed to fetch bloom events:', error)
    }
  },

  fetchAlerts: async (limit = 10) => {
    try {
      const alerts = await api.getAlerts(limit)
      set({ alerts })
    } catch (error) {
      console.error('Failed to fetch alerts:', error)
    }
  },

  refreshAll: async () => {
    const { fetchDashboardData, fetchBloomEvents, fetchAlerts } = get()
    await Promise.all([
      fetchDashboardData(),
      fetchBloomEvents(),
      fetchAlerts(),
    ])
  },

  clearError: () => set({ error: null }),
}))

