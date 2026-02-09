"""
End-to-end test for Flora AI triage, context awareness, and response quality.
Tests: greeting detection, farming intent, general questions, gibberish,
       multilingual support, typo tolerance, and conversation context.
"""

import sys
import json
import time

# ── Init ──────────────────────────────────────────────────────────────────
from flora_ai_gemini import FloraAIService

svc = FloraAIService()
if not svc.gemini_available:
    print("✗ Gemini not available — cannot run live tests")
    sys.exit(1)
print(f"✓ Flora AI ready  ({svc.backend} / {svc.model_name})\n")

PASS = 0
FAIL = 0


def check(label: str, result, expected_intent: str = None,
          should_contain: list = None, should_not_contain: list = None):
    """Validate a single test case."""
    global PASS, FAIL
    ok = True
    issues = []

    if expected_intent and result.get("_intent") != expected_intent:
        issues.append(f"intent={result.get('_intent')} expected={expected_intent}")
        ok = False

    reply = result.get("reply", "")
    if should_contain:
        for term in should_contain:
            if term.lower() not in reply.lower():
                issues.append(f"missing '{term}'")
                ok = False
    if should_not_contain:
        for term in should_not_contain:
            if term.lower() in reply.lower():
                issues.append(f"should NOT contain '{term}'")
                ok = False

    if not reply or len(reply) < 5:
        issues.append("reply too short or empty")
        ok = False

    status = "✓" if ok else "✗"
    if ok:
        PASS += 1
    else:
        FAIL += 1

    print(f"  {status} {label}")
    if issues:
        print(f"     Issues: {', '.join(issues)}")
    # Show first 120 chars of reply
    print(f"     Reply: {reply[:120]}{'…' if len(reply) > 120 else ''}")
    print()


def triage_and_respond(message, farmer_data=None, chat_history=None):
    """Run triage + generate_response together, returning result + intent."""
    triage = svc._triage_message(message)
    result = svc.generate_response(
        user_message=message,
        farmer_data=farmer_data,
        chat_history=chat_history,
    )
    result["_intent"] = triage["intent"]
    result["_language"] = triage["language"]
    return result


# ══════════════════════════════════════════════════════════════════════════
#  1. GREETING DETECTION
# ══════════════════════════════════════════════════════════════════════════
print("=" * 60)
print("1. GREETING DETECTION")
print("=" * 60)

greetings = [
    ("hello", "English hello"),
    ("hi flora", "Casual hi"),
    ("habari yako", "Swahili greeting"),
    ("good morning", "English morning"),
    ("helo", "Typo greeting"),
    ("thanks a lot!", "Gratitude"),
]

for msg, label in greetings:
    r = triage_and_respond(msg)
    check(label, r, expected_intent="greeting")
    time.sleep(1)

# ══════════════════════════════════════════════════════════════════════════
#  2. FARMING INTENT
# ══════════════════════════════════════════════════════════════════════════
print("=" * 60)
print("2. FARMING INTENT")
print("=" * 60)

farming_qs = [
    ("How do I treat maize rust?", "Maize disease"),
    ("best fertilizer for tomatoes", "Fertilizer advice"),
    ("when should I plant beans in Nakuru?", "Planting calendar"),
    ("my cows are not producing enough milk", "Livestock question"),
    ("ndvi value 0.3 what does it mean", "NDVI interpretation"),
    ("maiz helth", "Typo: maize health"),
    ("weathr tomoro nairobi", "Typo: weather tomorrow"),
]

farmer = {
    "name": "John Ochieng",
    "phone": "+254712345678",
    "county": "Kisumu",
    "crops": ["maize", "sugarcane"],
    "farm_size": 3,
}

for msg, label in farming_qs:
    r = triage_and_respond(msg, farmer_data=farmer)
    check(label, r, expected_intent="farming")
    time.sleep(1)

# ══════════════════════════════════════════════════════════════════════════
#  3. GENERAL (NON-FARMING) QUESTIONS — should answer, not refuse
# ══════════════════════════════════════════════════════════════════════════
print("=" * 60)
print("3. GENERAL (NON-FARMING) QUESTIONS")
print("=" * 60)

general_qs = [
    ("What is the capital of France?", "Geography",
     ["paris"], ["sorry", "can't help", "only farming"]),
    ("How do I cook chapati?", "Recipe",
     [], ["I can only", "not related to farming"]),
    ("What is 25 x 17?", "Math",
     ["425"], ["sorry"]),
    ("Tell me a joke", "Humor",
     [], ["I can only", "cannot"]),
]

for msg, label, should_have, should_not in general_qs:
    r = triage_and_respond(msg)
    check(label, r, expected_intent="general",
          should_contain=should_have, should_not_contain=should_not)
    time.sleep(1)

# ══════════════════════════════════════════════════════════════════════════
#  4. GIBBERISH HANDLING
# ══════════════════════════════════════════════════════════════════════════
print("=" * 60)
print("4. GIBBERISH HANDLING")
print("=" * 60)

gibberish_msgs = [
    ("asdfghjkl", "Random letters"),
    ("zzzzz qqqq xxxx", "Keyboard smash"),
    ("12345 67890 abcde", "Random chars"),
]

for msg, label in gibberish_msgs:
    r = triage_and_respond(msg)
    check(label, r, expected_intent="gibberish")
    time.sleep(1)

# ══════════════════════════════════════════════════════════════════════════
#  5. MULTILINGUAL SUPPORT
# ══════════════════════════════════════════════════════════════════════════
print("=" * 60)
print("5. MULTILINGUAL SUPPORT")
print("=" * 60)

multilingual = [
    ("Nataka kujua jinsi ya kupanda mahindi", "Swahili farming", "sw"),
    ("Comment cultiver les tomates?", "French farming", "fr"),
]

for msg, label, expected_lang in multilingual:
    triage = svc._triage_message(msg)
    r = svc.generate_response(user_message=msg, farmer_data=farmer)
    r["_intent"] = triage["intent"]
    r["_language"] = triage["language"]

    lang_ok = triage["language"] == expected_lang
    status_lang = "✓" if lang_ok else f"✗ (got {triage['language']})"
    print(f"  Language detection {status_lang}")
    check(label, r, expected_intent="farming")
    time.sleep(1)

# ══════════════════════════════════════════════════════════════════════════
#  6. CONTEXT AWARENESS — farmer data used
# ══════════════════════════════════════════════════════════════════════════
print("=" * 60)
print("6. CONTEXT AWARENESS (farmer data)")
print("=" * 60)

r = triage_and_respond(
    "What should I do on my farm this week?",
    farmer_data=farmer,
)
check("Personalized advice w/ farmer context", r,
      expected_intent="farming",
      should_contain=["Kisumu"])
time.sleep(1)

# ══════════════════════════════════════════════════════════════════════════
#  7. CONVERSATION HISTORY CONTEXT
# ══════════════════════════════════════════════════════════════════════════
print("=" * 60)
print("7. CONVERSATION HISTORY")
print("=" * 60)

history = [
    {"role": "user", "content": "I'm growing tomatoes in Kiambu"},
    {"role": "assistant", "content": "Great! Tomatoes do well in Kiambu's climate..."},
]
r = triage_and_respond(
    "What pests should I watch out for?",
    farmer_data=farmer,
    chat_history=history,
)
check("Follow-up uses history (tomatoes)", r,
      expected_intent="farming",
      should_contain=["tomato"])
time.sleep(1)

# ══════════════════════════════════════════════════════════════════════════
#  SUMMARY
# ══════════════════════════════════════════════════════════════════════════
print("=" * 60)
total = PASS + FAIL
print(f"RESULTS: {PASS}/{total} passed, {FAIL} failed")
print("=" * 60)
if FAIL:
    sys.exit(1)
