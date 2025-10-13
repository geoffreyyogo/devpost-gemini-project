/**
 * Kenya Climate Map Component
 * Interactive Leaflet map showing live climate and bloom data for all counties
 */

'use client'

import { useEffect, useState } from 'react'
import dynamic from 'next/dynamic'
import { Loader2 } from 'lucide-react'
import type { CountyMarker } from '@/lib/mapApi'
import { getLiveMapData } from '@/lib/mapApi'

// Dynamically import the entire map component to avoid SSR and re-initialization issues
const MapContent = dynamic(
  () => import('./MapContent'),
  { 
    ssr: false,
    loading: () => (
      <div className="flex items-center justify-center h-[500px] bg-gray-100 dark:bg-gray-800 rounded-lg">
        <Loader2 className="h-8 w-8 animate-spin text-green-600" />
      </div>
    )
  }
)

export function KenyaClimateMap() {
  const [markers, setMarkers] = useState<CountyMarker[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function loadMapData() {
      try {
        console.log('Loading map data...')
        const data = await getLiveMapData()
        console.log('Map data loaded:', data)
        console.log('Markers count:', data.markers?.length)
        setMarkers(data.markers || [])
        setLoading(false)
      } catch (err) {
        console.error('Map load error:', err)
        setError('Failed to load map data. Check console for details.')
        setLoading(false)
      }
    }

    loadMapData()
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[500px] bg-gray-100 dark:bg-gray-800 rounded-lg">
        <Loader2 className="h-8 w-8 animate-spin text-green-600" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-[500px] bg-gray-100 dark:bg-gray-800 rounded-lg">
        <p className="text-red-600">{error}</p>
      </div>
    )
  }

  return <MapContent markers={markers} />
}
