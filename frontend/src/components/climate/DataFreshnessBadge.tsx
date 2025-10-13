/**
 * Data Freshness Indicator Badge
 * Shows when satellite data was last updated
 */

'use client'

import { useEffect, useState } from 'react'
import { getDataFreshness, type DataFreshness } from '@/lib/mapApi'
import { CheckCircle, AlertTriangle, Info, RefreshCw } from 'lucide-react'

export function DataFreshnessBadge() {
  const [freshness, setFreshness] = useState<DataFreshness | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function loadFreshness() {
      try {
        const data = await getDataFreshness()
        setFreshness(data)
        setLoading(false)
      } catch (error) {
        console.error('Failed to load freshness data:', error)
        setLoading(false)
      }
    }

    loadFreshness()
  }, [])

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-gray-500">
        <RefreshCw className="h-4 w-4 animate-spin" />
        <span className="text-sm">Checking data freshness...</span>
      </div>
    )
  }

  if (!freshness) {
    return (
      <div className="flex items-center gap-2 px-4 py-2 bg-gray-100 dark:bg-gray-800 rounded-lg">
        <Info className="h-5 w-5 text-gray-500" />
        <span className="text-sm text-gray-700 dark:text-gray-300">
          Data status unavailable
        </span>
      </div>
    )
  }

  if (freshness.is_fresh) {
    return (
      <div className="flex items-center gap-2 px-4 py-2 bg-green-50 dark:bg-green-950 rounded-lg border border-green-200 dark:border-green-800">
        <CheckCircle className="h-5 w-5 text-green-600" />
        <span className="text-sm font-medium text-green-700 dark:text-green-400">
          ✓ Live NASA satellite data | Last updated: {freshness.age_str}
        </span>
      </div>
    )
  } else if (freshness.last_updated !== 'Never') {
    return (
      <div className="flex items-center gap-2 px-4 py-2 bg-yellow-50 dark:bg-yellow-950 rounded-lg border border-yellow-200 dark:border-yellow-800">
        <AlertTriangle className="h-5 w-5 text-yellow-600" />
        <span className="text-sm font-medium text-yellow-700 dark:text-yellow-400">
          ⚠ Data is {freshness.age_str} old | Consider refreshing
        </span>
      </div>
    )
  } else {
    return (
      <div className="flex items-center gap-2 px-4 py-2 bg-blue-50 dark:bg-blue-950 rounded-lg border border-blue-200 dark:border-blue-800">
        <Info className="h-5 w-5 text-blue-600" />
        <span className="text-sm font-medium text-blue-700 dark:text-blue-400">
          ℹ Using demo data | Run data fetcher to get real satellite data
        </span>
      </div>
    )
  }
}


