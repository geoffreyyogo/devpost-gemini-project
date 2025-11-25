/**
 * Climate Statistics Cards Component
 * Displays real-time climate metrics from satellite data
 */

'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { getClimateStats, type ClimateStats } from '@/lib/mapApi'
import { Flower, Thermometer, CloudRain, MapPin, TrendingUp, TrendingDown } from 'lucide-react'

export function ClimateStatsCards() {
  const [stats, setStats] = useState<ClimateStats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function loadStats() {
      try {
        console.log('Loading climate stats...')
        const data = await getClimateStats()
        console.log('Climate stats loaded:', data)
        setStats(data)
        setLoading(false)
      } catch (error) {
        console.error('Failed to load climate stats:', error)
        setLoading(false)
      }
    }

    loadStats()
  }, [])

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[1, 2, 3, 4].map((i) => (
          <Card key={i} className="animate-pulse">
            <CardContent className="p-6">
              <div className="h-24 bg-gray-200 dark:bg-gray-700 rounded"></div>
            </CardContent>
          </Card>
        ))}
      </div>
    )
  }

  const StatCard = ({ 
    icon: Icon, 
    label, 
    value, 
    delta, 
    color 
  }: { 
    icon: any
    label: string
    value: string
    delta?: string
    color: string
  }) => {
    const isPositive = delta && delta.includes('+')
    const isNegative = delta && delta.includes('-')
    
    return (
      <Card className="relative overflow-hidden hover:shadow-2xl transition-all duration-500 hover:-translate-y-2 border border-gray-200 dark:border-gray-800 group rounded-2xl">
        {/* Gradient Background */}
        <div 
          className="absolute inset-0 opacity-5 group-hover:opacity-10 transition-opacity duration-500"
          style={{
            background: `linear-gradient(135deg, ${color} 0%, ${color}88 100%)`
          }}
        />
        
        {/* Animated Border on Hover - All sides */}
        <div 
          className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-all duration-500 rounded-2xl pointer-events-none"
          style={{ 
            border: `2.5px solid ${color}`,
            boxShadow: `0 0 20px ${color}40, inset 0 0 0 1px ${color}20`
          }}
        />
        
        <CardContent className="p-6 relative z-10">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-3">
                <div 
                  className="p-3 rounded-xl shadow-md group-hover:scale-110 transition-transform duration-300" 
                  style={{ 
                    backgroundColor: `${color}20`,
                    border: `2px solid ${color}40`
                  }}
                >
                  <Icon className="h-6 w-6" style={{ color }} />
                </div>
                <p className="text-sm font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wide">
                  {label}
                </p>
              </div>
              <p className="text-4xl font-bold text-gray-900 dark:text-white mb-2 group-hover:scale-105 transition-transform">
                {value}
              </p>
              {delta && (
                <div className="flex items-center gap-1.5 mt-3 p-2 rounded-lg bg-gray-50 dark:bg-gray-800/50">
                  {isPositive && <TrendingUp className="h-4 w-4 text-green-600" />}
                  {isNegative && <TrendingDown className="h-4 w-4 text-red-600" />}
                  <span className={`text-sm font-bold ${isPositive ? 'text-green-600' : isNegative ? 'text-red-600' : 'text-gray-600'}`}>
                    {delta}
                  </span>
                  <span className="text-xs text-gray-500 ml-1">vs last period</span>
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <StatCard
        icon={Flower}
        label="🌸 Avg Bloom Level"
        value={stats?.avg_bloom_level || 'N/A'}
        delta={stats?.bloom_level_delta}
        color="#EC4899"
      />
      <StatCard
        icon={Thermometer}
        label="🌡️ Avg Temperature"
        value={stats?.avg_temperature || 'N/A'}
        delta={stats?.temperature_delta}
        color="#F59E0B"
      />
      <StatCard
        icon={CloudRain}
        label="🌧️ Avg Rainfall"
        value={stats?.avg_rainfall || 'N/A'}
        delta={stats?.rainfall_delta}
        color="#3B82F6"
      />
      <StatCard
        icon={MapPin}
        label="📍 Total Bloom Area"
        value={stats?.total_bloom_area || 'N/A'}
        color="#16A34A"
      />
    </div>
  )
}
