'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import Image from 'next/image'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Loader2, Store, Phone, Lock, User, Mail, MapPin, ArrowLeft, AlertCircle, CheckCircle2, CreditCard, Package } from 'lucide-react'
import { ThemeSwitcher } from '@/components/ui/theme-switcher'
import { LanguageSelector } from '@/components/ui/language-selector'
import { useToast } from '@/components/ui/use-toast'
import { useAuthStore, getDashboardRoute } from '@/store/authStore'
import { api } from '@/lib/api'
import type { AgrovetRegisterFormData } from '@/types'

const AGROVET_CATEGORIES = [
  'Seeds', 'Fertilizers', 'Pesticides', 'Herbicides', 'Farm Tools',
  'Animal Feed', 'Veterinary', 'Irrigation Equipment', 'Soil Amendments',
  'Organic Products', 'Protective Equipment', 'Packaging Materials',
]

export default function AgrovetRegisterPage() {
  const router = useRouter()
  const { toast } = useToast()
  const { registerAgrovet, isLoading, error: authError, clearError, isAuthenticated, farmer } = useAuthStore()

  // Redirect if already logged in
  useEffect(() => {
    if (isAuthenticated && farmer) {
      router.push(getDashboardRoute(farmer.user_type))
    }
  }, [isAuthenticated, farmer, router])

  // Step management (3-step wizard)
  const [step, setStep] = useState(1)

  // Step 1: Personal info
  const [name, setName] = useState('')
  const [phone, setPhone] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')

  // Step 2: Shop details
  const [shopName, setShopName] = useState('')
  const [shopDescription, setShopDescription] = useState('')
  const [shopCounty, setShopCounty] = useState('')
  const [shopSubCounty, setShopSubCounty] = useState('')
  const [shopAddress, setShopAddress] = useState('')
  const [selectedCategories, setSelectedCategories] = useState<string[]>([])

  // Step 3: Payment info
  const [mpesaTill, setMpesaTill] = useState('')
  const [mpesaPaybill, setMpesaPaybill] = useState('')
  const [bankName, setBankName] = useState('')
  const [bankAccount, setBankAccount] = useState('')

  // Region data
  const [counties, setCounties] = useState<string[]>([])
  const [subCounties, setSubCounties] = useState<Record<string, string[]>>({})
  const [localError, setLocalError] = useState('')

  // Fetch counties/sub-counties
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
        // fallback empty
      }
    }
    fetchData()
  }, [])

  const toggleCategory = (cat: string) => {
    setSelectedCategories(prev =>
      prev.includes(cat) ? prev.filter(c => c !== cat) : [...prev, cat]
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

  const validateStep2 = () => {
    if (!shopName) {
      setLocalError('Shop name is required')
      return false
    }
    if (selectedCategories.length === 0) {
      setLocalError('Select at least one product category')
      return false
    }
    setLocalError('')
    return true
  }

  const handleNext = () => {
    if (step === 1 && validateStep1()) setStep(2)
    else if (step === 2 && validateStep2()) setStep(3)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLocalError('')
    clearError()

    const data: AgrovetRegisterFormData = {
      name,
      phone,
      password,
      email: email || undefined,
      shop_name: shopName,
      shop_description: shopDescription || undefined,
      shop_county: shopCounty || undefined,
      shop_sub_county: shopSubCounty || undefined,
      shop_address: shopAddress || undefined,
      categories: selectedCategories,
      mpesa_till_number: mpesaTill || undefined,
      mpesa_paybill: mpesaPaybill || undefined,
    }

    const success = await registerAgrovet(data)

    if (success) {
      toast({
        title: 'Registration Successful!',
        description: 'Welcome to Smart Shamba! Your agrovet account is ready.',
      })
      router.push('/dashboard/agrovet')
    } else {
      setLocalError(authError || 'Registration failed. Please try again.')
    }
  }

  const displayError = localError || authError
  const availableSubCounties = shopCounty ? (subCounties[shopCounty] || []) : []

  return (
    <div className="min-h-screen bg-gradient-to-br from-amber-50 via-white to-amber-50 dark:from-gray-950 dark:via-gray-900 dark:to-gray-950 flex flex-col">
      {/* Header */}
      <header className="border-b border-white/20 dark:border-gray-800/30 bg-white/70 dark:bg-gray-950/70 backdrop-blur-xl sticky top-0 z-50 shadow-lg shadow-amber-500/5">
        <div className="container mx-auto px-4 py-3">
          <div className="flex items-center justify-between">
            <Link href="/" className="flex items-center space-x-3 group">
              <Image src="/BloomWatch.png" alt="Smart Shamba" width={40} height={40} className="h-10 w-auto transition-transform group-hover:scale-105" priority />
              <span className="text-xl md:text-2xl font-bold bg-gradient-to-r from-amber-600 to-amber-500 bg-clip-text text-transparent hidden sm:inline">Smart Shamba</span>
            </Link>
            <div className="flex items-center gap-2 md:gap-3">
              <ThemeSwitcher />
              <LanguageSelector />
              <div className="hidden md:block w-px h-6 bg-gray-300 dark:bg-gray-700" />
              <Link href="/login">
                <Button variant="ghost" size="sm" className="rounded-full h-9 px-3 md:px-4 hover:bg-amber-50 dark:hover:bg-amber-900/20">
                  <ArrowLeft className="h-4 w-4 md:mr-2" />
                  <span className="hidden md:inline">Back to Login</span>
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex items-center justify-center px-4 py-8">
        <Card className="w-full max-w-lg shadow-2xl border-amber-100 dark:border-amber-900/50">
          <CardHeader className="space-y-1 text-center">
            <div className="mx-auto mb-4 w-20 h-20 bg-amber-100 dark:bg-amber-950 rounded-full flex items-center justify-center">
              <Store className="h-10 w-10 text-amber-600" />
            </div>
            <CardTitle className="text-2xl font-bold text-amber-700 dark:text-amber-400">
              Agrovet Registration
            </CardTitle>
            <CardDescription className="text-base">
              Sell agricultural products to farmers across Kenya
            </CardDescription>

            {/* Step indicator */}
            <div className="flex items-center justify-center gap-2 pt-4">
              {[1, 2, 3].map(s => (
                <div key={s} className="flex items-center gap-2">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold transition-all ${
                    step > s ? 'bg-amber-600 text-white' : step === s ? 'bg-amber-600 text-white ring-4 ring-amber-200 dark:ring-amber-800' : 'bg-gray-200 dark:bg-gray-700 text-gray-500'
                  }`}>
                    {step > s ? <CheckCircle2 className="h-4 w-4" /> : s}
                  </div>
                  {s < 3 && <div className={`w-12 h-0.5 ${step > s ? 'bg-amber-600' : 'bg-gray-200 dark:bg-gray-700'}`} />}
                </div>
              ))}
            </div>
            <div className="flex justify-between text-xs text-gray-500 px-2">
              <span>Personal</span>
              <span>Shop Details</span>
              <span>Payment</span>
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
                    <Input id="name" value={name} onChange={e => setName(e.target.value)} placeholder="John Doe" className="h-12" required />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="phone" className="flex items-center gap-2"><Phone className="h-4 w-4" /> Phone Number *</Label>
                    <Input id="phone" type="tel" value={phone} onChange={e => setPhone(e.target.value)} placeholder="+254712345678" className="h-12" required />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="email" className="flex items-center gap-2"><Mail className="h-4 w-4" /> Email (optional)</Label>
                    <Input id="email" type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="john@example.com" className="h-12" />
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

              {/* Step 2: Shop Details */}
              {step === 2 && (
                <>
                  <div className="space-y-2">
                    <Label htmlFor="shopName" className="flex items-center gap-2"><Store className="h-4 w-4" /> Shop Name *</Label>
                    <Input id="shopName" value={shopName} onChange={e => setShopName(e.target.value)} placeholder="Green Harvest Agrovets" className="h-12" required />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="shopDesc">Shop Description</Label>
                    <Textarea id="shopDesc" value={shopDescription} onChange={e => setShopDescription(e.target.value)} placeholder="Tell farmers about your shop..." rows={3} />
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-2">
                      <Label className="flex items-center gap-2"><MapPin className="h-4 w-4" /> County</Label>
                      <Select value={shopCounty} onValueChange={v => { setShopCounty(v); setShopSubCounty('') }}>
                        <SelectTrigger className="h-12"><SelectValue placeholder="Select county" /></SelectTrigger>
                        <SelectContent>{counties.map(c => <SelectItem key={c} value={c}>{c}</SelectItem>)}</SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label>Sub-County</Label>
                      <Select value={shopSubCounty} onValueChange={setShopSubCounty} disabled={!shopCounty}>
                        <SelectTrigger className="h-12"><SelectValue placeholder="Sub-county" /></SelectTrigger>
                        <SelectContent>{availableSubCounties.map(sc => <SelectItem key={sc} value={sc}>{sc}</SelectItem>)}</SelectContent>
                      </Select>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="shopAddr">Physical Address</Label>
                    <Input id="shopAddr" value={shopAddress} onChange={e => setShopAddress(e.target.value)} placeholder="Kenyatta Ave, Shop No. 5" className="h-12" />
                  </div>
                  <div className="space-y-2">
                    <Label className="flex items-center gap-2"><Package className="h-4 w-4" /> Product Categories * <span className="text-xs text-gray-400">(select at least one)</span></Label>
                    <div className="flex flex-wrap gap-2">
                      {AGROVET_CATEGORIES.map(cat => (
                        <button
                          key={cat}
                          type="button"
                          onClick={() => toggleCategory(cat)}
                          className={`px-3 py-1.5 rounded-full text-xs font-medium border transition-all ${
                            selectedCategories.includes(cat)
                              ? 'bg-amber-600 text-white border-amber-600'
                              : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-300 border-gray-300 dark:border-gray-600 hover:border-amber-400'
                          }`}
                        >
                          {cat}
                        </button>
                      ))}
                    </div>
                  </div>
                </>
              )}

              {/* Step 3: Payment Info */}
              {step === 3 && (
                <>
                  <div className="bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 rounded-lg p-3 mb-2">
                    <p className="text-sm text-amber-700 dark:text-amber-300">
                      Payment information lets farmers pay you directly. You can add or update this later.
                    </p>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="mpesaTill" className="flex items-center gap-2"><CreditCard className="h-4 w-4" /> M-Pesa Till Number</Label>
                    <Input id="mpesaTill" value={mpesaTill} onChange={e => setMpesaTill(e.target.value)} placeholder="e.g. 123456" className="h-12" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="mpesaPaybill">M-Pesa Paybill</Label>
                    <Input id="mpesaPaybill" value={mpesaPaybill} onChange={e => setMpesaPaybill(e.target.value)} placeholder="e.g. 247247" className="h-12" />
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-2">
                      <Label htmlFor="bankName">Bank Name</Label>
                      <Input id="bankName" value={bankName} onChange={e => setBankName(e.target.value)} placeholder="KCB, Equity..." className="h-12" />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="bankAcct">Account Number</Label>
                      <Input id="bankAcct" value={bankAccount} onChange={e => setBankAccount(e.target.value)} placeholder="Account No." className="h-12" />
                    </div>
                  </div>

                  {/* Summary */}
                  <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4 space-y-2 border">
                    <h4 className="font-semibold text-sm">Registration Summary</h4>
                    <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
                      <span className="text-gray-500">Name:</span><span className="font-medium">{name}</span>
                      <span className="text-gray-500">Phone:</span><span className="font-medium">{phone}</span>
                      <span className="text-gray-500">Shop:</span><span className="font-medium">{shopName}</span>
                      <span className="text-gray-500">Location:</span><span className="font-medium">{shopCounty || 'N/A'}{shopSubCounty ? `, ${shopSubCounty}` : ''}</span>
                      <span className="text-gray-500">Categories:</span><span className="font-medium">{selectedCategories.join(', ') || 'N/A'}</span>
                    </div>
                  </div>
                </>
              )}

              {/* Navigation Buttons */}
              <div className="flex gap-3 pt-2">
                {step > 1 && (
                  <Button type="button" variant="outline" onClick={() => { setStep(step - 1); setLocalError('') }} className="flex-1 h-12">
                    Back
                  </Button>
                )}
                {step < 3 ? (
                  <Button type="button" onClick={handleNext} className="flex-1 h-12 bg-amber-600 hover:bg-amber-700">
                    Continue
                  </Button>
                ) : (
                  <Button type="submit" className="flex-1 h-12 bg-amber-600 hover:bg-amber-700" disabled={isLoading}>
                    {isLoading ? (
                      <><Loader2 className="mr-2 h-5 w-5 animate-spin" /> Creating Account...</>
                    ) : (
                      <><Store className="mr-2 h-5 w-5" /> Create Agrovet Account</>
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
              <Button variant="outline" className="w-full h-10 border-amber-600 text-amber-600 hover:bg-amber-50 dark:hover:bg-amber-950">
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
