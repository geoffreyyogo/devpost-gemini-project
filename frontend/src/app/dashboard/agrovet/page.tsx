'use client'

import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import Image from 'next/image'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { ThemeSwitcher } from '@/components/ui/theme-switcher'
import { LanguageSelector } from '@/components/ui/language-selector'
import { useToast } from '@/components/ui/use-toast'
import { useAuthStore, getDashboardRoute } from '@/store/authStore'
import { api } from '@/lib/api'
import {
  Store, Package, ShoppingCart, TrendingUp, Plus, Search, Bell, LogOut, User,
  DollarSign, BarChart3, Eye, Edit, Trash2, Check, X, Clock, Loader2,
  ChevronRight, Star, AlertTriangle, ArrowUpRight, ArrowDownRight, Filter,
} from 'lucide-react'
import type { AgrovetProduct, AgrovetOrder } from '@/types'

// ─── Metric Card ──────────────────────────────
function MetricCard({ icon: Icon, label, value, change, changeType, color }: {
  icon: any; label: string; value: string; change?: string; changeType?: 'up' | 'down'; color: string
}) {
  return (
    <Card className="relative overflow-hidden">
      <CardContent className="p-5">
        <div className="flex items-start justify-between">
          <div className="space-y-2">
            <p className="text-sm font-medium text-gray-500 dark:text-gray-400">{label}</p>
            <p className="text-2xl font-bold">{value}</p>
            {change && (
              <div className={`flex items-center text-xs font-medium ${changeType === 'up' ? 'text-green-600' : 'text-red-500'}`}>
                {changeType === 'up' ? <ArrowUpRight className="h-3 w-3 mr-1" /> : <ArrowDownRight className="h-3 w-3 mr-1" />}
                {change} from last month
              </div>
            )}
          </div>
          <div className={`p-3 rounded-xl ${color}`}>
            <Icon className="h-5 w-5 text-white" />
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

// ─── Status Badge ─────────────────────────────
function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    pending: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
    confirmed: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
    shipped: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
    delivered: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
    cancelled: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
  }
  return (
    <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${styles[status] || styles.pending}`}>
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  )
}

// ─── Add Product Dialog (inline) ──────────────
function AddProductForm({ onClose, onAdded }: { onClose: () => void; onAdded: () => void }) {
  const [name, setName] = useState('')
  const [category, setCategory] = useState('')
  const [price, setPrice] = useState('')
  const [stock, setStock] = useState('')
  const [unit, setUnit] = useState('kg')
  const [description, setDescription] = useState('')
  const [crop, setCrop] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const { toast } = useToast()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!name || !category || !price) return
    setSubmitting(true)
    try {
      await api.createAgrovetProduct({
        name,
        category,
        price_kes: parseFloat(price),
        stock_quantity: stock ? parseInt(stock) : undefined,
        unit,
        description: description || undefined,
        target_crop: crop || undefined,
      })
      toast({ title: 'Product Added!', description: `${name} has been listed.` })
      onAdded()
      onClose()
    } catch (err: any) {
      toast({ title: 'Error', description: err.message, variant: 'destructive' })
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Card className="border-2 border-amber-200 dark:border-amber-800 bg-amber-50/30 dark:bg-amber-950/20">
      <CardHeader className="pb-3">
        <CardTitle className="text-lg flex items-center gap-2">
          <Plus className="h-5 w-5 text-amber-600" /> Add New Product
        </CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label>Product Name *</Label>
              <Input value={name} onChange={e => setName(e.target.value)} placeholder="DAP Fertilizer" className="mt-1" required />
            </div>
            <div>
              <Label>Category *</Label>
              <Select value={category} onValueChange={setCategory}>
                <SelectTrigger className="mt-1"><SelectValue placeholder="Category" /></SelectTrigger>
                <SelectContent>
                  {['Seeds', 'Fertilizers', 'Pesticides', 'Herbicides', 'Farm Tools', 'Animal Feed', 'Veterinary', 'Irrigation', 'Organic'].map(c => (
                    <SelectItem key={c} value={c}>{c}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <div className="grid grid-cols-3 gap-3">
            <div>
              <Label>Price (KES) *</Label>
              <Input type="number" value={price} onChange={e => setPrice(e.target.value)} placeholder="3500" className="mt-1" required />
            </div>
            <div>
              <Label>Stock Qty</Label>
              <Input type="number" value={stock} onChange={e => setStock(e.target.value)} placeholder="100" className="mt-1" />
            </div>
            <div>
              <Label>Unit</Label>
              <Select value={unit} onValueChange={setUnit}>
                <SelectTrigger className="mt-1"><SelectValue /></SelectTrigger>
                <SelectContent>
                  {['kg', 'litre', 'piece', 'bag', 'bottle', 'packet', 'roll'].map(u => (
                    <SelectItem key={u} value={u}>{u}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <div>
            <Label>Target Crop</Label>
            <Input value={crop} onChange={e => setCrop(e.target.value)} placeholder="Maize, Wheat..." className="mt-1" />
          </div>
          <div>
            <Label>Description</Label>
            <Textarea value={description} onChange={e => setDescription(e.target.value)} placeholder="Product details..." rows={2} className="mt-1" />
          </div>
          <div className="flex gap-2 pt-2">
            <Button type="button" variant="outline" onClick={onClose} className="flex-1">Cancel</Button>
            <Button type="submit" className="flex-1 bg-amber-600 hover:bg-amber-700" disabled={submitting}>
              {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Add Product'}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  )
}

// ═══════════════════════════════════════════════
// MAIN DASHBOARD
// ═══════════════════════════════════════════════
export default function AgrovetDashboardPage() {
  const router = useRouter()
  const { farmer, isAuthenticated, logout } = useAuthStore()
  const { toast } = useToast()

  const [products, setProducts] = useState<AgrovetProduct[]>([])
  const [orders, setOrders] = useState<AgrovetOrder[]>([])
  const [loading, setLoading] = useState(true)
  const [showAddProduct, setShowAddProduct] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [filterCategory, setFilterCategory] = useState('')
  const [orderFilter, setOrderFilter] = useState('')
  const [updatingOrder, setUpdatingOrder] = useState<number | null>(null)

  // Auth guard
  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login')
      return
    }
    if (farmer?.user_type !== 'agrovet') {
      router.push(getDashboardRoute(farmer?.user_type))
    }
  }, [isAuthenticated, farmer, router])

  // Fetch data
  const fetchData = useCallback(async () => {
    setLoading(true)
    try {
      const [productsRes, ordersRes] = await Promise.all([
        api.getAgrovetProducts(),
        api.getShopOrders().catch(() =>
          farmer?.id ? api.getFarmerOrders(farmer.id) : Promise.resolve({ orders: [] })
        ),
      ])
      setProducts(productsRes.products || [])
      setOrders(ordersRes.orders || [])
    } catch {
      // graceful fallback
    } finally {
      setLoading(false)
    }
  }, [farmer?.id])

  useEffect(() => { fetchData() }, [fetchData])

  // ── Order status update ──
  const handleUpdateOrderStatus = async (orderId: number, deliveryStatus: string) => {
    setUpdatingOrder(orderId)
    try {
      await api.updateOrderStatus(orderId, { delivery_status: deliveryStatus })
      toast({ title: 'Order Updated', description: `Order status changed to ${deliveryStatus}` })
      fetchData()
    } catch (err: any) {
      toast({ title: 'Error', description: err.message, variant: 'destructive' })
    } finally {
      setUpdatingOrder(null)
    }
  }

  // ── Product delete ──
  const handleDeleteProduct = async (productId: number) => {
    try {
      await api.deleteAgrovetProduct(productId)
      toast({ title: 'Product Removed', description: 'Product has been deactivated.' })
      fetchData()
    } catch (err: any) {
      toast({ title: 'Error', description: err.message, variant: 'destructive' })
    }
  }

  // Computed metrics
  const totalRevenue = orders
    .filter(o => o.status === 'delivered')
    .reduce((sum, o) => sum + (o.total_price || 0), 0)
  const pendingOrders = orders.filter(o => o.status === 'pending').length
  const activeProducts = products.filter(p => p.in_stock).length
  const lowStock = products.filter(p => (p.stock_quantity ?? 0) < 10 && p.in_stock).length

  // Filter products
  const filteredProducts = products.filter(p => {
    const matchSearch = !searchQuery || p.name.toLowerCase().includes(searchQuery.toLowerCase())
    const matchCategory = !filterCategory || p.category === filterCategory
    return matchSearch && matchCategory
  })

  const categories = [...new Set(products.map(p => p.category))]

  if (!farmer || farmer.user_type !== 'agrovet') return null

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
                <h1 className="text-lg font-bold text-amber-700 dark:text-amber-400">Agrovet Dashboard</h1>
                <p className="text-xs text-gray-500">{farmer.display_id} &middot; {farmer.name}</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <ThemeSwitcher />
              <LanguageSelector />
              <Button variant="ghost" size="icon" className="relative">
                <Bell className="h-5 w-5" />
                {pendingOrders > 0 && (
                  <span className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 text-white text-[10px] rounded-full flex items-center justify-center">{pendingOrders}</span>
                )}
              </Button>
              <Button variant="ghost" size="sm" onClick={async () => { await logout(); router.push('/login') }}>
                <LogOut className="h-4 w-4 mr-1" /> Logout
              </Button>
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-6 space-y-6">
        {/* Metrics Row */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard icon={DollarSign} label="Total Revenue" value={`KES ${totalRevenue.toLocaleString()}`} change="+12%" changeType="up" color="bg-green-600" />
          <MetricCard icon={ShoppingCart} label="Pending Orders" value={String(pendingOrders)} color="bg-yellow-600" />
          <MetricCard icon={Package} label="Active Products" value={String(activeProducts)} color="bg-blue-600" />
          <MetricCard icon={AlertTriangle} label="Low Stock Items" value={String(lowStock)} color="bg-red-500" />
        </div>

        {/* Tabs */}
        <Tabs defaultValue="products" className="space-y-4">
          <TabsList className="bg-white dark:bg-gray-900 border p-1 rounded-xl">
            <TabsTrigger value="products" className="rounded-lg data-[state=active]:bg-amber-100 dark:data-[state=active]:bg-amber-900/30 data-[state=active]:text-amber-700">
              <Package className="h-4 w-4 mr-2" /> Products
            </TabsTrigger>
            <TabsTrigger value="orders" className="rounded-lg data-[state=active]:bg-amber-100 dark:data-[state=active]:bg-amber-900/30 data-[state=active]:text-amber-700">
              <ShoppingCart className="h-4 w-4 mr-2" /> Orders
            </TabsTrigger>
            <TabsTrigger value="analytics" className="rounded-lg data-[state=active]:bg-amber-100 dark:data-[state=active]:bg-amber-900/30 data-[state=active]:text-amber-700">
              <BarChart3 className="h-4 w-4 mr-2" /> Analytics
            </TabsTrigger>
            <TabsTrigger value="profile" className="rounded-lg data-[state=active]:bg-amber-100 dark:data-[state=active]:bg-amber-900/30 data-[state=active]:text-amber-700">
              <User className="h-4 w-4 mr-2" /> Profile
            </TabsTrigger>
          </TabsList>

          {/* ─── Products Tab ─── */}
          <TabsContent value="products" className="space-y-4">
            {/* Toolbar */}
            <div className="flex flex-col sm:flex-row gap-3 items-start sm:items-center justify-between">
              <div className="flex gap-2 flex-1 w-full sm:w-auto">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <Input value={searchQuery} onChange={e => setSearchQuery(e.target.value)} placeholder="Search products..." className="pl-10" />
                </div>
                <Select value={filterCategory} onValueChange={v => setFilterCategory(v === 'all' ? '' : v)}>
                  <SelectTrigger className="w-40"><Filter className="h-4 w-4 mr-2" /><SelectValue placeholder="Category" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Categories</SelectItem>
                    {categories.map(c => <SelectItem key={c} value={c}>{c}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <Button onClick={() => setShowAddProduct(!showAddProduct)} className="bg-amber-600 hover:bg-amber-700">
                <Plus className="h-4 w-4 mr-2" /> Add Product
              </Button>
            </div>

            {showAddProduct && <AddProductForm onClose={() => setShowAddProduct(false)} onAdded={fetchData} />}

            {/* Product Grid */}
            {loading ? (
              <div className="flex items-center justify-center py-16">
                <Loader2 className="h-8 w-8 animate-spin text-amber-600" />
              </div>
            ) : filteredProducts.length === 0 ? (
              <Card className="p-12 text-center">
                <Package className="h-12 w-12 text-gray-300 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-gray-600 dark:text-gray-400">No Products Yet</h3>
                <p className="text-sm text-gray-500 mt-2">Add your first product to start selling to farmers.</p>
                <Button onClick={() => setShowAddProduct(true)} className="mt-4 bg-amber-600 hover:bg-amber-700">
                  <Plus className="h-4 w-4 mr-2" /> Add Your First Product
                </Button>
              </Card>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {filteredProducts.map(product => (
                  <Card key={product.id} className="hover:shadow-lg transition-shadow">
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between mb-3">
                        <div>
                          <h3 className="font-semibold text-base">{product.name}</h3>
                          <Badge variant="secondary" className="mt-1 text-xs">{product.category}</Badge>
                        </div>
                        <div className="flex items-center gap-1">
                          <div className={`px-2 py-0.5 rounded text-xs font-medium ${product.in_stock ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300' : 'bg-gray-100 text-gray-500'}`}>
                            {product.in_stock ? 'Active' : 'Inactive'}
                          </div>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-7 w-7 text-red-400 hover:text-red-600 hover:bg-red-50"
                            onClick={() => handleDeleteProduct(product.id)}
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </Button>
                        </div>
                      </div>
                      <p className="text-sm text-gray-500 line-clamp-2 mb-3">{product.description || 'No description'}</p>
                      <div className="flex items-end justify-between">
                        <div>
                          <p className="text-xl font-bold text-amber-600">KES {product.price_kes?.toLocaleString()}</p>
                          <p className="text-xs text-gray-500">per {product.unit || 'unit'}</p>
                        </div>
                        <div className="text-right">
                          <p className={`text-sm font-medium ${(product.stock_quantity ?? 0) < 10 ? 'text-red-500' : 'text-gray-600'}`}>
                            {product.stock_quantity ?? '∞'} in stock
                          </p>
                          {product.crop_applicable && product.crop_applicable.length > 0 && (
                            <p className="text-xs text-gray-400">For: {product.crop_applicable.join(', ')}</p>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>

          {/* ─── Orders Tab ─── */}
          <TabsContent value="orders" className="space-y-4">
            {/* Order filter bar */}
            <div className="flex gap-2 items-center">
              <Select value={orderFilter} onValueChange={v => setOrderFilter(v === 'all' ? '' : v)}>
                <SelectTrigger className="w-44"><Filter className="h-4 w-4 mr-2" /><SelectValue placeholder="All Statuses" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Statuses</SelectItem>
                  <SelectItem value="pending">Pending</SelectItem>
                  <SelectItem value="processing">Processing</SelectItem>
                  <SelectItem value="shipped">Shipped</SelectItem>
                  <SelectItem value="delivered">Delivered</SelectItem>
                  <SelectItem value="cancelled">Cancelled</SelectItem>
                </SelectContent>
              </Select>
              <p className="text-sm text-gray-500 ml-auto">
                {orders.filter(o => !orderFilter || (o.status ?? o.delivery_status) === orderFilter).length} orders
              </p>
            </div>
            {orders.length === 0 ? (
              <Card className="p-12 text-center">
                <ShoppingCart className="h-12 w-12 text-gray-300 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-gray-600 dark:text-gray-400">No Orders Yet</h3>
                <p className="text-sm text-gray-500 mt-2">Orders from farmers will appear here.</p>
              </Card>
            ) : (
              <div className="space-y-3">
                {orders
                  .filter(o => !orderFilter || (o.status ?? o.delivery_status) === orderFilter)
                  .map(order => {
                  const currentStatus = order.status ?? order.delivery_status ?? 'pending'
                  const nextStatuses: Record<string, string[]> = {
                    pending: ['processing', 'cancelled'],
                    processing: ['shipped', 'cancelled'],
                    shipped: ['delivered'],
                    delivered: [],
                    cancelled: [],
                  }
                  const actions = nextStatuses[currentStatus] || []

                  return (
                  <Card key={order.id} className="hover:shadow-md transition-shadow">
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                          <div className="w-10 h-10 bg-amber-100 dark:bg-amber-900 rounded-lg flex items-center justify-center">
                            <ShoppingCart className="h-5 w-5 text-amber-600" />
                          </div>
                          <div>
                            <p className="font-semibold">
                              {order.order_number || `Order #${order.id}`}
                            </p>
                            <p className="text-sm text-gray-500">
                              {order.quantity} {order.unit || 'units'} &middot; {order.payment_method || 'M-Pesa'}
                            </p>
                            {order.created_at && (
                              <p className="text-xs text-gray-400">{new Date(order.created_at).toLocaleDateString()}</p>
                            )}
                          </div>
                        </div>
                        <div className="text-right space-y-2">
                          <p className="font-bold text-lg">KES {(order.total_price ?? order.total_price_kes)?.toLocaleString()}</p>
                          <StatusBadge status={currentStatus} />
                          {actions.length > 0 && (
                            <div className="flex gap-1 mt-1 justify-end">
                              {actions.map(nextStatus => (
                                <Button
                                  key={nextStatus}
                                  size="sm"
                                  variant={nextStatus === 'cancelled' ? 'destructive' : 'outline'}
                                  className="text-xs h-7 px-2"
                                  disabled={updatingOrder === order.id}
                                  onClick={() => handleUpdateOrderStatus(order.id, nextStatus)}
                                >
                                  {updatingOrder === order.id ? (
                                    <Loader2 className="h-3 w-3 animate-spin" />
                                  ) : nextStatus === 'cancelled' ? (
                                    <><X className="h-3 w-3 mr-1" /> Cancel</>
                                  ) : nextStatus === 'processing' ? (
                                    <><Check className="h-3 w-3 mr-1" /> Confirm</>
                                  ) : nextStatus === 'shipped' ? (
                                    <><ChevronRight className="h-3 w-3 mr-1" /> Ship</>
                                  ) : (
                                    <><Check className="h-3 w-3 mr-1" /> {nextStatus.charAt(0).toUpperCase() + nextStatus.slice(1)}</>
                                  )}
                                </Button>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                  )
                })}
              </div>
            )}
          </TabsContent>

          {/* ─── Analytics Tab ─── */}
          <TabsContent value="analytics" className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Revenue Breakdown</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {categories.length > 0 ? categories.map(cat => {
                    const catOrders = orders.filter(o => {
                      const prod = products.find(p => p.id === o.product_id)
                      return prod?.category === cat
                    })
                    const catRevenue = catOrders.reduce((s, o) => s + (o.total_price || 0), 0)
                    const pct = totalRevenue > 0 ? (catRevenue / totalRevenue) * 100 : 0
                    return (
                      <div key={cat} className="space-y-1">
                        <div className="flex justify-between text-sm">
                          <span>{cat}</span>
                          <span className="font-medium">KES {catRevenue.toLocaleString()}</span>
                        </div>
                        <div className="h-2 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
                          <div className="h-full bg-amber-500 rounded-full transition-all" style={{ width: `${pct}%` }} />
                        </div>
                      </div>
                    )
                  }) : (
                    <p className="text-sm text-gray-500 text-center py-8">No sales data yet</p>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Top Products</CardTitle>
                </CardHeader>
                <CardContent>
                  {products.length > 0 ? (
                    <div className="space-y-3">
                      {products.slice(0, 5).map((p, idx) => {
                        const productOrders = orders.filter(o => o.product_id === p.id)
                        const revenue = productOrders.reduce((s, o) => s + (o.total_price || 0), 0)
                        return (
                          <div key={p.id} className="flex items-center gap-3">
                            <span className="w-6 h-6 bg-amber-100 dark:bg-amber-900 rounded-full flex items-center justify-center text-xs font-bold text-amber-700">{idx + 1}</span>
                            <div className="flex-1 min-w-0">
                              <p className="font-medium text-sm truncate">{p.name}</p>
                              <p className="text-xs text-gray-500">{productOrders.length} orders</p>
                            </div>
                            <p className="font-semibold text-sm">KES {revenue.toLocaleString()}</p>
                          </div>
                        )
                      })}
                    </div>
                  ) : (
                    <p className="text-sm text-gray-500 text-center py-8">Add products to see analytics</p>
                  )}
                </CardContent>
              </Card>

              <Card className="md:col-span-2">
                <CardHeader>
                  <CardTitle className="text-base">Order Status Distribution</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
                    {['pending', 'confirmed', 'shipped', 'delivered', 'cancelled'].map(status => {
                      const count = orders.filter(o => o.status === status).length
                      return (
                        <div key={status} className="text-center p-3 rounded-lg bg-gray-50 dark:bg-gray-900">
                          <p className="text-2xl font-bold">{count}</p>
                          <StatusBadge status={status} />
                        </div>
                      )
                    })}
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* ─── Profile Tab ─── */}
          <TabsContent value="profile" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2"><User className="h-5 w-5" /> Shop Profile</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-3">
                    <div>
                      <Label className="text-gray-500 text-xs">Display ID</Label>
                      <p className="font-mono font-semibold text-amber-600">{farmer.display_id}</p>
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
                      <Badge className="bg-amber-100 text-amber-700 dark:bg-amber-900 dark:text-amber-200">Agrovet</Badge>
                    </div>
                    <div>
                      <Label className="text-gray-500 text-xs">Total Products</Label>
                      <p className="font-semibold">{products.length}</p>
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
