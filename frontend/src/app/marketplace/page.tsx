"use client";

import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import Link from "next/link";
import {
  ArrowLeft, Store, Search, Filter, MapPin, Plus,
  TrendingUp, Wheat, Apple, Milk, Beef, Carrot,
  Calendar, Star, MessageSquare,
} from "lucide-react";

interface Listing {
  id: number;
  farmer_id: number;
  produce_name: string;
  produce_category: string;
  description?: string;
  quantity_available: number;
  unit: string;
  price_per_unit_kes: number;
  min_order_quantity?: number;
  county?: string;
  pickup_location?: string;
  delivery_available: boolean;
  quality_grade?: string;
  harvest_date?: string;
  image_url?: string;
  status: string;
  created_at?: string;
}

const PRODUCE_CATEGORIES = [
  { key: "grains",     label: "Grains",     icon: <Wheat size={16} /> },
  { key: "vegetables", label: "Vegetables", icon: <Carrot size={16} /> },
  { key: "fruits",     label: "Fruits",     icon: <Apple size={16} /> },
  { key: "dairy",      label: "Dairy",      icon: <Milk size={16} /> },
  { key: "livestock",  label: "Livestock",  icon: <Beef size={16} /> },
];

const GRADE_COLORS: Record<string, string> = {
  A: "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300",
  B: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300",
  C: "bg-orange-100 text-orange-700 dark:bg-orange-900 dark:text-orange-300",
};

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function MarketplacePage() {
  const { t } = useTranslation();

  const [listings, setListings] = useState<Listing[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState<string | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);

  useEffect(() => {
    fetchListings();
  }, [category]);

  async function fetchListings() {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (category) params.set("category", category);
      const res = await fetch(`${API}/api/marketplace/listings?${params}`);
      const data = await res.json();
      setListings(data.listings || []);
    } catch {
      setListings([]);
    } finally {
      setLoading(false);
    }
  }

  const filtered = listings.filter((l) =>
    l.produce_name.toLowerCase().includes(search.toLowerCase()),
  );

  return (
    <div className="min-h-screen bg-gradient-to-b from-amber-50 to-white dark:from-gray-900 dark:to-gray-950">
      {/* Header */}
      <header className="sticky top-0 z-40 bg-white/80 dark:bg-gray-900/80 backdrop-blur border-b border-amber-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
          <Link href="/dashboard" className="flex items-center gap-2 text-amber-700 dark:text-amber-400 hover:underline">
            <ArrowLeft size={18} /> Dashboard
          </Link>
          <h1 className="text-xl font-bold text-amber-800 dark:text-amber-300 flex items-center gap-2">
            <Store size={22} /> {t("marketplace.title", "Marketplace")}
          </h1>
          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-1 px-3 py-2 rounded-lg bg-amber-600 hover:bg-amber-700 text-white text-sm font-medium"
          >
            <Plus size={16} /> {t("marketplace.sell", "Sell Produce")}
          </button>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-6 space-y-6">
        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
          <input
            type="text"
            placeholder={t("marketplace.search", "Search produce...")}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-3 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 focus:ring-2 focus:ring-amber-400"
          />
        </div>

        {/* Categories */}
        <div className="flex gap-2 overflow-x-auto pb-2">
          <button
            onClick={() => setCategory(null)}
            className={`flex-shrink-0 px-4 py-2 rounded-full text-sm font-medium transition
              ${!category ? "bg-amber-600 text-white" : "bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300 hover:bg-gray-200"}`}
          >
            <Filter size={14} className="inline mr-1" /> All
          </button>
          {PRODUCE_CATEGORIES.map((c) => (
            <button
              key={c.key}
              onClick={() => setCategory(c.key === category ? null : c.key)}
              className={`flex-shrink-0 px-4 py-2 rounded-full text-sm font-medium transition flex items-center gap-1
                ${category === c.key ? "bg-amber-600 text-white" : "bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300 hover:bg-gray-200"}`}
            >
              {c.icon} {c.label}
            </button>
          ))}
        </div>

        {/* Listings */}
        {loading ? (
          <div className="text-center py-20 text-gray-500">Loading listings...</div>
        ) : filtered.length === 0 ? (
          <div className="text-center py-20 text-gray-500">
            <Store size={48} className="mx-auto mb-3 opacity-30" />
            <p>No listings found</p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="mt-4 px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700"
            >
              <Plus size={16} className="inline mr-1" /> Be the first to sell
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {filtered.map((l) => (
              <div
                key={l.id}
                className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 overflow-hidden shadow-sm hover:shadow-md transition"
              >
                {/* Image / Placeholder */}
                <div className="h-36 bg-gradient-to-br from-amber-100 to-orange-50 dark:from-amber-900/30 dark:to-orange-900/20 flex items-center justify-center relative">
                  {l.image_url ? (
                    <img src={l.image_url} alt={l.produce_name} className="h-full w-full object-cover" />
                  ) : (
                    <span className="text-4xl">
                      {PRODUCE_CATEGORIES.find((c) => c.key === l.produce_category)?.icon || <Wheat size={40} />}
                    </span>
                  )}

                  {/* Quality badge */}
                  {l.quality_grade && (
                    <span className={`absolute top-2 right-2 px-2 py-0.5 rounded-full text-xs font-bold ${GRADE_COLORS[l.quality_grade] || ""}`}>
                      Grade {l.quality_grade}
                    </span>
                  )}

                  {l.delivery_available && (
                    <span className="absolute top-2 left-2 px-2 py-0.5 rounded-full text-xs bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300">
                      🚚 Delivery
                    </span>
                  )}
                </div>

                <div className="p-4 space-y-2">
                  <div className="flex items-start justify-between">
                    <h3 className="font-semibold text-gray-800 dark:text-gray-100">
                      {l.produce_name}
                    </h3>
                    <span className="text-xs px-2 py-0.5 rounded-full bg-amber-100 dark:bg-amber-900 text-amber-700 dark:text-amber-300">
                      {l.produce_category}
                    </span>
                  </div>

                  {l.description && (
                    <p className="text-sm text-gray-500 dark:text-gray-400 line-clamp-2">{l.description}</p>
                  )}

                  <div className="flex items-center gap-3 text-xs text-gray-500">
                    {l.county && (
                      <span className="flex items-center gap-0.5">
                        <MapPin size={12} /> {l.county}
                      </span>
                    )}
                    {l.harvest_date && (
                      <span className="flex items-center gap-0.5">
                        <Calendar size={12} /> Harvested {l.harvest_date}
                      </span>
                    )}
                  </div>

                  <div className="flex items-center justify-between pt-2 border-t border-gray-100 dark:border-gray-700">
                    <div>
                      <span className="text-lg font-bold text-amber-700 dark:text-amber-400">
                        KES {l.price_per_unit_kes.toLocaleString()}
                      </span>
                      <span className="text-xs text-gray-400 ml-1">/{l.unit}</span>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-medium text-gray-700 dark:text-gray-300">
                        {l.quantity_available.toLocaleString()} {l.unit}
                      </div>
                      <div className="text-xs text-gray-400">available</div>
                    </div>
                  </div>

                  <Link
                    href={`/marketplace/${l.id}`}
                    className="block w-full text-center mt-2 px-4 py-2 rounded-lg bg-amber-100 dark:bg-amber-900/50 text-amber-700 dark:text-amber-300 hover:bg-amber-200 dark:hover:bg-amber-900 font-medium text-sm transition"
                  >
                    <MessageSquare size={14} className="inline mr-1" /> View &amp; Bid
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>

      {/* Create Listing Modal */}
      {showCreateModal && (
        <CreateListingModal
          onClose={() => setShowCreateModal(false)}
          onCreated={() => { setShowCreateModal(false); fetchListings(); }}
        />
      )}
    </div>
  );
}


/* ─── Create Listing Modal ─── */

function CreateListingModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const { t } = useTranslation();
  const [submitting, setSubmitting] = useState(false);
  const [form, setForm] = useState({
    produce_name: "",
    produce_category: "grains",
    description: "",
    quantity_available: "",
    unit: "kg",
    price_per_unit_kes: "",
    county: "",
    pickup_location: "",
    delivery_available: false,
    quality_grade: "",
  });

  function set(key: string, value: string | boolean) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  async function submit() {
    if (!form.produce_name || !form.quantity_available || !form.price_per_unit_kes) return;
    setSubmitting(true);
    try {
      const res = await fetch(`${API}/api/marketplace/listings`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          farmer_id: 1, // TODO: get from auth store
          produce_name: form.produce_name,
          produce_category: form.produce_category,
          description: form.description || undefined,
          quantity_available: parseFloat(form.quantity_available),
          unit: form.unit,
          price_per_unit_kes: parseFloat(form.price_per_unit_kes),
          county: form.county || undefined,
          pickup_location: form.pickup_location || undefined,
          delivery_available: form.delivery_available,
          quality_grade: form.quality_grade || undefined,
        }),
      });
      if (res.ok) onCreated();
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
      <div className="bg-white dark:bg-gray-800 rounded-2xl max-w-lg w-full max-h-[90vh] overflow-y-auto p-6 space-y-4">
        <h2 className="text-xl font-bold text-gray-800 dark:text-white flex items-center gap-2">
          <Plus size={20} /> {t("marketplace.createListing", "New Listing")}
        </h2>

        <input placeholder="Produce name*" value={form.produce_name} onChange={(e) => set("produce_name", e.target.value)}
          className="w-full px-3 py-2 rounded-lg border dark:border-gray-600 dark:bg-gray-700" />

        <select value={form.produce_category} onChange={(e) => set("produce_category", e.target.value)}
          className="w-full px-3 py-2 rounded-lg border dark:border-gray-600 dark:bg-gray-700">
          {PRODUCE_CATEGORIES.map((c) => <option key={c.key} value={c.key}>{c.label}</option>)}
        </select>

        <textarea placeholder="Description" value={form.description} onChange={(e) => set("description", e.target.value)}
          className="w-full px-3 py-2 rounded-lg border dark:border-gray-600 dark:bg-gray-700" rows={2} />

        <div className="grid grid-cols-3 gap-2">
          <input placeholder="Quantity*" type="number" value={form.quantity_available} onChange={(e) => set("quantity_available", e.target.value)}
            className="px-3 py-2 rounded-lg border dark:border-gray-600 dark:bg-gray-700" />
          <select value={form.unit} onChange={(e) => set("unit", e.target.value)}
            className="px-3 py-2 rounded-lg border dark:border-gray-600 dark:bg-gray-700">
            <option value="kg">kg</option><option value="bag">bag</option><option value="crate">crate</option>
            <option value="piece">piece</option><option value="litre">litre</option>
          </select>
          <input placeholder="Price/unit*" type="number" value={form.price_per_unit_kes} onChange={(e) => set("price_per_unit_kes", e.target.value)}
            className="px-3 py-2 rounded-lg border dark:border-gray-600 dark:bg-gray-700" />
        </div>

        <div className="grid grid-cols-2 gap-2">
          <input placeholder="County" value={form.county} onChange={(e) => set("county", e.target.value)}
            className="px-3 py-2 rounded-lg border dark:border-gray-600 dark:bg-gray-700" />
          <select value={form.quality_grade} onChange={(e) => set("quality_grade", e.target.value)}
            className="px-3 py-2 rounded-lg border dark:border-gray-600 dark:bg-gray-700">
            <option value="">Grade</option><option value="A">A</option><option value="B">B</option><option value="C">C</option>
          </select>
        </div>

        <input placeholder="Pickup location" value={form.pickup_location} onChange={(e) => set("pickup_location", e.target.value)}
          className="w-full px-3 py-2 rounded-lg border dark:border-gray-600 dark:bg-gray-700" />

        <label className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-300">
          <input type="checkbox" checked={form.delivery_available} onChange={(e) => set("delivery_available", e.target.checked)} />
          Delivery available
        </label>

        <div className="flex gap-2 pt-2">
          <button onClick={onClose} className="flex-1 py-2 rounded-lg border border-gray-300 dark:border-gray-600">Cancel</button>
          <button onClick={submit} disabled={submitting}
            className="flex-1 py-2 rounded-lg bg-amber-600 text-white hover:bg-amber-700 disabled:opacity-50 font-medium">
            {submitting ? "Creating..." : "Create Listing"}
          </button>
        </div>
      </div>
    </div>
  );
}
