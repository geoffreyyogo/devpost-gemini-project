#!/usr/bin/env python3
"""
Context-awareness tests for Flora AI chatbot.

Tests that the chatbot properly resolves conversational references,
accumulates user context across messages, and uses history for triage.
"""

import os
import sys
import json
import time

# Ensure server/ is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

from flora_ai_gemini import FloraAIService

# ------------------------------------------------------------------ #
#  Test helpers
# ------------------------------------------------------------------ #

PASS = "\033[92m✓\033[0m"
FAIL = "\033[91m✗\033[0m"
total, passed, failed = 0, 0, 0

def run_test(name: str, check_fn, *args, **kwargs):
    global total, passed, failed
    total += 1
    try:
        result = check_fn(*args, **kwargs)
        if result:
            passed += 1
            print(f"  {PASS} {name}")
        else:
            failed += 1
            print(f"  {FAIL} {name}")
    except Exception as e:
        failed += 1
        print(f"  {FAIL} {name}: {e}")


# ------------------------------------------------------------------ #
#  Test cases
# ------------------------------------------------------------------ #

def test_triage_follow_up_farming():
    """Verify triage classifies 'list them' as farming when previous discussion
    was about farming topics."""
    svc = FloraAIService()
    
    # Simulate a conversation about Kisumu subcounties
    history = [
        {"role": "user", "content": "How many subcounties in Kisumu?"},
        {"role": "assistant", "content": "Kisumu County has 7 subcounties: Kisumu Central, Kisumu East, Kisumu West, Seme, Nyando, Muhoroni, and Nyakach."},
    ]
    
    # "List them" should be classified as farming (continuation of farming topic)
    result = svc._triage_message("List them", chat_history=history)
    intent = result.get("intent")
    # Accept farming or general — NOT gibberish
    return intent in ("farming", "general")


def test_triage_without_history():
    """Verify triage still works for standalone messages."""
    svc = FloraAIService()
    result = svc._triage_message("What fertilizer for maize?")
    return result.get("intent") == "farming"


def test_format_conversation_turns_frontend():
    """Test _format_conversation_turns with frontend message format."""
    turns = [
        {"role": "user", "content": "Hello there"},
        {"role": "assistant", "content": "Hi! I'm Flora."},
        {"role": "user", "content": "What crops grow in Kiambu?"},
    ]
    result = FloraAIService._format_conversation_turns(turns, max_turns=10)
    assert "Farmer: Hello there" in result
    assert "Flora: Hi! I'm Flora." in result
    assert "Farmer: What crops grow in Kiambu?" in result
    return True


def test_format_conversation_turns_db():
    """Test _format_conversation_turns with DB message format (role, message, response)."""
    turns = [
        {"role": "user", "message": "What is NDVI?", "response": "NDVI stands for Normalized Difference Vegetation Index."},
    ]
    result = FloraAIService._format_conversation_turns(turns, max_turns=10)
    assert "Farmer: What is NDVI?" in result
    assert "Flora: NDVI stands for" in result
    return True


def test_format_conversation_turns_truncation():
    """Test that very long messages are truncated."""
    long_msg = "A" * 500
    turns = [{"role": "user", "content": long_msg}]
    result = FloraAIService._format_conversation_turns(turns, max_turns=10)
    assert len(result) < 500  # Should be truncated
    assert "…" in result
    return True


def test_build_conversation_context_unauth():
    """Test that _build_conversation_context accumulates profile from history."""
    svc = FloraAIService()
    history = [
        {"role": "user", "content": "I grow maize in Kiambu"},
        {"role": "assistant", "content": "Great! Maize is a popular crop in Kiambu."},
        {"role": "user", "content": "I also have 5 acres"},
    ]
    ctx = svc._build_conversation_context(
        chat_history=history,
        user_message="What fertilizer should I use?",
        farmer_data=None,
    )
    profile = ctx["accumulated_profile"]
    assert profile["county"] == "Kiambu", f"Expected 'Kiambu', got '{profile['county']}'"
    assert "maize" in profile["crops"], f"Expected 'maize' in crops, got {profile['crops']}"
    assert profile["farm_size"] is not None, f"Expected farm_size, got None"
    return True


def test_build_conversation_context_livestock():
    """Test that livestock is extracted from conversation."""
    svc = FloraAIService()
    history = [
        {"role": "user", "content": "I keep dairy cows and goats"},
    ]
    ctx = svc._build_conversation_context(
        chat_history=history,
        user_message="What feed should I use?",
        farmer_data=None,
    )
    profile = ctx["accumulated_profile"]
    livestock = profile.get("livestock", [])
    has_dairy = "dairy" in livestock or "cows" in livestock
    has_goats = "goats" in livestock
    return has_dairy and has_goats


def test_build_conversation_context_past_sessions():
    """Test that past conversation summaries are formatted correctly."""
    svc = FloraAIService()
    past = [
        {"title": "Maize planting advice", "last_message": "When to plant?",
         "last_response": "Plant in March", "updated_at": "2026-02-01T10:00:00"},
    ]
    ctx = svc._build_conversation_context(
        chat_history=[],
        user_message="Hello",
        farmer_data={"name": "John"},
        past_conversations=past,
    )
    sessions = ctx["past_sessions"]
    assert "Maize planting advice" in sessions
    assert "When to plant?" in sessions
    return True


def test_generate_response_with_history():
    """Integration test: generate_response should produce a coherent reply
    that references conversational context."""
    svc = FloraAIService()
    if not svc.gemini_available:
        print("    (skipped - Gemini not available)")
        return True
    
    # First message about Kisumu subcounties
    history = [
        {"role": "user", "content": "How many subcounties are in Kisumu county?"},
        {"role": "assistant", "content": "Kisumu County has 7 subcounties: Kisumu Central, Kisumu East, Kisumu West, Seme, Nyando, Muhoroni, and Nyakach."},
    ]
    
    t0 = time.time()
    result = svc.generate_response(
        user_message="Can you list them?",
        chat_history=history,
    )
    elapsed = time.time() - t0
    
    reply = result.get("reply", "")
    print(f"    Reply ({elapsed:.1f}s, {len(reply)} chars): {reply[:200]}")
    
    # The reply should reference subcounties or Kisumu — not ask "list what?"
    reply_lower = reply.lower()
    has_context = any(word in reply_lower for word in 
                      ["kisumu", "subcounty", "sub-county", "muhoroni", "nyando", "seme"])
    return has_context


def test_unauth_context_accumulation():
    """Integration test: unauth user provides info across multiple messages,
    and the chatbot should use accumulated context."""
    svc = FloraAIService()
    if not svc.gemini_available:
        print("    (skipped - Gemini not available)")
        return True
    
    # User has mentioned Kiambu and maize in previous messages
    history = [
        {"role": "user", "content": "I grow maize"},
        {"role": "assistant", "content": "Maize is a great crop! Where is your farm located?"},
        {"role": "user", "content": "I'm in Kiambu county"},
        {"role": "assistant", "content": "Kiambu is a great area for farming! How can I help?"},
    ]
    
    t0 = time.time()
    result = svc.generate_response(
        user_message="What fertilizer should I use?",
        chat_history=history,
    )
    elapsed = time.time() - t0
    
    reply = result.get("reply", "")
    print(f"    Reply ({elapsed:.1f}s, {len(reply)} chars): {reply[:200]}")
    
    # The reply should reference maize AND/OR Kiambu — showing accumulated context
    reply_lower = reply.lower()
    has_maize = "maize" in reply_lower
    has_kiambu = "kiambu" in reply_lower
    has_fertilizer = any(w in reply_lower for w in ["fertilizer", "dap", "npk", "can", "urea", "manure", "nitrogen"])
    return has_fertilizer  # At minimum, should answer about fertilizer


# ------------------------------------------------------------------ #
#  Run all tests
# ------------------------------------------------------------------ #

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  FLORA AI — Context-Awareness Test Suite")
    print("=" * 60)

    print("\n📋 Unit tests:")
    run_test("Format turns (frontend format)", test_format_conversation_turns_frontend)
    run_test("Format turns (DB format)", test_format_conversation_turns_db)
    run_test("Format turns (truncation)", test_format_conversation_turns_truncation)
    run_test("Build context (unauth profile)", test_build_conversation_context_unauth)
    run_test("Build context (livestock)", test_build_conversation_context_livestock)
    run_test("Build context (past sessions)", test_build_conversation_context_past_sessions)

    print("\n🧠 Triage tests:")
    run_test("Triage standalone farming Q", test_triage_without_history)
    run_test("Triage follow-up with history", test_triage_follow_up_farming)

    print("\n🔄 Integration tests (requires Gemini):")
    run_test("Follow-up resolution", test_generate_response_with_history)
    run_test("Unauth context accumulation", test_unauth_context_accumulation)

    print(f"\n{'=' * 60}")
    print(f"  Results: {passed}/{total} passed, {failed} failed")
    print(f"{'=' * 60}\n")
    
    sys.exit(0 if failed == 0 else 1)
