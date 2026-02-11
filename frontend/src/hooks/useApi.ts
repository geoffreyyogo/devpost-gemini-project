/**
 * React Query hooks for Smart Shamba.
 *
 * These hooks replace raw useEffect + useState fetch patterns with
 * TanStack Query's automatic caching, deduplication, background
 * refetch, and stale-while-revalidate.
 *
 * Each hook specifies its own staleTime/gcTime when it differs from
 * the global defaults set in QueryProvider.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { useAuthStore } from '@/store/authStore'
import type { Conversation, ConversationMessage, ChatMessage, FarmOverview } from '@/types'

// ── Query key factory ────────────────────────────────────────────────
// Centralised keys make cache invalidation predictable.
export const queryKeys = {
  // Weather
  weather: {
    all: ['weather'] as const,
    daily: (lat: number, lon: number, days?: number) =>
      ['weather', 'daily', lat, lon, days] as const,
    hourly: (lat: number, lon: number, hours?: number) =>
      ['weather', 'hourly', lat, lon, hours] as const,
    current: (lat: number, lon: number) =>
      ['weather', 'current', lat, lon] as const,
    county: (countyId: string) =>
      ['weather', 'county', countyId] as const,
  },

  // Conversations
  conversations: {
    all: ['conversations'] as const,
    list: () => ['conversations', 'list'] as const,
    messages: (convId: string) => ['conversations', 'messages', convId] as const,
  },

  // Farm
  farm: {
    all: ['farm'] as const,
    list: () => ['farm', 'list'] as const,
    overview: (farmId: number) => ['farm', 'overview', farmId] as const,
  },

  // Farmer profile
  farmer: {
    profile: () => ['farmer', 'profile'] as const,
    dashboard: () => ['farmer', 'dashboard'] as const,
  },
} as const

// ── Weather hooks ────────────────────────────────────────────────────

export function useCountyWeather(countyId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.weather.county(countyId || ''),
    queryFn: () => api.getCountyWeather(countyId!),
    enabled: !!countyId,
    staleTime: 15 * 60 * 1000, // 15 min (weather doesn't change fast)
    gcTime: 30 * 60 * 1000,
  })
}

// ── Conversation hooks ──────────────────────────────────────────────

export function useConversations() {
  const { farmer } = useAuthStore()
  return useQuery({
    queryKey: queryKeys.conversations.list(),
    queryFn: () => api.getConversations(),
    enabled: !!farmer,
    staleTime: 30 * 1000,      // 30s — conversations change often
    gcTime: 5 * 60 * 1000,
  })
}

export function useConversationMessages(convId: string | null) {
  return useQuery({
    queryKey: queryKeys.conversations.messages(convId || ''),
    queryFn: () => api.getConversationMessages(convId!),
    enabled: !!convId,
    staleTime: 10 * 1000,      // 10s — messages update frequently
    gcTime: 5 * 60 * 1000,
  })
}

// ── Farm hooks ──────────────────────────────────────────────────────

export function useFarms() {
  const { farmer } = useAuthStore()
  return useQuery({
    queryKey: queryKeys.farm.list(),
    queryFn: () => api.getFarms(),
    enabled: !!farmer,
    staleTime: 5 * 60 * 1000,  // 5 min
  })
}

export function useFarmOverview(farmId: number | undefined) {
  return useQuery<FarmOverview>({
    queryKey: queryKeys.farm.overview(farmId || 0),
    queryFn: () => api.getFarmOverview(farmId!),
    enabled: !!farmId,
    staleTime: 2 * 60 * 1000,  // 2 min
  })
}

// ── Dashboard hook ──────────────────────────────────────────────────

export function useDashboard() {
  const { farmer } = useAuthStore()
  return useQuery({
    queryKey: queryKeys.farmer.dashboard(),
    queryFn: () => api.getDashboardData(),
    enabled: !!farmer,
    staleTime: 2 * 60 * 1000,
  })
}

// ── Mutation helpers ────────────────────────────────────────────────

/**
 * Hook to send a chat message with automatic conversation cache invalidation.
 */
export function useSendChatMessage() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({
      message,
      history,
      conversationId,
    }: {
      message: string
      history: ChatMessage[]
      conversationId?: string
    }) => api.sendChatMessage(message, history, conversationId),
    onSuccess: (_data, variables) => {
      // Invalidate conversations list so it refreshes
      qc.invalidateQueries({ queryKey: queryKeys.conversations.all })
      // Invalidate messages for the current conversation
      if (variables.conversationId) {
        qc.invalidateQueries({
          queryKey: queryKeys.conversations.messages(variables.conversationId),
        })
      }
    },
  })
}
