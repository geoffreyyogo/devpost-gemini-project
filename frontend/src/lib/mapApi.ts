/**
 * Map & Climate Data API Client
 * Fetches live Kenya climate and bloom data from FastAPI server
 */

import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Create axios instance with same config as main API client
const mapClient = axios.create({
  baseURL: API_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

export interface CountyMarker {
  name: string
  lat: number
  lon: number
  bloom_probability: string  // "26%" format
  temperature: string  // "23.8°C" format
  rainfall: string  // "0.0mm" format
  ndvi: string  // "0.143" format
  confidence: string
  is_real_data: boolean
  data_source: string
  // New fields for enhanced display
  bloom_area_km2?: number
  bloom_percentage?: number
  bloom_prediction?: number
  message?: string
}

export interface MapData {
  markers: CountyMarker[]
  center_lat: number
  center_lon: number
  zoom: number
  last_updated: string
}

export interface ClimateStats {
  avg_bloom_level: string
  bloom_level_delta: string
  avg_temperature: string
  temperature_delta: string
  avg_rainfall: string
  rainfall_delta: string
  total_bloom_area: string
}

export interface DataFreshness {
  is_fresh: boolean
  last_updated: string
  age_str: string
  age_hours: number
}

/**
 * Get live map data for all Kenya counties
 */
export async function getLiveMapData(): Promise<MapData> {
  try {
    console.log('Fetching map data from:', `${API_URL}/api/map/live-data`)
    console.log('API_URL:', API_URL)
    console.log('mapClient baseURL:', mapClient.defaults.baseURL)
    const response = await mapClient.get('/api/map/live-data')
    console.log('Map data response:', response.data)
    return response.data.data
  } catch (error) {
    console.error('Failed to fetch live map data:', error)
    console.error('Error details:', {
      message: error.message,
      code: error.code,
      response: error.response?.data,
      status: error.response?.status,
      statusText: error.response?.statusText
    })
    throw error
  }
}

/**
 * Get climate summary statistics
 */
export async function getClimateStats(): Promise<ClimateStats> {
  try {
    console.log('Fetching climate stats from:', `${API_URL}/api/map/climate-stats`)
    const response = await mapClient.get('/api/map/climate-stats')
    console.log('Climate stats response:', response.data)
    return response.data.data
  } catch (error) {
    console.error('Failed to fetch climate stats:', error)
    console.error('Error details:', {
      message: error.message,
      code: error.code,
      response: error.response?.data,
      status: error.response?.status,
      statusText: error.response?.statusText
    })
    throw error
  }
}

/**
 * Get data freshness information
 */
export async function getDataFreshness(): Promise<DataFreshness> {
  try {
    console.log('Fetching data freshness from:', `${API_URL}/api/map/freshness`)
    const response = await mapClient.get('/api/map/freshness')
    console.log('Data freshness response:', response.data)
    return response.data.data
  } catch (error) {
    console.error('Failed to fetch data freshness:', error)
    console.error('Error details:', {
      message: error.message,
      code: error.code,
      response: error.response?.data,
      status: error.response?.status,
      statusText: error.response?.statusText
    })
    throw error
  }
}

/**
 * Get detailed data for a specific county
 */
export async function getCountyData(countyId: string): Promise<any> {
  try {
    const response = await mapClient.get(`/api/counties/${countyId}`)
    return response.data.data
  } catch (error) {
    console.error(`Failed to fetch county data for ${countyId}:`, error)
    throw error
  }
}

/**
 * Get all regions and crops configuration
 */
export async function getRegionsAndCrops(): Promise<{
  regions: Record<string, any>
  crops: Record<string, any>
}> {
  try {
    const response = await mapClient.get('/api/public/regions')
    return response.data.data
  } catch (error) {
    console.error('Failed to fetch regions and crops:', error)
    throw error
  }
}

