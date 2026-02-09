# pyright: reportAssignmentType=false
"""
SQLModel database models for Smart Shamba Platform
PostgreSQL with pgvector extension

Tables:
- farmers: Farmer profiles and contact info
- farms: Farm details (location, size, crops)
- sensor_readings: IoT sensor data (time-series, partitioned)
- model_outputs: ML prediction outputs
- ag_knowledge: Agricultural knowledge base with vector embeddings (pgvector)
- gee_county_data: Google Earth Engine satellite data per county
- alerts: Notifications sent to farmers
- ussd_sessions: Active USSD session state
- bloom_events: Detected bloom/flowering events
- chat_history: Flora AI chatbot conversations
- message_templates: Multilingual message templates
- agrovet_products: Agricultural input products catalog
- agrovet_orders: Purchase orders for agrovet products
- marketplace_listings: Farmer produce listings
- marketplace_bids: Buyer bids on produce
- agrovet_profiles: Agrovet shop owner profiles
- buyer_profiles: Buyer/trader profiles
- transactions: Payment transactions (M-Pesa, Airtel, card)
"""

import uuid
from datetime import datetime, date
from typing import Optional, List
from decimal import Decimal

from sqlmodel import SQLModel, Field, Column, Relationship
from sqlalchemy import (
    Text, Index, UniqueConstraint, JSON, DateTime,
    Numeric, Boolean, BigInteger, SmallInteger,
    func, text as sa_text,
)
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from pgvector.sqlalchemy import Vector


# ==============================================================================
# Timestamp field factories (each call returns a NEW Column instance)
# ==============================================================================

def _created_at_field():
    return Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False),
    )

def _updated_at_field():
    return Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False),
    )


# ==============================================================================
# Core Models
# ==============================================================================

class Farmer(SQLModel, table=True):
    """Farmer profile and authentication data"""
    __tablename__ = "farmers"

    id: Optional[int] = Field(default=None, primary_key=True)
    phone: str = Field(max_length=20, index=True, unique=True)
    name: str = Field(max_length=100)
    email: Optional[str] = Field(default=None, max_length=255)
    
    # Authentication
    password_hash: Optional[str] = Field(default=None, max_length=255)
    password_salt: Optional[str] = Field(default=None, max_length=64)
    
    # Profile
    region: Optional[str] = Field(default=None, max_length=50, index=True)
    county: Optional[str] = Field(default=None, max_length=50, index=True)
    sub_county: Optional[str] = Field(default=None, max_length=100, index=True)
    language: str = Field(default="en", max_length=5)
    sms_enabled: bool = Field(default=True)
    
    # User type & identification
    user_type: str = Field(default="farmer", max_length=20, index=True)  # farmer | agrovet | buyer | admin
    display_id: Optional[str] = Field(default=None, max_length=20, unique=True, index=True)  # F-0001, A-0001, B-0001
    
    # Registration
    registration_source: str = Field(default="web", max_length=20)  # web | ussd | manual
    is_admin: bool = Field(default=False)
    active: bool = Field(default=True, index=True)
    
    # Profile picture
    avatar_url: Optional[str] = Field(default=None, max_length=500)
    
    # Location (for geo queries)
    location_lat: Optional[float] = Field(default=None)
    location_lon: Optional[float] = Field(default=None)
    
    # Crops stored as JSON array
    crops: Optional[List[str]] = Field(default=None, sa_column=Column(JSONB, nullable=True))
    
    # Farm details
    farm_size: Optional[float] = Field(default=None)  # acres
    
    # Counters
    alert_count: int = Field(default=0)
    last_login: Optional[datetime] = Field(default=None)
    last_alert: Optional[datetime] = Field(default=None)

    # Timestamps
    created_at: datetime = _created_at_field()
    updated_at: datetime = _updated_at_field()

    # Relationships (cascade delete children when farmer is deleted)
    farms: List["Farm"] = Relationship(back_populates="farmer", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    alerts: List["Alert"] = Relationship(back_populates="farmer", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    chat_history: List["ChatHistory"] = Relationship(back_populates="farmer", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    conversations: List["Conversation"] = Relationship(back_populates="farmer", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    agrovet_profile: Optional["AgrovetProfile"] = Relationship(back_populates="user", sa_relationship_kwargs={"cascade": "all, delete-orphan", "uselist": False})
    buyer_profile: Optional["BuyerProfile"] = Relationship(back_populates="user", sa_relationship_kwargs={"cascade": "all, delete-orphan", "uselist": False})


class Farm(SQLModel, table=True):
    """Individual farm owned by a farmer"""
    __tablename__ = "farms"

    id: Optional[int] = Field(default=None, primary_key=True)
    farmer_id: int = Field(foreign_key="farmers.id", index=True)
    name: Optional[str] = Field(default=None, max_length=100)
    
    # Location
    latitude: float
    longitude: float
    altitude_m: Optional[float] = Field(default=None)
    county: Optional[str] = Field(default=None, max_length=50)
    sub_county: Optional[str] = Field(default=None, max_length=100)
    
    # Farm details
    size_acres: Optional[float] = Field(default=None)
    crops: Optional[List[str]] = Field(default=None, sa_column=Column(JSONB, nullable=True))
    soil_type: Optional[str] = Field(default=None, max_length=50)
    irrigation_type: Optional[str] = Field(default=None, max_length=50)  # rainfed | drip | sprinkler
    
    # IoT device registration
    device_ids: Optional[List[str]] = Field(default=None, sa_column=Column(JSONB, nullable=True))
    
    # Status
    active: bool = Field(default=True)

    # Timestamps
    created_at: datetime = _created_at_field()
    updated_at: datetime = _updated_at_field()

    # Relationships
    farmer: Optional[Farmer] = Relationship(back_populates="farms")
    sensor_readings: List["SensorReading"] = Relationship(back_populates="farm")
    model_outputs: List["ModelOutput"] = Relationship(back_populates="farm")


class SensorReading(SQLModel, table=True):
    """
    IoT sensor readings from ESP32 devices.
    Designed for high-volume time-series ingestion.
    Partitioned by timestamp for performance.
    """
    __tablename__ = "sensor_readings"
    __table_args__ = (
        Index("ix_sensor_readings_farm_ts", "farm_id", "ts"),
        Index("ix_sensor_readings_device_ts", "device_id", "ts"),
    )

    id: Optional[int] = Field(default=None, sa_column=Column(BigInteger, primary_key=True, autoincrement=True))
    farm_id: int = Field(foreign_key="farms.id", index=True)
    device_id: str = Field(max_length=50, index=True)
    ts: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True),
    )
    
    # Sensor values (nullable — not all sensors report all values)
    temperature_c: Optional[float] = Field(default=None)
    humidity_pct: Optional[float] = Field(default=None)
    soil_moisture_pct: Optional[float] = Field(default=None)
    soil_ph: Optional[float] = Field(default=None)
    soil_nitrogen: Optional[float] = Field(default=None)
    soil_phosphorus: Optional[float] = Field(default=None)
    soil_potassium: Optional[float] = Field(default=None)
    light_lux: Optional[float] = Field(default=None)
    wind_speed_ms: Optional[float] = Field(default=None)
    rainfall_mm: Optional[float] = Field(default=None)
    pressure_hpa: Optional[float] = Field(default=None)
    co2_ppm: Optional[float] = Field(default=None)
    
    # Battery and connectivity
    battery_pct: Optional[float] = Field(default=None)
    rssi_dbm: Optional[int] = Field(default=None)
    
    # Raw payload for extensibility
    raw_payload: Optional[dict] = Field(default=None, sa_column=Column(JSONB, nullable=True))

    # Relationships
    farm: Optional[Farm] = Relationship(back_populates="sensor_readings")


class ModelOutput(SQLModel, table=True):
    """ML model prediction outputs"""
    __tablename__ = "model_outputs"
    __table_args__ = (
        Index("ix_model_outputs_farm_ts", "farm_id", "ts"),
    )

    model_config = {"protected_namespaces": ()}

    id: Optional[int] = Field(default=None, primary_key=True)
    farm_id: int = Field(foreign_key="farms.id", index=True)
    ts: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False),
    )
    
    # Predictions
    model_name: str = Field(max_length=100)  # e.g., "bloom_predictor_v2", "yield_forecast"
    model_version: Optional[str] = Field(default=None, max_length=50)
    
    yield_potential: Optional[float] = Field(default=None)  # tonnes/acre
    drought_risk: Optional[float] = Field(default=None)  # 0-1 probability
    bloom_probability: Optional[float] = Field(default=None)  # 0-1
    pest_risk: Optional[float] = Field(default=None)  # 0-1
    disease_risk: Optional[float] = Field(default=None)  # 0-1
    
    # Confidence and features
    confidence: Optional[float] = Field(default=None)
    input_features: Optional[dict] = Field(default=None, sa_column=Column(JSONB, nullable=True))
    
    # Image classification result (if from vision model)
    image_url: Optional[str] = Field(default=None, max_length=500)
    classification: Optional[str] = Field(default=None, max_length=100)
    classification_confidence: Optional[float] = Field(default=None)

    # Timestamps
    created_at: datetime = _created_at_field()
    updated_at: datetime = _updated_at_field()

    # Relationships
    farm: Optional[Farm] = Relationship(back_populates="model_outputs")


# ==============================================================================
# IoT Device Management
# ==============================================================================

class IoTDevice(SQLModel, table=True):
    """
    Registered IoT devices (ESP32 sensor arrays).
    Tracks device metadata, firmware version, assigned farm, and health status.
    """
    __tablename__ = "iot_devices"
    __table_args__ = (
        UniqueConstraint("device_id", name="uq_iot_devices_device_id"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    device_id: str = Field(max_length=50, index=True, unique=True)  # e.g., "esp32-001"
    farm_id: int = Field(foreign_key="farms.id", index=True)
    farmer_id: int = Field(foreign_key="farmers.id", index=True)

    # Device metadata
    device_type: str = Field(default="esp32", max_length=30)  # esp32 | esp32-cam | esp32-s3
    firmware_version: Optional[str] = Field(default=None, max_length=30)
    hardware_version: Optional[str] = Field(default=None, max_length=30)
    mac_address: Optional[str] = Field(default=None, max_length=17)

    # Sensor capabilities (which sensors are attached)
    has_soil_ph: bool = Field(default=False)
    has_soil_moisture: bool = Field(default=False)
    has_soil_npk: bool = Field(default=False)
    has_temperature: bool = Field(default=True)
    has_humidity: bool = Field(default=True)
    has_pressure: bool = Field(default=False)
    has_camera: bool = Field(default=False)
    has_light: bool = Field(default=False)
    has_rain_gauge: bool = Field(default=False)

    # Location (can differ from farm if device is placed at a specific field)
    latitude: Optional[float] = Field(default=None)
    longitude: Optional[float] = Field(default=None)

    # Health & connectivity
    last_seen: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))
    battery_pct: Optional[float] = Field(default=None)
    rssi_dbm: Optional[int] = Field(default=None)
    status: str = Field(default="active", max_length=20)  # active | offline | maintenance | decommissioned

    # Camera schedule (for weekly farm images)
    camera_capture_day: int = Field(default=0)  # 0=Monday ... 6=Sunday
    camera_capture_hour: int = Field(default=8)  # Hour of day (0-23, local time)

    # Timestamps
    created_at: datetime = _created_at_field()
    updated_at: datetime = _updated_at_field()


class CropImage(SQLModel, table=True):
    """
    Farm images captured by ESP32-CAM devices.
    Used for crop disease detection via BloomVisionCNN.
    Each image has a unique URL identifier for retrieval.
    """
    model_config = {"protected_namespaces": ()}
    __tablename__ = "crop_images"
    __table_args__ = (
        Index("ix_crop_images_farm_date", "farm_id", "captured_at"),
        Index("ix_crop_images_device_date", "device_id", "captured_at"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    image_uid: str = Field(max_length=64, unique=True, index=True)  # Unique URL identifier: farm1-esp32001-20260206T080000
    farm_id: int = Field(foreign_key="farms.id", index=True)
    device_id: str = Field(max_length=50, index=True)
    farmer_id: int = Field(foreign_key="farmers.id", index=True)

    # Image storage
    file_path: str = Field(max_length=500)  # Relative path: data/farm_images/farm_1/2026-02-06_esp32-001.jpg
    file_size_bytes: Optional[int] = Field(default=None)
    mime_type: str = Field(default="image/jpeg", max_length=30)
    image_width: Optional[int] = Field(default=None)
    image_height: Optional[int] = Field(default=None)

    # Capture metadata
    captured_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True),
    )
    capture_type: str = Field(default="weekly_scheduled", max_length=30)  # weekly_scheduled | manual | anomaly_triggered

    # Disease detection results (filled after inference)
    classification: Optional[str] = Field(default=None, max_length=100)  # healthy | leaf_blight | rust | aphid_damage | bloom_detected | wilting
    classification_confidence: Optional[float] = Field(default=None)
    all_probabilities: Optional[dict] = Field(default=None, sa_column=Column(JSONB, nullable=True))
    disease_detected: bool = Field(default=False)

    # Model metadata
    model_name: Optional[str] = Field(default=None, max_length=100)
    model_version: Optional[str] = Field(default=None, max_length=50)
    inference_time_ms: Optional[float] = Field(default=None)

    # Alert generated?
    alert_sent: bool = Field(default=False)
    alert_id: Optional[int] = Field(default=None)

    # Timestamps
    created_at: datetime = _created_at_field()
    updated_at: datetime = _updated_at_field()


class AgKnowledge(SQLModel, table=True):
    """
    Agricultural knowledge base with vector embeddings for RAG chatbot.
    Uses pgvector for semantic similarity search.
    """
    __tablename__ = "ag_knowledge"

    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Document content
    doc_title: Optional[str] = Field(default=None, max_length=255)
    doc_text: str = Field(sa_column=Column(Text, nullable=False))
    doc_source: Optional[str] = Field(default=None, max_length=255)  # URL or reference
    doc_category: Optional[str] = Field(default=None, max_length=50)  # crop_advice, pest, disease, etc.
    
    # Language
    language: str = Field(default="en", max_length=5)
    
    # Metadata for filtering
    crop: Optional[str] = Field(default=None, max_length=50, index=True)
    region: Optional[str] = Field(default=None, max_length=50)
    season: Optional[str] = Field(default=None, max_length=50)
    
    # Vector embedding (384-dim for sentence-transformers/all-MiniLM-L6-v2)
    embedding: Optional[List[float]] = Field(
        default=None,
        sa_column=Column(Vector(384), nullable=True),
    )
    
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )


class GEECountyData(SQLModel, table=True):
    """
    Google Earth Engine satellite data per county.
    Stores NDVI, rainfall, temperature from Sentinel-2, MODIS, CHIRPS, etc.
    """
    __tablename__ = "gee_county_data"
    __table_args__ = (
        Index("ix_gee_county_date", "county", "observation_date"),
        Index("ix_gee_subcounty_date", "sub_county", "observation_date"),
        UniqueConstraint("county", "sub_county", "observation_date", name="uq_county_subcounty_date"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    county: str = Field(max_length=50, index=True)
    sub_county: Optional[str] = Field(default=None, max_length=100, index=True)
    region: Optional[str] = Field(default=None, max_length=50)
    observation_date: date = Field(index=True)
    
    # Vegetation indices
    ndvi: Optional[float] = Field(default=None)
    ndwi: Optional[float] = Field(default=None)
    evi: Optional[float] = Field(default=None)
    savi: Optional[float] = Field(default=None)      # Soil-Adjusted Vegetation Index
    lai: Optional[float] = Field(default=None)       # Leaf Area Index
    
    # Climate data
    rainfall_mm: Optional[float] = Field(default=None)
    temperature_mean_c: Optional[float] = Field(default=None)
    temperature_max_c: Optional[float] = Field(default=None)
    temperature_min_c: Optional[float] = Field(default=None)
    evapotranspiration_mm: Optional[float] = Field(default=None)
    relative_humidity_pct: Optional[float] = Field(default=None)
    
    # Soil data
    soil_type: Optional[str] = Field(default=None, max_length=100)
    soil_moisture_pct: Optional[float] = Field(default=None)
    soil_organic_carbon: Optional[float] = Field(default=None)  # g/kg
    soil_ph: Optional[float] = Field(default=None)
    soil_clay_pct: Optional[float] = Field(default=None)
    soil_sand_pct: Optional[float] = Field(default=None)
    
    # Crop health & agriculture indices
    crop_water_stress_index: Optional[float] = Field(default=None)
    photosynthetic_activity: Optional[float] = Field(default=None)
    land_surface_temperature_c: Optional[float] = Field(default=None)
    
    # Bloom detection
    bloom_area_km2: Optional[float] = Field(default=None)
    bloom_percentage: Optional[float] = Field(default=None)
    bloom_probability: Optional[float] = Field(default=None)
    
    # Data quality
    cloud_cover_pct: Optional[float] = Field(default=None)
    data_source: Optional[str] = Field(default=None, max_length=100)
    is_real_data: bool = Field(default=True)
    
    # Raw satellite stats
    satellite_stats: Optional[dict] = Field(default=None, sa_column=Column(JSONB, nullable=True))
    
    # County coordinates (for map display)
    center_lat: Optional[float] = Field(default=None)
    center_lon: Optional[float] = Field(default=None)
    
    # Crops in this county
    main_crops: Optional[List[str]] = Field(default=None, sa_column=Column(JSONB, nullable=True))

    # Timestamps
    created_at: datetime = _created_at_field()
    updated_at: datetime = _updated_at_field()


class Alert(SQLModel, table=True):
    """Notification/alert sent to a farmer"""
    __tablename__ = "alerts"
    __table_args__ = (
        Index("ix_alerts_farmer_created", "farmer_id", "created_at"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    farmer_id: int = Field(foreign_key="farmers.id", index=True)
    
    # Alert details
    alert_type: str = Field(max_length=50)  # welcome | bloom_alert | crop_update | weather | custom | iot_anomaly
    severity: Optional[str] = Field(default=None, max_length=20)  # info | warning | critical
    message: str = Field(sa_column=Column(Text, nullable=False))
    message_sw: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))  # Swahili
    
    # Delivery
    channel: str = Field(default="sms", max_length=20)  # sms | ussd | email | push
    delivered: bool = Field(default=False)
    delivery_status: Optional[str] = Field(default=None, max_length=50)
    
    # Context
    crop: Optional[str] = Field(default=None, max_length=50)
    county: Optional[str] = Field(default=None, max_length=50)
    bloom_risk: Optional[str] = Field(default=None, max_length=20)  # Low | Moderate | High
    health_score: Optional[float] = Field(default=None)
    ndvi: Optional[float] = Field(default=None)
    data_source: Optional[str] = Field(default=None, max_length=100)
    
    # Metadata
    extra_data: Optional[dict] = Field(default=None, sa_column=Column("metadata", JSONB, nullable=True))

    # Timestamps
    created_at: datetime = _created_at_field()
    updated_at: datetime = _updated_at_field()

    # Relationships
    farmer: Optional[Farmer] = Relationship(back_populates="alerts")


class USSDSession(SQLModel, table=True):
    """Active USSD session state"""
    __tablename__ = "ussd_sessions"

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(max_length=100, unique=True, index=True)
    phone: str = Field(max_length=20, index=True)
    
    # Session state
    step: str = Field(default="language", max_length=50)
    data: Optional[dict] = Field(default=None, sa_column=Column(JSONB, nullable=True))
    is_registered: bool = Field(default=False)
    
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now()),
    )


class BloomEvent(SQLModel, table=True):
    """Detected bloom/flowering event"""
    __tablename__ = "bloom_events"
    __table_args__ = (
        Index("ix_bloom_events_region_ts", "region", "timestamp"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    region: Optional[str] = Field(default=None, max_length=50, index=True)
    county: Optional[str] = Field(default=None, max_length=50, index=True)
    sub_county: Optional[str] = Field(default=None, max_length=100, index=True)
    crop_type: Optional[str] = Field(default=None, max_length=50)
    
    # Event data
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), index=True),
    )
    bloom_intensity: Optional[float] = Field(default=None)
    bloom_area_km2: Optional[float] = Field(default=None)
    ndvi_mean: Optional[float] = Field(default=None)
    health_score: Optional[float] = Field(default=None)
    bloom_confidence: Optional[float] = Field(default=None)
    bloom_risk: Optional[str] = Field(default=None, max_length=20)
    
    # Location
    location_lat: Optional[float] = Field(default=None)
    location_lon: Optional[float] = Field(default=None)
    
    # Data source
    data_source: Optional[str] = Field(default=None, max_length=100)
    
    # Additional data
    bloom_months: Optional[List[int]] = Field(default=None, sa_column=Column(JSONB, nullable=True))
    bloom_scores: Optional[List[float]] = Field(default=None, sa_column=Column(JSONB, nullable=True))
    bloom_dates: Optional[List[str]] = Field(default=None, sa_column=Column(JSONB, nullable=True))

    # Timestamps
    created_at: datetime = _created_at_field()
    updated_at: datetime = _updated_at_field()


class Conversation(SQLModel, table=True):
    """A chat conversation/thread — groups ChatHistory messages together"""
    __tablename__ = "conversations"

    id: Optional[str] = Field(default=None, primary_key=True, max_length=36)  # UUID
    farmer_id: Optional[int] = Field(default=None, foreign_key="farmers.id", index=True)
    title: str = Field(default="New conversation", max_length=200)
    channel: str = Field(default="web", max_length=20)  # web | ussd | sms
    is_active: bool = Field(default=True)  # soft archive
    created_at: datetime = _created_at_field()
    updated_at: datetime = _updated_at_field()

    # Relationships
    farmer: Optional[Farmer] = Relationship(back_populates="conversations")
    messages: List["ChatHistory"] = Relationship(back_populates="conversation", sa_relationship_kwargs={"cascade": "all, delete-orphan", "order_by": "ChatHistory.timestamp"})


class ChatHistory(SQLModel, table=True):
    """Flora AI chatbot conversation history"""
    __tablename__ = "chat_history"
    __table_args__ = (
        Index("ix_chat_history_farmer_ts", "farmer_id", "timestamp"),
        Index("ix_chat_history_conversation", "conversation_id", "timestamp"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    conversation_id: Optional[str] = Field(default=None, foreign_key="conversations.id", max_length=36, index=True)
    farmer_id: Optional[int] = Field(default=None, foreign_key="farmers.id", index=True)
    phone: Optional[str] = Field(default=None, max_length=20, index=True)
    
    # Conversation
    role: str = Field(max_length=20)  # user | assistant
    message: str = Field(sa_column=Column(Text, nullable=False))
    response: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    reasoning: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    
    # Context
    via: str = Field(default="web", max_length=20)  # web | ussd | sms
    language: str = Field(default="en", max_length=5)
    
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), index=True),
    )

    # Relationships
    farmer: Optional[Farmer] = Relationship(back_populates="chat_history")
    conversation: Optional[Conversation] = Relationship(back_populates="messages")


class MessageTemplate(SQLModel, table=True):
    """Multilingual message templates for alerts and notifications"""
    __tablename__ = "message_templates"

    id: Optional[int] = Field(default=None, primary_key=True)
    template_id: str = Field(max_length=50, unique=True, index=True)
    category: str = Field(max_length=50, index=True)  # welcome | alert | advice
    
    # Template content in both languages
    content_en: str = Field(sa_column=Column(Text, nullable=False))
    content_sw: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    
    # Template variables (for reference)
    variables: Optional[List[str]] = Field(default=None, sa_column=Column(JSONB, nullable=True))
    
    active: bool = Field(default=True)
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )


class UserSession(SQLModel, table=True):
    """User authentication sessions"""
    __tablename__ = "user_sessions"

    id: Optional[int] = Field(default=None, primary_key=True)
    session_token: str = Field(max_length=100, unique=True, index=True)
    farmer_id: int = Field(foreign_key="farmers.id", index=True)
    phone: str = Field(max_length=20)
    
    expires_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )
    
    # Device/session info
    ip_address: Optional[str] = Field(default=None, max_length=45)
    user_agent: Optional[str] = Field(default=None, max_length=255)


class AgrovetProfile(SQLModel, table=True):
    """Agrovet shop owner profile — linked to base Farmer/User model"""
    __tablename__ = "agrovet_profiles"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="farmers.id", unique=True, index=True)
    
    # Shop details
    shop_name: str = Field(max_length=200)
    shop_description: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    business_registration_no: Optional[str] = Field(default=None, max_length=100)
    kra_pin: Optional[str] = Field(default=None, max_length=50)
    
    # Location
    shop_county: Optional[str] = Field(default=None, max_length=50, index=True)
    shop_sub_county: Optional[str] = Field(default=None, max_length=100)
    shop_address: Optional[str] = Field(default=None, max_length=255)
    shop_lat: Optional[float] = Field(default=None)
    shop_lon: Optional[float] = Field(default=None)
    
    # Categories sold
    categories: Optional[List[str]] = Field(default=None, sa_column=Column(JSONB, nullable=True))
    
    # Business metrics
    total_products: int = Field(default=0)
    total_orders: int = Field(default=0)
    total_revenue_kes: Decimal = Field(default=0, sa_column=Column(Numeric(12, 2), server_default="0"))
    average_rating: Optional[float] = Field(default=None)
    
    # Payment setup
    mpesa_till_number: Optional[str] = Field(default=None, max_length=20)
    mpesa_paybill: Optional[str] = Field(default=None, max_length=20)
    bank_name: Optional[str] = Field(default=None, max_length=100)
    bank_account: Optional[str] = Field(default=None, max_length=50)
    
    # Verification
    is_verified: bool = Field(default=False)
    verified_at: Optional[datetime] = Field(default=None)
    logo_url: Optional[str] = Field(default=None, max_length=500)
    active: bool = Field(default=True)

    created_at: datetime = _created_at_field()
    updated_at: datetime = _updated_at_field()

    user: Optional[Farmer] = Relationship(back_populates="agrovet_profile")


class BuyerProfile(SQLModel, table=True):
    """Buyer/trader profile — linked to base Farmer/User model"""
    __tablename__ = "buyer_profiles"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="farmers.id", unique=True, index=True)
    
    # Business details
    business_name: Optional[str] = Field(default=None, max_length=200)
    business_type: Optional[str] = Field(default=None, max_length=50)
    business_registration_no: Optional[str] = Field(default=None, max_length=100)
    
    # Location
    county: Optional[str] = Field(default=None, max_length=50, index=True)
    sub_county: Optional[str] = Field(default=None, max_length=100)
    address: Optional[str] = Field(default=None, max_length=255)
    
    # Preferences
    preferred_produce: Optional[List[str]] = Field(default=None, sa_column=Column(JSONB, nullable=True))
    preferred_counties: Optional[List[str]] = Field(default=None, sa_column=Column(JSONB, nullable=True))
    min_order_kg: Optional[float] = Field(default=None)
    
    # Metrics
    total_purchases: int = Field(default=0)
    total_spent_kes: Decimal = Field(default=0, sa_column=Column(Numeric(12, 2), server_default="0"))
    average_rating: Optional[float] = Field(default=None)
    
    is_verified: bool = Field(default=False)
    verified_at: Optional[datetime] = Field(default=None)
    active: bool = Field(default=True)

    created_at: datetime = _created_at_field()
    updated_at: datetime = _updated_at_field()

    user: Optional[Farmer] = Relationship(back_populates="buyer_profile")


class Transaction(SQLModel, table=True):
    """Payment transactions for orders and marketplace purchases"""
    __tablename__ = "transactions"
    __table_args__ = (
        Index("ix_transactions_buyer_ts", "buyer_id", "created_at"),
        Index("ix_transactions_seller_ts", "seller_id", "created_at"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    transaction_ref: str = Field(max_length=50, unique=True, index=True)
    
    buyer_id: int = Field(foreign_key="farmers.id", index=True)
    seller_id: Optional[int] = Field(default=None, foreign_key="farmers.id", index=True)
    
    transaction_type: str = Field(max_length=30)  # agrovet_order | marketplace_purchase
    order_id: Optional[int] = Field(default=None)
    amount_kes: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False))
    
    payment_method: str = Field(max_length=30)  # mpesa | airtel_money | bank_card | cash
    payment_status: str = Field(default="pending", max_length=20)
    payment_reference: Optional[str] = Field(default=None, max_length=100)
    mpesa_checkout_id: Optional[str] = Field(default=None, max_length=100)
    
    description: Optional[str] = Field(default=None, max_length=255)
    extra_data: Optional[dict] = Field(default=None, sa_column=Column(JSONB, nullable=True))

    created_at: datetime = _created_at_field()
    updated_at: datetime = _updated_at_field()


# ==============================================================================
# Agrovet & Marketplace Models (Enhanced)
# ==============================================================================

class AgrovetProduct(SQLModel, table=True):
    """Agricultural inputs catalog (seeds, fertilizers, pesticides, etc.)"""
    __tablename__ = "agrovet_products"

    id: Optional[int] = Field(default=None, primary_key=True)
    agrovet_id: Optional[int] = Field(default=None, foreign_key="farmers.id", index=True)
    name: str = Field(max_length=200)
    name_sw: Optional[str] = Field(default=None, max_length=200)
    description: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    category: str = Field(max_length=50, index=True)  # seeds | fertilizer | pesticide | tools | animal_feed
    
    # Pricing
    price_kes: Decimal = Field(sa_column=Column(Numeric(10, 2), nullable=False))
    unit: str = Field(max_length=20)  # kg | litre | bag | piece
    
    # Stock
    in_stock: bool = Field(default=True)
    stock_quantity: Optional[int] = Field(default=None)
    
    # Supplier
    supplier_name: Optional[str] = Field(default=None, max_length=200)
    supplier_location: Optional[str] = Field(default=None, max_length=200)
    supplier_county: Optional[str] = Field(default=None, max_length=50, index=True)
    supplier_sub_county: Optional[str] = Field(default=None, max_length=100, index=True)
    supplier_lat: Optional[float] = Field(default=None)
    supplier_lon: Optional[float] = Field(default=None)
    
    # Product details
    image_url: Optional[str] = Field(default=None, max_length=500)
    crop_applicable: Optional[List[str]] = Field(default=None, sa_column=Column(JSONB, nullable=True))
    
    active: bool = Field(default=True)

    # Timestamps
    created_at: datetime = _created_at_field()
    updated_at: datetime = _updated_at_field()


class AgrovetOrder(SQLModel, table=True):
    """Purchase orders for agrovet products"""
    __tablename__ = "agrovet_orders"

    id: Optional[int] = Field(default=None, primary_key=True)
    order_number: Optional[str] = Field(default=None, max_length=30, unique=True, index=True)  # ORD-XXXXXXXX
    farmer_id: int = Field(foreign_key="farmers.id", index=True)
    agrovet_id: Optional[int] = Field(default=None, foreign_key="farmers.id", index=True)
    product_id: int = Field(foreign_key="agrovet_products.id", index=True)
    
    quantity: int
    total_price_kes: Decimal = Field(sa_column=Column(Numeric(10, 2), nullable=False))
    
    # Payment
    payment_method: Optional[str] = Field(default=None, max_length=50)  # mpesa | airtel_money | bank_card | cash
    payment_status: str = Field(default="pending", max_length=20)  # pending | paid | failed | refunded
    payment_reference: Optional[str] = Field(default=None, max_length=100)
    
    # Delivery
    delivery_status: str = Field(default="pending", max_length=20)  # pending | processing | shipped | delivered
    delivery_address: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    
    # Order metadata
    order_source: str = Field(default="web", max_length=20)  # web | ussd | sms
    notes: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))

    # Timestamps
    created_at: datetime = _created_at_field()
    updated_at: datetime = _updated_at_field()


class MarketplaceListing(SQLModel, table=True):
    """Farmer produce listings for marketplace"""
    __tablename__ = "marketplace_listings"

    id: Optional[int] = Field(default=None, primary_key=True)
    farmer_id: int = Field(foreign_key="farmers.id", index=True)
    
    # Produce details
    produce_name: str = Field(max_length=200)
    produce_category: str = Field(max_length=50, index=True)  # grains | vegetables | fruits | dairy | livestock
    description: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    
    # Quantity and pricing
    quantity_available: float
    unit: str = Field(max_length=20)  # kg | bag | crate | piece | litre
    price_per_unit_kes: Decimal = Field(sa_column=Column(Numeric(10, 2), nullable=False))
    min_order_quantity: Optional[float] = Field(default=None)
    
    # Location
    county: Optional[str] = Field(default=None, max_length=50, index=True)
    sub_county: Optional[str] = Field(default=None, max_length=100)
    pickup_location: Optional[str] = Field(default=None, max_length=200)
    delivery_available: bool = Field(default=False)
    
    # Quality
    quality_grade: Optional[str] = Field(default=None, max_length=20)  # A | B | C
    harvest_date: Optional[date] = Field(default=None)
    image_url: Optional[str] = Field(default=None, max_length=500)
    
    # Status
    status: str = Field(default="active", max_length=20)  # active | sold | expired | draft
    expires_at: Optional[datetime] = Field(default=None)

    # Timestamps
    created_at: datetime = _created_at_field()
    updated_at: datetime = _updated_at_field()


class MarketplaceBid(SQLModel, table=True):
    """Buyer bids on marketplace produce listings"""
    __tablename__ = "marketplace_bids"

    id: Optional[int] = Field(default=None, primary_key=True)
    listing_id: int = Field(foreign_key="marketplace_listings.id", index=True)
    buyer_id: int = Field(foreign_key="farmers.id", index=True)  # Buyers are also farmers
    
    # Bid details
    quantity: float
    price_per_unit_kes: Decimal = Field(sa_column=Column(Numeric(10, 2), nullable=False))
    total_price_kes: Decimal = Field(sa_column=Column(Numeric(10, 2), nullable=False))
    
    # Status
    status: str = Field(default="pending", max_length=20)  # pending | accepted | rejected | completed | cancelled
    message: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    
    # Payment (on acceptance)
    payment_method: Optional[str] = Field(default=None, max_length=50)
    payment_status: Optional[str] = Field(default=None, max_length=20)
    payment_reference: Optional[str] = Field(default=None, max_length=100)

    # Timestamps
    created_at: datetime = _created_at_field()
    updated_at: datetime = _updated_at_field()


# ==============================================================================
# System Configuration
# ==============================================================================

class SystemConfig(SQLModel, table=True):
    """System-wide configuration key-value store"""
    __tablename__ = "system_config"

    id: Optional[int] = Field(default=None, primary_key=True)
    key: str = Field(max_length=100, unique=True, index=True)
    value: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    value_json: Optional[dict] = Field(default=None, sa_column=Column(JSONB, nullable=True))
    description: Optional[str] = Field(default=None, max_length=255)
    
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now()),
    )


class SMSDeliveryReport(SQLModel, table=True):
    """SMS delivery status reports"""
    __tablename__ = "sms_delivery_reports"

    id: Optional[int] = Field(default=None, primary_key=True)
    message_id: Optional[str] = Field(default=None, max_length=100, index=True)
    phone_number: Optional[str] = Field(default=None, max_length=20)
    status: Optional[str] = Field(default=None, max_length=50)
    network_code: Optional[str] = Field(default=None, max_length=20)
    retry_count: Optional[int] = Field(default=None)
    failure_reason: Optional[str] = Field(default=None, max_length=255)
    provider: str = Field(default="beem", max_length=20)  # beem | africastalking
    
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )


class MultimodalTrainingSample(SQLModel, table=True):
    """
    Labeled multimodal training samples for model retraining.

    Created when disease detection + soil telemetry + satellite data correlate,
    providing a confirmed labeled sample for the CNN and multimodal models.
    """
    __tablename__ = "multimodal_training_samples"

    id: Optional[int] = Field(default=None, primary_key=True)
    farm_id: int = Field(index=True)
    farmer_id: int = Field(index=True)

    # Image data
    image_uid: Optional[str] = Field(default=None, max_length=100, index=True)
    image_path: Optional[str] = Field(default=None, max_length=500)

    # Classification (ground truth label)
    label: str = Field(max_length=50, index=True)  # e.g. leaf_blight, rust, healthy
    label_source: str = Field(default="cnn_prediction", max_length=50)  # cnn_prediction | expert_verified | farmer_confirmed
    cnn_confidence: Optional[float] = Field(default=None)

    # Soil telemetry snapshot
    soil_ph: Optional[float] = Field(default=None)
    soil_moisture_pct: Optional[float] = Field(default=None)
    soil_nitrogen: Optional[float] = Field(default=None)
    soil_phosphorus: Optional[float] = Field(default=None)
    soil_potassium: Optional[float] = Field(default=None)
    temperature_c: Optional[float] = Field(default=None)
    humidity_pct: Optional[float] = Field(default=None)

    # Satellite snapshot
    ndvi: Optional[float] = Field(default=None)
    ndwi: Optional[float] = Field(default=None)
    rainfall_mm: Optional[float] = Field(default=None)
    land_surface_temp_c: Optional[float] = Field(default=None)

    # Correlation metadata
    correlation_score: Optional[float] = Field(default=None)  # How well the data sources agree
    used_in_training: bool = Field(default=False, index=True)
    training_epoch: Optional[int] = Field(default=None)
    notes: Optional[str] = Field(default=None, max_length=500)

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )
