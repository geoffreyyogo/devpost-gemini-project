"use client";

import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import Link from "next/link";
import {
  ShoppingCart, Search, Filter, ArrowLeft, Package,
  MapPin, Leaf, Star, Plus, Minus, ShoppingBag, X, Loader2, Check,
} from "lucide-react";
import { useAuthStore } from "@/store/authStore";

interface AgrovetProduct {
  id: number;
  name: string;
  name_sw?: string;
  description?: string;
  category: string;
  price_kes: number;
  unit: string;
  in_stock: boolean;
  stock_quantity?: number;
  supplier_name?: string;
  supplier_location?: string;
  supplier_county?: string;
  supplier_sub_county?: string;
  crop_applicable?: string[];
  image_url?: string;
}

const CATEGORIES = [
  { key: "seeds",       label: "Seeds",       icon: "🌱" },
  { key: "fertilizer",  label: "Fertilizer",  icon: "🧪" },
  { key: "pesticide",   label: "Pesticide",   icon: "🛡️" },
  { key: "tools",       label: "Tools",       icon: "🔧" },
  { key: "animal_feed", label: "Animal Feed", icon: "🐄" },
];

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function AgrovetPage() {
  const { t, i18n } = useTranslation();
  const lang = i18n.language;
  const { farmer, isAuthenticated } = useAuthStore();

  const [products, setProducts] = useState<AgrovetProduct[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState<string | null>(null);
  const [cart, setCart] = useState<Record<number, number>>({});
  const [showCart, setShowCart] = useState(false);
  const [ordering, setOrdering] = useState(false);
  const [orderSuccess, setOrderSuccess] = useState<string | null>(null);

  // Location filters
  const [counties, setCounties] = useState<string[]>([]);
  const [subCountiesMap, setSubCountiesMap] = useState<Record<string, string[]>>({});
  const [selectedCounty, setSelectedCounty] = useState<string>("");
  const [selectedSubCounty, setSelectedSubCounty] = useState<string>("");

  // Load counties list on mount
  useEffect(() => {
    async function loadCounties() {
      try {
        const res = await fetch(`${API}/api/counties`);
        const data = await res.json();
        const regions: Record<string, any> = data.data?.regions || {};
        const allCounties: string[] = [];
        Object.values(regions).forEach((r: any) => {
          if (r.counties) allCounties.push(...r.counties.map((c: any) => c.name || c));
        });
        setCounties(allCounties.sort());

        // Also load sub-counties map from public/regions endpoint
        const res2 = await fetch(`${API}/api/public/regions`);
        const data2 = await res2.json();
        setSubCountiesMap(data2.data?.sub_counties || {});
      } catch {
        // Fallback: farmer's county pre-selected
      }
    }
    loadCounties();
    // Pre-select farmer's county if logged in
    if (farmer?.county) setSelectedCounty(farmer.county);
    if (farmer?.sub_county) setSelectedSubCounty(farmer.sub_county);
  }, []);

  useEffect(() => {
    fetchProducts();
  }, [category, selectedCounty, selectedSubCounty]);

  async function fetchProducts() {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (category) params.set("category", category);
      if (selectedCounty) params.set("county", selectedCounty);
      if (selectedSubCounty) params.set("sub_county", selectedSubCounty);
      const res = await fetch(`${API}/api/agrovet/products?${params}`);
      const data = await res.json();
      setProducts(data.products || []);
    } catch {
      setProducts([]);
    } finally {
      setLoading(false);
    }
  }

  const filtered = products.filter((p) => {
    const name = lang === "sw" && p.name_sw ? p.name_sw : p.name;
    return name.toLowerCase().includes(search.toLowerCase());
  });

  const cartCount = Object.values(cart).reduce((a, b) => a + b, 0);

  function updateCart(id: number, delta: number) {
    setCart((prev) => {
      const qty = Math.max(0, (prev[id] || 0) + delta);
      if (qty === 0) {
        const { [id]: _, ...rest } = prev;
        return rest;
      }
      return { ...prev, [id]: qty };
    });
  }

  const cartItems = Object.entries(cart).map(([id, qty]) => {
    const product = products.find((p) => p.id === Number(id));
    return product ? { product, qty } : null;
  }).filter(Boolean) as { product: AgrovetProduct; qty: number }[];

  const cartTotal = cartItems.reduce((sum, item) => sum + item.product.price_kes * item.qty, 0);

  async function handleCheckout() {
    if (!isAuthenticated || !farmer?.id) {
      alert("Please log in to place an order.");
      return;
    }
    if (cartItems.length === 0) return;

    setOrdering(true);
    setOrderSuccess(null);
    try {
      const results = await Promise.all(
        cartItems.map((item) =>
          fetch(`${API}/api/agrovet/orders`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              farmer_id: farmer.id,
              product_id: item.product.id,
              quantity: item.qty,
              payment_method: "mpesa",
              order_source: "web",
            }),
          }).then((r) => r.json())
        )
      );
      const allOk = results.every((r) => r.order || r.id);
      if (allOk) {
        setCart({});
        setOrderSuccess(`${results.length} order(s) placed successfully! Total: KES ${cartTotal.toLocaleString()}`);
        setTimeout(() => setOrderSuccess(null), 8000);
        setShowCart(false);
      } else {
        alert("Some orders failed. Please try again.");
      }
    } catch {
      alert("Order failed. Please check your connection.");
    } finally {
      setOrdering(false);
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-green-50 to-white dark:from-gray-900 dark:to-gray-950">
      {/* Header */}
      <header className="sticky top-0 z-40 bg-white/80 dark:bg-gray-900/80 backdrop-blur border-b border-green-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
          <Link href="/dashboard" className="flex items-center gap-2 text-green-700 dark:text-green-400 hover:underline">
            <ArrowLeft size={18} /> Dashboard
          </Link>
          <h1 className="text-xl font-bold text-green-800 dark:text-green-300 flex items-center gap-2">
            <Package size={22} /> {t("agrovet.title", "Agrovet Shop")}
          </h1>
          <button
            onClick={() => setShowCart(true)}
            className="relative p-2 rounded-lg bg-green-100 dark:bg-green-800 text-green-700 dark:text-green-200 hover:bg-green-200 dark:hover:bg-green-700 transition"
          >
            <ShoppingCart size={20} />
            {cartCount > 0 && (
              <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs w-5 h-5 rounded-full flex items-center justify-center">
                {cartCount}
              </span>
            )}
          </button>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-6 space-y-6">
        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
          <input
            type="text"
            placeholder={t("agrovet.search", "Search products...")}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-3 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 focus:ring-2 focus:ring-green-400"
          />
        </div>

        {/* Location Filters */}
        <div className="flex flex-wrap gap-3">
          <div className="flex-1 min-w-[180px]">
            <select
              value={selectedCounty}
              onChange={(e) => { setSelectedCounty(e.target.value); setSelectedSubCounty(""); }}
              className="w-full px-3 py-2.5 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm focus:ring-2 focus:ring-green-400"
            >
              <option value="">All Counties</option>
              {counties.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>
          {selectedCounty && (subCountiesMap[selectedCounty]?.length ?? 0) > 0 && (
            <div className="flex-1 min-w-[180px]">
              <select
                value={selectedSubCounty}
                onChange={(e) => setSelectedSubCounty(e.target.value)}
                className="w-full px-3 py-2.5 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm focus:ring-2 focus:ring-green-400"
              >
                <option value="">All Sub-Counties</option>
                {(subCountiesMap[selectedCounty] || []).map((sc) => (
                  <option key={sc} value={sc}>{sc}</option>
                ))}
              </select>
            </div>
          )}
        </div>

        {/* Categories */}
        <div className="flex gap-2 overflow-x-auto pb-2">
          <button
            onClick={() => setCategory(null)}
            className={`flex-shrink-0 px-4 py-2 rounded-full text-sm font-medium transition
              ${!category ? "bg-green-600 text-white" : "bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300 hover:bg-gray-200"}`}
          >
            <Filter size={14} className="inline mr-1" /> All
          </button>
          {CATEGORIES.map((c) => (
            <button
              key={c.key}
              onClick={() => setCategory(c.key === category ? null : c.key)}
              className={`flex-shrink-0 px-4 py-2 rounded-full text-sm font-medium transition
                ${category === c.key ? "bg-green-600 text-white" : "bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300 hover:bg-gray-200"}`}
            >
              {c.icon} {c.label}
            </button>
          ))}
        </div>

        {/* Products Grid */}
        {loading ? (
          <div className="text-center py-20 text-gray-500">Loading products...</div>
        ) : filtered.length === 0 ? (
          <div className="text-center py-20 text-gray-500">
            <ShoppingBag size={48} className="mx-auto mb-3 opacity-30" />
            <p>No products found</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {filtered.map((p) => {
              const displayName = lang === "sw" && p.name_sw ? p.name_sw : p.name;
              const qty = cart[p.id] || 0;
              return (
                <div
                  key={p.id}
                  className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 overflow-hidden shadow-sm hover:shadow-md transition"
                >
                  {/* Image placeholder */}
                  <div className="h-40 bg-gradient-to-br from-green-100 to-emerald-50 dark:from-green-900/30 dark:to-emerald-900/20 flex items-center justify-center">
                    {p.image_url ? (
                      <img src={p.image_url} alt={displayName} className="h-full w-full object-cover" />
                    ) : (
                      <span className="text-5xl">
                        {CATEGORIES.find((c) => c.key === p.category)?.icon || "📦"}
                      </span>
                    )}
                  </div>

                  <div className="p-4 space-y-2">
                    <div className="flex items-start justify-between">
                      <h3 className="font-semibold text-gray-800 dark:text-gray-100">{displayName}</h3>
                      <span className="text-xs px-2 py-0.5 rounded-full bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300">
                        {p.category}
                      </span>
                    </div>

                    {p.description && (
                      <p className="text-sm text-gray-500 dark:text-gray-400 line-clamp-2">{p.description}</p>
                    )}

                    <div className="flex items-center gap-2 text-xs text-gray-500">
                      {p.supplier_county && (
                        <span className="flex items-center gap-0.5">
                          <MapPin size={12} /> {p.supplier_sub_county ? `${p.supplier_sub_county}, ` : ""}{p.supplier_county}
                        </span>
                      )}
                      {p.crop_applicable && p.crop_applicable.length > 0 && (
                        <span className="flex items-center gap-0.5">
                          <Leaf size={12} /> {p.crop_applicable.slice(0, 2).join(", ")}
                        </span>
                      )}
                    </div>

                    <div className="flex items-center justify-between pt-2 border-t border-gray-100 dark:border-gray-700">
                      <div>
                        <span className="text-lg font-bold text-green-700 dark:text-green-400">
                          KES {p.price_kes.toLocaleString()}
                        </span>
                        <span className="text-xs text-gray-400 ml-1">/{p.unit}</span>
                      </div>

                      <div className="flex items-center gap-1">
                        {qty > 0 && (
                          <>
                            <button
                              onClick={() => updateCart(p.id, -1)}
                              className="w-7 h-7 rounded-full bg-red-100 dark:bg-red-900 text-red-600 dark:text-red-300 flex items-center justify-center"
                            >
                              <Minus size={14} />
                            </button>
                            <span className="w-6 text-center text-sm font-medium">{qty}</span>
                          </>
                        )}
                        <button
                          onClick={() => updateCart(p.id, 1)}
                          className="w-7 h-7 rounded-full bg-green-600 text-white flex items-center justify-center hover:bg-green-700"
                        >
                          <Plus size={14} />
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </main>

      {/* Order Success Banner */}
      {orderSuccess && (
        <div className="fixed bottom-4 left-1/2 -translate-x-1/2 z-50 bg-green-600 text-white px-6 py-3 rounded-xl shadow-lg flex items-center gap-2 animate-in slide-in-from-bottom">
          <Check size={18} /> {orderSuccess}
        </div>
      )}

      {/* Cart Drawer */}
      {showCart && (
        <div className="fixed inset-0 z-50 flex justify-end">
          {/* Overlay */}
          <div
            className="absolute inset-0 bg-black/40"
            onClick={() => setShowCart(false)}
          />
          {/* Drawer */}
          <div className="relative w-full max-w-md bg-white dark:bg-gray-900 h-full shadow-2xl flex flex-col">
            {/* Drawer Header */}
            <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
              <h2 className="text-lg font-bold text-gray-800 dark:text-gray-100 flex items-center gap-2">
                <ShoppingCart size={20} /> Your Cart ({cartCount})
              </h2>
              <button
                onClick={() => setShowCart(false)}
                className="p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800"
              >
                <X size={20} />
              </button>
            </div>

            {/* Cart Items */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {cartItems.length === 0 ? (
                <div className="text-center py-12 text-gray-500">
                  <ShoppingBag size={48} className="mx-auto mb-3 opacity-30" />
                  <p>Your cart is empty</p>
                  <p className="text-sm mt-1">Browse products and add items to get started</p>
                </div>
              ) : (
                cartItems.map(({ product, qty }) => {
                  const displayName = lang === "sw" && product.name_sw ? product.name_sw : product.name;
                  return (
                    <div
                      key={product.id}
                      className="flex items-center gap-3 p-3 rounded-xl bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700"
                    >
                      <div className="w-12 h-12 rounded-lg bg-green-100 dark:bg-green-900/30 flex items-center justify-center text-2xl flex-shrink-0">
                        {CATEGORIES.find((c) => c.key === product.category)?.icon || "📦"}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-sm text-gray-800 dark:text-gray-100 truncate">
                          {displayName}
                        </p>
                        <p className="text-xs text-gray-500">
                          KES {product.price_kes.toLocaleString()} / {product.unit}
                        </p>
                      </div>
                      <div className="flex items-center gap-1">
                        <button
                          onClick={() => updateCart(product.id, -1)}
                          className="w-7 h-7 rounded-full bg-red-100 dark:bg-red-900 text-red-600 dark:text-red-300 flex items-center justify-center"
                        >
                          <Minus size={14} />
                        </button>
                        <span className="w-6 text-center text-sm font-medium">{qty}</span>
                        <button
                          onClick={() => updateCart(product.id, 1)}
                          className="w-7 h-7 rounded-full bg-green-600 text-white flex items-center justify-center hover:bg-green-700"
                        >
                          <Plus size={14} />
                        </button>
                      </div>
                      <p className="text-sm font-bold text-green-700 dark:text-green-400 w-20 text-right">
                        KES {(product.price_kes * qty).toLocaleString()}
                      </p>
                    </div>
                  );
                })
              )}
            </div>

            {/* Checkout Footer */}
            {cartItems.length > 0 && (
              <div className="border-t border-gray-200 dark:border-gray-700 p-4 space-y-3">
                <div className="flex items-center justify-between text-lg font-bold">
                  <span className="text-gray-700 dark:text-gray-300">Total</span>
                  <span className="text-green-700 dark:text-green-400">
                    KES {cartTotal.toLocaleString()}
                  </span>
                </div>
                {!isAuthenticated && (
                  <p className="text-xs text-amber-600 dark:text-amber-400">
                    Please log in to place an order
                  </p>
                )}
                <button
                  onClick={handleCheckout}
                  disabled={ordering || !isAuthenticated}
                  className="w-full py-3 rounded-xl bg-green-600 text-white font-semibold hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 transition"
                >
                  {ordering ? (
                    <><Loader2 size={18} className="animate-spin" /> Processing...</>
                  ) : (
                    <><ShoppingBag size={18} /> Checkout via M-Pesa</>
                  )}
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
