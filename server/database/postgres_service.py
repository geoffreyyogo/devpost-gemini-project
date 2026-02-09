# pyright: reportArgumentType=false, reportCallIssue=false, reportAttributeAccessIssue=false, reportOptionalMemberAccess=false
"""
PostgreSQL Service for Smart Shamba Platform
Drop-in replacement for MongoDBService using SQLModel/PostgreSQL

All methods preserve the same interface & return shapes as MongoDBService
so callers (main.py, auth_service.py, etc.) can switch with minimal changes.
"""

import logging
import math
from datetime import datetime, timedelta, date as date_type
from typing import List, Dict, Optional

from sqlmodel import Session, select, func, col, or_, and_
from sqlalchemy import text, delete, update, desc, asc
from sqlalchemy.dialects.postgresql import insert as pg_insert

from database.connection import engine, get_sync_session, init_db
from database.models import (
    Farmer, Farm, SensorReading, ModelOutput, AgKnowledge,
    GEECountyData, Alert, USSDSession, BloomEvent, ChatHistory,
    MessageTemplate, AgrovetProduct, AgrovetOrder,
    MarketplaceListing, MarketplaceBid, UserSession, SystemConfig,
    SMSDeliveryReport, Conversation,
)

logger = logging.getLogger(__name__)


class PostgresService:
    """PostgreSQL service — API-compatible with MongoDBService"""

    def __init__(self):
        self._connected = False
        try:
            init_db()
            # Quick connectivity check
            with Session(engine) as session:
                session.exec(text("SELECT 1"))
            self._connected = True
            logger.info("✓ Connected to PostgreSQL successfully")
        except Exception as e:
            logger.warning(f"PostgreSQL connection failed: {e}")
            logger.info("Running in demo mode without PostgreSQL")

    # ------------------------------------------------------------------
    # Connection helpers
    # ------------------------------------------------------------------

    def is_connected(self) -> bool:
        return self._connected

    @property
    def db(self):
        """Compatibility shim — callers check `service.db is not None`"""
        return self if self._connected else None

    # ------------------------------------------------------------------
    # Farmer CRUD
    # ------------------------------------------------------------------

    def register_farmer(self, farmer_data: Dict) -> Dict:
        """Register a new farmer or update existing (upsert by phone)."""
        if not self._connected:
            return {"success": False, "message": "Database not available", "demo": True}

        try:
            with Session(engine) as session:
                existing = session.exec(
                    select(Farmer).where(Farmer.phone == farmer_data["phone"])
                ).first()

                if existing:
                    # Update existing farmer
                    for key, value in farmer_data.items():
                        if key in ("_id", "location", "created_at"):
                            continue
                        if hasattr(existing, key):
                            setattr(existing, key, value)
                    existing.updated_at = datetime.utcnow()
                    session.add(existing)
                    session.commit()
                    session.refresh(existing)
                    logger.info(f"✓ Farmer updated: {existing.name} ({existing.phone})")
                    return {
                        "success": True,
                        "farmer_id": str(existing.id),
                        "message": "Farmer updated successfully",
                        "is_new": False,
                    }
                else:
                    # Insert new farmer
                    farmer = Farmer(
                        phone=farmer_data["phone"],
                        name=farmer_data.get("name", ""),
                        email=farmer_data.get("email"),
                        password_hash=farmer_data.get("password_hash"),
                        password_salt=farmer_data.get("password_salt"),
                        region=farmer_data.get("region"),
                        county=farmer_data.get("county"),
                        sub_county=farmer_data.get("sub_county"),
                        language=farmer_data.get("language", "en"),
                        sms_enabled=farmer_data.get("sms_enabled", True),
                        registration_source=farmer_data.get("registration_source", "web"),
                        is_admin=farmer_data.get("is_admin", False),
                        active=farmer_data.get("active", True),
                        location_lat=farmer_data.get("location_lat"),
                        location_lon=farmer_data.get("location_lon"),
                        crops=farmer_data.get("crops"),
                        farm_size=farmer_data.get("farm_size"),
                        alert_count=farmer_data.get("alert_count", 0),
                        user_type=farmer_data.get("user_type", "farmer"),
                        display_id=farmer_data.get("display_id"),
                        avatar_url=farmer_data.get("avatar_url"),
                    )
                    session.add(farmer)
                    session.commit()
                    session.refresh(farmer)
                    logger.info(f"✓ Farmer registered: {farmer.name} ({farmer.phone})")
                    return {
                        "success": True,
                        "farmer_id": str(farmer.id),
                        "message": "Farmer registered successfully",
                        "is_new": True,
                    }

        except Exception as e:
            logger.error(f"Error registering farmer: {e}")
            return {"success": False, "message": str(e)}

    def get_farmer_by_phone(self, phone: str) -> Optional[Dict]:
        """Get farmer by phone number."""
        if not self._connected:
            return None
        try:
            with Session(engine) as session:
                farmer = session.exec(
                    select(Farmer).where(Farmer.phone == phone)
                ).first()
                if farmer:
                    return self._farmer_to_dict(farmer)
                return None
        except Exception as e:
            logger.error(f"Error getting farmer: {e}")
            return None

    def get_farmer_by_id(self, farmer_id: int) -> Optional[Dict]:
        """Get farmer by primary key."""
        if not self._connected:
            return None
        try:
            with Session(engine) as session:
                farmer = session.get(Farmer, farmer_id)
                if farmer:
                    return self._farmer_to_dict(farmer)
                return None
        except Exception as e:
            logger.error(f"Error getting farmer by id: {e}")
            return None

    def get_farmers_in_radius(self, lat: float, lon: float, radius_km: float = 50) -> List[Dict]:
        """
        Get farmers within radius using Haversine approximation.
        (Without PostGIS we compute bounding box + Haversine in SQL.)
        """
        if not self._connected:
            return []

        try:
            # Bounding box optimisation
            lat_delta = radius_km / 111.0
            lon_delta = radius_km / (111.0 * max(math.cos(math.radians(lat)), 0.01))

            with Session(engine) as session:
                stmt = (
                    select(Farmer)
                    .where(
                        Farmer.active == True,
                        Farmer.sms_enabled == True,
                        Farmer.location_lat.isnot(None),
                        Farmer.location_lon.isnot(None),
                        Farmer.location_lat.between(lat - lat_delta, lat + lat_delta),
                        Farmer.location_lon.between(lon - lon_delta, lon + lon_delta),
                    )
                )
                farmers = session.exec(stmt).all()

                result = []
                for f in farmers:
                    dist = self._haversine(lat, lon, f.location_lat, f.location_lon)
                    if dist <= radius_km:
                        d = self._farmer_to_dict(f)
                        d["distance_km"] = round(dist, 2)
                        result.append(d)

                result.sort(key=lambda x: x["distance_km"])
                return result

        except Exception as e:
            logger.error(f"Error getting farmers in radius: {e}")
            return []

    def get_farmers_by_crop(self, crop: str, region: str = None) -> List[Dict]:
        """Get farmers growing a specific crop."""
        if not self._connected:
            return []

        try:
            with Session(engine) as session:
                # JSONB @> containment operator
                stmt = select(Farmer).where(
                    Farmer.active == True,
                    Farmer.crops.op("@>")(f'["{crop}"]'),
                )
                if region:
                    stmt = stmt.where(Farmer.region == region)

                farmers = session.exec(stmt).all()
                return [self._farmer_to_dict(f) for f in farmers]
        except Exception as e:
            logger.error(f"Error getting farmers by crop: {e}")
            return []

    def delete_farmer(self, farmer_id: str) -> bool:
        """Delete a farmer by ID."""
        if not self._connected:
            return False
        try:
            with Session(engine) as session:
                farmer = session.get(Farmer, int(farmer_id))
                if farmer:
                    session.delete(farmer)
                    session.commit()
                    return True
                return False
        except Exception as e:
            logger.error(f"Error deleting farmer: {e}")
            return False

    def get_all_farmers(self, skip: int = 0, limit: int = 100) -> List[Dict]:
        """Get paginated list of all farmers."""
        if not self._connected:
            return []
        try:
            with Session(engine) as session:
                stmt = (
                    select(Farmer)
                    .order_by(desc(Farmer.created_at))
                    .offset(skip)
                    .limit(limit)
                )
                farmers = session.exec(stmt).all()
                return [self._farmer_to_dict(f) for f in farmers]
        except Exception as e:
            logger.error(f"Error listing farmers: {e}")
            return []

    # ------------------------------------------------------------------
    # Alert CRUD
    # ------------------------------------------------------------------

    def log_alert(self, farmer_id: str, alert_data: Dict) -> bool:
        """Log an alert sent to a farmer."""
        if not self._connected:
            return False
        try:
            with Session(engine) as session:
                alert = Alert(
                    farmer_id=int(farmer_id),
                    alert_type=alert_data.get("alert_type", "custom"),
                    severity=alert_data.get("severity", "info"),
                    message=alert_data.get("message", ""),
                    message_sw=alert_data.get("message_sw"),
                    channel=alert_data.get("channel", "sms"),
                    delivered=alert_data.get("delivered", False),
                    delivery_status=alert_data.get("delivery_status"),
                    crop=alert_data.get("crop"),
                    county=alert_data.get("county"),
                    bloom_risk=alert_data.get("bloom_risk"),
                    health_score=alert_data.get("health_score"),
                    ndvi=alert_data.get("ndvi"),
                    data_source=alert_data.get("data_source"),
                    metadata=alert_data.get("metadata"),
                )
                session.add(alert)

                # Update farmer alert count
                farmer = session.get(Farmer, int(farmer_id))
                if farmer:
                    farmer.alert_count = (farmer.alert_count or 0) + 1
                    farmer.last_alert = datetime.utcnow()
                    session.add(farmer)

                session.commit()
                return True
        except Exception as e:
            logger.error(f"Error logging alert: {e}")
            return False

    def get_recent_alerts(self, limit: int = 50) -> List[Dict]:
        """Get recent alerts."""
        if not self._connected:
            return []
        try:
            with Session(engine) as session:
                stmt = (
                    select(Alert)
                    .order_by(desc(Alert.created_at))
                    .limit(limit)
                )
                alerts = session.exec(stmt).all()
                return [self._alert_to_dict(a) for a in alerts]
        except Exception as e:
            logger.error(f"Error getting recent alerts: {e}")
            return []

    # ------------------------------------------------------------------
    # USSD Sessions
    # ------------------------------------------------------------------

    def save_ussd_session(self, session_id: str, session_data: Dict) -> bool:
        """Save or update a USSD session (upsert)."""
        if not self._connected:
            return False
        try:
            with Session(engine) as session:
                ussd = session.exec(
                    select(USSDSession).where(USSDSession.session_id == session_id)
                ).first()
                if ussd:
                    ussd.step = session_data.get("step", ussd.step)
                    ussd.data = session_data.get("data", ussd.data)
                    ussd.phone = session_data.get("phone", ussd.phone)
                    ussd.is_registered = session_data.get("is_registered", ussd.is_registered)
                    ussd.updated_at = datetime.utcnow()
                else:
                    ussd = USSDSession(
                        session_id=session_id,
                        phone=session_data.get("phone", ""),
                        step=session_data.get("step", "language"),
                        data=session_data.get("data"),
                        is_registered=session_data.get("is_registered", False),
                    )
                session.add(ussd)
                session.commit()
                return True
        except Exception as e:
            logger.error(f"Error saving USSD session: {e}")
            return False

    def get_ussd_session(self, session_id: str) -> Optional[Dict]:
        """Get USSD session data."""
        if not self._connected:
            return None
        try:
            with Session(engine) as session:
                ussd = session.exec(
                    select(USSDSession).where(USSDSession.session_id == session_id)
                ).first()
                if ussd:
                    return {
                        "session_id": ussd.session_id,
                        "phone": ussd.phone,
                        "step": ussd.step,
                        "data": ussd.data or {},
                        "is_registered": ussd.is_registered,
                        "created_at": ussd.created_at,
                        "updated_at": ussd.updated_at,
                    }
                return None
        except Exception as e:
            logger.error(f"Error getting USSD session: {e}")
            return None

    # ------------------------------------------------------------------
    # Bloom Events
    # ------------------------------------------------------------------

    def save_bloom_event(self, event_data: Dict) -> Optional[str]:
        """Save a bloom event detection."""
        if not self._connected:
            return None
        try:
            with Session(engine) as session:
                event = BloomEvent(
                    region=event_data.get("region"),
                    county=event_data.get("county"),
                    sub_county=event_data.get("sub_county"),
                    crop_type=event_data.get("crop_type"),
                    bloom_intensity=event_data.get("bloom_intensity"),
                    bloom_area_km2=event_data.get("bloom_area_km2"),
                    ndvi_mean=event_data.get("ndvi_mean"),
                    health_score=event_data.get("health_score"),
                    bloom_confidence=event_data.get("bloom_confidence"),
                    bloom_risk=event_data.get("bloom_risk"),
                    location_lat=event_data.get("location_lat"),
                    location_lon=event_data.get("location_lon"),
                    data_source=event_data.get("data_source"),
                    bloom_months=event_data.get("bloom_months"),
                    bloom_scores=event_data.get("bloom_scores"),
                    bloom_dates=event_data.get("bloom_dates"),
                )
                session.add(event)
                session.commit()
                session.refresh(event)
                logger.info(
                    f"✓ Bloom event saved: {event.crop_type} in {event.region}"
                )
                return str(event.id)
        except Exception as e:
            logger.error(f"Error saving bloom event: {e}")
            return None

    def get_recent_bloom_events(self, days: int = 7, region: str = None) -> List[Dict]:
        """Get recent bloom events."""
        if not self._connected:
            return []
        try:
            with Session(engine) as session:
                cutoff = datetime.utcnow() - timedelta(days=days)
                stmt = select(BloomEvent).where(BloomEvent.timestamp >= cutoff)
                if region:
                    stmt = stmt.where(BloomEvent.region == region)
                stmt = stmt.order_by(desc(BloomEvent.timestamp))
                events = session.exec(stmt).all()
                return [self._bloom_event_to_dict(e) for e in events]
        except Exception as e:
            logger.error(f"Error getting bloom events: {e}")
            return []

    # ------------------------------------------------------------------
    # Statistics
    # ------------------------------------------------------------------

    def get_farmer_statistics(self) -> Dict:
        """Get overall farmer statistics."""
        if not self._connected:
            return {
                "total_farmers": 0,
                "active_farmers": 0,
                "farmers_by_region": {},
                "farmers_by_crop": {},
                "total_alerts_sent": 0,
            }
        try:
            with Session(engine) as session:
                total = session.exec(select(func.count(Farmer.id))).one()
                active = session.exec(
                    select(func.count(Farmer.id)).where(Farmer.active == True)
                ).one()
                total_alerts = session.exec(select(func.count(Alert.id))).one()

                # By region
                region_rows = session.exec(
                    select(Farmer.region, func.count(Farmer.id))
                    .where(Farmer.region.isnot(None))
                    .group_by(Farmer.region)
                ).all()
                by_region = {r: c for r, c in region_rows}

                # By registration source
                src_rows = session.exec(
                    select(Farmer.registration_source, func.count(Farmer.id))
                    .group_by(Farmer.registration_source)
                ).all()
                by_source = {(s or "unknown"): c for s, c in src_rows}

                # By crop — unnest JSONB array
                crop_rows = session.exec(
                    text(
                        "SELECT crop, COUNT(*) "
                        "FROM farmers, jsonb_array_elements_text(crops) AS crop "
                        "GROUP BY crop"
                    )
                ).all()
                by_crop = {r[0]: r[1] for r in crop_rows}

                return {
                    "total_farmers": total,
                    "active_farmers": active,
                    "farmers_by_region": by_region,
                    "farmers_by_crop": by_crop,
                    "farmers_by_source": by_source,
                    "total_alerts_sent": total_alerts,
                }
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}

    def get_recent_registrations(self, days: int = 7, limit: int = 10) -> List[Dict]:
        """Get recent farmer registrations."""
        if not self._connected:
            return []
        try:
            with Session(engine) as session:
                cutoff = datetime.utcnow() - timedelta(days=days)
                stmt = (
                    select(Farmer)
                    .where(Farmer.created_at >= cutoff)
                    .order_by(desc(Farmer.created_at))
                    .limit(limit)
                )
                farmers = session.exec(stmt).all()
                return [self._farmer_to_dict(f) for f in farmers]
        except Exception as e:
            logger.error(f"Error getting recent registrations: {e}")
            return []

    # ------------------------------------------------------------------
    # Chat History & Conversations
    # ------------------------------------------------------------------

    def create_conversation(self, farmer_id: int, title: str = "New conversation",
                            channel: str = "web") -> Optional[Dict]:
        """Create a new conversation thread."""
        if not self._connected:
            return None
        try:
            import uuid
            with Session(engine) as session:
                conv = Conversation(
                    id=str(uuid.uuid4()),
                    farmer_id=farmer_id,
                    title=title[:200],
                    channel=channel,
                    is_active=True,
                )
                session.add(conv)
                session.commit()
                session.refresh(conv)
                return {
                    "id": conv.id,
                    "farmer_id": conv.farmer_id,
                    "title": conv.title,
                    "channel": conv.channel,
                    "is_active": conv.is_active,
                    "created_at": conv.created_at.isoformat() if conv.created_at else None,
                    "updated_at": conv.updated_at.isoformat() if conv.updated_at else None,
                }
        except Exception as e:
            logger.error(f"Error creating conversation: {e}")
            return None

    def get_conversations(self, farmer_id: int, limit: int = 50) -> List[Dict]:
        """Get all conversations for a farmer, most recent first."""
        if not self._connected:
            return []
        try:
            with Session(engine) as session:
                stmt = (
                    select(Conversation)
                    .where(Conversation.farmer_id == farmer_id)
                    .where(Conversation.is_active == True)
                    .order_by(desc(Conversation.updated_at))
                    .limit(limit)
                )
                rows = session.exec(stmt).all()
                result = []
                for c in rows:
                    # Get last message preview and message count
                    last_msg = session.exec(
                        select(ChatHistory)
                        .where(ChatHistory.conversation_id == c.id)
                        .order_by(desc(ChatHistory.timestamp))
                        .limit(1)
                    ).first()
                    msg_count = session.exec(
                        select(func.count(ChatHistory.id))
                        .where(ChatHistory.conversation_id == c.id)
                    ).one()
                    result.append({
                        "id": c.id,
                        "title": c.title,
                        "channel": c.channel,
                        "message_count": msg_count or 0,
                        "last_message": last_msg.message[:100] if last_msg else None,
                        "last_response": last_msg.response[:100] if last_msg and last_msg.response else None,
                        "created_at": c.created_at.isoformat() if c.created_at else None,
                        "updated_at": c.updated_at.isoformat() if c.updated_at else None,
                    })
                return result
        except Exception as e:
            logger.error(f"Error fetching conversations: {e}")
            return []

    def get_conversation_messages(self, conversation_id: str, farmer_id: int,
                                  limit: int = 100) -> List[Dict]:
        """Get messages in a conversation, chronological order."""
        if not self._connected:
            return []
        try:
            with Session(engine) as session:
                # Verify ownership
                conv = session.exec(
                    select(Conversation)
                    .where(Conversation.id == conversation_id)
                    .where(Conversation.farmer_id == farmer_id)
                ).first()
                if not conv:
                    return []
                
                stmt = (
                    select(ChatHistory)
                    .where(ChatHistory.conversation_id == conversation_id)
                    .order_by(asc(ChatHistory.timestamp))
                    .limit(limit)
                )
                rows = session.exec(stmt).all()
                return [
                    {
                        "id": r.id,
                        "role": r.role,
                        "message": r.message,
                        "response": r.response,
                        "reasoning": r.reasoning,
                        "via": r.via,
                        "timestamp": r.timestamp.isoformat() if r.timestamp else None,
                    }
                    for r in rows
                ]
        except Exception as e:
            logger.error(f"Error getting conversation messages: {e}")
            return []

    def update_conversation_title(self, conversation_id: str, farmer_id: int,
                                   title: str) -> bool:
        """Update a conversation's title."""
        if not self._connected:
            return False
        try:
            with Session(engine) as session:
                conv = session.exec(
                    select(Conversation)
                    .where(Conversation.id == conversation_id)
                    .where(Conversation.farmer_id == farmer_id)
                ).first()
                if not conv:
                    return False
                conv.title = title[:200]
                conv.updated_at = datetime.utcnow()
                session.add(conv)
                session.commit()
                return True
        except Exception as e:
            logger.error(f"Error updating conversation title: {e}")
            return False

    def archive_conversation(self, conversation_id: str, farmer_id: int) -> bool:
        """Soft-delete (archive) a conversation."""
        if not self._connected:
            return False
        try:
            with Session(engine) as session:
                conv = session.exec(
                    select(Conversation)
                    .where(Conversation.id == conversation_id)
                    .where(Conversation.farmer_id == farmer_id)
                ).first()
                if not conv:
                    return False
                conv.is_active = False
                session.add(conv)
                session.commit()
                return True
        except Exception as e:
            logger.error(f"Error archiving conversation: {e}")
            return False

    def save_chat_message(self, phone: str, role: str, message: str,
                          response: Optional[str] = None, farmer_id: Optional[int] = None,
                          via: str = "web", language: str = "en",
                          conversation_id: Optional[str] = None,
                          reasoning: Optional[str] = None) -> Optional[str]:
        """Save a chat history entry. Returns conversation_id (creates one if needed)."""
        if not self._connected:
            return None
        try:
            import uuid
            with Session(engine) as session:
                # Auto-create conversation if not provided
                if not conversation_id and farmer_id:
                    conv_id = str(uuid.uuid4())
                    conv = Conversation(
                        id=conv_id,
                        farmer_id=farmer_id,
                        title=(message[:50] if message else "New conversation"),
                        channel=via,
                        is_active=True,
                    )
                    session.add(conv)
                    session.flush()
                    conversation_id = conv_id

                entry = ChatHistory(
                    conversation_id=conversation_id,
                    farmer_id=farmer_id,
                    phone=phone,
                    role=role,
                    message=message,
                    response=response,
                    reasoning=reasoning,
                    via=via,
                    language=language,
                )
                session.add(entry)

                # Update conversation timestamp
                if conversation_id:
                    conv = session.get(Conversation, conversation_id)
                    if conv:
                        conv.updated_at = datetime.utcnow()

                session.commit()
                return conversation_id
        except Exception as e:
            logger.error(f"Error saving chat message: {e}")
            return None

    def get_chat_history(self, phone: str = None, farmer_id: int = None,
                         limit: int = 20) -> List[Dict]:
        """Get chat history for a phone or farmer (flat, for backwards compat)."""
        if not self._connected:
            return []
        try:
            with Session(engine) as session:
                stmt = select(ChatHistory)
                if phone:
                    stmt = stmt.where(ChatHistory.phone == phone)
                elif farmer_id:
                    stmt = stmt.where(ChatHistory.farmer_id == farmer_id)
                stmt = stmt.order_by(desc(ChatHistory.timestamp)).limit(limit)
                rows = session.exec(stmt).all()
                return [
                    {
                        "id": r.id,
                        "conversation_id": r.conversation_id,
                        "phone": r.phone,
                        "role": r.role,
                        "message": r.message,
                        "response": r.response,
                        "reasoning": r.reasoning,
                        "via": r.via,
                        "language": r.language,
                        "timestamp": r.timestamp.isoformat() if r.timestamp else None,
                    }
                    for r in reversed(rows)  # chronological order
                ]
        except Exception as e:
            logger.error(f"Error getting chat history: {e}")
            return []

    def get_active_conversation_by_phone(self, phone: str) -> Optional[Dict]:
        """Get the most recent active conversation for a phone number (for SMS continuity)."""
        if not self._connected:
            return None
        try:
            with Session(engine) as session:
                # Find farmer by phone
                farmer = session.exec(
                    select(Farmer).where(Farmer.phone == phone)
                ).first()
                if not farmer:
                    return None
                # Get most recent active conversation within the last 24h
                cutoff = datetime.utcnow() - timedelta(hours=24)
                conv = session.exec(
                    select(Conversation)
                    .where(Conversation.farmer_id == farmer.id)
                    .where(Conversation.is_active == True)
                    .where(Conversation.updated_at >= cutoff)
                    .order_by(desc(Conversation.updated_at))
                    .limit(1)
                ).first()
                if not conv:
                    return None
                return {
                    "id": conv.id,
                    "farmer_id": conv.farmer_id,
                    "title": conv.title,
                    "channel": conv.channel,
                }
        except Exception as e:
            logger.error(f"Error getting active conversation: {e}")
            return None

    # ------------------------------------------------------------------
    # Message Templates
    # ------------------------------------------------------------------

    def get_template(self, template_id: str, language: str = "en") -> Optional[Dict]:
        """Get message template by ID."""
        if not self._connected:
            return None
        try:
            with Session(engine) as session:
                tmpl = session.exec(
                    select(MessageTemplate).where(
                        MessageTemplate.template_id == template_id
                    )
                ).first()
                if tmpl:
                    return {
                        "template_id": tmpl.template_id,
                        "category": tmpl.category,
                        "content_en": tmpl.content_en,
                        "content_sw": tmpl.content_sw,
                        "variables": tmpl.variables,
                    }
                return None
        except Exception as e:
            logger.error(f"Error getting template: {e}")
            return None

    # ------------------------------------------------------------------
    # Agricultural Advice (simple text KB — future: use AgKnowledge RAG)
    # ------------------------------------------------------------------

    def get_agricultural_advice(self, crop: str, stage: str, language: str = "en") -> Optional[str]:
        """Placeholder — returns None; advice currently in SmartAlertService."""
        return None

    # ------------------------------------------------------------------
    # GEE County Data
    # ------------------------------------------------------------------

    def save_county_data(self, county: str, obs_date: date_type, data: Dict,
                         sub_county: str = None) -> bool:
        """Upsert county/sub-county satellite data."""
        if not self._connected:
            return False
        try:
            with Session(engine) as session:
                stmt = select(GEECountyData).where(
                    GEECountyData.county == county,
                    GEECountyData.observation_date == obs_date,
                )
                if sub_county:
                    stmt = stmt.where(GEECountyData.sub_county == sub_county)
                else:
                    stmt = stmt.where(GEECountyData.sub_county.is_(None))
                existing = session.exec(stmt).first()
                if existing:
                    for k, v in data.items():
                        if hasattr(existing, k):
                            setattr(existing, k, v)
                    existing.updated_at = datetime.utcnow()
                    session.add(existing)
                else:
                    row = GEECountyData(
                        county=county,
                        sub_county=sub_county,
                        observation_date=obs_date,
                        **{k: v for k, v in data.items() if hasattr(GEECountyData, k)},
                    )
                    session.add(row)
                session.commit()
                return True
        except Exception as e:
            logger.error(f"Error saving county data: {e}")
            return False

    def get_county_data(self, county: str, days: int = 30,
                        sub_county: str = None) -> List[Dict]:
        """Get recent GEE data for a county/sub-county."""
        if not self._connected:
            return []
        try:
            with Session(engine) as session:
                cutoff = date_type.today() - timedelta(days=days)
                stmt = (
                    select(GEECountyData)
                    .where(
                        GEECountyData.county == county,
                        GEECountyData.observation_date >= cutoff,
                    )
                )
                if sub_county:
                    stmt = stmt.where(GEECountyData.sub_county == sub_county)
                stmt = stmt.order_by(desc(GEECountyData.observation_date))
                rows = session.exec(stmt).all()
                return [self._county_data_to_dict(r) for r in rows]
        except Exception as e:
            logger.error(f"Error getting county data: {e}")
            return []

    def get_all_counties_latest(self) -> List[Dict]:
        """Get latest data for all counties."""
        if not self._connected:
            return []
        try:
            with Session(engine) as session:
                # Subquery for max date per county
                subq = (
                    select(
                        GEECountyData.county,
                        func.max(GEECountyData.observation_date).label("max_date"),
                    )
                    .group_by(GEECountyData.county)
                    .subquery()
                )
                stmt = (
                    select(GEECountyData)
                    .join(
                        subq,
                        and_(
                            GEECountyData.county == subq.c.county,
                            GEECountyData.observation_date == subq.c.max_date,
                        ),
                    )
                    .order_by(GEECountyData.county)
                )
                rows = session.exec(stmt).all()
                return [self._county_data_to_dict(r) for r in rows]
        except Exception as e:
            logger.error(f"Error getting all counties latest: {e}")
            return []

    def get_map_data(self) -> Dict:
        """Get formatted map marker data from PostgreSQL for all counties."""
        from kenya_counties_config import KENYA_COUNTIES
        counties_latest = self.get_all_counties_latest()
        if not counties_latest:
            return {"markers": [], "last_updated": None, "has_real_data": False}

        markers = []
        for c in counties_latest:
            county_key = c["county"].lower().replace(" ", "_").replace("-", "_").replace("'", "")
            config = KENYA_COUNTIES.get(county_key, {})
            coords = config.get("coordinates", {})
            lat = c.get("center_lat") or coords.get("lat", 0)
            lon = c.get("center_lon") or coords.get("lon", 0)
            markers.append({
                "name": c["county"],
                "lat": lat,
                "lon": lon,
                "bloom_probability": f"{(c.get('bloom_probability') or 0):.0f}%",
                "temperature": f"{(c.get('temperature_mean_c') or 0):.1f}°C",
                "rainfall": f"{(c.get('rainfall_mm') or 0):.1f}mm",
                "ndvi": f"{(c.get('ndvi') or 0):.3f}",
                "confidence": "high" if c.get("is_real_data") else "low",
                "is_real_data": c.get("is_real_data", False),
                "data_source": "NASA Satellite" if c.get("is_real_data") else "Simulated",
                "bloom_area_km2": c.get("bloom_area_km2", 0),
                "bloom_percentage": c.get("bloom_percentage", 0),
                "bloom_prediction": c.get("bloom_probability", 0),
                "message": "N/A",
            })

        last_updated = None
        dates = [c.get("observation_date") for c in counties_latest if c.get("observation_date")]
        if dates:
            last_updated = max(dates)

        return {
            "markers": markers,
            "last_updated": last_updated,
            "has_real_data": any(m["is_real_data"] for m in markers),
        }

    def get_climate_summary_stats(self) -> Dict:
        """Aggregate climate statistics from PostgreSQL."""
        counties = self.get_all_counties_latest()
        if not counties:
            return {
                "avg_bloom_level": "N/A",
                "avg_temperature": "N/A",
                "avg_rainfall": "N/A",
                "total_bloom_area": "N/A",
                "bloom_level_delta": "0.0%",
                "temperature_delta": "0.0°C",
                "rainfall_delta": "0.0mm",
            }

        bloom_pcts = [c["bloom_percentage"] for c in counties if c.get("bloom_percentage") is not None]
        temps = [c["temperature_mean_c"] for c in counties if c.get("temperature_mean_c") is not None]
        rains = [c["rainfall_mm"] for c in counties if c.get("rainfall_mm") is not None]
        areas = [c["bloom_area_km2"] for c in counties if c.get("bloom_area_km2") is not None]

        avg_bloom = sum(bloom_pcts) / len(bloom_pcts) if bloom_pcts else 0
        avg_temp = sum(temps) / len(temps) if temps else 0
        avg_rain = sum(rains) / len(rains) if rains else 0
        total_area = sum(areas) if areas else 0

        # Get previous stats from system_config for delta calculation
        prev = self.get_config("previous_climate_stats") or {}
        prev_bloom = float(prev.get("bloom", 0))
        prev_temp = float(prev.get("temp", 0))
        prev_rain = float(prev.get("rain", 0))

        bd = avg_bloom - prev_bloom
        td = avg_temp - prev_temp
        rd = avg_rain - prev_rain

        # Save current as previous
        self.set_config("previous_climate_stats", {
            "bloom": avg_bloom, "temp": avg_temp, "rain": avg_rain,
            "ts": datetime.utcnow().isoformat(),
        })

        return {
            "avg_bloom_level": f"{avg_bloom:.1f}%" if bloom_pcts else "N/A",
            "avg_temperature": f"{avg_temp:.1f}°C" if temps else "N/A",
            "avg_rainfall": f"{avg_rain:.1f}mm" if rains else "N/A",
            "total_bloom_area": f"{total_area:.0f} km²" if areas else "N/A",
            "bloom_level_delta": f"{'+' if bd >= 0 else ''}{bd:.1f}%",
            "temperature_delta": f"{'+' if td >= 0 else ''}{td:.1f}°C",
            "rainfall_delta": f"{'+' if rd >= 0 else ''}{rd:.1f}mm",
        }

    def get_data_freshness(self) -> Dict:
        """Get data freshness information from PostgreSQL."""
        if not self._connected:
            return {
                "is_fresh": False, "last_updated": "Never",
                "age_hours": None,
                "message": "Database not connected.",
            }
        try:
            with Session(engine) as session:
                result = session.exec(
                    select(func.max(GEECountyData.updated_at))
                ).first()
                if not result:
                    return {
                        "is_fresh": False, "last_updated": "Never",
                        "age_hours": None,
                        "message": "No satellite data in database yet. Run data fetch.",
                    }
                # Handle timezone-aware vs naive datetimes
                now = datetime.utcnow()
                last = result.replace(tzinfo=None) if result.tzinfo else result
                age_hours = (now - last).total_seconds() / 3600
                is_fresh = age_hours <= 72  # Satellite data refreshed every few days
                if age_hours < 1:
                    age_str = f"{int(age_hours * 60)} minutes"
                elif age_hours < 24:
                    hrs = int(age_hours)
                    age_str = f"{hrs} hour{'s' if hrs != 1 else ''}"
                elif age_hours < 48:
                    hrs = int(age_hours)
                    remaining = hrs % 24
                    age_str = f"1 day, {remaining} hour{'s' if remaining != 1 else ''}"
                else:
                    days = int(age_hours / 24)
                    remaining = int(age_hours % 24)
                    if remaining > 0:
                        age_str = f"{days} day{'s' if days != 1 else ''}, {remaining} hr{'s' if remaining != 1 else ''}"
                    else:
                        age_str = f"{days} day{'s' if days != 1 else ''}"
                return {
                    "is_fresh": is_fresh,
                    "last_updated": result.strftime("%Y-%m-%d %H:%M:%S"),
                    "age_hours": age_hours,
                    "age_str": age_str,
                    "message": "Data is fresh" if is_fresh else "Data may be outdated. Consider refreshing.",
                }
        except Exception as e:
            logger.error(f"Error getting data freshness: {e}")
            return {
                "is_fresh": False, "last_updated": "Error",
                "age_hours": None, "message": f"Error: {e}",
            }

    def get_county_details(self, county_name: str) -> Dict:
        """Get detailed county data from PostgreSQL (replaces JSON file reads)."""
        from kenya_counties_config import KENYA_COUNTIES
        county_key = county_name.lower().replace(" ", "_").replace("-", "_").replace("'", "")
        config = KENYA_COUNTIES.get(county_key, {})
        rows = self.get_county_data(county_name, days=90)

        if not rows:
            # Return basic config-based info
            if config:
                return {
                    "county_name": config.get("name", county_name),
                    "county_id": county_key,
                    "region": config.get("region", "unknown"),
                    "coordinates": config.get("coordinates", {}),
                    "main_crops": config.get("main_crops", []),
                    "avg_temp_c": 25.0,
                    "total_rainfall_mm": 50.0,
                    "ndvi": 0.6,
                    "satellite_data": {},
                    "bloom_data": {},
                }
            return {"error": f"No data available for {county_name}"}

        latest = rows[0]
        return {
            "county_name": config.get("name", county_name),
            "county_id": county_key,
            "region": latest.get("region") or config.get("region", "unknown"),
            "coordinates": config.get("coordinates", {
                "lat": latest.get("center_lat", 0),
                "lon": latest.get("center_lon", 0),
            }),
            "main_crops": latest.get("main_crops") or config.get("main_crops", []),
            "avg_temp_c": latest.get("temperature_mean_c", 25.0),
            "total_rainfall_mm": latest.get("rainfall_mm", 50.0),
            "ndvi": latest.get("ndvi", 0.6),
            "satellite_data": {
                "ndvi": latest.get("ndvi"),
                "ndwi": latest.get("ndwi"),
                "evi": latest.get("evi"),
                "savi": latest.get("savi"),
                "lai": latest.get("lai"),
                "temperature_c": latest.get("temperature_mean_c"),
                "temperature_max_c": latest.get("temperature_max_c"),
                "temperature_min_c": latest.get("temperature_min_c"),
                "rainfall_mm": latest.get("rainfall_mm"),
                "soil_moisture_pct": latest.get("soil_moisture_pct"),
                "soil_ph": latest.get("soil_ph"),
                "evapotranspiration_mm": latest.get("evapotranspiration_mm"),
                "observation_date": latest.get("observation_date"),
                "data_source": latest.get("data_source"),
                "is_real_data": latest.get("is_real_data", False),
                "cloud_cover_pct": latest.get("cloud_cover_pct"),
            },
            "bloom_data": {
                "bloom_probability": latest.get("bloom_probability", 0),
                "bloom_percentage": latest.get("bloom_percentage", 0),
                "bloom_area_km2": latest.get("bloom_area_km2", 0),
            },
            "history": rows[:30],
        }

    def get_sub_county_details(self, county_name: str, sub_county_name: str) -> Dict:
        """Get detailed sub-county data from PostgreSQL."""
        from kenya_counties_config import KENYA_COUNTIES
        county_key = county_name.lower().replace(" ", "_").replace("-", "_").replace("'", "")
        config = KENYA_COUNTIES.get(county_key, {})
        rows = self.get_county_data(county_name, days=90, sub_county=sub_county_name)

        if not rows:
            return {"error": f"No sub-county data available for {sub_county_name}, {county_name}"}

        latest = rows[0]
        return {
            "county_name": config.get("name", county_name),
            "county_id": county_key,
            "sub_county": sub_county_name,
            "region": latest.get("region") or config.get("region", "unknown"),
            "coordinates": config.get("coordinates", {
                "lat": latest.get("center_lat", 0),
                "lon": latest.get("center_lon", 0),
            }),
            "main_crops": latest.get("main_crops") or config.get("main_crops", []),
            "avg_temp_c": latest.get("temperature_mean_c", 25.0),
            "total_rainfall_mm": latest.get("rainfall_mm", 50.0),
            "ndvi": latest.get("ndvi", 0.6),
            "satellite_data": {
                "ndvi": latest.get("ndvi"),
                "ndwi": latest.get("ndwi"),
                "evi": latest.get("evi"),
                "savi": latest.get("savi"),
                "lai": latest.get("lai"),
                "temperature_c": latest.get("temperature_mean_c"),
                "temperature_max_c": latest.get("temperature_max_c"),
                "temperature_min_c": latest.get("temperature_min_c"),
                "rainfall_mm": latest.get("rainfall_mm"),
                "soil_moisture_pct": latest.get("soil_moisture_pct"),
                "soil_ph": latest.get("soil_ph"),
                "evapotranspiration_mm": latest.get("evapotranspiration_mm"),
                "observation_date": latest.get("observation_date"),
                "data_source": latest.get("data_source"),
                "is_real_data": latest.get("is_real_data", False),
                "cloud_cover_pct": latest.get("cloud_cover_pct"),
            },
            "bloom_data": {
                "bloom_probability": latest.get("bloom_probability", 0),
                "bloom_percentage": latest.get("bloom_percentage", 0),
                "bloom_area_km2": latest.get("bloom_area_km2", 0),
            },
            "history": rows[:30],
        }

    # ------------------------------------------------------------------
    # User Sessions (Auth)
    # ------------------------------------------------------------------

    def create_session(self, session_token: str, farmer_id: int,
                       phone: str, expires_at: datetime,
                       ip_address: str = None, user_agent: str = None) -> bool:
        """Create a new user session."""
        if not self._connected:
            return False
        try:
            with Session(engine) as session:
                # Remove old sessions for this farmer
                session.exec(
                    delete(UserSession).where(UserSession.farmer_id == farmer_id)
                )
                us = UserSession(
                    session_token=session_token,
                    farmer_id=farmer_id,
                    phone=phone,
                    expires_at=expires_at,
                    ip_address=ip_address,
                    user_agent=user_agent,
                )
                session.add(us)
                session.commit()
                return True
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            return False

    def get_session(self, session_token: str) -> Optional[Dict]:
        """Get session by token."""
        if not self._connected:
            return None
        try:
            with Session(engine) as session:
                us = session.exec(
                    select(UserSession).where(
                        UserSession.session_token == session_token
                    )
                ).first()
                if us:
                    return {
                        "session_token": us.session_token,
                        "farmer_id": str(us.farmer_id),
                        "phone": us.phone,
                        "expires_at": us.expires_at,
                        "created_at": us.created_at,
                    }
                return None
        except Exception as e:
            logger.error(f"Error getting session: {e}")
            return None

    def delete_session(self, session_token: str) -> bool:
        """Delete a session (logout)."""
        if not self._connected:
            return False
        try:
            with Session(engine) as session:
                session.exec(
                    delete(UserSession).where(
                        UserSession.session_token == session_token
                    )
                )
                session.commit()
                return True
        except Exception as e:
            logger.error(f"Error deleting session: {e}")
            return False

    def cleanup_expired_sessions(self) -> int:
        """Remove expired sessions. Returns count deleted."""
        if not self._connected:
            return 0
        try:
            with Session(engine) as session:
                result = session.exec(
                    delete(UserSession).where(
                        UserSession.expires_at < datetime.utcnow()
                    )
                )
                session.commit()
                return result.rowcount  # type: ignore
        except Exception as e:
            logger.error(f"Error cleaning sessions: {e}")
            return 0

    # ------------------------------------------------------------------
    # IoT Sensor Readings
    # ------------------------------------------------------------------

    def save_sensor_reading(self, reading: Dict) -> bool:
        """Save a sensor reading from an IoT device."""
        if not self._connected:
            return False
        try:
            with Session(engine) as session:
                sr = SensorReading(
                    farm_id=reading["farm_id"],
                    device_id=reading["device_id"],
                    temperature_c=reading.get("temperature_c"),
                    humidity_pct=reading.get("humidity_pct"),
                    soil_moisture_pct=reading.get("soil_moisture_pct"),
                    soil_ph=reading.get("soil_ph"),
                    soil_nitrogen=reading.get("soil_nitrogen"),
                    soil_phosphorus=reading.get("soil_phosphorus"),
                    soil_potassium=reading.get("soil_potassium"),
                    light_lux=reading.get("light_lux"),
                    wind_speed_ms=reading.get("wind_speed_ms"),
                    rainfall_mm=reading.get("rainfall_mm"),
                    pressure_hpa=reading.get("pressure_hpa"),
                    co2_ppm=reading.get("co2_ppm"),
                    battery_pct=reading.get("battery_pct"),
                    rssi_dbm=reading.get("rssi_dbm"),
                    raw_payload=reading.get("raw_payload"),
                )
                session.add(sr)
                session.commit()
                return True
        except Exception as e:
            logger.error(f"Error saving sensor reading: {e}")
            return False

    def save_sensor_readings_batch(self, readings: List[Dict]) -> int:
        """Batch-insert sensor readings. Returns count inserted."""
        if not self._connected or not readings:
            return 0
        try:
            with Session(engine) as session:
                objects = [
                    SensorReading(
                        farm_id=r["farm_id"],
                        device_id=r["device_id"],
                        temperature_c=r.get("temperature_c"),
                        humidity_pct=r.get("humidity_pct"),
                        soil_moisture_pct=r.get("soil_moisture_pct"),
                        soil_ph=r.get("soil_ph"),
                        light_lux=r.get("light_lux"),
                        rainfall_mm=r.get("rainfall_mm"),
                        battery_pct=r.get("battery_pct"),
                        rssi_dbm=r.get("rssi_dbm"),
                        raw_payload=r.get("raw_payload"),
                    )
                    for r in readings
                ]
                session.add_all(objects)
                session.commit()
                return len(objects)
        except Exception as e:
            logger.error(f"Error batch-saving sensor readings: {e}")
            return 0

    def get_sensor_readings(self, farm_id: int, hours: int = 24,
                            device_id: str = None) -> List[Dict]:
        """Get recent sensor readings for a farm."""
        if not self._connected:
            return []
        try:
            with Session(engine) as session:
                cutoff = datetime.utcnow() - timedelta(hours=hours)
                stmt = (
                    select(SensorReading)
                    .where(
                        SensorReading.farm_id == farm_id,
                        SensorReading.ts >= cutoff,
                    )
                )
                if device_id:
                    stmt = stmt.where(SensorReading.device_id == device_id)
                stmt = stmt.order_by(desc(SensorReading.ts))
                rows = session.exec(stmt).all()
                return [
                    {
                        "device_id": r.device_id,
                        "ts": r.ts.isoformat() if r.ts else None,
                        "temperature_c": r.temperature_c,
                        "humidity_pct": r.humidity_pct,
                        "soil_moisture_pct": r.soil_moisture_pct,
                        "soil_ph": r.soil_ph,
                        "soil_nitrogen": r.soil_nitrogen,
                        "soil_phosphorus": r.soil_phosphorus,
                        "soil_potassium": r.soil_potassium,
                        "light_lux": r.light_lux,
                        "wind_speed_ms": r.wind_speed_ms,
                        "rainfall_mm": r.rainfall_mm,
                        "pressure_hpa": r.pressure_hpa,
                        "co2_ppm": r.co2_ppm,
                        "battery_pct": r.battery_pct,
                        "rssi_dbm": r.rssi_dbm,
                    }
                    for r in rows
                ]
        except Exception as e:
            logger.error(f"Error getting sensor readings: {e}")
            return []

    # ------------------------------------------------------------------
    # SMS Delivery Reports
    # ------------------------------------------------------------------

    def save_delivery_report(self, report: Dict) -> bool:
        """Save an SMS delivery report."""
        if not self._connected:
            return False
        try:
            with Session(engine) as session:
                dr = SMSDeliveryReport(
                    message_id=report.get("messageId"),
                    phone_number=report.get("phoneNumber"),
                    status=report.get("status"),
                    network_code=report.get("networkCode"),
                    retry_count=report.get("retryCount"),
                    failure_reason=report.get("failureReason"),
                    provider=report.get("provider", "beem"),
                )
                session.add(dr)
                session.commit()
                return True
        except Exception as e:
            logger.error(f"Error saving delivery report: {e}")
            return False

    # ------------------------------------------------------------------
    # Knowledge Base / RAG (pgvector)
    # ------------------------------------------------------------------

    def add_knowledge(self, doc_text: str, embedding: List[float] = None,
                      **kwargs) -> Optional[int]:
        """Add a document to the knowledge base."""
        if not self._connected:
            return None
        try:
            with Session(engine) as session:
                doc = AgKnowledge(
                    doc_text=doc_text,
                    embedding=embedding,
                    doc_title=kwargs.get("doc_title"),
                    doc_source=kwargs.get("doc_source"),
                    doc_category=kwargs.get("doc_category"),
                    language=kwargs.get("language", "en"),
                    crop=kwargs.get("crop"),
                    region=kwargs.get("region"),
                    season=kwargs.get("season"),
                )
                session.add(doc)
                session.commit()
                session.refresh(doc)
                return doc.id
        except Exception as e:
            logger.error(f"Error adding knowledge: {e}")
            return None

    def search_knowledge(self, query_embedding: List[float], limit: int = 5,
                         crop: str = None, language: str = None) -> List[Dict]:
        """
        Semantic search using pgvector cosine distance.
        Returns top-k documents closest to the query embedding.
        """
        if not self._connected or not query_embedding:
            return []
        try:
            with Session(engine) as session:
                # Build filter conditions
                filters = []
                if crop:
                    filters.append(f"crop = '{crop}'")
                if language:
                    filters.append(f"language = '{language}'")
                where_clause = (" AND " + " AND ".join(filters)) if filters else ""

                sql = text(
                    f"""
                    SELECT id, doc_title, doc_text, doc_source, doc_category,
                           crop, region, language,
                           1 - (embedding <=> :emb::vector) AS similarity
                    FROM ag_knowledge
                    WHERE embedding IS NOT NULL {where_clause}
                    ORDER BY embedding <=> :emb::vector
                    LIMIT :lim
                    """
                )
                rows = session.exec(
                    sql, params={"emb": str(query_embedding), "lim": limit}
                ).all()
                return [
                    {
                        "id": r[0],
                        "doc_title": r[1],
                        "doc_text": r[2],
                        "doc_source": r[3],
                        "doc_category": r[4],
                        "crop": r[5],
                        "region": r[6],
                        "language": r[7],
                        "similarity": float(r[8]),
                    }
                    for r in rows
                ]
        except Exception as e:
            logger.error(f"Error searching knowledge: {e}")
            return []

    # ------------------------------------------------------------------
    # System Config
    # ------------------------------------------------------------------

    def get_config(self, key: str) -> Optional[str]:
        if not self._connected:
            return None
        try:
            with Session(engine) as session:
                row = session.exec(
                    select(SystemConfig).where(SystemConfig.key == key)
                ).first()
                return row.value if row else None
        except Exception as e:
            logger.error(f"Error getting config: {e}")
            return None

    def set_config(self, key: str, value: str, description: str = None) -> bool:
        if not self._connected:
            return False
        try:
            with Session(engine) as session:
                row = session.exec(
                    select(SystemConfig).where(SystemConfig.key == key)
                ).first()
                if row:
                    row.value = value
                    row.updated_at = datetime.utcnow()
                else:
                    row = SystemConfig(key=key, value=value, description=description)
                session.add(row)
                session.commit()
                return True
        except Exception as e:
            logger.error(f"Error setting config: {e}")
            return False

    # ------------------------------------------------------------------
    # Compatibility stubs for unused MongoDB methods
    # ------------------------------------------------------------------

    def get_crop_info(self, crop_id: str) -> Optional[Dict]:
        return None

    def get_region_info(self, region_id: str) -> Optional[Dict]:
        return None

    def get_all_crops(self) -> List[Dict]:
        return []

    def get_all_regions(self) -> List[Dict]:
        return []

    def get_farmers_collection(self):
        """Compat stub — should not be used in new code."""
        return None

    def get_sessions_collection(self):
        return None

    def get_alerts_collection(self):
        return None

    def close(self):
        """No persistent connection to close with connection pool."""
        logger.info("PostgreSQL service closed")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Haversine distance in km."""
        R = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(dlon / 2) ** 2
        )
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    @staticmethod
    def _farmer_to_dict(f: Farmer) -> Dict:
        return {
            "_id": str(f.id),
            "id": f.id,
            "phone": f.phone,
            "name": f.name,
            "email": f.email,
            "region": f.region,
            "county": f.county,
            "sub_county": f.sub_county,
            "language": f.language,
            "sms_enabled": f.sms_enabled,
            "registration_source": f.registration_source,
            "is_admin": f.is_admin,
            "active": f.active,
            "user_type": getattr(f, "user_type", "farmer"),
            "display_id": getattr(f, "display_id", None),
            "avatar_url": getattr(f, "avatar_url", None),
            "location_lat": f.location_lat,
            "location_lon": f.location_lon,
            "crops": f.crops or [],
            "farm_size": f.farm_size,
            "alert_count": f.alert_count,
            "last_login": f.last_login.isoformat() if f.last_login else None,
            "last_alert": f.last_alert.isoformat() if f.last_alert else None,
            "created_at": f.created_at.isoformat() if f.created_at else None,
            "updated_at": f.updated_at.isoformat() if f.updated_at else None,
            "password_hash": f.password_hash,
            "password_salt": f.password_salt,
        }

    @staticmethod
    def _alert_to_dict(a: Alert) -> Dict:
        ts = a.created_at.isoformat() if a.created_at else None
        return {
            "_id": str(a.id),
            "id": a.id,
            "farmer_id": a.farmer_id,
            "alert_type": a.alert_type,
            "severity": a.severity,
            "title": (a.alert_type or "alert").replace("_", " ").title(),
            "message": a.message,
            "channel": a.channel,
            "delivered": a.delivered,
            "crop": a.crop,
            "county": a.county,
            "bloom_risk": a.bloom_risk,
            "timestamp": ts,
            "created_at": ts,
        }

    @staticmethod
    def _bloom_event_to_dict(e: BloomEvent) -> Dict:
        return {
            "_id": str(e.id),
            "id": e.id,
            "region": e.region,
            "county": e.county,
            "sub_county": e.sub_county,
            "crop_type": e.crop_type,
            "timestamp": e.timestamp.isoformat() if e.timestamp else None,
            "bloom_intensity": e.bloom_intensity,
            "bloom_area_km2": e.bloom_area_km2,
            "ndvi_mean": e.ndvi_mean,
            "health_score": e.health_score,
            "bloom_confidence": e.bloom_confidence,
            "bloom_risk": e.bloom_risk,
            "location_lat": e.location_lat,
            "location_lon": e.location_lon,
            "data_source": e.data_source,
        }

    @staticmethod
    def _county_data_to_dict(r: GEECountyData) -> Dict:
        return {
            "id": r.id,
            "county": r.county,
            "sub_county": r.sub_county,
            "region": r.region,
            "observation_date": r.observation_date.isoformat() if r.observation_date else None,
            "ndvi": r.ndvi,
            "ndwi": r.ndwi,
            "evi": r.evi,
            "savi": r.savi,
            "lai": r.lai,
            "rainfall_mm": r.rainfall_mm,
            "temperature_mean_c": r.temperature_mean_c,
            "temperature_max_c": r.temperature_max_c,
            "temperature_min_c": r.temperature_min_c,
            "evapotranspiration_mm": r.evapotranspiration_mm,
            "soil_type": r.soil_type,
            "soil_moisture_pct": r.soil_moisture_pct,
            "soil_organic_carbon": r.soil_organic_carbon,
            "soil_ph": r.soil_ph,
            "soil_clay_pct": r.soil_clay_pct,
            "soil_sand_pct": r.soil_sand_pct,
            "crop_water_stress_index": r.crop_water_stress_index,
            "land_surface_temperature_c": r.land_surface_temperature_c,
            "bloom_area_km2": r.bloom_area_km2,
            "bloom_percentage": r.bloom_percentage,
            "bloom_probability": r.bloom_probability,
            "cloud_cover_pct": r.cloud_cover_pct,
            "data_source": r.data_source,
            "is_real_data": r.is_real_data,
            "center_lat": r.center_lat,
            "center_lon": r.center_lon,
            "main_crops": r.main_crops,
        }
