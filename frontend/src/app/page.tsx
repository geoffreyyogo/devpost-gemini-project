/**
 * Home Page - Landing/Welcome page for BloomWatch Kenya
 */

'use client'

import Link from 'next/link'
import Image from 'next/image'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Satellite,
  TrendingUp,
  MessageSquare,
  Smartphone,
  MapPin,
  Bell,
  Sprout,
  Users,
  Rocket,
  LogIn,
  Phone,
  Menu,
  Shield,
  FileText,
  HelpCircle,
  Mail,
  ChevronRight,
  Map as MapIcon,
  BarChart3,
  Radio,
  BrainCircuit,
  Wifi,
  WifiOff,
  Globe,
  Zap,
  CheckCircle,
  Cloud,
  Twitter,
  Facebook,
  Github,
} from 'lucide-react'
import { KenyaClimateMap } from '@/components/maps/KenyaClimateMap'
import { ClimateStatsCards } from '@/components/climate/ClimateStatsCards'
import { DataFreshnessBadge } from '@/components/climate/DataFreshnessBadge'
import { AgriculturalCarousel } from '@/components/carousel/AgriculturalCarousel'
import { StatisticsSection } from '@/components/sections/StatisticsSection'
import { CTASection } from '@/components/sections/CTASection'
import { ThemeSwitcher } from '@/components/ui/theme-switcher'
import { LanguageSelector } from '@/components/ui/language-selector'
import { useAuthStore } from '@/store/authStore'
import { useAOSInit } from '@/lib/aos'

export default function HomePage() {
  const { isAuthenticated, farmer } = useAuthStore()
  
  // Initialize scroll animations
  useAOSInit()
  
  return (
    <div className="min-h-screen bg-gradient-to-b from-green-50 to-white dark:from-gray-950 dark:to-gray-900">
      {/* Navigation */}
      <nav className="border-b border-white/20 dark:border-gray-800/30 bg-white/70 dark:bg-gray-950/70 backdrop-blur-xl sticky top-0 z-50 shadow-lg shadow-green-500/5 dark:shadow-green-500/10">
        <div className="container mx-auto px-4 py-3">
          <div className="flex items-center justify-between">
            {/* Logo */}
            <Link href="/" className="flex items-center space-x-3 group">
              <Image
                src="/BloomWatch.png"
                alt="BloomWatch Kenya"
                width={55}
                height={55}
                className="h-14 w-auto transition-transform group-hover:scale-105"
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
              
              {/* Auth Buttons */}
              {isAuthenticated && farmer ? (
                <div className="flex items-center gap-2 md:gap-3">
                  <span className="text-sm text-gray-600 dark:text-gray-400 hidden lg:inline font-medium">
                    Welcome, {farmer.name.split(' ')[0]}!
                  </span>
                  <Link href="/dashboard">
                    <Button className="bg-green-600 hover:bg-green-700 text-white rounded-2xl px-4 md:px-6 h-9 text-sm font-semibold shadow-md hover:shadow-lg transition-all">
                      Dashboard
                    </Button>
                  </Link>
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <Link href="/login" className="hidden sm:inline">
                    <Button variant="ghost" className="rounded-2xl px-4 md:px-5 h-9 text-sm font-medium hover:bg-green-50 dark:hover:bg-green-900/20">
                      <LogIn className="mr-2 h-4 w-4" />
                      Login
                    </Button>
                  </Link>
                  <Link href="/register">
                    <Button className="bg-green-600 hover:bg-green-700 text-white rounded-2xl px-4 md:px-6 h-9 text-sm font-semibold shadow-md hover:shadow-lg transition-all">
                      <Rocket className="mr-2 h-4 w-4" />
                      <span className="hidden sm:inline">Get Started</span>
                      <span className="sm:hidden">Start</span>
                    </Button>
                  </Link>
                </div>
              )}
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section - Matching Streamlit Design */}
      <section className="container mx-auto px-4 py-8">
        <div className="hero-section-enhanced relative overflow-hidden rounded-3xl p-16 text-center text-white shadow-2xl min-h-[650px] flex flex-col justify-center">
          {/* Background Pattern Overlay */}
          <div className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1625246333195-78d9c38ad449?w=1200')] bg-center bg-cover opacity-15 animate-parallax" />
          
          {/* Content */}
          <div className="relative z-10 hero-content space-y-6 animate-fade-in-up">
            <h1 className="text-5xl md:text-7xl lg:text-[3.5rem] font-bold tracking-tight" 
                style={{ textShadow: '3px 3px 6px rgba(0,0,0,0.3)' }}>
              Welcome to BloomWatch Kenya
            </h1>
            
            <h2 className="text-3xl md:text-4xl lg:text-[2.2rem] font-semibold mt-4" 
                style={{ textShadow: '2px 2px 4px rgba(0,0,0,0.3)' }}>
              Track Maua, Master Ukulima
            </h2>
            
            <p className="text-lg md:text-xl lg:text-[1.3rem] max-w-4xl mx-auto opacity-95 mt-6" 
               style={{ textShadow: '1px 1px 3px rgba(0,0,0,0.3)' }}>
              Use NASA satellite data and Flora, our AI MauaMentor, to monitor blooming and climate for better harvests.
            </p>

            {/* Floating CTA Buttons */}
            <div className="flex flex-col sm:flex-row gap-6 justify-center items-center mt-12">
              <Link href="/register">
                <Button 
                  size="lg" 
                  className="bg-white text-green-700 hover:bg-green-50 hover:scale-105 transition-all duration-300 text-lg px-10 py-7 rounded-2xl shadow-xl font-bold min-w-[200px]"
                >
                  <Rocket className="mr-2 h-5 w-5" />
                  Get Started
                </Button>
              </Link>
              <Link href="/login">
                <Button 
                  size="lg" 
                  variant="outline" 
                  className="bg-green-800/30 text-white border-2 border-white hover:bg-white hover:text-green-700 hover:scale-105 transition-all duration-300 text-lg px-10 py-7 rounded-2xl shadow-xl font-bold min-w-[200px] backdrop-blur-sm"
                >
                  <LogIn className="mr-2 h-5 w-5" />
                  Farmer Login
                </Button>
              </Link>
            </div>

            {/* USSD Registration Box - Matching Streamlit */}
            <div className="relative z-10 mt-12 max-w-2xl mx-auto" data-aos="zoom-in" data-aos-delay="200">
              <div className="ussd-floating-box bg-gradient-to-br from-white to-gray-50 dark:from-gray-800 dark:to-gray-900 p-6 rounded-2xl shadow-2xl border border-green-100 dark:border-green-900">
                <p className="text-green-700 dark:text-green-400 text-lg font-semibold flex items-center justify-center mb-2">
                  <Phone className="mr-2 h-5 w-5" />
                  You can also register by dialing:
                </p>
                <h2 
                  className="text-green-700 dark:text-green-400 text-5xl md:text-6xl font-bold text-center tracking-[0.15em] my-4 ussd-code-mobile"
                  style={{ textShadow: '2px 2px 4px rgba(46,125,50,0.2)' }}
                >
                  *384*42434#
                </h2>
                <p className="text-gray-600 dark:text-gray-400 text-sm text-center">
                  Works on any phone - No internet required
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Kenya Live Climate & Bloom Data Section - Matching Streamlit */}
      <section className="container mx-auto px-4 py-20 bg-white dark:bg-gray-950">
        <div className="space-y-8">
          {/* Section Header */}
          <div className="text-center space-y-4" data-aos="fade-down">
            <h2 className="text-4xl md:text-5xl font-bold text-green-700 dark:text-green-400 flex items-center justify-center gap-3 mobile-heading">
              <MapIcon className="h-8 w-8 md:h-10 md:w-10" />
              Kenya Live Climate & Bloom Data
            </h2>
            <p className="text-lg text-gray-600 dark:text-gray-300 font-semibold">
              Real-time agricultural insights powered by NASA satellite technology
            </p>
          </div>

          {/* Data Freshness Indicator */}
          <div className="flex justify-center">
            <DataFreshnessBadge />
          </div>

          {/* Interactive Map */}
          <div className="max-w-6xl mx-auto" data-aos="zoom-in">
            <KenyaClimateMap />
          </div>

          {/* Climate Statistics Cards */}
          <div className="mt-8" data-aos="fade-up">
            <ClimateStatsCards />
          </div>

          {/* Real Data Indicator & CTA */}
          <div className="text-center space-y-4">
            <div className="bg-green-50 dark:bg-green-950 border border-green-200 dark:border-green-800 rounded-lg p-6 max-w-4xl mx-auto">
              <p className="text-green-700 dark:text-green-400 font-semibold flex items-center justify-center gap-2">
                <Satellite className="h-5 w-5" />
                ✓ Displaying real NASA satellite data from Google Earth Engine | Covering all 47 Kenya counties
              </p>
            </div>

            {/* CTA Button */}
            <div>
              <Link href={isAuthenticated && farmer ? "/dashboard" : "/login"}>
                <Button 
                  size="lg" 
                  className="bg-green-600 hover:bg-green-700 text-white px-10 py-6 rounded-2xl shadow-xl hover:scale-105 transition-all"
                >
                  <BarChart3 className="mr-2 h-5 w-5" />
                  {isAuthenticated && farmer ? "View Your Dashboard" : "Explore Your Region's Data"}
                </Button>
              </Link>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
                {isAuthenticated && farmer 
                  ? "✓ Access your personalized dashboard and insights" 
                  : "🔐 Please log in to access personalized regional data and alerts"
                }
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section - Why BloomWatch Kenya */}
      <section className="container mx-auto px-4 py-20">
        <div className="text-center mb-16" data-aos="fade-down">
          <h2 className="text-4xl md:text-5xl font-bold text-green-700 dark:text-green-400 mb-4 mobile-heading">
            🌟 Why BloomWatch Kenya?
          </h2>
          <p className="text-gray-600 dark:text-gray-300 text-lg max-w-3xl mx-auto">
            Powered by NASA satellite technology and AI-driven insights
          </p>
        </div>
        
        <div className="grid md:grid-cols-3 gap-8">
          {/* NASA Satellites Card */}
          <Card data-aos="fade-up" className="group relative overflow-hidden bg-white dark:bg-gray-900 rounded-[20px] border-2 border-transparent hover:border-green-600 dark:hover:border-green-500 shadow-lg hover:shadow-2xl transition-all duration-700 ease-out hover:-translate-y-3 hover:scale-[1.03] min-h-[500px]">
            {/* Gradient overlay on hover */}
            <div className="absolute inset-0 bg-gradient-to-br from-green-50/40 to-green-100/40 dark:from-green-950/40 dark:to-green-900/40 opacity-0 group-hover:opacity-100 transition-opacity duration-700 ease-out pointer-events-none" />
            
            {/* Subtle shine effect */}
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-700 ease-out pointer-events-none" />
            
            <CardHeader className="text-center relative z-10">
              <div className="flex justify-center mb-6">
                <div className="p-6 bg-green-50 dark:bg-green-950 rounded-full group-hover:scale-110 group-hover:rotate-6 transition-all duration-500 ease-out shadow-md group-hover:shadow-xl">
                  <Satellite className="h-16 w-16 text-green-600 dark:text-green-400 group-hover:animate-pulse" />
                </div>
              </div>
              <CardTitle className="text-2xl text-green-700 dark:text-green-400 mb-4 group-hover:scale-105 transition-transform duration-500">
                NASA Satellites
              </CardTitle>
            </CardHeader>
            <CardContent className="text-left px-6 relative z-10">
              <div className="space-y-4 mb-6">
                <div className="flex items-start gap-3 group/item hover:translate-x-1 transition-transform duration-300">
                  <Radio className="h-5 w-5 text-green-600 mt-0.5 flex-shrink-0 group-hover/item:scale-125 transition-transform duration-300" />
                  <div>
                    <p className="font-bold text-gray-900 dark:text-white">Sentinel-2</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">10m resolution • High precision imaging</p>
                  </div>
                </div>
                <div className="flex items-start gap-3 group/item hover:translate-x-1 transition-transform duration-300">
                  <Radio className="h-5 w-5 text-green-600 mt-0.5 flex-shrink-0 group-hover/item:scale-125 transition-transform duration-300" />
                  <div>
                    <p className="font-bold text-gray-900 dark:text-white">Landsat 8/9</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">30m resolution • 40+ year history</p>
                  </div>
                </div>
                <div className="flex items-start gap-3 group/item hover:translate-x-1 transition-transform duration-300">
                  <Radio className="h-5 w-5 text-green-600 mt-0.5 flex-shrink-0 group-hover/item:scale-125 transition-transform duration-300" />
                  <div>
                    <p className="font-bold text-gray-900 dark:text-white">MODIS (Terra/Aqua)</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">1km resolution • Daily coverage</p>
                  </div>
                </div>
              </div>
              
              <div className="mt-6 p-4 bg-green-100 dark:bg-green-900/30 rounded-lg border border-green-300 dark:border-green-700">
                <p className="font-bold text-sm text-green-800 dark:text-green-300 mb-3 flex items-center gap-2">
                  <Globe className="h-4 w-4" />
                  Datasets Used:
                </p>
                <ul className="text-xs text-gray-700 dark:text-gray-300 space-y-1.5">
                  <li className="flex items-center gap-2">
                    <CheckCircle className="h-3 w-3 text-green-600" />
                    Landsat ARI (Anthocyanin)
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle className="h-3 w-3 text-green-600" />
                    MODIS NDVI (Vegetation)
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle className="h-3 w-3 text-green-600" />
                    Sentinel-2 ARI & NDVI
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle className="h-3 w-3 text-green-600" />
                    CHIRPS (Rainfall Data)
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle className="h-3 w-3 text-green-600" />
                    NDVI Anomaly Detection
                  </li>
                </ul>
              </div>
            </CardContent>
          </Card>

          {/* USSD & SMS Alerts Card */}
          <Card data-aos="fade-up" data-aos-delay="200" className="group relative overflow-hidden bg-white dark:bg-gray-900 rounded-[20px] border-2 border-transparent hover:border-blue-600 dark:hover:border-blue-500 shadow-lg hover:shadow-2xl transition-all duration-700 ease-out hover:-translate-y-3 hover:scale-[1.03] min-h-[500px]">
            {/* Gradient overlay on hover */}
            <div className="absolute inset-0 bg-gradient-to-br from-blue-50/40 to-blue-100/40 dark:from-blue-950/40 dark:to-blue-900/40 opacity-0 group-hover:opacity-100 transition-opacity duration-700 ease-out pointer-events-none" />
            
            {/* Subtle shine effect */}
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-700 ease-out pointer-events-none" />
            
            <CardHeader className="text-center relative z-10">
              <div className="flex justify-center mb-6">
                <div className="p-6 bg-blue-50 dark:bg-blue-950 rounded-full group-hover:scale-110 group-hover:-rotate-6 transition-all duration-500 ease-out shadow-md group-hover:shadow-xl">
                  <Smartphone className="h-16 w-16 text-blue-600 dark:text-blue-400 group-hover:animate-pulse" />
                </div>
              </div>
              <CardTitle className="text-2xl text-blue-700 dark:text-blue-400 mb-4 group-hover:scale-105 transition-transform duration-500">
                USSD & SMS Alerts
              </CardTitle>
            </CardHeader>
            <CardContent className="text-left px-6 relative z-10">
              <div className="space-y-4 mb-6">
                <div className="flex items-start gap-3 group/item hover:translate-x-1 transition-transform duration-300">
                  <Phone className="h-5 w-5 text-blue-600 mt-0.5 flex-shrink-0 group-hover/item:scale-125 transition-transform duration-300" />
                  <div>
                    <p className="font-bold text-gray-900 dark:text-white">Works on ANY phone</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">Feature phones supported</p>
                  </div>
                </div>
                <div className="flex items-start gap-3 group/item hover:translate-x-1 transition-transform duration-300">
                  <WifiOff className="h-5 w-5 text-blue-600 mt-0.5 flex-shrink-0 group-hover/item:scale-125 transition-transform duration-300" />
                  <div>
                    <p className="font-bold text-gray-900 dark:text-white">No internet required</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">USSD works offline</p>
                  </div>
                </div>
                <div className="flex items-start gap-3 group/item hover:translate-x-1 transition-transform duration-300">
                  <Zap className="h-5 w-5 text-blue-600 mt-0.5 flex-shrink-0 group-hover/item:scale-125 transition-transform duration-300" />
                  <div>
                    <p className="font-bold text-gray-900 dark:text-white">Instant SMS alerts</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">Bloom notifications in &lt; 30s</p>
                  </div>
                </div>
                <div className="flex items-start gap-3 group/item hover:translate-x-1 transition-transform duration-300">
                  <Globe className="h-5 w-5 text-blue-600 mt-0.5 flex-shrink-0 group-hover/item:scale-125 transition-transform duration-300" />
                  <div>
                    <p className="font-bold text-gray-900 dark:text-white">Bilingual support</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">English & Kiswahili</p>
                  </div>
                </div>
              </div>
              
              <div className="mt-6 p-4 bg-blue-100 dark:bg-blue-900/30 rounded-lg border-2 border-blue-300 dark:border-blue-700 text-center hover:bg-blue-200 dark:hover:bg-blue-900/50 hover:border-blue-400 dark:hover:border-blue-600 transition-all duration-500 hover:shadow-lg cursor-pointer group/cta">
                <p className="text-2xl font-bold text-blue-800 dark:text-blue-300 flex items-center justify-center gap-2 group-hover/cta:scale-105 transition-transform duration-300">
                  <Phone className="h-6 w-6 group-hover/cta:rotate-12 transition-transform duration-300" />
                  Dial: *384*42434#
                </p>
                <p className="text-xs text-gray-600 dark:text-gray-400 mt-2">
                  Access bloom data from any phone
                </p>
              </div>
            </CardContent>
          </Card>

          {/* AI-Powered Chatbot Card */}
          <Card data-aos="fade-up" data-aos-delay="400" className="group relative overflow-hidden bg-white dark:bg-gray-900 rounded-[20px] border-2 border-transparent hover:border-purple-600 dark:hover:border-purple-500 shadow-lg hover:shadow-2xl transition-all duration-700 ease-out hover:-translate-y-3 hover:scale-[1.03] min-h-[500px]">
            {/* Gradient overlay on hover */}
            <div className="absolute inset-0 bg-gradient-to-br from-purple-50/40 to-purple-100/40 dark:from-purple-950/40 dark:to-purple-900/40 opacity-0 group-hover:opacity-100 transition-opacity duration-700 ease-out pointer-events-none" />
            
            {/* Subtle shine effect */}
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-700 ease-out pointer-events-none" />
            
            <CardHeader className="text-center relative z-10">
              <div className="flex justify-center mb-6">
                <div className="p-6 bg-purple-50 dark:bg-purple-950 rounded-full group-hover:scale-110 group-hover:rotate-12 transition-all duration-500 ease-out shadow-md group-hover:shadow-xl">
                  <BrainCircuit className="h-16 w-16 text-purple-600 dark:text-purple-400 group-hover:animate-pulse" />
                </div>
              </div>
              <CardTitle className="text-2xl text-purple-700 dark:text-purple-400 mb-4 group-hover:scale-105 transition-transform duration-500">
                AI-Powered Chatbot
              </CardTitle>
            </CardHeader>
            <CardContent className="text-left px-6 relative z-10">
              <div className="space-y-4 mb-6">
                <div className="flex items-start gap-3 group/item hover:translate-x-1 transition-transform duration-300">
                  <Sprout className="h-5 w-5 text-purple-600 mt-0.5 flex-shrink-0 group-hover/item:scale-125 group-hover/item:rotate-12 transition-all duration-300" />
                  <div>
                    <p className="font-bold text-gray-900 dark:text-white">Meet Flora</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">Your MauaMentor AI assistant</p>
                  </div>
                </div>
                <div className="flex items-start gap-3 group/item hover:translate-x-1 transition-transform duration-300">
                  <Sprout className="h-5 w-5 text-purple-600 mt-0.5 flex-shrink-0 group-hover/item:scale-125 group-hover/item:rotate-12 transition-all duration-300" />
                  <div>
                    <p className="font-bold text-gray-900 dark:text-white">Planting advice</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">When & what to plant</p>
                  </div>
                </div>
                <div className="flex items-start gap-3 group/item hover:translate-x-1 transition-transform duration-300">
                  <TrendingUp className="h-5 w-5 text-purple-600 mt-0.5 flex-shrink-0 group-hover/item:scale-125 transition-transform duration-300" />
                  <div>
                    <p className="font-bold text-gray-900 dark:text-white">Bloom predictions</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">ML-powered optimal timing guidance</p>
                  </div>
                </div>
                <div className="flex items-start gap-3 group/item hover:translate-x-1 transition-transform duration-300">
                  <Shield className="h-5 w-5 text-purple-600 mt-0.5 flex-shrink-0 group-hover/item:scale-125 transition-transform duration-300" />
                  <div>
                    <p className="font-bold text-gray-900 dark:text-white">Climate adaptation</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">Weather-smart strategies</p>
                  </div>
                </div>
              </div>
              
              <div className="mt-6 p-4 bg-purple-100 dark:bg-purple-900/30 rounded-lg border border-purple-300 dark:border-purple-700">
                <p className="font-bold text-sm text-purple-800 dark:text-purple-300 mb-3 flex items-center gap-2">
                  <BrainCircuit className="h-4 w-4" />
                  Powered By:
                </p>
                <ul className="text-xs text-gray-700 dark:text-gray-300 space-y-1.5">
                  <li className="flex items-center gap-2">
                    <CheckCircle className="h-3 w-3 text-purple-600" />
                    OpenAI GPT-4 (Advanced AI)
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle className="h-3 w-3 text-purple-600" />
                    Trained ML Model (NASA data)
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle className="h-3 w-3 text-purple-600" />
                    Real-time satellite insights
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle className="h-3 w-3 text-purple-600" />
                    Kenya agricultural expertise
                  </li>
                </ul>
              </div>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* Meet Flora - AI MauaMentor Section */}
      <section className="bg-gradient-to-b from-white to-green-50/30 dark:from-gray-950 dark:to-green-950/30 py-20">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold text-green-700 dark:text-green-400 mb-4 mobile-heading">
              🌺 Meet Flora - Your AI MauaMentor
            </h2>
            <p className="text-gray-600 dark:text-gray-300 text-base md:text-lg max-w-2xl mx-auto">
              Get instant agricultural guidance powered by advanced AI
            </p>
          </div>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-12">
            {/* Left Side - Flora Description */}
            <Card className="group relative overflow-hidden bg-white dark:bg-gray-900 rounded-2xl border-2 border-green-200 dark:border-green-800 shadow-lg hover:shadow-2xl transition-all duration-700 ease-in-out hover:-translate-y-2">
              {/* Subtle gradient background */}
              <div className="absolute inset-0 bg-gradient-to-br from-green-50/30 to-transparent dark:from-green-950/30 opacity-0 group-hover:opacity-100 transition-opacity duration-700" />
              
              <CardHeader className="relative z-10">
                <CardTitle className="flex items-center gap-3 text-xl md:text-2xl text-green-700 dark:text-green-400 mb-4">
                  <MessageSquare className="h-6 w-6 md:h-7 md:w-7" />
                  Flora, Your Agricultural AI Assistant
                </CardTitle>
              </CardHeader>
              
              <CardContent className="relative z-10 px-4 md:px-6">
                <p className="text-base md:text-lg leading-relaxed mb-6 text-gray-700 dark:text-gray-300">
                  Flora uses advanced AI to provide <span className="font-bold text-green-600">instant agricultural guidance</span>:
                </p>
                
                <ul className="space-y-3 md:space-y-4 mb-6">
                  <li className="flex items-start gap-3 group/item hover:translate-x-1 transition-transform duration-300">
                    <Sprout className="h-5 w-5 text-green-600 mt-0.5 flex-shrink-0 group-hover/item:scale-125 group-hover/item:rotate-12 transition-all duration-300" />
                    <div>
                      <span className="font-bold text-gray-900 dark:text-white">Planting advice</span>
                      <span className="text-gray-600 dark:text-gray-400"> tailored to your region</span>
                    </div>
                  </li>
                  <li className="flex items-start gap-3 group/item hover:translate-x-1 transition-transform duration-300">
                    <TrendingUp className="h-5 w-5 text-green-600 mt-0.5 flex-shrink-0 group-hover/item:scale-125 transition-transform duration-300" />
                    <div>
                      <span className="font-bold text-gray-900 dark:text-white">Bloom predictions</span>
                      <span className="text-gray-600 dark:text-gray-400"> for optimal timing</span>
                    </div>
                  </li>
                  <li className="flex items-start gap-3 group/item hover:translate-x-1 transition-transform duration-300">
                    <Cloud className="h-5 w-5 text-green-600 mt-0.5 flex-shrink-0 group-hover/item:scale-125 transition-transform duration-300" />
                    <div>
                      <span className="font-bold text-gray-900 dark:text-white">Climate adaptation</span>
                      <span className="text-gray-600 dark:text-gray-400"> strategies</span>
                    </div>
                  </li>
                  <li className="flex items-start gap-3 group/item hover:translate-x-1 transition-transform duration-300">
                    <Sprout className="h-5 w-5 text-green-600 mt-0.5 flex-shrink-0 group-hover/item:scale-125 group-hover/item:rotate-12 transition-all duration-300" />
                    <div>
                      <span className="font-bold text-gray-900 dark:text-white">Crop health</span>
                      <span className="text-gray-600 dark:text-gray-400"> monitoring guidance</span>
                    </div>
                  </li>
                  <li className="flex items-start gap-3 group/item hover:translate-x-1 transition-transform duration-300">
                    <Smartphone className="h-5 w-5 text-green-600 mt-0.5 flex-shrink-0 group-hover/item:scale-125 transition-transform duration-300" />
                    <div>
                      <span className="font-bold text-gray-900 dark:text-white">Accessible via USSD</span>
                      <span className="text-gray-600 dark:text-gray-400"> - works on any phone</span>
                    </div>
                  </li>
                  <li className="flex items-start gap-3 group/item hover:translate-x-1 transition-transform duration-300">
                    <Globe className="h-5 w-5 text-green-600 mt-0.5 flex-shrink-0 group-hover/item:scale-125 transition-transform duration-300" />
                    <div>
                      <span className="text-gray-600 dark:text-gray-400">Available in </span>
                      <span className="font-bold text-gray-900 dark:text-white">English & Kiswahili</span>
                    </div>
                  </li>
                </ul>
                
                <Link href={isAuthenticated && farmer ? "/dashboard" : "/login"}>
                  <Button className="w-full bg-green-600 hover:bg-green-700 text-white py-6 text-base md:text-lg rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105">
                    <MessageSquare className="mr-2 h-5 w-5" />
                    Chat with Flora Now
                  </Button>
                </Link>
              </CardContent>
            </Card>

            {/* Right Side - Mock Chat Interface */}
            <div className="bg-gradient-to-br from-green-50 to-green-100 dark:from-green-950/50 dark:to-green-900/50 p-4 md:p-6 rounded-2xl border-2 border-green-200 dark:border-green-800 shadow-lg hover:shadow-xl transition-shadow duration-500 min-h-[400px] flex flex-col">
              <div className="flex items-center gap-3 mb-6 pb-4 border-b border-green-300 dark:border-green-700">
                <div className="p-2 bg-green-600 rounded-full animate-pulse">
                  <MessageSquare className="h-5 w-5 text-white" />
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <h3 className="font-bold text-green-800 dark:text-green-300">Flora AI Chat</h3>
                    <div className="flex gap-1">
                      <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                      <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }}></div>
                      <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" style={{ animationDelay: '0.4s' }}></div>
                    </div>
                  </div>
                  <p className="text-xs text-gray-600 dark:text-gray-400">Example conversation</p>
                </div>
              </div>
              
              <div className="flex-1 space-y-4 overflow-y-auto">
                {/* User Message 1 */}
                <div className="flex justify-end animate-fade-in" style={{ animationDelay: '0.2s' }}>
                  <div className="bg-white dark:bg-gray-800 rounded-xl rounded-tr-sm px-4 py-3 max-w-[85%] shadow-md hover:shadow-lg transition-shadow duration-300">
                    <p className="text-sm text-gray-700 dark:text-gray-300">
                      <span className="font-bold text-gray-900 dark:text-white">You:</span> When should I plant maize in Nyeri?
                    </p>
                  </div>
                </div>
                
                {/* Flora Response 1 */}
                <div className="flex justify-start animate-fade-in" style={{ animationDelay: '0.4s' }}>
                  <div className="bg-green-600 dark:bg-green-700 rounded-xl rounded-tl-sm px-4 py-3 max-w-[85%] shadow-md hover:shadow-lg transition-shadow duration-300">
                    <p className="text-sm text-white leading-relaxed">
                      <span className="font-bold">🌺 Flora:</span> Great question! In Nyeri, the best time to plant maize is during the long rains season (March-April). The current soil moisture is optimal, and temperatures are favorable at 19°C. I recommend planting hybrid varieties for your altitude.
                    </p>
                  </div>
                </div>
                
                {/* User Message 2 */}
                <div className="flex justify-end animate-fade-in" style={{ animationDelay: '0.6s' }}>
                  <div className="bg-white dark:bg-gray-800 rounded-xl rounded-tr-sm px-4 py-3 max-w-[85%] shadow-md hover:shadow-lg transition-shadow duration-300">
                    <p className="text-sm text-gray-700 dark:text-gray-300">
                      <span className="font-bold text-gray-900 dark:text-white">You:</span> Is it blooming in Kitale now?
                    </p>
                  </div>
                </div>
                
                {/* Flora Response 2 */}
                <div className="flex justify-start animate-fade-in" style={{ animationDelay: '0.8s' }}>
                  <div className="bg-green-600 dark:bg-green-700 rounded-xl rounded-tl-sm px-4 py-3 max-w-[85%] shadow-md hover:shadow-lg transition-shadow duration-300">
                    <p className="text-sm text-white leading-relaxed">
                      <span className="font-bold">🌺 Flora:</span> Yes! Kitale is showing 65% bloom activity for maize. This is a good sign for pollination. Ensure adequate irrigation and watch for pest activity during this critical stage.
                    </p>
                  </div>
                </div>
              </div>
              
              <div className="mt-4 pt-4 border-t border-green-300 dark:border-green-700">
                <p className="text-xs text-center text-gray-600 dark:text-gray-400">
                  💡 Flora combines NASA satellite data with AI to provide real-time farming advice
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* BloomWatch Kenya Expected Impact */}
      <section className="bg-white dark:bg-gray-950 py-16 md:py-20">
        <div className="container mx-auto px-4">
          <div className="text-center mb-12 md:mb-16" data-aos="fade-down">
            <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold text-green-700 dark:text-green-400 mb-4 mobile-heading">
              BloomWatch Kenya Expected Impact
            </h2>
            <p className="text-base md:text-lg font-semibold text-gray-700 dark:text-gray-300">
              Empowering thousands of farmers across Kenya
            </p>
          </div>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 md:gap-8">
            {/* Stat 1: Farmers Registered */}
            <Card data-aos="fade-up" className="group relative overflow-hidden bg-gradient-to-br from-white to-gray-50 dark:from-gray-900 dark:to-gray-800 rounded-2xl border-2 border-green-100 dark:border-green-900 hover:border-green-500 dark:hover:border-green-400 shadow-lg hover:shadow-[0_20px_40px_rgba(46,125,50,0.15)] transition-all duration-700 ease-out hover:-translate-y-3 hover:scale-[1.03] min-h-[350px] md:min-h-[400px] flex flex-col justify-center">
              {/* Subtle gradient glow on hover */}
              <div className="absolute inset-0 bg-gradient-to-br from-green-500/10 via-green-400/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-700 ease-out" />
              
              <CardContent className="text-center p-6 md:p-10 relative z-10">
                {/* Icon */}
                <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-gradient-to-br from-green-600 to-green-400 flex items-center justify-center shadow-[0_4px_15px_rgba(46,125,50,0.3)] group-hover:shadow-[0_8px_25px_rgba(46,125,50,0.4)] group-hover:scale-110 group-hover:rotate-[5deg] transition-all duration-500">
                  <Users className="h-10 w-10 text-white" />
                </div>
                
                {/* Number */}
                <h3 className="text-4xl md:text-5xl lg:text-[3.5rem] font-bold text-green-700 dark:text-green-400 mb-3 group-hover:scale-105 group-hover:drop-shadow-[0_2px_10px_rgba(46,125,50,0.2)] transition-all duration-300 ease-in-out">
                  5,000+
                </h3>
                
                {/* Label */}
                <p className="text-lg md:text-xl font-semibold text-gray-900 dark:text-white mb-2">
                  Farmers Registered
                </p>
                
                {/* Subtitle */}
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Across Kenya
                </p>
              </CardContent>
            </Card>

            {/* Stat 2: Yield Increase */}
            <Card data-aos="fade-up" data-aos-delay="200" className="group relative overflow-hidden bg-gradient-to-br from-white to-gray-50 dark:from-gray-900 dark:to-gray-800 rounded-2xl border-2 border-orange-100 dark:border-orange-900 hover:border-orange-500 dark:hover:border-orange-400 shadow-lg hover:shadow-[0_20px_40px_rgba(245,124,0,0.15)] transition-all duration-700 ease-out hover:-translate-y-3 hover:scale-[1.03] min-h-[350px] md:min-h-[400px] flex flex-col justify-center">
              {/* Subtle gradient glow on hover */}
              <div className="absolute inset-0 bg-gradient-to-br from-orange-500/10 via-orange-400/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-700 ease-out" />
              
              <CardContent className="text-center p-6 md:p-10 relative z-10">
                {/* Icon */}
                <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-gradient-to-br from-orange-600 to-orange-400 flex items-center justify-center shadow-[0_4px_15px_rgba(245,124,0,0.3)] group-hover:shadow-[0_8px_25px_rgba(245,124,0,0.4)] group-hover:scale-110 group-hover:rotate-[5deg] transition-all duration-500">
                  <TrendingUp className="h-10 w-10 text-white" />
                </div>
                
                {/* Number */}
                <h3 className="text-4xl md:text-5xl lg:text-[3.5rem] font-bold text-orange-600 dark:text-orange-400 mb-3 group-hover:scale-105 group-hover:drop-shadow-[0_2px_10px_rgba(245,124,0,0.2)] transition-all duration-300 ease-in-out">
                  30%
                </h3>
                
                {/* Label */}
                <p className="text-lg md:text-xl font-semibold text-gray-900 dark:text-white mb-2">
                  Avg Yield Increase
                </p>
                
                {/* Subtitle */}
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Validated with farmers
                </p>
              </CardContent>
            </Card>

            {/* Stat 3: Counties Covered */}
            <Card data-aos="fade-up" data-aos-delay="400" className="group relative overflow-hidden bg-gradient-to-br from-white to-gray-50 dark:from-gray-900 dark:to-gray-800 rounded-2xl border-2 border-blue-100 dark:border-blue-900 hover:border-blue-500 dark:hover:border-blue-400 shadow-lg hover:shadow-[0_20px_40px_rgba(25,118,210,0.15)] transition-all duration-700 ease-out hover:-translate-y-3 hover:scale-[1.03] min-h-[350px] md:min-h-[400px] flex flex-col justify-center">
              {/* Subtle gradient glow on hover */}
              <div className="absolute inset-0 bg-gradient-to-br from-blue-500/10 via-blue-400/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-700 ease-out" />
              
              <CardContent className="text-center p-6 md:p-10 relative z-10">
                {/* Icon */}
                <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-gradient-to-br from-blue-600 to-blue-400 flex items-center justify-center shadow-[0_4px_15px_rgba(25,118,210,0.3)] group-hover:shadow-[0_8px_25px_rgba(25,118,210,0.4)] group-hover:scale-110 group-hover:rotate-[5deg] transition-all duration-500">
                  <MapPin className="h-10 w-10 text-white" />
                </div>
                
                {/* Number */}
                <h3 className="text-4xl md:text-5xl lg:text-[3.5rem] font-bold text-blue-600 dark:text-blue-400 mb-3 group-hover:scale-105 group-hover:drop-shadow-[0_2px_10px_rgba(25,118,210,0.2)] transition-all duration-300 ease-in-out">
                  47
                </h3>
                
                {/* Label */}
                <p className="text-lg md:text-xl font-semibold text-gray-900 dark:text-white mb-2">
                  Counties Covered
                </p>
                
                {/* Subtitle */}
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Nationwide reach
                </p>
              </CardContent>
            </Card>

            {/* Stat 4: Extra Income */}
            <Card data-aos="fade-up" data-aos-delay="600" className="group relative overflow-hidden bg-gradient-to-br from-white to-gray-50 dark:from-gray-900 dark:to-gray-800 rounded-2xl border-2 border-emerald-100 dark:border-emerald-900 hover:border-emerald-500 dark:hover:border-emerald-400 shadow-lg hover:shadow-[0_20px_40px_rgba(56,142,60,0.15)] transition-all duration-700 ease-out hover:-translate-y-3 hover:scale-[1.03] min-h-[350px] md:min-h-[400px] flex flex-col justify-center">
              {/* Subtle gradient glow on hover */}
              <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/10 via-emerald-400/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-700 ease-out" />
              
              <CardContent className="text-center p-6 md:p-10 relative z-10">
                {/* Icon */}
                <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-gradient-to-br from-emerald-600 to-emerald-400 flex items-center justify-center shadow-[0_4px_15px_rgba(56,142,60,0.3)] group-hover:shadow-[0_8px_25px_rgba(56,142,60,0.4)] group-hover:scale-110 group-hover:rotate-[5deg] transition-all duration-500">
                  <BarChart3 className="h-10 w-10 text-white" />
                </div>
                
                {/* Number */}
                <h3 className="text-4xl md:text-5xl lg:text-[3.5rem] font-bold text-emerald-600 dark:text-emerald-400 mb-3 group-hover:scale-105 group-hover:drop-shadow-[0_2px_10px_rgba(56,142,60,0.2)] transition-all duration-300 ease-in-out">
                  $500
                </h3>
                
                {/* Label */}
                <p className="text-lg md:text-xl font-semibold text-gray-900 dark:text-white mb-2">
                  Extra Income/Season
                </p>
                
                {/* Subtitle */}
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Per farmer average
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Farmer Success Stories */}
      <section className="bg-gradient-to-b from-green-50/50 to-white dark:from-green-950/30 dark:to-gray-950 py-16 md:py-20">
        <div className="container mx-auto px-4">
          <div className="text-center mb-12 md:mb-16">
            <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold text-green-700 dark:text-green-400 mb-4 mobile-heading">
              👥 Farmer Success Stories
            </h2>
            <p className="text-base md:text-lg font-semibold text-gray-700 dark:text-gray-300">
              Real farmers, real results across Kenya's diverse regions
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 md:gap-8 mb-12 md:mb-16">
            {/* Testimonial 1: Jane Wanjiru */}
            <Card className="group relative overflow-hidden bg-white dark:bg-gray-900 rounded-2xl border-2 border-green-100 dark:border-green-800 hover:border-green-600 dark:hover:border-green-500 shadow-lg hover:shadow-2xl transition-all duration-700 ease-out hover:-translate-y-2 hover:scale-[1.02]">
              {/* Subtle glow on hover */}
              <div className="absolute inset-0 bg-gradient-to-br from-green-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-700" />
              
              <CardContent className="text-center p-6 md:p-8 relative z-10">
                {/* Avatar */}
                <div className="w-20 h-20 mx-auto mb-4 rounded-full bg-gradient-to-br from-green-600 to-green-400 flex items-center justify-center text-white text-3xl font-bold shadow-lg group-hover:shadow-xl group-hover:scale-110 transition-all duration-500">
                  JW
                </div>
                
                {/* Name */}
                <h3 className="text-xl md:text-2xl font-bold text-green-700 dark:text-green-400 mb-2">
                  Jane Wanjiru
                </h3>
                
                {/* Role */}
                <p className="text-sm md:text-base font-semibold text-gray-600 dark:text-gray-400 mb-4">
                  Maize Farmer - Nakuru
                </p>
                
                {/* Quote */}
                <p className="text-sm md:text-base italic leading-relaxed text-gray-700 dark:text-gray-300 mb-4">
                  "BloomWatch helped me plant at the right time, and my maize yield doubled! The SMS alerts in Kiswahili made it so easy to understand."
                </p>
                
                {/* Rating */}
                <div className="flex justify-center gap-1 text-orange-500">
                  {[...Array(5)].map((_, i) => (
                    <span key={i} className="text-xl">⭐</span>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Testimonial 2: Peter Kamau */}
            <Card className="group relative overflow-hidden bg-white dark:bg-gray-900 rounded-2xl border-2 border-green-100 dark:border-green-800 hover:border-green-600 dark:hover:border-green-500 shadow-lg hover:shadow-2xl transition-all duration-700 ease-out hover:-translate-y-2 hover:scale-[1.02]">
              {/* Subtle glow on hover */}
              <div className="absolute inset-0 bg-gradient-to-br from-green-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-700" />
              
              <CardContent className="text-center p-6 md:p-8 relative z-10">
                {/* Avatar */}
                <div className="w-20 h-20 mx-auto mb-4 rounded-full bg-gradient-to-br from-blue-600 to-blue-400 flex items-center justify-center text-white text-3xl font-bold shadow-lg group-hover:shadow-xl group-hover:scale-110 transition-all duration-500">
                  PK
                </div>
                
                {/* Name */}
                <h3 className="text-xl md:text-2xl font-bold text-green-700 dark:text-green-400 mb-2">
                  Peter Kamau
                </h3>
                
                {/* Role */}
                <p className="text-sm md:text-base font-semibold text-gray-600 dark:text-gray-400 mb-4">
                  Coffee Farmer - Kericho
                </p>
                
                {/* Quote */}
                <p className="text-sm md:text-base italic leading-relaxed text-gray-700 dark:text-gray-300 mb-4">
                  "The bloom alerts helped me time my coffee harvest perfectly. I upgraded from Grade B to Grade A beans and got 40% better prices!"
                </p>
                
                {/* Rating */}
                <div className="flex justify-center gap-1 text-orange-500">
                  {[...Array(5)].map((_, i) => (
                    <span key={i} className="text-xl">⭐</span>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Testimonial 3: Mary Atieno */}
            <Card className="group relative overflow-hidden bg-white dark:bg-gray-900 rounded-2xl border-2 border-green-100 dark:border-green-800 hover:border-green-600 dark:hover:border-green-500 shadow-lg hover:shadow-2xl transition-all duration-700 ease-out hover:-translate-y-2 hover:scale-[1.02]">
              {/* Subtle glow on hover */}
              <div className="absolute inset-0 bg-gradient-to-br from-green-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-700" />
              
              <CardContent className="text-center p-6 md:p-8 relative z-10">
                {/* Avatar */}
                <div className="w-20 h-20 mx-auto mb-4 rounded-full bg-gradient-to-br from-purple-600 to-purple-400 flex items-center justify-center text-white text-3xl font-bold shadow-lg group-hover:shadow-xl group-hover:scale-110 transition-all duration-500">
                  MA
                </div>
                
                {/* Name */}
                <h3 className="text-xl md:text-2xl font-bold text-green-700 dark:text-green-400 mb-2">
                  Mary Atieno
                </h3>
                
                {/* Role */}
                <p className="text-sm md:text-base font-semibold text-gray-600 dark:text-gray-400 mb-4">
                  Vegetable Grower - Machakos
                </p>
                
                {/* Quote */}
                <p className="text-sm md:text-base italic leading-relaxed text-gray-700 dark:text-gray-300 mb-4">
                  "Flora taught me about intercropping and climate patterns. I prevented 20% crop loss with timely fungicide application!"
                </p>
                
                {/* Rating */}
                <div className="flex justify-center gap-1 text-orange-500">
                  {[...Array(5)].map((_, i) => (
                    <span key={i} className="text-xl">⭐</span>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Featured Farmer Spotlight */}
          <Card className="group relative overflow-hidden bg-gradient-to-br from-white to-green-50/30 dark:from-gray-900 dark:to-green-950/30 rounded-2xl border-2 border-green-200 dark:border-green-800 hover:border-green-600 dark:hover:border-green-500 shadow-xl hover:shadow-2xl transition-all duration-700 ease-out">
            {/* Glow overlay */}
            <div className="absolute inset-0 bg-gradient-to-br from-green-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-700" />
            
            {/* Decorative corner accent */}
            <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-green-500/10 to-transparent rounded-bl-full opacity-0 group-hover:opacity-100 transition-opacity duration-700" />
            
            <CardContent className="p-0">
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-0">
                {/* Left: Farmer Image */}
                <div className="lg:col-span-1 p-0 bg-gradient-to-br from-green-600 to-green-400 flex flex-col items-center justify-center text-white relative overflow-hidden min-h-[300px] lg:min-h-[500px]">
                  {/* Image */}
                  <div className="absolute inset-0 w-full h-full">
                    <img 
                      src="/John_Kisumu.png" 
                      alt="John Odhiambo - Maize Farmer from Kisumu"
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700"
                    />
                  </div>
                  
                  {/* Overlay with name on image */}
                  <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/40 to-transparent flex flex-col items-center justify-end p-8 text-center z-10">
                    <h3 className="text-2xl md:text-3xl font-bold mb-2 drop-shadow-lg">John Odhiambo</h3>
                    <p className="text-base md:text-lg opacity-90 flex items-center gap-2 justify-center drop-shadow-md mb-4">
                      <MapPin className="h-4 w-4" />
                      Kisumu, Kenya
                    </p>
                    <div className="px-4 py-2 bg-white/20 backdrop-blur-sm rounded-full text-sm font-semibold">
                      Maize Farmer
                    </div>
                  </div>
                </div>
                
                {/* Right: Story */}
                <div className="lg:col-span-2 p-6 md:p-10 relative z-10">
                  <div className="flex flex-col sm:flex-row items-start gap-3 mb-6">
                    <div className="p-3 bg-green-100 dark:bg-green-900/30 rounded-xl group-hover:scale-110 transition-transform duration-500">
                      <Users className="h-7 w-7 text-green-600" />
                    </div>
                    <div className="flex-1">
                      <div className="flex flex-wrap items-center gap-2 mb-2">
                        <h4 className="text-xl md:text-2xl font-bold text-green-700 dark:text-green-400">
                          🌟 Featured Farmer
                        </h4>
                        <span className="px-3 py-1 bg-green-600 text-white text-xs font-bold rounded-full">
                          SUCCESS STORY
                        </span>
                      </div>
                      <p className="text-base md:text-lg text-gray-700 dark:text-gray-300 leading-relaxed">
                        John Odhiambo is a smallholder maize farmer from Kisumu, Kenya.
                      </p>
                    </div>
                  </div>
                  
                  <h5 className="font-bold text-gray-900 dark:text-white mb-4 text-base md:text-lg">
                    After joining BloomWatch:
                  </h5>
                  
                  <ul className="space-y-3 mb-6">
                    <li className="flex items-start gap-3 group/item hover:translate-x-1 transition-transform duration-300">
                      <BarChart3 className="h-5 w-5 text-green-600 mt-0.5 flex-shrink-0 group-hover/item:scale-125 transition-transform duration-300" />
                      <span className="text-sm md:text-base text-gray-700 dark:text-gray-300">
                        <span className="font-semibold">Increased maize yield</span> from 2.5 to 3.8 tons per acre (52% improvement)
                      </span>
                    </li>
                    <li className="flex items-start gap-3 group/item hover:translate-x-1 transition-transform duration-300">
                      <BarChart3 className="h-5 w-5 text-green-600 mt-0.5 flex-shrink-0 group-hover/item:scale-125 transition-transform duration-300" />
                      <span className="text-sm md:text-base text-gray-700 dark:text-gray-300">
                        <span className="font-semibold">Earned an extra</span> KSh 45,000 ($350) per season
                      </span>
                    </li>
                    <li className="flex items-start gap-3 group/item hover:translate-x-1 transition-transform duration-300">
                      <Cloud className="h-5 w-5 text-green-600 mt-0.5 flex-shrink-0 group-hover/item:scale-125 transition-transform duration-300" />
                      <span className="text-sm md:text-base text-gray-700 dark:text-gray-300">
                        <span className="font-semibold">Optimized irrigation timing</span> based on satellite rainfall data
                      </span>
                    </li>
                    <li className="flex items-start gap-3 group/item hover:translate-x-1 transition-transform duration-300">
                      <Sprout className="h-5 w-5 text-green-600 mt-0.5 flex-shrink-0 group-hover/item:scale-125 transition-transform duration-300" />
                      <span className="text-sm md:text-base text-gray-700 dark:text-gray-300">
                        <span className="font-semibold">Reduced fertilizer waste</span> by 30% through precision timing
                      </span>
                    </li>
                  </ul>
                  
                  {/* Quote */}
                  <div className="relative border-l-4 border-green-500 pl-4 md:pl-6 py-4 bg-green-50/50 dark:bg-green-950/30 rounded-r-lg group-hover:bg-green-100/50 dark:group-hover:bg-green-950/50 transition-colors duration-500">
                    <MessageSquare className="absolute -top-2 -left-2 h-8 w-8 text-green-500 bg-white dark:bg-gray-900 rounded-full p-1.5" />
                    <p className="text-sm md:text-base italic text-gray-700 dark:text-gray-300 leading-relaxed">
                      "The USSD system works perfectly on my basic phone. I get instant answers from Flora AI via USSD and receive SMS alerts before every rain. Flora helps me understand what the satellite data means for my farm. BloomWatch changed my life!"
                    </p>
                    <div className="flex items-center gap-2 mt-3 text-xs text-green-700 dark:text-green-400">
                      <CheckCircle className="h-4 w-4" />
                      <span className="font-semibold">Verified farmer using USSD + SMS + Flora AI</span>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* Access BloomWatch on ANY Phone */}
      <section className="bg-white dark:bg-gray-950 py-16 md:py-20">
        <div className="container mx-auto px-4">
          <div className="text-center mb-12 md:mb-16">
            <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold text-green-700 dark:text-green-400 mb-4 flex items-center justify-center gap-3 mobile-heading">
              <Phone className="h-6 w-6 md:h-8 md:w-8" />
              Access BloomWatch on ANY Phone
            </h2>
            <p className="text-base md:text-lg font-semibold text-gray-700 dark:text-gray-300">
              No smartphone needed! Use USSD for instant updates
            </p>
          </div>
          
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 lg:gap-10">
            {/* Left: How USSD Works */}
            <Card className="group relative overflow-hidden bg-white dark:bg-gray-900 rounded-2xl border-2 border-green-100 dark:border-green-800 hover:border-green-600 dark:hover:border-green-500 shadow-lg hover:shadow-2xl transition-all duration-700 ease-out hover:-translate-y-2">
              <div className="absolute inset-0 bg-gradient-to-br from-green-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-700" />
              
              <CardHeader className="relative z-10">
                <CardTitle className="flex items-center gap-2 text-xl md:text-2xl text-green-700 dark:text-green-400">
                  <Phone className="h-6 w-6" />
                  How USSD Works
                </CardTitle>
              </CardHeader>
              
              <CardContent className="relative z-10 space-y-4">
                <div className="space-y-3">
                  <div className="flex items-start gap-3">
                    <div className="flex-shrink-0 w-8 h-8 bg-green-600 text-white rounded-full flex items-center justify-center font-bold text-sm">1</div>
                    <div>
                      <p className="text-sm md:text-base text-gray-700 dark:text-gray-300">
                        <span className="font-bold">Dial</span> <span className="text-orange-600 dark:text-orange-400 text-lg md:text-xl font-bold">*384*42434#</span>
                      </p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <div className="flex-shrink-0 w-8 h-8 bg-green-600 text-white rounded-full flex items-center justify-center font-bold text-sm">2</div>
                    <p className="text-sm md:text-base text-gray-700 dark:text-gray-300">
                      <span className="font-bold">Select language</span> (English/Kiswahili)
                    </p>
                  </div>
                  <div className="flex items-start gap-3">
                    <div className="flex-shrink-0 w-8 h-8 bg-green-600 text-white rounded-full flex items-center justify-center font-bold text-sm">3</div>
                    <p className="text-sm md:text-base text-gray-700 dark:text-gray-300">
                      <span className="font-bold">Enter</span> your name and region
                    </p>
                  </div>
                  <div className="flex items-start gap-3">
                    <div className="flex-shrink-0 w-8 h-8 bg-green-600 text-white rounded-full flex items-center justify-center font-bold text-sm">4</div>
                    <p className="text-sm md:text-base text-gray-700 dark:text-gray-300">
                      <span className="font-bold">Choose</span> crops you grow
                    </p>
                  </div>
                  <div className="flex items-start gap-3">
                    <div className="flex-shrink-0 w-8 h-8 bg-green-600 text-white rounded-full flex items-center justify-center font-bold text-sm">5</div>
                    <p className="text-sm md:text-base text-gray-700 dark:text-gray-300">
                      <span className="font-bold">Receive</span> instant SMS alerts!
                    </p>
                  </div>
                </div>
                
                <div className="mt-6 p-4 bg-green-50 dark:bg-green-950/30 rounded-xl border border-green-200 dark:border-green-700">
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-sm">
                      <CheckCircle className="h-4 w-4 text-green-600" />
                      <span className="font-bold text-gray-900 dark:text-white">Works on feature phones</span>
                    </div>
                    <div className="flex items-center gap-2 text-sm">
                      <CheckCircle className="h-4 w-4 text-green-600" />
                      <span className="font-bold text-gray-900 dark:text-white">No internet required</span>
                    </div>
                    <div className="flex items-center gap-2 text-sm">
                      <CheckCircle className="h-4 w-4 text-green-600" />
                      <span className="font-bold text-gray-900 dark:text-white">Registration takes &lt; 2 minutes</span>
                    </div>
                    <div className="flex items-center gap-2 text-sm">
                      <CheckCircle className="h-4 w-4 text-green-600" />
                      <span className="font-bold text-gray-900 dark:text-white">Free for all farmers</span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Center: Phone Mockup */}
            <div className="flex items-center justify-center">
              <div className="relative group/phone">
                {/* Phone device */}
                <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-[32px] p-6 shadow-2xl w-[320px] mx-auto group-hover/phone:scale-105 transition-transform duration-700">
                  {/* Phone screen */}
                  <div className="bg-white dark:bg-gray-100 rounded-[24px] p-6 min-h-[500px] relative flex flex-col">
                    {/* Status bar */}
                    <div className="mb-4">
                      <div className="h-2 w-16 bg-gray-300 rounded-full mx-auto mb-3"></div>
                      <div className="flex justify-between items-center text-xs text-gray-500 px-2 mb-2">
                        <span>📶 Safaricom</span>
                        <span>12:34 PM</span>
                        <span>🔋 85%</span>
                      </div>
                      <p className="text-sm font-bold text-gray-900 text-center">Dialing...</p>
                    </div>
                    
                    {/* Dial code display */}
                    <div className="bg-gray-100 p-2 rounded-lg mb-2 animate-pulse">
                      <p className="text-xl font-bold text-green-700 text-center font-mono tracking-widest">
                        *384*42434#
                      </p>
                    </div>
                    
                    {/* USSD Menu */}
                    <div className="bg-green-50 p-3 rounded-lg mb-2 text-left flex-grow">
                      <p className="text-xs leading-relaxed text-gray-900">
                        <span className="font-bold text-green-700">🌾 BloomWatch Kenya</span><br />
                        <span className="text-gray-600 text-xs">Karibu! Welcome!</span><br /><br />
                        <span className="font-semibold text-xs">Select language:</span><br />
                        <span className="font-semibold text-xs">1. English</span><br />
                        <span className="font-semibold text-xs">2. Kiswahili</span>
                      </p>
                    </div>
                    
                    {/* Full Keypad */}
                    <div className="grid grid-cols-3 gap-2 mb-4">
                      {[1, 2, 3, 4, 5, 6, 7, 8, 9, '*', 0, '#'].map((key, index) => (
                        <button
                          key={index}
                          className="bg-gray-200 hover:bg-gray-300 active:bg-gray-400 p-4 rounded-lg text-center font-bold text-lg text-gray-800 cursor-pointer transition-all duration-200 hover:scale-105 shadow-sm hover:shadow-md"
                        >
                          {key}
                        </button>
                      ))}
                    </div>
                    
                    {/* Call buttons */}
                    <div className="grid grid-cols-2 gap-3">
                      <button className="bg-red-500 hover:bg-red-600 p-2.5 rounded-lg text-white font-semibold text-sm transition-colors duration-200 flex items-center justify-center gap-1.5">
                        <Phone className="h-3.5 w-3.5 rotate-135" />
                        End
                      </button>
                      <button className="bg-green-600 hover:bg-green-700 p-2.5 rounded-lg text-white font-semibold text-sm transition-colors duration-200 flex items-center justify-center gap-1.5">
                        <Phone className="h-3.5 w-3.5" />
                        Call
                      </button>
                    </div>
                  </div>
                  
                  {/* Home button */}
                  <div className="mt-4 flex justify-center">
                    <div className="w-14 h-14 bg-gray-700 rounded-full shadow-lg group-hover/phone:bg-gray-600 transition-colors duration-300"></div>
                  </div>
                </div>
                
                {/* Floating labels */}
                <div className="absolute -left-6 top-1/4 hidden xl:block">
                  <div className="bg-green-600 text-white px-4 py-2 rounded-lg shadow-lg text-sm font-semibold animate-bounce">
                    Works offline! →
                  </div>
                </div>
                <div className="absolute -right-6 bottom-1/4 hidden xl:block">
                  <div className="bg-blue-600 text-white px-4 py-2 rounded-lg shadow-lg text-sm font-semibold animate-bounce" style={{ animationDelay: '0.5s' }}>
                    ← Any phone!
                  </div>
                </div>
              </div>
            </div>

            {/* Right: Sample SMS Alert */}
            <Card className="group relative overflow-hidden bg-white dark:bg-gray-900 rounded-2xl border-2 border-blue-100 dark:border-blue-800 hover:border-blue-600 dark:hover:border-blue-500 shadow-lg hover:shadow-2xl transition-all duration-700 ease-out hover:-translate-y-2">
              <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-700" />
              
              <CardHeader className="relative z-10">
                <CardTitle className="flex items-center gap-2 text-xl md:text-2xl text-blue-700 dark:text-blue-400">
                  <MessageSquare className="h-6 w-6" />
                  Sample SMS Alert
                </CardTitle>
              </CardHeader>
              
              <CardContent className="relative z-10">
                <div className="bg-blue-50 dark:bg-blue-950/30 p-4 md:p-6 rounded-xl border-l-4 border-blue-600">
                  <p className="text-xs text-gray-600 dark:text-gray-400 mb-3">+254-700-BLOOM</p>
                  <div className="space-y-3 text-sm md:text-base text-gray-900 dark:text-white leading-relaxed">
                    <p className="font-bold text-green-700 dark:text-green-400 text-base md:text-lg">
                      🌸 BloomWatch Alert
                    </p>
                    
                    <p>
                      Habari Jane! Maize blooming detected in Nakuru (2.3km from your farm).
                    </p>
                    
                    <div className="space-y-1">
                      <p><span className="font-bold">Intensity:</span> 85% (High)</p>
                      <p><span className="font-bold">Action:</span> Optimal time for pollination management. Ensure adequate moisture.</p>
                    </div>
                    
                    <p><span className="font-bold">Weather:</span> 24°C, 60% humidity</p>
                    
                    <p className="text-gray-700 dark:text-gray-300 pt-2 border-t border-blue-200 dark:border-blue-800">
                      Reply HELP for tips. - Flora 🌺
                    </p>
                  </div>
                </div>
                
                <p className="text-xs text-center text-gray-600 dark:text-gray-400 mt-4 flex items-center justify-center gap-2">
                  <Zap className="h-3 w-3" />
                  Delivered in &lt; 30 seconds
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Statistics */}
      <StatisticsSection />

      {/* CTA Section */}
      <CTASection />

      {/* From Kenyan Farms */}
      <section className="bg-gradient-to-b from-green-50/50 to-white dark:from-green-950/30 dark:to-gray-950 py-16 md:py-20">
        <div className="container mx-auto px-4">
          <h3 className="text-2xl md:text-3xl font-bold text-green-700 dark:text-green-400 mb-8 text-center mobile-heading" data-aos="fade-down">
            🌾 From Kenyan Farms
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Maize Blooming Card */}
            <div data-aos="fade-up" className="relative group overflow-hidden rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300 hover:-translate-y-2">
              <div className="relative h-[200px] md:h-[220px] bg-cover bg-center" style={{
                backgroundImage: "url('https://images.unsplash.com/photo-1625246333195-78d9c38ad449?w=400')"
              }}>
                <div className="absolute inset-0 bg-gradient-to-t from-green-900/80 via-transparent to-transparent" />
                <div className="absolute bottom-0 left-0 right-0 p-4 md:p-5">
                  <p className="text-white font-bold text-lg md:text-xl drop-shadow-lg">
                    Maize Blooming
                  </p>
                </div>
              </div>
            </div>

            {/* Coffee Harvest Card */}
            <div data-aos="fade-up" data-aos-delay="200" className="relative group overflow-hidden rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300 hover:-translate-y-2">
              <div className="relative h-[200px] md:h-[220px] bg-cover bg-center" style={{
                backgroundImage: "url('https://www.greenlife.co.ke/wp-content/uploads/2022/04/Coffee-Feeding-Greenlife.jpg')"
              }}>
                <div className="absolute inset-0 bg-gradient-to-t from-green-900/80 via-transparent to-transparent" />
                <div className="absolute bottom-0 left-0 right-0 p-4 md:p-5">
                  <p className="text-white font-bold text-lg md:text-xl drop-shadow-lg">
                    Coffee Harvest
                  </p>
                </div>
              </div>
            </div>

            {/* Tea Plantations Card */}
            <div data-aos="fade-up" data-aos-delay="400" className="relative group overflow-hidden rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300 hover:-translate-y-2">
              <div className="relative h-[200px] md:h-[220px] bg-cover bg-center" style={{
                backgroundImage: "url('https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=400')"
              }}>
                <div className="absolute inset-0 bg-gradient-to-t from-green-900/80 via-transparent to-transparent" />
                <div className="absolute bottom-0 left-0 right-0 p-4 md:p-5">
                  <p className="text-white font-bold text-lg md:text-xl drop-shadow-lg">
                    Tea Plantations
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Powered By Section - Animated Logo Marquee */}
      <section className="bg-gradient-to-br from-green-50/50 to-white dark:from-green-950/30 dark:to-gray-950 py-16 md:py-20 border-y border-green-200/50 dark:border-green-800/30">
        <div className="container mx-auto px-4">
          <h3 className="text-center text-gray-600 dark:text-gray-400 font-bold text-lg md:text-xl mb-10 md:mb-14 tracking-[0.15em] uppercase">
            Powered By
          </h3>
          
          {/* Marquee Container with Overflow Hidden */}
          <div className="relative w-full overflow-hidden">
            {/* Gradient Fade Overlays */}
            <div className="absolute left-0 top-0 bottom-0 w-24 md:w-40 bg-gradient-to-r from-white via-white/90 to-transparent dark:from-gray-950 dark:via-gray-950/90 dark:to-transparent z-10 pointer-events-none" />
            <div className="absolute right-0 top-0 bottom-0 w-24 md:w-40 bg-gradient-to-l from-white via-white/90 to-transparent dark:from-gray-950 dark:via-gray-950/90 dark:to-transparent z-10 pointer-events-none" />
            
            {/* Scrolling Logo Track - True Infinite Scroll with Multiple Duplicates */}
            <div className="marquee-container">
              <div className="marquee-content items-center">
                <div className="flex-shrink-0 w-32 md:w-40 h-16 md:h-20 flex items-center justify-center transition-transform duration-300 hover:scale-110">
                  <img
                    src="https://www.nasa.gov/wp-content/themes/nasa/assets/images/nasa-logo.svg"
                    alt="NASA"
                    className="max-w-full max-h-full object-contain filter grayscale-[30%] hover:grayscale-0 transition-all duration-300"
                  />
                </div>
                
                <div className="flex-shrink-0 w-32 md:w-40 h-16 md:h-20 flex items-center justify-center transition-transform duration-300 hover:scale-110">
                  <img
                    src="https://learn.digitalearthafrica.org/static/NewThemeUpdated/images/logo.79a4f6b72027.png"
                    alt="Digital Earth Africa"
                    className="max-w-full max-h-full object-contain filter grayscale-[30%] hover:grayscale-0 transition-all duration-300"
                  />
                </div>
                
                <div className="flex-shrink-0 w-32 md:w-40 h-16 md:h-20 flex items-center justify-center transition-transform duration-300 hover:scale-110">
                  <img
                    src="https://earthengine.google.com/static/images/earth_engine_logo.png"
                    alt="Google Earth Engine"
                    className="max-w-full max-h-full object-contain filter grayscale-[30%] hover:grayscale-0 transition-all duration-300"
                  />
                </div>
                
                <div className="flex-shrink-0 w-32 md:w-40 h-16 md:h-20 flex items-center justify-center transition-transform duration-300 hover:scale-110">
                  <img
                    src="https://www.esri.com/content/dam/esrisites/en-us/common/icons/product-logos/ArcGIS-Enterprise.png"
                    alt="ESRI"
                    className="max-w-full max-h-full object-contain filter grayscale-[30%] hover:grayscale-0 transition-all duration-300"
                  />
                </div>
                
                <div className="flex-shrink-0 w-32 md:w-40 h-16 md:h-20 flex items-center justify-center transition-transform duration-300 hover:scale-110">
                  <img
                    src="https://www.star-idaz.net/wp-content/uploads/2024/07/kalro-logo.webp"
                    alt="KALRO"
                    className="max-w-full max-h-full object-contain filter grayscale-[30%] hover:grayscale-0 transition-all duration-300"
                  />
                </div>
                
                <div className="flex-shrink-0 w-32 md:w-40 h-16 md:h-20 flex items-center justify-center transition-transform duration-300 hover:scale-110">
                  <div className="bg-white dark:bg-gray-100 rounded-xl p-3 shadow-md">
                    <img
                      src="https://ksa.go.ke/assets/images/ksa-logo-new.png-web2-207x165.png"
                      alt="Kenya Space Agency"
                      className="max-w-full max-h-full object-contain"
                    />
                  </div>
                </div>
                
                <div className="flex-shrink-0 w-32 md:w-40 h-16 md:h-20 flex items-center justify-center transition-transform duration-300 hover:scale-110">
                  <img
                    src="https://mespt.org/wp-content/uploads/2019/07/MESPT_Logo-jpg.png"
                    alt="MESPT"
                    className="max-w-full max-h-full object-contain filter grayscale-[30%] hover:grayscale-0 transition-all duration-300"
                  />
                </div>
                
                <div className="flex-shrink-0 w-32 md:w-40 h-16 md:h-20 flex items-center justify-center transition-transform duration-300 hover:scale-110">
                  <img
                    src="https://res.cloudinary.com/startup-grind/image/upload/c_fill,dpr_2.0,f_auto,g_center,q_auto:good/v1/gcs/platform-data-africastalking/events/484x304.png"
                    alt="Africa's Talking"
                    className="max-w-full max-h-full object-contain filter grayscale-[30%] hover:grayscale-0 transition-all duration-300"
                  />
                </div>
                
                <div className="flex-shrink-0 w-32 md:w-40 h-16 md:h-20 flex items-center justify-center transition-transform duration-300 hover:scale-110">
                  <img
                    src="https://enablinginnovation.africa/wp-content/uploads/2022/07/riis-logo-transparent.png"
                    alt="RIIS"
                    className="max-w-full max-h-full object-contain filter grayscale-[30%] hover:grayscale-0 transition-all duration-300"
                  />
                </div>
                
                <div className="flex-shrink-0 w-32 md:w-40 h-16 md:h-20 flex items-center justify-center transition-transform duration-300 hover:scale-110">
                  <img
                    src="https://uonbi.ac.ke/sites/default/files/UoN_Logo.png"
                    alt="University of Nairobi"
                    className="max-w-full max-h-full object-contain filter grayscale-[30%] hover:grayscale-0 transition-all duration-300"
                  />
                </div>
              
              {/* Duplicate Set 1 - For seamless infinite scroll */}
                <div className="flex-shrink-0 w-32 md:w-40 h-16 md:h-20 flex items-center justify-center transition-transform duration-300 hover:scale-110">
                  <img
                    src="https://www.nasa.gov/wp-content/themes/nasa/assets/images/nasa-logo.svg"
                    alt="NASA"
                    className="max-w-full max-h-full object-contain filter grayscale-[30%] hover:grayscale-0 transition-all duration-300"
                  />
                </div>
                
                <div className="flex-shrink-0 w-32 md:w-40 h-16 md:h-20 flex items-center justify-center transition-transform duration-300 hover:scale-110">
                  <img
                    src="https://learn.digitalearthafrica.org/static/NewThemeUpdated/images/logo.79a4f6b72027.png"
                    alt="Digital Earth Africa"
                    className="max-w-full max-h-full object-contain filter grayscale-[30%] hover:grayscale-0 transition-all duration-300"
                  />
                </div>
                
                <div className="flex-shrink-0 w-32 md:w-40 h-16 md:h-20 flex items-center justify-center transition-transform duration-300 hover:scale-110">
                  <img
                    src="https://earthengine.google.com/static/images/earth_engine_logo.png"
                    alt="Google Earth Engine"
                    className="max-w-full max-h-full object-contain filter grayscale-[30%] hover:grayscale-0 transition-all duration-300"
                  />
                </div>
                
                <div className="flex-shrink-0 w-32 md:w-40 h-16 md:h-20 flex items-center justify-center transition-transform duration-300 hover:scale-110">
                  <img
                    src="https://www.esri.com/content/dam/esrisites/en-us/common/icons/product-logos/ArcGIS-Enterprise.png"
                    alt="ESRI"
                    className="max-w-full max-h-full object-contain filter grayscale-[30%] hover:grayscale-0 transition-all duration-300"
                  />
                </div>
                
                <div className="flex-shrink-0 w-32 md:w-40 h-16 md:h-20 flex items-center justify-center transition-transform duration-300 hover:scale-110">
                  <img
                    src="https://www.star-idaz.net/wp-content/uploads/2024/07/kalro-logo.webp"
                    alt="KALRO"
                    className="max-w-full max-h-full object-contain filter grayscale-[30%] hover:grayscale-0 transition-all duration-300"
                  />
                </div>
                
                <div className="flex-shrink-0 w-32 md:w-40 h-16 md:h-20 flex items-center justify-center transition-transform duration-300 hover:scale-110">
                  <div className="bg-white dark:bg-gray-100 rounded-xl p-3 shadow-md">
                    <img
                      src="https://ksa.go.ke/assets/images/ksa-logo-new.png-web2-207x165.png"
                      alt="Kenya Space Agency"
                      className="max-w-full max-h-full object-contain"
                    />
                  </div>
                </div>
                
                <div className="flex-shrink-0 w-32 md:w-40 h-16 md:h-20 flex items-center justify-center transition-transform duration-300 hover:scale-110">
                  <img
                    src="https://mespt.org/wp-content/uploads/2019/07/MESPT_Logo-jpg.png"
                    alt="MESPT"
                    className="max-w-full max-h-full object-contain filter grayscale-[30%] hover:grayscale-0 transition-all duration-300"
                  />
                </div>
                
                <div className="flex-shrink-0 w-32 md:w-40 h-16 md:h-20 flex items-center justify-center transition-transform duration-300 hover:scale-110">
                  <img
                    src="https://res.cloudinary.com/startup-grind/image/upload/c_fill,dpr_2.0,f_auto,g_center,q_auto:good/v1/gcs/platform-data-africastalking/events/484x304.png"
                    alt="Africa's Talking"
                    className="max-w-full max-h-full object-contain filter grayscale-[30%] hover:grayscale-0 transition-all duration-300"
                  />
                </div>
                
                <div className="flex-shrink-0 w-32 md:w-40 h-16 md:h-20 flex items-center justify-center transition-transform duration-300 hover:scale-110">
                  <img
                    src="https://enablinginnovation.africa/wp-content/uploads/2022/07/riis-logo-transparent.png"
                    alt="RIIS"
                    className="max-w-full max-h-full object-contain filter grayscale-[30%] hover:grayscale-0 transition-all duration-300"
                  />
                </div>
                
                <div className="flex-shrink-0 w-32 md:w-40 h-16 md:h-20 flex items-center justify-center transition-transform duration-300 hover:scale-110">
                  <img
                    src="https://uonbi.ac.ke/sites/default/files/UoN_Logo.png"
                    alt="University of Nairobi"
                    className="max-w-full max-h-full object-contain filter grayscale-[30%] hover:grayscale-0 transition-all duration-300"
                  />
                </div>
              
              {/* Duplicate Set 2 - For extra smooth infinite scroll */}
                <div className="flex-shrink-0 w-32 md:w-40 h-16 md:h-20 flex items-center justify-center transition-transform duration-300 hover:scale-110">
                  <img
                    src="https://www.nasa.gov/wp-content/themes/nasa/assets/images/nasa-logo.svg"
                    alt="NASA"
                    className="max-w-full max-h-full object-contain filter grayscale-[30%] hover:grayscale-0 transition-all duration-300"
                  />
                </div>
                
                <div className="flex-shrink-0 w-32 md:w-40 h-16 md:h-20 flex items-center justify-center transition-transform duration-300 hover:scale-110">
                  <img
                    src="https://learn.digitalearthafrica.org/static/NewThemeUpdated/images/logo.79a4f6b72027.png"
                    alt="Digital Earth Africa"
                    className="max-w-full max-h-full object-contain filter grayscale-[30%] hover:grayscale-0 transition-all duration-300"
                  />
                </div>
                
                <div className="flex-shrink-0 w-32 md:w-40 h-16 md:h-20 flex items-center justify-center transition-transform duration-300 hover:scale-110">
                  <img
                    src="https://earthengine.google.com/static/images/earth_engine_logo.png"
                    alt="Google Earth Engine"
                    className="max-w-full max-h-full object-contain filter grayscale-[30%] hover:grayscale-0 transition-all duration-300"
                  />
                </div>
                
                <div className="flex-shrink-0 w-32 md:w-40 h-16 md:h-20 flex items-center justify-center transition-transform duration-300 hover:scale-110">
                  <img
                    src="https://www.esri.com/content/dam/esrisites/en-us/common/icons/product-logos/ArcGIS-Enterprise.png"
                    alt="ESRI"
                    className="max-w-full max-h-full object-contain filter grayscale-[30%] hover:grayscale-0 transition-all duration-300"
                  />
                </div>
                
                <div className="flex-shrink-0 w-32 md:w-40 h-16 md:h-20 flex items-center justify-center transition-transform duration-300 hover:scale-110">
                  <img
                    src="https://www.star-idaz.net/wp-content/uploads/2024/07/kalro-logo.webp"
                    alt="KALRO"
                    className="max-w-full max-h-full object-contain filter grayscale-[30%] hover:grayscale-0 transition-all duration-300"
                  />
                </div>
                
                <div className="flex-shrink-0 w-32 md:w-40 h-16 md:h-20 flex items-center justify-center transition-transform duration-300 hover:scale-110">
                  <div className="bg-white dark:bg-gray-100 rounded-xl p-3 shadow-md">
                    <img
                      src="https://ksa.go.ke/assets/images/ksa-logo-new.png-web2-207x165.png"
                      alt="Kenya Space Agency"
                      className="max-w-full max-h-full object-contain"
                    />
                  </div>
                </div>
                
                <div className="flex-shrink-0 w-32 md:w-40 h-16 md:h-20 flex items-center justify-center transition-transform duration-300 hover:scale-110">
                  <img
                    src="https://mespt.org/wp-content/uploads/2019/07/MESPT_Logo-jpg.png"
                    alt="MESPT"
                    className="max-w-full max-h-full object-contain filter grayscale-[30%] hover:grayscale-0 transition-all duration-300"
                  />
                </div>
                
                <div className="flex-shrink-0 w-32 md:w-40 h-16 md:h-20 flex items-center justify-center transition-transform duration-300 hover:scale-110">
                  <img
                    src="https://res.cloudinary.com/startup-grind/image/upload/c_fill,dpr_2.0,f_auto,g_center,q_auto:good/v1/gcs/platform-data-africastalking/events/484x304.png"
                    alt="Africa's Talking"
                    className="max-w-full max-h-full object-contain filter grayscale-[30%] hover:grayscale-0 transition-all duration-300"
                  />
                </div>
                
                <div className="flex-shrink-0 w-32 md:w-40 h-16 md:h-20 flex items-center justify-center transition-transform duration-300 hover:scale-110">
                  <img
                    src="https://enablinginnovation.africa/wp-content/uploads/2022/07/riis-logo-transparent.png"
                    alt="RIIS"
                    className="max-w-full max-h-full object-contain filter grayscale-[30%] hover:grayscale-0 transition-all duration-300"
                  />
                </div>
                
                <div className="flex-shrink-0 w-32 md:w-40 h-16 md:h-20 flex items-center justify-center transition-transform duration-300 hover:scale-110">
                  <img
                    src="https://uonbi.ac.ke/sites/default/files/UoN_Logo.png"
                    alt="University of Nairobi"
                    className="max-w-full max-h-full object-contain filter grayscale-[30%] hover:grayscale-0 transition-all duration-300"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t bg-white dark:bg-gray-950 py-12">
        <div className="container mx-auto px-4">
          <div className="grid md:grid-cols-4 gap-8">
            <div>
              <div className="mb-4 flex flex-col items-start space-y-2">
                <div className="flex items-center">
                  <Image
                    src="/BloomWatch.png"
                    alt="BloomWatch Kenya Logo"
                    width={70}
                    height={70}
                    className="h-auto ml-6"
                  />
                </div>
                <span className="text-xl font-bold bg-gradient-to-r from-green-600 to-green-500 bg-clip-text text-transparent">
                  BloomWatch Kenya
                </span>
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed mb-4">
                Empowering Kenyan farmers with NASA satellite technology for smart crop monitoring and bloom detection
              </p>
              <div className="mt-4 space-y-2">
                <div className="flex items-center text-sm text-gray-600 dark:text-gray-400">
                  <Phone className="h-4 w-4 mr-2 text-green-600" />
                  <span>USSD: *384*42434#</span>
                </div>
                <div className="flex items-center text-sm text-gray-600 dark:text-gray-400">
                  <Mail className="h-4 w-4 mr-2 text-green-600" />
                  <span>hello@bloomwatch.ke</span>
                </div>
              </div>
            </div>
            <div>
              <h4 className="font-semibold mb-4 text-green-700 dark:text-green-400 flex items-center">
                <ChevronRight className="h-4 w-4 mr-1" />
                Platform
              </h4>
              <ul className="space-y-3">
                <li>
                  <Link href="/features" className="text-sm text-gray-600 dark:text-gray-400 hover:text-green-600 dark:hover:text-green-400 transition-colors flex items-center">
                    <Satellite className="h-3 w-3 mr-2" />
                    Features
                  </Link>
                </li>
                <li>
                  <Link href="/how-it-works" className="text-sm text-gray-600 dark:text-gray-400 hover:text-green-600 dark:hover:text-green-400 transition-colors flex items-center">
                    <HelpCircle className="h-3 w-3 mr-2" />
                    How It Works
                  </Link>
                </li>
                <li>
                  <Link href="/register" className="text-sm text-gray-600 dark:text-gray-400 hover:text-green-600 dark:hover:text-green-400 transition-colors flex items-center">
                    <Rocket className="h-3 w-3 mr-2" />
                    Get Started
                  </Link>
                </li>
                <li>
                  <Link href="#" className="text-sm text-gray-600 dark:text-gray-400 hover:text-green-600 dark:hover:text-green-400 transition-colors flex items-center">
                    <Smartphone className="h-3 w-3 mr-2" />
                    Download Android App
                  </Link>
                </li>
                <li>
                  <Link href="#" className="text-sm text-gray-600 dark:text-gray-400 hover:text-green-600 dark:hover:text-green-400 transition-colors flex items-center">
                    <Smartphone className="h-3 w-3 mr-2" />
                    Download iOS App
                  </Link>
                </li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4 text-green-700 dark:text-green-400 flex items-center">
                <ChevronRight className="h-4 w-4 mr-1" />
                Support & Connect
              </h4>
              <ul className="space-y-3">
                <li>
                  <Link href="/help" className="text-sm text-gray-600 dark:text-gray-400 hover:text-green-600 dark:hover:text-green-400 transition-colors flex items-center">
                    <HelpCircle className="h-3 w-3 mr-2" />
                    Help Center
                  </Link>
                </li>
                <li>
                  <Link href="/contact" className="text-sm text-gray-600 dark:text-gray-400 hover:text-green-600 dark:hover:text-green-400 transition-colors flex items-center">
                    <Mail className="h-3 w-3 mr-2" />
                    Contact Us
                  </Link>
                </li>
                <li>
                  <Link href="/faq" className="text-sm text-gray-600 dark:text-gray-400 hover:text-green-600 dark:hover:text-green-400 transition-colors flex items-center">
                    <MessageSquare className="h-3 w-3 mr-2" />
                    FAQ
                  </Link>
                </li>
                <li>
                  <Link href="#" className="text-sm text-gray-600 dark:text-gray-400 hover:text-green-600 dark:hover:text-green-400 transition-colors flex items-center">
                    <Twitter className="h-3 w-3 mr-2" />
                    @BloomWatchKE
                  </Link>
                </li>
                <li>
                  <Link href="#" className="text-sm text-gray-600 dark:text-gray-400 hover:text-green-600 dark:hover:text-green-400 transition-colors flex items-center">
                    <Facebook className="h-3 w-3 mr-2" />
                    /BloomWatchKenya
                  </Link>
                </li>
                <li>
                  <Link href="https://github.com/geoffreyyogo/bloom-detector" target="_blank" className="text-sm text-gray-600 dark:text-gray-400 hover:text-green-600 dark:hover:text-green-400 transition-colors flex items-center">
                    <Github className="h-3 w-3 mr-2" />
                    GitHub Repository
                  </Link>
                </li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4 text-green-700 dark:text-green-400 flex items-center">
                <ChevronRight className="h-4 w-4 mr-1" />
                Partners & Legal
              </h4>
              <div className="space-y-2 mb-4">
                <p className="text-xs text-gray-500 dark:text-gray-500 font-semibold">Powered by:</p>
                <p className="text-xs text-gray-600 dark:text-gray-400">• NASA Space Apps</p>
                <p className="text-xs text-gray-600 dark:text-gray-400">• Digital Earth Africa</p>
                <p className="text-xs text-gray-600 dark:text-gray-400">• Africa's Talking</p>
                <p className="text-xs text-gray-600 dark:text-gray-400">• Google Earth Engine</p>
                <p className="text-xs text-gray-600 dark:text-gray-400">• MongoDB Atlas</p>
              </div>
              <ul className="space-y-3 mt-4">
                <li>
                  <Link href="/privacy" className="text-sm text-gray-600 dark:text-gray-400 hover:text-green-600 dark:hover:text-green-400 transition-colors flex items-center">
                    <Shield className="h-3 w-3 mr-2" />
                    Privacy Policy
                  </Link>
                </li>
                <li>
                  <Link href="/terms" className="text-sm text-gray-600 dark:text-gray-400 hover:text-green-600 dark:hover:text-green-400 transition-colors flex items-center">
                    <FileText className="h-3 w-3 mr-2" />
                    Terms of Service
                  </Link>
                </li>
              </ul>
            </div>
          </div>
          <div className="mt-12 pt-8 border-t">
            <p className="text-center text-sm text-gray-600 dark:text-gray-400 mb-2">
              BloomWatch Kenya - NASA Space Apps Challenge 2025 | Powered by Earth Observation Data
            </p>
            <p className="text-center text-sm text-gray-500 dark:text-gray-500">
              &copy; {new Date().getFullYear()} BloomWatch Kenya. All rights reserved. Made with ❤️ for Kenyan farmers
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}

