'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import Image from 'next/image'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Loader2, UserPlus, Phone, Lock, User, Mail, MapPin, Sprout as SproutIcon, ArrowLeft, AlertCircle, CheckCircle2 } from 'lucide-react'
import { ThemeSwitcher } from '@/components/ui/theme-switcher'
import { LanguageSelector } from '@/components/ui/language-selector'
import { useToast } from '@/components/ui/use-toast'
import { useAuthStore } from '@/store/authStore'
import { api } from '@/lib/api'

interface RegionData {
  regions: Record<string, {
    name: string
    counties: string[]
    main_crops: string[]
  }>
  crops: Record<string, {
    name: string
    category: string
  }>
}

export default function RegisterPage() {
  const router = useRouter()
  const { toast } = useToast()
  const { register: authRegister, isLoading: authLoading, error: authError, clearError, isAuthenticated } = useAuthStore()
  
  // Redirect if already logged in (industry standard)
  useEffect(() => {
    if (isAuthenticated) {
      router.push('/dashboard')
    }
  }, [isAuthenticated, router])

  // Form state
  const [name, setName] = useState('')
  const [phone, setPhone] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [region, setRegion] = useState('')
  const [county, setCounty] = useState('')
  const [selectedCrops, setSelectedCrops] = useState<string[]>([])
  const [otherCrops, setOtherCrops] = useState('')
  const [farmSize, setFarmSize] = useState(1.0)
  const [language, setLanguage] = useState('en')
  
  // UI state
  const [localError, setLocalError] = useState('')
  const [step, setStep] = useState(1)
  const [regionsData, setRegionsData] = useState<RegionData | null>(null)
  const [availableCounties, setAvailableCounties] = useState<string[]>([])
  const [availableCrops, setAvailableCrops] = useState<string[]>([])
  
  const displayError = localError || authError

  // Fetch regions and crops data
  useEffect(() => {
    const fetchData = async () => {
      try {
        console.log('Fetching regions and crops...')
        const data = await api.getRegionsAndCrops()
        console.log('Regions and crops loaded:', data)
        setRegionsData(data)
        
        // Set default region if not set
        if (!region && data.regions && Object.keys(data.regions).length > 0) {
          const firstRegion = Object.keys(data.regions)[0]
          setRegion(firstRegion)
        }
      } catch (error) {
        console.error('Failed to fetch regions/crops:', error)
      }
    }
    fetchData()
  }, [])

  // Update counties when region changes
  useEffect(() => {
    if (region && regionsData) {
      console.log('Region changed to:', region)
      const counties = regionsData.regions[region]?.counties || []
      console.log('Available counties:', counties)
      setAvailableCounties(counties)
      
      // Set first county as default
      if (counties.length > 0 && !county) {
        setCounty(counties[0])
      } else if (!counties.includes(county)) {
        setCounty(counties[0] || '')
      }
      
      // Set available crops for region (combine main_crops + all available)
      const regionCrops = regionsData.regions[region]?.main_crops || []
      // Also include all crops from the crops object
      const allCropsArray = Object.keys(regionsData.crops || {})
      const combinedCrops = [...new Set([...regionCrops, ...allCropsArray])]
      console.log('Available crops:', combinedCrops)
      setAvailableCrops(combinedCrops)
    }
  }, [region, regionsData])

  const handleCropToggle = (crop: string) => {
    setSelectedCrops(prev => 
      prev.includes(crop) 
        ? prev.filter(c => c !== crop)
        : [...prev, crop]
    )
  }

  const validateStep1 = () => {
    if (!name || !phone || !password) {
      setLocalError('Please fill in all required fields')
      return false
    }
    if (password !== confirmPassword) {
      setLocalError('Passwords do not match')
      return false
    }
    if (password.length < 6) {
      setLocalError('Password must be at least 6 characters')
      return false
    }
    return true
  }

  const validateStep2 = () => {
    if (!region || !county) {
      setLocalError('Please select your region and county')
      return false
    }
    // Check if at least one crop is selected OR manual crops are entered
    if (selectedCrops.length === 0 && !otherCrops.trim()) {
      setLocalError('Please select at least one crop or enter your crops manually')
      return false
    }
    return true
  }

  const handleNext = () => {
    setLocalError('')
    clearError()
    if (step === 1 && validateStep1()) {
      setStep(2)
    }
  }

  const handleBack = () => {
    setLocalError('')
    clearError()
    setStep(1)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLocalError('')
    clearError()
    
    if (!validateStep2()) return

    // Helper function to capitalize crop names properly
    const capitalizeCrop = (crop: string): string => {
      return crop
        .trim()
        .split(' ')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
        .join(' ')
    }
    
    // Combine selected crops with other crops
    const allCrops = [...selectedCrops]
    if (otherCrops.trim()) {
      const additionalCrops = otherCrops
        .split(',')
        .map(c => c.trim())
        .filter(c => c.length > 0)
        .map(c => `other:${capitalizeCrop(c)}`)
      allCrops.push(...additionalCrops)
    }
    
    const success = await authRegister({
      name,
      phone,
      email: email || undefined,
      password,
      region,
      county,
      crops: allCrops,
      language,
      farm_size: farmSize,
    })
    
    if (success) {
      toast({
        title: 'Registration Successful! 🎉',
        description: 'Your account has been created. Redirecting to dashboard...',
      })
      
      // Redirect to dashboard
      setTimeout(() => {
        router.push('/dashboard')
      }, 1500)
    } else {
      setLocalError(authError || 'Registration failed. Please try again.')
    }
  }

  const progressPercentage = step === 1 ? 33 : step === 2 ? 66 : 100

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-white to-green-50 dark:from-gray-950 dark:via-gray-900 dark:to-gray-950 flex flex-col">
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

            {/* Right Side - Actions */}
            <div className="flex items-center gap-2 md:gap-3">
              {/* Theme Switcher */}
              <ThemeSwitcher />
              
              {/* Language Selector */}
              <LanguageSelector />
              
              {/* Divider */}
              <div className="hidden md:block w-px h-6 bg-gray-300 dark:bg-gray-700" />
              
              {/* Back to Home */}
              <Link href="/">
                <Button variant="ghost" size="sm" className="rounded-full h-9 px-3 md:px-4 hover:bg-green-50 dark:hover:bg-green-900/20">
                  <ArrowLeft className="h-4 w-4 md:mr-2" />
                  <span className="hidden md:inline">Back to Home</span>
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex items-center justify-center px-4 py-12">
        <Card className="w-full max-w-2xl shadow-2xl border-green-100 dark:border-green-900">
          <CardHeader className="space-y-1 text-center">
            <div className="mx-auto mb-4 w-20 h-20 bg-green-100 dark:bg-green-950 rounded-full flex items-center justify-center">
              <UserPlus className="h-10 w-10 text-green-600" />
            </div>
            <CardTitle className="text-3xl font-bold text-green-700 dark:text-green-400">
              Register as Farmer
            </CardTitle>
            <CardDescription className="text-base">
              Join BloomWatch Kenya and start monitoring your crops
            </CardDescription>
            
            {/* Progress Bar */}
            <div className="pt-4">
              <div className="flex justify-between text-xs text-gray-600 dark:text-gray-400 mb-2">
                <span className={step >= 1 ? 'text-green-600 font-semibold' : ''}>Personal Info</span>
                <span className={step >= 2 ? 'text-green-600 font-semibold' : ''}>Farm Location</span>
                <span className={step >= 3 ? 'text-green-600 font-semibold' : ''}>Complete</span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div 
                  className="bg-green-600 h-2 rounded-full transition-all duration-500 ease-in-out"
                  style={{ width: `${progressPercentage}%` }}
                />
              </div>
            </div>
          </CardHeader>

          <form onSubmit={handleSubmit}>
            <CardContent className="space-y-4">
              {displayError && (
                <div className="bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800 rounded-lg p-3 flex items-start gap-2">
                  <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
                  <p className="text-sm text-red-600 dark:text-red-400">{displayError}</p>
                </div>
              )}

              {step === 1 && (
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="name" className="flex items-center gap-2">
                      <User className="h-4 w-4" />
                      Full Name *
                    </Label>
                    <Input
                      id="name"
                      type="text"
                      placeholder="John Mwangi"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      className="h-12"
                      required
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="phone" className="flex items-center gap-2">
                      <Phone className="h-4 w-4" />
                      Phone Number *
                    </Label>
                    <Input
                      id="phone"
                      type="tel"
                      placeholder="+254712345678"
                      value={phone}
                      onChange={(e) => setPhone(e.target.value)}
                      className="h-12"
                      required
                    />
                    <p className="text-xs text-gray-500">This will be your username</p>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="email" className="flex items-center gap-2">
                      <Mail className="h-4 w-4" />
                      Email (Optional)
                    </Label>
                    <Input
                      id="email"
                      type="email"
                      placeholder="john@example.com"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="h-12"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="password" className="flex items-center gap-2">
                      <Lock className="h-4 w-4" />
                      Password *
                    </Label>
                    <Input
                      id="password"
                      type="password"
                      placeholder="Minimum 6 characters"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className="h-12"
                      required
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="confirmPassword" className="flex items-center gap-2">
                      <Lock className="h-4 w-4" />
                      Confirm Password *
                    </Label>
                    <Input
                      id="confirmPassword"
                      type="password"
                      placeholder="Re-enter password"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      className="h-12"
                      required
                    />
                  </div>

                  <Button
                    type="button"
                    onClick={handleNext}
                    className="w-full h-12 text-lg bg-green-600 hover:bg-green-700"
                  >
                    Next Step →
                  </Button>
                </div>
              )}

              {step === 2 && (
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="region" className="flex items-center gap-2">
                      <MapPin className="h-4 w-4" />
                      Region *
                    </Label>
                    <Select value={region} onValueChange={setRegion}>
                      <SelectTrigger className="h-12">
                        <SelectValue placeholder="Select your region" />
                      </SelectTrigger>
                      <SelectContent>
                        {regionsData && Object.keys(regionsData.regions).length > 0 ? (
                          Object.entries(regionsData.regions).map(([key, data]) => (
                            <SelectItem key={key} value={key}>
                              {data.name}
                            </SelectItem>
                          ))
                        ) : (
                          <SelectItem value="loading" disabled>Loading regions...</SelectItem>
                        )}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="county" className="flex items-center gap-2">
                      <MapPin className="h-4 w-4" />
                      County *
                    </Label>
                    <Select value={county} onValueChange={setCounty} disabled={!region || availableCounties.length === 0}>
                      <SelectTrigger className="h-12">
                        <SelectValue placeholder={region ? "Select your county" : "Select region first"} />
                      </SelectTrigger>
                      <SelectContent>
                        {availableCounties.length > 0 ? (
                          availableCounties.map((c) => (
                            <SelectItem key={c} value={c}>
                              {c}
                            </SelectItem>
                          ))
                        ) : (
                          <SelectItem value="loading" disabled>
                            {region ? "Loading counties..." : "Select region first"}
                          </SelectItem>
                        )}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="farm-size" className="flex items-center gap-2">
                      <MapPin className="h-4 w-4" />
                      Farm Size (Acres) *
                    </Label>
                    <Input
                      id="farm-size"
                      type="number"
                      min="0.1"
                      max="10000"
                      step="0.1"
                      value={farmSize}
                      onChange={(e) => {
                        const value = e.target.value
                        if (value === '' || value === '.') {
                          setFarmSize(0)
                        } else {
                          const parsed = parseFloat(value)
                          if (!isNaN(parsed)) {
                            setFarmSize(parsed)
                          }
                        }
                      }}
                      onBlur={(e) => {
                        // Ensure minimum value on blur
                        if (farmSize < 0.1) {
                          setFarmSize(0.1)
                        }
                      }}
                      className="h-12"
                      placeholder="Enter farm size (e.g., 0.5, 1.25, 5)"
                    />
                    <p className="text-xs text-gray-500">Enter your farm size in acres (minimum 0.1)</p>
                  </div>

                  <div className="space-y-2">
                    <Label className="flex items-center gap-2">
                      <SproutIcon className="h-4 w-4" />
                      Select Your Crops (Optional - or type below)
                    </Label>
                    {availableCrops.length > 0 ? (
                      <div className="border rounded-lg p-4 bg-gray-50 dark:bg-gray-900">
                        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2 max-h-[400px] overflow-y-auto">
                          {availableCrops.map((crop) => {
                            // Get crop display name from regionsData if available
                            const cropData = regionsData?.crops?.[crop]
                            const displayName = cropData?.name || crop.charAt(0).toUpperCase() + crop.slice(1).replace('_', ' ')
                            const icon = (cropData as any)?.icon || ''
                            
                            return (
                              <Button
                                key={crop}
                                type="button"
                                variant={selectedCrops.includes(crop) ? 'default' : 'outline'}
                                className={`justify-start h-auto py-3 text-sm ${selectedCrops.includes(crop) ? 'bg-green-600 hover:bg-green-700 text-white' : 'hover:bg-green-50 dark:hover:bg-green-950'}`}
                                onClick={() => handleCropToggle(crop)}
                              >
                                <span className="flex items-center gap-1 w-full">
                                  {selectedCrops.includes(crop) && <CheckCircle2 className="h-4 w-4 flex-shrink-0" />}
                                  <span className="truncate">{icon} {displayName}</span>
                                </span>
                              </Button>
                            )
                          })}
                        </div>
                      </div>
                    ) : (
                      <div className="p-4 border rounded-lg text-center text-gray-500">
                        {regionsData ? (region ? 'Loading crops...' : 'Select a region first') : 'Loading...'}
                      </div>
                    )}
                    <p className="text-xs text-gray-500 font-semibold mt-2">
                      ✓ Selected: {selectedCrops.length} crop{selectedCrops.length !== 1 ? 's' : ''} 
                      {selectedCrops.length > 0 && ` (${selectedCrops.slice(0, 3).map(c => c.replace('_', ' ')).join(', ')}${selectedCrops.length > 3 ? '...' : ''})`}
                    </p>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="other-crops" className="flex items-center gap-2">
                      <SproutIcon className="h-4 w-4" />
                      Manual Crop Entry * (If not listed above)
                    </Label>
                    <Input
                      id="other-crops"
                      type="text"
                      placeholder="Enter crops separated by commas: quinoa, avocado, passion fruit"
                      value={otherCrops}
                      onChange={(e) => setOtherCrops(e.target.value)}
                      className="h-12"
                    />
                    <p className="text-xs text-gray-500">
                      Enter crop names separated by commas if not in the list above
                    </p>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="language">Preferred Language</Label>
                    <Select value={language} onValueChange={setLanguage}>
                      <SelectTrigger className="h-12">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="en">English</SelectItem>
                        <SelectItem value="sw">Kiswahili</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="flex gap-3">
                    <Button
                      type="button"
                      onClick={handleBack}
                      variant="outline"
                      className="flex-1 h-12 text-lg"
                    >
                      ← Back
                    </Button>
                    <Button
                      type="submit"
                      className="flex-1 h-12 text-lg bg-green-600 hover:bg-green-700"
                      disabled={authLoading}
                    >
                      {authLoading ? (
                        <>
                          <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                          Registering...
                        </>
                      ) : (
                        <>
                          <UserPlus className="mr-2 h-5 w-5" />
                          Register
                        </>
                      )}
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
          </form>

          <CardFooter className="flex flex-col space-y-4">
            <div className="relative w-full">
              <div className="absolute inset-0 flex items-center">
                <span className="w-full border-t" />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-white dark:bg-gray-950 px-2 text-gray-500">
                  Already have an account?
                </span>
              </div>
            </div>

            <Link href="/login" className="w-full">
              <Button variant="outline" className="w-full h-12 text-lg border-green-600 text-green-600 hover:bg-green-50 dark:hover:bg-green-950">
                Login Instead
              </Button>
            </Link>

            <div className="text-center space-y-2">
              <p className="text-sm text-gray-600 dark:text-gray-400">
                or register via USSD (no internet required)
              </p>
              <p className="text-2xl font-bold text-green-600">
                *384*42434#
              </p>
            </div>
          </CardFooter>
        </Card>
      </main>

      {/* Footer */}
      <footer className="border-t bg-white dark:bg-gray-950 py-6">
        <div className="container mx-auto px-4 text-center text-sm text-gray-600 dark:text-gray-400">
          <p>© 2025 BloomWatch Kenya. All rights reserved.</p>
        </div>
      </footer>
    </div>
  )
}

