"""
Authentication Service for Smart Shamba — PostgreSQL backed
Drop-in replacement for the MongoDB auth_service.py

Uses PostgreSQL via database.postgres_service.PostgresService
"""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Optional imports for smart alerts
try:
    from smart_alert_service import SmartAlertService
    from bloom_processor import BloomProcessor
    SMART_ALERTS_AVAILABLE = True
except ImportError:
    SMART_ALERTS_AVAILABLE = False
    logger.warning("Smart alerts not available — missing dependencies")


class AuthService:
    """Authentication and session management (PostgreSQL)"""

    def __init__(self, db_service=None):
        # Accept either a PostgresService or the legacy MongoDBService
        if db_service is None:
            from database.postgres_service import PostgresService
            db_service = PostgresService()
        self.db = db_service

        # In-memory session cache for fast lookups
        self.sessions: Dict[str, Dict] = {}

        # Smart alert service (optional)
        self.alert_service = None
        if SMART_ALERTS_AVAILABLE:
            try:
                self.bloom_processor = BloomProcessor(db_service=self.db)
                # SMS service will be injected later or lazily
                self.alert_service = SmartAlertService(
                    db_service=self.db,  # uses same interface
                )
                logger.info("Smart alerts enabled")
            except Exception as e:
                logger.warning(f"Could not initialise smart alerts: {e}")

    # ------------------------------------------------------------------ #
    # Password helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def hash_password(password: str, salt: str = None) -> tuple:
        """Hash password with PBKDF2-SHA256"""
        if not salt:
            salt = secrets.token_hex(16)
        pwd_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            100000,
        )
        return pwd_hash.hex(), salt

    @staticmethod
    def verify_password(password: str, pwd_hash: str, salt: str) -> bool:
        computed, _ = AuthService.hash_password(password, salt)
        return computed == pwd_hash

    # ------------------------------------------------------------------ #
    # Registration
    # ------------------------------------------------------------------ #

    def register_farmer(self, farmer_data: Dict, password: str) -> Dict:
        """Register new farmer with password."""
        if not self.db.is_connected():
            return {"success": False, "message": "Database not available", "demo": True}

        # Check duplicate phone
        existing = self.db.get_farmer_by_phone(farmer_data["phone"])
        if existing:
            return {"success": False, "message": "Phone number already registered"}

        # Hash password
        pwd_hash, salt = self.hash_password(password)
        farmer_data["password_hash"] = pwd_hash
        farmer_data["password_salt"] = salt

        result = self.db.register_farmer(farmer_data)

        if result["success"]:
            logger.info(f"✓ New farmer registered: {farmer_data.get('name')}")

            # Send welcome alert (non-blocking)
            if self.alert_service and hasattr(self, "bloom_processor"):
                try:
                    bloom_data = self.bloom_processor.detect_bloom_events(
                        farmer_data.get("region", "kenya")
                    )
                    alert_result = self.alert_service.send_welcome_alert(
                        farmer_data, bloom_data
                    )
                    if alert_result and alert_result.get("success"):
                        result["alerts_sent"] = alert_result.get("alerts_sent", 0)
                except Exception as e:
                    logger.error(f"Error sending welcome alert: {e}")

        return result

    # ------------------------------------------------------------------ #
    # Login / Session
    # ------------------------------------------------------------------ #

    def login(self, phone: str, password: str) -> Dict:
        """Authenticate farmer and create session."""
        if not self.db.is_connected():
            return {
                "success": True,
                "demo": True,
                "farmer": {
                    "phone": phone,
                    "name": "Demo Farmer",
                    "region": "central",
                    "crops": ["maize", "beans"],
                },
                "session_token": "demo_token",
            }

        farmer = self.db.get_farmer_by_phone(phone)
        if not farmer:
            return {"success": False, "message": "Phone number not registered"}

        if not self.verify_password(
            password, farmer["password_hash"], farmer["password_salt"]
        ):
            return {"success": False, "message": "Incorrect password"}

        # Create session token
        session_token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=24)

        session_data = {
            "session_token": session_token,
            "farmer_id": farmer["_id"],
            "phone": farmer["phone"],
            "farmer_data": {
                "phone": farmer["phone"],
                "name": farmer["name"],
                "email": farmer.get("email"),
                "region": farmer.get("region"),
                "county": farmer.get("county"),
                "crops": farmer.get("crops", []),
                "language": farmer.get("language", "en"),
                "created_at": farmer.get("created_at"),
                "farm_size": farmer.get("farm_size"),
            },
            "created_at": datetime.utcnow(),
            "expires_at": expires_at,
        }

        # Persist to PostgreSQL
        self.db.create_session(
            session_token=session_token,
            farmer_id=int(farmer["_id"]),
            phone=farmer["phone"],
            expires_at=expires_at,
        )

        # Cache in memory
        self.sessions[session_token] = session_data

        # Update last_login on farmer record
        # (uses raw update via service — we can extend postgres_service if needed)
        try:
            from sqlmodel import Session as DBSession
            from database.connection import engine
            from database.models import Farmer as FarmerModel

            with DBSession(engine) as sess:
                fm = sess.get(FarmerModel, int(farmer["_id"]))
                if fm:
                    fm.last_login = datetime.utcnow()
                    sess.add(fm)
                    sess.commit()
        except Exception:
            pass  # non-critical

        # Sanitise response
        safe_farmer = {k: v for k, v in farmer.items()
                       if k not in ("password_hash", "password_salt")}

        logger.info(f"✓ Farmer logged in: {farmer['name']}")
        return {
            "success": True,
            "farmer": safe_farmer,
            "session_token": session_token,
        }

    def verify_session(self, session_token: str) -> Optional[Dict]:
        """Verify a session token — checks cache then DB."""
        if session_token == "demo_token":
            return {
                "phone": "demo",
                "farmer_id": "demo",
                "demo": True,
                "farmer_data": {
                    "phone": "demo",
                    "name": "Demo Farmer",
                    "region": "central",
                    "crops": ["maize", "beans"],
                    "language": "en",
                },
            }

        # 1. Check in-memory cache
        session = self.sessions.get(session_token)

        # 2. Check PostgreSQL
        if not session:
            db_session = self.db.get_session(session_token)
            if db_session:
                # Rebuild full session_data from DB
                farmer = self.db.get_farmer_by_id(int(db_session["farmer_id"]))
                session = {
                    "session_token": session_token,
                    "farmer_id": db_session["farmer_id"],
                    "phone": db_session["phone"],
                    "expires_at": db_session["expires_at"],
                    "created_at": db_session["created_at"],
                    "farmer_data": {
                        "phone": farmer["phone"],
                        "name": farmer["name"],
                        "email": farmer.get("email"),
                        "region": farmer.get("region"),
                        "county": farmer.get("county"),
                        "crops": farmer.get("crops", []),
                        "language": farmer.get("language", "en"),
                        "farm_size": farmer.get("farm_size"),
                    } if farmer else {},
                }
                self.sessions[session_token] = session

        if not session:
            return None

        # Check expiry
        expires_at = session.get("expires_at")
        if expires_at:
            if isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(expires_at)
            # Make comparison tz-aware safe
            now = datetime.utcnow()
            if expires_at.tzinfo is not None:
                from datetime import timezone
                now = now.replace(tzinfo=timezone.utc)
            if now > expires_at:
                self.sessions.pop(session_token, None)
                self.db.delete_session(session_token)
                return None

        return session

    def logout(self, session_token: str) -> bool:
        """Invalidate session."""
        self.sessions.pop(session_token, None)
        self.db.delete_session(session_token)
        logger.info("✓ Farmer logged out")
        return True

    # ------------------------------------------------------------------ #
    # Profile helpers
    # ------------------------------------------------------------------ #

    def get_farmer_from_session(self, session_token: str) -> Optional[Dict]:
        """Get farmer data from session."""
        session = self.verify_session(session_token)
        if not session:
            return None

        if session.get("demo"):
            return {
                "phone": "demo",
                "name": "Demo Farmer",
                "region": "central",
                "crops": ["maize", "beans"],
                "language": "en",
                "demo": True,
            }

        farmer_id = session.get("farmer_id")
        if not farmer_id:
            return None

        farmer = self.db.get_farmer_by_id(int(farmer_id))
        if farmer:
            farmer.pop("password_hash", None)
            farmer.pop("password_salt", None)
        return farmer

    def update_farmer_profile(self, session_token: str, updates: Dict) -> Dict:
        """Update farmer profile fields."""
        session = self.verify_session(session_token)
        if not session:
            return {"success": False, "message": "Session expired"}
        if session.get("demo"):
            return {"success": True, "message": "Profile updated (demo mode)", "demo": True}

        farmer_id = session.get("farmer_id")
        if not farmer_id:
            return {"success": False, "message": "Invalid session"}

        # Strip sensitive fields
        for key in ("password_hash", "password_salt", "phone"):
            updates.pop(key, None)

        try:
            from sqlmodel import Session as DBSession
            from database.connection import engine
            from database.models import Farmer as FarmerModel

            with DBSession(engine) as sess:
                fm = sess.get(FarmerModel, int(farmer_id))
                if not fm:
                    return {"success": False, "message": "Farmer not found"}
                for k, v in updates.items():
                    if hasattr(fm, k):
                        setattr(fm, k, v)
                fm.updated_at = datetime.utcnow()
                sess.add(fm)
                sess.commit()
            return {"success": True, "message": "Profile updated successfully"}
        except Exception as e:
            logger.error(f"Error updating profile: {e}")
            return {"success": False, "message": str(e)}

    def change_password(self, session_token: str, old_password: str,
                        new_password: str) -> Dict:
        """Change farmer password."""
        session = self.verify_session(session_token)
        if not session:
            return {"success": False, "message": "Session expired"}
        if session.get("demo"):
            return {"success": True, "message": "Password changed (demo mode)", "demo": True}

        farmer_id = session.get("farmer_id")
        farmer = self.db.get_farmer_by_id(int(farmer_id))
        if not farmer:
            return {"success": False, "message": "Farmer not found"}

        if not self.verify_password(
            old_password, farmer["password_hash"], farmer["password_salt"]
        ):
            return {"success": False, "message": "Incorrect current password"}

        pwd_hash, salt = self.hash_password(new_password)

        try:
            from sqlmodel import Session as DBSession
            from database.connection import engine
            from database.models import Farmer as FarmerModel

            with DBSession(engine) as sess:
                fm = sess.get(FarmerModel, int(farmer_id))
                fm.password_hash = pwd_hash
                fm.password_salt = salt
                fm.updated_at = datetime.utcnow()
                sess.add(fm)
                sess.commit()
            return {"success": True, "message": "Password changed successfully"}
        except Exception as e:
            logger.error(f"Error changing password: {e}")
            return {"success": False, "message": str(e)}


# ------------------------------------------------------------------ #
# Quick smoke test
# ------------------------------------------------------------------ #

if __name__ == "__main__":
    print("🌾 Smart Shamba — Auth Service Test (PostgreSQL)")
    print("=" * 60)

    auth = AuthService()

    test_farmer = {
        "name": "Test Farmer",
        "phone": "+254799999999",
        "email": "test@example.com",
        "location_lat": -1.2921,
        "location_lon": 36.8219,
        "region": "central",
        "crops": ["maize", "beans"],
        "language": "en",
    }

    result = auth.register_farmer(test_farmer, "test123")
    print(f"\n✓ Registration: {result}")

    login_result = auth.login("+254799999999", "test123")
    print(f"✓ Login: Success={login_result['success']}")

    if login_result["success"]:
        token = login_result["session_token"]
        session = auth.verify_session(token)
        print(f"✓ Session verified: {session is not None}")
        auth.logout(token)
        print("✓ Logout successful")

    print("\n🛰️ Auth service test completed!")
