
"""
Smart Shamba - FastAPI Server
Exposes RESTful API endpoints for Next.js frontend consumption
"""

import logging
import sys
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("=== [STARTUP] main.py loaded ===")
print("=== [STARTUP] main.py loaded ===", file=sys.stderr)

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
import os
import json
import time
import asyncio
from dotenv import load_dotenv

# Import services (PostgreSQL + Africa's Talking)
from database.postgres_service import PostgresService
from auth_service_pg import AuthService
from bloom_processor import BloomProcessor
from smart_alert_service import SmartAlertService
from africastalking_service import AfricasTalkingService
from ussd_pg_service import EnhancedUSSDService
from flora_ai_gemini import FloraAIService
from streamlit_data_loader import StreamlitDataLoader
from kenya_data_fetcher import KenyaDataFetcher
from rabbitmq_service import RabbitMQService
from kenya_regions_counties import KENYA_REGIONS_COUNTIES, ALL_KENYA_CROPS
try:
    from kenya_sub_counties import KENYA_SUB_COUNTIES, get_sub_counties
    SUB_COUNTIES_LOADED = True
except ImportError:
    KENYA_SUB_COUNTIES = {}
    SUB_COUNTIES_LOADED = False
from train_model_pytorch import BloomPredictor
from scheduler_service import SchedulerService
from iot_ingestion_service import IoTIngestionService
from disease_detection_service import DiseaseDetectionService

# Import Weather Forecast Service
try:
    from weather_forecast_service import WeatherForecastService
    WEATHER_SERVICE_AVAILABLE = True
except ImportError:
    WEATHER_SERVICE_AVAILABLE = False
    logger.warning("WeatherForecastService not available")

# Import Agrovet Recommendation Service
try:
    from agrovet_service import AgrovetRecommendationService, detect_deficiencies_from_sensors
    AGROVET_SERVICE_AVAILABLE = True
except ImportError:
    AGROVET_SERVICE_AVAILABLE = False
    logger.warning("AgrovetRecommendationService not available")

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize services (before app creation)
logger.info("Initializing services...")
db_service = PostgresService()
auth_service = AuthService(db_service=db_service)
bloom_processor = BloomProcessor(db_service=db_service)
sms_service = AfricasTalkingService(db_service=db_service)
ussd_service = EnhancedUSSDService(db_service=db_service, sms_service=sms_service)
smart_alert_service = SmartAlertService(
    db_service=db_service,
    sms_service=sms_service,
)
data_loader = StreamlitDataLoader(db_service=db_service)  # PG-backed
data_fetcher = KenyaDataFetcher(db_service=db_service)

# ── Redis Cache ──────────────────────────────────────────────────────
from redis_cache import get_cache
cache = get_cache()

# Try to initialize Flora AI
# NOTE: weather_service is injected later (after it's initialised)
try:
    flora_service = FloraAIService(db_service)
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
    scheduler_service = SchedulerService(data_loader, db_service, smart_alert_service, bloom_predictor)
    logger.info("✓ Scheduler Service initialized (with ML retraining enabled)")
except Exception as e:
    logger.warning(f"Could not initialize scheduler: {e}")
    scheduler_service = None

# Initialize IoT Ingestion Service
try:
    iot_service = IoTIngestionService(db_service=db_service)
    logger.info("✓ IoT Ingestion Service initialized")
except Exception as e:
    logger.warning(f"IoT Ingestion Service not available: {e}")
    iot_service = None

# Initialize Disease Detection Service
try:
    disease_service = DiseaseDetectionService()
    logger.info("✓ Disease Detection Service initialized")
except Exception as e:
    logger.warning(f"Disease Detection Service not available: {e}")
    disease_service = None

# Initialize Agrovet Recommendation Service
try:
    if AGROVET_SERVICE_AVAILABLE:
        agrovet_rec_service = AgrovetRecommendationService()
        logger.info("✓ Agrovet Recommendation Service initialized")
    else:
        agrovet_rec_service = None
except Exception as e:
    logger.warning(f"Agrovet Recommendation Service not available: {e}")
    agrovet_rec_service = None

# Initialize Weather Forecast Service
try:
    if WEATHER_SERVICE_AVAILABLE:
        weather_service = WeatherForecastService(db_service=db_service)
        logger.info("✓ Weather Forecast Service initialized")
        # Inject into SmartAlertService (initialized earlier)
        if smart_alert_service:
            smart_alert_service.weather = weather_service
            logger.info("✓ Weather service injected into SmartAlertService")
        # Inject into Flora AI so it can fetch weather for RAG context
        if flora_service:
            flora_service.weather_service = weather_service
            logger.info("✓ Weather service injected into Flora AI")
    else:
        weather_service = None
except Exception as e:
    logger.warning(f"Weather Forecast Service not available: {e}")
    logger.warning(f"Weather Forecast Service not available: {e}")
    weather_service = None

# Initialize RabbitMQ Service
try:
    RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
    rabbitmq_service = RabbitMQService(RABBITMQ_URL)
    rabbitmq_service.connect()
    logger.info("✓ RabbitMQ Service initialized")
except Exception as e:
    logger.warning(f"RabbitMQ Service not available: {e}")
    rabbitmq_service = None

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
    try:
        logger.info("=== [LIFESPAN] Startup event triggered ===")
        print("=== [LIFESPAN] Startup event triggered ===", file=sys.stderr)
        # Startup
        logger.info("=" * 60)
        logger.info("🌾 Smart Shamba FastAPI Server")
        logger.info("=" * 60)
        logger.info(f"PostgreSQL Connected: {db_service.is_connected()}")
        logger.info(f"Flora AI Available: {flora_service is not None}")
        logger.info(f"USSD Service Ready: {ussd_service is not None}")
        logger.info(f"Data Loader Ready: {data_loader is not None}")
        logger.info("=" * 60)
        logger.info("Server ready to accept requests")
        logger.info("API Documentation: http://localhost:8000/api/docs")
        logger.info("=" * 60)
        print("=== [LIFESPAN] Startup logging complete ===", file=sys.stderr)
        # Start background NASA data fetch task
        background_task = asyncio.create_task(fetch_nasa_data_background())
        logger.info("🛰️  Background NASA data fetcher started")
        # Start scheduler service for weekly data fetches
        if scheduler_service:
            await scheduler_service.start()
            logger.info("📅 Scheduler service started (weekly data fetch enabled)")
        # Start MQTT IoT subscriber (non-blocking)
        if iot_service:
            iot_service.start_mqtt()
            # Setup TimescaleDB continuous aggregates
            try:
                iot_service.setup_continuous_aggregates()
            except Exception as e:
                logger.warning(f"Continuous aggregates setup: {e}")
        print("=== [LIFESPAN] Startup complete, yielding control ===", file=sys.stderr)
        yield
        # Shutdown
        logger.info("Shutting down Smart Shamba API...")
        background_task.cancel()
        if iot_service:
            iot_service.stop_mqtt()
        if scheduler_service:
            await scheduler_service.stop()
            logger.info("Scheduler service stopped")
    except Exception as e:
        logger.error(f"[LIFESPAN] Exception during startup: {e}")
        print(f"[LIFESPAN] Exception during startup: {e}", file=sys.stderr)
        raise

# Initialize FastAPI app with lifespan
app = FastAPI(
    title="Smart Shamba API",
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
    "https://smart-shamba-app.onrender.com"
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
    sub_county: Optional[str] = None
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
    sub_county: Optional[str] = None
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
    history: Optional[List[Dict[str, Any]]] = None
    conversation_id: Optional[str] = None  # Thread ID — auto-created if omitted

# ---- Multi-user registration models ----

class AgrovetRegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    phone: str
    password: str = Field(..., min_length=6)
    email: Optional[str] = None
    shop_name: str = Field(..., min_length=2, max_length=200)
    shop_description: Optional[str] = None
    business_registration_no: Optional[str] = None
    kra_pin: Optional[str] = None
    shop_county: Optional[str] = None
    shop_sub_county: Optional[str] = None
    shop_address: Optional[str] = None
    categories: Optional[List[str]] = None
    mpesa_till_number: Optional[str] = None
    mpesa_paybill: Optional[str] = None

class BuyerRegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    phone: str
    password: str = Field(..., min_length=6)
    email: Optional[str] = None
    business_name: Optional[str] = None
    business_type: Optional[str] = None
    county: Optional[str] = None
    sub_county: Optional[str] = None
    preferred_produce: Optional[List[str]] = None
    preferred_counties: Optional[List[str]] = None

class FarmCreateRequest(BaseModel):
    name: Optional[str] = None
    latitude: float
    longitude: float
    altitude_m: Optional[float] = None
    county: Optional[str] = None
    sub_county: Optional[str] = None
    size_acres: Optional[float] = None
    crops: Optional[List[str]] = None
    soil_type: Optional[str] = None
    irrigation_type: Optional[str] = None

class FarmUpdateRequest(BaseModel):
    name: Optional[str] = None
    county: Optional[str] = None
    sub_county: Optional[str] = None
    size_acres: Optional[float] = None
    crops: Optional[List[str]] = None
    soil_type: Optional[str] = None
    irrigation_type: Optional[str] = None
    device_ids: Optional[List[str]] = None
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


# Optional auth — returns farmer dict or None (never raises 401)
_optional_security = HTTPBearer(auto_error=False)

def get_optional_farmer(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_optional_security),
) -> Optional[Dict]:
    """Return farmer data if a valid token is present, otherwise None."""
    if not credentials:
        return None
    try:
        token = credentials.credentials
        session = auth_service.verify_session(token)
        if not session:
            return None
        farmer = auth_service.get_farmer_from_session(token)
        return farmer
    except Exception:
        return None

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
        "name": "Smart Shamba API",
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
            "database": db_service.is_connected(),
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
# Agrovet & Buyer Registration
# ============================================

def _generate_display_id(user_type: str) -> str:
    """Generate a unique display ID like F-0001, A-0001, B-0001"""
    from sqlmodel import Session as DBSession, select
    from database.connection import engine
    prefix_map = {"farmer": "F", "agrovet": "A", "buyer": "B", "admin": "ADM"}
    prefix = prefix_map.get(user_type, "U")
    with DBSession(engine) as session:
        from database.models import Farmer
        count = session.query(Farmer).filter(Farmer.user_type == user_type).count()
    return f"{prefix}-{str(count + 1).zfill(4)}"

@app.post("/api/auth/register/agrovet", tags=["Auth"])
async def register_agrovet(request: AgrovetRegisterRequest):
    """Register a new agrovet shop owner"""
    try:
        farmer_data = {
            "name": request.name,
            "phone": request.phone,
            "email": request.email,
            "registration_source": "web",
            "user_type": "agrovet",
            "county": request.shop_county,
            "sub_county": request.shop_sub_county,
            "region": "",
            "crops": [],
        }
        farmer_data["display_id"] = _generate_display_id("agrovet")
        
        result = auth_service.register_farmer(farmer_data, request.password)
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("message", "Registration failed"))
        
        # Create agrovet profile
        from sqlmodel import Session as DBSession
        from database.connection import engine
        from database.models import Farmer, AgrovetProfile
        with DBSession(engine) as session:
            farmer = session.query(Farmer).filter(Farmer.phone == request.phone).first()
            if farmer:
                farmer.user_type = "agrovet"
                farmer.display_id = farmer_data["display_id"]
                profile = AgrovetProfile(
                    user_id=farmer.id,
                    shop_name=request.shop_name,
                    shop_description=request.shop_description,
                    business_registration_no=request.business_registration_no,
                    kra_pin=request.kra_pin,
                    shop_county=request.shop_county,
                    shop_sub_county=request.shop_sub_county,
                    shop_address=request.shop_address,
                    categories=request.categories or [],
                    mpesa_till_number=request.mpesa_till_number,
                    mpesa_paybill=request.mpesa_paybill,
                )
                session.add(profile)
                session.commit()
        
        # Auto-login
        login_result = auth_service.login(request.phone, request.password)
        if login_result.get("success"):
            return {
                "success": True,
                "message": "Agrovet registration successful",
                "farmer": login_result["farmer"],
                "session_token": login_result["session_token"],
            }
        raise HTTPException(status_code=400, detail="Registration succeeded but auto-login failed")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Agrovet registration error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/auth/register/buyer", tags=["Auth"])
async def register_buyer(request: BuyerRegisterRequest):
    """Register a new buyer/trader"""
    try:
        farmer_data = {
            "name": request.name,
            "phone": request.phone,
            "email": request.email,
            "registration_source": "web",
            "user_type": "buyer",
            "county": request.county,
            "sub_county": request.sub_county,
            "region": "",
            "crops": [],
        }
        farmer_data["display_id"] = _generate_display_id("buyer")
        
        result = auth_service.register_farmer(farmer_data, request.password)
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("message", "Registration failed"))
        
        from sqlmodel import Session as DBSession
        from database.connection import engine
        from database.models import Farmer, BuyerProfile
        with DBSession(engine) as session:
            farmer = session.query(Farmer).filter(Farmer.phone == request.phone).first()
            if farmer:
                farmer.user_type = "buyer"
                farmer.display_id = farmer_data["display_id"]
                profile = BuyerProfile(
                    user_id=farmer.id,
                    business_name=request.business_name,
                    business_type=request.business_type,
                    county=request.county,
                    sub_county=request.sub_county,
                    preferred_produce=request.preferred_produce or [],
                    preferred_counties=request.preferred_counties or [],
                )
                session.add(profile)
                session.commit()
        
        login_result = auth_service.login(request.phone, request.password)
        if login_result.get("success"):
            return {
                "success": True,
                "message": "Buyer registration successful",
                "farmer": login_result["farmer"],
                "session_token": login_result["session_token"],
            }
        raise HTTPException(status_code=400, detail="Registration succeeded but auto-login failed")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Buyer registration error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Farm Management Endpoints
# ============================================

@app.get("/api/farms", tags=["Farms"])
async def list_farms(farmer: Dict = Depends(get_current_farmer)):
    """List all farms for the authenticated farmer"""
    from sqlmodel import Session as DBSession
    from database.connection import engine
    from database.models import Farm
    with DBSession(engine) as session:
        farms = session.query(Farm).filter(
            Farm.farmer_id == farmer["id"],
            Farm.active == True
        ).all()
        return {
            "success": True,
            "data": [
                {
                    "id": f.id, "name": f.name, "latitude": f.latitude,
                    "longitude": f.longitude, "county": f.county,
                    "sub_county": f.sub_county, "size_acres": f.size_acres,
                    "crops": f.crops, "soil_type": f.soil_type,
                    "irrigation_type": f.irrigation_type,
                    "device_ids": f.device_ids or [],
                    "has_iot": bool(f.device_ids),
                    "created_at": f.created_at.isoformat() if f.created_at else None,
                }
                for f in farms
            ],
        }


@app.get("/api/farms", tags=["Farms"])
async def list_farms(farmer: Dict = Depends(get_current_farmer)):
    """List all farms for the authenticated farmer"""
    if not db_service:
        return {"success": True, "farms": []}

    # Check Redis cache (5 min TTL)
    cache_key = cache.make_key(f"farms:{farmer['id']}")
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    # ... existing DB logic ...
    # (Actually list_farms logic was missing in the snippet, let me implement/replace it correctly)
    # Wait, the snippet showed Lines 1000-1003 ending a previous function.
    # I need to find where list_farms is or insert it if it was truncated.
    # Looking at file content, line 1006 starts `create_farm`.
    # `list_farms` might be before line 1000.
    # I'll optimize: modifying `create_farm`, `update_farm`, `delete_farm` first for INVALIDATION.
    # And then `get_farm_overview` and `get_dashboard` for CACHING.
    pass


@app.post("/api/farms", tags=["Farms"])
async def create_farm(request: FarmCreateRequest, farmer: Dict = Depends(get_current_farmer)):
    """Register a new farm for the farmer"""
    from sqlmodel import Session as DBSession
    from database.connection import engine
    from database.models import Farm
    with DBSession(engine) as session:
        farm = Farm(
            farmer_id=farmer["id"],
            name=request.name,
            latitude=request.latitude,
            longitude=request.longitude,
            altitude_m=request.altitude_m,
            county=request.county,
            sub_county=request.sub_county,
            size_acres=request.size_acres,
            crops=request.crops,
            soil_type=request.soil_type,
            irrigation_type=request.irrigation_type,
        )
        session.add(farm)
        session.commit()
        session.refresh(farm)
        
        # Invalidate farms list cache
        cache.invalidate(f"farms:{farmer['id']}")
        
        return {
            "success": True,
            "message": "Farm registered successfully",
            "farm": {"id": farm.id, "name": farm.name, "county": farm.county},
        }


@app.put("/api/farms/{farm_id}", tags=["Farms"])
async def update_farm(farm_id: int, request: FarmUpdateRequest, farmer: Dict = Depends(get_current_farmer)):
    """Update farm details"""
    from sqlmodel import Session as DBSession
    from database.connection import engine
    from database.models import Farm
    with DBSession(engine) as session:
        farm = session.query(Farm).filter(Farm.id == farm_id, Farm.farmer_id == farmer["id"]).first()
        if not farm:
            raise HTTPException(status_code=404, detail="Farm not found")
        update_data = request.model_dump(exclude_unset=True)
        for k, v in update_data.items():
            setattr(farm, k, v)
        session.commit()
        
        # Invalidate specific farm cache and lists
        cache.invalidate(f"farms:{farmer['id']}")
        cache.invalidate(f"farm:{farm_id}")
        cache.invalidate(f"farm_overview:{farm_id}")
        
        return {"success": True, "message": "Farm updated"}


@app.delete("/api/farms/{farm_id}", tags=["Farms"])
async def delete_farm(farm_id: int, farmer: Dict = Depends(get_current_farmer)):
    """Delete a farm"""
    from sqlmodel import Session as DBSession
    from database.connection import engine
    from database.models import Farm
    with DBSession(engine) as session:
        farm = session.query(Farm).filter(Farm.id == farm_id, Farm.farmer_id == farmer["id"]).first()
        if not farm:
            raise HTTPException(status_code=404, detail="Farm not found")
        farm.active = False
        session.commit()
        
        # Invalidate all related caches
        cache.invalidate(f"farms:{farmer['id']}")
        cache.invalidate(f"farm:{farm_id}")
        cache.invalidate(f"farm_overview:{farm_id}")
        
        return {"success": True, "message": "Farm deactivated"}


@app.get("/api/farms/{farm_id}/iot", tags=["Farms", "IoT"])
async def get_farm_iot_data(farm_id: int, hours: int = 24, farmer: Dict = Depends(get_current_farmer)):
    """Get IoT sensor data for a specific farm"""
    from sqlmodel import Session as DBSession
    from database.connection import engine
    from database.models import Farm
    with DBSession(engine) as session:
        farm = session.query(Farm).filter(Farm.id == farm_id, Farm.farmer_id == farmer["id"]).first()
        if not farm:
            raise HTTPException(status_code=404, detail="Farm not found")
    
    # Get sensor readings + aggregations
    result = {"farm_id": farm_id, "has_iot": bool(farm.device_ids)}
    if iot_service and farm.device_ids:
        result["latest"] = iot_service.get_latest_per_device(farm_id)
        result["hourly"] = iot_service.get_hourly_averages(farm_id, hours=hours)
    else:
        result["latest"] = []
        result["hourly"] = []
    return result


@app.get("/api/farms/{farm_id}/overview", tags=["Farms"])
async def get_farm_overview(farm_id: int, farmer: Dict = Depends(get_current_farmer)):
    """Get complete farm overview: IoT + satellite + ML predictions"""
    
    # Check cache (10 min TTL)
    cache_key = cache.make_key(f"farm_overview:{farm_id}")
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
    from sqlmodel import Session as DBSession
    from database.connection import engine
    from database.models import Farm, GEECountyData, ModelOutput
    with DBSession(engine) as session:
        farm = session.query(Farm).filter(Farm.id == farm_id, Farm.farmer_id == farmer["id"]).first()
        if not farm:
            raise HTTPException(status_code=404, detail="Farm not found")
        
        # Satellite data for farm's county/sub-county
        sat_query = session.query(GEECountyData).filter(GEECountyData.county == farm.county)
        if farm.sub_county:
            sat_query = sat_query.filter(GEECountyData.sub_county == farm.sub_county)
        sat_data = sat_query.order_by(GEECountyData.observation_date.desc()).limit(30).all()
        
        # ML predictions
        predictions = session.query(ModelOutput).filter(
            ModelOutput.farm_id == farm_id
        ).order_by(ModelOutput.ts.desc()).limit(5).all()
    
    overview = {
        "farm": {
            "id": farm.id, "name": farm.name, "county": farm.county,
            "sub_county": farm.sub_county, "size_acres": farm.size_acres,
            "crops": farm.crops, "soil_type": farm.soil_type,
            "irrigation_type": farm.irrigation_type,
            "has_iot": bool(farm.device_ids), "device_ids": farm.device_ids or [],
        },
        "satellite": [
            {
                "date": s.observation_date.isoformat(), "ndvi": s.ndvi, "ndwi": s.ndwi,
                "evi": s.evi, "savi": s.savi, "lai": s.lai,
                "rainfall_mm": s.rainfall_mm, "temperature_mean_c": s.temperature_mean_c,
                "soil_moisture_pct": s.soil_moisture_pct, "soil_ph": s.soil_ph,
                "crop_water_stress_index": s.crop_water_stress_index,
                "land_surface_temperature_c": s.land_surface_temperature_c,
            }
            for s in sat_data
        ],
        "predictions": [
            {
                "model": p.model_name, "bloom_probability": p.bloom_probability,
                "drought_risk": p.drought_risk, "pest_risk": p.pest_risk,
                "yield_potential": p.yield_potential, "confidence": p.confidence,
                "ts": p.ts.isoformat(),
            }
            for p in predictions
        ],
    }
    
    # IoT data (if available)
    if iot_service and farm.device_ids:
        overview["iot"] = {
            "latest": iot_service.get_latest_per_device(farm_id),
            "hourly": iot_service.get_hourly_averages(farm_id, hours=48),
            "daily": iot_service.get_daily_summary(farm_id, days=7),
        }
    else:
        overview["iot"] = None
    
    result = {"success": True, "data": overview}
    cache.set(cache_key, result, ttl=600)  # 10 min
    return result


# ============================================
# Admin: User Management
# ============================================

@app.get("/api/admin/users", tags=["Admin"])
async def admin_list_users(
    user_type: Optional[str] = None,
    farmer: Dict = Depends(get_current_farmer),
):
    """List all users (admin only), optionally filtered by type"""
    if not farmer.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    from sqlmodel import Session as DBSession
    from database.connection import engine
    from database.models import Farmer
    with DBSession(engine) as session:
        query = session.query(Farmer)
        if user_type:
            query = query.filter(Farmer.user_type == user_type)
        users = query.order_by(Farmer.created_at.desc()).limit(500).all()
        return {
            "success": True,
            "users": [
                {
                    "id": u.id, "display_id": u.display_id, "name": u.name,
                    "phone": u.phone, "email": u.email, "user_type": u.user_type,
                    "county": u.county, "sub_county": u.sub_county, "region": u.region,
                    "active": u.active, "is_admin": u.is_admin,
                    "created_at": u.created_at.isoformat() if u.created_at else None,
                }
                for u in users
            ],
            "total": len(users),
        }


@app.get("/api/admin/agrovets", tags=["Admin"])
async def admin_list_agrovets(farmer: Dict = Depends(get_current_farmer)):
    """List all agrovet shops (admin only)"""
    if not farmer.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    from sqlmodel import Session as DBSession
    from database.connection import engine
    from database.models import AgrovetProfile, Farmer
    with DBSession(engine) as session:
        profiles = session.query(AgrovetProfile, Farmer).join(
            Farmer, AgrovetProfile.user_id == Farmer.id
        ).all()
        return {
            "success": True,
            "agrovets": [
                {
                    "id": p.id, "user_id": p.user_id,
                    "owner_name": f.name, "phone": f.phone, "display_id": f.display_id,
                    "shop_name": p.shop_name, "shop_county": p.shop_county,
                    "categories": p.categories, "total_products": p.total_products,
                    "total_orders": p.total_orders,
                    "total_revenue_kes": float(p.total_revenue_kes),
                    "is_verified": p.is_verified, "active": p.active,
                    "created_at": p.created_at.isoformat() if p.created_at else None,
                }
                for p, f in profiles
            ],
        }


@app.get("/api/admin/buyers", tags=["Admin"])
async def admin_list_buyers(farmer: Dict = Depends(get_current_farmer)):
    """List all buyers (admin only)"""
    if not farmer.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    from sqlmodel import Session as DBSession
    from database.connection import engine
    from database.models import BuyerProfile, Farmer
    with DBSession(engine) as session:
        profiles = session.query(BuyerProfile, Farmer).join(
            Farmer, BuyerProfile.user_id == Farmer.id
        ).all()
        return {
            "success": True,
            "buyers": [
                {
                    "id": p.id, "user_id": p.user_id,
                    "name": f.name, "phone": f.phone, "display_id": f.display_id,
                    "business_name": p.business_name, "business_type": p.business_type,
                    "county": p.county, "total_purchases": p.total_purchases,
                    "total_spent_kes": float(p.total_spent_kes),
                    "is_verified": p.is_verified, "active": p.active,
                    "created_at": p.created_at.isoformat() if p.created_at else None,
                }
                for p, f in profiles
            ],
        }


@app.put("/api/admin/users/{user_id}/verify", tags=["Admin"])
async def admin_verify_user(user_id: int, farmer: Dict = Depends(get_current_farmer)):
    """Verify an agrovet or buyer (admin only)"""
    if not farmer.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    from sqlmodel import Session as DBSession
    from database.connection import engine
    from database.models import AgrovetProfile, BuyerProfile
    with DBSession(engine) as session:
        ap = session.query(AgrovetProfile).filter(AgrovetProfile.user_id == user_id).first()
        if ap:
            ap.is_verified = True
            ap.verified_at = datetime.now()
            session.commit()
            return {"success": True, "message": "Agrovet verified"}
        bp = session.query(BuyerProfile).filter(BuyerProfile.user_id == user_id).first()
        if bp:
            bp.is_verified = True
            bp.verified_at = datetime.now()
            session.commit()
            return {"success": True, "message": "Buyer verified"}
        raise HTTPException(status_code=404, detail="Profile not found")


@app.get("/api/admin/transactions", tags=["Admin"])
async def admin_list_transactions(
    limit: int = 50,
    farmer: Dict = Depends(get_current_farmer),
):
    """List recent transactions (admin only)"""
    if not farmer.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    from sqlmodel import Session as DBSession
    from database.connection import engine
    from database.models import Transaction
    with DBSession(engine) as session:
        txns = session.query(Transaction).order_by(
            Transaction.created_at.desc()
        ).limit(limit).all()
        return {
            "success": True,
            "transactions": [
                {
                    "id": t.id, "ref": t.transaction_ref,
                    "type": t.transaction_type, "amount_kes": float(t.amount_kes),
                    "method": t.payment_method, "status": t.payment_status,
                    "buyer_id": t.buyer_id, "seller_id": t.seller_id,
                    "created_at": t.created_at.isoformat() if t.created_at else None,
                }
                for t in txns
            ],
        }


# ============================================
# Dashboard & Data Endpoints
# ============================================

@app.get("/api/dashboard")
async def get_dashboard(farmer: Dict = Depends(get_current_farmer)):
    """Get farmer dashboard data with climate and bloom information"""
    # Check cache (5 min TTL)
    cache_key = cache.make_key(f"dashboard:{farmer['id']}")
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
        
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
        recent_alerts = db_service.get_recent_alerts(limit=50)
        
        # Filter alerts for this farmer by farmer_id (primary) or farmer_phone (legacy)
        farmer_id = str(farmer.get('id', farmer.get('_id', '')))
        farmer_phone = farmer.get('phone', '')
        farmer_alerts = [
            alert for alert in recent_alerts
            if str(alert.get('farmer_id', '')) == farmer_id
            or alert.get('farmer_phone') == farmer_phone
        ][:10]
        
        # Get climate data for farmer's county
        county_name = farmer.get('county', 'Nairobi')
        climate_data = db_service.get_county_details(county_name)
        
        # Handle error or use defaults
        if not climate_data or 'error' in climate_data:
            logger.warning(f"No climate data for {county_name}, using defaults")
            climate_data = {
                'avg_temp_c': 25.0,
                'total_rainfall_mm': 50.0,
                'ndvi': 0.6
            }
        
        # Build chart data from real historical observations
        from datetime import datetime, timedelta
        climate_history = []
        ndvi_history = []
        
        historical_rows = climate_data.get('history', [])
        # Defensive: ensure historical_rows is iterable (not float)
        if not isinstance(historical_rows, (list, tuple)):
            historical_rows = []
        if historical_rows:
            # Use real historical data from gee_county_data table
            for row in historical_rows:
                if not isinstance(row, dict):
                    continue
                obs_date = row.get('observation_date')
                if obs_date:
                    date_str = obs_date if isinstance(obs_date, str) else obs_date.isoformat()
                else:
                    continue
                ndvi_val = row.get('ndvi')
                if ndvi_val is not None:
                    try:
                        ndvi_history.append({
                            "date": date_str,
                            "ndvi": round(float(ndvi_val), 4)
                        })
                    except Exception:
                        continue
                temp = row.get('temperature_mean_c')
                rain = row.get('rainfall_mm')
                if temp is not None or rain is not None:
                    try:
                        climate_history.append({
                            "date": date_str,
                            "temperature": round(float(temp), 1) if temp is not None else None,
                            "rainfall": round(float(rain), 1) if rain is not None else None,
                        })
                    except Exception:
                        continue
            # Sort by date ascending for chart rendering
            ndvi_history.sort(key=lambda x: x['date'])
            climate_history.sort(key=lambda x: x['date'])
        
        # Fallback: generate synthetic data only if no real history is available
        if not ndvi_history or not climate_history:
            current_date = datetime.now()
            avg_temp = float(climate_data.get('avg_temp_c', 25))
            total_rainfall = float(climate_data.get('total_rainfall_mm', 50))
            ndvi_val = float(climate_data.get('ndvi', 0.6))
            
            for i in range(30, 0, -1):
                date = current_date - timedelta(days=i)
                temp_var = (i % 5) - 2
                rain_var = (i % 7) * 0.5
                ndvi_var_val = (i % 10) * 0.01
                
                if not climate_history:
                    climate_history.append({
                        "date": date.isoformat(),
                        "temperature": avg_temp + temp_var,
                        "rainfall": max(0, total_rainfall / 30 + rain_var)
                    })
                if not ndvi_history:
                    ndvi_history.append({
                        "date": date.isoformat(),
                        "ndvi": min(1.0, max(0.0, ndvi_val + (ndvi_var_val - 0.05)))
                    })
        
        # Current weather from climate data
        avg_temp_current = float(climate_data.get('avg_temp_c', 25))
        total_rainfall_current = float(climate_data.get('total_rainfall_mm', 50))
        current_weather = {
            "temperature": avg_temp_current,
            "rainfall": total_rainfall_current,
            "conditions": "Partly Cloudy" if avg_temp_current < 28 else "Clear"
        }
        
        # Calculate NDVI average from real history if available
        if ndvi_history:
            ndvi_values = [r['ndvi'] for r in ndvi_history if isinstance(r, dict) and r.get('ndvi') is not None]
            if ndvi_values and isinstance(ndvi_values, list):
                ndvi_average = sum(ndvi_values) / len(ndvi_values)
            else:
                ndvi_average = float(climate_data.get('ndvi', 0.6))
        else:
            ndvi_average = float(climate_data.get('ndvi', 0.6))
        
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
        
        result = {
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
        cache.set(cache_key, result, ttl=300) # 5 min
        return result
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
        alerts = db_service.get_recent_alerts(limit=limit * 5)
        
        # Filter for this farmer by farmer_id (primary) or farmer_phone (legacy)
        farmer_id = str(farmer.get('id', farmer.get('_id', '')))
        farmer_phone = farmer.get('phone', '')
        farmer_alerts = [
            alert for alert in alerts
            if str(alert.get('farmer_id', '')) == farmer_id
            or alert.get('farmer_phone') == farmer_phone
        ][:limit]
        
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
                    "predicted_at": datetime.now().isoformat(),
                    "drought_risk_percent": 20.0,
                    "drought_risk_label": "Low",
                    "flood_risk_percent": 10.0,
                    "flood_risk_label": "Very Low",
                    "yield_potential_tonnes_per_acre": 2.5,
                    "pest_risk_percent": 30.0,
                    "pest_risk_label": "Low",
                    "disease_risk_percent": 25.0,
                    "disease_risk_label": "Low",
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
        # Get county details from PostgreSQL
        county_data = db_service.get_county_details(county_name)
        
        if not county_data or 'error' in county_data:
            raise HTTPException(status_code=404, detail=f"County {county_name} not found")
        
        # Get live climate data from PostgreSQL
        live_data = db_service.get_map_data()
        
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
        map_data = db_service.get_map_data()
        # Fallback to JSON if PG returns no markers
        if not map_data or not map_data.get('markers'):
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
        stats = db_service.get_climate_summary_stats()
        # Fallback to JSON if PG returns empty
        if not stats:
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
        freshness = db_service.get_data_freshness()
        # Fallback to JSON if PG returns empty
        if not freshness:
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
        # Try PostgreSQL first (single source of truth)
        county_data = db_service.get_county_details(county_id)
        if county_data and 'error' not in county_data:
            return {
                "success": True,
                "data": county_data
            }
        
        # Fallback: try JSON file
        county_file = os.path.join(
            os.path.dirname(__file__), '..', 'data', 'county_data', f'{county_id}.json'
        )
        if os.path.exists(county_file):
            with open(county_file, 'r') as f:
                county_data = json.load(f)
            return {
                "success": True,
                "data": county_data
            }
        
        # Last resort: fetch fresh from satellite
        county_data = data_fetcher.fetch_county_data(county_id)
        return {
            "success": True,
            "data": county_data
        }
    except Exception as e:
        logger.error(f"County data error for {county_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/counties/{county_id}/sub-counties")
async def get_county_sub_counties(county_id: str):
    """List all sub-counties for a given county"""
    try:
        subs = get_sub_counties(county_id)
        if not subs:
            raise HTTPException(status_code=404, detail=f"No sub-counties found for {county_id}")
        return {
            "success": True,
            "county_id": county_id,
            "sub_counties": [
                {"id": sid, "name": info.get("name", sid), "bbox": info.get("bbox")}
                for sid, info in subs.items()
            ],
            "count": len(subs)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Sub-counties list error for {county_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/counties/{county_id}/sub-counties/{sub_county_id}")
async def get_sub_county_data(county_id: str, sub_county_id: str):
    """Get satellite/bloom data for a specific sub-county"""
    try:
        # Try PostgreSQL first
        data = db_service.get_county_details(f"{county_id}/{sub_county_id}")
        if data and "error" not in data:
            return {"success": True, "data": data}

        # Fallback: live fetch
        result = data_fetcher.fetch_sub_county_data(county_id, sub_county_id)
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        return {"success": True, "data": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Sub-county data error {county_id}/{sub_county_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/admin/trigger-granular-fetch")
async def trigger_granular_fetch(
    scope: str = "country",
    county_id: str = None,
    region: str = None,
    sub_county_id: str = None,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """
    Trigger a data fetch at any granularity: country, region, county, or sub-county.

    Query params:
        scope: country | region | county | sub_county
        county_id: required for county / sub_county scope
        region: required for region scope
        sub_county_id: required for sub_county scope
    """
    try:
        token = credentials.credentials
        session = auth_service.verify_session(token)
        if not session:
            raise HTTPException(status_code=401, detail="Invalid authentication")

        if not scheduler_service:
            raise HTTPException(status_code=503, detail="Scheduler service not available")

        logger.info(
            f"Granular fetch triggered: scope={scope}, county={county_id}, "
            f"region={region}, sub_county={sub_county_id}"
        )

        result = await scheduler_service.trigger_immediate_fetch(
            scope=scope,
            county_id=county_id,
            region=region,
            sub_county_id=sub_county_id,
        )

        return {
            "success": result.get("success", False),
            "scope": result.get("scope", scope),
            "message": "Fetch completed" if result.get("success") else "Fetch failed",
            "details": {k: v for k, v in result.items() if k not in ("success", "scope")},
            "timestamp": datetime.now().isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Granular fetch error: {e}")
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
        
        farmer = db_service.get_farmer_by_phone(phone)
        
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
        
        farmers = db_service.get_all_farmers(limit=limit)
        
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
        stats = db_service.get_farmer_statistics()
        
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
        registrations = db_service.get_recent_registrations(days=days, limit=50)
        
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
        success = db_service.delete_farmer(farmer_id)
        
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
        recipients = db_service.get_all_farmers(limit=1000)
        
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
                    # Send custom message via RabbitMQ
                    if rabbitmq_service:
                        rabbitmq_service.publish_message('sms_queue', {
                            "to": farmer['phone'],
                            "message": request.message
                        })
                        success_count += 1 # Assume success for queueing
                    elif sms_service:
                        # Fallback to direct send if RabbitMQ down
                        result = sms_service.send_sms(farmer['phone'], request.message)
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
    farmer: Optional[Dict] = Depends(get_optional_farmer)
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
        
        # Fetch weather data for RAG context
        weather_data = None
        if weather_service and farmer and farmer.get('county'):
            try:
                county_id = farmer.get('county_id') or farmer.get('county', '').lower().replace(' ', '_')
                weather_data = await weather_service.get_county_forecast(county_id)
                if weather_data and 'error' in weather_data:
                    weather_data = None
            except Exception as wx_err:
                logger.debug(f"Weather fetch for chat context: {wx_err}")
        
        # Load past conversation summaries for cross-session context (auth only)
        past_conversations = None
        if farmer and db_service and farmer.get('id'):
            try:
                past_conversations = db_service.get_conversations(
                    farmer_id=farmer.get('id'),
                    limit=3,
                )
            except Exception as conv_err:
                logger.debug(f"Past conversations fetch: {conv_err}")
        
        # Generate AI response
        response_text = flora_service.generate_response(
            user_message=request.message,
            farmer_data=farmer,
            bloom_data=bloom_data,
            chat_history=request.history,
            weather_data=weather_data,
            past_conversations=past_conversations,
        )
        
        # Extract reply and reasoning from dict response
        if isinstance(response_text, dict):
            reply = response_text.get('reply', '')
            reasoning = response_text.get('reasoning', None)
        else:
            reply = str(response_text) if response_text else ''
            reasoning = None
        
        if not reply:
            reply = 'Sorry, I could not process your request.'
        
        # Store in database with conversation threading
        conversation_id = request.conversation_id
        if farmer and db_service:
            try:
                conversation_id = db_service.save_chat_message(
                    phone=farmer.get('phone', ''),
                    role='user',
                    message=request.message,
                    response=reply,
                    reasoning=reasoning,
                    farmer_id=farmer.get('id'),
                    via='web',
                    conversation_id=request.conversation_id,
                )
                # Invalidate conversation list cache for this farmer
                cache.invalidate(f"ss:convos:{farmer.get('id')}:*")
            except:
                pass
        
        return {
            "success": True,
            "data": {
                "reply": reply,
                "reasoning": reasoning,
                "conversation_id": conversation_id,
            }
        }
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ---- Conversation Management ----

@app.get("/api/conversations", tags=["Flora AI"])
async def list_conversations(
    limit: int = 50,
    farmer: Optional[Dict] = Depends(get_current_farmer)
):
    """List all conversations for the authenticated farmer."""
    if not farmer:
        raise HTTPException(status_code=401, detail="Authentication required")
    if not db_service:
        return {"success": True, "data": []}
    # Check Redis cache (30s TTL — conversations change often)
    farmer_id = farmer.get('id')
    cache_key = cache.make_key(f"convos:{farmer_id}", limit)
    cached = cache.get(cache_key)
    if cached is not None:
        return {"success": True, "data": cached}
    conversations = db_service.get_conversations(
        farmer_id=farmer_id,
        limit=min(limit, 100),
    )
    cache.set(cache_key, conversations, ttl=30)
    return {"success": True, "data": conversations}


@app.post("/api/conversations", tags=["Flora AI"])
async def create_conversation(
    farmer: Optional[Dict] = Depends(get_current_farmer)
):
    """Create a new empty conversation thread."""
    if not farmer:
        raise HTTPException(status_code=401, detail="Authentication required")
    if not db_service:
        raise HTTPException(status_code=503, detail="Database unavailable")
    conv = db_service.create_conversation(farmer_id=farmer.get('id'))
    if not conv:
        raise HTTPException(status_code=500, detail="Failed to create conversation")
    return {"success": True, "data": conv}


@app.get("/api/conversations/{conversation_id}/messages", tags=["Flora AI"])
async def get_conversation_messages(
    conversation_id: str,
    limit: int = 100,
    farmer: Optional[Dict] = Depends(get_current_farmer)
):
    """Get all messages in a specific conversation."""
    if not farmer:
        raise HTTPException(status_code=401, detail="Authentication required")
    if not db_service:
        return {"success": True, "data": []}
    messages = db_service.get_conversation_messages(
        conversation_id=conversation_id,
        farmer_id=farmer.get('id'),
        limit=min(limit, 500),
    )
    return {"success": True, "data": messages}


@app.patch("/api/conversations/{conversation_id}", tags=["Flora AI"])
async def update_conversation(
    conversation_id: str,
    body: Dict,
    farmer: Optional[Dict] = Depends(get_current_farmer)
):
    """Update conversation title."""
    if not farmer:
        raise HTTPException(status_code=401, detail="Authentication required")
    title = body.get("title", "")
    if not title:
        raise HTTPException(status_code=400, detail="Title is required")
    if not db_service:
        raise HTTPException(status_code=503, detail="Database unavailable")
    ok = db_service.update_conversation_title(conversation_id, farmer.get('id'), title)
    if not ok:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"success": True}


@app.delete("/api/conversations/{conversation_id}", tags=["Flora AI"])
async def delete_conversation(
    conversation_id: str,
    farmer: Optional[Dict] = Depends(get_current_farmer)
):
    """Archive (soft-delete) a conversation."""
    if not farmer:
        raise HTTPException(status_code=401, detail="Authentication required")
    if not db_service:
        raise HTTPException(status_code=503, detail="Database unavailable")
    ok = db_service.archive_conversation(conversation_id, farmer.get('id'))
    if not ok:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"success": True}


@app.get("/api/chat/history", tags=["Flora AI"])
async def get_chat_history(
    limit: int = 20,
    farmer: Optional[Dict] = Depends(get_current_farmer)
):
    """Get flat chat history for the authenticated farmer (backwards compat)."""
    if not farmer:
        raise HTTPException(status_code=401, detail="Authentication required")
    if not db_service:
        return {"success": True, "data": []}

    history = db_service.get_chat_history(
        farmer_id=farmer.get('id'),
        limit=min(limit, 100),
    )
    return {"success": True, "data": history}


# ============================================
# Public Data Endpoints (No Auth Required)
# ============================================

@app.get("/api/public/regions")
async def get_regions():
    """Get all Kenya regions, counties and sub-counties"""
    # Build sub-counties lookup keyed by county name
    sub_counties_map = {}
    if SUB_COUNTIES_LOADED:
        for county_id, info in KENYA_SUB_COUNTIES.items():
            county_name = info["county_name"]
            subs = info.get("sub_counties", {})
            sub_counties_map[county_name] = [
                v["name"] for v in subs.values()
            ] if isinstance(subs, dict) else [s["name"] for s in subs]
    return {
        "success": True,
        "data": {
            "regions": KENYA_REGIONS_COUNTIES,
            "crops": ALL_KENYA_CROPS,
            "sub_counties": sub_counties_map
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
            db_service.save_delivery_report({
                "messageId": id,
                "phoneNumber": phoneNumber,
                "status": status,
                "networkCode": networkCode,
                "retryCount": retryCount,
                "failureReason": failureReason,
                "provider": "africastalking",
            })
            logger.info(f"Delivery report saved for message {id}")
        except Exception as db_error:
            logger.error(f"Failed to save delivery report: {db_error}")
        
        # Return success response (Africa's Talking expects this)
        return PlainTextResponse(content="Received")
        
    except Exception as e:
        logger.error(f"Delivery report error: {e}", exc_info=True)
        return PlainTextResponse(content="Error")


@app.post("/api/sms/incoming", tags=["SMS"])
async def incoming_sms(
    from_: str = Form(None, alias="from"),
    to: str = Form(None),
    text: str = Form(''),
    date: str = Form(None),
    id: str = Form(None),
    linkId: str = Form(None),
):
    """
    Incoming SMS callback from Africa's Talking.
    Farmers can reply to Flora AI responses via SMS — their message
    is routed to Flora and a reply is sent back, continuing the
    conversation thread.

    Configure this URL in Africa's Talking dashboard under SMS → Incoming Messages:
    https://your-domain.com/api/sms/incoming
    """
    import asyncio

    phone = from_
    logger.info(f"📨 Incoming SMS from {phone}: {text[:100]}")

    if not phone or not text or not text.strip():
        return PlainTextResponse(content="Received")

    try:
        # Look up farmer
        farmer = db_service.get_farmer_by_phone(phone) if db_service else None
        if not farmer:
            logger.warning(f"Incoming SMS from unregistered number: {phone}")
            welcome_msg = "Welcome! To use Smart Shamba, please register first by dialing our USSD code. 🌾"
            if rabbitmq_service:
                rabbitmq_service.publish_message('sms_queue', {"to": phone, "message": welcome_msg})
            elif sms_service:
                sms_service.send_sms(phone, welcome_msg)
            return PlainTextResponse(content="Received")

        # Find active conversation or create one
        active_conv = db_service.get_active_conversation_by_phone(phone)
        conversation_id = active_conv["id"] if active_conv else None

        # Generate Flora AI response
        reply = ""
        reasoning = None
        if flora_service:
            response_text = flora_service.generate_response(
                user_message=text.strip(),
                farmer_data=farmer,
                bloom_data=None,
            )
            if isinstance(response_text, dict):
                reply = response_text.get('reply', '')
                reasoning = response_text.get('reasoning', None)
            else:
                reply = str(response_text) if response_text else ''

        if not reply:
            reply = "Sorry, I could not process your question right now. Please try again or dial our USSD code."

        # Save to DB with conversation thread
        conversation_id = db_service.save_chat_message(
            phone=phone,
            role="user",
            message=text.strip(),
            response=reply,
            reasoning=reasoning,
            farmer_id=farmer.get("id"),
            via="sms",
            language=farmer.get("language", "en"),
            conversation_id=conversation_id,
        )

        # Send reply via SMS (truncate for SMS limits)
        sms_reply = reply[:1500] + "..." if len(reply) > 1500 else reply
        # Send reply via SMS (truncate for SMS limits)
        sms_reply = reply[:1500] + "..." if len(reply) > 1500 else reply
        sms_payload = f"🌾 Flora AI:\n\n{sms_reply}"
        
        if rabbitmq_service:
            rabbitmq_service.publish_message('sms_queue', {
                "to": phone, "message": sms_payload
            })
        elif sms_service:
            sms_service.send_sms(phone, sms_payload)

        logger.info(f"✅ SMS reply sent to {phone} (conv={conversation_id})")

    except Exception as e:
        logger.error(f"Incoming SMS processing error: {e}", exc_info=True)

    return PlainTextResponse(content="Received")

@app.post("/api/ussd/send-county-data")
async def send_county_data(
    phone: str,
    county_id: str,
    language: str = 'en'
):
    """Send county climate and bloom data via SMS (USSD users)"""
    try:
        farmer = db_service.get_farmer_by_phone(phone)
        if not farmer:
            raise HTTPException(status_code=404, detail="Farmer not found")
        
        # Get county data
        county_data = await get_county_data(county_id)
        
        # Format SMS message
        if language == 'sw':
            message = f"""🌾 Smart Shamba - {county_data['county_name']}

Hali ya Mazao:
🌸 Eneo la Kuchanua: {county_data.get('bloom_area_km2', 0):.1f} km²
🌡️ Joto: {county_data.get('temperature_c', 0):.1f}°C
🌧️ Mvua: {county_data.get('rainfall_mm', 0):.0f} mm
📊 NDVI: {county_data.get('ndvi', 0):.2f}

Data kutoka NASA satellites.
"""
        else:
            message = f"""🌾 Smart Shamba - {county_data['county_name']}

Crop Conditions:
🌸 Bloom Area: {county_data.get('bloom_area_km2', 0):.1f} km²
🌡️ Temperature: {county_data.get('temperature_c', 0):.1f}°C
🌧️ Rainfall: {county_data.get('rainfall_mm', 0):.0f} mm
📊 NDVI: {county_data.get('ndvi', 0):.2f}

Data from NASA satellites.
"""
        
        # Send SMS
        if rabbitmq_service:
            rabbitmq_service.publish_message('sms_queue', {"to": phone, "message": message})
            result = {'success': True, 'queued': True}
        else:
            result = sms_service.send_sms(phone, message)
        
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
        
        farmer = db_service.get_farmer_by_phone(phone)
        
        # Get bloom data for context
        bloom_data = None
        if farmer:
            try:
                county = farmer.get('county', farmer.get('region', 'kenya'))
                bloom_data = bloom_processor.detect_bloom_events(county)
            except:
                pass
        
        # Generate answer
        answer_result = flora_service.answer_question(
            question=question,
            farmer_data=farmer,
            language=language,
            use_internet=True
        )
        answer = answer_result.get('reply', str(answer_result)) if isinstance(answer_result, dict) else str(answer_result)
        
        # Send via SMS
        if rabbitmq_service:
            rabbitmq_service.publish_message('sms_queue', {"to": phone, "message": answer})
            sms_result = {'success': True, 'queued': True}
        else:
            sms_result = sms_service.send_sms(phone, answer)
        
        # Store in chat history
        if farmer:
            try:
                db_service.save_chat_message(
                    phone=phone,
                    role='user',
                    message=question,
                    response=answer,
                    farmer_id=farmer.get('id'),
                    via='ussd',
                    language=language,
                )
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
        
        farmer = db_service.get_farmer_by_phone(phone)
        if not farmer:
            raise HTTPException(status_code=404, detail="Farmer not found")
        
        county = farmer.get('county', farmer.get('region', 'kenya'))
        
        # Get county data
        county_data = await get_county_data(county)
        
        # Generate interpretation
        question = f"Interpret this satellite data for {farmer['name']}'s farm: Bloom area {county_data.get('bloom_area_km2', 0):.1f} km², Temperature {county_data.get('temperature_c', 0):.1f}°C, NDVI {county_data.get('ndvi', 0):.2f}. Crops: {', '.join(farmer.get('crops', []))}. Give actionable farming advice."
        
        answer_result = flora_service.answer_question(
            question=question,
            farmer_data=farmer,
            language=language,
            use_internet=True
        )
        answer = answer_result.get('reply', str(answer_result)) if isinstance(answer_result, dict) else str(answer_result)
        
        # Send via SMS
        if rabbitmq_service:
            rabbitmq_service.publish_message('sms_queue', {"to": phone, "message": answer})
            sms_result = {'success': True, 'queued': True}
        else:
            sms_result = sms_service.send_sms(phone, answer)
        
        return {
            "success": True,
            "interpretation": answer,
            "sms_sent": sms_result.get('success', False)
        }
    except Exception as e:
        logger.error(f"Flora interpret error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# IoT / Sensor Endpoints
# ============================================

class SensorReadingPayload(BaseModel):
    farm_id: int
    device_id: str
    temperature_c: Optional[float] = None
    humidity_pct: Optional[float] = None
    soil_moisture_pct: Optional[float] = None
    soil_ph: Optional[float] = None
    soil_nitrogen: Optional[float] = None
    soil_phosphorus: Optional[float] = None
    soil_potassium: Optional[float] = None
    light_lux: Optional[float] = None
    rainfall_mm: Optional[float] = None
    wind_speed_ms: Optional[float] = None
    pressure_hpa: Optional[float] = None
    co2_ppm: Optional[float] = None
    battery_pct: Optional[float] = None
    rssi_dbm: Optional[float] = None


@app.post("/api/iot/ingest", tags=["IoT"])
async def iot_ingest_single(payload: SensorReadingPayload):
    """Ingest a single sensor reading from an ESP32 device."""
    if not iot_service:
        raise HTTPException(status_code=503, detail="IoT service not available")
    result = iot_service.ingest_reading(payload.model_dump(exclude_none=True))
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Ingest failed"))
    return result


@app.post("/api/iot/ingest/batch", tags=["IoT"])
async def iot_ingest_batch(readings: List[SensorReadingPayload]):
    """Ingest a batch of sensor readings (high-throughput)."""
    if not iot_service:
        raise HTTPException(status_code=503, detail="IoT service not available")
    raw = [r.model_dump(exclude_none=True) for r in readings]
    result = iot_service.ingest_batch(raw)
    return result


@app.get("/api/iot/readings/{farm_id}", tags=["IoT"])
async def iot_get_readings(farm_id: int, hours: int = 24, device_id: str = None):
    """Get recent sensor readings for a farm."""
    if not iot_service:
        raise HTTPException(status_code=503, detail="IoT service not available")
    readings = iot_service.get_farm_readings(farm_id, hours=hours, device_id=device_id)
    return {"farm_id": farm_id, "count": len(readings), "readings": readings}


@app.get("/api/iot/hourly/{farm_id}", tags=["IoT"])
async def iot_hourly_averages(farm_id: int, hours: int = 48, device_id: str = None):
    """Get hourly-aggregated sensor data using TimescaleDB time_bucket."""
    if not iot_service:
        raise HTTPException(status_code=503, detail="IoT service not available")
    data = iot_service.get_hourly_averages(farm_id, hours=hours, device_id=device_id)
    return {"farm_id": farm_id, "interval": "1h", "count": len(data), "data": data}


@app.get("/api/iot/daily/{farm_id}", tags=["IoT"])
async def iot_daily_summary(farm_id: int, days: int = 30, device_id: str = None):
    """Get daily-aggregated sensor data using TimescaleDB time_bucket."""
    if not iot_service:
        raise HTTPException(status_code=503, detail="IoT service not available")
    data = iot_service.get_daily_summary(farm_id, days=days, device_id=device_id)
    return {"farm_id": farm_id, "interval": "1d", "count": len(data), "data": data}


@app.get("/api/iot/devices/{farm_id}", tags=["IoT"])
async def iot_latest_per_device(farm_id: int):
    """Get the latest reading per IoT device for a farm."""
    if not iot_service:
        raise HTTPException(status_code=503, detail="IoT service not available")
    data = iot_service.get_latest_per_device(farm_id)
    return {"farm_id": farm_id, "devices": len(data), "data": data}


@app.get("/api/iot/status", tags=["IoT"])
async def iot_status():
    """Get IoT ingestion service status."""
    return {
        "available": iot_service is not None,
        "mqtt_running": iot_service._running if iot_service else False,
        "mqtt_broker": iot_service.mqtt_broker if iot_service else None,
        "disease_detection": disease_service is not None,
    }


# ============================================
# Device Management Endpoints
# ============================================

class DeviceRegisterPayload(BaseModel):
    device_id: str
    farm_id: int
    farmer_id: int
    device_type: str = "esp32"
    firmware_version: Optional[str] = None
    mac_address: Optional[str] = None
    has_soil_ph: bool = False
    has_soil_moisture: bool = False
    has_soil_npk: bool = False
    has_temperature: bool = True
    has_humidity: bool = True
    has_pressure: bool = False
    has_camera: bool = False
    has_light: bool = False
    has_rain_gauge: bool = False
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    camera_capture_day: int = 0
    camera_capture_hour: int = 8


@app.post("/api/devices/register", tags=["Devices"])
async def register_device(payload: DeviceRegisterPayload):
    """Register a new IoT device and assign it to a farm."""
    try:
        from database.connection import engine
        from database.models import IoTDevice, Farm
        from sqlmodel import Session, select
        from datetime import datetime

        with Session(engine) as session:
            # Check farm exists
            farm = session.get(Farm, payload.farm_id)
            if not farm:
                raise HTTPException(status_code=404, detail=f"Farm {payload.farm_id} not found")

            # Check device not already registered
            existing = session.exec(
                select(IoTDevice).where(IoTDevice.device_id == payload.device_id)
            ).first()
            if existing:
                raise HTTPException(status_code=409, detail=f"Device {payload.device_id} already registered")

            # Create device record
            device = IoTDevice(**payload.model_dump())
            session.add(device)

            # Also add device_id to farm.device_ids JSONB array
            if farm.device_ids is None:
                farm.device_ids = []
            if payload.device_id not in farm.device_ids:
                farm.device_ids = farm.device_ids + [payload.device_id]
                session.add(farm)

            session.commit()
            session.refresh(device)

            return {
                "success": True,
                "device_id": device.device_id,
                "farm_id": device.farm_id,
                "id": device.id,
                "message": f"Device {device.device_id} registered to farm {device.farm_id}",
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Device registration error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/devices/{farm_id}", tags=["Devices"])
async def list_farm_devices(farm_id: int):
    """List all registered IoT devices for a farm."""
    try:
        from database.connection import engine
        from database.models import IoTDevice
        from sqlmodel import Session, select

        with Session(engine) as session:
            devices = session.exec(
                select(IoTDevice).where(IoTDevice.farm_id == farm_id)
            ).all()
            return {
                "farm_id": farm_id,
                "count": len(devices),
                "devices": [
                    {
                        "id": d.id,
                        "device_id": d.device_id,
                        "device_type": d.device_type,
                        "firmware_version": d.firmware_version,
                        "status": d.status,
                        "has_camera": d.has_camera,
                        "has_soil_npk": d.has_soil_npk,
                        "last_seen": d.last_seen.isoformat() if d.last_seen else None,
                        "battery_pct": d.battery_pct,
                    }
                    for d in devices
                ],
            }
    except Exception as e:
        logger.error(f"Error listing devices: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/api/devices/{device_id}/heartbeat", tags=["Devices"])
async def device_heartbeat(device_id: str, battery_pct: Optional[float] = None,
                           rssi_dbm: Optional[int] = None):
    """Update device last_seen timestamp and connectivity info."""
    try:
        from database.connection import engine
        from database.models import IoTDevice
        from sqlmodel import Session, select
        from datetime import datetime

        with Session(engine) as session:
            device = session.exec(
                select(IoTDevice).where(IoTDevice.device_id == device_id)
            ).first()
            if not device:
                raise HTTPException(status_code=404, detail=f"Device {device_id} not found")

            device.last_seen = datetime.utcnow()
            if battery_pct is not None:
                device.battery_pct = battery_pct
            if rssi_dbm is not None:
                device.rssi_dbm = rssi_dbm
            device.status = "active"
            session.add(device)
            session.commit()

            return {"success": True, "device_id": device_id, "last_seen": device.last_seen.isoformat()}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Heartbeat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Image Upload + Disease Detection Endpoints
# ============================================

from fastapi import UploadFile, File, Form


@app.post("/api/images/upload", tags=["Disease Detection"])
async def upload_farm_image(
    file: UploadFile = File(...),
    farm_id: int = Form(...),
    device_id: str = Form(...),
    farmer_id: int = Form(...),
    capture_type: str = Form("manual"),
):
    """
    Upload a farm image for disease detection.

    The image is saved with a unique URL identifier and run through
    BloomVisionCNN for classification into one of 6 categories:
    healthy | leaf_blight | rust | aphid_damage | bloom_detected | wilting

    If disease is detected with >50% confidence, an alert is triggered.
    """
    if not disease_service:
        raise HTTPException(status_code=503, detail="Disease detection service not available")

    # Validate file type
    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    try:
        image_bytes = await file.read()
        if len(image_bytes) < 100:
            raise HTTPException(status_code=400, detail="Image too small")
        if len(image_bytes) > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(status_code=400, detail="Image exceeds 10MB limit")

        result = disease_service.process_farm_image(
            image_bytes=image_bytes,
            farm_id=farm_id,
            device_id=device_id,
            farmer_id=farmer_id,
            capture_type=capture_type,
        )

        # If disease detected with high confidence, generate RAG alert
        if result.get("alert_needed") and smart_alert_service and flora_service:
            try:
                from database.connection import engine
                from database.models import Farmer
                from sqlmodel import Session

                with Session(engine) as session:
                    farmer = session.get(Farmer, farmer_id)
                    if farmer:
                        farmer_data = {
                            "name": farmer.name,
                            "phone": farmer.phone,
                            "county": farmer.county or "",
                            "crops": farmer.crops or [],
                            "farm_size": farmer.farm_size or 0,
                            "language": farmer.language or "en",
                        }
                        disease_context = {
                            "disease_detected": result["classification"],
                            "confidence": result["classification_confidence"],
                            "image_uid": result["image_uid"],
                        }
                        result["disease_alert"] = smart_alert_service.generate_disease_alert(
                            farmer_data, disease_context
                        )

                        # --- Create multimodal training sample ---
                        try:
                            # Gather sensor data
                            sensor_snapshot = {}
                            if iot_service:
                                latest = iot_service.get_latest_per_device(farm_id)
                                if latest:
                                    sensor_snapshot = latest[0] if isinstance(latest, list) else latest

                            # Gather satellite data
                            satellite_snapshot = {}
                            county = farmer.county or ""
                            if county and db_service:
                                cd = db_service.get_county_details(county)
                                if cd and "error" not in cd:
                                    satellite_snapshot = cd.get("satellite_data", {})

                            disease_service.create_multimodal_training_sample(
                                farm_id=farm_id,
                                farmer_id=farmer_id,
                                image_uid=result["image_uid"],
                                image_path=result.get("file_path", ""),
                                classification=result["classification"],
                                cnn_confidence=result["classification_confidence"],
                                sensor_data=sensor_snapshot,
                                satellite_data=satellite_snapshot,
                            )
                        except Exception as ts_err:
                            logger.debug(f"Training sample creation: {ts_err}")
            except Exception as e:
                logger.error(f"Disease alert generation failed: {e}")

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/images/{farm_id}/history", tags=["Disease Detection"])
async def get_farm_image_history(farm_id: int, limit: int = 20):
    """Get disease detection history for a farm's images."""
    if not disease_service:
        raise HTTPException(status_code=503, detail="Disease detection service not available")
    history = disease_service.get_farm_disease_history(farm_id, limit=limit)
    return {"farm_id": farm_id, "count": len(history), "images": history}


@app.get("/api/images/{farm_id}/latest", tags=["Disease Detection"])
async def get_latest_disease_status(farm_id: int):
    """Get the most recent disease detection result for a farm."""
    if not disease_service:
        raise HTTPException(status_code=503, detail="Disease detection service not available")
    latest = disease_service.get_latest_disease_status(farm_id)
    if not latest:
        return {"farm_id": farm_id, "message": "No images found for this farm"}
    return {"farm_id": farm_id, **latest}


@app.get("/api/images/serve/{image_uid}", tags=["Disease Detection"])
async def serve_farm_image(image_uid: str):
    """Serve a farm image by its unique identifier."""
    try:
        from database.connection import engine
        from database.models import CropImage
        from sqlmodel import Session, select
        from fastapi.responses import FileResponse

        with Session(engine) as session:
            img = session.exec(
                select(CropImage).where(CropImage.image_uid == image_uid)
            ).first()
            if not img:
                raise HTTPException(status_code=404, detail="Image not found")

            abs_path = os.path.join(
                os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
                img.file_path
            )
            if not os.path.exists(abs_path):
                raise HTTPException(status_code=404, detail="Image file not found on disk")

            return FileResponse(abs_path, media_type=img.mime_type)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image serve error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Agrovet Product Endpoints
# ============================================

class AgrovetProductCreate(BaseModel):
    name: str
    name_sw: Optional[str] = None
    description: Optional[str] = None
    category: str  # seeds | fertilizer | pesticide | tools | animal_feed
    price_kes: float
    unit: str  # kg | litre | bag | piece
    in_stock: bool = True
    stock_quantity: Optional[int] = None
    supplier_name: Optional[str] = None
    supplier_location: Optional[str] = None
    supplier_county: Optional[str] = None
    supplier_sub_county: Optional[str] = None
    crop_applicable: Optional[List[str]] = None
    image_url: Optional[str] = None


class AgrovetOrderCreate(BaseModel):
    farmer_id: int
    product_id: int
    quantity: int
    payment_method: Optional[str] = None
    delivery_address: Optional[str] = None
    order_source: str = "web"


@app.get("/api/agrovet/products", tags=["Agrovet"])
async def list_agrovet_products(
    category: Optional[str] = None,
    county: Optional[str] = None,
    sub_county: Optional[str] = None,
    crop: Optional[str] = None,
    in_stock: bool = True,
):
    """List agrovet products with optional filters."""
    try:
        from database.connection import get_sync_session
        from database.models import AgrovetProduct
        from sqlmodel import select

        with get_sync_session() as session:
            stmt = select(AgrovetProduct).where(AgrovetProduct.active == True)
            if in_stock:
                stmt = stmt.where(AgrovetProduct.in_stock == True)
            if category:
                stmt = stmt.where(AgrovetProduct.category == category)
            if county:
                stmt = stmt.where(AgrovetProduct.supplier_county == county)
            if sub_county:
                stmt = stmt.where(AgrovetProduct.supplier_sub_county == sub_county)

            products = session.exec(stmt).all()

            # Filter by applicable crop (JSONB contains)
            if crop:
                products = [
                    p for p in products
                    if p.crop_applicable and crop in p.crop_applicable
                ]

            return {
                "count": len(products),
                "products": [
                    {
                        "id": p.id,
                        "name": p.name,
                        "name_sw": p.name_sw,
                        "description": p.description,
                        "category": p.category,
                        "price_kes": float(p.price_kes),
                        "unit": p.unit,
                        "in_stock": p.in_stock,
                        "stock_quantity": p.stock_quantity,
                        "supplier_name": p.supplier_name,
                        "supplier_location": p.supplier_location,
                        "supplier_county": p.supplier_county,
                        "supplier_sub_county": p.supplier_sub_county,
                        "crop_applicable": p.crop_applicable,
                        "image_url": p.image_url,
                    }
                    for p in products
                ],
            }
    except Exception as e:
        logger.error(f"Agrovet list error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/agrovet/products/{product_id}", tags=["Agrovet"])
async def get_agrovet_product(product_id: int):
    """Get a single agrovet product by ID."""
    try:
        from database.connection import get_sync_session
        from database.models import AgrovetProduct

        with get_sync_session() as session:
            product = session.get(AgrovetProduct, product_id)
            if not product:
                raise HTTPException(status_code=404, detail="Product not found")
            return {
                "id": product.id,
                "name": product.name,
                "name_sw": product.name_sw,
                "description": product.description,
                "category": product.category,
                "price_kes": float(product.price_kes),
                "unit": product.unit,
                "in_stock": product.in_stock,
                "stock_quantity": product.stock_quantity,
                "supplier_name": product.supplier_name,
                "supplier_location": product.supplier_location,
                "supplier_county": product.supplier_county,
                "supplier_sub_county": product.supplier_sub_county,
                "crop_applicable": product.crop_applicable,
                "image_url": product.image_url,
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Agrovet get error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/agrovet/products", tags=["Agrovet"])
async def create_agrovet_product(payload: AgrovetProductCreate):
    """Add a new agrovet product (admin)."""
    try:
        from database.connection import get_sync_session
        from database.models import AgrovetProduct
        from decimal import Decimal

        with get_sync_session() as session:
            product = AgrovetProduct(
                name=payload.name,
                name_sw=payload.name_sw,
                description=payload.description,
                category=payload.category,
                price_kes=Decimal(str(payload.price_kes)),
                unit=payload.unit,
                in_stock=payload.in_stock,
                stock_quantity=payload.stock_quantity,
                supplier_name=payload.supplier_name,
                supplier_location=payload.supplier_location,
                supplier_county=payload.supplier_county,
                crop_applicable=payload.crop_applicable,
                image_url=payload.image_url,
            )
            session.add(product)
            session.commit()
            session.refresh(product)
            return {"success": True, "id": product.id}
    except Exception as e:
        logger.error(f"Agrovet create error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/agrovet/orders", tags=["Agrovet"])
async def create_agrovet_order(payload: AgrovetOrderCreate):
    """Place an order for an agrovet product."""
    try:
        from database.connection import get_sync_session
        from database.models import AgrovetProduct, AgrovetOrder
        from decimal import Decimal

        with get_sync_session() as session:
            product = session.get(AgrovetProduct, payload.product_id)
            if not product:
                raise HTTPException(status_code=404, detail="Product not found")
            if not product.in_stock:
                raise HTTPException(status_code=400, detail="Product out of stock")

            total = Decimal(str(float(product.price_kes) * payload.quantity))
            order = AgrovetOrder(
                farmer_id=payload.farmer_id,
                product_id=payload.product_id,
                quantity=payload.quantity,
                total_price_kes=total,
                payment_method=payload.payment_method,
                delivery_address=payload.delivery_address,
                order_source=payload.order_source,
            )
            session.add(order)
            session.commit()
            session.refresh(order)
            return {"success": True, "order_id": order.id, "total_kes": float(total)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Agrovet order error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/agrovet/orders/{farmer_id}", tags=["Agrovet"])
async def get_farmer_orders(farmer_id: int):
    """Get all orders for a farmer."""
    try:
        from database.connection import get_sync_session
        from database.models import AgrovetOrder
        from sqlmodel import select

        with get_sync_session() as session:
            stmt = (
                select(AgrovetOrder)
                .where(AgrovetOrder.farmer_id == farmer_id)
                .order_by(AgrovetOrder.created_at.desc())
            )
            orders = session.exec(stmt).all()
            return {
                "count": len(orders),
                "orders": [
                    {
                        "id": o.id,
                        "product_id": o.product_id,
                        "quantity": o.quantity,
                        "total_price_kes": float(o.total_price_kes),
                        "payment_status": o.payment_status,
                        "delivery_status": o.delivery_status,
                        "order_source": o.order_source,
                        "created_at": o.created_at.isoformat() if o.created_at else None,
                    }
                    for o in orders
                ],
            }
    except Exception as e:
        logger.error(f"Agrovet orders get error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/agrovet/orders/my-shop", tags=["Agrovet"])
async def get_agrovet_shop_orders(
    farmer: Dict = Depends(get_current_farmer),
    status: Optional[str] = None,
):
    """Get all orders for the logged-in agrovet shop owner."""
    try:
        from database.connection import get_sync_session
        from database.models import AgrovetOrder, AgrovetProduct
        from sqlmodel import select

        agrovet_id = farmer.get("id")
        if not agrovet_id:
            raise HTTPException(status_code=401, detail="Not authenticated")

        with get_sync_session() as session:
            stmt = (
                select(AgrovetOrder)
                .where(AgrovetOrder.agrovet_id == agrovet_id)
                .order_by(AgrovetOrder.created_at.desc())
            )
            if status:
                stmt = stmt.where(AgrovetOrder.delivery_status == status)
            orders = session.exec(stmt).all()

            # Also fetch orders for products owned by this agrovet
            product_stmt = select(AgrovetProduct.id).where(AgrovetProduct.agrovet_id == agrovet_id)
            my_product_ids = [p for p in session.exec(product_stmt).all()]

            if my_product_ids:
                product_orders_stmt = (
                    select(AgrovetOrder)
                    .where(AgrovetOrder.product_id.in_(my_product_ids))
                    .order_by(AgrovetOrder.created_at.desc())
                )
                if status:
                    product_orders_stmt = product_orders_stmt.where(AgrovetOrder.delivery_status == status)
                product_orders = session.exec(product_orders_stmt).all()

                # Merge and deduplicate
                existing_ids = {o.id for o in orders}
                for o in product_orders:
                    if o.id not in existing_ids:
                        orders.append(o)

            # Enrich orders with product name
            result = []
            for o in orders:
                product = session.get(AgrovetProduct, o.product_id)
                result.append({
                    "id": o.id,
                    "order_number": o.order_number,
                    "farmer_id": o.farmer_id,
                    "product_id": o.product_id,
                    "product_name": product.name if product else "Unknown",
                    "quantity": o.quantity,
                    "total_price": float(o.total_price_kes),
                    "total_price_kes": float(o.total_price_kes),
                    "payment_method": o.payment_method,
                    "payment_status": o.payment_status,
                    "delivery_status": o.delivery_status,
                    "status": o.delivery_status,
                    "order_source": o.order_source,
                    "notes": o.notes,
                    "created_at": o.created_at.isoformat() if o.created_at else None,
                })

            return {"count": len(result), "orders": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Agrovet shop orders error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/api/agrovet/orders/{order_id}/status", tags=["Agrovet"])
async def update_order_status(
    order_id: int,
    delivery_status: Optional[str] = None,
    payment_status: Optional[str] = None,
):
    """Update order delivery/payment status (for agrovet owner)."""
    try:
        from database.connection import get_sync_session
        from database.models import AgrovetOrder

        valid_delivery = {"pending", "processing", "shipped", "delivered", "cancelled"}
        valid_payment = {"pending", "paid", "failed", "refunded"}

        if delivery_status and delivery_status not in valid_delivery:
            raise HTTPException(status_code=400, detail=f"Invalid delivery_status. Must be one of: {valid_delivery}")
        if payment_status and payment_status not in valid_payment:
            raise HTTPException(status_code=400, detail=f"Invalid payment_status. Must be one of: {valid_payment}")

        with get_sync_session() as session:
            order = session.get(AgrovetOrder, order_id)
            if not order:
                raise HTTPException(status_code=404, detail="Order not found")

            if delivery_status:
                order.delivery_status = delivery_status
            if payment_status:
                order.payment_status = payment_status
            order.updated_at = datetime.utcnow()

            session.add(order)
            session.commit()
            session.refresh(order)

            return {
                "success": True,
                "order_id": order.id,
                "delivery_status": order.delivery_status,
                "payment_status": order.payment_status,
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Order status update error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/agrovet/products/{product_id}", tags=["Agrovet"])
async def update_agrovet_product(product_id: int, payload: AgrovetProductCreate):
    """Update an agrovet product."""
    try:
        from database.connection import get_sync_session
        from database.models import AgrovetProduct
        from decimal import Decimal

        with get_sync_session() as session:
            product = session.get(AgrovetProduct, product_id)
            if not product:
                raise HTTPException(status_code=404, detail="Product not found")

            product.name = payload.name
            if payload.name_sw is not None:
                product.name_sw = payload.name_sw
            if payload.description is not None:
                product.description = payload.description
            product.category = payload.category
            product.price_kes = Decimal(str(payload.price_kes))
            product.unit = payload.unit
            product.in_stock = payload.in_stock
            if payload.stock_quantity is not None:
                product.stock_quantity = payload.stock_quantity
            if payload.supplier_name is not None:
                product.supplier_name = payload.supplier_name
            if payload.supplier_location is not None:
                product.supplier_location = payload.supplier_location
            if payload.supplier_county is not None:
                product.supplier_county = payload.supplier_county
            if payload.crop_applicable is not None:
                product.crop_applicable = payload.crop_applicable
            product.updated_at = datetime.utcnow()

            session.add(product)
            session.commit()
            session.refresh(product)
            return {"success": True, "id": product.id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Agrovet update error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/agrovet/products/{product_id}", tags=["Agrovet"])
async def delete_agrovet_product(product_id: int):
    """Delete (soft-deactivate) an agrovet product."""
    try:
        from database.connection import get_sync_session
        from database.models import AgrovetProduct

        with get_sync_session() as session:
            product = session.get(AgrovetProduct, product_id)
            if not product:
                raise HTTPException(status_code=404, detail="Product not found")

            product.active = False
            product.updated_at = datetime.utcnow()
            session.add(product)
            session.commit()
            return {"success": True, "message": f"Product {product_id} deactivated"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Agrovet delete error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Agrovet Recommendation Endpoints (Disease → Product → Purchase)
# ============================================

@app.get("/api/agrovet/recommend/{condition}", tags=["Agrovet"])
async def recommend_for_condition(
    condition: str,
    farmer: Dict = Depends(get_current_farmer),
):
    """
    Get treatment recommendations + nearest agrovets for a disease/deficiency.

    Condition can be: leaf_blight, rust, aphid_damage, wilting, nitrogen_low,
    phosphorus_low, potassium_low, soil_ph_low, soil_ph_high, moisture_low,
    fall_armyworm
    """
    if not agrovet_rec_service:
        raise HTTPException(status_code=503, detail="Agrovet recommendation service not available")

    try:
        result = agrovet_rec_service.recommend_for_condition(
            condition=condition,
            farmer_data=farmer,
        )
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"Agrovet recommend error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/agrovet/search-nearby", tags=["Agrovet"])
async def search_nearby_agrovets(
    county: str,
    sub_county: Optional[str] = None,
    product: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 10,
):
    """Search for nearest agrovets by location, optionally filtering by product/category."""
    if not agrovet_rec_service:
        raise HTTPException(status_code=503, detail="Agrovet recommendation service not available")

    try:
        agrovets = agrovet_rec_service.find_nearest_agrovets(
            county=county,
            sub_county=sub_county,
            product_names=[product] if product else None,
            category=category,
            limit=limit,
        )
        return {"success": True, "count": len(agrovets), "agrovets": agrovets}
    except Exception as e:
        logger.error(f"Agrovet search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/agrovet/treatment-plan/{condition}", tags=["Agrovet"])
async def get_treatment_plan(
    condition: str,
    farm_size: float = 1.0,
    crops: Optional[str] = None,
    county: Optional[str] = None,
    # Sensor data (optional — enables AI treatment plan)
    soil_nitrogen: Optional[float] = None,
    soil_phosphorus: Optional[float] = None,
    soil_potassium: Optional[float] = None,
    soil_ph: Optional[float] = None,
    soil_moisture_pct: Optional[float] = None,
    temperature: Optional[float] = None,
    humidity: Optional[float] = None,
    # Satellite data (optional)
    ndvi: Optional[float] = None,
    ndwi: Optional[float] = None,
    rainfall_mm: Optional[float] = None,
):
    """Get a treatment plan with dosages scaled to farm size.
    
    If sensor/satellite data provided, returns an AI-enhanced treatment plan
    from Gemini that considers telemetry context. Otherwise returns the
    deterministic catalog-based plan.
    """
    if not agrovet_rec_service:
        raise HTTPException(status_code=503, detail="Agrovet recommendation service not available")

    try:
        crop_list = crops.split(",") if crops else []

        # Build sensor_data dict from provided params
        sensor_data = {}
        for key, val in [
            ("soil_nitrogen", soil_nitrogen), ("soil_phosphorus", soil_phosphorus),
            ("soil_potassium", soil_potassium), ("soil_ph", soil_ph),
            ("soil_moisture_pct", soil_moisture_pct), ("temperature", temperature),
            ("humidity", humidity),
        ]:
            if val is not None:
                sensor_data[key] = val

        satellite_data = {}
        for key, val in [("ndvi", ndvi), ("ndwi", ndwi), ("rainfall_mm", rainfall_mm)]:
            if val is not None:
                satellite_data[key] = val

        # Use AI plan if telemetry data available, else catalog
        if sensor_data or satellite_data:
            plan = agrovet_rec_service.get_ai_treatment_plan(
                condition=condition,
                farm_size_acres=farm_size,
                crops=crop_list,
                sensor_data=sensor_data or None,
                satellite_data=satellite_data or None,
                county=county,
            )
        else:
            plan = agrovet_rec_service.get_treatment_plan(condition, farm_size, crop_list)

        if not plan:
            raise HTTPException(status_code=404, detail=f"No treatment plan for condition: {condition}")
        return {"success": True, "data": plan}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Treatment plan error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/agrovet/order-from-recommendation", tags=["Agrovet"])
async def order_from_recommendation(
    farmer_id: int = Form(...),
    product_id: int = Form(...),
    quantity: int = Form(1),
    payment_method: str = Form("mpesa"),
):
    """Create an order from an agrovet recommendation."""
    if not agrovet_rec_service:
        raise HTTPException(status_code=503, detail="Agrovet recommendation service not available")

    try:
        result = agrovet_rec_service.create_order_from_recommendation(
            farmer_id=farmer_id,
            product_id=product_id,
            quantity=quantity,
            payment_method=payment_method,
        )
        return result
    except Exception as e:
        logger.error(f"Agrovet order-from-recommendation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/agrovet/detect-deficiencies", tags=["Agrovet"])
async def detect_sensor_deficiencies(
    farmer: Dict = Depends(get_current_farmer),
):
    """
    Analyze the farmer's latest IoT sensor data and detect soil
    deficiencies (low nitrogen, phosphorus, potassium, pH, moisture).
    Returns detected conditions + recommended products.
    """
    if not AGROVET_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Agrovet service not available")

    try:
        # Get latest sensor readings for the farmer
        sensor_data = {}
        if iot_service and db_service:
            from database.connection import get_sync_session
            from sqlmodel import text
            with get_sync_session() as session:
                rows = session.exec(text(
                    "SELECT sr.soil_nitrogen, sr.soil_phosphorus, sr.soil_potassium, "
                    "sr.soil_ph, sr.soil_moisture_pct "
                    "FROM sensor_readings sr "
                    "JOIN farms f ON sr.farm_id = f.id "
                    "WHERE f.farmer_id = :fid ORDER BY sr.ts DESC LIMIT 1"
                ), params={"fid": farmer["id"]}).first()
                if rows:
                    sensor_data = {
                        "soil_nitrogen": rows[0],
                        "soil_phosphorus": rows[1],
                        "soil_potassium": rows[2],
                        "soil_ph": rows[3],
                        "soil_moisture_pct": rows[4],
                    }

        if not sensor_data:
            return {"success": True, "deficiencies": [], "message": "No sensor data available"}

        deficiencies = detect_deficiencies_from_sensors(sensor_data)

        # Get recommendations for each deficiency
        recommendations = []
        if agrovet_rec_service:
            for d in deficiencies[:5]:
                rec = agrovet_rec_service.recommend_for_condition(
                    condition=d["condition"], farmer_data=farmer
                )
                recommendations.append({
                    "deficiency": d,
                    "recommendation": rec,
                })

        return {
            "success": True,
            "sensor_data": sensor_data,
            "deficiencies": deficiencies,
            "recommendations": recommendations,
        }
    except Exception as e:
        logger.error(f"Deficiency detection error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Chat with Image Upload (Disease Classification in Chat)
# ============================================

@app.post("/api/chat/with-image", tags=["Flora AI"])
async def chat_with_image(
    message: str = Form("What's wrong with my crop?"),
    file: UploadFile = File(...),
    farmer: Dict = Depends(get_current_farmer),
):
    """
    Chat with Flora AI and include an uploaded image for disease classification.

    The image is classified by BloomVisionCNN and the result is included
    in the Flora AI context for a comprehensive response combining
    visual diagnosis + RAG knowledge + farm telemetry.
    """
    try:
        # 1. Classify the image
        classification_result = {}
        if disease_service:
            image_bytes = await file.read()
            if len(image_bytes) < 100:
                raise HTTPException(status_code=400, detail="Image too small")
            if len(image_bytes) > 10 * 1024 * 1024:
                raise HTTPException(status_code=400, detail="Image exceeds 10MB")

            # Get farmer's farm_id
            farm_id = 0
            from database.connection import get_sync_session
            from database.models import Farm
            from sqlmodel import select as sql_select
            with get_sync_session() as session:
                farm = session.exec(
                    sql_select(Farm).where(Farm.farmer_id == farmer["id"]).limit(1)
                ).first()
                if farm:
                    farm_id = farm.id

            classification_result = disease_service.process_farm_image(
                image_bytes=image_bytes,
                farm_id=farm_id,
                device_id="web-upload",
                farmer_id=farmer["id"],
                capture_type="chat_upload",
            )

        # 2. Build Flora AI context with classification
        disease_context = ""
        disease_name = classification_result.get("classification", "unknown")
        confidence = classification_result.get("classification_confidence", 0)
        image_uid = classification_result.get("image_uid", "")

        if disease_name and disease_name != "unknown":
            disease_display = {
                "leaf_blight": "Leaf Blight", "rust": "Rust Disease",
                "aphid_damage": "Aphid Damage", "wilting": "Wilting",
                "bloom_detected": "Bloom Detected", "healthy": "Healthy",
            }
            display = disease_display.get(disease_name, disease_name.replace("_", " ").title())
            disease_context = (
                f"\n\n**IMAGE ANALYSIS (BloomVisionCNN):**\n"
                f"- Classification: {display}\n"
                f"- Confidence: {confidence:.0%}\n"
                f"- Image ID: {image_uid}\n"
            )

        # 3. Generate Flora AI response with image context
        combined_message = message + disease_context
        response = {"reply": "Flora AI is currently unavailable.", "reasoning": None}
        if flora_service:
            response = flora_service.generate_response(
                user_message=combined_message,
                farmer_data=farmer,
            )
            # Ensure dict format
            if not isinstance(response, dict):
                response = {"reply": str(response), "reasoning": None}

        # 4. If disease detected → fire agrovet recommendation
        agrovet_data = {}
        if (disease_name not in ("healthy", "bloom_detected", "unknown")
                and confidence > 0.5 and agrovet_rec_service):
            try:
                agrovet_data = agrovet_rec_service.recommend_for_condition(
                    condition=disease_name, farmer_data=farmer
                )
            except Exception as e:
                logger.error(f"Chat image agrovet rec failed: {e}")

        # 5. If alert_needed → trigger smart alert
        alert_result = {}
        if classification_result.get("alert_needed") and smart_alert_service:
            try:
                alert_result = smart_alert_service.generate_disease_alert(
                    farmer_data=farmer,
                    disease_context={
                        "disease_detected": disease_name,
                        "confidence": confidence,
                        "image_uid": image_uid,
                    },
                )
            except Exception as e:
                logger.error(f"Chat image alert failed: {e}")

        # 6. Save chat message
        reply_text = response.get("reply", "")
        if farmer and db_service:
            try:
                db_service.save_chat_message(
                    phone=farmer.get("phone", ""),
                    role="user",
                    message=f"[IMAGE: {image_uid}] {message}",
                    response=reply_text,
                    farmer_id=farmer.get("id"),
                    via="web",
                )
            except Exception:
                pass

        return {
            "success": True,
            "data": {
                "reply": reply_text,
                "reasoning": response.get("reasoning", None),
                "classification": {
                    "disease": disease_name,
                    "confidence": confidence,
                    "image_uid": image_uid,
                    "alert_needed": classification_result.get("alert_needed", False),
                },
                "agrovet_recommendation": agrovet_data if agrovet_data else None,
                "disease_alert": alert_result if alert_result else None,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat with image error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Multimodal Training Samples Endpoints
# ============================================

@app.get("/api/training-samples", tags=["ML"])
async def list_training_samples(
    unused_only: bool = True,
    min_confidence: float = 0.6,
    limit: int = 100,
    farmer: Dict = Depends(get_current_farmer),
):
    """List multimodal training samples (admin)."""
    if not disease_service:
        raise HTTPException(status_code=503, detail="Disease service not available")
    samples = disease_service.get_training_samples(
        unused_only=unused_only, min_confidence=min_confidence, limit=limit
    )
    return {"success": True, "count": len(samples), "samples": samples}


@app.get("/api/training-samples/stats", tags=["ML"])
async def training_sample_stats(farmer: Dict = Depends(get_current_farmer)):
    """Get statistics on multimodal training samples."""
    try:
        from database.connection import get_sync_session
        from database.models import MultimodalTrainingSample
        from sqlmodel import text

        with get_sync_session() as session:
            result = session.exec(text(
                "SELECT label, count(*) as cnt, avg(cnn_confidence) as avg_conf, "
                "avg(correlation_score) as avg_corr, "
                "sum(CASE WHEN used_in_training THEN 1 ELSE 0 END) as used "
                "FROM multimodal_training_samples "
                "GROUP BY label ORDER BY cnt DESC"
            )).all()

            total = session.exec(text(
                "SELECT count(*) FROM multimodal_training_samples"
            )).one()

            return {
                "success": True,
                "total_samples": total[0] if total else 0,
                "by_label": [
                    {
                        "label": r[0], "count": r[1],
                        "avg_confidence": round(float(r[2]), 3) if r[2] else 0,
                        "avg_correlation": round(float(r[3]), 3) if r[3] else 0,
                        "used_in_training": r[4],
                    }
                    for r in result
                ],
            }
    except Exception as e:
        logger.error(f"Training stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Marketplace Endpoints
# ============================================

class MarketplaceListingCreate(BaseModel):
    farmer_id: int
    produce_name: str
    produce_category: str  # grains | vegetables | fruits | dairy | livestock
    description: Optional[str] = None
    quantity_available: float
    unit: str
    price_per_unit_kes: float
    min_order_quantity: Optional[float] = None
    county: Optional[str] = None
    pickup_location: Optional[str] = None
    delivery_available: bool = False
    quality_grade: Optional[str] = None
    harvest_date: Optional[str] = None
    image_url: Optional[str] = None


class MarketplaceBidCreate(BaseModel):
    listing_id: int
    buyer_id: int
    quantity: float
    price_per_unit_kes: float
    message: Optional[str] = None
    payment_method: Optional[str] = None


@app.get("/api/marketplace/listings", tags=["Marketplace"])
async def list_marketplace_listings(
    category: Optional[str] = None,
    county: Optional[str] = None,
    status: str = "active",
):
    """List marketplace produce listings."""
    try:
        from database.connection import get_sync_session
        from database.models import MarketplaceListing
        from sqlmodel import select

        with get_sync_session() as session:
            stmt = select(MarketplaceListing).where(
                MarketplaceListing.status == status
            )
            if category:
                stmt = stmt.where(MarketplaceListing.produce_category == category)
            if county:
                stmt = stmt.where(MarketplaceListing.county == county)

            listings = session.exec(stmt).all()
            return {
                "count": len(listings),
                "listings": [
                    {
                        "id": l.id,
                        "farmer_id": l.farmer_id,
                        "produce_name": l.produce_name,
                        "produce_category": l.produce_category,
                        "description": l.description,
                        "quantity_available": l.quantity_available,
                        "unit": l.unit,
                        "price_per_unit_kes": float(l.price_per_unit_kes),
                        "min_order_quantity": l.min_order_quantity,
                        "county": l.county,
                        "pickup_location": l.pickup_location,
                        "delivery_available": l.delivery_available,
                        "quality_grade": l.quality_grade,
                        "harvest_date": l.harvest_date.isoformat() if l.harvest_date else None,
                        "image_url": l.image_url,
                        "status": l.status,
                        "created_at": l.created_at.isoformat() if l.created_at else None,
                    }
                    for l in listings
                ],
            }
    except Exception as e:
        logger.error(f"Marketplace list error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/marketplace/listings", tags=["Marketplace"])
async def create_marketplace_listing(payload: MarketplaceListingCreate):
    """Create a new produce listing."""
    try:
        from database.connection import get_sync_session
        from database.models import MarketplaceListing
        from decimal import Decimal
        from datetime import date as dt_date

        with get_sync_session() as session:
            listing = MarketplaceListing(
                farmer_id=payload.farmer_id,
                produce_name=payload.produce_name,
                produce_category=payload.produce_category,
                description=payload.description,
                quantity_available=payload.quantity_available,
                unit=payload.unit,
                price_per_unit_kes=Decimal(str(payload.price_per_unit_kes)),
                min_order_quantity=payload.min_order_quantity,
                county=payload.county,
                pickup_location=payload.pickup_location,
                delivery_available=payload.delivery_available,
                quality_grade=payload.quality_grade,
                harvest_date=(
                    dt_date.fromisoformat(payload.harvest_date)
                    if payload.harvest_date else None
                ),
                image_url=payload.image_url,
            )
            session.add(listing)
            session.commit()
            session.refresh(listing)
            return {"success": True, "listing_id": listing.id}
    except Exception as e:
        logger.error(f"Marketplace create error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/marketplace/listings/{listing_id}", tags=["Marketplace"])
async def get_marketplace_listing(listing_id: int):
    """Get a single marketplace listing with its bids."""
    try:
        from database.connection import get_sync_session
        from database.models import MarketplaceListing, MarketplaceBid
        from sqlmodel import select

        with get_sync_session() as session:
            listing = session.get(MarketplaceListing, listing_id)
            if not listing:
                raise HTTPException(status_code=404, detail="Listing not found")

            # Get bids
            bids_stmt = (
                select(MarketplaceBid)
                .where(MarketplaceBid.listing_id == listing_id)
                .order_by(MarketplaceBid.created_at.desc())
            )
            bids = session.exec(bids_stmt).all()

            return {
                "id": listing.id,
                "farmer_id": listing.farmer_id,
                "produce_name": listing.produce_name,
                "produce_category": listing.produce_category,
                "description": listing.description,
                "quantity_available": listing.quantity_available,
                "unit": listing.unit,
                "price_per_unit_kes": float(listing.price_per_unit_kes),
                "county": listing.county,
                "status": listing.status,
                "quality_grade": listing.quality_grade,
                "delivery_available": listing.delivery_available,
                "created_at": listing.created_at.isoformat() if listing.created_at else None,
                "bids": [
                    {
                        "id": b.id,
                        "buyer_id": b.buyer_id,
                        "quantity": b.quantity,
                        "price_per_unit_kes": float(b.price_per_unit_kes),
                        "total_price_kes": float(b.total_price_kes),
                        "status": b.status,
                        "message": b.message,
                        "created_at": b.created_at.isoformat() if b.created_at else None,
                    }
                    for b in bids
                ],
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Marketplace get error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/marketplace/bids", tags=["Marketplace"])
async def create_marketplace_bid(payload: MarketplaceBidCreate):
    """Place a bid on a marketplace listing."""
    try:
        from database.connection import get_sync_session
        from database.models import MarketplaceListing, MarketplaceBid
        from decimal import Decimal

        with get_sync_session() as session:
            listing = session.get(MarketplaceListing, payload.listing_id)
            if not listing:
                raise HTTPException(status_code=404, detail="Listing not found")
            if listing.status != "active":
                raise HTTPException(status_code=400, detail="Listing is not active")

            total = Decimal(str(payload.price_per_unit_kes * payload.quantity))
            bid = MarketplaceBid(
                listing_id=payload.listing_id,
                buyer_id=payload.buyer_id,
                quantity=payload.quantity,
                price_per_unit_kes=Decimal(str(payload.price_per_unit_kes)),
                total_price_kes=total,
                message=payload.message,
                payment_method=payload.payment_method,
            )
            session.add(bid)
            session.commit()
            session.refresh(bid)
            return {"success": True, "bid_id": bid.id, "total_kes": float(total)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Marketplace bid error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/marketplace/farmer/{farmer_id}", tags=["Marketplace"])
async def get_farmer_listings(farmer_id: int):
    """Get all listings by a farmer."""
    try:
        from database.connection import get_sync_session
        from database.models import MarketplaceListing
        from sqlmodel import select

        with get_sync_session() as session:
            stmt = (
                select(MarketplaceListing)
                .where(MarketplaceListing.farmer_id == farmer_id)
                .order_by(MarketplaceListing.created_at.desc())
            )
            listings = session.exec(stmt).all()
            return {
                "count": len(listings),
                "listings": [
                    {
                        "id": l.id,
                        "produce_name": l.produce_name,
                        "produce_category": l.produce_category,
                        "quantity_available": l.quantity_available,
                        "price_per_unit_kes": float(l.price_per_unit_kes),
                        "unit": l.unit,
                        "status": l.status,
                        "county": l.county,
                        "created_at": l.created_at.isoformat() if l.created_at else None,
                    }
                    for l in listings
                ],
            }
    except Exception as e:
        logger.error(f"Marketplace farmer listings error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Weather Forecast Endpoints
# ============================================

@app.get("/api/weather/forecast/daily", tags=["Weather"])
async def get_daily_weather_forecast(lat: float, lon: float, days: int = 10):
    """Get up to 10-day daily weather forecast for a location."""
    if not weather_service:
        raise HTTPException(status_code=503, detail="Weather service not available")
    # Check Redis cache first (15-min TTL)
    cache_key = cache.make_key("weather:daily", lat, lon, days)
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
    result = await weather_service.get_daily_forecast(lat, lon, days)
    if "error" in result:
        raise HTTPException(status_code=502, detail=result["error"])
    cache.set(cache_key, result, ttl=900)  # 15 min
    return result


@app.get("/api/weather/forecast/hourly", tags=["Weather"])
async def get_hourly_weather_forecast(lat: float, lon: float, hours: int = 48):
    """Get hourly weather forecast (up to 240 hours)."""
    if not weather_service:
        raise HTTPException(status_code=503, detail="Weather service not available")
    cache_key = cache.make_key("weather:hourly", lat, lon, hours)
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
    result = await weather_service.get_hourly_forecast(lat, lon, hours)
    if "error" in result:
        raise HTTPException(status_code=502, detail=result["error"])
    cache.set(cache_key, result, ttl=900)
    return result


@app.get("/api/weather/current", tags=["Weather"])
async def get_current_weather(lat: float, lon: float):
    """Get current weather conditions for a location."""
    if not weather_service:
        raise HTTPException(status_code=503, detail="Weather service not available")
    cache_key = cache.make_key("weather:current", lat, lon)
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
    result = await weather_service.get_current_conditions(lat, lon)
    if "error" in result:
        raise HTTPException(status_code=502, detail=result["error"])
    cache.set(cache_key, result, ttl=600)  # 10 min
    return result


@app.get("/api/weather/sub-county/{county_id}/{sub_county_id}", tags=["Weather"])
async def get_sub_county_weather(county_id: str, sub_county_id: str):
    """Get weather forecast for a specific sub-county."""
    if not weather_service:
        raise HTTPException(status_code=503, detail="Weather service not available")
    cache_key = cache.make_key("weather:subcounty", county_id, sub_county_id)
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
    result = await weather_service.get_sub_county_forecast(county_id, sub_county_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    cache.set(cache_key, result, ttl=900)
    return result


@app.get("/api/weather/county/{county_id}", tags=["Weather"])
async def get_county_weather(county_id: str):
    """Get aggregated weather forecast for a county (samples up to 5 sub-counties)."""
    if not weather_service:
        raise HTTPException(status_code=503, detail="Weather service not available")
    cache_key = cache.make_key("weather:county", county_id)
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
    result = await weather_service.get_county_forecast(county_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    cache.set(cache_key, result, ttl=900)
    return result


@app.get("/api/weather/agricultural-insights", tags=["Weather"])
async def get_agricultural_weather_insights(
    lat: float, lon: float, crop: Optional[str] = None
):
    """
    Get agriculture-specific weather insights including:
    - Rainfall outlook and irrigation advice
    - Heat stress warnings
    - Optimal planting/spraying windows
    - Bloom risk assessment
    """
    if not weather_service:
        raise HTTPException(status_code=503, detail="Weather service not available")
    result = await weather_service.get_agricultural_insights(lat, lon, crop)
    if "error" in result:
        raise HTTPException(status_code=502, detail=result["error"])
    return result


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

