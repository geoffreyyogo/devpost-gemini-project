/**
 * API Client for Smart Shamba
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
  Farm,
  FarmFormData,
  FarmOverview,
  FarmIoTData,
  AgrovetRegisterFormData,
  BuyerRegisterFormData,
  AgrovetProfile,
  BuyerProfile,
  Transaction,
  AgrovetProduct,
  AgrovetOrder,
  MarketplaceListing,
  MarketplaceBid,
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
          // Don't redirect for chat endpoints — allow unauthenticated usage
          const url = error.config?.url || ''
          if (!url.includes('/api/chat')) {
            this.clearSession()
            if (typeof window !== 'undefined') {
              window.location.href = '/login'
            }
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

  async registerAgrovet(data: AgrovetRegisterFormData): Promise<AuthResponse> {
    try {
      const response = await this.client.post<AuthResponse>('/api/auth/register/agrovet', data)
      if (response.data.success && response.data.session_token) {
        this.setSessionToken(response.data.session_token)
      }
      return response.data
    } catch (error) {
      throw this.handleError(error)
    }
  }

  async registerBuyer(data: BuyerRegisterFormData): Promise<AuthResponse> {
    try {
      const response = await this.client.post<AuthResponse>('/api/auth/register/buyer', data)
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
    sub_counties?: Record<string, string[]>
  }> {
    try {
      // Fetch regions (which includes both regions and crops)
      const response = await this.client.get('/api/public/regions')
      
      console.log('Regions API full response:', response.data)
      console.log('Regions count:', Object.keys(response.data.data?.regions || {}).length)
      console.log('Crops count:', Object.keys(response.data.data?.crops || {}).length)
      console.log('Sub-counties count:', Object.keys(response.data.data?.sub_counties || {}).length)
      
      if (!response.data.success) {
        throw new Error('API returned success: false')
      }
      
      return {
        regions: response.data.data.regions || {},
        crops: response.data.data.crops || {},
        sub_counties: response.data.data.sub_counties || {}
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
  // Flora AI Chatbot & Conversations
  // ============================================

  async sendChatMessage(
    message: string,
    history: ChatMessage[] = [],
    conversationId?: string
  ): Promise<{ reply: string; reasoning?: string | null; conversation_id?: string }> {
    try {
      const response = await this.client.post<ApiResponse<{ reply: string; reasoning?: string | null; conversation_id?: string }>>('/api/chat', {
        message,
        history,
        conversation_id: conversationId,
      })
      return {
        reply: response.data.data?.reply || 'Sorry, I could not process your request.',
        reasoning: response.data.data?.reasoning || null,
        conversation_id: response.data.data?.conversation_id,
      }
    } catch (error) {
      throw this.handleError(error)
    }
  }

  async sendChatMessageWithImage(
    message: string,
    image: File,
    conversationId?: string
  ): Promise<{ reply: string; reasoning?: string | null; conversation_id?: string; classification: { disease: string; confidence: number; image_uid: string; alert_needed: boolean } }> {
    try {
      const formData = new FormData()
      formData.append('message', message)
      formData.append('file', image)
      if (conversationId) formData.append('conversation_id', conversationId)
      const response = await this.client.post('/api/chat/with-image', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      const data = response.data.data || {}
      return {
        reply: data.reply || 'Sorry, I could not process your image.',
        reasoning: data.reasoning || null,
        conversation_id: data.conversation_id,
        classification: data.classification || { disease: 'unknown', confidence: 0, image_uid: '', alert_needed: false },
      }
    } catch (error) {
      throw this.handleError(error)
    }
  }

  async getConversations(limit = 50): Promise<any[]> {
    try {
      const response = await this.client.get<ApiResponse<any[]>>('/api/conversations', { params: { limit } })
      return response.data.data || []
    } catch (error) {
      throw this.handleError(error)
    }
  }

  async createConversation(): Promise<any> {
    try {
      const response = await this.client.post<ApiResponse<any>>('/api/conversations')
      return response.data.data
    } catch (error) {
      throw this.handleError(error)
    }
  }

  async getConversationMessages(conversationId: string, limit = 100): Promise<any[]> {
    try {
      const response = await this.client.get<ApiResponse<any[]>>(`/api/conversations/${conversationId}/messages`, { params: { limit } })
      return response.data.data || []
    } catch (error) {
      throw this.handleError(error)
    }
  }

  async updateConversationTitle(conversationId: string, title: string): Promise<void> {
    try {
      await this.client.patch(`/api/conversations/${conversationId}`, { title })
    } catch (error) {
      throw this.handleError(error)
    }
  }

  async deleteConversation(conversationId: string): Promise<void> {
    try {
      await this.client.delete(`/api/conversations/${conversationId}`)
    } catch (error) {
      throw this.handleError(error)
    }
  }

  // ============================================
  // IoT / Sensor Endpoints
  // ============================================

  async getIoTReadings(farmId: number, hours = 24): Promise<any[]> {
    try {
      const response = await this.client.get(`/api/iot/readings/${farmId}`, { params: { hours } })
      return response.data.readings || []
    } catch (error) {
      throw this.handleError(error)
    }
  }

  async getIoTStatus(): Promise<any> {
    try {
      const response = await this.client.get('/api/iot/status')
      return response.data
    } catch (error) {
      throw this.handleError(error)
    }
  }

  // ============================================
  // Farm Management Endpoints
  // ============================================

  async getFarms(): Promise<Farm[]> {
    try {
      const response = await this.client.get<ApiResponse<Farm[]>>('/api/farms')
      return response.data.data || []
    } catch (error) {
      throw this.handleError(error)
    }
  }

  async createFarm(data: FarmFormData): Promise<Farm> {
    try {
      const response = await this.client.post<ApiResponse<Farm>>('/api/farms', data)
      return response.data.data!
    } catch (error) {
      throw this.handleError(error)
    }
  }

  async updateFarm(farmId: number, data: Partial<FarmFormData>): Promise<Farm> {
    try {
      const response = await this.client.put<ApiResponse<Farm>>(`/api/farms/${farmId}`, data)
      return response.data.data!
    } catch (error) {
      throw this.handleError(error)
    }
  }

  async deleteFarm(farmId: number): Promise<ApiResponse> {
    try {
      const response = await this.client.delete<ApiResponse>(`/api/farms/${farmId}`)
      return response.data
    } catch (error) {
      throw this.handleError(error)
    }
  }

  async getFarmOverview(farmId: number): Promise<FarmOverview> {
    try {
      const response = await this.client.get<ApiResponse<FarmOverview>>(`/api/farms/${farmId}/overview`)
      return response.data.data!
    } catch (error) {
      throw this.handleError(error)
    }
  }

  async getFarmIoTData(farmId: number, hours = 24): Promise<FarmIoTData> {
    try {
      const response = await this.client.get<ApiResponse<FarmIoTData>>(`/api/farms/${farmId}/iot`, { params: { hours } })
      return response.data.data!
    } catch (error) {
      throw this.handleError(error)
    }
  }

  // ============================================
  // Agrovet Endpoints
  // ============================================

  async getAgrovetProducts(params: { category?: string; county?: string; crop?: string } = {}): Promise<any> {
    try {
      const response = await this.client.get('/api/agrovet/products', { params })
      return response.data
    } catch (error) {
      throw this.handleError(error)
    }
  }

  async getAgrovetProduct(productId: number): Promise<any> {
    try {
      const response = await this.client.get(`/api/agrovet/products/${productId}`)
      return response.data
    } catch (error) {
      throw this.handleError(error)
    }
  }

  async createAgrovetProduct(data: Record<string, any>): Promise<any> {
    try {
      const response = await this.client.post('/api/agrovet/products', data)
      return response.data
    } catch (error) {
      throw this.handleError(error)
    }
  }

  async createAgrovetOrder(data: {
    farmer_id: number; product_id: number; quantity: number;
    payment_method?: string; delivery_address?: string; order_source?: string;
  }): Promise<any> {
    try {
      const response = await this.client.post('/api/agrovet/orders', data)
      return response.data
    } catch (error) {
      throw this.handleError(error)
    }
  }

  async getFarmerOrders(farmerId: number): Promise<any> {
    try {
      const response = await this.client.get(`/api/agrovet/orders/${farmerId}`)
      return response.data
    } catch (error) {
      throw this.handleError(error)
    }
  }

  async getShopOrders(status?: string): Promise<any> {
    try {
      const params: Record<string, string> = {}
      if (status) params.status = status
      const response = await this.client.get('/api/agrovet/orders/my-shop', { params })
      return response.data
    } catch (error) {
      throw this.handleError(error)
    }
  }

  async updateOrderStatus(orderId: number, data: { delivery_status?: string; payment_status?: string }): Promise<any> {
    try {
      const params = new URLSearchParams()
      if (data.delivery_status) params.set('delivery_status', data.delivery_status)
      if (data.payment_status) params.set('payment_status', data.payment_status)
      const response = await this.client.patch(`/api/agrovet/orders/${orderId}/status?${params.toString()}`)
      return response.data
    } catch (error) {
      throw this.handleError(error)
    }
  }

  async updateAgrovetProduct(productId: number, data: Record<string, any>): Promise<any> {
    try {
      const response = await this.client.put(`/api/agrovet/products/${productId}`, data)
      return response.data
    } catch (error) {
      throw this.handleError(error)
    }
  }

  async deleteAgrovetProduct(productId: number): Promise<any> {
    try {
      const response = await this.client.delete(`/api/agrovet/products/${productId}`)
      return response.data
    } catch (error) {
      throw this.handleError(error)
    }
  }

  async getTreatmentPlan(condition: string, params: Record<string, any> = {}): Promise<any> {
    try {
      const response = await this.client.get(`/api/agrovet/treatment-plan/${condition}`, { params })
      return response.data
    } catch (error) {
      throw this.handleError(error)
    }
  }

  async searchNearbyAgrovets(county: string, params: Record<string, any> = {}): Promise<any> {
    try {
      const response = await this.client.get('/api/agrovet/search-nearby', { params: { county, ...params } })
      return response.data
    } catch (error) {
      throw this.handleError(error)
    }
  }

  // ============================================
  // Marketplace Endpoints
  // ============================================

  async getMarketplaceListings(params: { category?: string; county?: string; status?: string } = {}): Promise<any> {
    try {
      const response = await this.client.get('/api/marketplace/listings', { params })
      return response.data
    } catch (error) {
      throw this.handleError(error)
    }
  }

  async getMarketplaceListing(listingId: number): Promise<any> {
    try {
      const response = await this.client.get(`/api/marketplace/listings/${listingId}`)
      return response.data
    } catch (error) {
      throw this.handleError(error)
    }
  }

  async createMarketplaceListing(data: Record<string, any>): Promise<any> {
    try {
      const response = await this.client.post('/api/marketplace/listings', data)
      return response.data
    } catch (error) {
      throw this.handleError(error)
    }
  }

  async createMarketplaceBid(data: {
    listing_id: number; buyer_id: number; quantity: number;
    price_per_unit_kes: number; message?: string; payment_method?: string;
  }): Promise<any> {
    try {
      const response = await this.client.post('/api/marketplace/bids', data)
      return response.data
    } catch (error) {
      throw this.handleError(error)
    }
  }

  async getFarmerListings(farmerId: number): Promise<any> {
    try {
      const response = await this.client.get(`/api/marketplace/farmer/${farmerId}`)
      return response.data
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

  async triggerGranularFetch(scope: string, countyId?: string, region?: string, subCountyId?: string): Promise<any> {
    try {
      const params: Record<string, string> = { scope }
      if (countyId) params.county_id = countyId
      if (region) params.region = region
      if (subCountyId) params.sub_county_id = subCountyId
      const response = await this.client.post('/api/admin/trigger-granular-fetch', null, { params })
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

  // ============================================
  // Admin User Management
  // ============================================

  async adminGetUsers(userType?: string): Promise<Farmer[]> {
    try {
      const params = userType ? { user_type: userType } : {}
      const response = await this.client.get<ApiResponse<Farmer[]>>('/api/admin/users', { params })
      return response.data.data || []
    } catch (error) {
      throw this.handleError(error)
    }
  }

  async adminGetAgrovets(): Promise<AgrovetProfile[]> {
    try {
      const response = await this.client.get<ApiResponse<AgrovetProfile[]>>('/api/admin/agrovets')
      return response.data.data || []
    } catch (error) {
      throw this.handleError(error)
    }
  }

  async adminGetBuyers(): Promise<BuyerProfile[]> {
    try {
      const response = await this.client.get<ApiResponse<BuyerProfile[]>>('/api/admin/buyers')
      return response.data.data || []
    } catch (error) {
      throw this.handleError(error)
    }
  }

  async adminVerifyUser(userId: number): Promise<ApiResponse> {
    try {
      const response = await this.client.put<ApiResponse>(`/api/admin/users/${userId}/verify`)
      return response.data
    } catch (error) {
      throw this.handleError(error)
    }
  }

  async adminGetTransactions(limit = 50): Promise<Transaction[]> {
    try {
      const response = await this.client.get<ApiResponse<Transaction[]>>('/api/admin/transactions', {
        params: { limit },
      })
      return response.data.data || []
    } catch (error) {
      throw this.handleError(error)
    }
  }

  // ============================================
  // Weather Forecast Endpoints
  // ============================================

  async getWeatherForecast(lat: number, lon: number, days = 10): Promise<any> {
    try {
      const response = await this.client.get('/api/weather/forecast/daily', {
        params: { lat, lon, days },
      })
      return response.data
    } catch (error) {
      console.error('Weather forecast error:', error)
      return null
    }
  }

  async getCurrentWeather(lat: number, lon: number): Promise<any> {
    try {
      const response = await this.client.get('/api/weather/current', {
        params: { lat, lon },
      })
      return response.data
    } catch (error) {
      console.error('Current weather error:', error)
      return null
    }
  }

  async getSubCountyWeather(countyId: string, subCountyId: string): Promise<any> {
    try {
      const response = await this.client.get(`/api/weather/sub-county/${countyId}/${subCountyId}`)
      return response.data
    } catch (error) {
      console.error('Sub-county weather error:', error)
      return null
    }
  }

  async getCountyWeather(countyId: string): Promise<any> {
    try {
      const response = await this.client.get(`/api/weather/county/${countyId}`)
      return response.data
    } catch (error) {
      console.error('County weather error:', error)
      return null
    }
  }

  async getAgriculturalInsights(lat: number, lon: number, crop?: string): Promise<any> {
    try {
      const params: any = { lat, lon }
      if (crop) params.crop = crop
      const response = await this.client.get('/api/weather/agricultural-insights', { params })
      return response.data
    } catch (error) {
      console.error('Agricultural insights error:', error)
      return null
    }
  }

  async getSubCountyData(countyId: string, subCountyId: string): Promise<any> {
    try {
      const response = await this.client.get(`/api/counties/${countyId}/sub-counties/${subCountyId}`)
      return response.data?.data || response.data
    } catch (error) {
      console.error('Sub-county data error:', error)
      return null
    }
  }
}

// Export singleton instance
export const api = new ApiClient()

// Export types for convenience
export type { ApiResponse }

