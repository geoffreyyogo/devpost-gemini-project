// Core Types for BloomWatch Kenya

export interface Farmer {
  _id?: string;
  phone: string;
  name: string;
  email?: string;
  region: string;
  county?: string;
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
  total_alerts_sent: number;
}

export interface DashboardData {
  farmer: Farmer;
  bloom_events: BloomEvent[];
  recent_alerts: Alert[];
  health_score: number;
  next_bloom?: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
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

// Component Props Types
export interface LayoutProps {
  children: React.ReactNode;
}

export interface NavItem {
  title: string;
  href: string;
  icon?: React.ComponentType<{ className?: string }>;
  disabled?: boolean;
  external?: boolean;
}

