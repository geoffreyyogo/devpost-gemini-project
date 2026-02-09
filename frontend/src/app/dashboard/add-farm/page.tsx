'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { ArrowLeft, Loader2, MapPin, Sprout, Plus, X } from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import { api } from '@/lib/api'

const KENYA_COUNTIES = [
  'Baringo', 'Bomet', 'Bungoma', 'Busia', 'Elgeyo-Marakwet',
  'Embu', 'Garissa', 'Homa Bay', 'Isiolo', 'Kajiado',
  'Kakamega', 'Kericho', 'Kiambu', 'Kilifi', 'Kirinyaga',
  'Kisii', 'Kisumu', 'Kitui', 'Kwale', 'Laikipia',
  'Lamu', 'Machakos', 'Makueni', 'Mandera', 'Marsabit',
  'Meru', 'Migori', 'Mombasa', 'Muranga', 'Nairobi',
  'Nakuru', 'Nandi', 'Narok', 'Nyamira', 'Nyandarua',
  'Nyeri', 'Samburu', 'Siaya', 'Taita-Taveta', 'Tana River',
  'Tharaka-Nithi', 'Trans-Nzoia', 'Turkana', 'Uasin Gishu',
  'Vihiga', 'Wajir', 'West Pokot',
]

const SOIL_TYPES = ['Loam', 'Clay', 'Sandy', 'Silt', 'Clay Loam', 'Sandy Loam', 'Laterite', 'Black Cotton']
const IRRIGATION_TYPES = ['Rainfed', 'Drip', 'Sprinkler', 'Furrow', 'Flood', 'Center Pivot']
const COMMON_CROPS = ['Maize', 'Beans', 'Wheat', 'Rice', 'Tea', 'Coffee', 'Sugarcane', 'Tomatoes', 'Potatoes', 'Sorghum', 'Millet', 'Cassava', 'Sweet Potatoes', 'Bananas', 'Avocados', 'Mangoes']

export default function AddFarmPage() {
  const router = useRouter()
  const { farmer, hasHydrated, isAuthenticated } = useAuthStore()
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Form state
  const [name, setName] = useState('')
  const [county, setCounty] = useState('')
  const [subCounty, setSubCounty] = useState('')
  const [latitude, setLatitude] = useState('')
  const [longitude, setLongitude] = useState('')
  const [sizeAcres, setSizeAcres] = useState('')
  const [soilType, setSoilType] = useState('')
  const [irrigationType, setIrrigation] = useState('')
  const [crops, setCrops] = useState<string[]>([])
  const [cropInput, setCropInput] = useState('')

  const addCrop = (crop: string) => {
    const clean = crop.trim().toLowerCase()
    if (clean && !crops.includes(clean)) {
      setCrops(prev => [...prev, clean])
    }
    setCropInput('')
  }

  const removeCrop = (crop: string) => {
    setCrops(prev => prev.filter(c => c !== crop))
  }

  const handleGetLocation = () => {
    if (!navigator.geolocation) return
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLatitude(pos.coords.latitude.toFixed(6))
        setLongitude(pos.coords.longitude.toFixed(6))
      },
      () => setError('Could not get your location. Please enter coordinates manually.')
    )
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    const lat = parseFloat(latitude)
    const lon = parseFloat(longitude)
    if (isNaN(lat) || isNaN(lon)) {
      setError('Please provide valid latitude and longitude coordinates.')
      return
    }

    setSubmitting(true)
    try {
      await api.createFarm({
        name: name || undefined,
        latitude: lat,
        longitude: lon,
        county: county || undefined,
        sub_county: subCounty || undefined,
        size_acres: sizeAcres ? parseFloat(sizeAcres) : undefined,
        crops: crops.length > 0 ? crops : undefined,
        soil_type: soilType || undefined,
        irrigation_type: irrigationType || undefined,
      })
      router.push('/dashboard?tab=farms')
    } catch (err: any) {
      setError(err?.message || 'Failed to register farm. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  if (!hasHydrated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-green-50 to-white dark:from-gray-950 dark:to-gray-900">
        <Loader2 className="h-12 w-12 animate-spin text-green-600" />
      </div>
    )
  }

  if (!isAuthenticated || !farmer) {
    router.push('/login')
    return null
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-white to-green-50 dark:from-gray-950 dark:via-gray-900 dark:to-gray-950">
      <div className="container mx-auto max-w-2xl px-4 py-8">
        {/* Header */}
        <div className="flex items-center gap-4 mb-8">
          <Link href="/dashboard">
            <Button variant="ghost" size="sm" className="rounded-xl">
              <ArrowLeft className="h-4 w-4 mr-2" /> Back
            </Button>
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-green-700 dark:text-green-400 flex items-center gap-2">
              <Sprout className="h-6 w-6" /> Register a New Farm
            </h1>
            <p className="text-sm text-gray-500">Add your farm for satellite monitoring and AI predictions</p>
          </div>
        </div>

        <form onSubmit={handleSubmit}>
          <Card className="shadow-lg border-green-200 dark:border-green-800">
            <CardHeader>
              <CardTitle>Farm Details</CardTitle>
              <CardDescription>Fill in your farm information. Location coordinates are required.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Farm Name */}
              <div>
                <label className="block text-sm font-medium mb-1.5">Farm Name</label>
                <Input
                  placeholder="e.g. Shamba ya Nyumbani"
                  value={name}
                  onChange={e => setName(e.target.value)}
                />
              </div>

              {/* Location */}
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="text-sm font-medium">Location *</label>
                  <Button type="button" variant="outline" size="sm" onClick={handleGetLocation} className="text-xs h-7">
                    <MapPin className="h-3 w-3 mr-1" /> Use My Location
                  </Button>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <Input
                      type="number"
                      step="any"
                      placeholder="Latitude (e.g. -0.0917)"
                      value={latitude}
                      onChange={e => setLatitude(e.target.value)}
                      required
                    />
                  </div>
                  <div>
                    <Input
                      type="number"
                      step="any"
                      placeholder="Longitude (e.g. 34.7680)"
                      value={longitude}
                      onChange={e => setLongitude(e.target.value)}
                      required
                    />
                  </div>
                </div>
              </div>

              {/* County & Sub-County */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium mb-1.5">County</label>
                  <Select value={county} onValueChange={setCounty}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select county" />
                    </SelectTrigger>
                    <SelectContent>
                      {KENYA_COUNTIES.map(c => (
                        <SelectItem key={c} value={c}>{c}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1.5">Sub-County</label>
                  <Input
                    placeholder="e.g. Kisumu Central"
                    value={subCounty}
                    onChange={e => setSubCounty(e.target.value)}
                  />
                </div>
              </div>

              {/* Size */}
              <div>
                <label className="block text-sm font-medium mb-1.5">Farm Size (acres)</label>
                <Input
                  type="number"
                  step="0.1"
                  min="0"
                  placeholder="e.g. 2.5"
                  value={sizeAcres}
                  onChange={e => setSizeAcres(e.target.value)}
                />
              </div>

              {/* Crops */}
              <div>
                <label className="block text-sm font-medium mb-1.5">Crops</label>
                <div className="flex flex-wrap gap-1.5 mb-2">
                  {crops.map(crop => (
                    <Badge key={crop} variant="secondary" className="px-2 py-1 text-xs gap-1">
                      {crop.charAt(0).toUpperCase() + crop.slice(1)}
                      <button type="button" onClick={() => removeCrop(crop)}>
                        <X className="h-3 w-3" />
                      </button>
                    </Badge>
                  ))}
                </div>
                <div className="flex gap-2">
                  <Input
                    placeholder="Type a crop name..."
                    value={cropInput}
                    onChange={e => setCropInput(e.target.value)}
                    onKeyDown={e => {
                      if (e.key === 'Enter') {
                        e.preventDefault()
                        addCrop(cropInput)
                      }
                    }}
                  />
                  <Button type="button" variant="outline" size="sm" onClick={() => addCrop(cropInput)} disabled={!cropInput.trim()}>
                    <Plus className="h-4 w-4" />
                  </Button>
                </div>
                <div className="flex flex-wrap gap-1 mt-2">
                  {COMMON_CROPS.filter(c => !crops.includes(c.toLowerCase())).slice(0, 8).map(c => (
                    <button
                      key={c}
                      type="button"
                      onClick={() => addCrop(c)}
                      className="text-xs px-2 py-0.5 rounded-full border border-green-200 dark:border-green-800 text-green-700 dark:text-green-400 hover:bg-green-50 dark:hover:bg-green-950 transition-colors"
                    >
                      + {c}
                    </button>
                  ))}
                </div>
              </div>

              {/* Soil Type & Irrigation */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium mb-1.5">Soil Type</label>
                  <Select value={soilType} onValueChange={setSoilType}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select soil type" />
                    </SelectTrigger>
                    <SelectContent>
                      {SOIL_TYPES.map(s => (
                        <SelectItem key={s} value={s}>{s}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1.5">Irrigation</label>
                  <Select value={irrigationType} onValueChange={setIrrigation}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select type" />
                    </SelectTrigger>
                    <SelectContent>
                      {IRRIGATION_TYPES.map(i => (
                        <SelectItem key={i} value={i}>{i}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {/* Error */}
              {error && (
                <div className="p-3 rounded-lg bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 text-sm text-red-700 dark:text-red-400">
                  {error}
                </div>
              )}

              {/* Submit */}
              <div className="flex gap-3 pt-2">
                <Link href="/dashboard" className="flex-1">
                  <Button type="button" variant="outline" className="w-full">Cancel</Button>
                </Link>
                <Button
                  type="submit"
                  disabled={submitting || !latitude || !longitude}
                  className="flex-1 bg-green-600 hover:bg-green-700"
                >
                  {submitting ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" /> Registering...
                    </>
                  ) : (
                    <>
                      <Sprout className="h-4 w-4 mr-2" /> Register Farm
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        </form>
      </div>
    </div>
  )
}
