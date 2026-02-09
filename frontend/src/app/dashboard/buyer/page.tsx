'use client'

import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import Image from 'next/image'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { Textarea } from '@/components/ui/textarea'
import { ThemeSwitcher } from '@/components/ui/theme-switcher'
import { LanguageSelector } from '@/components/ui/language-selector'
import { useToast } from '@/components/ui/use-toast'
import { useAuthStore, getDashboardRoute } from '@/store/authStore'
import { api } from '@/lib/api'
import {
  ShoppingBag, Search, Bell, LogOut, User, TrendingUp, MapPin, Clock,
  Package, Loader2, Filter, ArrowUpRight, ArrowDownRight, Gavel,
  DollarSign, Eye, ChevronRight, Star, Heart, Tag, Weight,
} from 'lucide-react'
import type { MarketplaceListing, MarketplaceBid } from '@/types'

// ─── Metric Card ──────────────────────────────
function MetricCard({ icon: Icon, label, value, color }: {
  icon: any; label: string; value: string; color: string
}) {
  return (
    <Card className="relative overflow-hidden">
      <CardContent className="p-5">
        <div className="flex items-start justify-between">
          <div className="space-y-2">
            <p className="text-sm font-medium text-gray-500 dark:text-gray-400">{label}</p>
            <p className="text-2xl font-bold">{value}</p>
          </div>
          <div className={`p-3 rounded-xl ${color}`}>
            <Icon className="h-5 w-5 text-white" />
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

// ─── Listing Card ─────────────────────────────
function ListingCard({ listing, onBid }: {
  listing: MarketplaceListing
  onBid: (listing: MarketplaceListing) => void
}) {
  const daysAgo = listing.created_at
    ? Math.floor((Date.now() - new Date(listing.created_at).getTime()) / 86400000)
    : 0

  return (
    <Card className="hover:shadow-lg transition-all group cursor-pointer border-l-4 border-l-transparent hover:border-l-blue-500">
      <CardContent className="p-4">
        <div className="flex items-start justify-between mb-2">
          <div>
            <h3 className="font-semibold text-base group-hover:text-blue-600 transition-colors">{listing.produce_name}</h3>
            <div className="flex items-center gap-2 mt-1">
              <Badge variant="secondary" className="text-xs">{listing.category || 'Produce'}</Badge>
              <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                listing.status === 'active'
                  ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300'
                  : listing.status === 'sold'
                  ? 'bg-blue-100 text-blue-700'
                  : 'bg-gray-100 text-gray-500'
              }`}>
                {listing.status}
              </span>
            </div>
          </div>
          <div className="text-right">
            <p className="text-xl font-bold text-blue-600">KES {listing.price_per_unit_kes?.toLocaleString()}</p>
            <p className="text-xs text-gray-500">per {listing.unit || 'kg'}</p>
          </div>
        </div>

        <p className="text-sm text-gray-500 line-clamp-2 mb-3">{listing.description || 'Fresh produce from local farms'}</p>

        <div className="grid grid-cols-3 gap-2 text-xs text-gray-500 mb-3">
          <div className="flex items-center gap-1">
            <Weight className="h-3 w-3" />
            {listing.quantity_available} {listing.unit || 'kg'}
          </div>
          <div className="flex items-center gap-1">
            <MapPin className="h-3 w-3" />
            {listing.county || 'Kenya'}
          </div>
          <div className="flex items-center gap-1">
            <Clock className="h-3 w-3" />
            {daysAgo === 0 ? 'Today' : `${daysAgo}d ago`}
          </div>
        </div>

        <div className="flex gap-2">
          <Button
            size="sm"
            className="flex-1 bg-blue-600 hover:bg-blue-700"
            onClick={() => onBid(listing)}
          >
            <Gavel className="h-3.5 w-3.5 mr-1" /> Place Bid
          </Button>
          <Button size="sm" variant="outline" className="flex-1">
            <Eye className="h-3.5 w-3.5 mr-1" /> Details
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

// ─── Bid Dialog ───────────────────────────────
function BidForm({ listing, onClose, onSubmitted }: {
  listing: MarketplaceListing; onClose: () => void; onSubmitted: () => void
}) {
  const { farmer } = useAuthStore()
  const { toast } = useToast()
  const [quantity, setQuantity] = useState('')
  const [price, setPrice] = useState(String(listing.price_per_unit_kes || ''))
  const [message, setMessage] = useState('')
  const [paymentMethod, setPaymentMethod] = useState('mpesa')
  const [submitting, setSubmitting] = useState(false)

  const totalPrice = (parseFloat(quantity) || 0) * (parseFloat(price) || 0)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!farmer?.id || !quantity || !price) return
    setSubmitting(true)
    try {
      await api.createMarketplaceBid({
        listing_id: listing.id,
        buyer_id: farmer.id,
        quantity: parseFloat(quantity),
        price_per_unit_kes: parseFloat(price),
        message: message || undefined,
        payment_method: paymentMethod,
      })
      toast({ title: 'Bid Placed!', description: `Your bid for ${quantity} ${listing.unit || 'kg'} of ${listing.produce_name} has been submitted.` })
      onSubmitted()
      onClose()
    } catch (err: any) {
      toast({ title: 'Error', description: err.message, variant: 'destructive' })
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Card className="border-2 border-blue-200 dark:border-blue-800 bg-blue-50/30 dark:bg-blue-950/20">
      <CardHeader className="pb-3">
        <CardTitle className="text-lg flex items-center gap-2">
          <Gavel className="h-5 w-5 text-blue-600" /> Bid on {listing.produce_name}
        </CardTitle>
        <CardDescription>
          Available: {listing.quantity_available} {listing.unit || 'kg'} &middot; Ask price: KES {listing.price_per_unit_kes?.toLocaleString()}/{listing.unit || 'kg'}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label>Quantity ({listing.unit || 'kg'}) *</Label>
              <Input type="number" value={quantity} onChange={e => setQuantity(e.target.value)} placeholder="50" className="mt-1" required />
            </div>
            <div>
              <Label>Your Price (KES/{listing.unit || 'kg'}) *</Label>
              <Input type="number" value={price} onChange={e => setPrice(e.target.value)} placeholder="120" className="mt-1" required />
            </div>
          </div>
          {totalPrice > 0 && (
            <div className="bg-blue-50 dark:bg-blue-950/50 border border-blue-200 dark:border-blue-800 rounded-lg p-3 text-center">
              <p className="text-sm text-gray-500">Estimated Total</p>
              <p className="text-2xl font-bold text-blue-600">KES {totalPrice.toLocaleString()}</p>
            </div>
          )}
          <div>
            <Label>Payment Method</Label>
            <Select value={paymentMethod} onValueChange={setPaymentMethod}>
              <SelectTrigger className="mt-1"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="mpesa">M-Pesa</SelectItem>
                <SelectItem value="airtel_money">Airtel Money</SelectItem>
                <SelectItem value="bank_transfer">Bank Transfer</SelectItem>
                <SelectItem value="cash">Cash on Delivery</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label>Message to Farmer (optional)</Label>
            <Textarea value={message} onChange={e => setMessage(e.target.value)} placeholder="I need weekly supply..." rows={2} className="mt-1" />
          </div>
          <div className="flex gap-2 pt-2">
            <Button type="button" variant="outline" onClick={onClose} className="flex-1">Cancel</Button>
            <Button type="submit" className="flex-1 bg-blue-600 hover:bg-blue-700" disabled={submitting}>
              {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Submit Bid'}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  )
}

// ═══════════════════════════════════════════════
// MAIN BUYER DASHBOARD
// ═══════════════════════════════════════════════
export default function BuyerDashboardPage() {
  const router = useRouter()
  const { farmer, isAuthenticated, logout } = useAuthStore()

  const [listings, setListings] = useState<MarketplaceListing[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [filterCategory, setFilterCategory] = useState('')
  const [filterCounty, setFilterCounty] = useState('')
  const [biddingListing, setBiddingListing] = useState<MarketplaceListing | null>(null)

  // Auth guard
  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login')
      return
    }
    if (farmer?.user_type !== 'buyer') {
      router.push(getDashboardRoute(farmer?.user_type))
    }
  }, [isAuthenticated, farmer, router])

  const fetchListings = useCallback(async () => {
    setLoading(true)
    try {
      const params: any = { status: 'active' }
      if (filterCategory) params.category = filterCategory
      if (filterCounty) params.county = filterCounty
      const res = await api.getMarketplaceListings(params)
      setListings(res.listings || [])
    } catch {
      // graceful
    } finally {
      setLoading(false)
    }
  }, [filterCategory, filterCounty])

  useEffect(() => { fetchListings() }, [fetchListings])

  // Filter by search
  const filteredListings = listings.filter(l =>
    !searchQuery || l.produce_name.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const categories = [...new Set(listings.map(l => l.category).filter(Boolean))]
  const counties = [...new Set(listings.map(l => l.county).filter(Boolean))]
  const totalListings = listings.length
  const avgPrice = listings.length > 0
    ? Math.round(listings.reduce((s, l) => s + (l.price_per_unit_kes || 0), 0) / listings.length)
    : 0

  if (!farmer || farmer.user_type !== 'buyer') return null

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      {/* Top Nav */}
      <header className="bg-white dark:bg-gray-900 border-b shadow-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Link href="/">
                <Image src="/BloomWatch.png" alt="Smart Shamba" width={36} height={36} className="h-9 w-auto" />
              </Link>
              <div>
                <h1 className="text-lg font-bold text-blue-700 dark:text-blue-400">Buyer Dashboard</h1>
                <p className="text-xs text-gray-500">{farmer.display_id} &middot; {farmer.name}</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <ThemeSwitcher />
              <LanguageSelector />
              <Button variant="ghost" size="sm" onClick={async () => { await logout(); router.push('/login') }}>
                <LogOut className="h-4 w-4 mr-1" /> Logout
              </Button>
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-6 space-y-6">
        {/* Metrics */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard icon={Package} label="Available Listings" value={String(totalListings)} color="bg-blue-600" />
          <MetricCard icon={DollarSign} label="Avg. Price (KES/kg)" value={String(avgPrice)} color="bg-green-600" />
          <MetricCard icon={MapPin} label="Source Counties" value={String(counties.length)} color="bg-purple-600" />
          <MetricCard icon={Tag} label="Categories" value={String(categories.length)} color="bg-amber-600" />
        </div>

        {/* Tabs */}
        <Tabs defaultValue="marketplace" className="space-y-4">
          <TabsList className="bg-white dark:bg-gray-900 border p-1 rounded-xl">
            <TabsTrigger value="marketplace" className="rounded-lg data-[state=active]:bg-blue-100 dark:data-[state=active]:bg-blue-900/30 data-[state=active]:text-blue-700">
              <ShoppingBag className="h-4 w-4 mr-2" /> Marketplace
            </TabsTrigger>
            <TabsTrigger value="mybids" className="rounded-lg data-[state=active]:bg-blue-100 dark:data-[state=active]:bg-blue-900/30 data-[state=active]:text-blue-700">
              <Gavel className="h-4 w-4 mr-2" /> My Bids
            </TabsTrigger>
            <TabsTrigger value="profile" className="rounded-lg data-[state=active]:bg-blue-100 dark:data-[state=active]:bg-blue-900/30 data-[state=active]:text-blue-700">
              <User className="h-4 w-4 mr-2" /> Profile
            </TabsTrigger>
          </TabsList>

          {/* ─── Marketplace Tab ─── */}
          <TabsContent value="marketplace" className="space-y-4">
            {/* Filters */}
            <div className="flex flex-col sm:flex-row gap-3">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input value={searchQuery} onChange={e => setSearchQuery(e.target.value)} placeholder="Search produce..." className="pl-10" />
              </div>
              <Select value={filterCategory || 'all'} onValueChange={v => setFilterCategory(v === 'all' ? '' : v)}>
                <SelectTrigger className="w-40"><Filter className="h-4 w-4 mr-2" /><SelectValue placeholder="Category" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Categories</SelectItem>
                  {categories.map(c => <SelectItem key={c!} value={c!}>{c}</SelectItem>)}
                </SelectContent>
              </Select>
              <Select value={filterCounty || 'all'} onValueChange={v => setFilterCounty(v === 'all' ? '' : v)}>
                <SelectTrigger className="w-40"><MapPin className="h-4 w-4 mr-2" /><SelectValue placeholder="County" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Counties</SelectItem>
                  {counties.map(c => <SelectItem key={c!} value={c!}>{c}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>

            {/* Bid form if active */}
            {biddingListing && (
              <BidForm
                listing={biddingListing}
                onClose={() => setBiddingListing(null)}
                onSubmitted={fetchListings}
              />
            )}

            {/* Listings Grid */}
            {loading ? (
              <div className="flex items-center justify-center py-16">
                <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
              </div>
            ) : filteredListings.length === 0 ? (
              <Card className="p-12 text-center">
                <ShoppingBag className="h-12 w-12 text-gray-300 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-gray-600 dark:text-gray-400">No Listings Found</h3>
                <p className="text-sm text-gray-500 mt-2">Check back later for fresh produce from farmers.</p>
              </Card>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {filteredListings.map(listing => (
                  <ListingCard key={listing.id} listing={listing} onBid={setBiddingListing} />
                ))}
              </div>
            )}
          </TabsContent>

          {/* ─── My Bids Tab ─── */}
          <TabsContent value="mybids" className="space-y-4">
            <Card className="p-12 text-center">
              <Gavel className="h-12 w-12 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-600 dark:text-gray-400">Your Bids</h3>
              <p className="text-sm text-gray-500 mt-2">
                Place bids on marketplace listings to see them here.
              </p>
            </Card>
          </TabsContent>

          {/* ─── Profile Tab ─── */}
          <TabsContent value="profile" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2"><User className="h-5 w-5" /> Buyer Profile</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-3">
                    <div>
                      <Label className="text-gray-500 text-xs">Display ID</Label>
                      <p className="font-mono font-semibold text-blue-600">{farmer.display_id}</p>
                    </div>
                    <div>
                      <Label className="text-gray-500 text-xs">Name</Label>
                      <p className="font-medium">{farmer.name}</p>
                    </div>
                    <div>
                      <Label className="text-gray-500 text-xs">Phone</Label>
                      <p>{farmer.phone}</p>
                    </div>
                    <div>
                      <Label className="text-gray-500 text-xs">Email</Label>
                      <p>{farmer.email || 'Not set'}</p>
                    </div>
                  </div>
                  <div className="space-y-3">
                    <div>
                      <Label className="text-gray-500 text-xs">County</Label>
                      <p>{farmer.county || 'Not set'}</p>
                    </div>
                    <div>
                      <Label className="text-gray-500 text-xs">Sub-County</Label>
                      <p>{farmer.sub_county || 'Not set'}</p>
                    </div>
                    <div>
                      <Label className="text-gray-500 text-xs">Account Type</Label>
                      <Badge className="bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-200">Buyer</Badge>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  )
}
