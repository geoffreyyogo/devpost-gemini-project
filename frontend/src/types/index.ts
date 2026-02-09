// Core Types for Smart Shamba

export type UserType = 'farmer' | 'agrovet' | 'buyer' | 'admin';

export interface Farmer {
  _id?: string;
  id?: number;
  phone: string;
  name: string;
  email?: string;
  region: string;
  county?: string;
  sub_county?: string;
  crops: string[];
  language: 'en' | 'sw';
  sms_enabled: boolean;
  registered_via: 'web' | 'ussd' | 'manual';
  registered_at?: string;
  registered_by?: string;
  location_lat?: number;
  location_lon?: number;
  farm_size?: number;
  is_admin?: boolean;
  active?: boolean;
  last_login?: string;
  alert_count?: number;
  user_type?: UserType;
  display_id?: string;
  avatar_url?: string;
}

// Farm management
export interface Farm {
  id: number;
  farmer_id?: number;
  name?: string;
  latitude: number;
  longitude: number;
  altitude_m?: number;
  county?: string;
  sub_county?: string;
  size_acres?: number;
  crops?: string[];
  soil_type?: string;
  irrigation_type?: string;
  device_ids?: string[];
  has_iot?: boolean;
  sensor_count?: number;
  active?: boolean;
  created_at?: string;
}

export interface FarmOverview {
  farm: Farm;
  satellite: Array<{
    date: string;
    ndvi?: number;
    ndwi?: number;
    evi?: number;
    savi?: number;
    lai?: number;
    rainfall_mm?: number;
    temperature_mean_c?: number;
    soil_moisture_pct?: number;
    soil_ph?: number;
    crop_water_stress_index?: number;
    land_surface_temperature_c?: number;
  }>;
  predictions: Array<{
    model: string;
    bloom_probability?: number;
    drought_risk?: number;
    pest_risk?: number;
    yield_potential?: number;
    confidence?: number;
    ts: string;
  }>;
  iot?: {
    latest: IoTDeviceReading[];
    hourly: IoTHourlyAvg[];
    daily: IoTDailySummary[];
  } | null;
}

export interface IoTDeviceReading {
  device_id: string;
  ts: string;
  temperature_c?: number;
  humidity_pct?: number;
  soil_moisture_pct?: number;
  soil_ph?: number;
  soil_nitrogen?: number;
  soil_phosphorus?: number;
  soil_potassium?: number;
  wind_speed_ms?: number;
  light_lux?: number;
  pressure_hpa?: number;
  co2_ppm?: number;
  battery_pct?: number;
  rssi_dbm?: number;
}

export interface IoTHourlyAvg {
  bucket: string;
  device_id: string;
  avg_temp?: number;
  avg_humidity?: number;
  avg_soil_moisture?: number;
  avg_ph?: number;
  min_temp?: number;
  max_temp?: number;
  reading_count: number;
}

export interface IoTDailySummary {
  day: string;
  device_id: string;
  avg_temp?: number;
  min_temp?: number;
  max_temp?: number;
  avg_humidity?: number;
  avg_soil_moisture?: number;
  total_rainfall?: number;
  min_battery?: number;
  reading_count: number;
}

export interface FarmIoTData {
  latest: IoTDeviceReading[];
  hourly: IoTHourlyAvg[];
  daily: IoTDailySummary[];
}

// User profiles
export interface AgrovetProfile {
  id: number;
  user_id: number;
  shop_name: string;
  shop_description?: string;
  business_registration_no?: string;
  kra_pin?: string;
  shop_county?: string;
  shop_sub_county?: string;
  shop_address?: string;
  categories?: string[];
  total_products: number;
  total_orders: number;
  total_revenue_kes: number;
  average_rating?: number;
  mpesa_till_number?: string;
  mpesa_paybill?: string;
  is_verified: boolean;
  logo_url?: string;
  active: boolean;
  created_at?: string;
}

export interface BuyerProfile {
  id: number;
  user_id: number;
  business_name?: string;
  business_type?: string;
  county?: string;
  sub_county?: string;
  preferred_produce?: string[];
  preferred_counties?: string[];
  total_purchases: number;
  total_spent_kes: number;
  average_rating?: number;
  is_verified: boolean;
  active: boolean;
  created_at?: string;
}

export interface Transaction {
  id: number;
  ref: string;
  type: string;
  amount_kes: number;
  method: string;
  status: string;
  buyer_id: number;
  seller_id?: number;
  created_at?: string;
}

export interface Session {
  session_token: string;
  farmer_id: string;
  phone: string;
  farmer_data: Farmer;
  created_at: string;
  expires_at: string;
}

export interface AuthResponse {
  success: boolean;
  message?: string;
  farmer?: Farmer;
  session_token?: string;
  demo?: boolean;
}

export interface BloomEvent {
  _id?: string;
  region: string;
  crop_type: string;
  bloom_intensity: number;
  ndvi_mean: number;
  health_score: number;
  bloom_confidence: number;
  bloom_risk: 'Low' | 'Moderate' | 'High';
  data_source: string;
  timestamp: string;
  location_lat?: number;
  location_lon?: number;
  bloom_months: number[];
  bloom_scores: number[];
  bloom_dates: string[];
}

export interface Alert {
  _id?: string;
  farmer_id: string;
  farmer_phone: string;
  farmer_email?: string;
  crop: string;
  message: string;
  bloom_risk: string;
  health_score: number;
  ndvi: number;
  data_source: string;
  timestamp: string;
  sent_sms: boolean;
  sent_email: boolean;
  delivered?: boolean;
  alert_type: 'welcome' | 'bloom_alert' | 'crop_update' | 'custom';
}

export interface Region {
  id: string;
  name: string;
  name_sw: string;
  counties: string[];
  main_crops: string[];
  coordinates: {
    lat: number;
    lon: number;
  };
}

export interface Crop {
  id: string;
  name: string;
  name_sw: string;
  category: string;
  growing_season: string[];
  bloom_months: number[];
}

export interface Statistics {
  total_farmers: number;
  active_farmers: number;
  farmers_by_region: Record<string, number>;
  farmers_by_crop: Record<string, number>;
  farmers_by_source: Record<string, number>;
  total_alerts_sent: number;
}

export interface DashboardData {
  farmer: Farmer;
  bloom_events: BloomEvent[];
  recent_alerts: Alert[];
  health_score: number;
  next_bloom?: string;
  season?: {
    name: string;
    status: string;
  };
  climate_history?: Array<{
    date: string;
    temperature: number;
    rainfall: number;
  }>;
  ndvi_history?: Array<{
    date: string;
    ndvi: number;
  }>;
  current_weather?: {
    temperature: number;
    rainfall: number;
    conditions: string;
  };
  ndvi_average?: number;
  ml_prediction?: any;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  reasoning?: string | null;
  timestamp: string;
  conversation_id?: string;
  via?: string;
}

export interface Conversation {
  id: string;
  title: string;
  channel: string;
  message_count: number;
  last_message?: string | null;
  last_response?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ConversationMessage {
  id: number;
  role: string;
  message: string;
  response?: string | null;
  reasoning?: string | null;
  via: string;
  timestamp: string;
}

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
}

// Form Types
export interface LoginFormData {
  phone: string;
  password: string;
}

export interface RegisterFormData {
  name: string;
  phone: string;
  email?: string;
  password: string;
  region: string;
  county?: string;
  sub_county?: string;
  crops: string[];
  language: 'en' | 'sw';
  sms_enabled: boolean;
  location_lat?: number;
  location_lon?: number;
  farm_size?: number;
}

export interface ProfileUpdateData {
  name?: string;
  email?: string;
  region?: string;
  county?: string;
  sub_county?: string;
  crops?: string[];
  language?: 'en' | 'sw';
  sms_enabled?: boolean;
  farm_size?: number;
}

export interface SendAlertData {
  target: 'all' | 'region' | 'crop' | 'individual';
  target_value?: string;
  alert_type: 'bloom' | 'weather' | 'custom';
  message?: string;
}

// IoT / Sensor Types
export interface SensorReading {
  id?: number;
  farm_id: number;
  device_id: string;
  temperature_c?: number;
  humidity_pct?: number;
  soil_moisture_pct?: number;
  soil_ph?: number;
  light_lux?: number;
  rainfall_mm?: number;
  wind_speed_ms?: number;
  battery_pct?: number;
  rssi_dbm?: number;
  reading_time?: string;
}

// Agrovet Types
export interface AgrovetProduct {
  id: number;
  agrovet_id?: number;
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
  crop_applicable?: string[];
  image_url?: string;
}

export interface AgrovetOrder {
  id: number;
  order_number?: string;
  farmer_id: number;
  agrovet_id?: number;
  product_id: number;
  quantity: number;
  total_price_kes: number;
  total_price?: number;
  payment_status: string;
  delivery_status: string;
  status?: string;
  order_source: string;
  unit?: string;
  payment_method?: string;
  delivery_address?: string;
  created_at?: string;
}

// Marketplace Types
export interface MarketplaceListing {
  id: number;
  farmer_id: number;
  produce_name: string;
  produce_category: string;
  category?: string;
  description?: string;
  quantity_available: number;
  unit: string;
  price_per_unit_kes: number;
  min_order_quantity?: number;
  county?: string;
  sub_county?: string;
  pickup_location?: string;
  delivery_available: boolean;
  quality_grade?: string;
  harvest_date?: string;
  image_url?: string;
  status: string;
  created_at?: string;
}

export interface MarketplaceBid {
  id: number;
  listing_id: number;
  buyer_id: number;
  quantity: number;
  price_per_unit_kes: number;
  total_price_kes: number;
  status: string;
  message?: string;
  created_at?: string;
}

// Component Props Types

export interface LayoutProps {
  children: React.ReactNode;
}

export interface NavItem {
  title: string;
  href: string;
  icon?: string | React.ComponentType<{ className?: string }>;
  disabled?: boolean;
  external?: boolean;
}

// Registration form types for different user roles
export interface AgrovetRegisterFormData {
  name: string;
  phone: string;
  password: string;
  email?: string;
  shop_name: string;
  shop_description?: string;
  business_registration_no?: string;
  kra_pin?: string;
  shop_county?: string;
  shop_sub_county?: string;
  shop_address?: string;
  categories?: string[];
  mpesa_till_number?: string;
  mpesa_paybill?: string;
}

export interface BuyerRegisterFormData {
  name: string;
  phone: string;
  password: string;
  email?: string;
  business_name?: string;
  business_type?: string;
  county?: string;
  sub_county?: string;
  preferred_produce?: string[];
  preferred_counties?: string[];
}

export interface FarmFormData {
  name?: string;
  latitude: number;
  longitude: number;
  altitude_m?: number;
  county?: string;
  sub_county?: string;
  size_acres?: number;
  crops?: string[];
  soil_type?: string;
  irrigation_type?: string;
}
export interface LayoutProps {
  children: React.ReactNode;
}

