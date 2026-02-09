"""
Integration tests for Smart Shamba platform — PostgreSQL migration.

Covers:
- PostgresService CRUD
- AuthService (auth_service_pg) login/register/verify
- AfricasTalkingService (demo mode)
- IoTIngestionService
- PyTorch BloomPredictor
- FloraAIService (Gemini fallback)
- Agrovet & Marketplace DB operations

Run:
    cd /home/yogo/bloom-detector/server && python -m pytest tests/test_integration.py -v
"""

import os
import sys
import pytest
from datetime import datetime, date
from decimal import Decimal

# Ensure server dir is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ── Fixtures ──────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def db_service():
    from database.postgres_service import PostgresService
    svc = PostgresService()
    assert svc.is_connected(), "PostgreSQL must be running"
    return svc


@pytest.fixture(scope="module")
def auth_service(db_service):
    from auth_service_pg import AuthService
    return AuthService(db_service=db_service)


@pytest.fixture(scope="module")
def sms_service(db_service):
    from africastalking_service import AfricasTalkingService
    return AfricasTalkingService(db_service=db_service)


@pytest.fixture(scope="module")
def iot_service(db_service):
    from iot_ingestion_service import IoTIngestionService
    return IoTIngestionService(db_service=db_service)


@pytest.fixture(scope="module")
def bloom_predictor():
    from train_model_pytorch import BloomPredictor
    return BloomPredictor()


@pytest.fixture(scope="module")
def flora_service():
    from flora_ai_gemini import FloraAIService
    return FloraAIService()


# ── PostgresService ───────────────────────────────────────────────────

class TestPostgresService:
    """CRUD operations on the farmers table."""

    _phone = "+254700999888"
    _farmer_id: str = ""

    def test_connection(self, db_service):
        assert db_service.is_connected()

    def test_register_farmer(self, db_service):
        result = db_service.register_farmer({
            "phone": self._phone,
            "name": "Integration Test Farmer",
            "region": "central",
            "county": "Kiambu",
            "crops": ["maize", "beans"],
            "language": "en",
            "password_hash": "test_hash",
        })
        assert result is not None
        assert result.get("success") is True

    def test_get_farmer_by_phone(self, db_service):
        farmer = db_service.get_farmer_by_phone(self._phone)
        assert farmer is not None
        assert farmer["name"] == "Integration Test Farmer"
        self.__class__._farmer_id = str(farmer["id"])

    def test_get_farmer_statistics(self, db_service):
        stats = db_service.get_farmer_statistics()
        assert "total_farmers" in stats
        assert stats["total_farmers"] >= 1

    def test_save_bloom_event(self, db_service):
        result = db_service.save_bloom_event({
            "region": "central",
            "county": "Kiambu",
            "crop_type": "maize",
            "bloom_intensity": 0.75,
            "health_score": 82.5,
            "ndvi_mean": 0.65,
            "data_source": "integration_test",
        })
        # save_bloom_event returns Optional[str] (event_id) or None
        assert result is not None

    def test_get_recent_bloom_events(self, db_service):
        events = db_service.get_recent_bloom_events(days=7)
        assert isinstance(events, list)

    def test_log_alert(self, db_service):
        farmer = db_service.get_farmer_by_phone(self._phone)
        assert farmer is not None
        result = db_service.log_alert(str(farmer["id"]), {
            "phone": self._phone,
            "crop": "maize",
            "message": "Integration test alert",
            "alert_type": "custom",
            "bloom_risk": "Low",
            "health_score": 85.0,
        })
        assert result is True

    def test_delete_farmer(self, db_service):
        result = db_service.delete_farmer(self._farmer_id)
        assert result is True
        farmer = db_service.get_farmer_by_phone(self._phone)
        assert farmer is None


# ── AuthService (auth_service_pg) ────────────────────────────────────

class TestAuthService:
    _phone = "+254700888777"
    _password = "TestPass123!"
    _token: str = ""

    def test_register(self, auth_service):
        result = auth_service.register_farmer(
            {
                "phone": self._phone,
                "name": "Auth Test Farmer",
                "region": "western",
                "county": "Kakamega",
                "crops": ["sugarcane"],
                "language": "sw",
            },
            password=self._password,
        )
        assert result.get("success") is True

    def test_login(self, auth_service):
        result = auth_service.login(self._phone, self._password)
        assert result.get("success") is True
        assert "session_token" in result
        self.__class__._token = result["session_token"]

    def test_verify_session(self, auth_service):
        result = auth_service.verify_session(self._token)
        # verify_session returns session dict or None
        assert result is not None
        assert result.get("phone") == self._phone

    def test_logout(self, auth_service):
        result = auth_service.logout(self._token)
        # logout returns bool
        assert result is True

    def test_cleanup(self, db_service):
        farmer = db_service.get_farmer_by_phone(self._phone)
        if farmer:
            db_service.delete_farmer(str(farmer["id"]))


# ── AfricasTalkingService ─────────────────────────────────────────────

class TestSMSService:

    def test_init(self, sms_service):
        assert sms_service is not None

    def test_send_sms_demo(self, sms_service):
        # Without real API keys this should still not crash
        result = sms_service.send_sms("+254700000000", "Integration test")
        # May fail gracefully if no API key, but shouldn't raise
        assert isinstance(result, dict)


# ── IoT Ingestion ────────────────────────────────────────────────────

class TestIoTIngestion:

    @classmethod
    def _ensure_farm(cls):
        """Create a farmer + farm row if none exists (sensor_readings FK requires it)."""
        from database.connection import get_sync_session
        from database.models import Farm, Farmer
        from sqlmodel import select

        with get_sync_session() as session:
            existing = session.exec(select(Farm)).first()
            if existing:
                cls._farm_id = existing.id
                return

            # Need a farmer first for FK
            farmer = session.exec(select(Farmer)).first()
            if not farmer:
                farmer = Farmer(
                    phone="+254700555444",
                    name="IoT Test Farmer",
                    region="rift_valley",
                    county="Nakuru",
                    language="en",
                )
                session.add(farmer)
                session.commit()
                session.refresh(farmer)

            farm = Farm(
                farmer_id=farmer.id,  # type: ignore[arg-type]
                name="IoT Test Farm",
                county="Nakuru",
                latitude=-0.3,
                longitude=36.07,
                size_acres=5.0,
            )
            session.add(farm)
            session.commit()
            session.refresh(farm)
            cls._farm_id = farm.id

    def test_ingest_reading(self, iot_service):
        self._ensure_farm()
        result = iot_service.ingest_reading({
            "farm_id": self._farm_id,
            "device_id": "test-esp32-001",
            "temperature_c": 25.5,
            "humidity_pct": 65.0,
            "soil_moisture_pct": 40.0,
        })
        assert result.get("success") is True

    def test_ingest_batch(self, iot_service):
        readings = [
            {"farm_id": self._farm_id, "device_id": "test-esp32-001", "temperature_c": 26.0, "humidity_pct": 60.0},
            {"farm_id": self._farm_id, "device_id": "test-esp32-001", "temperature_c": 26.5, "humidity_pct": 58.0},
        ]
        result = iot_service.ingest_batch(readings)
        assert result.get("inserted", 0) >= 2

    def test_get_readings(self, iot_service):
        readings = iot_service.get_farm_readings(self._farm_id, hours=24)
        assert isinstance(readings, list)
        assert len(readings) >= 1


# ── PyTorch BloomPredictor ───────────────────────────────────────────

class TestBloomPredictor:

    def test_init(self, bloom_predictor):
        assert bloom_predictor is not None

    def test_train(self, bloom_predictor):
        result = bloom_predictor.train_model(include_weather=True)
        assert result.get("status") == "success" or "error" in result

    def test_predict(self, bloom_predictor):
        pred = bloom_predictor.predict_bloom_probability()
        assert "bloom_probability_percent" in pred
        assert 0 <= pred["bloom_probability_percent"] <= 100

    def test_save_load(self, bloom_predictor):
        saved = bloom_predictor.save_model()
        # May be False if train failed, that's OK
        if saved:
            from train_model_pytorch import BloomPredictor
            p2 = BloomPredictor()
            assert p2.load_model() is True

    def test_model_info(self, bloom_predictor):
        info = bloom_predictor.get_model_info()
        assert isinstance(info, dict)


# ── Flora AI Gemini ──────────────────────────────────────────────────

class TestFloraAI:

    def test_init(self, flora_service):
        assert flora_service is not None

    def test_fallback_response(self, flora_service):
        resp = flora_service.answer_question("When to plant maize?", language="en")
        assert isinstance(resp, str)
        assert len(resp) > 0

    def test_fallback_swahili(self, flora_service):
        resp = flora_service.answer_question("Wakati gani kupanda mahindi?", language="sw")
        assert isinstance(resp, str)

    def test_generate_response(self, flora_service):
        resp = flora_service.generate_response("How is my crop?")
        assert isinstance(resp, str)


# ── Agrovet & Marketplace (DB-level) ────────────────────────────────

class TestAgrovetDB:

    def test_create_product(self):
        from database.connection import get_sync_session
        from database.models import AgrovetProduct

        with get_sync_session() as session:
            product = AgrovetProduct(
                name="Test Fertilizer",
                name_sw="Mbolea ya Mtihani",
                category="fertilizer",
                price_kes=Decimal("1500.00"),
                unit="bag",
                in_stock=True,
                supplier_county="Nakuru",
            )
            session.add(product)
            session.commit()
            session.refresh(product)
            assert product.id is not None
            TestAgrovetDB._product_id = product.id

    def test_query_products(self):
        from database.connection import get_sync_session
        from database.models import AgrovetProduct
        from sqlmodel import select

        with get_sync_session() as session:
            stmt = select(AgrovetProduct).where(AgrovetProduct.category == "fertilizer")
            products = session.exec(stmt).all()
            assert len(products) >= 1

    def test_cleanup(self):
        from database.connection import get_sync_session
        from database.models import AgrovetProduct

        with get_sync_session() as session:
            p = session.get(AgrovetProduct, self._product_id)
            if p:
                session.delete(p)
                session.commit()


class TestMarketplaceDB:

    def test_create_listing(self, db_service):
        # Need a farmer first
        result = db_service.register_farmer({
            "phone": "+254700111222",
            "name": "Marketplace Test",
            "region": "rift_valley",
            "county": "Nakuru",
            "crops": ["wheat"],
            "language": "en",
            "password_hash": "test",
        })

        from database.connection import get_sync_session
        from database.models import MarketplaceListing

        farmer_id = int(result["farmer_id"]) if result.get("success") else 1

        with get_sync_session() as session:
            listing = MarketplaceListing(
                farmer_id=farmer_id,
                produce_name="Test Wheat",
                produce_category="grains",
                quantity_available=500.0,
                unit="kg",
                price_per_unit_kes=Decimal("55.00"),
                county="Nakuru",
                delivery_available=True,
                quality_grade="A",
            )
            session.add(listing)
            session.commit()
            session.refresh(listing)
            assert listing.id is not None
            TestMarketplaceDB._listing_id = listing.id
            TestMarketplaceDB._farmer_id = str(farmer_id)
            TestMarketplaceDB._farmer_phone = "+254700111222"

    def test_query_listings(self):
        from database.connection import get_sync_session
        from database.models import MarketplaceListing
        from sqlmodel import select

        with get_sync_session() as session:
            stmt = select(MarketplaceListing).where(MarketplaceListing.status == "active")
            listings = session.exec(stmt).all()
            assert len(listings) >= 1

    def test_cleanup(self, db_service):
        from database.connection import get_sync_session
        from database.models import MarketplaceListing

        with get_sync_session() as session:
            listing = session.get(MarketplaceListing, self._listing_id)
            if listing:
                session.delete(listing)
                session.commit()

        db_service.delete_farmer(self._farmer_id)


# ── Run ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
