#!/usr/bin/env python3
"""
Diagnostic test: Flora AI chatbot for both authenticated and unauthenticated users.
Tests the full generate_response pipeline to identify failures.
"""

import os
import sys
import json
import time
import logging

# Ensure server/ is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.chdir(os.path.join(os.path.dirname(__file__), '..', '..'))

from dotenv import load_dotenv
load_dotenv()

# Set up visible logging
logging.basicConfig(
    level=logging.INFO,
    format='%(name)s: %(message)s',
    stream=sys.stderr,
)

from flora_ai_gemini import FloraAIService

def main():
    print("=" * 60)
    print("CHATBOT DIAGNOSTIC TEST")
    print("=" * 60)

    flora = FloraAIService()
    print(f"\nGemini available: {flora.gemini_available}")
    print(f"Backend: {flora.backend}")
    print(f"Model: {getattr(flora, 'model_name', 'N/A')}")

    if not flora.gemini_available:
        print("\n❌ FATAL: Gemini is not available. Cannot test chatbot.")
        print("Check GEMINI_API_KEY or Vertex AI configuration.")
        sys.exit(1)

    results = []

    # ── Test 1: RAG Knowledge Retrieval ──
    print("\n" + "-" * 60)
    print("TEST 1: RAG Knowledge Retrieval")
    print("-" * 60)
    try:
        snippets = flora._retrieve_knowledge('What is the optimal soil pH for maize?', top_k=3)
        ok = len(snippets) > 0
        print(f"  Snippets found: {len(snippets)} {'✅' if ok else '❌'}")
        for i, s in enumerate(snippets):
            print(f"    [{i}] {s[:100]}...")
        results.append(("RAG Retrieval", ok, None))
    except Exception as e:
        print(f"  ❌ ERROR: {type(e).__name__}: {e}")
        results.append(("RAG Retrieval", False, str(e)))

    # ── Test 2: Triage Classification ──
    print("\n" + "-" * 60)
    print("TEST 2: Triage Classification")
    print("-" * 60)
    triage_cases = [
        ("Hello!", "greeting"),
        ("My maize has yellow leaves", "farming"),
        ("What is 2+2?", "general"),
    ]
    for msg, expected in triage_cases:
        try:
            result = flora._triage_message(msg)
            intent = result["intent"]
            ok = intent == expected
            status_emoji = "✅" if ok else "❌"
            print(f"  {status_emoji} '{msg}' → {intent} (expected: {expected})")
            results.append((f"Triage: {msg}", ok, None if ok else f"got {intent}"))
        except Exception as e:
            print(f"  ❌ '{msg}' → ERROR: {type(e).__name__}: {e}")
            results.append((f"Triage: {msg}", False, str(e)))

    # ── Test 3: Greeting reply (no RAG, lightweight) ──
    print("\n" + "-" * 60)
    print("TEST 3: Greeting Reply (unauthenticated)")
    print("-" * 60)
    try:
        t0 = time.time()
        result = flora.generate_response(
            user_message="Hello!",
            farmer_data=None,
            chat_history=None,
            channel="web",
        )
        elapsed = time.time() - t0
        reply = result.get("reply", "")
        ok = len(reply) > 5
        status_emoji = "✅" if ok else "❌"
        print(f"  {status_emoji} Reply ({elapsed:.1f}s, {len(reply)} chars): {reply[:200]}")
        results.append(("Greeting (unauth)", ok, None if ok else "empty reply"))
    except Exception as e:
        print(f"  ❌ ERROR: {type(e).__name__}: {e}")
        results.append(("Greeting (unauth)", False, str(e)))

    # ── Test 4: Farming question — unauthenticated, NO location ──
    print("\n" + "-" * 60)
    print("TEST 4: Farming Q (unauth, no location)")
    print("-" * 60)
    try:
        t0 = time.time()
        result = flora.generate_response(
            user_message="How do I deal with pests on my farm?",
            farmer_data=None,
            chat_history=None,
            channel="web",
        )
        elapsed = time.time() - t0
        reply = result.get("reply", "")
        ok = len(reply) > 20
        status_emoji = "✅" if ok else "❌"
        print(f"  {status_emoji} Reply ({elapsed:.1f}s, {len(reply)} chars): {reply[:200]}")
        results.append(("Farming Q (unauth, no loc)", ok, None if ok else "empty/short reply"))
    except Exception as e:
        print(f"  ❌ ERROR: {type(e).__name__}: {e}")
        results.append(("Farming Q (unauth, no loc)", False, str(e)))

    # ── Test 5: Farming question — unauthenticated, WITH location ──
    print("\n" + "-" * 60)
    print("TEST 5: Farming Q (unauth, with location in message)")
    print("-" * 60)
    try:
        t0 = time.time()
        result = flora.generate_response(
            user_message="What fertilizer should I use for maize in Kiambu?",
            farmer_data=None,
            chat_history=None,
            channel="web",
        )
        elapsed = time.time() - t0
        reply = result.get("reply", "")
        ok = len(reply) > 50
        status_emoji = "✅" if ok else "❌"
        print(f"  {status_emoji} Reply ({elapsed:.1f}s, {len(reply)} chars): {reply[:200]}")
        results.append(("Farming Q (unauth, with loc)", ok, None if ok else "empty/short reply"))
    except Exception as e:
        print(f"  ❌ ERROR: {type(e).__name__}: {e}")
        results.append(("Farming Q (unauth, with loc)", False, str(e)))

    # ── Test 6: Farming question — authenticated farmer ──
    print("\n" + "-" * 60)
    print("TEST 6: Farming Q (authenticated farmer)")
    print("-" * 60)
    farmer_data = {
        "name": "John Kamau",
        "phone": "+254712345678",
        "county": "Kiambu",
        "sub_county": "Thika",
        "region": "central",
        "crops": ["coffee", "maize", "beans"],
        "farm_size": 5,
        "language": "en",
    }
    try:
        t0 = time.time()
        result = flora.generate_response(
            user_message="My maize leaves are turning yellow. What could be wrong?",
            farmer_data=farmer_data,
            chat_history=None,
            channel="web",
        )
        elapsed = time.time() - t0
        reply = result.get("reply", "")
        reasoning = result.get("reasoning")
        ok = len(reply) > 50
        status_emoji = "✅" if ok else "❌"
        print(f"  {status_emoji} Reply ({elapsed:.1f}s, {len(reply)} chars): {reply[:200]}")
        print(f"      Has reasoning: {bool(reasoning)}")
        results.append(("Farming Q (auth)", ok, None if ok else "empty/short reply"))
    except Exception as e:
        print(f"  ❌ ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Farming Q (auth)", False, str(e)))

    # ── Test 7: answer_question directly ──
    print("\n" + "-" * 60)
    print("TEST 7: answer_question (direct call, auth farmer)")
    print("-" * 60)
    try:
        t0 = time.time()
        result = flora.answer_question(
            question="When should I plant beans?",
            farmer_data=farmer_data,
            language="en",
            channel="web",
        )
        elapsed = time.time() - t0
        reply = result.get("reply", "") if isinstance(result, dict) else str(result)
        ok = len(reply) > 20
        status_emoji = "✅" if ok else "❌"
        print(f"  {status_emoji} Reply ({elapsed:.1f}s, {len(reply)} chars): {reply[:200]}")
        results.append(("answer_question (auth)", ok, None if ok else "empty/short reply"))
    except Exception as e:
        print(f"  ❌ ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        results.append(("answer_question (auth)", False, str(e)))

    # ── Summary ──
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    passed = sum(1 for _, ok, _ in results if ok)
    failed = sum(1 for _, ok, _ in results if not ok)
    for name, ok, error in results:
        emoji = "✅" if ok else "❌"
        detail = f" — {error}" if error else ""
        print(f"  {emoji} {name}{detail}")
    print(f"\n  Total: {passed}/{passed + failed} passed")
    if failed > 0:
        print(f"  ⚠️  {failed} test(s) FAILED")
        sys.exit(1)
    else:
        print("  🎉 All tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
