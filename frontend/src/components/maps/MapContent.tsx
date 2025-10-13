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
  const getMarkerColor = (bloomProbabilityStr: string, temperatureStr: string) => {
    // Parse values from strings
    const bloomProbability = parseFloat(bloomProbabilityStr) / 100 || 0
    const temperature = parseFloat(temperatureStr) || 0
    
    // Red for high bloom probability or high temp
    if (bloomProbability > 0.7 || temperature > 35) return '#DC2626'
    // Yellow for medium
    if (bloomProbability > 0.4 || temperature > 30) return '#F59E0B'
    // Green for low/good conditions
    return '#16A34A'
  }

  const getMarkerSize = (marker: CountyMarker) => {
    // Default size for now (bloom_area_km2 not in API response)
    return 10
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
            fillColor={getMarkerColor(marker.bloom_probability, marker.temperature)}
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
