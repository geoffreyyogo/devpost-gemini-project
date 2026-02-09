'use client'

import { useEffect, useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import Image from 'next/image'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { 
  Loader2, Sprout, TrendingUp, Cloud, Bell, User, LogOut, 
  Calendar, MapPin, Thermometer, Droplets, BarChart3, AlertTriangle,
  MessageSquare, ChevronRight, Cpu, Wifi, WifiOff, Plus, Leaf,
  Wind, Gauge, Sun, CloudRain, ShieldAlert, Zap, Camera, Activity,
  Menu, X as XIcon, Store, ShoppingBag,
} from 'lucide-react'
import { useAuthStore, getDashboardRoute } from '@/store/authStore'
import { useDashboardStore } from '@/store/dashboardStore'
import { CountyFocusedMap } from '@/components/maps/CountyFocusedMap'
import { ThemeSwitcher } from '@/components/ui/theme-switcher'
import { LanguageSelector } from '@/components/ui/language-selector'
import { api } from '@/lib/api'
import { ChatPage } from '@/components/chat/ChatPage'
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import type { Farm, FarmOverview } from '@/types'

export default function DashboardPage() {
  const router = useRouter()
  const { farmer, isAuthenticated, logout, hasHydrated } = useAuthStore()
  const { data: dashboardData, isLoading: loading, error, fetchDashboardData, fetchBloomEvents, fetchAlerts } = useDashboardStore()
  const [selectedTab, setSelectedTab] = useState(() => {
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search)
      return params.get('tab') || 'overview'
    }
    return 'overview'
  })
  const [sidebarOpen, setSidebarOpen] = useState(false)

  // Multi-farm state
  const [farms, setFarms] = useState<Farm[]>([])
  const [selectedFarmId, setSelectedFarmId] = useState<number | null>(null)
  const [farmOverview, setFarmOverview] = useState<FarmOverview | null>(null)
  const [farmsLoading, setFarmsLoading] = useState(false)

  // Weather state — real data from Google Weather API
  const [weatherForecast, setWeatherForecast] = useState<any>(null)
  const [currentWeather, setCurrentWeather] = useState<any>(null)
  const [agInsights, setAgInsights] = useState<any>(null)
  const [weatherLoading, setWeatherLoading] = useState(false)

  // Check authentication - but wait for hydration first
  useEffect(() => {
    // Wait for store to hydrate from localStorage
    if (!hasHydrated) {
      return
    }
    
    // Now check auth after hydration
    if (!isAuthenticated || !farmer) {
      router.push('/login')
      return
    }
    
    // Fetch dashboard data
    const loadData = async () => {
      await fetchDashboardData()
      await fetchBloomEvents(farmer.region)
      await fetchAlerts()
    }
    loadData()
  }, [isAuthenticated, farmer, router, fetchDashboardData, fetchBloomEvents, fetchAlerts, hasHydrated])

  // Fetch farms
  useEffect(() => {
    if (!hasHydrated || !isAuthenticated || !farmer) return
    const loadFarms = async () => {
      setFarmsLoading(true)
      try {
        const farmsData = await api.getFarms()
        setFarms(farmsData)
        if (farmsData.length > 0 && !selectedFarmId) {
          setSelectedFarmId(farmsData[0].id)
        }
      } catch {
        // Will show empty farms
      } finally {
        setFarmsLoading(false)
      }
    }
    loadFarms()
  }, [isAuthenticated, farmer, hasHydrated])

  // Fetch farm overview when selected farm changes
  useEffect(() => {
    if (!selectedFarmId) return
    const loadOverview = async () => {
      try {
        const overview = await api.getFarmOverview(selectedFarmId)
        setFarmOverview(overview)
      } catch {
        setFarmOverview(null)
      }
    }
    loadOverview()
  }, [selectedFarmId])

  // Fetch real weather data for the farmer's location
  useEffect(() => {
    if (!hasHydrated || !isAuthenticated || !farmer) return
    let cancelled = false
    const loadWeather = async () => {
      setWeatherLoading(true)
      try {
        const lat = farmer.location_lat || 0
        const lon = farmer.location_lon || 0
        let gotForecast = false

        // Try sub-county weather first, then fall back to coord-based
        if (farmer.county && farmer.sub_county) {
          const subWeather = await api.getSubCountyWeather(
            farmer.county.toLowerCase().replace(/[\s-]+/g, '_'),
            farmer.sub_county.toLowerCase().replace(/[\s-]+/g, '_')
          )
          if (!cancelled && subWeather && !subWeather.error) {
            setWeatherForecast(subWeather)
            gotForecast = true
            // Also fetch current conditions for the sub-county coordinates
            const scLat = subWeather.latitude || lat
            const scLon = subWeather.longitude || lon
            if (scLat && scLon) {
              const current = await api.getCurrentWeather(scLat, scLon)
              if (!cancelled && current && !current.error) setCurrentWeather(current)
            }
          }
        }

        // If sub-county didn't work, use coordinates
        if (!gotForecast && lat && lon) {
          const [forecast, current] = await Promise.all([
            api.getWeatherForecast(lat, lon, 10),
            api.getCurrentWeather(lat, lon),
          ])
          if (!cancelled) {
            if (forecast) setWeatherForecast(forecast)
            if (current) setCurrentWeather(current)
          }
        }

        // Fetch agricultural insights
        if (lat && lon) {
          const crop = farmer.crops?.[0] || undefined
          const insights = await api.getAgriculturalInsights(lat, lon, crop)
          if (!cancelled && insights) setAgInsights(insights)
        }
      } catch (err) {
        console.error('Weather fetch error:', err)
      } finally {
        if (!cancelled) setWeatherLoading(false)
      }
    }
    loadWeather()
    return () => { cancelled = true }
  }, [hasHydrated, isAuthenticated, farmer])

  const handleLogout = async () => {
    await logout()
    router.push('/')
  }

  if (!farmer) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-green-50 to-white dark:from-gray-950 dark:to-gray-900">
        <Loader2 className="h-12 w-12 animate-spin text-green-600" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-white to-green-50 dark:from-gray-950 dark:via-gray-900 dark:to-gray-950 flex flex-col">
      {/* Header */}
      <header className="border-b border-white/20 dark:border-gray-800/30 bg-white/70 dark:bg-gray-950/70 backdrop-blur-xl sticky top-0 z-50 shadow-lg shadow-green-500/5 dark:shadow-green-500/10">
        <div className="px-4 py-3">
          <div className="flex items-center justify-between">
            {/* Mobile sidebar toggle + Logo */}
            <div className="flex items-center gap-3">
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="lg:hidden p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
              >
                {sidebarOpen ? <XIcon className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
              </button>
              <Link href="/" className="flex items-center space-x-3 group">
              <Image
                src="/BloomWatch.png"
                alt="Smart Shamba"
                width={40}
                height={40}
                className="h-10 w-auto transition-transform group-hover:scale-105"
                priority
              />
              <span className="text-xl md:text-2xl font-bold bg-gradient-to-r from-green-600 to-green-500 bg-clip-text text-transparent hidden sm:inline">
                Smart Shamba
              </span>
            </Link>
            </div>

            {/* Right Side - minimal on desktop (controls in sidebar) */}
            <div className="flex items-center gap-2">
              {/* User name - visible on larger screens */}
              <div className="text-right hidden lg:block">
                <p className="text-sm font-semibold text-gray-900 dark:text-white">
                  {farmer.name}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400 flex items-center justify-end gap-1">
                  <MapPin className="h-3 w-3" />
                  {farmer.county || farmer.region}
                </p>
              </div>
              {/* Mobile-only theme + logout */}
              <div className="flex items-center gap-1 lg:hidden">
                <ThemeSwitcher />
                <Button 
                  variant="ghost" 
                  size="sm" 
                  onClick={handleLogout}
                  className="rounded-full h-9 px-3 hover:bg-red-50 dark:hover:bg-red-900/20 hover:text-red-600"
                >
                  <LogOut className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="flex flex-1 min-h-0">
        {/* Sidebar */}
        <aside className={`
          fixed lg:sticky top-[65px] left-0 z-40 h-[calc(100vh-65px)]
          w-64 bg-white dark:bg-gray-950 border-r border-gray-200 dark:border-gray-800
          shadow-xl lg:shadow-none
          transition-transform duration-300 ease-in-out
          shrink-0
          ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
          flex flex-col
        `}>
          {/* Sidebar Header - Farmer Info */}
          <div className="p-4 border-b border-gray-200 dark:border-gray-800">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-green-500 to-green-600 flex items-center justify-center text-white font-bold text-sm">
                {farmer.name.charAt(0)}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-gray-900 dark:text-white truncate">{farmer.name}</p>
                <p className="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-1">
                  <MapPin className="h-3 w-3 flex-shrink-0" />
                  <span className="truncate">{farmer.county || farmer.region}</span>
                </p>
              </div>
            </div>
            {/* Farm Selector */}
            {farms.length > 0 && (
              <div className="mt-3">
                <Select value={String(selectedFarmId || '')} onValueChange={v => setSelectedFarmId(parseInt(v))}>
                  <SelectTrigger className="w-full h-8 text-xs">
                    <SelectValue placeholder="Select farm" />
                  </SelectTrigger>
                  <SelectContent>
                    {farms.map(f => (
                      <SelectItem key={f.id} value={String(f.id)}>
                        {f.name || `Farm in ${f.county}`}
                        {f.sensor_count && f.sensor_count > 0 ? ' 📡' : ''}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}
          </div>

          {/* Navigation Items */}
          <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
            {[
              { id: 'overview', label: 'Overview', icon: BarChart3 },
              { id: 'farms', label: 'Farms', icon: Leaf, badge: farms.length > 0 ? farms.length : undefined },
              { id: 'chat', label: 'Chat', icon: MessageSquare },
              { id: 'bloom', label: 'Bloom', icon: Sprout },
              { id: 'weather', label: 'Weather', icon: Cloud },
              { id: 'alerts', label: 'Alerts', icon: Bell },
            ].map(item => (
              <button
                key={item.id}
                onClick={() => { setSelectedTab(item.id); setSidebarOpen(false) }}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 ${
                  selectedTab === item.id
                    ? 'bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-400 shadow-sm border border-green-200 dark:border-green-800'
                    : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-gray-900 dark:hover:text-white'
                }`}
              >
                <item.icon className={`h-5 w-5 flex-shrink-0 ${selectedTab === item.id ? 'text-green-600 dark:text-green-400' : ''}`} />
                <span>{item.label}</span>
                {item.badge && (
                  <Badge variant="secondary" className="ml-auto text-[10px] px-1.5">{item.badge}</Badge>
                )}
                {selectedTab === item.id && (
                  <ChevronRight className="ml-auto h-4 w-4 text-green-500" />
                )}
              </button>
            ))}

            <div className="border-t border-gray-200 dark:border-gray-800 my-3" />

            {/* Quick Links */}
            <Link href="/agrovet" className="block" onClick={() => setSidebarOpen(false)}>
              <div className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-gray-600 dark:text-gray-400 hover:bg-amber-50 dark:hover:bg-amber-950/30 hover:text-amber-700 dark:hover:text-amber-400 transition-all">
                <Store className="h-5 w-5" />
                <span>Agrovet Shop</span>
              </div>
            </Link>
            <Link href="/marketplace" className="block" onClick={() => setSidebarOpen(false)}>
              <div className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-gray-600 dark:text-gray-400 hover:bg-teal-50 dark:hover:bg-teal-950/30 hover:text-teal-700 dark:hover:text-teal-400 transition-all">
                <ShoppingBag className="h-5 w-5" />
                <span>Marketplace</span>
              </div>
            </Link>
          </nav>

          {/* Sidebar Footer */}
          <div className="p-3 border-t border-gray-200 dark:border-gray-800 space-y-2">
            <div className="flex items-center gap-2 px-1">
              <ThemeSwitcher />
              <LanguageSelector />
            </div>
            <div className="flex gap-2">
              <Link href="/profile" className="flex-1">
                <Button variant="outline" size="sm" className="w-full h-8 text-xs rounded-lg">
                  <User className="mr-1.5 h-3.5 w-3.5" />
                  Profile
                </Button>
              </Link>
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={handleLogout}
                className="h-8 px-3 text-xs rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 hover:text-red-600"
              >
                <LogOut className="h-3.5 w-3.5" />
              </Button>
            </div>
          </div>
        </aside>

        {/* Mobile sidebar overlay */}
        {sidebarOpen && (
          <div 
            className="fixed inset-0 bg-black/30 z-30 lg:hidden" 
            onClick={() => setSidebarOpen(false)} 
          />
        )}

        {/* Main Content */}
        <main className="flex-1 overflow-y-auto p-4 md:p-6 lg:p-8">
        {/* Welcome Section */}
        <div className="mb-8">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div>
              <h1 className="text-3xl lg:text-4xl font-bold text-green-700 dark:text-green-400 mb-1">
                Welcome back, {farmer.name.split(' ')[0]}! 👋
              </h1>
              <p className="text-gray-600 dark:text-gray-400 flex items-center gap-2">
                {farmer.display_id && <Badge variant="outline" className="font-mono text-green-600">{farmer.display_id}</Badge>}
                Here&apos;s what&apos;s happening with your crops today
              </p>
            </div>
            {/* Add Farm button - selector is in sidebar */}
            {farms.length > 0 && (
              <Link href="/dashboard/add-farm">
                <Button variant="outline" size="sm" className="h-9 gap-2">
                  <Plus className="h-4 w-4" />
                  Add Farm
                </Button>
              </Link>
            )}
          </div>
        </div>

        {/* Farm IoT Status Bar (if selected farm has IoT) */}
        {farmOverview && selectedFarmId && (
          <Card className="mb-6 bg-gradient-to-r from-cyan-50 to-blue-50 dark:from-cyan-950/30 dark:to-blue-950/30 border-cyan-200 dark:border-cyan-800">
            <CardContent className="py-4">
              <div className="flex items-center gap-6 flex-wrap">
                <div className="flex items-center gap-2">
                  {(farmOverview.farm?.sensor_count ?? 0) > 0 ? (
                    <Wifi className="h-4 w-4 text-green-500" />
                  ) : (
                    <WifiOff className="h-4 w-4 text-gray-400" />
                  )}
                  <span className="text-sm font-medium">
                    {(farmOverview.farm?.sensor_count ?? 0) > 0
                      ? `${farmOverview.farm?.sensor_count} ESP32 sensor(s) active`
                      : 'Satellite-only monitoring'}
                  </span>
                </div>
                <div className="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400">
                  <span><MapPin className="h-3 w-3 inline mr-1" />{farmOverview.farm?.county}{farmOverview.farm?.sub_county ? `, ${farmOverview.farm.sub_county}` : ''}</span>
                  <span>{farmOverview.farm?.size_acres ? `${farmOverview.farm.size_acres} acres` : ''}</span>
                  {farmOverview.farm?.crops && farmOverview.farm.crops.length > 0 && (
                    <span>{farmOverview.farm.crops.join(', ')}</span>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {loading && !dashboardData ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="h-12 w-12 animate-spin text-green-600" />
          </div>
        ) : error ? (
          <Card className="border-red-200 dark:border-red-800">
            <CardContent className="pt-6">
              <div className="flex items-center gap-2 text-red-600">
                <AlertTriangle className="h-5 w-5" />
                <p>Failed to load dashboard data. Please try again.</p>
              </div>
            </CardContent>
          </Card>
        ) : (
          <>
            {/* Content Panels */}
            <div className="space-y-6">

              {/* Overview Tab */}
              {selectedTab === 'overview' && (
              <div className="space-y-6">
            {/* Metrics Cards */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6">
              <Card className="relative overflow-hidden border-0 shadow-md bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-950/60 dark:to-blue-900/40">
                <div className="absolute top-0 right-0 w-16 h-16 bg-blue-200/40 dark:bg-blue-800/20 rounded-bl-[2rem]" />
                <CardHeader className="pb-1">
                  <CardDescription className="flex items-center gap-2 text-blue-600 dark:text-blue-400 font-medium">
                    <Cloud className="h-4 w-4" />
                    Season
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="text-2xl md:text-3xl font-bold text-blue-800 dark:text-blue-200">
                    {dashboardData?.season?.name || 'Loading...'}
                  </p>
                  <p className="text-xs text-blue-600/70 dark:text-blue-400/70 mt-1">
                    {dashboardData?.season?.status || 'Ongoing'}
                  </p>
                </CardContent>
              </Card>

              <Card className="relative overflow-hidden border-0 shadow-md bg-gradient-to-br from-pink-50 to-pink-100 dark:from-pink-950/60 dark:to-pink-900/40">
                <div className="absolute top-0 right-0 w-16 h-16 bg-pink-200/40 dark:bg-pink-800/20 rounded-bl-[2rem]" />
                <CardHeader className="pb-1">
                  <CardDescription className="flex items-center gap-2 text-pink-600 dark:text-pink-400 font-medium">
                    <Sprout className="h-4 w-4" />
                    Blooms
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="text-2xl md:text-3xl font-bold text-pink-700 dark:text-pink-300">
                    {dashboardData?.bloom_events?.length || 0}
                  </p>
                  <p className="text-xs text-pink-600/70 dark:text-pink-400/70 mt-1">
                    {(dashboardData?.bloom_events?.length ?? 0) > 0 ? 'Active events' : 'None detected'}
                  </p>
                </CardContent>
              </Card>

              <Card className="relative overflow-hidden border-0 shadow-md bg-gradient-to-br from-green-50 to-emerald-100 dark:from-green-950/60 dark:to-emerald-900/40">
                <div className="absolute top-0 right-0 w-16 h-16 bg-green-200/40 dark:bg-green-800/20 rounded-bl-[2rem]" />
                <CardHeader className="pb-1">
                  <CardDescription className="flex items-center gap-2 text-green-600 dark:text-green-400 font-medium">
                    <Activity className="h-4 w-4" />
                    Crop Health
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="text-2xl md:text-3xl font-bold text-green-700 dark:text-green-300">
                    {dashboardData?.ndvi_average ? `${(dashboardData.ndvi_average * 100).toFixed(0)}%` : 'N/A'}
                  </p>
                  <p className="text-xs text-green-600/70 dark:text-green-400/70 mt-1">
                    NDVI Index
                  </p>
                </CardContent>
              </Card>

              <Card className="relative overflow-hidden border-0 shadow-md bg-gradient-to-br from-amber-50 to-orange-100 dark:from-amber-950/60 dark:to-orange-900/40">
                <div className="absolute top-0 right-0 w-16 h-16 bg-amber-200/40 dark:bg-amber-800/20 rounded-bl-[2rem]" />
                <CardHeader className="pb-1">
                  <CardDescription className="flex items-center gap-2 text-amber-600 dark:text-amber-400 font-medium">
                    <Bell className="h-4 w-4" />
                    Alerts
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="text-2xl md:text-3xl font-bold text-amber-700 dark:text-amber-300">
                    {dashboardData?.recent_alerts?.length || 0}
                  </p>
                  <p className="text-xs text-amber-600/70 dark:text-amber-400/70 mt-1">
                    {dashboardData?.recent_alerts?.some((a: any) => !a.read) ? 'Unread alerts' : 'All read'}
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* ML Prediction Card - Comprehensive AI Predictions */}
            {dashboardData?.ml_prediction && (
              <Card className="mb-8 border-2 border-purple-200 dark:border-purple-800 bg-gradient-to-br from-white via-purple-50/30 to-pink-50/30 dark:from-gray-900 dark:via-purple-950/30 dark:to-pink-950/30 shadow-lg">
                <CardHeader className="pb-3">
                  <CardTitle className="flex items-center gap-2 text-purple-700 dark:text-purple-300">
                    <Cpu className="h-6 w-6" />
                    🤖 AI-Powered Farm Predictions
                  </CardTitle>
                  <CardDescription>
                    Machine Learning predictions based on satellite imagery, weather patterns, and environmental data
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  {/* Primary: Bloom + Yield Row */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Bloom Probability */}
                    <div className="rounded-xl bg-gradient-to-br from-purple-100 to-purple-50 dark:from-purple-900/40 dark:to-purple-950/40 p-4 border border-purple-200 dark:border-purple-800">
                      <div className="flex items-center justify-between mb-2">
                        <p className="text-sm font-medium text-purple-700 dark:text-purple-300 flex items-center gap-1.5">
                          <Sprout className="h-4 w-4" /> Bloom Probability
                        </p>
                        <Badge variant="outline" className={`text-xs ${
                          dashboardData.ml_prediction.confidence === 'High' ? 'border-green-500 text-green-700 dark:text-green-400' :
                          dashboardData.ml_prediction.confidence === 'Medium' ? 'border-yellow-500 text-yellow-700 dark:text-yellow-400' :
                          'border-gray-500 text-gray-600'
                        }`}>
                          {dashboardData.ml_prediction.confidence} Confidence
                        </Badge>
                      </div>
                      <p className="text-4xl font-bold text-purple-600 dark:text-purple-400">
                        {dashboardData.ml_prediction.bloom_probability_percent?.toFixed(0)}%
                      </p>
                      <p className="text-xs text-purple-600/70 dark:text-purple-400/70 mt-1">
                        {dashboardData.ml_prediction.message}
                      </p>
                    </div>

                    {/* Yield Potential */}
                    <div className="rounded-xl bg-gradient-to-br from-emerald-100 to-emerald-50 dark:from-emerald-900/40 dark:to-emerald-950/40 p-4 border border-emerald-200 dark:border-emerald-800">
                      <div className="flex items-center justify-between mb-2">
                        <p className="text-sm font-medium text-emerald-700 dark:text-emerald-300 flex items-center gap-1.5">
                          <TrendingUp className="h-4 w-4" /> Yield Potential
                        </p>
                        <Badge variant="outline" className="text-xs border-emerald-500 text-emerald-700 dark:text-emerald-400">
                          Per Acre
                        </Badge>
                      </div>
                      <p className="text-4xl font-bold text-emerald-600 dark:text-emerald-400">
                        {dashboardData.ml_prediction.yield_potential_tonnes_per_acre ?? '—'}
                        <span className="text-lg ml-1 font-normal">t/acre</span>
                      </p>
                      <p className="text-xs text-emerald-600/70 dark:text-emerald-400/70 mt-1">
                        Estimated based on current vegetation health and conditions
                      </p>
                    </div>
                  </div>

                  {/* Risk Assessment Grid */}
                  <div>
                    <p className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-1.5">
                      <ShieldAlert className="h-4 w-4" /> Risk Assessment
                    </p>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                      {/* Drought Risk */}
                      <div className="rounded-lg bg-amber-50 dark:bg-amber-950/30 p-3 border border-amber-200 dark:border-amber-800">
                        <div className="flex items-center gap-1.5 mb-1">
                          <Sun className="h-3.5 w-3.5 text-amber-600" />
                          <p className="text-xs font-medium text-amber-700 dark:text-amber-400">Drought</p>
                        </div>
                        <p className={`text-2xl font-bold ${
                          (dashboardData.ml_prediction.drought_risk_percent ?? 0) >= 60 ? 'text-red-600' :
                          (dashboardData.ml_prediction.drought_risk_percent ?? 0) >= 30 ? 'text-amber-600' :
                          'text-green-600'
                        }`}>
                          {dashboardData.ml_prediction.drought_risk_percent?.toFixed(0) ?? '—'}%
                        </p>
                        <p className="text-[10px] text-amber-600/70 dark:text-amber-500/60 mt-0.5">
                          {dashboardData.ml_prediction.drought_risk_label ?? 'N/A'}
                        </p>
                      </div>

                      {/* Flood Risk */}
                      <div className="rounded-lg bg-blue-50 dark:bg-blue-950/30 p-3 border border-blue-200 dark:border-blue-800">
                        <div className="flex items-center gap-1.5 mb-1">
                          <CloudRain className="h-3.5 w-3.5 text-blue-600" />
                          <p className="text-xs font-medium text-blue-700 dark:text-blue-400">Flood</p>
                        </div>
                        <p className={`text-2xl font-bold ${
                          (dashboardData.ml_prediction.flood_risk_percent ?? 0) >= 60 ? 'text-red-600' :
                          (dashboardData.ml_prediction.flood_risk_percent ?? 0) >= 30 ? 'text-blue-600' :
                          'text-green-600'
                        }`}>
                          {dashboardData.ml_prediction.flood_risk_percent?.toFixed(0) ?? '—'}%
                        </p>
                        <p className="text-[10px] text-blue-600/70 dark:text-blue-500/60 mt-0.5">
                          {dashboardData.ml_prediction.flood_risk_label ?? 'N/A'}
                        </p>
                      </div>

                      {/* Pest Risk */}
                      <div className="rounded-lg bg-orange-50 dark:bg-orange-950/30 p-3 border border-orange-200 dark:border-orange-800">
                        <div className="flex items-center gap-1.5 mb-1">
                          <AlertTriangle className="h-3.5 w-3.5 text-orange-600" />
                          <p className="text-xs font-medium text-orange-700 dark:text-orange-400">Pest</p>
                        </div>
                        <p className={`text-2xl font-bold ${
                          (dashboardData.ml_prediction.pest_risk_percent ?? 0) >= 60 ? 'text-red-600' :
                          (dashboardData.ml_prediction.pest_risk_percent ?? 0) >= 30 ? 'text-orange-600' :
                          'text-green-600'
                        }`}>
                          {dashboardData.ml_prediction.pest_risk_percent?.toFixed(0) ?? '—'}%
                        </p>
                        <p className="text-[10px] text-orange-600/70 dark:text-orange-500/60 mt-0.5">
                          {dashboardData.ml_prediction.pest_risk_label ?? 'N/A'}
                        </p>
                      </div>

                      {/* Disease Risk */}
                      <div className="rounded-lg bg-red-50 dark:bg-red-950/30 p-3 border border-red-200 dark:border-red-800">
                        <div className="flex items-center gap-1.5 mb-1">
                          <ShieldAlert className="h-3.5 w-3.5 text-red-600" />
                          <p className="text-xs font-medium text-red-700 dark:text-red-400">Disease</p>
                        </div>
                        <p className={`text-2xl font-bold ${
                          (dashboardData.ml_prediction.disease_risk_percent ?? 0) >= 60 ? 'text-red-600' :
                          (dashboardData.ml_prediction.disease_risk_percent ?? 0) >= 30 ? 'text-orange-600' :
                          'text-green-600'
                        }`}>
                          {dashboardData.ml_prediction.disease_risk_percent?.toFixed(0) ?? '—'}%
                        </p>
                        <p className="text-[10px] text-red-600/70 dark:text-red-500/60 mt-0.5">
                          {dashboardData.ml_prediction.disease_risk_label ?? 'N/A'}
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="pt-3 border-t border-purple-200 dark:border-purple-800 flex items-center justify-between">
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {dashboardData.ml_prediction.model_version} • NASA satellite + weather data
                    </p>
                    <p className="text-xs text-gray-400">
                      Updated: {new Date(dashboardData.ml_prediction.predicted_at).toLocaleString()}
                    </p>
                  </div>
                </CardContent>
              </Card>
            )}

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* NDVI Trend Chart */}
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <TrendingUp className="h-5 w-5 text-green-600" />
                        NDVI Trend (Last 30 Days)
                      </CardTitle>
                      <CardDescription>
                        Vegetation health index from satellite data
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      {dashboardData?.ndvi_history && dashboardData.ndvi_history.length > 0 ? (
                        <ResponsiveContainer width="100%" height={300}>
                          <AreaChart data={dashboardData.ndvi_history}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis 
                              dataKey="date" 
                              tick={{ fontSize: 12 }}
                              tickFormatter={(value) => new Date(value).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                            />
                            <YAxis domain={[0, 1]} />
                            <Tooltip 
                              labelFormatter={(value) => new Date(value).toLocaleDateString()}
                              formatter={(value: any) => [value.toFixed(3), 'NDVI']}
                            />
                            <Area 
                              type="monotone" 
                              dataKey="ndvi" 
                              stroke="#16a34a" 
                              fill="#86efac" 
                              fillOpacity={0.6}
                            />
                          </AreaChart>
                        </ResponsiveContainer>
                      ) : (
                        <div className="h-[300px] flex items-center justify-center text-gray-500">
                          No NDVI data available
                        </div>
                      )}
                    </CardContent>
                  </Card>

                  {/* Temperature & Rainfall */}
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <Thermometer className="h-5 w-5 text-red-600" />
                        Climate Data
                      </CardTitle>
                      <CardDescription>
                        Temperature and rainfall patterns
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      {dashboardData?.climate_history && dashboardData.climate_history.length > 0 ? (
                        <ResponsiveContainer width="100%" height={300}>
                          <LineChart data={dashboardData.climate_history}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis 
                              dataKey="date" 
                              tick={{ fontSize: 12 }}
                              tickFormatter={(value) => new Date(value).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                            />
                            <YAxis yAxisId="left" />
                            <YAxis yAxisId="right" orientation="right" />
                            <Tooltip labelFormatter={(value) => new Date(value).toLocaleDateString()} />
                            <Legend />
                            <Line 
                              yAxisId="left"
                              type="monotone" 
                              dataKey="temperature" 
                              stroke="#ef4444" 
                              name="Temperature (°C)"
                            />
                            <Line 
                              yAxisId="right"
                              type="monotone" 
                              dataKey="rainfall" 
                              stroke="#3b82f6" 
                              name="Rainfall (mm)"
                            />
                          </LineChart>
                        </ResponsiveContainer>
                      ) : (
                        <div className="h-[300px] flex items-center justify-center text-gray-500">
                          No climate data available
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </div>

                {/* Sub-County Focused Map */}
                {farmer.county && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <MapPin className="h-5 w-5 text-blue-600" />
                        {farmer.sub_county
                          ? `${farmer.sub_county}, ${farmer.county}`
                          : `Your County: ${farmer.county}`}
                      </CardTitle>
                      <CardDescription>
                        Live bloom and climate data for your exact area
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <CountyFocusedMap
                        countyName={farmer.county}
                        subCounty={farmer.sub_county}
                        farmLat={farmer.location_lat}
                        farmLon={farmer.location_lon}
                      />
                    </CardContent>
                  </Card>
                )}

                {/* Your Crops & Farm Status */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Sprout className="h-5 w-5 text-green-600" />
                      Your Crops
                    </CardTitle>
                    <CardDescription>
                      Crops you&apos;re currently growing
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                      {farmer.crops.map((crop) => {
                        const cropInfo: Record<string, { emoji: string; color: string }> = {
                          maize: { emoji: '🌽', color: 'from-amber-50 to-yellow-50 dark:from-amber-950/30 dark:to-yellow-950/30 border-amber-200 dark:border-amber-800' },
                          beans: { emoji: '🫘', color: 'from-emerald-50 to-green-50 dark:from-emerald-950/30 dark:to-green-950/30 border-emerald-200 dark:border-emerald-800' },
                          sugarcane: { emoji: '🎋', color: 'from-lime-50 to-green-50 dark:from-lime-950/30 dark:to-green-950/30 border-lime-200 dark:border-lime-800' },
                          tea: { emoji: '🍵', color: 'from-green-50 to-emerald-50 dark:from-green-950/30 dark:to-emerald-950/30 border-green-200 dark:border-green-800' },
                          coffee: { emoji: '☕', color: 'from-amber-50 to-orange-50 dark:from-amber-950/30 dark:to-orange-950/30 border-amber-300 dark:border-amber-700' },
                          wheat: { emoji: '🌾', color: 'from-yellow-50 to-amber-50 dark:from-yellow-950/30 dark:to-amber-950/30 border-yellow-200 dark:border-yellow-800' },
                          rice: { emoji: '🍚', color: 'from-sky-50 to-blue-50 dark:from-sky-950/30 dark:to-blue-950/30 border-sky-200 dark:border-sky-800' },
                          tomatoes: { emoji: '🍅', color: 'from-red-50 to-rose-50 dark:from-red-950/30 dark:to-rose-950/30 border-red-200 dark:border-red-800' },
                          potatoes: { emoji: '🥔', color: 'from-orange-50 to-amber-50 dark:from-orange-950/30 dark:to-amber-950/30 border-orange-200 dark:border-orange-800' },
                        }
                        const info = cropInfo[crop.toLowerCase()] || { emoji: '🌿', color: 'from-green-50 to-emerald-50 dark:from-green-950/30 dark:to-emerald-950/30 border-green-200 dark:border-green-800' }
                        const ndvi = dashboardData?.ndvi_average
                        const healthLabel = ndvi ? (ndvi > 0.6 ? 'Healthy' : ndvi > 0.4 ? 'Fair' : ndvi > 0.2 ? 'Stressed' : 'Poor') : 'Monitoring'
                        const healthColor = ndvi ? (ndvi > 0.6 ? 'text-green-600' : ndvi > 0.4 ? 'text-yellow-600' : ndvi > 0.2 ? 'text-orange-600' : 'text-red-600') : 'text-gray-500'

                        return (
                          <div
                            key={crop}
                            className={`p-4 rounded-xl bg-gradient-to-br ${info.color} border flex items-center gap-3`}
                          >
                            <span className="text-2xl">{info.emoji}</span>
                            <div className="flex-1 min-w-0">
                              <p className="font-semibold text-sm">{crop.charAt(0).toUpperCase() + crop.slice(1)}</p>
                              <p className={`text-xs font-medium ${healthColor}`}>{healthLabel}</p>
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  </CardContent>
                </Card>

                {/* Soil Test Results Widget */}
                {(() => {
                  // Aggregate soil data from IoT sensors and satellite
                  const iotDevice = farmOverview?.iot?.latest?.[0]
                  const satData = farmOverview?.satellite?.[0]
                  const hasSoilData = iotDevice?.soil_nitrogen != null
                    || iotDevice?.soil_phosphorus != null
                    || iotDevice?.soil_potassium != null
                    || iotDevice?.soil_moisture_pct != null
                    || satData?.soil_moisture_pct != null

                  if (!hasSoilData) return null

                  // Soil health calculations
                  const nitrogen = iotDevice?.soil_nitrogen ?? null
                  const phosphorus = iotDevice?.soil_phosphorus ?? null
                  const potassium = iotDevice?.soil_potassium ?? null
                  const ph = iotDevice?.soil_ph ?? null
                  const iotMoisture = iotDevice?.soil_moisture_pct ?? null
                  const satMoisture = satData?.soil_moisture_pct ?? null
                  const moisture = iotMoisture ?? satMoisture

                  // Nutrient status helpers (mg/kg thresholds for tropical soils)
                  const nStatus = nitrogen != null ? (nitrogen >= 40 ? 'Optimal' : nitrogen >= 20 ? 'Moderate' : 'Low') : null
                  const pStatus = phosphorus != null ? (phosphorus >= 25 ? 'Optimal' : phosphorus >= 10 ? 'Moderate' : 'Low') : null
                  const kStatus = potassium != null ? (potassium >= 200 ? 'Optimal' : potassium >= 100 ? 'Moderate' : 'Low') : null
                  const phStatus = ph != null ? (ph >= 6.0 && ph <= 7.5 ? 'Optimal' : ph >= 5.5 ? 'Slightly Acidic' : ph < 5.5 ? 'Acidic' : 'Alkaline') : null
                  const moistureStatus = moisture != null ? (moisture >= 60 ? 'Wet' : moisture >= 30 ? 'Good' : moisture >= 15 ? 'Dry' : 'Very Dry') : null

                  const statusColor = (s: string | null) => {
                    if (!s) return 'text-gray-400'
                    if (s === 'Optimal' || s === 'Good') return 'text-green-600 dark:text-green-400'
                    if (s === 'Moderate' || s === 'Slightly Acidic' || s === 'Wet') return 'text-yellow-600 dark:text-yellow-400'
                    return 'text-red-600 dark:text-red-400'
                  }
                  const statusBg = (s: string | null) => {
                    if (!s) return 'bg-gray-100 dark:bg-gray-800'
                    if (s === 'Optimal' || s === 'Good') return 'bg-green-50 dark:bg-green-950/30'
                    if (s === 'Moderate' || s === 'Slightly Acidic' || s === 'Wet') return 'bg-yellow-50 dark:bg-yellow-950/30'
                    return 'bg-red-50 dark:bg-red-950/30'
                  }

                  // Overall soil health score (simple average of nutrient statuses)
                  const scores = [nStatus, pStatus, kStatus, phStatus, moistureStatus].filter(Boolean)
                  const scoreValues = scores.map(s => s === 'Optimal' || s === 'Good' ? 3 : (s === 'Moderate' || s === 'Slightly Acidic' || s === 'Wet') ? 2 : 1)
                  const avgScore = scoreValues.length > 0 ? scoreValues.reduce((a, b) => a + b, 0) / scoreValues.length : 0
                  const overallHealth = avgScore >= 2.5 ? 'Good' : avgScore >= 1.5 ? 'Fair' : 'Needs Attention'
                  const overallColor = overallHealth === 'Good' ? 'text-green-600' : overallHealth === 'Fair' ? 'text-yellow-600' : 'text-red-600'
                  const overallBg = overallHealth === 'Good' ? 'from-green-500 to-emerald-500' : overallHealth === 'Fair' ? 'from-yellow-500 to-amber-500' : 'from-red-500 to-orange-500'

                  return (
                    <Card className="border-2 border-amber-200 dark:border-amber-800 bg-gradient-to-br from-white via-amber-50/20 to-orange-50/20 dark:from-gray-900 dark:via-amber-950/20 dark:to-orange-950/20 shadow-lg">
                      <CardHeader className="pb-3">
                        <CardTitle className="flex items-center justify-between">
                          <span className="flex items-center gap-2 text-amber-700 dark:text-amber-300">
                            <span className="text-xl">🧪</span>
                            Soil Test Results
                          </span>
                          <div className={`px-3 py-1 rounded-full text-xs font-bold text-white bg-gradient-to-r ${overallBg}`}>
                            {overallHealth}
                          </div>
                        </CardTitle>
                        <CardDescription>
                          {iotMoisture != null ? 'IoT sensor' : 'Satellite'} soil analysis • {farmOverview?.farm?.name || 'Your Farm'}
                        </CardDescription>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        {/* N-P-K Nutrient Bar */}
                        {(nitrogen != null || phosphorus != null || potassium != null) && (
                          <div>
                            <p className="text-xs font-semibold text-gray-600 dark:text-gray-400 mb-2 flex items-center gap-1">
                              <span className="text-sm">🌱</span> Macronutrients (N-P-K)
                            </p>
                            <div className="grid grid-cols-3 gap-3">
                              {nitrogen != null && (
                                <div className={`rounded-xl p-3 text-center ${statusBg(nStatus)} border border-green-200 dark:border-green-800`}>
                                  <div className="w-10 h-10 rounded-full bg-green-100 dark:bg-green-900/50 flex items-center justify-center mx-auto mb-2">
                                    <span className="text-sm font-black text-green-700 dark:text-green-400">N</span>
                                  </div>
                                  <p className="text-xl font-bold text-green-700 dark:text-green-400">{nitrogen.toFixed(0)}</p>
                                  <p className="text-[10px] text-gray-500">mg/kg</p>
                                  <p className={`text-xs font-semibold mt-1 ${statusColor(nStatus)}`}>{nStatus}</p>
                                </div>
                              )}
                              {phosphorus != null && (
                                <div className={`rounded-xl p-3 text-center ${statusBg(pStatus)} border border-purple-200 dark:border-purple-800`}>
                                  <div className="w-10 h-10 rounded-full bg-purple-100 dark:bg-purple-900/50 flex items-center justify-center mx-auto mb-2">
                                    <span className="text-sm font-black text-purple-700 dark:text-purple-400">P</span>
                                  </div>
                                  <p className="text-xl font-bold text-purple-700 dark:text-purple-400">{phosphorus.toFixed(0)}</p>
                                  <p className="text-[10px] text-gray-500">mg/kg</p>
                                  <p className={`text-xs font-semibold mt-1 ${statusColor(pStatus)}`}>{pStatus}</p>
                                </div>
                              )}
                              {potassium != null && (
                                <div className={`rounded-xl p-3 text-center ${statusBg(kStatus)} border border-orange-200 dark:border-orange-800`}>
                                  <div className="w-10 h-10 rounded-full bg-orange-100 dark:bg-orange-900/50 flex items-center justify-center mx-auto mb-2">
                                    <span className="text-sm font-black text-orange-700 dark:text-orange-400">K</span>
                                  </div>
                                  <p className="text-xl font-bold text-orange-700 dark:text-orange-400">{potassium.toFixed(0)}</p>
                                  <p className="text-[10px] text-gray-500">mg/kg</p>
                                  <p className={`text-xs font-semibold mt-1 ${statusColor(kStatus)}`}>{kStatus}</p>
                                </div>
                              )}
                            </div>
                          </div>
                        )}

                        {/* pH and Moisture Row */}
                        <div className="grid grid-cols-2 gap-4">
                          {ph != null && (
                            <div className={`rounded-xl p-4 ${statusBg(phStatus)} border border-blue-200 dark:border-blue-800`}>
                              <div className="flex items-center gap-2 mb-2">
                                <span className="text-lg">⚗️</span>
                                <p className="text-xs font-semibold text-gray-600 dark:text-gray-400">Soil pH</p>
                              </div>
                              <div className="flex items-end gap-2">
                                <p className="text-3xl font-bold text-blue-700 dark:text-blue-400">{ph.toFixed(1)}</p>
                                <p className={`text-xs font-semibold mb-1 ${statusColor(phStatus)}`}>{phStatus}</p>
                              </div>
                              {/* pH scale bar */}
                              <div className="mt-2 relative h-2 rounded-full bg-gradient-to-r from-red-400 via-green-400 to-blue-400 overflow-hidden">
                                <div
                                  className="absolute top-0 w-1.5 h-full bg-white border border-gray-800 rounded-full shadow"
                                  style={{ left: `${Math.min(100, Math.max(0, ((ph - 3) / 11) * 100))}%` }}
                                />
                              </div>
                              <div className="flex justify-between mt-0.5">
                                <span className="text-[9px] text-gray-400">Acidic</span>
                                <span className="text-[9px] text-gray-400">Neutral</span>
                                <span className="text-[9px] text-gray-400">Alkaline</span>
                              </div>
                            </div>
                          )}

                          {moisture != null && (
                            <div className={`rounded-xl p-4 ${statusBg(moistureStatus)} border border-cyan-200 dark:border-cyan-800`}>
                              <div className="flex items-center gap-2 mb-2">
                                <Droplets className="h-4 w-4 text-cyan-600" />
                                <p className="text-xs font-semibold text-gray-600 dark:text-gray-400">
                                  Soil Moisture {iotMoisture != null ? '(IoT)' : '(Sat)'}
                                </p>
                              </div>
                              <div className="flex items-end gap-2">
                                <p className="text-3xl font-bold text-cyan-700 dark:text-cyan-400">{moisture.toFixed(0)}%</p>
                                <p className={`text-xs font-semibold mb-1 ${statusColor(moistureStatus)}`}>{moistureStatus}</p>
                              </div>
                              {/* Moisture bar */}
                              <div className="mt-2 relative h-2 rounded-full bg-gray-200 dark:bg-gray-700 overflow-hidden">
                                <div
                                  className="h-full rounded-full bg-gradient-to-r from-cyan-400 to-blue-500 transition-all duration-500"
                                  style={{ width: `${Math.min(100, moisture)}%` }}
                                />
                              </div>
                            </div>
                          )}
                        </div>

                        <div className="pt-2 border-t border-amber-200 dark:border-amber-800 flex items-center justify-between">
                          <p className="text-[10px] text-gray-400">
                            {iotMoisture != null ? '📡 ESP32 IoT Sensor • ' : '🛰️ Satellite Data • '}
                            {farmOverview?.farm?.county || farmer.county}{farmOverview?.farm?.sub_county ? `, ${farmOverview.farm.sub_county}` : ''}
                          </p>
                          <p className="text-[10px] text-gray-400">
                            See Farms tab for full details
                          </p>
                        </div>
                      </CardContent>
                    </Card>
                  )
                })()}

                {/* Weather Summary — compact 3-day strip on overview */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Cloud className="h-5 w-5 text-blue-600" />
                      Weather — {farmer.sub_county ? `${farmer.sub_county}` : farmer.county}
                    </CardTitle>
                    <CardDescription>
                      Current conditions and 3-day outlook
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    {weatherForecast?.daily_forecasts || weatherForecast?.daily_forecast || weatherForecast?.forecast ? (
                      <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                        {/* Current */}
                        <div className="flex items-center gap-3 p-3 rounded-xl bg-gradient-to-br from-blue-50 to-sky-50 dark:from-blue-950/40 dark:to-sky-950/40 border border-blue-100 dark:border-blue-800">
                          <Sun className="h-8 w-8 text-amber-500" />
                          <div>
                            <p className="text-lg font-bold">
                              {currentWeather?.temperature_c ?? currentWeather?.temperature ?? weatherForecast?.current?.temperature ?? dashboardData?.current_weather?.temperature ?? '--'}°C
                            </p>
                            <p className="text-xs text-gray-500">Now</p>
                          </div>
                        </div>
                        {/* Next 3 days */}
                        {(weatherForecast.daily_forecasts || weatherForecast.daily_forecast || weatherForecast.forecast || []).slice(0, 3).map((day: any, idx: number) => {
                          const maxT = day.max_temp_c ?? day.max_temp ?? day.temperature_max ?? day.temp_max ?? '--'
                          const minT = day.min_temp_c ?? day.min_temp ?? day.temperature_min ?? day.temp_min ?? '--'
                          const precip = day.precipitation_mm ?? day.precipitation ?? day.rain ?? day.rainfall ?? 0
                          const label = idx === 0 ? 'Today' : new Date(day.date || Date.now() + idx * 86400000).toLocaleDateString('en-US', { weekday: 'short' })
                          return (
                            <div key={idx} className="flex items-center justify-between p-3 rounded-xl bg-gray-50 dark:bg-gray-800/50 border border-gray-100 dark:border-gray-700">
                              <div>
                                <p className="text-xs font-semibold text-gray-500">{label}</p>
                                <p className="text-sm font-bold">{maxT}° / {minT}°</p>
                              </div>
                              {precip > 0 && (
                                <Badge variant="secondary" className="text-xs">{precip}mm</Badge>
                              )}
                            </div>
                          )
                        })}
                      </div>
                    ) : weatherLoading ? (
                      <div className="flex items-center gap-2 text-gray-400">
                        <Loader2 className="h-4 w-4 animate-spin" /> Loading weather...
                      </div>
                    ) : (
                      <p className="text-sm text-gray-400">Weather data unavailable — set your farm coordinates</p>
                    )}

                    {/* Ag insights warnings banner */}
                    {agInsights && (
                      (agInsights.insights?.some((i: any) => i.severity === 'warning' || i.severity === 'alert') ||
                       agInsights.heat_stress || agInsights.drought_risk === 'high' || agInsights.drought_risk === 'critical') && (
                      <div className="mt-4 p-3 rounded-xl bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 flex items-start gap-2">
                        <ShieldAlert className="h-5 w-5 text-red-600 mt-0.5 flex-shrink-0" />
                        <div>
                          <p className="text-sm font-semibold text-red-700 dark:text-red-400">Weather Warning</p>
                          <p className="text-xs text-red-600 dark:text-red-500">
                            {agInsights.insights?.filter((i: any) => i.severity === 'warning' || i.severity === 'alert')
                              .map((i: any) => i.message).join(' ') ||
                             (agInsights.heat_stress ? 'High temperatures may stress crops. ' : '') +
                             ((agInsights.drought_risk === 'high' || agInsights.drought_risk === 'critical') ? `Drought risk is ${agInsights.drought_risk}. Consider irrigation.` : '')}
                          </p>
                        </div>
                      </div>
                    ))}
                  </CardContent>
                </Card>
              </div>
              )}
              {selectedTab === 'farms' && (
              <div className="space-y-6">
                {farms.length === 0 ? (
                  <Card className="p-12 text-center">
                    <Leaf className="h-12 w-12 text-gray-300 mx-auto mb-4" />
                    <h3 className="text-lg font-semibold text-gray-600 dark:text-gray-400">No Farms Registered</h3>
                    <p className="text-sm text-gray-500 mt-2 mb-4">
                      Register your farms to get satellite monitoring, IoT data, and AI predictions.
                    </p>
                    <Link href="/dashboard/add-farm">
                      <Button className="bg-green-600 hover:bg-green-700">
                        <Plus className="h-4 w-4 mr-2" /> Register Your First Farm
                      </Button>
                    </Link>
                  </Card>
                ) : (
                  <>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      {farms.map(farm => (
                        <Card
                          key={farm.id}
                          className={`cursor-pointer transition-all hover:shadow-lg ${
                            selectedFarmId === farm.id
                              ? 'border-2 border-green-500 ring-2 ring-green-100 dark:ring-green-900'
                              : ''
                          }`}
                          onClick={() => setSelectedFarmId(farm.id)}
                        >
                          <CardContent className="p-4">
                            <div className="flex items-start justify-between mb-3">
                              <div>
                                <h3 className="font-semibold text-base">{farm.name || `Farm #${farm.id}`}</h3>
                                <p className="text-sm text-gray-500 flex items-center gap-1">
                                  <MapPin className="h-3 w-3" />
                                  {farm.county}{farm.sub_county ? `, ${farm.sub_county}` : ''}
                                </p>
                              </div>
                              <div className="flex items-center gap-1.5">
                                {farm.sensor_count && farm.sensor_count > 0 ? (
                                  <Badge className="bg-cyan-100 text-cyan-700 dark:bg-cyan-900 dark:text-cyan-300 text-xs">
                                    <Cpu className="h-3 w-3 mr-1" /> {farm.sensor_count} ESP32
                                  </Badge>
                                ) : (
                                  <Badge variant="outline" className="text-xs">
                                    <Cloud className="h-3 w-3 mr-1" /> Satellite
                                  </Badge>
                                )}
                              </div>
                            </div>
                            <div className="grid grid-cols-2 gap-2 text-xs text-gray-500">
                              {farm.size_acres && <span>{farm.size_acres} acres</span>}
                              {farm.crops && farm.crops.length > 0 && (
                                <span>{farm.crops.slice(0, 3).join(', ')}</span>
                              )}
                              {farm.soil_type && <span>Soil: {farm.soil_type}</span>}
                              {farm.irrigation_type && <span>{farm.irrigation_type}</span>}
                            </div>
                          </CardContent>
                        </Card>
                      ))}
                    </div>

                    {/* Selected Farm Details */}
                    {farmOverview && (
                      <div className="space-y-4">
                        <h3 className="text-lg font-semibold text-green-700 dark:text-green-400">
                          Farm Details: {farmOverview.farm?.name || 'Selected Farm'}
                        </h3>

                        {/* IoT Data Section */}
                        {farmOverview.iot && (
                          <Card className="border-cyan-200 dark:border-cyan-800">
                            <CardHeader className="pb-3">
                              <CardTitle className="text-base flex items-center gap-2">
                                <Cpu className="h-5 w-5 text-cyan-600" /> Live IoT Sensor Data
                              </CardTitle>
                            </CardHeader>
                            <CardContent>
                              {farmOverview.iot.latest && farmOverview.iot.latest.length > 0 ? (
                                <div className="space-y-4">
                                  {farmOverview.iot.latest.map((device: any, idx: number) => (
                                    <div key={idx} className="p-4 bg-cyan-50 dark:bg-cyan-950/30 rounded-xl border border-cyan-100 dark:border-cyan-800">
                                      <div className="flex items-center gap-2 mb-3 pb-2 border-b border-cyan-200 dark:border-cyan-700">
                                        <Wifi className="h-4 w-4 text-green-500" />
                                        <span className="text-sm font-mono font-semibold text-gray-700 dark:text-gray-300">
                                          {device.device_id?.slice(-8) || `Sensor-${idx + 1}`}
                                        </span>
                                        {device.battery_pct != null && (
                                          <Badge variant={device.battery_pct < 20 ? "destructive" : "secondary"} className="ml-auto text-xs">
                                            🔋 {device.battery_pct.toFixed(0)}%
                                          </Badge>
                                        )}
                                      </div>
                                      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-3">
                                        {device.temperature_c != null && (
                                          <div className="text-center p-2 bg-white dark:bg-gray-900 rounded-lg">
                                            <Thermometer className="h-4 w-4 mx-auto text-red-500 mb-1" />
                                            <p className="text-lg font-bold text-red-600">{device.temperature_c.toFixed(1)}°C</p>
                                            <p className="text-[10px] text-gray-500">Temperature</p>
                                          </div>
                                        )}
                                        {device.humidity_pct != null && (
                                          <div className="text-center p-2 bg-white dark:bg-gray-900 rounded-lg">
                                            <Droplets className="h-4 w-4 mx-auto text-blue-500 mb-1" />
                                            <p className="text-lg font-bold text-blue-600">{device.humidity_pct.toFixed(0)}%</p>
                                            <p className="text-[10px] text-gray-500">Humidity</p>
                                          </div>
                                        )}
                                        {device.soil_moisture_pct != null && (
                                          <div className="text-center p-2 bg-white dark:bg-gray-900 rounded-lg">
                                            <span className="text-base block mb-1">💧</span>
                                            <p className="text-lg font-bold text-amber-600">{device.soil_moisture_pct.toFixed(0)}%</p>
                                            <p className="text-[10px] text-gray-500">Soil Moisture</p>
                                          </div>
                                        )}
                                        {device.soil_nitrogen != null && (
                                          <div className="text-center p-2 bg-white dark:bg-gray-900 rounded-lg">
                                            <span className="text-xs font-bold text-green-700 block mb-1">N</span>
                                            <p className="text-lg font-bold text-green-600">{device.soil_nitrogen.toFixed(0)}</p>
                                            <p className="text-[10px] text-gray-500">Nitrogen</p>
                                          </div>
                                        )}
                                        {device.soil_phosphorus != null && (
                                          <div className="text-center p-2 bg-white dark:bg-gray-900 rounded-lg">
                                            <span className="text-xs font-bold text-purple-700 block mb-1">P</span>
                                            <p className="text-lg font-bold text-purple-600">{device.soil_phosphorus.toFixed(0)}</p>
                                            <p className="text-[10px] text-gray-500">Phosphorus</p>
                                          </div>
                                        )}
                                        {device.soil_potassium != null && (
                                          <div className="text-center p-2 bg-white dark:bg-gray-900 rounded-lg">
                                            <span className="text-xs font-bold text-orange-700 block mb-1">K</span>
                                            <p className="text-lg font-bold text-orange-600">{device.soil_potassium.toFixed(0)}</p>
                                            <p className="text-[10px] text-gray-500">Potassium</p>
                                          </div>
                                        )}
                                        {device.wind_speed_ms != null && (
                                          <div className="text-center p-2 bg-white dark:bg-gray-900 rounded-lg">
                                            <Wind className="h-4 w-4 mx-auto text-teal-500 mb-1" />
                                            <p className="text-lg font-bold text-teal-600">{device.wind_speed_ms.toFixed(1)}</p>
                                            <p className="text-[10px] text-gray-500">Wind m/s</p>
                                          </div>
                                        )}
                                        {device.light_lux != null && (
                                          <div className="text-center p-2 bg-white dark:bg-gray-900 rounded-lg">
                                            <Sun className="h-4 w-4 mx-auto text-yellow-500 mb-1" />
                                            <p className="text-lg font-bold text-yellow-600">{device.light_lux.toFixed(0)}</p>
                                            <p className="text-[10px] text-gray-500">Light (lux)</p>
                                          </div>
                                        )}
                                        {device.pressure_hpa != null && (
                                          <div className="text-center p-2 bg-white dark:bg-gray-900 rounded-lg">
                                            <Gauge className="h-4 w-4 mx-auto text-indigo-500 mb-1" />
                                            <p className="text-lg font-bold text-indigo-600">{device.pressure_hpa.toFixed(0)}</p>
                                            <p className="text-[10px] text-gray-500">Pressure hPa</p>
                                          </div>
                                        )}
                                        {device.co2_ppm != null && (
                                          <div className="text-center p-2 bg-white dark:bg-gray-900 rounded-lg">
                                            <span className="text-xs font-bold text-gray-600 block mb-1">CO₂</span>
                                            <p className="text-lg font-bold text-gray-700">{device.co2_ppm.toFixed(0)}</p>
                                            <p className="text-[10px] text-gray-500">ppm</p>
                                          </div>
                                        )}
                                        {device.rainfall_mm != null && device.rainfall_mm > 0 && (
                                          <div className="text-center p-2 bg-white dark:bg-gray-900 rounded-lg">
                                            <CloudRain className="h-4 w-4 mx-auto text-blue-500 mb-1" />
                                            <p className="text-lg font-bold text-blue-600">{device.rainfall_mm.toFixed(1)}</p>
                                            <p className="text-[10px] text-gray-500">Rain (mm)</p>
                                          </div>
                                        )}
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              ) : (
                                <p className="text-sm text-gray-500 text-center py-4">
                                  No IoT devices connected to this farm. Using satellite data only.
                                </p>
                              )}
                            </CardContent>
                          </Card>
                        )}

                        {/* Satellite Data */}
                        {farmOverview.satellite && farmOverview.satellite.length > 0 && (() => {
                          const sat = farmOverview.satellite[0];
                          return (
                          <Card>
                            <CardHeader className="pb-3">
                              <CardTitle className="text-base flex items-center gap-2">
                                <TrendingUp className="h-5 w-5 text-green-600" /> Satellite Analysis
                              </CardTitle>
                            </CardHeader>
                            <CardContent>
                              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                {sat.ndvi != null && (
                                  <div className="p-3 bg-green-50 dark:bg-green-950/30 rounded-lg text-center">
                                    <p className="text-xs text-gray-500 mb-1">NDVI</p>
                                    <p className="text-2xl font-bold text-green-600">{(sat.ndvi * 100).toFixed(0)}%</p>
                                  </div>
                                )}
                                {sat.temperature_mean_c != null && (
                                  <div className="p-3 bg-red-50 dark:bg-red-950/30 rounded-lg text-center">
                                    <p className="text-xs text-gray-500 mb-1">Temperature</p>
                                    <p className="text-2xl font-bold text-red-600">{sat.temperature_mean_c.toFixed(1)}°C</p>
                                  </div>
                                )}
                                {sat.rainfall_mm != null && (
                                  <div className="p-3 bg-blue-50 dark:bg-blue-950/30 rounded-lg text-center">
                                    <p className="text-xs text-gray-500 mb-1">Rainfall</p>
                                    <p className="text-2xl font-bold text-blue-600">{sat.rainfall_mm.toFixed(0)}mm</p>
                                  </div>
                                )}
                                {sat.soil_moisture_pct != null && (
                                  <div className="p-3 bg-amber-50 dark:bg-amber-950/30 rounded-lg text-center">
                                    <p className="text-xs text-gray-500 mb-1">Soil Moisture</p>
                                    <p className="text-2xl font-bold text-amber-600">{sat.soil_moisture_pct.toFixed(0)}%</p>
                                  </div>
                                )}
                              </div>
                            </CardContent>
                          </Card>
                          );
                        })()}

                        {/* AI Predictions for this farm */}
                        {farmOverview.predictions && farmOverview.predictions.length > 0 && (
                          <Card className="border-purple-200 dark:border-purple-800">
                            <CardHeader className="pb-3">
                              <CardTitle className="text-base flex items-center gap-2">
                                🤖 AI Predictions for This Farm
                              </CardTitle>
                            </CardHeader>
                            <CardContent>
                              <div className="space-y-2">
                                {farmOverview.predictions.map((pred: any, idx: number) => (
                                  <div key={idx} className="flex items-center justify-between p-3 bg-purple-50 dark:bg-purple-950/30 rounded-lg">
                                    <span className="text-sm font-medium">{pred.label || 'Bloom Prediction'}</span>
                                    <span className="font-bold text-purple-600">{pred.value || `${(pred.probability * 100).toFixed(0)}%`}</span>
                                  </div>
                                ))}
                              </div>
                            </CardContent>
                          </Card>
                        )}
                      </div>
                    )}
                  </>
                )}
              </div>
              )}

              {/* Bloom Data Tab */}
              {selectedTab === 'bloom' && (
              <div className="space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Sprout className="h-5 w-5 text-pink-600" />
                      Recent Bloom Events
                    </CardTitle>
                    <CardDescription>
                      Detected bloom activity in your region
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    {dashboardData?.bloom_events && dashboardData.bloom_events.length > 0 ? (
                      <div className="space-y-4">
                        {dashboardData.bloom_events.map((bloom: any, index: number) => (
                          <div
                            key={index}
                            className="flex items-start justify-between p-4 border rounded-lg hover:bg-gray-50 dark:hover:bg-gray-900 transition-colors"
                          >
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-2">
                                <Sprout className="h-5 w-5 text-pink-600" />
                                <h3 className="font-semibold text-lg">
                                  {bloom.crop_type?.charAt(0).toUpperCase() + bloom.crop_type?.slice(1) || 'Unknown Crop'}
                                </h3>
                              </div>
                              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                                <div>
                                  <p className="text-gray-500">Probability</p>
                                  <p className="font-semibold text-pink-600">
                                    {bloom.bloom_probability ? `${(bloom.bloom_probability * 100).toFixed(0)}%` : 'N/A'}
                                  </p>
                                </div>
                                <div>
                                  <p className="text-gray-500">Area</p>
                                  <p className="font-semibold">
                                    {bloom.bloom_area_km2 ? `${bloom.bloom_area_km2.toFixed(1)} km²` : 'N/A'}
                                  </p>
                                </div>
                                <div>
                                  <p className="text-gray-500">Confidence</p>
                                  <p className="font-semibold">{bloom.confidence || 'Medium'}</p>
                                </div>
                                <div>
                                  <p className="text-gray-500">Date</p>
                                  <p className="font-semibold">
                                    {bloom.detection_date ? new Date(bloom.detection_date).toLocaleDateString() : 'Recent'}
                                  </p>
                                </div>
                              </div>
                            </div>
                            <ChevronRight className="h-5 w-5 text-gray-400" />
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-center py-12 text-gray-500">
                        <Sprout className="h-12 w-12 mx-auto mb-4 opacity-50" />
                        <p>No bloom events detected in your area yet.</p>
                        <p className="text-sm mt-2">Check back later for updates.</p>
                      </div>
                    )}
                  </CardContent>
                </Card>

                {/* County Map in Bloom Tab */}
                {farmer.county && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <MapPin className="h-5 w-5 text-blue-600" />
                        Bloom Activity Map - {farmer.sub_county ? `${farmer.sub_county}, ${farmer.county}` : farmer.county}
                      </CardTitle>
                      <CardDescription>
                        Visual representation of bloom activity in your area
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <CountyFocusedMap
                        countyName={farmer.county}
                        subCounty={farmer.sub_county}
                        farmLat={farmer.location_lat}
                        farmLon={farmer.location_lon}
                      />
                    </CardContent>
                  </Card>
                )}

                {/* Crop Calendar */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Calendar className="h-5 w-5 text-green-600" />
                      Crop Calendar - Current Season
                    </CardTitle>
                    <CardDescription>
                      Planting and harvesting schedules for your crops
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {farmer.crops.map((crop) => {
                        const currentMonth = new Date().getMonth() + 1
                        const cropName = crop.startsWith('other:') ? crop.replace('other:', '') : crop.charAt(0).toUpperCase() + crop.slice(1)
                        
                        // Simplified calendar logic
                        const isPlantingSeason = currentMonth >= 3 && currentMonth <= 5 || currentMonth >= 10 && currentMonth <= 11
                        const isHarvestSeason = currentMonth >= 7 && currentMonth <= 9 || currentMonth === 1 || currentMonth === 12
                        
                        return (
                          <div key={crop} className="border rounded-lg p-4">
                            <div className="flex items-center justify-between mb-2">
                              <h4 className="font-semibold text-lg">{cropName}</h4>
                              <span className={`px-3 py-1 rounded-full text-sm ${
                                isPlantingSeason ? 'bg-green-100 text-green-700' :
                                isHarvestSeason ? 'bg-yellow-100 text-yellow-700' :
                                'bg-gray-100 text-gray-700'
                              }`}>
                                {isPlantingSeason ? '🌱 Planting Season' :
                                 isHarvestSeason ? '🌾 Harvest Season' :
                                 '🌿 Growth Season'}
                              </span>
                            </div>
                            <div className="grid grid-cols-2 gap-4 text-sm">
                              <div>
                                <p className="text-gray-500">Optimal Planting</p>
                                <p className="font-semibold">March - May, Oct - Nov</p>
                              </div>
                              <div>
                                <p className="text-gray-500">Expected Harvest</p>
                                <p className="font-semibold">July - Sept, Dec - Jan</p>
                              </div>
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  </CardContent>
                </Card>
              </div>
              )}

              {/* Weather Tab — Real Google Weather API Data */}
              {selectedTab === 'weather' && (
              <div className="space-y-6">
                {/* Location Header */}
                <div className="flex items-center gap-2 text-sm text-gray-500">
                  <MapPin className="h-4 w-4" />
                  <span>
                    Weather for {farmer.sub_county ? `${farmer.sub_county}, ${farmer.county}` : farmer.county || 'your area'}
                  </span>
                  {weatherLoading && <Loader2 className="h-4 w-4 animate-spin ml-2" />}
                </div>

                {/* Current Conditions */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <Card>
                    <CardContent className="pt-6">
                      <div className="flex items-center gap-3">
                        <Thermometer className="h-8 w-8 text-red-500" />
                        <div>
                          <p className="text-3xl font-bold text-red-600">
                            {currentWeather?.temperature_c ?? currentWeather?.temperature ?? weatherForecast?.current?.temperature ?? dashboardData?.current_weather?.temperature ?? '--'}°C
                          </p>
                          <p className="text-xs text-gray-500">Temperature</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardContent className="pt-6">
                      <div className="flex items-center gap-3">
                        <Droplets className="h-8 w-8 text-blue-500" />
                        <div>
                          <p className="text-3xl font-bold text-blue-600">
                            {currentWeather?.humidity_pct ?? currentWeather?.humidity ?? weatherForecast?.current?.humidity ?? (dashboardData?.current_weather as any)?.humidity ?? '--'}%
                          </p>
                          <p className="text-xs text-gray-500">Humidity</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardContent className="pt-6">
                      <div className="flex items-center gap-3">
                        <Wind className="h-8 w-8 text-teal-500" />
                        <div>
                          <p className="text-3xl font-bold text-teal-600">
                            {currentWeather?.wind_speed_kmh ?? currentWeather?.wind_speed ?? weatherForecast?.current?.wind_speed ?? '--'} km/h
                          </p>
                          <p className="text-xs text-gray-500">Wind Speed</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardContent className="pt-6">
                      <div className="flex items-center gap-3">
                        <CloudRain className="h-8 w-8 text-indigo-500" />
                        <div>
                          <p className="text-3xl font-bold text-indigo-600">
                            {currentWeather?.precipitation_mm ?? currentWeather?.precipitation ?? weatherForecast?.current?.precipitation ?? dashboardData?.current_weather?.rainfall ?? 0} mm
                          </p>
                          <p className="text-xs text-gray-500">Precipitation</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {/* 10-Day Forecast from Google Weather API */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Calendar className="h-5 w-5 text-blue-600" />
                      10-Day Forecast
                    </CardTitle>
                    <CardDescription>
                      {farmer.sub_county ? `${farmer.sub_county}, ${farmer.county}` : farmer.county} — Google Weather API
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    {weatherForecast?.daily_forecasts || weatherForecast?.daily_forecast || weatherForecast?.forecast ? (
                      <div className="grid grid-cols-2 md:grid-cols-5 lg:grid-cols-5 gap-3">
                        {(weatherForecast.daily_forecasts || weatherForecast.daily_forecast || weatherForecast.forecast || []).slice(0, 10).map((day: any, idx: number) => {
                          const dayLabel = idx === 0 ? 'Today' : new Date(day.date || day.datetime || Date.now() + idx * 86400000).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })
                          const maxT = day.max_temp_c ?? day.max_temp ?? day.temperature_max ?? day.temp_max ?? '--'
                          const minT = day.min_temp_c ?? day.min_temp ?? day.temperature_min ?? day.temp_min ?? '--'
                          const precip = day.precipitation_mm ?? day.precipitation ?? day.rain ?? day.rainfall ?? 0
                          const condition = day.condition ?? day.conditions ?? day.description ?? ''
                          const humidity = day.humidity_pct ?? day.humidity ?? day.avg_humidity ?? '--'

                          const getIcon = () => {
                            const c = condition.toLowerCase()
                            if (c.includes('rain') || c.includes('shower')) return '🌧️'
                            if (c.includes('storm') || c.includes('thunder')) return '⛈️'
                            if (c.includes('cloud') || c.includes('overcast')) return '☁️'
                            if (c.includes('partly')) return '⛅'
                            if (c.includes('fog') || c.includes('mist')) return '🌫️'
                            return '☀️'
                          }

                          return (
                            <div key={idx} className="border rounded-xl p-4 text-center hover:shadow-md transition-shadow bg-white dark:bg-gray-900">
                              <p className="font-semibold text-xs text-gray-500 mb-2">{dayLabel}</p>
                              <div className="text-3xl mb-2">{getIcon()}</div>
                              <div className="flex items-center justify-center gap-2 mb-1">
                                <span className="text-lg font-bold text-red-600">{maxT}°</span>
                                <span className="text-sm text-gray-400">/</span>
                                <span className="text-sm text-blue-500">{minT}°</span>
                              </div>
                              {precip > 0 && (
                                <p className="text-xs text-blue-600 font-medium">{precip}mm rain</p>
                              )}
                              <p className="text-xs text-gray-400 mt-1">{humidity}% humidity</p>
                              {condition && (
                                <p className="text-xs text-gray-500 mt-1 truncate" title={condition}>{condition}</p>
                              )}
                            </div>
                          )
                        })}
                      </div>
                    ) : (
                      <div className="h-[200px] flex flex-col items-center justify-center text-gray-400">
                        {weatherLoading ? (
                          <Loader2 className="h-8 w-8 animate-spin mb-2" />
                        ) : (
                          <>
                            <Cloud className="h-10 w-10 mb-2" />
                            <p className="text-sm">Weather forecast data unavailable</p>
                            <p className="text-xs mt-1">Set your farm coordinates to enable weather</p>
                          </>
                        )}
                      </div>
                    )}
                  </CardContent>
                </Card>

                {/* Agricultural Insights */}
                {agInsights && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <Sprout className="h-5 w-5 text-green-600" />
                        Agricultural Weather Insights
                      </CardTitle>
                      <CardDescription>
                        AI-powered farming recommendations based on weather
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      {/* New insights array from backend */}
                      {agInsights.insights && agInsights.insights.length > 0 && (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-4">
                          {agInsights.insights.map((insight: any, idx: number) => {
                            const severityStyles = {
                              warning: 'border-amber-200 bg-amber-50 dark:bg-amber-950/30 dark:border-amber-800',
                              alert: 'border-red-200 bg-red-50 dark:bg-red-950/30 dark:border-red-800',
                              info: 'border-blue-200 bg-blue-50 dark:bg-blue-950/30 dark:border-blue-800',
                            }
                            const icons: Record<string, string> = {
                              heavy_rain: '🌧️', moderate_rain: '🌦️', light_rain: '💧', dry_spell: '🔥',
                              heat_stress: '🌡️', planting_window: '🌱', bloom_risk: '🌸',
                              spray_window: '🧪', fungal_risk: '🍄',
                            }
                            return (
                              <div key={idx} className={`p-4 rounded-xl border-2 ${(severityStyles as any)[insight.severity] || severityStyles.info}`}>
                                <div className="flex items-center gap-2 mb-2">
                                  <span className="text-lg">{icons[insight.type] || 'ℹ️'}</span>
                                  <h4 className="font-semibold text-sm capitalize">{insight.type.replace(/_/g, ' ')}</h4>
                                </div>
                                <p className="text-xs text-gray-600 dark:text-gray-400">{insight.message}</p>
                              </div>
                            )
                          })}
                        </div>
                      )}

                      {/* Summary stats */}
                      {agInsights.agriculture_summary && (
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                          <div className="p-3 rounded-lg bg-blue-50 dark:bg-blue-950/30 text-center">
                            <p className="text-xl font-bold text-blue-700">{agInsights.agriculture_summary.total_rain_10d_mm?.toFixed(1) ?? '--'} mm</p>
                            <p className="text-xs text-gray-500">Total Rainfall ({agInsights.agriculture_summary.rainy_days ?? 0} rainy days)</p>
                          </div>
                          <div className="p-3 rounded-lg bg-red-50 dark:bg-red-950/30 text-center">
                            <p className="text-xl font-bold text-red-600">{agInsights.agriculture_summary.max_temperature_c?.toFixed(1) ?? '--'}°C</p>
                            <p className="text-xs text-gray-500">Max Temperature</p>
                          </div>
                          <div className="p-3 rounded-lg bg-cyan-50 dark:bg-cyan-950/30 text-center">
                            <p className="text-xl font-bold text-cyan-700">{agInsights.agriculture_summary.min_temperature_c?.toFixed(1) ?? '--'}°C</p>
                            <p className="text-xs text-gray-500">Min Temperature</p>
                          </div>
                          <div className="p-3 rounded-lg bg-green-50 dark:bg-green-950/30 text-center">
                            <p className="text-xl font-bold text-green-700 capitalize">{agInsights.agriculture_summary.crop ?? 'General'}</p>
                            <p className="text-xs text-gray-500">Crop Focus</p>
                          </div>
                        </div>
                      )}

                      {/* Legacy format support */}
                      {!agInsights.insights && (
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {/* Spray Window */}
                        {agInsights.spray_window && (
                          <div className={`p-4 rounded-xl border-2 ${agInsights.spray_window.suitable ? 'border-green-200 bg-green-50 dark:bg-green-950/30 dark:border-green-800' : 'border-red-200 bg-red-50 dark:bg-red-950/30 dark:border-red-800'}`}>
                            <div className="flex items-center gap-2 mb-2">
                              <span className="text-lg">{agInsights.spray_window.suitable ? '✅' : '❌'}</span>
                              <h4 className="font-semibold text-sm">Spray Window</h4>
                            </div>
                            <p className="text-xs text-gray-600 dark:text-gray-400">
                              {agInsights.spray_window.reason || (agInsights.spray_window.suitable ? 'Conditions are suitable for spraying' : 'Not recommended — check wind/rain')}
                            </p>
                          </div>
                        )}

                        {/* Planting Window */}
                        {agInsights.planting_window && (
                          <div className={`p-4 rounded-xl border-2 ${agInsights.planting_window.suitable ? 'border-green-200 bg-green-50 dark:bg-green-950/30 dark:border-green-800' : 'border-amber-200 bg-amber-50 dark:bg-amber-950/30 dark:border-amber-800'}`}>
                            <div className="flex items-center gap-2 mb-2">
                              <span className="text-lg">{agInsights.planting_window.suitable ? '🌱' : '⏳'}</span>
                              <h4 className="font-semibold text-sm">Planting Window</h4>
                            </div>
                            <p className="text-xs text-gray-600 dark:text-gray-400">
                              {agInsights.planting_window.reason || 'Check soil temperature and moisture levels'}
                            </p>
                          </div>
                        )}

                        {/* Drought Risk */}
                        {agInsights.drought_risk !== undefined && (
                          <div className={`p-4 rounded-xl border-2 ${agInsights.drought_risk === 'low' ? 'border-green-200 bg-green-50 dark:bg-green-950/30 dark:border-green-800' : agInsights.drought_risk === 'moderate' ? 'border-amber-200 bg-amber-50 dark:bg-amber-950/30 dark:border-amber-800' : 'border-red-200 bg-red-50 dark:bg-red-950/30 dark:border-red-800'}`}>
                            <div className="flex items-center gap-2 mb-2">
                              <span className="text-lg">{agInsights.drought_risk === 'low' ? '💧' : agInsights.drought_risk === 'moderate' ? '⚠️' : '🔥'}</span>
                              <h4 className="font-semibold text-sm">Drought Risk: {agInsights.drought_risk}</h4>
                            </div>
                            <p className="text-xs text-gray-600 dark:text-gray-400">
                              {agInsights.drought_message || `Current drought risk is ${agInsights.drought_risk}`}
                            </p>
                          </div>
                        )}

                        {/* Heat Stress */}
                        {agInsights.heat_stress !== undefined && (
                          <div className={`p-4 rounded-xl border-2 ${!agInsights.heat_stress ? 'border-green-200 bg-green-50 dark:bg-green-950/30 dark:border-green-800' : 'border-red-200 bg-red-50 dark:bg-red-950/30 dark:border-red-800'}`}>
                            <div className="flex items-center gap-2 mb-2">
                              <span className="text-lg">{agInsights.heat_stress ? '🌡️' : '✅'}</span>
                              <h4 className="font-semibold text-sm">Heat Stress</h4>
                            </div>
                            <p className="text-xs text-gray-600 dark:text-gray-400">
                              {agInsights.heat_stress ? 'High temperatures may stress crops — consider shade netting' : 'No heat stress detected'}
                            </p>
                          </div>
                        )}

                        {/* Bloom Risk */}
                        {agInsights.bloom_risk && (
                          <div className={`p-4 rounded-xl border-2 ${agInsights.bloom_risk.level === 'low' ? 'border-green-200 bg-green-50 dark:bg-green-950/30 dark:border-green-800' : agInsights.bloom_risk.level === 'moderate' ? 'border-amber-200 bg-amber-50 dark:bg-amber-950/30 dark:border-amber-800' : 'border-red-200 bg-red-50 dark:bg-red-950/30 dark:border-red-800'}`}>
                            <div className="flex items-center gap-2 mb-2">
                              <span className="text-lg">🌸</span>
                              <h4 className="font-semibold text-sm">Bloom Risk: {agInsights.bloom_risk.level}</h4>
                            </div>
                            <p className="text-xs text-gray-600 dark:text-gray-400">
                              {agInsights.bloom_risk.message || `Algal bloom risk is ${agInsights.bloom_risk.level}`}
                            </p>
                          </div>
                        )}

                        {/* Irrigation Advisory */}
                        {agInsights.irrigation_needed !== undefined && (
                          <div className={`p-4 rounded-xl border-2 ${agInsights.irrigation_needed ? 'border-blue-200 bg-blue-50 dark:bg-blue-950/30 dark:border-blue-800' : 'border-green-200 bg-green-50 dark:bg-green-950/30 dark:border-green-800'}`}>
                            <div className="flex items-center gap-2 mb-2">
                              <span className="text-lg">{agInsights.irrigation_needed ? '💦' : '✅'}</span>
                              <h4 className="font-semibold text-sm">Irrigation</h4>
                            </div>
                            <p className="text-xs text-gray-600 dark:text-gray-400">
                              {agInsights.irrigation_needed ? 'Irrigation recommended based on forecast' : 'Sufficient rainfall expected — no irrigation needed'}
                            </p>
                          </div>
                        )}
                      </div>
                      )}
                    </CardContent>
                  </Card>
                )}

                {/* Historical Weather Chart */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <BarChart3 className="h-5 w-5 text-purple-600" />
                      Weather History (Last 30 Days)
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {dashboardData?.climate_history && dashboardData.climate_history.length > 0 ? (
                      <ResponsiveContainer width="100%" height={300}>
                        <LineChart data={dashboardData.climate_history}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis 
                            dataKey="date" 
                            tick={{ fontSize: 12 }}
                            tickFormatter={(value) => new Date(value).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                          />
                          <YAxis yAxisId="left" label={{ value: 'Temp (°C)', angle: -90, position: 'insideLeft' }} />
                          <YAxis yAxisId="right" orientation="right" label={{ value: 'Rain (mm)', angle: 90, position: 'insideRight' }} />
                          <Tooltip labelFormatter={(value) => new Date(value).toLocaleDateString()} />
                          <Legend />
                          <Line 
                            yAxisId="left"
                            type="monotone" 
                            dataKey="temperature" 
                            stroke="#ef4444" 
                            name="Temperature (°C)"
                            strokeWidth={2}
                          />
                          <Line 
                            yAxisId="right"
                            type="monotone" 
                            dataKey="rainfall" 
                            stroke="#3b82f6" 
                            name="Rainfall (mm)"
                            strokeWidth={2}
                          />
                        </LineChart>
                      </ResponsiveContainer>
                    ) : (
                      <div className="h-[300px] flex items-center justify-center text-gray-500">
                        No historical weather data available
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>
              )}

              {/* Alerts Tab — Enhanced with alert type distinction */}
              {selectedTab === 'chat' && (
                <ChatPage />
              )}

              {selectedTab === 'alerts' && (
              <div className="space-y-6">
                {/* Extreme event banner */}
                {dashboardData?.recent_alerts?.some((a: any) => 
                  a.alert_type === 'extreme_event' || a.type === 'extreme_event' || a.severity === 'critical'
                ) && (
                  <div className="p-4 rounded-xl bg-red-100 dark:bg-red-950/40 border-2 border-red-300 dark:border-red-700 flex items-start gap-3">
                    <ShieldAlert className="h-6 w-6 text-red-600 mt-0.5 flex-shrink-0" />
                    <div>
                      <h4 className="font-bold text-red-700 dark:text-red-400">Extreme Weather Event Detected</h4>
                      <p className="text-sm text-red-600 dark:text-red-500 mt-1">
                        One or more critical weather events are impacting your area. Review red-flagged alerts below for details.
                      </p>
                    </div>
                  </div>
                )}

                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Bell className="h-5 w-5 text-orange-600" />
                      Recent Alerts
                    </CardTitle>
                    <CardDescription>
                      Smart alerts from satellite data, IoT sensors, weather, and AI analysis
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    {dashboardData?.recent_alerts && dashboardData.recent_alerts.length > 0 ? (
                      <div className="space-y-3">
                        {dashboardData.recent_alerts.map((alert: any, index: number) => {
                          // Determine alert styling based on type/severity
                          const alertType = alert.alert_type || alert.type || 'info'
                          const severity = alert.severity || 'info'
                          
                          const getAlertIcon = () => {
                            if (alertType === 'extreme_event' || severity === 'critical') return '⛔'
                            if (alertType === 'disease_detection') return '🦠'
                            if (alertType === 'condition' || alertType === 'condition_alert') return '📊'
                            if (alertType === 'rag_smart_alert' || alertType === 'smart_alert') return '🤖'
                            if (alertType === 'warning') return '⚠️'
                            if (alertType === 'success') return '✅'
                            return '🔔'
                          }

                          const getBorderColor = () => {
                            if (alertType === 'extreme_event' || severity === 'critical') return 'border-l-red-600 bg-red-50 dark:bg-red-950/20'
                            if (alertType === 'disease_detection') return 'border-l-purple-500 bg-purple-50 dark:bg-purple-950/20'
                            if (alertType === 'rag_smart_alert' || alertType === 'smart_alert') return 'border-l-cyan-500 bg-cyan-50 dark:bg-cyan-950/20'
                            if (alertType === 'warning' || severity === 'warning') return 'border-l-orange-500 bg-orange-50 dark:bg-orange-950/20'
                            if (alertType === 'success') return 'border-l-green-500 bg-green-50 dark:bg-green-950/20'
                            return 'border-l-blue-500 bg-blue-50 dark:bg-blue-950/20'
                          }

                          const getSeverityBadge = () => {
                            if (severity === 'critical') return <Badge variant="destructive" className="text-[10px]">Critical</Badge>
                            if (severity === 'warning') return <Badge className="text-[10px] bg-amber-500">Warning</Badge>
                            if (severity === 'info') return <Badge variant="secondary" className="text-[10px]">Info</Badge>
                            return null
                          }

                          return (
                            <div
                              key={index}
                              className={`p-4 border-l-4 rounded-lg ${getBorderColor()}`}
                            >
                              <div className="flex items-start justify-between gap-3">
                                <div className="flex-1">
                                  <div className="flex items-center gap-2 mb-1">
                                    <span className="text-lg">{getAlertIcon()}</span>
                                    <h4 className="font-semibold">{alert.title}</h4>
                                    {getSeverityBadge()}
                                  </div>
                                  <p className="text-sm text-gray-600 dark:text-gray-400">
                                    {alert.message}
                                  </p>
                                  <div className="flex items-center gap-3 mt-2">
                                    <p className="text-xs text-gray-500">
                                      {alert.timestamp ? new Date(alert.timestamp).toLocaleString() : 'Just now'}
                                    </p>
                                    {alert.channel && (
                                      <span className="text-xs text-gray-400">via {alert.channel}</span>
                                    )}
                                  </div>
                                </div>
                              </div>
                            </div>
                          )
                        })}
                      </div>
                    ) : (
                      <div className="text-center py-12 text-gray-500">
                        <Bell className="h-12 w-12 mx-auto mb-4 opacity-50" />
                        <p>No alerts yet.</p>
                        <p className="text-sm mt-2">You&apos;ll be notified about bloom events, weather extremes, crop diseases, and IoT sensor anomalies.</p>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>
              )}
            </div>

            {/* Quick Actions */}
            <div className="mt-10 mb-4">
              <h2 className="text-lg font-semibold text-gray-700 dark:text-gray-300 flex items-center gap-2 mb-4">
                <Zap className="h-5 w-5 text-amber-500" />
                Quick Actions
              </h2>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
                <Card className="group hover:shadow-lg hover:border-green-300 dark:hover:border-green-700 transition-all cursor-pointer border-2 border-transparent" onClick={() => setSelectedTab('chat')}>
                  <CardContent className="pt-5 pb-4 text-center">
                    <div className="w-12 h-12 mx-auto mb-3 rounded-xl bg-green-100 dark:bg-green-900/40 flex items-center justify-center group-hover:scale-110 transition-transform">
                      <MessageSquare className="h-6 w-6 text-green-600" />
                    </div>
                    <p className="font-semibold text-sm">Chat with Flora</p>
                    <p className="text-xs text-gray-500 mt-1">AI farming assistant</p>
                  </CardContent>
                </Card>

                <Card className="group hover:shadow-lg hover:border-blue-300 dark:hover:border-blue-700 transition-all cursor-pointer border-2 border-transparent" onClick={() => setSelectedTab('bloom')}>
                  <CardContent className="pt-5 pb-4 text-center">
                    <div className="w-12 h-12 mx-auto mb-3 rounded-xl bg-blue-100 dark:bg-blue-900/40 flex items-center justify-center group-hover:scale-110 transition-transform">
                      <Calendar className="h-6 w-6 text-blue-600" />
                    </div>
                    <p className="font-semibold text-sm">Crop Calendar</p>
                    <p className="text-xs text-gray-500 mt-1">Planting schedule</p>
                  </CardContent>
                </Card>

                <Link href="/disease-detection" className="block">
                  <Card className="group hover:shadow-lg hover:border-purple-300 dark:hover:border-purple-700 transition-all cursor-pointer h-full border-2 border-transparent">
                    <CardContent className="pt-5 pb-4 text-center">
                      <div className="w-12 h-12 mx-auto mb-3 rounded-xl bg-purple-100 dark:bg-purple-900/40 flex items-center justify-center group-hover:scale-110 transition-transform">
                        <Camera className="h-6 w-6 text-purple-600" />
                      </div>
                      <p className="font-semibold text-sm">Disease Detection</p>
                      <p className="text-xs text-gray-500 mt-1">Scan your crops</p>
                    </CardContent>
                  </Card>
                </Link>

                <Link href="/agrovet" className="block">
                  <Card className="group hover:shadow-lg hover:border-amber-300 dark:hover:border-amber-700 transition-all cursor-pointer h-full border-2 border-transparent">
                    <CardContent className="pt-5 pb-4 text-center">
                      <div className="w-12 h-12 mx-auto mb-3 rounded-xl bg-amber-100 dark:bg-amber-900/40 flex items-center justify-center group-hover:scale-110 transition-transform">
                        <span className="text-xl">🧪</span>
                      </div>
                      <p className="font-semibold text-sm">Agrovet Shop</p>
                      <p className="text-xs text-gray-500 mt-1">Seeds & fertilizers</p>
                    </CardContent>
                  </Card>
                </Link>

                <Link href="/marketplace" className="block">
                  <Card className="group hover:shadow-lg hover:border-teal-300 dark:hover:border-teal-700 transition-all cursor-pointer h-full border-2 border-transparent">
                    <CardContent className="pt-5 pb-4 text-center">
                      <div className="w-12 h-12 mx-auto mb-3 rounded-xl bg-teal-100 dark:bg-teal-900/40 flex items-center justify-center group-hover:scale-110 transition-transform">
                        <span className="text-xl">🏪</span>
                      </div>
                      <p className="font-semibold text-sm">Marketplace</p>
                      <p className="text-xs text-gray-500 mt-1">Buy & sell produce</p>
                    </CardContent>
                  </Card>
                </Link>
              </div>
            </div>
          </>
        )}
      </main>
      </div>
    </div>
  )
}

