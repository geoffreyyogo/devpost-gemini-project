/**
 * Map Content Component - Separated to avoid re-initialization issues
 */

'use client'

import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet'
import type { CountyMarker } from '@/lib/mapApi'
import { Sprout, Thermometer, Droplets, TrendingUp, MapPin, AlertCircle, CheckCircle2, Activity } from 'lucide-react'
import 'leaflet/dist/leaflet.css'

interface MapContentProps {
  markers: CountyMarker[]
}

export default function MapContent({ markers }: MapContentProps) {
  /**
   * Determine marker color based on bloom risk assessment
   * 
   * Color coding:
   * - Green (#16A34A): Low risk - favorable conditions, low bloom probability
   * - Yellow (#F59E0B): Medium risk - moderate bloom probability or stress indicators
   * - Red (#DC2626): High risk - high bloom probability, extreme temperatures, or drought
   * 
   * Factors considered:
   * - Bloom probability (primary factor)
   * - NDVI (vegetation health - low NDVI in agricultural areas = stress)
   * - Temperature extremes (>35°C indicates arid/stress conditions)
   */
  const getMarkerColor = (marker: CountyMarker) => {
    // Parse bloom probability from string "52%" -> 52
    const bloomProbability = parseFloat(marker.bloom_probability) || 0
    const temperature = parseFloat(marker.temperature) || 25
    const ndvi = parseFloat(marker.ndvi) || 0.4
    
    // Calculate risk score (0-100)
    let riskScore = 0
    
    // Bloom probability is the main factor (0-60 points)
    // Higher bloom probability = higher risk for bloom events
    if (bloomProbability > 70) {
      riskScore += 60
    } else if (bloomProbability > 50) {
      riskScore += 40
    } else if (bloomProbability > 30) {
      riskScore += 20
    } else {
      riskScore += 10
    }
    
    // Temperature stress factor (0-25 points)
    // Extreme temperatures indicate harsh conditions
    if (temperature > 35) {
      riskScore += 25  // Very hot - arid regions
    } else if (temperature > 32) {
      riskScore += 15
    } else if (temperature < 15) {
      riskScore += 10  // Cold stress
    }
    
    // Vegetation stress factor based on NDVI (0-15 points)
    // Low NDVI in agricultural context indicates poor conditions
    if (ndvi < 0.2) {
      riskScore += 15  // Sparse vegetation - likely arid
    } else if (ndvi < 0.3) {
      riskScore += 10  // Low vegetation
    } else if (ndvi > 0.6) {
      riskScore -= 5   // Healthy vegetation - reduce risk
    }
    
    // Determine color based on risk score
    if (riskScore >= 60) {
      return '#DC2626'  // Red - High risk
    } else if (riskScore >= 35) {
      return '#F59E0B'  // Yellow/Orange - Medium risk
    } else {
      return '#16A34A'  // Green - Low risk
    }
  }

  const getMarkerSize = (marker: CountyMarker) => {
    // Size based on bloom area if available, otherwise default
    const bloomArea = marker.bloom_area_km2 || 0
    if (bloomArea > 100) return 14
    if (bloomArea > 50) return 12
    if (bloomArea > 10) return 10
    return 8
  }

  return (
    <div className="h-[500px] w-full rounded-lg overflow-hidden shadow-lg border border-gray-200 dark:border-gray-700">
      <MapContainer
        center={[-0.0236, 37.9062]} // Center of Kenya
        zoom={6}
        style={{ height: '100%', width: '100%' }}
        scrollWheelZoom={false}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        
        {markers.map((marker, index) => (
          <CircleMarker
            key={marker.name + index}
            center={[marker.lat, marker.lon]}
            radius={getMarkerSize(marker)}
            fillColor={getMarkerColor(marker)}
            color="#ffffff"
            weight={2}
            opacity={0.9}
            fillOpacity={0.7}
          >
            <Popup>
              <div className="p-0 min-w-[280px] max-w-[320px]">
                {/* Header */}
                <div className="bg-gradient-to-r from-green-600 to-green-500 px-4 py-3 rounded-t-lg">
                  <div className="flex items-center gap-2 text-white">
                    <MapPin className="h-5 w-5" />
                    <h3 className="font-bold text-lg">
                      {marker.name}
                    </h3>
                  </div>
                  <p className="text-xs text-green-50 mt-1 flex items-center gap-1">
                    {marker.is_real_data ? (
                      <>
                        <CheckCircle2 className="h-3 w-3" />
                        NASA Satellite Data
                      </>
                    ) : (
                      <>
                        <AlertCircle className="h-3 w-3" />
                        Demo Data
                      </>
                    )}
                  </p>
                </div>

                {/* Content */}
                <div className="p-4 bg-white dark:bg-gray-900">
                  {/* Bloom Probability - Most Important */}
                  <div className="mb-4 p-3 bg-gradient-to-br from-green-50 to-green-100 dark:from-green-950 dark:to-green-900 rounded-lg border border-green-200 dark:border-green-800">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <Sprout className="h-5 w-5 text-green-600 dark:text-green-400" />
                        <span className="text-sm font-semibold text-gray-700 dark:text-gray-300">Bloom Forecast</span>
                      </div>
                      <span className="text-2xl font-bold text-green-700 dark:text-green-400">
                        {marker.bloom_probability}
                      </span>
                    </div>
                    {marker.message && marker.message !== 'N/A' && (
                      <p className="text-xs text-gray-600 dark:text-gray-400 italic">
                        {marker.message}
                      </p>
                    )}
                    {marker.confidence && (
                      <div className="flex items-center gap-1 mt-2">
                        <Activity className="h-3 w-3 text-gray-500" />
                        <span className="text-xs text-gray-500 dark:text-gray-400">
                          Confidence: <span className="font-medium">{marker.confidence}</span>
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Environmental Metrics */}
                  <div className="space-y-2.5">
                    {/* Current Bloom Level - Right after forecast */}
                    <div className="flex items-center justify-between py-2 border-b border-gray-100 dark:border-gray-800">
                      <div className="flex items-center gap-2">
                        <Sprout className="h-4 w-4 text-purple-500" />
                        <span className="text-sm text-gray-600 dark:text-gray-400">Current Bloom Level</span>
                      </div>
                      <span className="font-semibold text-gray-900 dark:text-gray-100">
                        {marker.bloom_percentage !== undefined ? `${marker.bloom_percentage.toFixed(1)}%` : '0.0%'}
                      </span>
                    </div>

                    {/* Temperature */}
                    <div className="flex items-center justify-between py-2 border-b border-gray-100 dark:border-gray-800">
                      <div className="flex items-center gap-2">
                        <Thermometer className="h-4 w-4 text-orange-500" />
                        <span className="text-sm text-gray-600 dark:text-gray-400">Temperature</span>
                      </div>
                      <span className="font-semibold text-gray-900 dark:text-gray-100">{marker.temperature}</span>
                    </div>

                    {/* NDVI */}
                    <div className="flex items-center justify-between py-2 border-b border-gray-100 dark:border-gray-800">
                      <div className="flex items-center gap-2">
                        <TrendingUp className="h-4 w-4 text-green-600" />
                        <span className="text-sm text-gray-600 dark:text-gray-400">Vegetation Index</span>
                      </div>
                      <span className="font-semibold text-gray-900 dark:text-gray-100">{marker.ndvi}</span>
                    </div>

                    {/* Rainfall */}
                    <div className="flex items-center justify-between py-2">
                      <div className="flex items-center gap-2">
                        <Droplets className="h-4 w-4 text-blue-500" />
                        <span className="text-sm text-gray-600 dark:text-gray-400">Rainfall</span>
                      </div>
                      <span className="font-semibold text-gray-900 dark:text-gray-100">{marker.rainfall}</span>
                    </div>
                  </div>

                  {/* Footer - Data Source */}
                  <div className="mt-4 pt-3 border-t border-gray-200 dark:border-gray-700">
                    <p className="text-xs text-center text-gray-500 dark:text-gray-400">
                      📡 {marker.data_source} • {marker.confidence} Confidence
                    </p>
                  </div>
                </div>
              </div>
            </Popup>
          </CircleMarker>
        ))}
      </MapContainer>
    </div>
  )
}