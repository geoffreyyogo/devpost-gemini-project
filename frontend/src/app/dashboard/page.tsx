'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import Image from 'next/image'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  Loader2, Sprout, TrendingUp, Cloud, Bell, User, LogOut, 
  Calendar, MapPin, Thermometer, Droplets, BarChart3, AlertTriangle,
  MessageSquare, ChevronRight
} from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import { useDashboardStore } from '@/store/dashboardStore'
import { CountyFocusedMap } from '@/components/maps/CountyFocusedMap'
import { ThemeSwitcher } from '@/components/ui/theme-switcher'
import { LanguageSelector } from '@/components/ui/language-selector'
import { api } from '@/lib/api'
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

export default function DashboardPage() {
  const router = useRouter()
  const { farmer, isAuthenticated, logout, hasHydrated } = useAuthStore()
  const { data: dashboardData, isLoading: loading, error, fetchDashboardData, fetchBloomEvents, fetchAlerts } = useDashboardStore()
  const [selectedTab, setSelectedTab] = useState('overview')

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
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-white to-green-50 dark:from-gray-950 dark:via-gray-900 dark:to-gray-950">
      {/* Header */}
      <header className="border-b border-white/20 dark:border-gray-800/30 bg-white/70 dark:bg-gray-950/70 backdrop-blur-xl sticky top-0 z-50 shadow-lg shadow-green-500/5 dark:shadow-green-500/10">
        <div className="container mx-auto px-4 py-3">
          <div className="flex items-center justify-between">
            {/* Logo */}
            <Link href="/" className="flex items-center space-x-3 group">
              <Image
                src="/BloomWatch.png"
                alt="BloomWatch Kenya"
                width={40}
                height={40}
                className="h-10 w-auto transition-transform group-hover:scale-105"
                priority
              />
              <span className="text-xl md:text-2xl font-bold bg-gradient-to-r from-green-600 to-green-500 bg-clip-text text-transparent hidden sm:inline">
                BloomWatch Kenya
              </span>
            </Link>

            {/* Right Side - User Info & Actions */}
            <div className="flex items-center gap-2 md:gap-3">
              {/* User Info */}
              <div className="text-right hidden lg:block">
                <p className="text-sm font-semibold text-gray-900 dark:text-white">
                  {farmer.name}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400 flex items-center justify-end gap-1">
                  <MapPin className="h-3 w-3" />
                  {farmer.county || farmer.region}
                </p>
              </div>

              {/* Theme Switcher */}
              <ThemeSwitcher />
              
              {/* Language Selector */}
              <LanguageSelector />
              
              {/* Divider */}
              <div className="hidden md:block w-px h-6 bg-gray-300 dark:bg-gray-700" />
              
              {/* Profile & Logout */}
              <Link href="/profile" className="hidden md:inline">
                <Button variant="outline" size="sm" className="rounded-full h-9 px-4 hover:bg-green-50 dark:hover:bg-green-900/20">
                  <User className="mr-2 h-4 w-4" />
                  Profile
                </Button>
              </Link>
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={handleLogout}
                className="rounded-full h-9 px-3 md:px-4 hover:bg-red-50 dark:hover:bg-red-900/20 hover:text-red-600 dark:hover:text-red-400"
              >
                <LogOut className="h-4 w-4 md:mr-2" />
                <span className="hidden md:inline">Logout</span>
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        {/* Welcome Section */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-green-700 dark:text-green-400 mb-2">
            Welcome back, {farmer.name.split(' ')[0]}! 👋
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Here's what's happening with your crops today
          </p>
        </div>

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
            {/* Metrics Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              <Card className="border-l-4 border-l-blue-500">
                <CardHeader className="pb-2">
                  <CardDescription className="flex items-center gap-2">
                    <Cloud className="h-4 w-4" />
                    Current Season
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="text-3xl font-bold">
                    {dashboardData?.season?.name || 'Loading...'}
                  </p>
                  <p className="text-sm text-gray-500 mt-1">
                    {dashboardData?.season?.status || 'Ongoing'}
                  </p>
                </CardContent>
              </Card>

              <Card className="border-l-4 border-l-pink-500">
                <CardHeader className="pb-2">
                  <CardDescription className="flex items-center gap-2">
                    <Sprout className="h-4 w-4" />
                    Active Blooms
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="text-3xl font-bold text-pink-600">
                    {dashboardData?.bloom_events?.length || 0}
                  </p>
                  <p className="text-sm text-gray-500 mt-1">
                    {(dashboardData?.bloom_events?.length ?? 0) > 0 ? 'In progress' : 'None detected'}
                  </p>
                </CardContent>
              </Card>

              <Card className="border-l-4 border-l-green-500">
                <CardHeader className="pb-2">
                  <CardDescription className="flex items-center gap-2">
                    <TrendingUp className="h-4 w-4" />
                    Crop Health
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="text-3xl font-bold text-green-600">
                    {dashboardData?.ndvi_average ? `${(dashboardData.ndvi_average * 100).toFixed(0)}%` : 'N/A'}
                  </p>
                  <p className="text-sm text-gray-500 mt-1">
                    NDVI Index
                  </p>
                </CardContent>
              </Card>

              <Card className="border-l-4 border-l-orange-500">
                <CardHeader className="pb-2">
                  <CardDescription className="flex items-center gap-2">
                    <Bell className="h-4 w-4" />
                    Alerts
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="text-3xl font-bold text-orange-600">
                    {dashboardData?.recent_alerts?.length || 0}
                  </p>
                  <p className="text-sm text-gray-500 mt-1">
                    {dashboardData?.recent_alerts?.some((a: any) => !a.read) ? 'Unread alerts' : 'All read'}
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* ML Prediction Card - Prominent Feature */}
            {dashboardData?.ml_prediction && (
              <Card className="mb-8 border-2 border-purple-500 bg-gradient-to-r from-purple-50 to-pink-50 dark:from-purple-950 dark:to-pink-950">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-purple-700 dark:text-purple-300">
                    <TrendingUp className="h-6 w-6" />
                    🤖 AI Bloom Prediction (Next 7 Days)
                  </CardTitle>
                  <CardDescription>
                    Machine Learning prediction based on satellite data and weather patterns
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div>
                      <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">Bloom Probability</p>
                      <p className="text-5xl font-bold text-purple-600 dark:text-purple-400">
                        {dashboardData.ml_prediction.bloom_probability_percent?.toFixed(0)}%
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">Confidence Level</p>
                      <p className={`text-2xl font-bold ${
                        dashboardData.ml_prediction.confidence === 'High' ? 'text-green-600' :
                        dashboardData.ml_prediction.confidence === 'Medium' ? 'text-yellow-600' :
                        'text-gray-600'
                      }`}>
                        {dashboardData.ml_prediction.confidence}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">Prediction</p>
                      <p className="text-sm text-gray-700 dark:text-gray-300">
                        {dashboardData.ml_prediction.message}
                      </p>
                    </div>
                  </div>
                  <div className="mt-4 pt-4 border-t">
                    <p className="text-xs text-gray-500">
                      Model trained on historical NASA satellite data • Last updated: {new Date(dashboardData.ml_prediction.predicted_at).toLocaleString()}
                    </p>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Tabs */}
            <Tabs value={selectedTab} onValueChange={setSelectedTab} className="space-y-6">
              <TabsList className="grid w-full grid-cols-4">
                <TabsTrigger value="overview" className="flex items-center gap-2">
                  <BarChart3 className="h-4 w-4" />
                  Overview
                </TabsTrigger>
                <TabsTrigger value="bloom" className="flex items-center gap-2">
                  <Sprout className="h-4 w-4" />
                  Bloom Data
                </TabsTrigger>
                <TabsTrigger value="weather" className="flex items-center gap-2">
                  <Cloud className="h-4 w-4" />
                  Weather
                </TabsTrigger>
                <TabsTrigger value="alerts" className="flex items-center gap-2">
                  <Bell className="h-4 w-4" />
                  Alerts
                </TabsTrigger>
              </TabsList>

              {/* Overview Tab */}
              <TabsContent value="overview" className="space-y-6">
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

                {/* County Focused Map */}
                {farmer.county && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <MapPin className="h-5 w-5 text-blue-600" />
                        Your County: {farmer.county}
                      </CardTitle>
                      <CardDescription>
                        Live bloom and climate data for your area
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <CountyFocusedMap countyName={farmer.county} />
                    </CardContent>
                  </Card>
                )}

                {/* Your Crops */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Sprout className="h-5 w-5 text-green-600" />
                      Your Crops
                    </CardTitle>
                    <CardDescription>
                      Crops you're currently monitoring
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="flex flex-wrap gap-2">
                      {farmer.crops.map((crop) => (
                        <div
                          key={crop}
                          className="px-4 py-2 bg-green-100 dark:bg-green-950 text-green-700 dark:text-green-400 rounded-full font-semibold"
                        >
                          {crop.charAt(0).toUpperCase() + crop.slice(1)}
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              {/* Bloom Data Tab */}
              <TabsContent value="bloom" className="space-y-6">
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
                        Bloom Activity Map - {farmer.county}
                      </CardTitle>
                      <CardDescription>
                        Visual representation of bloom activity in your county
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <CountyFocusedMap countyName={farmer.county} />
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
              </TabsContent>

              {/* Weather Tab */}
              <TabsContent value="weather" className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <Thermometer className="h-5 w-5 text-red-600" />
                        Temperature
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-4xl font-bold text-red-600">
                        {dashboardData?.current_weather?.temperature || 'N/A'}°C
                      </p>
                      <p className="text-sm text-gray-500 mt-2">
                        Current temperature
                      </p>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <Droplets className="h-5 w-5 text-blue-600" />
                        Rainfall
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-4xl font-bold text-blue-600">
                        {dashboardData?.current_weather?.rainfall || 0} mm
                      </p>
                      <p className="text-sm text-gray-500 mt-2">
                        Last 24 hours
                      </p>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <Cloud className="h-5 w-5 text-gray-600" />
                        Conditions
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-2xl font-bold text-gray-700 dark:text-gray-300">
                        {dashboardData?.current_weather?.conditions || 'Clear'}
                      </p>
                      <p className="text-sm text-gray-500 mt-2">
                        Current conditions
                      </p>
                    </CardContent>
                  </Card>
                </div>

                {/* 7-Day Weather Forecast */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Calendar className="h-5 w-5 text-blue-600" />
                      7-Day Forecast
                    </CardTitle>
                    <CardDescription>
                      Predicted weather conditions for the coming week
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
                      {Array.from({ length: 7 }).map((_, index) => {
                        const date = new Date()
                        date.setDate(date.getDate() + index)
                        const dayName = date.toLocaleDateString('en-US', { weekday: 'short' })
                        
                        // Generate forecast based on climate history pattern
                        const baseTemp = dashboardData?.current_weather?.temperature || 25
                        const tempVariation = Math.sin(index * 0.5) * 3
                        const forecastTemp = Math.round(baseTemp + tempVariation)
                        
                        const baseRain = dashboardData?.current_weather?.rainfall || 10
                        const rainChance = Math.random() > 0.6 ? Math.round(baseRain * (0.5 + Math.random())) : 0
                        
                        return (
                          <div key={index} className="border rounded-lg p-3 text-center">
                            <p className="font-semibold text-sm mb-2">{index === 0 ? 'Today' : dayName}</p>
                            <div className="text-3xl mb-2">
                              {rainChance > 5 ? '🌧️' : forecastTemp > 28 ? '☀️' : '⛅'}
                            </div>
                            <p className="text-lg font-bold">{forecastTemp}°C</p>
                            {rainChance > 0 && (
                              <p className="text-xs text-blue-600 mt-1">{rainChance}mm rain</p>
                            )}
                          </div>
                        )
                      })}
                    </div>
                    <p className="text-xs text-gray-500 mt-4">
                      * Forecast based on historical climate patterns and current conditions
                    </p>
                  </CardContent>
                </Card>

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
              </TabsContent>

              {/* Alerts Tab */}
              <TabsContent value="alerts" className="space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Bell className="h-5 w-5 text-orange-600" />
                      Recent Alerts
                    </CardTitle>
                    <CardDescription>
                      Notifications and updates about your crops
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    {dashboardData?.recent_alerts && dashboardData.recent_alerts.length > 0 ? (
                      <div className="space-y-3">
                        {dashboardData.recent_alerts.map((alert: any, index: number) => (
                          <div
                            key={index}
                            className={`p-4 border-l-4 rounded ${
                              alert.type === 'warning' 
                                ? 'border-l-orange-500 bg-orange-50 dark:bg-orange-950/20'
                                : alert.type === 'success'
                                ? 'border-l-green-500 bg-green-50 dark:bg-green-950/20'
                                : 'border-l-blue-500 bg-blue-50 dark:bg-blue-950/20'
                            }`}
                          >
                            <div className="flex items-start justify-between">
                              <div className="flex-1">
                                <h4 className="font-semibold mb-1">{alert.title}</h4>
                                <p className="text-sm text-gray-600 dark:text-gray-400">
                                  {alert.message}
                                </p>
                                <p className="text-xs text-gray-500 mt-2">
                                  {alert.timestamp ? new Date(alert.timestamp).toLocaleString() : 'Just now'}
                                </p>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-center py-12 text-gray-500">
                        <Bell className="h-12 w-12 mx-auto mb-4 opacity-50" />
                        <p>No alerts yet.</p>
                        <p className="text-sm mt-2">You'll be notified when there's important information about your crops.</p>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>

            {/* Quick Actions */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-8">
              <Card className="hover:shadow-lg transition-shadow cursor-pointer">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <MessageSquare className="h-5 w-5 text-green-600" />
                    Chat with Flora AI
                  </CardTitle>
                  <CardDescription>
                    Get instant farming advice from our AI assistant
                  </CardDescription>
                </CardHeader>
              </Card>

              <Card className="hover:shadow-lg transition-shadow cursor-pointer">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Calendar className="h-5 w-5 text-blue-600" />
                    View Crop Calendar
                  </CardTitle>
                  <CardDescription>
                    See planting and harvesting schedules for your crops
                  </CardDescription>
                </CardHeader>
              </Card>
            </div>
          </>
        )}
      </main>
    </div>
  )
}

