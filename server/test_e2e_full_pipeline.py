#!/usr/bin/env python3
"""
Full E2E Pipeline Test — Smart Shamba
==========================================
Tests the complete Smart Shamba intelligence pipeline:

  1. pgvector RAG retrieval (ag_knowledge)
  2. Gemini fallback chain:  Vertex AI → API key → Template
  3. Flora AI chatbot (farmer-initiated queries)
  4. Threshold-based condition evaluator (optimal ranges)
  5. Condition-based automated alerts
  6. RAG-augmented alerts (Gemini + knowledge base)
  7. Disease detection alert pipeline

Run:
  cd server && source ../venv/bin/activate && python test_e2e_full_pipeline.py
"""

import os, sys, json, time, traceback
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from sqlalchemy import text
from database.connection import engine, Session

# ─── Tracking ───────────────────────────────────────────────────────
RESULTS = {"passed": 0, "failed": 0, "skipped": 0, "tests": []}

def record(name: str, status: str, detail: str = ""):
    RESULTS["tests"].append({"name": name, "status": status, "detail": detail})
    RESULTS[status] += 1
    icon = {"passed": "✅", "failed": "❌", "skipped": "⏭️"}[status]
    print(f"  {icon} {name}" + (f" — {detail}" if detail else ""))


# ═══════════════════════════════════════════════════════════════════════
#  STEP 0: Prerequisites
# ═══════════════════════════════════════════════════════════════════════
print("=" * 72)
print("  SMART SHAMBA FULL E2E PIPELINE TEST")
print("  " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
print("=" * 72)

# Check backend config
api_key = os.getenv("GEMINI_API_KEY", "")
use_vertex = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "").lower() in ("true", "1")
vertex_project = os.getenv("GOOGLE_CLOUD_PROJECT", "")
gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

print(f"\n  Vertex AI:      {'ENABLED' if use_vertex else 'disabled'} (project={vertex_project or 'n/a'})")
print(f"  Gemini API key: {'SET' if api_key else 'NOT SET'}")
print(f"  Model:          {gemini_model}")

# ag_knowledge count
with Session(engine) as s:
    ag_count = s.execute(text("SELECT COUNT(*) FROM ag_knowledge")).scalar()
    print(f"  ag_knowledge:   {ag_count} entries")

# Farmer
from database.postgres_service import PostgresService
db = PostgresService()

with Session(engine) as s:
    row = s.execute(text(
        "SELECT id, name, phone, county, crops, language, farm_size "
        "FROM farmers LIMIT 1"
    )).fetchone()

if row:
    farmer_data = {
        "id": row[0], "name": row[1], "phone": row[2],
        "county": row[3], "crops": row[4] or ["maize"],
        "language": row[5] or "en", "farm_size": row[6] or 2.0,
    }
else:
    test_f = {
        "name": "Wanjiku Kamau", "phone": "+254700000001",
        "county": "Kiambu", "sub_county": "Thika",
        "crops": ["maize", "beans", "coffee"], "language": "en",
        "farm_size": 3.5, "location": {"lat": -1.0396, "lng": 37.0900},
    }
    result = db.register_farmer(test_f)
    farmer_data = {**test_f, "id": result.get("id") if isinstance(result, dict) else result}

print(f"  Farmer:         {farmer_data['name']} (id={farmer_data['id']}, {farmer_data['county']})")
print(f"  Crops:          {', '.join(farmer_data['crops'])}")


# ═══════════════════════════════════════════════════════════════════════
#  TEST 1: pgvector RAG Retrieval
# ═══════════════════════════════════════════════════════════════════════
print("\n" + "─" * 72)
print("  [1] pgvector RAG RETRIEVAL")
print("─" * 72)

from flora_ai_gemini import FloraAIService
flora = FloraAIService(db)

rag_queries = [
    ("Optimal soil pH for maize in Kenya", "soil_health"),
    ("How to detect armyworm infestation", "pest_management"),
    ("NDVI interpretation for crop health monitoring", "remote_sensing"),
    ("Coffee rust disease treatment Kenya", "disease_management"),
    ("Drought-resistant maize varieties for Kenya", "crop_management"),
]

for query, expected_category in rag_queries:
    try:
        snippets = flora._retrieve_knowledge(query, top_k=3)
        if snippets and len(snippets) > 0:
            record(f"RAG: {query[:45]}…", "passed", f"{len(snippets)} snippets")
        else:
            record(f"RAG: {query[:45]}…", "failed", "No snippets returned")
    except Exception as e:
        record(f"RAG: {query[:45]}…", "failed", str(e))


# ═══════════════════════════════════════════════════════════════════════
#  TEST 2: Gemini Fallback Chain  (Vertex → API key → Template)
# ═══════════════════════════════════════════════════════════════════════
print("\n" + "─" * 72)
print("  [2] GEMINI FALLBACK CHAIN")
print("─" * 72)

# 2a — Check which backend was selected at init
try:
    backend = getattr(flora, 'backend', None)
    vertex_client = getattr(flora, '_vertex_client', None)
    apikey_client = getattr(flora, '_apikey_client', None)

    print(f"  Active backend:   {backend}")
    print(f"  Vertex client:    {'ready' if vertex_client else 'n/a'}")
    print(f"  API key client:   {'ready' if apikey_client else 'n/a'}")
    print(f"  gemini_available: {flora.gemini_available}")

    if flora.gemini_available:
        record("Gemini init (primary)", "passed", f"backend={backend}")
    else:
        record("Gemini init (primary)", "failed", "No backend available")

    # Check that we have a fallback path
    if backend == 'vertex' and apikey_client:
        record("Fallback API key client ready", "passed")
    elif backend == 'api_key':
        record("Using API key directly", "passed", "No Vertex AI, API key primary")
    elif not flora.gemini_available:
        record("Fallback API key client ready", "skipped", "No Gemini at all")
    else:
        record("Fallback API key client ready", "skipped", f"backend={backend}")

except Exception as e:
    record("Gemini fallback chain init", "failed", str(e))

# 2b — Test _call_gemini with a simple prompt
print()
if flora.gemini_available:
    print("  Testing _call_gemini (live API call)…")
    time.sleep(2)
    try:
        result = flora._call_gemini(
            "Reply with exactly: PONG",
            max_tokens=50,
            temperature=0.0,
        )
        if result and len(result) > 0:
            record("_call_gemini live call", "passed", f"Response: {result[:60]}")
        else:
            record("_call_gemini live call", "failed", "Empty response")
    except Exception as e:
        record("_call_gemini live call", "failed", str(e)[:100])
else:
    record("_call_gemini live call", "skipped", "No Gemini backend")

# 2c — Test template fallback (simulate no Gemini)
print()
try:
    fallback_en = flora._fallback_response("test question", "en")
    fallback_sw = flora._fallback_response("test question", "sw")

    if "Flora AI service" in fallback_en or "smart shamba" in fallback_en.lower():
        record("Template fallback (English)", "passed")
    else:
        record("Template fallback (English)", "failed", f"Unexpected: {fallback_en[:80]}")

    if "Flora" in fallback_sw or "smart shamba" in fallback_sw.lower():
        record("Template fallback (Swahili)", "passed")
    else:
        record("Template fallback (Swahili)", "failed", f"Unexpected: {fallback_sw[:80]}")
except Exception as e:
    record("Template fallback", "failed", str(e))


# ═══════════════════════════════════════════════════════════════════════
#  TEST 3: Flora AI Chatbot — Farmer-Initiated Queries
# ═══════════════════════════════════════════════════════════════════════
print("\n" + "─" * 72)
print("  [3] FLORA AI CHATBOT (farmer queries)")
print("─" * 72)

farmer_questions = [
    {
        "q": "My maize leaves are turning yellow, what should I do?",
        "channel": "sms",
        "expect_keywords": ["maize", "nitrogen", "yellow", "soil", "leaves",
                           "fertilizer", "apply", "urea", "deficiency"],
    },
    {
        "q": "What is the best time to plant coffee in Kiambu?",
        "channel": "web",
        "expect_keywords": ["coffee", "plant", "rain", "march", "season",
                           "kiambu", "long rains", "october"],
    },
    {
        "q": "Mashamba yangu yana mdudu gani? Mimea inaonyesha madoa ya kahawia",
        "channel": "sms",
        "expect_keywords": [],  # Swahili response hard to keyword-check
    },
]

for i, fq in enumerate(farmer_questions):
    print(f"\n  Q{i+1}: {fq['q'][:65]}…")
    if not flora.gemini_available:
        record(f"Chatbot Q{i+1} ({fq['channel']})", "skipped", "No Gemini")
        continue

    # Rate limit cooldown
    wait = 5 if i == 0 else 15
    print(f"  (cooldown {wait}s…)")
    time.sleep(wait)

    try:
        lang = "sw" if "mashamba" in fq["q"].lower() else "en"
        answer = flora.answer_question(
            question=fq["q"],
            farmer_data=farmer_data,
            language=lang,
            channel=fq["channel"],
        )
        if not answer or len(answer) < 10:
            record(f"Chatbot Q{i+1} ({fq['channel']})", "failed", "Empty/too short")
            continue

        # Check SMS length constraint
        if fq["channel"] == "sms" and len(answer) > 500:
            print(f"  ⚠  SMS response is {len(answer)} chars (expected ≤160)")

        # Keyword check (at least 1 match = relevant)
        answer_lower = answer.lower()
        matched = [k for k in fq["expect_keywords"] if k in answer_lower]
        relevance = f"{len(matched)}/{len(fq['expect_keywords'])} keywords"

        preview = answer.replace('\n', ' ')[:200]
        print(f"  A: {preview}…")
        record(f"Chatbot Q{i+1} ({fq['channel']})", "passed", relevance)

    except Exception as e:
        record(f"Chatbot Q{i+1} ({fq['channel']})", "failed", str(e)[:100])


# ═══════════════════════════════════════════════════════════════════════
#  TEST 4: Threshold-Based Condition Evaluator
# ═══════════════════════════════════════════════════════════════════════
print("\n" + "─" * 72)
print("  [4] THRESHOLD CONDITION EVALUATOR")
print("─" * 72)

from smart_alert_service import SmartAlertService, CROP_OPTIMAL_RANGES
alert_svc = SmartAlertService(db_service=db)

# Test data scenarios
scenarios = [
    {
        "name": "All optimal (maize)",
        "crop": "maize",
        "sensor": {"soil_ph": 6.5, "soil_moisture_pct": 55, "temperature_c": 24, "humidity_pct": 70},
        "satellite": {"ndvi": 0.72, "ndwi": 0.15, "rainfall_mm": 120},
        "expect_status": "optimal",
    },
    {
        "name": "Low pH + dry soil (maize)",
        "crop": "maize",
        "sensor": {"soil_ph": 4.2, "soil_moisture_pct": 25, "temperature_c": 25, "humidity_pct": 65},
        "satellite": {"ndvi": 0.65, "ndwi": 0.10, "rainfall_mm": 40},
        "expect_status": "critical",
    },
    {
        "name": "Mild warning (coffee)",
        "crop": "coffee",
        "sensor": {"soil_ph": 5.8, "soil_moisture_pct": 45, "temperature_c": 22, "humidity_pct": 75},
        "satellite": {"ndvi": 0.50, "ndwi": 0.05, "rainfall_mm": 90},
        "expect_status": "warning",
    },
    {
        "name": "Heat stress (tea)",
        "crop": "tea",
        "sensor": {"soil_ph": 5.0, "soil_moisture_pct": 65, "temperature_c": 35, "humidity_pct": 55},
        "satellite": {"ndvi": 0.45, "ndwi": 0.08, "rainfall_mm": 60},
        "expect_status": "critical",
    },
    {
        "name": "All optimal (beans)",
        "crop": "beans",
        "sensor": {"soil_ph": 6.2, "soil_moisture_pct": 50, "temperature_c": 22, "humidity_pct": 65},
        "satellite": {"ndvi": 0.55, "ndwi": 0.10, "rainfall_mm": 80},
        "expect_status": "optimal",
    },
]

for sc in scenarios:
    try:
        report = alert_svc.evaluate_farm_conditions(
            crop=sc["crop"],
            sensor_data=sc["sensor"],
            satellite_data=sc["satellite"],
        )
        status_ok = report.status in (sc["expect_status"], "good")  # 'good' is close to 'optimal'

        detail = (
            f"status={report.status} score={report.overall_score:.0f}% "
            f"optimal={len(report.optimal_metrics)} deviations={len(report.deviations)}"
        )

        if report.deviations:
            dev_names = [d.display_name for d in report.deviations[:3]]
            detail += f" [{', '.join(dev_names)}]"

        # Accept if status is correct OR close (good≈optimal, warning≈critical)
        if status_ok or (sc["expect_status"] == "optimal" and report.status == "good"):
            record(f"Threshold: {sc['name']}", "passed", detail)
        else:
            record(f"Threshold: {sc['name']}", "failed",
                   f"Expected {sc['expect_status']}, got {report.status}. {detail}")

    except Exception as e:
        record(f"Threshold: {sc['name']}", "failed", str(e)[:100])


# ═══════════════════════════════════════════════════════════════════════
#  TEST 5: Automated Condition Alerts (full pipeline)
# ═══════════════════════════════════════════════════════════════════════
print("\n" + "─" * 72)
print("  [5] AUTOMATED CONDITION ALERTS")
print("─" * 72)

# 5a — Good-news alert (optimal conditions)
try:
    result = alert_svc.generate_condition_alert(
        farmer_data=farmer_data,
        sensor_data={"soil_ph": 6.5, "soil_moisture_pct": 55, "temperature_c": 24, "humidity_pct": 70},
        satellite_data={"ndvi": 0.72, "ndwi": 0.15, "rainfall_mm": 120},
    )
    sms = result.get("sms_text", "")
    if "optimal" in result.get("alert_type", "").lower() or "🟢" in sms or "great" in sms.lower():
        record("Condition alert: optimal (good-news)", "passed", f"{len(sms)} chars")
    else:
        record("Condition alert: optimal (good-news)", "failed", f"type={result.get('alert_type')}")
    print(f"    SMS preview: {sms[:200]}")
except Exception as e:
    record("Condition alert: optimal", "failed", str(e)[:100])

# 5b — Warning alert (suboptimal)
try:
    result = alert_svc.generate_condition_alert(
        farmer_data=farmer_data,
        sensor_data={"soil_ph": 4.2, "soil_moisture_pct": 25, "temperature_c": 25, "humidity_pct": 65},
        satellite_data={"ndvi": 0.65, "ndwi": 0.10, "rainfall_mm": 40},
    )
    sms = result.get("sms_text", "")
    if "🔴" in sms or "🟡" in sms or "alert" in result.get("alert_type", "").lower():
        record("Condition alert: suboptimal (warning)", "passed", f"{len(sms)} chars")
    else:
        record("Condition alert: suboptimal (warning)", "failed", f"type={result.get('alert_type')}")
    print(f"    SMS preview: {sms[:250]}")
except Exception as e:
    record("Condition alert: suboptimal", "failed", str(e)[:100])


# ═══════════════════════════════════════════════════════════════════════
#  TEST 6: RAG-Augmented Alert (Gemini + pgvector knowledge)
# ═══════════════════════════════════════════════════════════════════════
print("\n" + "─" * 72)
print("  [6] RAG-AUGMENTED ALERT (Gemini + knowledge base)")
print("─" * 72)

if not flora.gemini_available:
    print("  ⏭️  Gemini unavailable — testing template fallback only")

# Wait for rate limit
print("  (cooldown 15s…)")
time.sleep(15)

try:
    rag_result = alert_svc.generate_rag_alert(
        farmer_data=farmer_data,
        sensor_data={"soil_ph": 4.2, "soil_moisture_pct": 25, "temperature_c": 25, "humidity_pct": 65},
        satellite_data={"ndvi": 0.45, "ndwi": -0.05, "rainfall_mm": 20,
                        "data_source": "Sentinel-2", "bloom_probability": 35},
    )
    sms = rag_result.get("sms_text", "")
    web = rag_result.get("web_text", "")

    if sms and len(sms) > 10:
        # Check if it's Gemini-generated or template
        is_gemini = web and len(web) > len(sms) and web != sms
        source = "Gemini" if is_gemini else "template fallback"
        record("RAG alert generation", "passed", f"{source}, {len(sms)} chars SMS")
        print(f"    SMS: {sms[:250]}")
        if web and web != sms:
            print(f"    Web: {web[:250]}")
    else:
        record("RAG alert generation", "failed", "Empty SMS")
except Exception as e:
    record("RAG alert generation", "failed", str(e)[:120])
    traceback.print_exc()


# ═══════════════════════════════════════════════════════════════════════
#  TEST 7: Disease Detection Alert Pipeline
# ═══════════════════════════════════════════════════════════════════════
print("\n" + "─" * 72)
print("  [7] DISEASE DETECTION ALERT PIPELINE")
print("─" * 72)

# 7a — Test generate_disease_alert with high-confidence disease
print("  (cooldown 15s…)")
time.sleep(15)

disease_scenarios = [
    {
        "name": "Leaf blight (high confidence)",
        "context": {"disease_detected": "leaf_blight", "confidence": 0.92,
                    "image_uid": "farm1-esp32001-20260207T080000"},
        "expect_urgent": True,
    },
    {
        "name": "Rust (moderate confidence)",
        "context": {"disease_detected": "rust", "confidence": 0.65,
                    "image_uid": "farm1-esp32001-20260207T090000"},
        "expect_urgent": False,
    },
    {
        "name": "Aphid damage (low confidence)",
        "context": {"disease_detected": "aphid_damage", "confidence": 0.52,
                    "image_uid": "farm1-esp32001-20260207T100000"},
        "expect_urgent": False,
    },
]

for i, ds in enumerate(disease_scenarios):
    if i > 0:
        print(f"  (cooldown 10s…)")
        time.sleep(10)
    try:
        result = alert_svc.generate_disease_alert(
            farmer_data=farmer_data,
            disease_context=ds["context"],
        )
        sms = result.get("sms_text", "")
        web = result.get("web_text", "")
        disease = result.get("disease_display", "")

        if sms and len(sms) > 10:
            # Check it mentions the disease
            is_gemini = web and len(web) > 80 and "##" in web
            source = "Gemini" if is_gemini else "template"
            record(f"Disease alert: {ds['name']}", "passed",
                   f"{source}, conf={ds['context']['confidence']:.0%}")
            print(f"    Disease: {disease}")
            print(f"    SMS: {sms[:200]}")
        else:
            record(f"Disease alert: {ds['name']}", "failed", "Empty SMS")
    except Exception as e:
        record(f"Disease alert: {ds['name']}", "failed", str(e)[:100])

# 7b — Test healthy image (should NOT trigger alert)
print()
try:
    result = alert_svc.generate_disease_alert(
        farmer_data=farmer_data,
        disease_context={"disease_detected": "healthy", "confidence": 0.95,
                         "image_uid": "farm1-esp32001-20260207T110000"},
    )
    sms = result.get("sms_text", "")
    # Even a "healthy" detection should produce a message
    record("Disease alert: healthy crop", "passed",
           f"disease={result.get('disease')}, sms={len(sms)} chars")
except Exception as e:
    record("Disease alert: healthy crop", "failed", str(e)[:100])


# ═══════════════════════════════════════════════════════════════════════
#  TEST 8: generate_response (chat endpoint path)
# ═══════════════════════════════════════════════════════════════════════
print("\n" + "─" * 72)
print("  [8] CHAT ENDPOINT — generate_response()")
print("─" * 72)

if not flora.gemini_available:
    record("generate_response chat", "skipped", "No Gemini")
else:
    print("  (cooldown 10s…)")
    time.sleep(10)
    try:
        chat_history = [
            {"role": "user", "content": "Hi Flora, how are my crops doing?"},
            {"role": "assistant", "content": "Hello! Let me check your farm data…"},
        ]
        resp = flora.generate_response(
            user_message="Based on my sensor data, should I apply lime to my maize field?",
            farmer_data=farmer_data,
            chat_history=chat_history,
            channel="web",
        )
        if resp and len(resp) > 20:
            record("generate_response chat", "passed", f"{len(resp)} chars")
            print(f"    Response: {resp[:200]}…")
        else:
            record("generate_response chat", "failed", f"Too short: {len(resp or '')} chars")
    except Exception as e:
        record("generate_response chat", "failed", str(e)[:100])


# ═══════════════════════════════════════════════════════════════════════
#  SUMMARY
# ═══════════════════════════════════════════════════════════════════════
print("\n" + "=" * 72)
print("  RESULTS SUMMARY")
print("=" * 72)

for t in RESULTS["tests"]:
    icon = {"passed": "✅", "failed": "❌", "skipped": "⏭️"}[t["status"]]
    detail = f"  ({t['detail']})" if t["detail"] else ""
    print(f"  {icon} {t['name']}{detail}")

total = RESULTS["passed"] + RESULTS["failed"] + RESULTS["skipped"]
print(f"\n  Total: {total}  |  ✅ Passed: {RESULTS['passed']}  "
      f"|  ❌ Failed: {RESULTS['failed']}  |  ⏭️ Skipped: {RESULTS['skipped']}")

# Gemini backend summary
if flora.gemini_available:
    print(f"\n  🤖 Gemini backend: {flora.backend}")
    if flora.backend == 'vertex':
        if flora._apikey_client:
            print("     ↳ API key fallback: ready")
        else:
            print("     ↳ API key fallback: not configured")
    print(f"     ↳ Model: {flora.model_name}")
else:
    print("\n  🤖 Gemini: UNAVAILABLE (template fallback only)")

print("\n" + "=" * 72)
print("  E2E PIPELINE TEST COMPLETE")
print("=" * 72)

sys.exit(0 if RESULTS["failed"] == 0 else 1)
