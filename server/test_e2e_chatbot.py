#!/usr/bin/env python3
"""
End-to-end test: Flora AI chatbot, RAG, Smart Alert System
Tests the full pipeline with a real Gemini API call.
"""

import os, sys, json, asyncio
from pathlib import Path
from datetime import datetime, timedelta

# Ensure .env is loaded
sys.path.insert(0, str(Path(__file__).parent))
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from sqlalchemy import text
from database.connection import engine, Session

# ── Step 0: Check prerequisites ─────────────────────────────────────
print("=" * 70)
print("SMART SHAMBA E2E TEST — Flora AI + RAG + Smart Alerts")
print("=" * 70)

gemini_key = os.getenv("GEMINI_API_KEY", "")
print(f"\n[0] Gemini API key: {'SET ✓' if gemini_key and 'your_' not in gemini_key else 'MISSING ✗'}")
print(f"    Model: {os.getenv('GEMINI_MODEL', 'not set')}")

# Check ag_knowledge count
with Session(engine) as s:
    cnt = s.execute(text("SELECT COUNT(*) FROM ag_knowledge")).scalar()
    print(f"    ag_knowledge entries: {cnt}")

# ── Step 1: Find or create a test farmer ────────────────────────────
print("\n" + "=" * 70)
print("[1] FARMER SETUP")
print("=" * 70)

from database.postgres_service import PostgresService
db_service = PostgresService()

# Try to find an existing farmer
with Session(engine) as s:
    farmer_row = s.execute(text(
        "SELECT id, name, phone, county, crops, language, farm_size "
        "FROM farmers LIMIT 1"
    )).fetchone()

if farmer_row:
    farmer_id = farmer_row[0]
    print(f"  Using existing farmer: {farmer_row[1]} (id={farmer_id})")
    farmer_data = {
        "id": farmer_row[0],
        "name": farmer_row[1],
        "phone": farmer_row[2],
        "county": farmer_row[3],
        "crops": farmer_row[4] if farmer_row[4] else ["maize"],
        "language": farmer_row[5] or "en",
        "farm_size": farmer_row[6] or 2.0,
    }
else:
    print("  No existing farmer — creating test farmer...")
    test_farmer = {
        "name": "Wanjiku Kamau",
        "phone": "+254700000001",
        "county": "Kiambu",
        "sub_county": "Thika",
        "crops": ["maize", "beans", "coffee"],
        "language": "en",
        "farm_size": 3.5,
        "location": {"lat": -1.0396, "lng": 37.0900},
    }
    result = db_service.register_farmer(test_farmer)
    farmer_id = result.get("id") if isinstance(result, dict) else result
    farmer_data = {**test_farmer, "id": farmer_id}
    print(f"  Created farmer: {test_farmer['name']} (id={farmer_id})")

print(f"  Farmer: {json.dumps({k: str(v) for k, v in farmer_data.items()}, indent=4)}")

# ── Step 2: Test RAG Knowledge Retrieval ────────────────────────────
print("\n" + "=" * 70)
print("[2] RAG KNOWLEDGE RETRIEVAL TEST")
print("=" * 70)

from flora_ai_gemini import FloraAIService
flora_ai = FloraAIService(db_service)

# Test knowledge retrieval directly
rag_queries = [
    "What is the optimal soil pH for maize?",
    "How do I detect armyworm infestation?",
    "What is a good NDVI value for healthy crops?",
]

for q in rag_queries:
    print(f"\n  Query: '{q}'")
    try:
        snippets = flora_ai._retrieve_knowledge(q, top_k=3)
        if snippets:
            for i, s in enumerate(snippets):
                preview = s[:120].replace('\n', ' ')
                print(f"    [{i+1}] {preview}...")
        else:
            print("    ⚠ No knowledge retrieved (empty result)")
    except Exception as e:
        print(f"    ✗ Error: {e}")

# ── Step 3: Test Flora AI Chatbot (Gemini API) ──────────────────────
print("\n" + "=" * 70)
print("[3] FLORA AI CHATBOT TEST (Gemini API call)")
print("=" * 70)

chatbot_questions = [
    "My maize leaves are turning yellow. What could be wrong?",
]

import time
for q in chatbot_questions:
    print(f"\n  Q: '{q}'")
    print("  (Waiting 25s for Gemini rate limit cooldown...)")
    time.sleep(25)
    try:
        response = flora_ai.answer_question(
            question=q,
            farmer_data=farmer_data,
            language="en",
            use_internet=False,
            channel="sms"
        )
        if isinstance(response, dict):
            answer = response.get("answer", response.get("response", str(response)))
        else:
            answer = str(response)
        # Truncate for display
        if len(answer) > 400:
            answer = answer[:400] + "..."
        print(f"  A: {answer}")
        print(f"  ✓ Gemini response received")
    except Exception as e:
        print(f"  ✗ Error: {type(e).__name__}: {e}")

# ── Step 4: Test Smart Alert — Condition Evaluator ──────────────────
print("\n" + "=" * 70)
print("[4] SMART ALERT — CONDITION EVALUATOR")
print("=" * 70)

from smart_alert_service import SmartAlertService
alert_service = SmartAlertService(db_service)

# Simulate sensor data (IoT readings)
sensor_data_optimal = {
    "soil_ph": 6.5,
    "soil_moisture_pct": 55.0,
    "temperature_c": 24.0,
    "humidity_pct": 70.0,
}

# Simulate satellite data
satellite_data_optimal = {
    "ndvi": 0.72,
    "ndwi": 0.15,
    "rainfall_mm": 120.0,
}

print("\n  --- Test A: ALL OPTIMAL conditions (maize) ---")
try:
    report = alert_service.evaluate_farm_conditions(
        crop="maize",
        sensor_data=sensor_data_optimal,
        satellite_data=satellite_data_optimal
    )
    print(f"  Status: {report.status}")
    print(f"  Overall Score: {report.overall_score:.0f}%")
    print(f"  Optimal Metrics: {report.optimal_metrics}")
    print(f"  Deviations: {len(report.deviations)}")
    if report.deviations:
        for d in report.deviations:
            print(f"    - {d.display_name}: {d.value} (optimal {d.optimal_min}-{d.optimal_max} {d.unit}) [{d.severity}]")
    print("  ✓ Condition evaluation works")
except Exception as e:
    print(f"  ✗ Error: {type(e).__name__}: {e}")
    import traceback; traceback.print_exc()

print("\n  --- Test B: MIXED conditions (some suboptimal) ---")
sensor_data_mixed = {
    "soil_ph": 4.5,          # Too acidic for maize (optimal 5.5-7.0)
    "soil_moisture_pct": 30,  # Too dry (optimal 40-70)
    "temperature_c": 25.0,    # OK
    "humidity_pct": 65.0,     # OK
}
satellite_data_mixed = {
    "ndvi": 0.65,       # OK
    "ndwi": 0.10,       # OK
    "rainfall_mm": 40,  # Low (optimal 50-180)
}

try:
    report = alert_service.evaluate_farm_conditions(
        crop="maize",
        sensor_data=sensor_data_mixed,
        satellite_data=satellite_data_mixed
    )
    print(f"  Status: {report.status}")
    print(f"  Overall Score: {report.overall_score:.0f}%")
    print(f"  Optimal Metrics: {report.optimal_metrics}")
    print(f"  Deviations ({len(report.deviations)}):")
    for d in report.deviations:
        print(f"    - {d.display_name}: {d.value} (optimal {d.optimal_min}-{d.optimal_max} {d.unit}) [{d.severity}] {d.direction}")
    print("  ✓ Mixed condition detection works")
except Exception as e:
    print(f"  ✗ Error: {type(e).__name__}: {e}")
    import traceback; traceback.print_exc()

# ── Step 5: Test Smart Alert Generation (full pipeline) ─────────────
print("\n" + "=" * 70)
print("[5] SMART ALERT — FULL ALERT GENERATION")
print("=" * 70)

# Test with optimal conditions
print("\n  --- Test A: Full alert — ALL OPTIMAL ---")
try:
    alert_result = alert_service.generate_condition_alert(
        farmer_data=farmer_data,
        sensor_data=sensor_data_optimal,
        satellite_data=satellite_data_optimal
    )
    if alert_result:
        print(f"  SMS Text: {alert_result.get('sms_text', 'N/A')[:300]}")
        print(f"  Alert Type: {alert_result.get('alert_type', 'N/A')}")
        print(f"  ✓ Good-news alert generated")
    else:
        print("  ⚠ No alert generated (returned None)")
except Exception as e:
    print(f"  ✗ Error: {type(e).__name__}: {e}")
    import traceback; traceback.print_exc()

# Test with mixed conditions
print("\n  --- Test B: Full alert — MIXED conditions ---")
try:
    alert_result = alert_service.generate_condition_alert(
        farmer_data=farmer_data,
        sensor_data=sensor_data_mixed,
        satellite_data=satellite_data_mixed
    )
    if alert_result:
        print(f"  SMS Text: {alert_result.get('sms_text', 'N/A')[:500]}")
        print(f"  Web Text: {alert_result.get('web_text', 'N/A')[:500]}")
        print(f"  Alert Type: {alert_result.get('alert_type', 'N/A')}")
        print(f"  ✓ Per-metric alert generated")
    else:
        print("  ⚠ No alert generated (returned None)")
except Exception as e:
    print(f"  ✗ Error: {type(e).__name__}: {e}")
    import traceback; traceback.print_exc()

# ── Step 6: Test RAG-Enhanced Alert ─────────────────────────────────
print("\n" + "=" * 70)
print("[6] RAG-ENHANCED ALERT (Gemini + Knowledge Base)")
print("=" * 70)

print("  (Waiting 25s for Gemini rate limit cooldown...)")
time.sleep(25)
try:
    rag_alert = alert_service.generate_rag_alert(
        farmer_data=farmer_data,
        sensor_data=sensor_data_mixed,
        satellite_data=satellite_data_mixed
    )
    if rag_alert:
        print(f"  SMS: {rag_alert.get('sms_text', 'N/A')[:400]}")
        print(f"  Web: {rag_alert.get('web_text', 'N/A')[:400]}")
        print(f"  ✓ RAG alert generated with knowledge base enrichment")
    else:
        print("  ⚠ No RAG alert generated")
except Exception as e:
    print(f"  ✗ Error: {type(e).__name__}: {e}")
    import traceback; traceback.print_exc()

# ── Summary ─────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("E2E TEST COMPLETE")
print("=" * 70)
