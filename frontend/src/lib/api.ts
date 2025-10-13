/**
 * API Client for BloomWatch Kenya
 * Handles all communication with the backend
 */

import axios, { AxiosError, AxiosInstance } from 'axios'
import type {
  ApiResponse,
  AuthResponse,
  Farmer,
  LoginFormData,
  RegisterFormData,
  ProfileUpdateData,
  BloomEvent,
  Alert,
  Statistics,
  DashboardData,
  SendAlertData,
  ChatMessage,
} from '@/types'

// FastAPI server running on port 8000
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

class ApiClient {
  private client: AxiosInstance
  private sessionToken: string | null = null

  constructor() {
    this.client = axios.create({
      baseURL: API_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // Request interceptor to add auth token
    this.client.interceptors.request.use(
      (config) => {
        const token = this.getSessionToken()
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }
        return config
      },
      (error) => Promise.reject(error)
    )

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        if (error.response?.status === 401) {
          this.clearSession()
          if (typeof window !== 'undefined') {
            window.location.href = '/login'
          }
        }
        return Promise.reject(error)
      }
    )
  }

  private getSessionToken(): string | null {
    if (typeof window === 'undefined') return null
    if (this.sessionToken) return this.sessionToken
    
    const token = localStorage.getItem('session_token')
    if (token) {
      this.sessionToken = token
    }
    return token
  }

  private setSessionToken(token: string): void {
    this.sessionToken = token
    if (typeof window !== 'undefined') {
      localStorage.setItem('session_token', token)
    }
  }

  private clearSession(): void {
    this.sessionToken = null
    if (typeof window !== 'undefined') {
      localStorage.removeItem('session_token')
    }
  }

  // ============================================
  // Authentication Endpoints
  // ============================================

  async login(data: LoginFormData): Promise<AuthResponse> {
    try {
      const response = await this.client.post<AuthResponse>('/api/auth/login', data)
      if (response.data.success && response.data.session_token) {
        this.setSessionToken(response.data.session_token)
      }
      return response.data
    } catch (error) {
      throw this.handleError(error)
    }
  }

  async register(data: RegisterFormData): Promise<AuthResponse> {
    try {
      const response = await this.client.post<AuthResponse>('/api/auth/register', data)
      if (response.data.success && response.data.session_token) {
        this.setSessionToken(response.data.session_token)
      }
      return response.data
    } catch (error) {
      throw this.handleError(error)
    }
  }

  async logout(): Promise<void> {
    try {
      await this.client.post('/api/auth/logout')
    } finally {
      this.clearSession()
    }
  }

  async verifySession(): Promise<Farmer | null> {
    try {
      const response = await this.client.get<ApiResponse<Farmer>>('/api/auth/verify')
      return response.data.data || null
    } catch (error) {
      return null
    }
  }

  // ============================================
  // Farmer Endpoints
  // ============================================

  async getFarmer(phone: string): Promise<Farmer | null> {
    try {
      const response = await this.client.get<ApiResponse<Farmer>>(`/api/farmers/${phone}`)
      return response.data.data || null
    } catch (error) {
      return null
    }
  }

  async updateProfile(data: ProfileUpdateData): Promise<ApiResponse> {
    try {
      const response = await this.client.put<ApiResponse>('/api/farmers/profile', data)
      return response.data
    } catch (error) {
      throw this.handleError(error)
    }
  }

  async changePassword(oldPassword: string, newPassword: string): Promise<ApiResponse> {
    try {
      const response = await this.client.post<ApiResponse>('/api/auth/change-password', {
        old_password: oldPassword,
        new_password: newPassword,
      })
      return response.data
    } catch (error) {
      throw this.handleError(error)
    }
  }

  // ============================================
  // Dashboard Endpoints
  // ============================================

  async getDashboardData(): Promise<DashboardData> {
    try {
      const response = await this.client.get<ApiResponse<DashboardData>>('/api/dashboard')
      return response.data.data!
    } catch (error) {
      throw this.handleError(error)
    }
  }

  async getBloomEvents(region?: string): Promise<BloomEvent[]> {
    try {
      const params = region ? { region } : {}
      const response = await this.client.get<ApiResponse<BloomEvent[]>>('/api/bloom/events', { params })
      return response.data.data || []
    } catch (error) {
      throw this.handleError(error)
    }
  }

  async getAlerts(limit = 10): Promise<Alert[]> {
    try {
      const response = await this.client.get<ApiResponse<Alert[]>>('/api/alerts', {
        params: { limit },
      })
      return response.data.data || []
    } catch (error) {
      throw this.handleError(error)
    }
  }

  async getCountyMapData(countyName: string): Promise<any> {
    try {
      const response = await this.client.get(`/api/county/${countyName}/map-data`)
      return response.data.data
    } catch (error) {
      throw this.handleError(error)
    }
  }

  // ============================================
  // Public Data Endpoints
  // ============================================

  async getRegionsAndCrops(): Promise<{
    regions: Record<string, any>
    crops: Record<string, any>
  }> {
    try {
      // Fetch regions (which includes both regions and crops)
      const response = await this.client.get('/api/public/regions')
      
      console.log('Regions API full response:', response.data)
      console.log('Regions count:', Object.keys(response.data.data?.regions || {}).length)
      console.log('Crops count:', Object.keys(response.data.data?.crops || {}).length)
      
      if (!response.data.success) {
        throw new Error('API returned success: false')
      }
      
      return {
        regions: response.data.data.regions || {},
        crops: response.data.data.crops || {}
      }
    } catch (error) {
      console.error('Failed to fetch regions and crops:', error)
      // Don't use fallback - let user know there's an error
      throw new Error('Could not load regions and crops data. Please check if the server is running.')
    }
  }

  // ============================================
  // Admin Endpoints
  // ============================================

  async getFarmers(query: Record<string, any> = {}): Promise<Farmer[]> {
    try {
      const response = await this.client.get<ApiResponse<Farmer[]>>('/api/admin/farmers', {
        params: query,
      })
      return response.data.data || []
    } catch (error) {
      throw this.handleError(error)
    }
  }

  async getStatistics(): Promise<Statistics> {
    try {
      const response = await this.client.get<ApiResponse<Statistics>>('/api/admin/statistics')
      return response.data.data!
    } catch (error) {
      throw this.handleError(error)
    }
  }

  async deleteFarmer(farmerId: string): Promise<ApiResponse> {
    try {
      const response = await this.client.delete<ApiResponse>(`/api/admin/farmers/${farmerId}`)
      return response.data
    } catch (error) {
      throw this.handleError(error)
    }
  }

  async sendAlert(data: SendAlertData): Promise<ApiResponse> {
    try {
      const response = await this.client.post<ApiResponse>('/api/admin/alerts/send', data)
      return response.data
    } catch (error) {
      throw this.handleError(error)
    }
  }

  async getRecentRegistrations(days = 7): Promise<Farmer[]> {
    try {
      const response = await this.client.get<ApiResponse<Farmer[]>>('/api/admin/registrations/recent', {
        params: { days },
      })
      return response.data.data || []
    } catch (error) {
      throw this.handleError(error)
    }
  }

  // ============================================
  // Map & Climate Data (Public)
  // ============================================

  async getLiveMapData(): Promise<any> {
    try {
      const response = await this.client.get<ApiResponse>('/api/map/live-data')
      return response.data.data
    } catch (error) {
      throw this.handleError(error)
    }
  }

  async getClimateStats(): Promise<any> {
    try {
      const response = await this.client.get<ApiResponse>('/api/map/climate-stats')
      return response.data.data
    } catch (error) {
      throw this.handleError(error)
    }
  }

  async getDataFreshness(): Promise<any> {
    try {
      const response = await this.client.get<ApiResponse>('/api/map/freshness')
      return response.data.data
    } catch (error) {
      throw this.handleError(error)
    }
  }

  // ============================================
  // Flora AI Chatbot
  // ============================================

  async sendChatMessage(message: string, history: ChatMessage[] = []): Promise<string> {
    try {
      const response = await this.client.post<ApiResponse<{ reply: string }>>('/api/chat', {
        message,
        history,
      })
      return response.data.data?.reply || 'Sorry, I could not process your request.'
    } catch (error) {
      throw this.handleError(error)
    }
  }

  // ============================================
  // Error Handling
  // ============================================

  private handleError(error: unknown): Error {
    if (axios.isAxiosError(error)) {
      const message = error.response?.data?.message || error.response?.data?.error || error.message
      return new Error(message)
    }
    return error instanceof Error ? error : new Error('An unknown error occurred')
  }

  // Admin System Management Methods
  async triggerDataFetch(): Promise<any> {
    try {
      const response = await this.client.post('/api/admin/trigger-data-fetch')
      return response.data
    } catch (error) {
      throw this.handleError(error)
    }
  }

  async triggerMLRetrain(): Promise<any> {
    try {
      const response = await this.client.post('/api/admin/trigger-ml-retrain')
      return response.data
    } catch (error) {
      throw this.handleError(error)
    }
  }

  async getSchedulerStatus(): Promise<any> {
    try {
      const response = await this.client.get('/api/admin/scheduler-status')
      return response.data
    } catch (error) {
      throw this.handleError(error)
    }
  }
}

// Export singleton instance
export const api = new ApiClient()

// Export types for convenience
export type { ApiResponse }

