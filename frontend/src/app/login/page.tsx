'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import Image from 'next/image'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Loader2, LogIn, Phone, Lock, ArrowLeft, Sprout, AlertCircle } from 'lucide-react'
import { ThemeSwitcher } from '@/components/ui/theme-switcher'
import { LanguageSelector } from '@/components/ui/language-selector'
import { useToast } from '@/components/ui/use-toast'
import { useAuthStore, getDashboardRoute } from '@/store/authStore'

export default function LoginPage() {
  const router = useRouter()
  const { toast } = useToast()
  const { login: authLogin, isLoading, error: authError, clearError, isAuthenticated } = useAuthStore()
  
  const [phone, setPhone] = useState('')
  const [password, setPassword] = useState('')
  const [localError, setLocalError] = useState('')

  // Redirect if already logged in (industry standard)
  useEffect(() => {
    if (isAuthenticated) {
      const { farmer } = useAuthStore.getState()
      router.push(getDashboardRoute(farmer?.user_type))
    }
  }, [isAuthenticated, router])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLocalError('')
    clearError()
    
    if (!phone || !password) {
      setLocalError('Please fill in all fields')
      return
    }

    const success = await authLogin(phone, password)
    
    if (success) {
      const { farmer } = useAuthStore.getState()
      
      // Show success message
      toast({
        title: 'Login Successful! 🎉',
        description: `Welcome back, ${farmer?.name}!`,
      })
      
      // Redirect based on user type
      router.push(getDashboardRoute(farmer?.user_type))
    } else {
      setLocalError(authError || 'Login failed. Please check your credentials.')
    }
  }
  
  const displayError = localError || authError

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
        <Card className="w-full max-w-md shadow-2xl border-green-100 dark:border-green-900">
          <CardHeader className="space-y-1 text-center">
            <div className="mx-auto mb-4 w-20 h-20 bg-green-100 dark:bg-green-950 rounded-full flex items-center justify-center">
              <LogIn className="h-10 w-10 text-green-600" />
            </div>
            <CardTitle className="text-3xl font-bold text-green-700 dark:text-green-400">
              Welcome Back
            </CardTitle>
            <CardDescription className="text-base">
              Sign in to access your dashboard
            </CardDescription>
          </CardHeader>

          <form onSubmit={handleSubmit}>
            <CardContent className="space-y-4">
              {displayError && (
                <div className="bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800 rounded-lg p-3 flex items-start gap-2">
                  <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
                  <p className="text-sm text-red-600 dark:text-red-400">{displayError}</p>
                </div>
              )}

              <div className="space-y-2">
                <Label htmlFor="phone" className="flex items-center gap-2">
                  <Phone className="h-4 w-4" />
                  Phone Number
                </Label>
                <Input
                  id="phone"
                  type="tel"
                  placeholder="+254712345678"
                      value={phone}
                      onChange={(e) => setPhone(e.target.value)}
                      className="h-12"
                      disabled={isLoading}
                      required
                />
                <p className="text-xs text-gray-500">Enter your registered phone number</p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="password" className="flex items-center gap-2">
                  <Lock className="h-4 w-4" />
                  Password
                </Label>
                <Input
                  id="password"
                  type="password"
                  placeholder="Enter your password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className="h-12"
                      disabled={isLoading}
                      required
                />
              </div>

              <Button
                type="submit"
                className="w-full h-12 text-lg bg-green-600 hover:bg-green-700"
                disabled={isLoading}
              >
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                    Authenticating...
                  </>
                ) : (
                  <>
                    <LogIn className="mr-2 h-5 w-5" />
                    Login
                  </>
                )}
              </Button>
            </CardContent>
          </form>

          <CardFooter className="flex flex-col space-y-4">
            <div className="relative w-full">
              <div className="absolute inset-0 flex items-center">
                <span className="w-full border-t" />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-white dark:bg-gray-950 px-2 text-gray-500">
                  Don&apos;t have an account?
                </span>
              </div>
            </div>

            <div className="w-full grid grid-cols-1 gap-2">
              <Link href="/register" className="w-full">
                <Button variant="outline" className="w-full h-11 border-green-600 text-green-600 hover:bg-green-50 dark:hover:bg-green-950">
                  <Sprout className="mr-2 h-4 w-4" />
                  Register as Farmer
                </Button>
              </Link>
              <div className="grid grid-cols-2 gap-2">
                <Link href="/register/agrovet">
                  <Button variant="outline" className="w-full h-10 text-sm border-amber-600 text-amber-600 hover:bg-amber-50 dark:hover:bg-amber-950">
                    Register as Agrovet
                  </Button>
                </Link>
                <Link href="/register/buyer">
                  <Button variant="outline" className="w-full h-10 text-sm border-blue-600 text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-950">
                    Register as Buyer
                  </Button>
                </Link>
              </div>
            </div>

            <div className="text-center space-y-2">
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Farmers can also register via USSD (no internet)
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
          <p>© 2025 Smart Shamba. All rights reserved.</p>
        </div>
      </footer>
    </div>
  )
}

