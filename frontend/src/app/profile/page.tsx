'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Loader2, User, Phone, Mail, MapPin, Sprout, ArrowLeft, Save, LogOut, AlertCircle, CheckCircle2, Settings } from 'lucide-react'
import { useToast } from '@/components/ui/use-toast'
import { useAuthStore } from '@/store/authStore'

export default function ProfilePage() {
  const router = useRouter()
  const { toast } = useToast()
  const { farmer, isAuthenticated, logout, updateProfile, isLoading } = useAuthStore()
  
  // Form state
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [selectedCrops, setSelectedCrops] = useState<string[]>([])
  const [language, setLanguage] = useState<'en' | 'sw'>('en')
  const [smsEnabled, setSmsEnabled] = useState(true)
  const [hasChanges, setHasChanges] = useState(false)

  // Check authentication
  useEffect(() => {
    if (!isAuthenticated || !farmer) {
      router.push('/login')
    }
  }, [isAuthenticated, farmer, router])

  // Initialize form with farmer data
  useEffect(() => {
    if (farmer) {
      setName(farmer.name)
      setEmail(farmer.email || '')
      setSelectedCrops(farmer.crops || [])
      setLanguage(farmer.language || 'en')
      setSmsEnabled(farmer.sms_enabled)
    }
  }, [farmer])

  // Track changes
  useEffect(() => {
    if (farmer) {
      const changed = 
        name !== farmer.name ||
        email !== (farmer.email || '') ||
        JSON.stringify(selectedCrops) !== JSON.stringify(farmer.crops) ||
        language !== farmer.language ||
        smsEnabled !== farmer.sms_enabled
      
      setHasChanges(changed)
    }
  }, [name, email, selectedCrops, language, smsEnabled, farmer])

  const handleCropToggle = (crop: string) => {
    setSelectedCrops(prev => 
      prev.includes(crop) 
        ? prev.filter(c => c !== crop)
        : [...prev, crop]
    )
  }

  const handleSave = async () => {
    if (!hasChanges) return

    const success = await updateProfile({
      name,
      email: email || undefined,
      crops: selectedCrops,
      language,
      sms_enabled: smsEnabled,
    })

    if (success) {
      toast({
        title: 'Profile Updated! ✅',
        description: 'Your profile has been successfully updated.',
      })
      setHasChanges(false)
    } else {
      toast({
        title: 'Update Failed',
        description: 'Could not update profile. Please try again.',
        variant: 'destructive',
      })
    }
  }

  const handleLogout = async () => {
    await logout()
    toast({
      title: 'Logged Out',
      description: 'You have been successfully logged out.',
    })
    router.push('/')
  }

  if (!farmer) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-green-600" />
      </div>
    )
  }

  const availableCrops = ['maize', 'beans', 'coffee', 'tea', 'wheat', 'rice', 'potatoes', 'tomatoes', 'bananas', 'sugarcane']

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-white to-green-50 dark:from-gray-950 dark:via-gray-900 dark:to-gray-950 flex flex-col">
      {/* Header */}
      <header className="border-b bg-white/80 dark:bg-gray-950/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <Link href="/dashboard" className="flex items-center space-x-2">
            <Sprout className="h-8 w-8 text-green-600" />
            <span className="text-2xl font-bold text-green-600">Smart Shamba</span>
          </Link>
          <div className="flex items-center gap-2">
            <Link href="/dashboard">
              <Button variant="ghost" size="sm">
                <ArrowLeft className="mr-2 h-4 w-4" />
                Back to Dashboard
              </Button>
            </Link>
            <Button variant="outline" size="sm" onClick={handleLogout}>
              <LogOut className="mr-2 h-4 w-4" />
              Logout
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 container mx-auto px-4 py-8 max-w-4xl">
        <div className="space-y-6">
          {/* Profile Header */}
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold text-green-700 dark:text-green-400">Profile Settings</h1>
              <p className="text-gray-600 dark:text-gray-400 mt-2">Manage your account information</p>
            </div>
            <div className="w-20 h-20 bg-green-100 dark:bg-green-950 rounded-full flex items-center justify-center">
              <User className="h-10 w-10 text-green-600" />
            </div>
          </div>

          {/* Tabs */}
          <Tabs defaultValue="personal" className="w-full">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="personal">Personal Information</TabsTrigger>
              <TabsTrigger value="farm">Farm & Preferences</TabsTrigger>
            </TabsList>

            {/* Personal Information Tab */}
            <TabsContent value="personal" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Personal Details</CardTitle>
                  <CardDescription>Update your personal information</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="name" className="flex items-center gap-2">
                      <User className="h-4 w-4" />
                      Full Name
                    </Label>
                    <Input
                      id="name"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      className="h-12"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="phone" className="flex items-center gap-2">
                      <Phone className="h-4 w-4" />
                      Phone Number
                    </Label>
                    <Input
                      id="phone"
                      value={farmer.phone}
                      className="h-12 bg-gray-100 dark:bg-gray-800"
                      disabled
                    />
                    <p className="text-xs text-gray-500">Phone number cannot be changed</p>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="email" className="flex items-center gap-2">
                      <Mail className="h-4 w-4" />
                      Email Address (Optional)
                    </Label>
                    <Input
                      id="email"
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="your.email@example.com"
                      className="h-12"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="region" className="flex items-center gap-2">
                      <MapPin className="h-4 w-4" />
                      Region
                    </Label>
                    <Input
                      id="region"
                      value={farmer.region}
                      className="h-12 bg-gray-100 dark:bg-gray-800"
                      disabled
                    />
                    <p className="text-xs text-gray-500">Region cannot be changed after registration</p>
                  </div>

                  {farmer.county && (
                    <div className="space-y-2">
                      <Label htmlFor="county" className="flex items-center gap-2">
                        <MapPin className="h-4 w-4" />
                        County
                      </Label>
                      <Input
                        id="county"
                        value={farmer.county}
                        className="h-12 bg-gray-100 dark:bg-gray-800"
                        disabled
                      />
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            {/* Farm & Preferences Tab */}
            <TabsContent value="farm" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Farm Information</CardTitle>
                  <CardDescription>Manage your crops and preferences</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label className="flex items-center gap-2">
                      <Sprout className="h-4 w-4" />
                      Your Crops
                    </Label>
                    <div className="grid grid-cols-2 gap-2">
                      {availableCrops.map((crop) => (
                        <Button
                          key={crop}
                          type="button"
                          variant={selectedCrops.includes(crop) ? 'default' : 'outline'}
                          className={`justify-start ${selectedCrops.includes(crop) ? 'bg-green-600 hover:bg-green-700' : ''}`}
                          onClick={() => handleCropToggle(crop)}
                        >
                          {selectedCrops.includes(crop) && <CheckCircle2 className="mr-2 h-4 w-4" />}
                          {crop.charAt(0).toUpperCase() + crop.slice(1)}
                        </Button>
                      ))}
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="language">Preferred Language</Label>
                    <Select value={language} onValueChange={(value: 'en' | 'sw') => setLanguage(value)}>
                      <SelectTrigger className="h-12">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="en">English</SelectItem>
                        <SelectItem value="sw">Kiswahili</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="sms">SMS Notifications</Label>
                    <Select value={smsEnabled ? 'enabled' : 'disabled'} onValueChange={(value) => setSmsEnabled(value === 'enabled')}>
                      <SelectTrigger className="h-12">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="enabled">Enabled</SelectItem>
                        <SelectItem value="disabled">Disabled</SelectItem>
                      </SelectContent>
                    </Select>
                    <p className="text-xs text-gray-500">
                      Receive alerts and notifications via SMS
                    </p>
                  </div>

                  <div className="bg-green-50 dark:bg-green-950 border border-green-200 dark:border-green-800 rounded-lg p-4">
                    <div className="flex items-start gap-2">
                      <Settings className="h-5 w-5 text-green-600 flex-shrink-0 mt-0.5" />
                      <div className="text-sm text-green-700 dark:text-green-400">
                        <p className="font-semibold">Registration Details</p>
                        <p className="mt-1">Registered via: <strong>{farmer.registered_via}</strong></p>
                        {farmer.registered_at && (
                          <p>Date: <strong>{new Date(farmer.registered_at).toLocaleDateString()}</strong></p>
                        )}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>

          {/* Save Button */}
          {hasChanges && (
            <Card className="border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-950">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-green-700 dark:text-green-400">
                    <AlertCircle className="h-5 w-5" />
                    <span className="font-semibold">You have unsaved changes</span>
                  </div>
                  <Button
                    onClick={handleSave}
                    disabled={isLoading}
                    className="bg-green-600 hover:bg-green-700"
                  >
                    {isLoading ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Saving...
                      </>
                    ) : (
                      <>
                        <Save className="mr-2 h-4 w-4" />
                        Save Changes
                      </>
                    )}
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t bg-white dark:bg-gray-950 py-6">
        <div className="container mx-auto px-4 text-center text-sm text-gray-600 dark:text-gray-400">
          <p>© 2025 Smart Shamba. All rights reserved.</p>
        </div>
      </footer>
    </div>
  )
}


