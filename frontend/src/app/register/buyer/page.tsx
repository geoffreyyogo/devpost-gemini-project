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
import { Loader2, ShoppingBag, Phone, Lock, User, Mail, MapPin, ArrowLeft, AlertCircle, CheckCircle2, Building2 } from 'lucide-react'
import { ThemeSwitcher } from '@/components/ui/theme-switcher'
import { LanguageSelector } from '@/components/ui/language-selector'
import { useToast } from '@/components/ui/use-toast'
import { useAuthStore, getDashboardRoute } from '@/store/authStore'
import { api } from '@/lib/api'
import type { BuyerRegisterFormData } from '@/types'

const BUSINESS_TYPES = [
  'Individual Buyer',
  'Restaurant / Hotel',
  'Supermarket / Retail',
  'Wholesale Trader',
  'Processor / Manufacturer',
  'Exporter',
  'Institution (School/Hospital)',
  'Other',
]

const PRODUCE_OPTIONS = [
  'Maize', 'Beans', 'Rice', 'Wheat', 'Sorghum', 'Millet',
  'Tomatoes', 'Onions', 'Cabbages', 'Kale/Sukuma Wiki', 'Spinach', 'Carrots',
  'Potatoes', 'Sweet Potatoes', 'Cassava',
  'Bananas', 'Mangoes', 'Avocados', 'Oranges', 'Pawpaw', 'Passion Fruit',
  'Tea', 'Coffee', 'Sugarcane', 'Macadamia', 'Cashew Nuts',
  'Milk', 'Eggs', 'Honey', 'Fish',
]

export default function BuyerRegisterPage() {
  const router = useRouter()
  const { toast } = useToast()
  const { registerBuyer, isLoading, error: authError, clearError, isAuthenticated, farmer } = useAuthStore()

  useEffect(() => {
    if (isAuthenticated && farmer) {
      router.push(getDashboardRoute(farmer.user_type))
    }
  }, [isAuthenticated, farmer, router])

  // Step management (2-step wizard)
  const [step, setStep] = useState(1)

  // Step 1: Personal info
  const [name, setName] = useState('')
  const [phone, setPhone] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')

  // Step 2: Business details
  const [businessName, setBusinessName] = useState('')
  const [businessType, setBusinessType] = useState('')
  const [county, setCounty] = useState('')
  const [subCounty, setSubCounty] = useState('')
  const [preferredProduce, setPreferredProduce] = useState<string[]>([])
  const [preferredCounties, setPreferredCounties] = useState<string[]>([])

  // Region data
  const [counties, setCounties] = useState<string[]>([])
  const [subCounties, setSubCounties] = useState<Record<string, string[]>>({})
  const [localError, setLocalError] = useState('')

  useEffect(() => {
    const fetchData = async () => {
      try {
        const data = await api.getRegionsAndCrops()
        const allCounties: string[] = []
        Object.values(data.regions).forEach((r: any) => {
          if (r.counties) allCounties.push(...r.counties)
        })
        setCounties([...new Set(allCounties)].sort())
        if (data.sub_counties) setSubCounties(data.sub_counties)
      } catch {
        // fallback
      }
    }
    fetchData()
  }, [])

  const toggleProduce = (item: string) => {
    setPreferredProduce(prev =>
      prev.includes(item) ? prev.filter(p => p !== item) : [...prev, item]
    )
  }

  const togglePreferredCounty = (c: string) => {
    setPreferredCounties(prev =>
      prev.includes(c) ? prev.filter(x => x !== c) : prev.length < 10 ? [...prev, c] : prev
    )
  }

  const validateStep1 = () => {
    if (!name || !phone || !password || !confirmPassword) {
      setLocalError('Please fill in all required fields')
      return false
    }
    if (password.length < 4) {
      setLocalError('Password must be at least 4 characters')
      return false
    }
    if (password !== confirmPassword) {
      setLocalError('Passwords do not match')
      return false
    }
    setLocalError('')
    return true
  }

  const handleNext = () => {
    if (step === 1 && validateStep1()) setStep(2)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLocalError('')
    clearError()

    const data: BuyerRegisterFormData = {
      name,
      phone,
      password,
      email: email || undefined,
      business_name: businessName || undefined,
      business_type: businessType || undefined,
      county: county || undefined,
      sub_county: subCounty || undefined,
      preferred_produce: preferredProduce.length > 0 ? preferredProduce : undefined,
      preferred_counties: preferredCounties.length > 0 ? preferredCounties : undefined,
    }

    const success = await registerBuyer(data)

    if (success) {
      toast({
        title: 'Registration Successful!',
        description: 'Welcome to Smart Shamba Marketplace!',
      })
      router.push('/dashboard/buyer')
    } else {
      setLocalError(authError || 'Registration failed. Please try again.')
    }
  }

  const displayError = localError || authError
  const availableSubCounties = county ? (subCounties[county] || []) : []

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-blue-50 dark:from-gray-950 dark:via-gray-900 dark:to-gray-950 flex flex-col">
      {/* Header */}
      <header className="border-b border-white/20 dark:border-gray-800/30 bg-white/70 dark:bg-gray-950/70 backdrop-blur-xl sticky top-0 z-50 shadow-lg shadow-blue-500/5">
        <div className="container mx-auto px-4 py-3">
          <div className="flex items-center justify-between">
            <Link href="/" className="flex items-center space-x-3 group">
              <Image src="/BloomWatch.png" alt="Smart Shamba" width={40} height={40} className="h-10 w-auto transition-transform group-hover:scale-105" priority />
              <span className="text-xl md:text-2xl font-bold bg-gradient-to-r from-blue-600 to-blue-500 bg-clip-text text-transparent hidden sm:inline">Smart Shamba</span>
            </Link>
            <div className="flex items-center gap-2 md:gap-3">
              <ThemeSwitcher />
              <LanguageSelector />
              <div className="hidden md:block w-px h-6 bg-gray-300 dark:bg-gray-700" />
              <Link href="/login">
                <Button variant="ghost" size="sm" className="rounded-full h-9 px-3 md:px-4 hover:bg-blue-50 dark:hover:bg-blue-900/20">
                  <ArrowLeft className="h-4 w-4 md:mr-2" />
                  <span className="hidden md:inline">Back to Login</span>
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </header>

      {/* Main */}
      <main className="flex-1 flex items-center justify-center px-4 py-8">
        <Card className="w-full max-w-lg shadow-2xl border-blue-100 dark:border-blue-900/50">
          <CardHeader className="space-y-1 text-center">
            <div className="mx-auto mb-4 w-20 h-20 bg-blue-100 dark:bg-blue-950 rounded-full flex items-center justify-center">
              <ShoppingBag className="h-10 w-10 text-blue-600" />
            </div>
            <CardTitle className="text-2xl font-bold text-blue-700 dark:text-blue-400">
              Buyer Registration
            </CardTitle>
            <CardDescription className="text-base">
              Buy fresh produce directly from Kenyan farmers
            </CardDescription>

            {/* Step indicator */}
            <div className="flex items-center justify-center gap-2 pt-4">
              {[1, 2].map(s => (
                <div key={s} className="flex items-center gap-2">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold transition-all ${
                    step > s ? 'bg-blue-600 text-white' : step === s ? 'bg-blue-600 text-white ring-4 ring-blue-200 dark:ring-blue-800' : 'bg-gray-200 dark:bg-gray-700 text-gray-500'
                  }`}>
                    {step > s ? <CheckCircle2 className="h-4 w-4" /> : s}
                  </div>
                  {s < 2 && <div className={`w-16 h-0.5 ${step > s ? 'bg-blue-600' : 'bg-gray-200 dark:bg-gray-700'}`} />}
                </div>
              ))}
            </div>
            <div className="flex justify-between text-xs text-gray-500 px-8">
              <span>Personal Info</span>
              <span>Business Details</span>
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

              {/* Step 1: Personal Info */}
              {step === 1 && (
                <>
                  <div className="space-y-2">
                    <Label htmlFor="name" className="flex items-center gap-2"><User className="h-4 w-4" /> Full Name *</Label>
                    <Input id="name" value={name} onChange={e => setName(e.target.value)} placeholder="Jane Wanjiku" className="h-12" required />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="phone" className="flex items-center gap-2"><Phone className="h-4 w-4" /> Phone Number *</Label>
                    <Input id="phone" type="tel" value={phone} onChange={e => setPhone(e.target.value)} placeholder="+254712345678" className="h-12" required />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="email" className="flex items-center gap-2"><Mail className="h-4 w-4" /> Email (optional)</Label>
                    <Input id="email" type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="jane@example.com" className="h-12" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="password" className="flex items-center gap-2"><Lock className="h-4 w-4" /> Password *</Label>
                    <Input id="password" type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="Create a password" className="h-12" required />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="confirmPassword" className="flex items-center gap-2"><Lock className="h-4 w-4" /> Confirm Password *</Label>
                    <Input id="confirmPassword" type="password" value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)} placeholder="Re-enter password" className="h-12" required />
                  </div>
                </>
              )}

              {/* Step 2: Business Details */}
              {step === 2 && (
                <>
                  <div className="space-y-2">
                    <Label htmlFor="bizName" className="flex items-center gap-2"><Building2 className="h-4 w-4" /> Business Name</Label>
                    <Input id="bizName" value={businessName} onChange={e => setBusinessName(e.target.value)} placeholder="Your business name (optional)" className="h-12" />
                  </div>
                  <div className="space-y-2">
                    <Label>Business Type</Label>
                    <Select value={businessType} onValueChange={setBusinessType}>
                      <SelectTrigger className="h-12"><SelectValue placeholder="Select business type" /></SelectTrigger>
                      <SelectContent>{BUSINESS_TYPES.map(t => <SelectItem key={t} value={t}>{t}</SelectItem>)}</SelectContent>
                    </Select>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-2">
                      <Label className="flex items-center gap-2"><MapPin className="h-4 w-4" /> Your County</Label>
                      <Select value={county} onValueChange={v => { setCounty(v); setSubCounty('') }}>
                        <SelectTrigger className="h-12"><SelectValue placeholder="County" /></SelectTrigger>
                        <SelectContent>{counties.map(c => <SelectItem key={c} value={c}>{c}</SelectItem>)}</SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label>Sub-County</Label>
                      <Select value={subCounty} onValueChange={setSubCounty} disabled={!county}>
                        <SelectTrigger className="h-12"><SelectValue placeholder="Sub-county" /></SelectTrigger>
                        <SelectContent>{availableSubCounties.map(sc => <SelectItem key={sc} value={sc}>{sc}</SelectItem>)}</SelectContent>
                      </Select>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label className="flex items-center gap-2"><ShoppingBag className="h-4 w-4" /> Preferred Produce <span className="text-xs text-gray-400">(select what you buy)</span></Label>
                    <div className="flex flex-wrap gap-1.5 max-h-36 overflow-y-auto p-2 border rounded-lg bg-gray-50 dark:bg-gray-900">
                      {PRODUCE_OPTIONS.map(item => (
                        <button
                          key={item}
                          type="button"
                          onClick={() => toggleProduce(item)}
                          className={`px-2.5 py-1 rounded-full text-xs font-medium border transition-all ${
                            preferredProduce.includes(item)
                              ? 'bg-blue-600 text-white border-blue-600'
                              : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-300 border-gray-300 dark:border-gray-600 hover:border-blue-400'
                          }`}
                        >
                          {item}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label>Preferred Source Counties <span className="text-xs text-gray-400">(max 10)</span></Label>
                    <div className="flex flex-wrap gap-1.5 max-h-28 overflow-y-auto p-2 border rounded-lg bg-gray-50 dark:bg-gray-900">
                      {counties.slice(0, 47).map(c => (
                        <button
                          key={c}
                          type="button"
                          onClick={() => togglePreferredCounty(c)}
                          className={`px-2.5 py-1 rounded-full text-xs font-medium border transition-all ${
                            preferredCounties.includes(c)
                              ? 'bg-blue-600 text-white border-blue-600'
                              : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-300 border-gray-300 dark:border-gray-600 hover:border-blue-400'
                          }`}
                        >
                          {c}
                        </button>
                      ))}
                    </div>
                  </div>
                </>
              )}

              {/* Navigation */}
              <div className="flex gap-3 pt-2">
                {step > 1 && (
                  <Button type="button" variant="outline" onClick={() => { setStep(1); setLocalError('') }} className="flex-1 h-12">
                    Back
                  </Button>
                )}
                {step < 2 ? (
                  <Button type="button" onClick={handleNext} className="flex-1 h-12 bg-blue-600 hover:bg-blue-700">
                    Continue
                  </Button>
                ) : (
                  <Button type="submit" className="flex-1 h-12 bg-blue-600 hover:bg-blue-700" disabled={isLoading}>
                    {isLoading ? (
                      <><Loader2 className="mr-2 h-5 w-5 animate-spin" /> Creating Account...</>
                    ) : (
                      <><ShoppingBag className="mr-2 h-5 w-5" /> Create Buyer Account</>
                    )}
                  </Button>
                )}
              </div>
            </CardContent>
          </form>

          <CardFooter className="flex flex-col space-y-3 pt-0">
            <div className="relative w-full">
              <div className="absolute inset-0 flex items-center"><span className="w-full border-t" /></div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-white dark:bg-gray-950 px-2 text-gray-500">Already have an account?</span>
              </div>
            </div>
            <Link href="/login" className="w-full">
              <Button variant="outline" className="w-full h-10 border-blue-600 text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-950">
                Sign In
              </Button>
            </Link>
          </CardFooter>
        </Card>
      </main>

      <footer className="border-t bg-white dark:bg-gray-950 py-6">
        <div className="container mx-auto px-4 text-center text-sm text-gray-600 dark:text-gray-400">
          <p>&copy; 2025 Smart Shamba. All rights reserved.</p>
        </div>
      </footer>
    </div>
  )
}
