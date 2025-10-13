'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  Loader2, Users, TrendingUp, MessageSquare, Bell, Shield,
  Search, Filter, Plus, Send, Trash2, Eye, BarChart3,
  UserPlus, PhoneCall, Mail, MapPin, Sprout, Calendar,
  AlertCircle, CheckCircle, Clock, ArrowLeft, LogOut,
  Download, RefreshCw
} from 'lucide-react'
import { useToast } from '@/components/ui/use-toast'
import { useAuthStore } from '@/store/authStore'
import { useAdminStore } from '@/store/adminStore'
import { api } from '@/lib/api'
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

export default function AdminDashboardPage() {
  const router = useRouter()
  const { toast } = useToast()
  const { farmer, isAuthenticated, logout, hasHydrated } = useAuthStore()
  const { 
    farmers, 
    statistics, 
    recentRegistrations,
    isLoading,
    error,
    fetchFarmers,
    fetchStatistics,
    fetchRecentRegistrations,
    deleteFarmer: deleteFarmerFromStore,
    sendAlert
  } = useAdminStore()

  const [selectedTab, setSelectedTab] = useState('overview')
  const [searchQuery, setSearchQuery] = useState('')
  const [regionFilter, setRegionFilter] = useState('all')
  const [sourceFilter, setSourceFilter] = useState('all')
  
  // Alert form state
  const [alertTarget, setAlertTarget] = useState('all')
  const [alertRegion, setAlertRegion] = useState('central')
  const [alertCrop, setAlertCrop] = useState('maize')
  const [alertType, setAlertType] = useState('bloom')
  const [customMessage, setCustomMessage] = useState('')
  const [sendingAlert, setSendingAlert] = useState(false)

  // System management state
  const [fetchingData, setFetchingData] = useState(false)
  const [retrainingModel, setRetrainingModel] = useState(false)
  const [schedulerStatus, setSchedulerStatus] = useState<any>(null)

  // Check authentication and admin role - wait for hydration first
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
    
    // Check admin privileges
    if (!farmer.is_admin) {
      console.log('Admin check failed. Farmer data:', farmer)
      toast({
        title: 'Access Denied',
        description: 'You do not have admin privileges.',
        variant: 'destructive',
      })
      router.push('/dashboard')
      return
    }
    
    // Fetch admin data
    fetchStatistics()
    fetchRecentRegistrations(7)
    fetchFarmers()
  }, [hasHydrated, isAuthenticated, farmer, router, fetchStatistics, fetchRecentRegistrations, fetchFarmers, toast])

  const handleLogout = async () => {
    await logout()
    router.push('/')
  }

  const handleDeleteFarmer = async (farmerId: string) => {
    if (!confirm('Are you sure you want to delete this farmer?')) return

    try {
      await deleteFarmerFromStore(farmerId)
      toast({
        title: 'Farmer Deleted',
        description: 'The farmer has been removed from the system.',
      })
      fetchFarmers()
      fetchStatistics()
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to delete farmer.',
        variant: 'destructive',
      })
    }
  }

  const handleSendAlert = async () => {
    setSendingAlert(true)
    
    try {
      const alertData = {
        target: alertTarget,
        target_value: alertTarget === 'region' ? alertRegion : alertTarget === 'crop' ? alertCrop : null,
        alert_type: alertType,
        message: alertType === 'custom' ? customMessage : null,
      }
      
      await sendAlert(alertData)
      
      toast({
        title: 'Alert Sent! ✅',
        description: 'The alert has been sent to the selected farmers.',
      })
      
      // Reset form
      setCustomMessage('')
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to send alert.',
        variant: 'destructive',
      })
    } finally {
      setSendingAlert(false)
    }
  }

  // Filter farmers
  const filteredFarmers = farmers?.filter(f => {
    const matchesSearch = !searchQuery || 
      f.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      f.phone?.includes(searchQuery) ||
      f.region?.toLowerCase().includes(searchQuery.toLowerCase())
    
    const matchesRegion = regionFilter === 'all' || f.region === regionFilter
    const matchesSource = sourceFilter === 'all' || f.registered_via === sourceFilter
    
    return matchesSearch && matchesRegion && matchesSource
  })

  // Chart colors
  const COLORS = ['#16a34a', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899']

  if (!farmer || !farmer.is_admin) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-12 w-12 animate-spin text-green-600" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-50 dark:from-gray-950 dark:via-gray-900 dark:to-gray-950">
      {/* Header */}
      <header className="border-b bg-white/80 dark:bg-gray-950/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Shield className="h-8 w-8 text-purple-600" />
              <div>
                <h1 className="text-2xl font-bold text-purple-600">Admin Dashboard</h1>
                <p className="text-sm text-gray-500">BloomWatch Kenya Management</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <Link href="/dashboard">
                <Button variant="outline" size="sm">
                  <ArrowLeft className="mr-2 h-4 w-4" />
                  Back to Dashboard
                </Button>
              </Link>
              <Button variant="ghost" size="sm" onClick={handleLogout}>
                <LogOut className="mr-2 h-4 w-4" />
                Logout
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        {isLoading && !statistics ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="h-12 w-12 animate-spin text-purple-600" />
          </div>
        ) : (
          <>
            {/* Tabs */}
            <Tabs value={selectedTab} onValueChange={setSelectedTab} className="space-y-6">
              <TabsList className="grid w-full grid-cols-6">
                <TabsTrigger value="overview" className="flex items-center gap-2">
                  <BarChart3 className="h-4 w-4" />
                  Overview
                </TabsTrigger>
                <TabsTrigger value="farmers" className="flex items-center gap-2">
                  <Users className="h-4 w-4" />
                  Farmers
                </TabsTrigger>
                <TabsTrigger value="alerts" className="flex items-center gap-2">
                  <Send className="h-4 w-4" />
                  Send Alerts
                </TabsTrigger>
                <TabsTrigger value="registrations" className="flex items-center gap-2">
                  <UserPlus className="h-4 w-4" />
                  Registrations
                </TabsTrigger>
                <TabsTrigger value="analytics" className="flex items-center gap-2">
                  <TrendingUp className="h-4 w-4" />
                  Analytics
                </TabsTrigger>
                <TabsTrigger value="system" className="flex items-center gap-2">
                  <RefreshCw className="h-4 w-4" />
                  System
                </TabsTrigger>
              </TabsList>

              {/* Overview Tab */}
              <TabsContent value="overview" className="space-y-6">
                {/* Metrics Cards */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                  <Card className="border-l-4 border-l-purple-500">
                    <CardHeader className="pb-2">
                      <CardDescription className="flex items-center gap-2">
                        <Users className="h-4 w-4" />
                        Total Farmers
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <p className="text-4xl font-bold text-purple-600">
                        {statistics?.total_farmers || 0}
                      </p>
                      <p className="text-sm text-gray-500 mt-1">
                        Registered farmers
                      </p>
                    </CardContent>
                  </Card>

                  <Card className="border-l-4 border-l-green-500">
                    <CardHeader className="pb-2">
                      <CardDescription className="flex items-center gap-2">
                        <CheckCircle className="h-4 w-4" />
                        Active Farmers
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <p className="text-4xl font-bold text-green-600">
                        {statistics?.active_farmers || 0}
                      </p>
                      <p className="text-sm text-gray-500 mt-1">
                        Currently active
                      </p>
                    </CardContent>
                  </Card>

                  <Card className="border-l-4 border-l-blue-500">
                    <CardHeader className="pb-2">
                      <CardDescription className="flex items-center gap-2">
                        <PhoneCall className="h-4 w-4" />
                        USSD Registrations
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <p className="text-4xl font-bold text-blue-600">
                        {statistics ? Math.floor(statistics.total_farmers * 0.3) : 0}
                      </p>
                      <p className="text-sm text-gray-500 mt-1">
                        Via *384*42434# (est.)
                      </p>
                    </CardContent>
                  </Card>

                  <Card className="border-l-4 border-l-orange-500">
                    <CardHeader className="pb-2">
                      <CardDescription className="flex items-center gap-2">
                        <Bell className="h-4 w-4" />
                        Alerts Sent
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <p className="text-4xl font-bold text-orange-600">
                        {statistics?.total_alerts_sent || 0}
                      </p>
                      <p className="text-sm text-gray-500 mt-1">
                        Total alerts
                      </p>
                    </CardContent>
                  </Card>
                </div>

                {/* Charts */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Farmers by Region */}
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <MapPin className="h-5 w-5 text-purple-600" />
                        Farmers by Region
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      {statistics?.farmers_by_region && Object.keys(statistics.farmers_by_region).length > 0 ? (
                        <ResponsiveContainer width="100%" height={300}>
                          <BarChart data={Object.entries(statistics.farmers_by_region).map(([region, count]) => ({
                            region: region.replace('_', ' ').toUpperCase(),
                            count
                          }))}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="region" tick={{ fontSize: 12 }} />
                            <YAxis />
                            <Tooltip />
                            <Bar dataKey="count" fill="#9333ea" />
                          </BarChart>
                        </ResponsiveContainer>
                      ) : (
                        <div className="h-[300px] flex items-center justify-center text-gray-500">
                          No regional data available
                        </div>
                      )}
                    </CardContent>
                  </Card>

                  {/* Registration Sources */}
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <TrendingUp className="h-5 w-5 text-green-600" />
                        Registration Sources
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      {statistics ? (
                        <ResponsiveContainer width="100%" height={300}>
                          <PieChart>
                            <Pie
                              data={[
                                { name: 'Web', value: statistics.web || 0 },
                                { name: 'USSD', value: statistics.ussd || 0 },
                                { name: 'Manual', value: (statistics.total || 0) - (statistics.web || 0) - (statistics.ussd || 0) },
                              ].filter(d => d.value > 0)}
                              cx="50%"
                              cy="50%"
                              labelLine={false}
                              label={(entry) => `${entry.name}: ${entry.value}`}
                              outerRadius={100}
                              fill="#8884d8"
                              dataKey="value"
                            >
                              {[0, 1, 2].map((index) => (
                                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                              ))}
                            </Pie>
                            <Tooltip />
                          </PieChart>
                        </ResponsiveContainer>
                      ) : (
                        <div className="h-[300px] flex items-center justify-center text-gray-500">
                          No data available
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </div>

                {/* Quick Actions */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <Button 
                    size="lg" 
                    className="h-20"
                    onClick={() => setSelectedTab('farmers')}
                  >
                    <Users className="mr-2 h-5 w-5" />
                    Manage Farmers
                  </Button>
                  <Button 
                    size="lg" 
                    className="h-20 bg-orange-600 hover:bg-orange-700"
                    onClick={() => setSelectedTab('alerts')}
                  >
                    <Send className="mr-2 h-5 w-5" />
                    Send Alerts
                  </Button>
                  <Button 
                    size="lg" 
                    className="h-20 bg-green-600 hover:bg-green-700"
                    onClick={() => {
                      fetchStatistics()
                      fetchFarmers()
                      fetchRecentRegistrations(7)
                    }}
                  >
                    <RefreshCw className="mr-2 h-5 w-5" />
                    Refresh Data
                  </Button>
                </div>
              </TabsContent>

              {/* Farmers Tab */}
              <TabsContent value="farmers" className="space-y-6">
                {/* Search and Filters */}
                <Card>
                  <CardHeader>
                    <CardTitle>Search & Filter Farmers</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div>
                        <Label htmlFor="search">Search</Label>
                        <div className="relative">
                          <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                          <Input
                            id="search"
                            placeholder="Name, phone, or region..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="pl-10"
                          />
                        </div>
                      </div>
                      <div>
                        <Label htmlFor="region">Region</Label>
                        <Select value={regionFilter} onValueChange={setRegionFilter}>
                          <SelectTrigger id="region">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="all">All Regions</SelectItem>
                            <SelectItem value="central">Central</SelectItem>
                            <SelectItem value="rift_valley">Rift Valley</SelectItem>
                            <SelectItem value="western">Western</SelectItem>
                            <SelectItem value="eastern">Eastern</SelectItem>
                            <SelectItem value="coast">Coast</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <div>
                        <Label htmlFor="source">Source</Label>
                        <Select value={sourceFilter} onValueChange={setSourceFilter}>
                          <SelectTrigger id="source">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="all">All Sources</SelectItem>
                            <SelectItem value="web">Web</SelectItem>
                            <SelectItem value="ussd">USSD</SelectItem>
                            <SelectItem value="manual">Manual</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                    <p className="text-sm text-gray-500 mt-4">
                      Found {filteredFarmers?.length || 0} farmers
                    </p>
                  </CardContent>
                </Card>

                {/* Farmers List */}
                <div className="space-y-4">
                  {filteredFarmers?.map((farmer) => (
                    <Card key={farmer._id}>
                      <CardContent className="pt-6">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-3 mb-3">
                              <div className="w-12 h-12 bg-green-100 dark:bg-green-950 rounded-full flex items-center justify-center">
                                <Users className="h-6 w-6 text-green-600" />
                              </div>
                              <div>
                                <h3 className="text-lg font-semibold">{farmer.name}</h3>
                                <p className="text-sm text-gray-500 flex items-center gap-2">
                                  <PhoneCall className="h-3 w-3" />
                                  {farmer.phone}
                                </p>
                              </div>
                            </div>
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                              <div>
                                <p className="text-gray-500">Region</p>
                                <p className="font-semibold flex items-center gap-1">
                                  <MapPin className="h-3 w-3" />
                                  {farmer.region?.replace('_', ' ').toUpperCase() || 'N/A'}
                                </p>
                              </div>
                              <div>
                                <p className="text-gray-500">Crops</p>
                                <p className="font-semibold flex items-center gap-1">
                                  <Sprout className="h-3 w-3" />
                                  {farmer.crops?.length || 0} types
                                </p>
                              </div>
                              <div>
                                <p className="text-gray-500">Source</p>
                                <p className="font-semibold uppercase">
                                  {farmer.registered_via || 'N/A'}
                                </p>
                              </div>
                              <div>
                                <p className="text-gray-500">Registered</p>
                                <p className="font-semibold flex items-center gap-1">
                                  <Calendar className="h-3 w-3" />
                                  {farmer.registered_at ? new Date(farmer.registered_at).toLocaleDateString() : 'N/A'}
                                </p>
                              </div>
                            </div>
                          </div>
                          <div className="flex flex-col gap-2">
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleDeleteFarmer(farmer._id!)}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </TabsContent>

              {/* Send Alerts Tab */}
              <TabsContent value="alerts" className="space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Send className="h-5 w-5 text-orange-600" />
                      Send Smart Alerts
                    </CardTitle>
                    <CardDescription>
                      Send notifications to farmers via SMS
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor="alert-target">Send To</Label>
                        <Select value={alertTarget} onValueChange={setAlertTarget}>
                          <SelectTrigger id="alert-target">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="all">All Farmers</SelectItem>
                            <SelectItem value="region">By Region</SelectItem>
                            <SelectItem value="crop">By Crop</SelectItem>
                            <SelectItem value="individual">Specific Farmer</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>

                      {alertTarget === 'region' && (
                        <div>
                          <Label htmlFor="alert-region">Select Region</Label>
                          <Select value={alertRegion} onValueChange={setAlertRegion}>
                            <SelectTrigger id="alert-region">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="central">Central</SelectItem>
                              <SelectItem value="rift_valley">Rift Valley</SelectItem>
                              <SelectItem value="western">Western</SelectItem>
                              <SelectItem value="eastern">Eastern</SelectItem>
                              <SelectItem value="coast">Coast</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                      )}

                      {alertTarget === 'crop' && (
                        <div>
                          <Label htmlFor="alert-crop">Select Crop</Label>
                          <Select value={alertCrop} onValueChange={setAlertCrop}>
                            <SelectTrigger id="alert-crop">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="maize">Maize</SelectItem>
                              <SelectItem value="beans">Beans</SelectItem>
                              <SelectItem value="coffee">Coffee</SelectItem>
                              <SelectItem value="tea">Tea</SelectItem>
                              <SelectItem value="wheat">Wheat</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                      )}
                    </div>

                    <div>
                      <Label htmlFor="alert-type">Alert Type</Label>
                      <Select value={alertType} onValueChange={setAlertType}>
                        <SelectTrigger id="alert-type">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="bloom">Bloom Detection</SelectItem>
                          <SelectItem value="weather">Weather Update</SelectItem>
                          <SelectItem value="custom">Custom Message</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    {alertType === 'custom' && (
                      <div>
                        <Label htmlFor="custom-message">Custom Message</Label>
                        <textarea
                          id="custom-message"
                          value={customMessage}
                          onChange={(e) => setCustomMessage(e.target.value)}
                          className="w-full min-h-[100px] p-3 border rounded-md"
                          maxLength={160}
                          placeholder="Enter your message (max 160 characters)"
                        />
                        <p className="text-sm text-gray-500 mt-1">
                          {customMessage.length}/160 characters
                        </p>
                      </div>
                    )}

                    <Button
                      onClick={handleSendAlert}
                      disabled={sendingAlert || (alertType === 'custom' && !customMessage)}
                      className="w-full bg-orange-600 hover:bg-orange-700"
                    >
                      {sendingAlert ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          Sending...
                        </>
                      ) : (
                        <>
                          <Send className="mr-2 h-4 w-4" />
                          Send Alert Now
                        </>
                      )}
                    </Button>
                  </CardContent>
                </Card>
              </TabsContent>

              {/* Registrations Tab */}
              <TabsContent value="registrations" className="space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <UserPlus className="h-5 w-5 text-green-600" />
                      Recent Registrations (Last 7 Days)
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {recentRegistrations && recentRegistrations.length > 0 ? (
                      <div className="space-y-3">
                        {recentRegistrations.map((farmer) => (
                          <div
                            key={farmer._id}
                            className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50 dark:hover:bg-gray-900"
                          >
                            <div className="flex items-center gap-3">
                              <div className="w-10 h-10 bg-green-100 dark:bg-green-950 rounded-full flex items-center justify-center">
                                <Users className="h-5 w-5 text-green-600" />
                              </div>
                              <div>
                                <p className="font-semibold">{farmer.name}</p>
                                <p className="text-sm text-gray-500">{farmer.phone}</p>
                              </div>
                            </div>
                            <div className="text-right">
                              <p className="text-sm font-semibold">
                                {farmer.region?.replace('_', ' ').toUpperCase()}
                              </p>
                              <p className="text-xs text-gray-500">
                                {farmer.registered_via?.toUpperCase()}
                              </p>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-center py-12 text-gray-500">
                        <UserPlus className="h-12 w-12 mx-auto mb-4 opacity-50" />
                        <p>No recent registrations</p>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>

              {/* Analytics Tab */}
              <TabsContent value="analytics" className="space-y-6">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <Card>
                    <CardHeader>
                      <CardTitle>Popular Crops</CardTitle>
                    </CardHeader>
                    <CardContent>
                      {statistics?.farmers_by_crop && Object.keys(statistics.farmers_by_crop).length > 0 ? (
                        <ResponsiveContainer width="100%" height={300}>
                          <BarChart data={Object.entries(statistics.farmers_by_crop).slice(0, 8).map(([crop, count]) => ({
                            crop: crop.charAt(0).toUpperCase() + crop.slice(1),
                            count
                          }))}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="crop" tick={{ fontSize: 12 }} />
                            <YAxis />
                            <Tooltip />
                            <Bar dataKey="count" fill="#16a34a" />
                          </BarChart>
                        </ResponsiveContainer>
                      ) : (
                        <div className="h-[300px] flex items-center justify-center text-gray-500">
                          No crop data available
                        </div>
                      )}
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle>Growth Trend</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="h-[300px] flex items-center justify-center text-gray-500">
                        <p>Growth analytics coming soon</p>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </TabsContent>

              {/* System Management Tab */}
              <TabsContent value="system" className="space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <RefreshCw className="h-5 w-5" />
                      System Data Management
                    </CardTitle>
                    <CardDescription>
                      Manually trigger NASA data fetching and ML model retraining
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    {/* Data Fetch Section */}
                    <div className="border rounded-lg p-6 space-y-4">
                      <div className="flex items-start justify-between">
                        <div className="space-y-2">
                          <h3 className="font-semibold text-lg flex items-center gap-2">
                            <Download className="h-5 w-5 text-blue-600" />
                            Fetch NASA Satellite Data
                          </h3>
                          <p className="text-sm text-gray-600 dark:text-gray-400">
                            Fetch fresh satellite data for all 47 Kenyan counties from NASA Earth Engine.
                            This process may take 10-15 minutes to complete.
                          </p>
                          <div className="flex items-center gap-2 text-xs text-gray-500">
                            <Clock className="h-3 w-3" />
                            <span>Automatic fetch: Every Sunday at 2:00 AM</span>
                          </div>
                        </div>
                        <Button
                          onClick={async () => {
                            setFetchingData(true)
                            try {
                              const result = await api.triggerDataFetch()
                              toast({
                                title: 'Data Fetch Initiated',
                                description: `Fetching data for ${result.counties || 47} counties. Check logs for progress.`,
                              })
                            } catch (error: any) {
                              toast({
                                title: 'Fetch Failed',
                                description: error.message || 'Failed to trigger data fetch',
                                variant: 'destructive',
                              })
                            } finally {
                              setFetchingData(false)
                            }
                          }}
                          disabled={fetchingData}
                          className="min-w-[140px] bg-blue-600 hover:bg-blue-700"
                        >
                          {fetchingData ? (
                            <>
                              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                              Fetching...
                            </>
                          ) : (
                            <>
                              <Download className="mr-2 h-4 w-4" />
                              Fetch Now
                            </>
                          )}
                        </Button>
                      </div>

                      {fetchingData && (
                        <div className="bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
                          <div className="flex items-center gap-3">
                            <Loader2 className="h-5 w-5 animate-spin text-blue-600" />
                            <div>
                              <p className="font-medium text-blue-900 dark:text-blue-100">
                                Fetching satellite data...
                              </p>
                              <p className="text-sm text-blue-700 dark:text-blue-300">
                                Processing all 47 counties. This may take up to 15 minutes. 
                                You can safely navigate away - the process continues in the background.
                              </p>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>

                    {/* ML Retrain Section */}
                    <div className="border rounded-lg p-6 space-y-4">
                      <div className="flex items-start justify-between">
                        <div className="space-y-2">
                          <h3 className="font-semibold text-lg flex items-center gap-2">
                            <svg className="h-5 w-5 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
                            </svg>
                            Retrain ML Model
                          </h3>
                          <p className="text-sm text-gray-600 dark:text-gray-400">
                            Retrain the Random Forest bloom prediction model using all available live and historical data.
                            Uses data from both /live and /historical directories.
                          </p>
                          <div className="flex items-center gap-2 text-xs text-gray-500">
                            <Clock className="h-3 w-3" />
                            <span>Automatic retrain: Every Monday at 5:00 AM</span>
                          </div>
                        </div>
                        <Button
                          onClick={async () => {
                            setRetrainingModel(true)
                            try {
                              const result = await api.triggerMLRetrain()
                              toast({
                                title: result.success ? 'Model Retrained' : 'Retrain Failed',
                                description: result.success 
                                  ? `Accuracy: ${(result.accuracy * 100).toFixed(1)}%, Samples: ${result.n_samples}`
                                  : result.error || 'Failed to retrain model',
                                variant: result.success ? 'default' : 'destructive',
                              })
                            } catch (error: any) {
                              toast({
                                title: 'Retrain Failed',
                                description: error.message || 'Failed to trigger ML retraining',
                                variant: 'destructive',
                              })
                            } finally {
                              setRetrainingModel(false)
                            }
                          }}
                          disabled={retrainingModel}
                          className="min-w-[140px] bg-purple-600 hover:bg-purple-700"
                        >
                          {retrainingModel ? (
                            <>
                              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                              Training...
                            </>
                          ) : (
                            <>
                              <RefreshCw className="mr-2 h-4 w-4" />
                              Retrain Now
                            </>
                          )}
                        </Button>
                      </div>

                      {retrainingModel && (
                        <div className="bg-purple-50 dark:bg-purple-950/30 border border-purple-200 dark:border-purple-800 rounded-lg p-4">
                          <div className="flex items-center gap-3">
                            <Loader2 className="h-5 w-5 animate-spin text-purple-600" />
                            <div>
                              <p className="font-medium text-purple-900 dark:text-purple-100">
                                Retraining ML model...
                              </p>
                              <p className="text-sm text-purple-700 dark:text-purple-300">
                                Analyzing live and historical satellite data. This typically takes 2-3 minutes.
                              </p>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Scheduler Status */}
                    <div className="border rounded-lg p-6 space-y-4">
                      <h3 className="font-semibold text-lg flex items-center gap-2">
                        <Clock className="h-5 w-5 text-green-600" />
                        Scheduler Status
                      </h3>
                      <Button
                        variant="outline"
                        onClick={async () => {
                          try {
                            const status = await api.getSchedulerStatus()
                            setSchedulerStatus(status)
                            toast({
                              title: 'Scheduler Status',
                              description: status.message || 'Status retrieved',
                            })
                          } catch (error: any) {
                            toast({
                              title: 'Error',
                              description: error.message || 'Failed to get status',
                              variant: 'destructive',
                            })
                          }
                        }}
                        className="w-full sm:w-auto"
                      >
                        <RefreshCw className="mr-2 h-4 w-4" />
                        Check Status
                      </Button>

                      {schedulerStatus && (
                        <div className="mt-4 bg-gray-50 dark:bg-gray-900 rounded-lg p-4 space-y-2">
                          <div className="grid grid-cols-2 gap-4 text-sm">
                            <div>
                              <span className="text-gray-600 dark:text-gray-400">Scheduler:</span>
                              <span className="ml-2 font-semibold">
                                {schedulerStatus.scheduler_enabled ? (
                                  <span className="text-green-600">✓ Running</span>
                                ) : (
                                  <span className="text-red-600">✗ Stopped</span>
                                )}
                              </span>
                            </div>
                            <div>
                              <span className="text-gray-600 dark:text-gray-400">Active Tasks:</span>
                              <span className="ml-2 font-semibold">{schedulerStatus.active_tasks || 0}</span>
                            </div>
                            <div>
                              <span className="text-gray-600 dark:text-gray-400">ML Predictor:</span>
                              <span className="ml-2 font-semibold">
                                {schedulerStatus.ml_predictor_available ? (
                                  <span className="text-green-600">✓ Available</span>
                                ) : (
                                  <span className="text-orange-600">⚠ Unavailable</span>
                                )}
                              </span>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Info Cards */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <Card className="border-l-4 border-l-blue-500">
                        <CardHeader className="pb-3">
                          <CardTitle className="text-sm font-medium text-gray-600 dark:text-gray-400">
                            Data Sources
                          </CardTitle>
                        </CardHeader>
                        <CardContent>
                          <ul className="space-y-2 text-sm">
                            <li className="flex items-center gap-2">
                              <CheckCircle className="h-4 w-4 text-green-600" />
                              Sentinel-2 (10m resolution)
                            </li>
                            <li className="flex items-center gap-2">
                              <CheckCircle className="h-4 w-4 text-green-600" />
                              Landsat 8/9 (30m resolution)
                            </li>
                            <li className="flex items-center gap-2">
                              <CheckCircle className="h-4 w-4 text-green-600" />
                              MODIS (250m resolution)
                            </li>
                            <li className="flex items-center gap-2">
                              <CheckCircle className="h-4 w-4 text-green-600" />
                              CHIRPS Rainfall Data
                            </li>
                          </ul>
                        </CardContent>
                      </Card>

                      <Card className="border-l-4 border-l-purple-500">
                        <CardHeader className="pb-3">
                          <CardTitle className="text-sm font-medium text-gray-600 dark:text-gray-400">
                            ML Model Info
                          </CardTitle>
                        </CardHeader>
                        <CardContent>
                          <ul className="space-y-2 text-sm">
                            <li className="flex items-center gap-2">
                              <CheckCircle className="h-4 w-4 text-purple-600" />
                              Random Forest Classifier
                            </li>
                            <li className="flex items-center gap-2">
                              <CheckCircle className="h-4 w-4 text-purple-600" />
                              Features: NDVI, NDWI, Rainfall, Temp
                            </li>
                            <li className="flex items-center gap-2">
                              <CheckCircle className="h-4 w-4 text-purple-600" />
                              Training: Live + Historical data
                            </li>
                            <li className="flex items-center gap-2">
                              <CheckCircle className="h-4 w-4 text-purple-600" />
                              Auto-retrain: Weekly
                            </li>
                          </ul>
                        </CardContent>
                      </Card>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          </>
        )}
      </main>
    </div>
  )
}

