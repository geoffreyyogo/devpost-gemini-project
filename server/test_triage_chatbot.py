#!/usr/bin/env python3
"""
Test suite for Flora AI triage + context-aware chatbot improvements.

Tests:
  1. Triage classification (greeting / farming / general / gibberish)
  2. Typo tolerance
  3. Multilingual detection
  4. Conversational replies for non-farming intents
  5. Farming intent → full RAG pipeline
  6. Context-awareness (farmer data injection)
"""

import os
import sys
import json
import time

# Ensure server/ is on path
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from flora_ai_gemini import FloraAIService

# ------------------------------------------------------------------ #
#  Test cases
# ------------------------------------------------------------------ #

TRIAGE_TESTS = [
    # (message, expected_intent, description)
    ("Hello!", "greeting", "Simple English greeting"),
    ("Hi Flora, how are you?", "greeting", "Greeting with name"),
    ("Habari yako?", "greeting", "Swahili greeting"),
    ("Thanks for the help!", "greeting", "Thank-you message"),
    ("Mambo vipi?", "greeting", "Informal Swahili greeting"),

    ("What fertilizer should I use for maize?", "farming", "Direct farming Q"),
    ("My tomatoes have yellow leaves", "farming", "Crop disease symptom"),
    ("When should I plant beans in Kisumu?", "farming", "Planting calendar Q"),
    ("What is NDVI?", "farming", "Technical agriculture term"),
    ("Best pesticide for aphids", "farming", "Pest control"),
    ("maiz helth", "farming", "Typo-heavy farming Q"),
    ("weathr tomoro for my farm", "farming", "Weather + farming with typos"),
    ("How much is fertilizer at the agrovet?", "farming", "Agrovet price Q"),

    ("What is the capital of France?", "general", "Geography Q"),
    ("Tell me a joke", "general", "Entertainment request"),
    ("How do I write a for loop in Python?", "general", "Coding question"),
    ("What is 25 times 13?", "general", "Math question"),

    ("asdfghjkl", "gibberish", "Keyboard smash"),
    ("qqqqwwww", "gibberish", "Random repeated chars"),
]

RESPONSE_TESTS = [
    # (message, farmer_data, description, checks)
    (
        "Hello!",
        {"name": "John Kamau", "county": "Kiambu"},
        "Greeting with farmer context",
        lambda r: len(r["reply"]) > 5 and "error" not in r["reply"].lower(),
    ),
    (
        "What fertilizer should I use for maize?",
        {"name": "Mary", "county": "Nakuru", "crops": ["maize"], "farm_size": 2},
        "Farming Q with full context",
        lambda r: len(r["reply"]) > 50,
    ),
    (
        "What is 2 + 2?",
        None,
        "General Q, no auth",
        lambda r: "4" in r["reply"],
    ),
    (
        "Habari! Mimea yangu inakufa",
        {"name": "Juma", "county": "Mombasa"},
        "Swahili farming Q",
        lambda r: len(r["reply"]) > 20,
    ),
    (
        "jjjkkklll",
        None,
        "Gibberish → polite redirect",
        lambda r: len(r["reply"]) > 10,
    ),
]


def run_triage_tests(service: FloraAIService):
    """Test the triage classifier."""
    print("\n" + "=" * 60)
    print("  TRIAGE CLASSIFICATION TESTS")
    print("=" * 60)

    passed = 0
    failed = 0

    for msg, expected, desc in TRIAGE_TESTS:
        result = service._triage_message(msg)
        intent = result["intent"]
        lang = result["language"]
        ok = intent == expected
        status = "✅" if ok else "❌"

        if ok:
            passed += 1
        else:
            failed += 1

        print(f"  {status} [{intent:10s}] lang={lang:3s} | {desc}")
        if not ok:
            print(f"       Expected: {expected}, Got: {intent}")

    print(f"\n  Results: {passed}/{passed + failed} passed")
    return passed, failed


def run_response_tests(service: FloraAIService):
    """Test full generate_response pipeline."""
    print("\n" + "=" * 60)
    print("  RESPONSE GENERATION TESTS")
    print("=" * 60)

    passed = 0
    failed = 0

    for msg, farmer_data, desc, check in RESPONSE_TESTS:
        try:
            t0 = time.time()
            result = service.generate_response(
                user_message=msg,
                farmer_data=farmer_data,
                chat_history=None,
                channel="web",
            )
            elapsed = time.time() - t0

            ok = check(result)
            status = "✅" if ok else "❌"

            if ok:
                passed += 1
            else:
                failed += 1

            reply_preview = result["reply"][:120].replace("\n", " ")
            print(f"\n  {status} {desc} ({elapsed:.1f}s)")
            print(f"     Q: {msg}")
            print(f"     A: {reply_preview}...")
        except Exception as e:
            failed += 1
            print(f"\n  ❌ {desc}")
            print(f"     Error: {e}")

    print(f"\n  Results: {passed}/{passed + failed} passed")
    return passed, failed


def run_context_test(service: FloraAIService):
    """Test that farmer context is properly injected."""
    print("\n" + "=" * 60)
    print("  CONTEXT-AWARENESS TEST")
    print("=" * 60)

    farmer = {
        "name": "Geoffrey Yogo",
        "county": "Kisumu",
        "sub_county": "Kisumu Central",
        "crops": ["maize", "sugarcane"],
        "farm_size": 5,
    }

    result = service.generate_response(
        user_message="How is the weather looking for my crops?",
        farmer_data=farmer,
        chat_history=[
            {"role": "user", "content": "Hello Flora"},
            {"role": "assistant", "content": "Hello Geoffrey! How can I help you today?"},
        ],
        channel="web",
    )

    reply = result["reply"]
    print(f"  Reply ({len(reply)} chars):")
    print(f"  {reply[:300]}...")

    # Check context signals
    checks = {
        "Reply is non-empty": len(reply) > 50,
        "Has substantive content": len(reply) > 100,
    }

    all_ok = True
    for label, ok in checks.items():
        status = "✅" if ok else "❌"
        print(f"  {status} {label}")
        if not ok:
            all_ok = False

    return (1, 0) if all_ok else (0, 1)


if __name__ == "__main__":
    print("🌿 Flora AI Triage & Context-Awareness Test Suite")
    print("=" * 60)

    service = FloraAIService()

    if not service.gemini_available:
        print("❌ Gemini is not available. Set GEMINI_API_KEY or configure Vertex AI.")
        sys.exit(1)

    print(f"✅ Gemini ready (model: {service.model_name})")

    total_passed = 0
    total_failed = 0

    p, f = run_triage_tests(service)
    total_passed += p
    total_failed += f

    p, f = run_response_tests(service)
    total_passed += p
    total_failed += f

    p, f = run_context_test(service)
    total_passed += p
    total_failed += f

    print("\n" + "=" * 60)
    print(f"  TOTAL: {total_passed}/{total_passed + total_failed} passed")
    if total_failed == 0:
        print("  🎉 All tests passed!")
    else:
        print(f"  ⚠️  {total_failed} test(s) failed")
    print("=" * 60)
