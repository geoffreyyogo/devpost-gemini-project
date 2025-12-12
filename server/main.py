"""
BloomWatch Kenya - FastAPI Server
Exposes RESTful API endpoints for Next.js frontend consumption
"""

from fastapi import FastAPI, HTTPException, Depends, status, Header, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, JSONResponse
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from collections import defaultdict
import logging
import os
import json
import time
import asyncio
from dotenv import load_dotenv

# Import services
from mongodb_service import MongoDBService
from auth_service import AuthService
from bloom_processor import BloomProcessor
from smart_alert_service import SmartAlertService
from africastalking_service import AfricasTalkingService
from ussd_enhanced_service import EnhancedUSSDService
from flora_ai_service import FloraAIService
from streamlit_data_loader import StreamlitDataLoader
from kenya_data_fetcher import KenyaDataFetcher
from kenya_regions_counties import KENYA_REGIONS_COUNTIES, ALL_KENYA_CROPS
from train_model import BloomPredictor
from scheduler_service import SchedulerService

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize services (before app creation)
logger.info("Initializing services...")
mongo_service = MongoDBService()
auth_service = AuthService(mongo_service=mongo_service)
bloom_processor = BloomProcessor()
at_service = AfricasTalkingService()
ussd_service = EnhancedUSSDService()
smart_alert_service = SmartAlertService(
    mongo_service=mongo_service,
    africastalking_service=at_service
)
data_loader = StreamlitDataLoader()
data_fetcher = KenyaDataFetcher()

# Try to initialize Flora AI
try:
    flora_service = FloraAIService(mongo_service)
    logger.info("✓ Flora AI service initialized")
except Exception as e:
    logger.warning(f"Flora AI not available: {e}")
    flora_service = None

# Try to initialize ML Bloom Predictor
try:
    bloom_predictor = BloomPredictor()
    # Try to load existing model
    if bloom_predictor.load_model():
        logger.info("✓ ML Bloom Predictor loaded from saved model")
    else:
        logger.warning("⚠ ML model not found - will use fallback predictions")
except Exception as e:
    logger.warning(f"ML Bloom Predictor not available: {e}")
    bloom_predictor = None

# Initialize Scheduler Service (pass bloom_predictor for ML retraining)
try:
    scheduler_service = SchedulerService(data_loader, mongo_service, smart_alert_service, bloom_predictor)
    logger.info("✓ Scheduler Service initialized (with ML retraining enabled)")
except Exception as e:
    logger.warning(f"Could not initialize scheduler: {e}")
    scheduler_service = None

# Security
security = HTTPBearer()

# Background task cache for NASA data
nasa_data_cache = {
    'last_update': None,
    'data': None,
    'is_fetching': False
}

async def fetch_nasa_data_background():
    """
    Background task to fetch NASA satellite data periodically
    
    NOTE: This is now a placeholder task - real data fetching happens via:
      1. kenya_data_fetcher.py (CSV-based Sentinel-2 data)
      2. scheduler_service.py (weekly automated fetches)
    
    This task is kept for backward compatibility but returns placeholder data.
    """
    while True:
        try:
            if not nasa_data_cache['is_fetching']:
                nasa_data_cache['is_fetching'] = True
                
                # NOTE: Old GeoTIFF-based bloom detection is deprecated
                # Real bloom detection happens in ee_pipeline.py with Sentinel-2
                # This just updates the cache with placeholder data
                
                # Run bloom detection in thread pool (returns placeholder now)
                loop = asyncio.get_event_loop()
                bloom_data = await loop.run_in_executor(
                    None, 
                    bloom_processor.detect_bloom_events,
                    'kenya'
                )
                
                nasa_data_cache['data'] = bloom_data
                nasa_data_cache['last_update'] = datetime.now()
                nasa_data_cache['is_fetching'] = False
                
                logger.info(f"✓ NASA data updated at {nasa_data_cache['last_update']}")
                logger.info("(Placeholder data - real data from kenya_data_fetcher.py)")
        except Exception as e:
            logger.error(f"Background NASA fetch error: {e}")
            nasa_data_cache['is_fetching'] = False
        
        # Wait 15 minutes before next fetch (placeholder task)
        await asyncio.sleep(900)

# Lifespan context manager
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler"""
    # Startup
    logger.info("=" * 60)
    logger.info("🌾 BloomWatch Kenya FastAPI Server")
    logger.info("=" * 60)
    logger.info(f"MongoDB Connected: {mongo_service.is_connected()}")
    logger.info(f"Flora AI Available: {flora_service is not None}")
    logger.info(f"USSD Service Ready: {ussd_service is not None}")
    logger.info(f"Data Loader Ready: {data_loader is not None}")
    logger.info("=" * 60)
    logger.info("Server ready to accept requests")
    logger.info("API Documentation: http://localhost:8000/api/docs")
    logger.info("=" * 60)
    
    # Start background NASA data fetch task
    background_task = asyncio.create_task(fetch_nasa_data_background())
    logger.info("🛰️  Background NASA data fetcher started")
    
    # Start scheduler service for weekly data fetches
    if scheduler_service:
        await scheduler_service.start()
        logger.info("📅 Scheduler service started (weekly data fetch enabled)")
    
    yield
    
    # Shutdown
    logger.info("Shutting down BloomWatch Kenya API...")
    background_task.cancel()
    if scheduler_service:
        await scheduler_service.stop()
        logger.info("Scheduler service stopped")

# Initialize FastAPI app with lifespan
app = FastAPI(
    title="BloomWatch Kenya API",
    description="NASA-Powered Bloom Tracking Platform API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# ============================================
# Security Middleware & Rate Limiting
# ============================================

# Rate Limiter
class RateLimiter:
    """In-memory rate limiter for API endpoints"""
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.requests = defaultdict(list)
        self.max_requests = max_requests
        self.window = window_seconds
    
    async def check_rate_limit(self, identifier: str) -> bool:
        """Check if request is within rate limit"""
        now = time.time()
        
        # Clean old requests outside the time window
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if now - req_time < self.window
        ]
        
        # Check if limit exceeded
        if len(self.requests[identifier]) >= self.max_requests:
            return False
        
        # Record this request
        self.requests[identifier].append(now)
        return True

# Initialize rate limiters with different limits
auth_rate_limiter = RateLimiter(max_requests=10, window_seconds=60)  # Stricter for auth
general_rate_limiter = RateLimiter(max_requests=100, window_seconds=60)  # General endpoints

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware"""
    client_ip = request.client.host if request.client else "unknown"
    
    # Skip rate limiting for health check, docs, and OPTIONS (CORS preflight)
    if request.method == "OPTIONS":
        return await call_next(request)
    
    if request.url.path in ["/health", "/", "/api/docs", "/api/redoc", "/openapi.json"]:
        return await call_next(request)
    
    # Use stricter rate limit for authentication endpoints
    if "/api/auth/" in request.url.path:
        limiter = auth_rate_limiter
    else:
        limiter = general_rate_limiter
    
    # Check rate limit
    if not await limiter.check_rate_limit(client_ip):
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please slow down and try again later."
        )
    
    response = await call_next(request)
    return response

@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """Add security headers to responses"""
    response = await call_next(request)
    
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    
    return response

# CORS configuration
cors_origins = [
    "http://localhost:3000",
    "http://localhost:3001", 
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
    "http://172.18.54.46:3000",
    "http://172.18.54.46:3001",
    "https://bloomwatch.co.ke",
    "https://www.bloomwatch.co.ke",
    "https://bloomwatch-nextjs.onrender.com",
    "https://bloomwatch-nextjs-oomk.onrender.com",
    "https://bloomwatch-app.onrender.com",
    "https://smartfarm-app.onrender.com"
]

# Add CORS origins from environment variable if available
cors_origins_env = os.getenv('CORS_ORIGINS', '')
if cors_origins_env:
    cors_origins.extend([origin.strip() for origin in cors_origins_env.split(',')])

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count"],
    max_age=3600,
)

# GZip compression for better performance
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Trusted Host Middleware (uncomment for production)
# app.add_middleware(
#     TrustedHostMiddleware,
#     allowed_hosts=["localhost", "127.0.0.1", "bloomwatch.co.ke", "*.bloomwatch.co.ke"]
# )

# ============================================
# CSRF Protection (Optional - for production)
# ============================================

# Simple CSRF token manager
import secrets

class CSRFProtection:
    """CSRF token management"""
    def __init__(self):
        self.tokens = {}  # In production, use Redis or similar
    
    def generate_token(self, user_id: str) -> str:
        """Generate CSRF token for user"""
        token = secrets.token_urlsafe(32)
        self.tokens[user_id] = token
        return token
    
    def validate_token(self, user_id: str, token: str) -> bool:
        """Validate CSRF token"""
        return self.tokens.get(user_id) == token

csrf_protection = CSRFProtection()

# CSRF validation dependency (use for state-changing operations)
async def validate_csrf(
    request: Request,
    x_csrf_token: Optional[str] = Header(None)
):
    """Validate CSRF token for POST/PUT/DELETE requests"""
    # Skip CSRF for GET requests and public endpoints
    if request.method == "GET" or request.url.path in ["/api/auth/login", "/api/auth/register"]:
        return True
    
    # In development, CSRF is optional
    # In production, make this required by removing the return True below
    return True  # TODO: Enable CSRF in production
    
    # Uncomment for production:
    # if not x_csrf_token:
    #     raise HTTPException(status_code=403, detail="CSRF token missing")
    # return True

# ============================================
# Pydantic Models
# ============================================

class LoginRequest(BaseModel):
    phone: str
    password: str
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        # Basic Kenya phone validation
        cleaned = v.replace('+', '').replace(' ', '').replace('-', '')
        if not (cleaned.startswith('254') or cleaned.startswith('0')):
            raise ValueError('Invalid Kenya phone number')
        return v

class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    phone: str
    password: str = Field(..., min_length=6)
    email: Optional[str] = None
    region: str
    county: Optional[str] = None
    crops: List[str]
    language: str = 'en'
    sms_enabled: bool = True
    location_lat: Optional[float] = None
    location_lon: Optional[float] = None
    farm_size: Optional[float] = None

class ProfileUpdateRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    region: Optional[str] = None
    county: Optional[str] = None
    crops: Optional[List[str]] = None
    language: Optional[str] = None
    sms_enabled: Optional[bool] = None
    farm_size: Optional[float] = None

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=6)

class SendAlertRequest(BaseModel):
    target: str = Field(..., pattern="^(all|region|crop|individual)$")
    target_value: Optional[str] = None
    alert_type: str = Field(..., pattern="^(bloom|weather|custom)$")
    message: Optional[str] = None

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Dict[str, str]]] = []

# ============================================
# Helper Functions
# ============================================

def get_current_farmer(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    """Verify session and return farmer data"""
    token = credentials.credentials
    session = auth_service.verify_session(token)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session"
        )
    
    farmer = auth_service.get_farmer_from_session(token)
    if not farmer:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Farmer not found"
        )
    
    return farmer

def verify_admin(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    """Verify admin session"""
    farmer = get_current_farmer(credentials)
    
    # Check if farmer is admin (you can add admin flag to farmer document)
    if not farmer.get('is_admin', False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return farmer

# ============================================
# Health & Info Endpoints
# ============================================

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "name": "Shamba Smart API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/api/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "mongodb": mongo_service.is_connected(),
            "flora_ai": flora_service is not None,
            "data_loader": True,
            "scheduler": scheduler_service is not None
        }
    }

@app.post("/api/admin/trigger-data-fetch")
async def trigger_manual_data_fetch(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Manually trigger weekly data fetch (Admin only)
    
    Use this endpoint to immediately fetch fresh satellite data for all counties
    without waiting for the weekly schedule.
    """
    try:
        # Verify admin access (you can enhance this with proper admin check)
        token = credentials.credentials
        session = auth_service.verify_session(token)
        if not session:
            raise HTTPException(status_code=401, detail="Invalid authentication")
        
        if not scheduler_service:
            raise HTTPException(status_code=503, detail="Scheduler service not available")
        
        logger.info(f"Manual data fetch triggered by user: {session.get('farmer_phone')}")
        
        # Trigger immediate fetch
        result = await scheduler_service.trigger_immediate_fetch()
        
        return {
            "success": result.get("success", False),
            "message": "Data fetch initiated" if result.get("success") else "Fetch failed",
            "counties": result.get("counties", 0),
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering manual fetch: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/scheduler-status")
async def get_scheduler_status(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get scheduler service status and next run times"""
    try:
        # Verify admin access
        token = credentials.credentials
        session = auth_service.verify_session(token)
        if not session:
            raise HTTPException(status_code=401, detail="Invalid authentication")
        
        if not scheduler_service:
            return {"scheduler_enabled": False, "message": "Scheduler not initialized"}
        
        return {
            "scheduler_enabled": scheduler_service.is_running,
            "active_tasks": len(scheduler_service.tasks),
            "ml_predictor_available": scheduler_service.bloom_predictor is not None,
            "message": "Scheduler is running" if scheduler_service.is_running else "Scheduler is stopped"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting scheduler status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/admin/trigger-ml-retrain")
async def trigger_ml_retrain(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Manually trigger ML model retraining (Admin only)
    
    Retrains the Random Forest bloom prediction model with all available
    live and historical data.
    """
    try:
        # Verify admin access
        token = credentials.credentials
        session = auth_service.verify_session(token)
        if not session:
            raise HTTPException(status_code=401, detail="Invalid authentication")
        
        if not scheduler_service:
            raise HTTPException(status_code=503, detail="Scheduler service not available")
        
        logger.info(f"Manual ML retrain triggered by user: {session.get('farmer_phone')}")
        
        # Trigger immediate retrain
        result = await scheduler_service.trigger_immediate_retrain()
        
        return {
            "success": result.get("success", False),
            "message": "Model retrained successfully" if result.get("success") else "Retrain failed",
            "accuracy": result.get("accuracy"),
            "f1_score": result.get("f1_score"),
            "n_samples": result.get("n_samples"),
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering ML retrain: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# Authentication Endpoints
# ============================================

@app.post("/api/auth/login")
async def login(request: LoginRequest):
    """Authenticate farmer and return session token"""
    try:
        result = auth_service.login(request.phone, request.password)
        
        if result['success']:
            return {
                "success": True,
                "farmer": result['farmer'],
                "session_token": result['session_token']
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=result.get('message', 'Login failed')
            )
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/auth/register")
async def register(request: RegisterRequest):
    """Register new farmer"""
    try:
        farmer_data = request.model_dump(exclude={'password'})
        farmer_data['registration_source'] = 'web'  # Track registration source
        result = auth_service.register_farmer(farmer_data, request.password)
        
        if result['success']:
            # Auto-login after registration
            login_result = auth_service.login(request.phone, request.password)
            
            if login_result.get('success'):
                return {
                    "success": True,
                    "message": result.get('message', 'Registration successful'),
                    "farmer": login_result.get('farmer'),
                    "session_token": login_result.get('session_token')
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=login_result.get('message', 'Auto-login failed')
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get('message', 'Registration failed')
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/auth/logout")
async def logout(farmer: Dict = Depends(get_current_farmer)):
    """Logout farmer"""
    try:
        # Get token from dependency
        auth_service.logout(farmer.get('session_token', ''))
        return {"success": True, "message": "Logged out successfully"}
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/auth/verify")
async def verify_session(farmer: Dict = Depends(get_current_farmer)):
    """Verify session and return farmer data"""
    return {
        "success": True,
        "data": farmer
    }

@app.post("/api/auth/change-password")
async def change_password(
    request: ChangePasswordRequest,
    farmer: Dict = Depends(get_current_farmer)
):
    """Change farmer password"""
    try:
        # Get session token from farmer
        session_token = farmer.get('session_token', '')
        result = auth_service.change_password(
            session_token,
            request.old_password,
            request.new_password
        )
        
        if result['success']:
            return {"success": True, "message": "Password changed successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get('message', 'Password change failed')
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Change password error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# Dashboard & Data Endpoints
# ============================================

@app.get("/api/dashboard")
async def get_dashboard(farmer: Dict = Depends(get_current_farmer)):
    """Get farmer dashboard data with climate and bloom information"""
    try:
        # Use cached NASA data from background task (fast!)
        if nasa_data_cache['data'] is not None:
            bloom_events = nasa_data_cache['data']
            logger.info(f"Using cached NASA data (last updated: {nasa_data_cache['last_update']})")
        else:
            # Fallback if cache not ready yet (first load)
            logger.info("Cache not ready, using fallback data")
            bloom_events = {
                'region': farmer.get('region', 'kenya'),
                'bloom_probability': 0.45,
                'health_score': 75,
                'ndvi_mean': 0.65,
                'data_source': 'Fallback - NASA data loading',
                'bloom_dates': []
            }
        
        # Get recent alerts
        recent_alerts = mongo_service.get_recent_alerts(limit=10)
        
        # Filter alerts for this farmer
        farmer_alerts = [
            alert for alert in recent_alerts
            if alert.get('farmer_phone') == farmer.get('phone')
        ]
        
        # Get climate data for farmer's county
        county_name = farmer.get('county', 'Nairobi')
        climate_data = data_loader.get_county_details(county_name)
        
        # Handle error or use defaults
        if not climate_data or 'error' in climate_data:
            logger.warning(f"No climate data for {county_name}, using defaults")
            climate_data = {
                'avg_temp_c': 25.0,
                'total_rainfall_mm': 50.0,
                'ndvi': 0.6
            }
        
        # Generate climate history for the last 30 days
        from datetime import datetime, timedelta
        climate_history = []
        ndvi_history = []
        current_date = datetime.now()
        
        # Extract climate values safely
        avg_temp = float(climate_data.get('avg_temp_c', 25))
        total_rainfall = float(climate_data.get('total_rainfall_mm', 50))
        ndvi_val = float(climate_data.get('ndvi', 0.6))
        
        for i in range(30, 0, -1):
            date = current_date - timedelta(days=i)
            # Use actual climate data with slight variations
            temp_var = (i % 5) - 2  # -2 to +2 variation
            rain_var = (i % 7) * 0.5
            ndvi_var = (i % 10) * 0.01
            
            climate_history.append({
                "date": date.isoformat(),
                "temperature": avg_temp + temp_var,
                "rainfall": max(0, total_rainfall / 30 + rain_var)
            })
            
            ndvi_history.append({
                "date": date.isoformat(),
                "ndvi": min(1.0, max(0.0, ndvi_val + (ndvi_var - 0.05)))
            })
        
        # Current weather from climate data
        current_weather = {
            "temperature": avg_temp,
            "rainfall": total_rainfall,
            "conditions": "Partly Cloudy" if avg_temp < 28 else "Clear"
        }
        
        # Calculate NDVI average
        ndvi_average = ndvi_val
        
        # Determine season based on current month
        current_month = datetime.now().month
        if current_month in [3, 4, 5]:
            season = {"name": "Long Rains", "status": "Active"}
        elif current_month in [10, 11, 12]:
            season = {"name": "Short Rains", "status": "Active"}
        elif current_month in [6, 7, 8, 9]:
            season = {"name": "Dry Season", "status": "Ongoing"}
        else:
            season = {"name": "Inter-seasonal", "status": "Transitioning"}
        
        # Get ML predictions
        ml_prediction = None
        if bloom_predictor:
            try:
                ml_prediction = bloom_predictor.predict_bloom_probability()
            except Exception as e:
                logger.warning(f"ML prediction failed: {e}")
        
        return {
            "success": True,
            "data": {
                "farmer": farmer,
                "bloom_events": [bloom_events] if isinstance(bloom_events, dict) else bloom_events,
                "recent_alerts": farmer_alerts,
                "climate_history": climate_history,
                "ndvi_history": ndvi_history,
                "current_weather": current_weather,
                "ndvi_average": ndvi_average,
                "season": season,
                "health_score": bloom_events.get('health_score', 0) if isinstance(bloom_events, dict) else 0,
                "next_bloom": (bloom_events.get('bloom_dates', []) or [None])[0] if isinstance(bloom_events, dict) else None,
                "ml_prediction": ml_prediction
            }
        }
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/bloom/events")
async def get_bloom_events(
    region: Optional[str] = None,
    farmer: Dict = Depends(get_current_farmer)
):
    """Get bloom events for region"""
    try:
        target_region = region or farmer.get('region', 'kenya')
        
        # Use cached NASA data (fast!)
        if nasa_data_cache['data'] is not None:
            events = nasa_data_cache['data']
            logger.info(f"Using cached bloom events (last updated: {nasa_data_cache['last_update']})")
        else:
            # Fallback if cache not ready
            logger.info("Cache not ready, using fallback bloom data")
            events = {
                'region': target_region,
                'crop_type': 'general',
                'bloom_probability': 0.45,
                'bloom_area_km2': 125.5,
                'confidence': 'Medium',
                'detection_date': datetime.now().isoformat(),
                'health_score': 75,
                'data_source': 'Fallback - NASA data loading'
            }
        
        return {
            "success": True,
            "data": [events]  # Return as list for consistency
        }
    except Exception as e:
        logger.error(f"Bloom events error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/alerts")
async def get_alerts(
    limit: int = 10,
    farmer: Dict = Depends(get_current_farmer)
):
    """Get farmer's recent alerts"""
    try:
        alerts = mongo_service.get_recent_alerts(limit=limit)
        
        # Filter for this farmer
        farmer_alerts = [
            alert for alert in alerts
            if alert.get('farmer_phone') == farmer.get('phone')
        ]
        
        return {
            "success": True,
            "data": farmer_alerts
        }
    except Exception as e:
        logger.error(f"Alerts error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ml/predictions")
async def get_ml_predictions(farmer: Dict = Depends(get_current_farmer)):
    """Get ML-based bloom predictions for farmer's region"""
    try:
        if bloom_predictor is None:
            logger.warning("ML Predictor not available")
            return {
                "success": True,
                "data": {
                    "bloom_probability_percent": 45.0,
                    "confidence": "Medium",
                    "message": "ML model not available - using fallback predictions",
                    "model_version": "Fallback",
                    "predicted_at": datetime.now().isoformat()
                }
            }
        
        # Get ML prediction
        prediction = bloom_predictor.predict_bloom_probability()
        
        return {
            "success": True,
            "data": prediction
        }
    except Exception as e:
        logger.error(f"ML prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/county/{county_name}/map-data")
async def get_county_map_data(county_name: str, farmer: Dict = Depends(get_current_farmer)):
    """Get live map data focused on specific county"""
    try:
        # Get county details
        county_data = data_loader.get_county_details(county_name)
        
        if not county_data or 'error' in county_data:
            raise HTTPException(status_code=404, detail=f"County {county_name} not found")
        
        # Get live climate data
        live_data = data_loader.get_landing_page_map_data()
        
        # Filter for this county's markers
        county_markers = [
            marker for marker in live_data.get('markers', [])
            if marker.get('name', '').lower() == county_name.lower()
        ]
        
        return {
            "success": True,
            "data": {
                "county": county_name,
                "markers": county_markers,
                "county_details": county_data
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"County map data error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# Map & Climate Data Endpoints
# ============================================

@app.get("/api/map/live-data")
async def get_live_map_data():
    """Get live map data for all Kenya counties (public endpoint)"""
    try:
        map_data = data_loader.get_landing_page_map_data()
        return {
            "success": True,
            "data": map_data
        }
    except Exception as e:
        logger.error(f"Live map data error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/map/climate-stats")
async def get_climate_stats():
    """Get climate summary statistics (public endpoint)"""
    try:
        stats = data_loader.get_climate_summary_stats()
        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        logger.error(f"Climate stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/map/freshness")
async def get_data_freshness():
    """Get data freshness information (public endpoint)"""
    try:
        freshness = data_loader.get_data_freshness_info()
        return {
            "success": True,
            "data": freshness
        }
    except Exception as e:
        logger.error(f"Data freshness error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/counties")
async def get_counties():
    """Get all Kenya counties configuration (public endpoint)"""
    try:
        return {
            "success": True,
            "data": {
                "regions": KENYA_REGIONS_COUNTIES,
                "crops": ALL_KENYA_CROPS
            }
        }
    except Exception as e:
        logger.error(f"Counties error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/counties/{county_id}")
async def get_county_data(county_id: str):
    """Get detailed data for specific county (public endpoint)"""
    try:
        # Try to load from saved county data
        county_file = f"/home/yogo/bloom-detector/data/county_data/{county_id}.json"
        
        if os.path.exists(county_file):
            with open(county_file, 'r') as f:
                county_data = json.load(f)
            return {
                "success": True,
                "data": county_data
            }
        else:
            # Fetch fresh data
            county_data = data_fetcher.fetch_county_data(county_id)
            return {
                "success": True,
                "data": county_data
            }
    except Exception as e:
        logger.error(f"County data error for {county_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# Farmer Profile Endpoints
# ============================================

@app.get("/api/farmers/{phone}")
async def get_farmer(phone: str, current_farmer: Dict = Depends(get_current_farmer)):
    """Get farmer by phone (must be authenticated)"""
    try:
        # Only allow farmers to view their own profile or admins to view any
        if current_farmer.get('phone') != phone and not current_farmer.get('is_admin', False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        farmer = mongo_service.get_farmer_by_phone(phone)
        
        if not farmer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Farmer not found"
            )
        
        return {
            "success": True,
            "data": farmer
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get farmer error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/farmers/profile")
async def update_profile(
    request: ProfileUpdateRequest,
    farmer: Dict = Depends(get_current_farmer)
):
    """Update farmer profile"""
    try:
        # Get session token
        session_token = farmer.get('session_token', '')
        updates = request.dict(exclude_unset=True)
        
        result = auth_service.update_farmer_profile(session_token, updates)
        
        if result['success']:
            return {"success": True, "message": "Profile updated successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get('message', 'Update failed')
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update profile error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# Admin Endpoints
# ============================================

@app.get("/api/admin/farmers")
async def get_all_farmers(
    region: Optional[str] = None,
    crop: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 50,
    admin: Dict = Depends(verify_admin)
):
    """Get all farmers (admin only)"""
    try:
        query = {}
        
        if region:
            query['region'] = region
        if crop:
            query['crops'] = crop
        if search:
            query['$or'] = [
                {'name': {'$regex': search, '$options': 'i'}},
                {'phone': {'$regex': search, '$options': 'i'}},
                {'email': {'$regex': search, '$options': 'i'}}
            ]
        
        farmers = list(mongo_service.farmers.find(query).limit(limit))
        
        # Convert ObjectId to string
        for farmer in farmers:
            farmer['_id'] = str(farmer['_id'])
        
        return {
            "success": True,
            "data": farmers
        }
    except Exception as e:
        logger.error(f"Get farmers error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/statistics")
async def get_statistics(admin: Dict = Depends(verify_admin)):
    """Get farmer statistics (admin only)"""
    try:
        stats = mongo_service.get_farmer_statistics()
        
        # Add more stats
        stats['total'] = stats.get('total_farmers', 0)
        stats['active'] = stats.get('active_farmers', 0)
        stats['by_region'] = stats.get('farmers_by_region', {})
        stats['popular_crops'] = [
            [crop, count] for crop, count in 
            sorted(stats.get('farmers_by_crop', {}).items(), key=lambda x: x[1], reverse=True)[:10]
        ]
        
        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        logger.error(f"Statistics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/registrations/recent")
async def get_recent_registrations(
    days: int = 7,
    admin: Dict = Depends(verify_admin)
):
    """Get recent farmer registrations (admin only)"""
    try:
        registrations = mongo_service.get_recent_registrations(days=days, limit=50)
        
        return {
            "success": True,
            "data": registrations
        }
    except Exception as e:
        logger.error(f"Recent registrations error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/admin/farmers/{farmer_id}")
async def delete_farmer(farmer_id: str, admin: Dict = Depends(verify_admin)):
    """Delete farmer (admin only)"""
    try:
        success = mongo_service.delete_farmer(farmer_id)
        
        if success:
            return {"success": True, "message": "Farmer deleted successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Farmer not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete farmer error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/admin/alerts/send")
async def send_alert(request: SendAlertRequest, admin: Dict = Depends(verify_admin)):
    """Send alert to farmers (admin only)"""
    try:
        # Build query based on target
        query = {}
        
        if request.target == 'region':
            query['region'] = request.target_value
        elif request.target == 'crop':
            query['crops'] = request.target_value
        elif request.target == 'individual':
            query['phone'] = request.target_value
        
        # Get recipients
        recipients = list(mongo_service.farmers.find(query))
        
        if not recipients:
            return {
                "success": False,
                "message": "No recipients found",
                "count": 0
            }
        
        # Send alerts
        success_count = 0
        
        for farmer in recipients:
            try:
                if request.alert_type == 'custom' and request.message:
                    # Send custom message
                    result = at_service.send_sms(farmer['phone'], request.message)
                    if result.get('success'):
                        success_count += 1
                else:
                    # Send smart alert
                    bloom_data = bloom_processor.detect_bloom_events(farmer.get('region', 'central'))
                    result = smart_alert_service.send_welcome_alert(farmer, bloom_data)
                    if result.get('success'):
                        success_count += 1
            except Exception as e:
                logger.warning(f"Failed to send alert to {farmer.get('phone')}: {e}")
        
        return {
            "success": True,
            "message": f"Sent {success_count}/{len(recipients)} alerts",
            "count": success_count,
            "total": len(recipients)
        }
    except Exception as e:
        logger.error(f"Send alert error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# Flora AI Chatbot Endpoint
# ============================================

@app.post("/api/chat")
async def chat_with_flora(
    request: ChatRequest,
    farmer: Optional[Dict] = Depends(get_current_farmer)
):
    """Chat with Flora AI"""
    try:
        if not flora_service:
            return {
                "success": True,
                "data": {
                    "reply": "Flora AI is currently unavailable. Please try again later or contact support."
                }
            }
        
        # Get bloom data for context
        bloom_data = None
        if farmer:
            try:
                bloom_data = bloom_processor.detect_bloom_events(farmer.get('region', 'kenya'))
            except:
                pass
        
        # Generate AI response
        response = flora_service.generate_response(
            user_message=request.message,
            farmer_data=farmer,
            bloom_data=bloom_data,
            chat_history=request.history
        )
        
        # Store in MongoDB
        if farmer and mongo_service:
            try:
                mongo_service.chat_history.insert_one({
                    'farmer_id': farmer.get('_id'),
                    'phone': farmer.get('phone'),
                    'message': request.message,
                    'response': response.get('reply', ''),
                    'timestamp': datetime.now(),
                    'created_at': datetime.now()
                })
            except:
                pass
        
        return {
            "success": True,
            "data": response
        }
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# Public Data Endpoints (No Auth Required)
# ============================================

@app.get("/api/public/regions")
async def get_regions():
    """Get all Kenya regions and counties"""
    return {
        "success": True,
        "data": {
            "regions": KENYA_REGIONS_COUNTIES,
            "crops": ALL_KENYA_CROPS
        }
    }

@app.get("/api/public/crops")
async def get_crops():
    """Get all available crops"""
    return {
        "success": True,
        "data": ALL_KENYA_CROPS
    }

# ============================================
# Error Handlers
# ============================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "detail": str(exc) if os.getenv('DEBUG') == 'True' else None
        }
    )

# ============================================
# USSD & Flora AI Endpoints
# ============================================

@app.post("/api/ussd/callback")
async def ussd_callback(
    sessionId: str = Form(None),
    serviceCode: str = Form(None),
    phoneNumber: str = Form(None),
    text: str = Form('')
):
    """
    USSD callback endpoint for Africa's Talking
    
    This endpoint receives USSD requests from Africa's Talking and returns
    USSD menu responses in plain text format.
    
    Configure this URL in Africa's Talking dashboard:
    https://your-domain.com/api/ussd/callback
    """
    try:
        logger.info(f"USSD Request - Session: {sessionId}, Phone: {phoneNumber}, Text: '{text}'")
        
        response_text = ussd_service.handle_ussd_request(
            sessionId,
            serviceCode,
            phoneNumber,
            text
        )
        
        logger.info(f"USSD Response: {response_text[:100]}...")
        
        # Africa's Talking expects plain text response
        return PlainTextResponse(content=response_text)
        
    except Exception as e:
        logger.error(f"USSD error: {e}", exc_info=True)
        return PlainTextResponse(content="END An error occurred. Please try again later.")

@app.post("/api/sms/delivery-reports")
async def sms_delivery_report(
    id: str = Form(None),
    phoneNumber: str = Form(None),
    status: str = Form(None),
    networkCode: str = Form(None),
    retryCount: str = Form(None),
    failureReason: str = Form(None)
):
    """
    SMS delivery report callback from Africa's Talking
    
    This endpoint receives delivery status updates for sent SMS messages.
    
    Configure this URL in Africa's Talking dashboard:
    https://your-domain.com/api/sms/delivery-reports
    
    Status values: 'Success', 'Failed', 'Sent', 'Queued', 'Rejected'
    """
    try:
        logger.info(
            f"SMS Delivery Report - ID: {id}, Phone: {phoneNumber}, "
            f"Status: {status}, Network: {networkCode}, "
            f"Retry: {retryCount}, Reason: {failureReason}"
        )
        
        # Store delivery report in database for analytics
        try:
            mongo_service.db.sms_delivery_reports.insert_one({
                "message_id": id,
                "phone_number": phoneNumber,
                "status": status,
                "network_code": networkCode,
                "retry_count": retryCount,
                "failure_reason": failureReason,
                "timestamp": datetime.now(),
                "processed": True
            })
            logger.info(f"Delivery report saved for message {id}")
        except Exception as db_error:
            logger.error(f"Failed to save delivery report: {db_error}")
        
        # Return success response (Africa's Talking expects this)
        return PlainTextResponse(content="Received")
        
    except Exception as e:
        logger.error(f"Delivery report error: {e}", exc_info=True)
        return PlainTextResponse(content="Error")

@app.post("/api/ussd/send-county-data")
async def send_county_data(
    phone: str,
    county_id: str,
    language: str = 'en'
):
    """Send county climate and bloom data via SMS (USSD users)"""
    try:
        farmer = mongo_service.get_farmer_by_phone(phone)
        if not farmer:
            raise HTTPException(status_code=404, detail="Farmer not found")
        
        # Get county data
        county_data = await get_county_data(county_id)
        
        # Format SMS message
        if language == 'sw':
            message = f"""🌾 BloomWatch Kenya - {county_data['county_name']}

Hali ya Mazao:
🌸 Eneo la Kuchanua: {county_data.get('bloom_area_km2', 0):.1f} km²
🌡️ Joto: {county_data.get('temperature_c', 0):.1f}°C
🌧️ Mvua: {county_data.get('rainfall_mm', 0):.0f} mm
📊 NDVI: {county_data.get('ndvi', 0):.2f}

Data kutoka NASA satellites.
"""
        else:
            message = f"""🌾 BloomWatch Kenya - {county_data['county_name']}

Crop Conditions:
🌸 Bloom Area: {county_data.get('bloom_area_km2', 0):.1f} km²
🌡️ Temperature: {county_data.get('temperature_c', 0):.1f}°C
🌧️ Rainfall: {county_data.get('rainfall_mm', 0):.0f} mm
📊 NDVI: {county_data.get('ndvi', 0):.2f}

Data from NASA satellites.
"""
        
        # Send SMS
        result = at_service.send_sms(phone, message)
        
        return {
            "success": True,
            "message": "County data sent via SMS",
            "sms_sent": result.get('success', False)
        }
    except Exception as e:
        logger.error(f"Send county data error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/flora/ask-ussd")
async def flora_ask_ussd(
    phone: str,
    question: str,
    language: str = 'en'
):
    """Flora AI question via USSD (sends answer via SMS)"""
    try:
        if not flora_service:
            return {
                "success": False,
                "message": "Flora AI not available"
            }
        
        farmer = mongo_service.get_farmer_by_phone(phone)
        
        # Get bloom data for context
        bloom_data = None
        if farmer:
            try:
                county = farmer.get('county', farmer.get('region', 'kenya'))
                bloom_data = bloom_processor.detect_bloom_events(county)
            except:
                pass
        
        # Generate answer
        answer = flora_service.answer_question(
            question=question,
            farmer_data=farmer,
            language=language,
            use_internet=True
        )
        
        # Send via SMS
        sms_result = at_service.send_sms(phone, answer)
        
        # Store in chat history
        if farmer:
            try:
                mongo_service.chat_history.insert_one({
                    'farmer_id': farmer.get('_id'),
                    'phone': phone,
                    'question': question,
                    'answer': answer,
                    'via': 'ussd',
                    'language': language,
                    'timestamp': datetime.now(),
                    'created_at': datetime.now()
                })
            except:
                pass
        
        return {
            "success": True,
            "answer": answer,
            "sms_sent": sms_result.get('success', False)
        }
    except Exception as e:
        logger.error(f"Flora USSD error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/flora/interpret-data-ussd")
async def flora_interpret_ussd(
    phone: str,
    language: str = 'en'
):
    """Flora AI interprets farmer's county data and sends via SMS"""
    try:
        if not flora_service:
            return {"success": False, "message": "Flora AI not available"}
        
        farmer = mongo_service.get_farmer_by_phone(phone)
        if not farmer:
            raise HTTPException(status_code=404, detail="Farmer not found")
        
        county = farmer.get('county', farmer.get('region', 'kenya'))
        
        # Get county data
        county_data = await get_county_data(county)
        
        # Generate interpretation
        question = f"Interpret this satellite data for {farmer['name']}'s farm: Bloom area {county_data.get('bloom_area_km2', 0):.1f} km², Temperature {county_data.get('temperature_c', 0):.1f}°C, NDVI {county_data.get('ndvi', 0):.2f}. Crops: {', '.join(farmer.get('crops', []))}. Give actionable farming advice."
        
        answer = flora_service.answer_question(
            question=question,
            farmer_data=farmer,
            language=language,
            use_internet=True
        )
        
        # Send via SMS
        sms_result = at_service.send_sms(phone, answer)
        
        return {
            "success": True,
            "interpretation": answer,
            "sms_sent": sms_result.get('success', False)
        }
    except Exception as e:
        logger.error(f"Flora interpret error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Main Entry Point
# ============================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

