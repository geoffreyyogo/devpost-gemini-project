/**
 * County / Sub-County Focused Map Component
 * Shows farmer's exact sub-county with satellite data overlay.
 * Falls back to county-level view when sub-county is not provided.
 */

'use client'

import { useEffect, useState } from 'react'
import dynamic from 'next/dynamic'
import { Loader2, MapPin, Sprout, Thermometer, CloudRain, Droplets, Activity, Flower2, Wind, Gauge } from 'lucide-react'

// Dynamic import to avoid SSR issues with Leaflet
const MapContainer = dynamic(
  () => import('react-leaflet').then((mod) => mod.MapContainer),
  { ssr: false }
)
const TileLayer = dynamic(
  () => import('react-leaflet').then((mod) => mod.TileLayer),
  { ssr: false }
)
const CircleMarker = dynamic(
  () => import('react-leaflet').then((mod) => mod.CircleMarker),
  { ssr: false }
)
const Popup = dynamic(
  () => import('react-leaflet').then((mod) => mod.Popup),
  { ssr: false }
)
const Marker = dynamic(
  () => import('react-leaflet').then((mod) => mod.Marker),
  { ssr: false }
)

import { getLiveMapData } from '@/lib/mapApi'
import type { CountyMarker } from '@/lib/mapApi'

interface CountyFocusedMapProps {
  countyName: string
  subCounty?: string
  farmLat?: number
  farmLon?: number
}

// Kenya county coordinates (approximate centers)
const COUNTY_COORDS: Record<string, [number, number]> = {
  'Nairobi': [-1.286389, 36.817223],
  'Mombasa': [-4.0435, 39.6682],
  'Kisumu': [-0.0917, 34.7680],
  'Nakuru': [-0.3031, 36.0800],
  'Eldoret': [0.5143, 35.2698],
  'Kiambu': [-1.1714, 36.8356],
  'Machakos': [-1.5177, 37.2634],
  'Meru': [0.0469, 37.6556],
  'Nyeri': [-0.4197, 36.9471],
  'Kakamega': [0.2827, 34.7519],
  'Kisii': [-0.6774, 34.7799],
  'Kitui': [-1.3669, 38.0106],
  'Garissa': [-0.4569, 39.6401],
  'Kilifi': [-3.6307, 39.8494],
  'Kwale': [-4.1733, 39.4520],
  'Lamu': [-2.2717, 40.9020],
  'Bungoma': [0.5635, 34.5608],
  'Busia': [0.4604, 34.1115],
  'Vihiga': [0.0765, 34.7228],
  'Bomet': [-0.7806, 35.3086],
  'Kericho': [-0.3676, 35.2839],
  'Kajiado': [-2.0982, 36.7820],
  'Makueni': [-2.2667, 37.8333],
  'Nyandarua': [-0.1805, 36.4667],
  'Embu': [-0.5392, 37.4577],
  'Tharaka-Nithi': [-0.3667, 37.7333],
  'Murang\'a': [-0.7833, 37.1333],
  'Kirinyaga': [-0.6589, 37.3822],
  'Laikipia': [0.3667, 36.7833],
  'Trans Nzoia': [1.0500, 34.9500],
  'Uasin Gishu': [0.5500, 35.3000],
  'Elgeyo-Marakwet': [0.8833, 35.4500],
  'Nandi': [0.1833, 35.1167],
  'Baringo': [0.4667, 36.0833],
  'West Pokot': [1.6167, 35.1167],
  'Samburu': [1.2167, 37.0333],
  'Turkana': [3.1167, 35.5667],
  'Marsabit': [2.3333, 37.9833],
  'Isiolo': [0.3556, 38.4889],
  'Wajir': [1.7500, 40.0667],
  'Mandera': [3.9366, 41.8667],
  'Taita-Taveta': [-3.3167, 38.4833],
  'Homa Bay': [-0.5167, 34.4500],
  'Migori': [-1.0634, 34.4731],
  'Siaya': [0.0622, 34.2883],
  'Nyamira': [-0.5667, 34.9333],
}

export function CountyFocusedMap({ countyName, subCounty, farmLat, farmLon }: CountyFocusedMapProps) {
  const [markers, setMarkers] = useState<CountyMarker[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function loadMapData() {
      try {
        console.log('Loading map data for:', subCounty || countyName)
        const data = await getLiveMapData()
        
        // Find the specific county marker
        const countyMarker = data.markers.find(
          (m: CountyMarker) => m.name.toLowerCase() === countyName.toLowerCase()
        )
        
        if (countyMarker) {
          setMarkers([countyMarker])
        } else {
          console.log('County not found in API, showing all markers')
          setMarkers(data.markers || [])
        }
        
        setLoading(false)
      } catch (err) {
        console.error('County map error:', err)
        setError('Unable to load map data')
        setLoading(false)
      }
    }

    loadMapData()
  }, [countyName, subCounty])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[400px] bg-gray-100 dark:bg-gray-800 rounded-lg">
        <Loader2 className="h-8 w-8 animate-spin text-green-600" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-[400px] bg-gray-100 dark:bg-gray-800 rounded-lg p-6">
        <MapPin className="h-12 w-12 text-gray-400 mb-4" />
        <p className="text-gray-500 text-center">{error}</p>
        <p className="text-xs text-gray-400 mt-2 text-center">
          The map is temporarily unavailable
        </p>
      </div>
    )
  }

  // Determine map center: prefer farm coords > county fallback > Kenya center
  const hasFarmCoords = farmLat && farmLon && farmLat !== 0 && farmLon !== 0
  const center: [number, number] = hasFarmCoords
    ? [farmLat!, farmLon!]
    : COUNTY_COORDS[countyName] || [-0.0236, 37.9062]
  // Zoom to sub-county level when we have precise coordinates, else county level
  const zoom = hasFarmCoords ? 12 : 9

  const getMarkerColor = (bloomProbabilityStr: string, temperatureStr: string) => {
    // Support both numeric percentages (e.g. 52.3) and strings like "52%"
    const bpRaw = typeof bloomProbabilityStr === 'number' ? bloomProbabilityStr : parseFloat(String(bloomProbabilityStr))
    const bloomProbability = Number.isFinite(bpRaw) ? bpRaw : 0
    const temperature = parseFloat(String(temperatureStr)) || 0

    // Create a simple risk score similar to the main map logic
    let riskScore = 0

    // Bloom probability (0-60)
    if (bloomProbability > 70) {
      riskScore += 60
    } else if (bloomProbability > 50) {
      riskScore += 40
    } else if (bloomProbability > 30) {
      riskScore += 20
    } else {
      riskScore += 10
    }

    // Temperature stress (0-25)
    if (temperature > 35) {
      riskScore += 25
    } else if (temperature > 32) {
      riskScore += 15
    } else if (temperature < 15) {
      riskScore += 10
    }

    if (riskScore >= 60) return '#DC2626'
    if (riskScore >= 35) return '#F59E0B'
    return '#16A34A'
  }

  const getMarkerSize = (marker: CountyMarker) => {
    // Size based on bloom area if available, otherwise a larger default for focused map
    const bloomArea = marker.bloom_area_km2 || 0
    if (bloomArea > 100) return 20
    if (bloomArea > 50) return 18
    return 15
  }

  return (
    <div className="h-[400px] w-full rounded-lg overflow-hidden shadow-lg border border-gray-200 dark:border-gray-700">
      <MapContainer
        center={center}
        zoom={zoom}
        style={{ height: '100%', width: '100%' }}
        scrollWheelZoom={false}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        
        {markers.map((marker, index) => {
          const isMainCounty = marker.name.toLowerCase() === countyName.toLowerCase()
          
          return (
            <CircleMarker
              key={marker.name + index}
              center={[marker.lat, marker.lon]}
              radius={isMainCounty ? 20 : 12}
              fillColor={getMarkerColor(marker.bloom_probability, marker.temperature)}
              color={isMainCounty ? "#1e40af" : "#ffffff"}
              weight={isMainCounty ? 4 : 2}
              opacity={1}
              fillOpacity={isMainCounty ? 0.9 : 0.6}
            >
              <Popup maxWidth={350} className="custom-popup">
                <div className="min-w-[280px]">
                  {/* Header */}
                  <div className="bg-gradient-to-r from-green-600 to-green-700 dark:from-green-700 dark:to-green-800 px-4 py-4 -m-3 mb-3 rounded-t-lg">
                    <h3 className="font-bold text-white text-lg flex items-center gap-2 mb-1.5">
                      <MapPin className="h-5 w-5" />
                      {isMainCounty && subCounty ? `${subCounty}, ${marker.name}` : marker.name}
                      {isMainCounty && <span className="ml-auto text-xs bg-blue-500 px-2 py-1 rounded">Your Area</span>}
                    </h3>
                    <p className="text-xs text-green-100">
                      {isMainCounty && subCounty ? 'Sub-County Satellite Data' : 'NASA Satellite Data'}
                    </p>
                  </div>

                  <div className="p-4 bg-white dark:bg-gray-900">
                    {/* Bloom Forecast - Most Important */}
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
                      {/* Current Bloom Level - Always show */}
                      <div className="flex items-center justify-between p-2 bg-pink-50 dark:bg-pink-950/30 rounded-lg border border-pink-200 dark:border-pink-800">
                        <div className="flex items-center gap-2">
                          <Flower2 className="h-4 w-4 text-pink-600 dark:text-pink-400" />
                          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Current Bloom Level</span>
                        </div>
                        <span className="text-sm font-bold text-pink-700 dark:text-pink-400">
                          {marker.bloom_percentage !== undefined && typeof marker.bloom_percentage === 'number' 
                            ? `${marker.bloom_percentage.toFixed(1)}%`
                            : marker.bloom_percentage || '0.0%'}
                        </span>
                      </div>

                      {/* Temperature */}
                      <div className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
                        <div className="flex items-center gap-2">
                          <Thermometer className="h-4 w-4 text-orange-600 dark:text-orange-400" />
                          <span className="text-sm text-gray-700 dark:text-gray-300">Temperature</span>
                        </div>
                        <span className="text-sm font-semibold text-gray-900 dark:text-white">{marker.temperature}</span>
                      </div>

                      {/* Vegetation Index (NDVI) */}
                      <div className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
                        <div className="flex items-center gap-2">
                          <Sprout className="h-4 w-4 text-green-600 dark:text-green-400" />
                          <span className="text-sm text-gray-700 dark:text-gray-300">Vegetation Index</span>
                        </div>
                        <span className="text-sm font-semibold text-gray-900 dark:text-white">{marker.ndvi}</span>
                      </div>

                      {/* Rainfall */}
                      <div className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
                        <div className="flex items-center gap-2">
                          <CloudRain className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                          <span className="text-sm text-gray-700 dark:text-gray-300">Rainfall</span>
                        </div>
                        <span className="text-sm font-semibold text-gray-900 dark:text-white">{marker.rainfall}</span>
                      </div>
                    </div>

                    {/* Data Source Footer */}
                    <div className="mt-4 pt-3 border-t border-gray-200 dark:border-gray-700 flex items-center justify-between">
                      <span className="text-xs text-gray-500 dark:text-gray-400">
                        {marker.is_real_data ? '✓ Real Satellite Data' : '⚠ Demo Data'}
                      </span>
                      {marker.data_source && (
                        <span className="text-xs text-gray-400 dark:text-gray-500">
                          {marker.data_source}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </Popup>
            </CircleMarker>
          )
        })}

        {/* Farm location pin */}
        {hasFarmCoords && (
          <CircleMarker
            center={[farmLat!, farmLon!]}
            radius={8}
            fillColor="#3b82f6"
            color="#1e3a8a"
            weight={3}
            opacity={1}
            fillOpacity={1}
          >
            <Popup>
              <div className="text-center p-2">
                <p className="font-bold text-sm flex items-center gap-1 justify-center">
                  <MapPin className="h-4 w-4 text-blue-600" /> Your Farm
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  {subCounty ? `${subCounty}, ${countyName}` : countyName}
                </p>
                <p className="text-xs text-gray-400 mt-0.5">
                  {farmLat!.toFixed(4)}°, {farmLon!.toFixed(4)}°
                </p>
              </div>
            </Popup>
          </CircleMarker>
        )}
      </MapContainer>
    </div>
  )
}