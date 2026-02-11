"""
Flora AI Service — Gemini + pgvector RAG Edition
Drop-in replacement for flora_ai_service.py.

Uses Google Gemini for generation and pgvector (ag_knowledge table)
for retrieval-augmented generation of agricultural advice.
"""

import os
import re
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------- Gemini ----------
try:
    from google import genai
    from google.genai import types as genai_types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None  # type: ignore[assignment]
    genai_types = None  # type: ignore[assignment]
    logger.warning("google-genai not installed — Flora AI will use fallback responses.")

# ---------- Embeddings (sentence-transformers for pgvector RAG) ----------
try:
    from sentence_transformers import SentenceTransformer
    _embed_model: Optional[SentenceTransformer] = None

    def _get_embed_model() -> SentenceTransformer:
        global _embed_model
        if _embed_model is None:
            _embed_model = SentenceTransformer("all-MiniLM-L6-v2")  # 384-dim
        return _embed_model

    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    logger.warning("sentence-transformers not installed — RAG disabled.")

    _get_embed_model = lambda: None  # type: ignore[assignment,misc]  # noqa: E731

# ---------- Database ----------
try:
    from database.connection import get_sync_session
    from database.models import AgKnowledge, ChatHistory
    from sqlmodel import select, text
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False
    get_sync_session = None  # type: ignore[assignment]
    AgKnowledge = None  # type: ignore[assignment,misc]
    ChatHistory = None  # type: ignore[assignment,misc]
    select = None  # type: ignore[assignment]
    text = None  # type: ignore[assignment]
    logger.warning("Database modules not available — RAG and chat history disabled.")


# ---------- County name lookup for unauth location extraction ----------
try:
    from kenya_counties_config import KENYA_COUNTIES
    # Build a lowercase name → county_id mapping for fast matching
    _COUNTY_NAME_TO_ID: Dict[str, str] = {}
    for _cid, _cinfo in KENYA_COUNTIES.items():
        _COUNTY_NAME_TO_ID[_cid.lower()] = _cid
        _COUNTY_NAME_TO_ID[_cinfo['name'].lower()] = _cid
except ImportError:
    KENYA_COUNTIES = {}  # type: ignore[assignment,misc]
    _COUNTY_NAME_TO_ID = {}
    logger.warning("kenya_counties_config not available — location extraction disabled.")

try:
    from kenya_sub_counties import KENYA_SUB_COUNTIES
except ImportError:
    KENYA_SUB_COUNTIES = {}  # type: ignore[assignment,misc]


class FloraAIService:
    """AI agricultural assistant powered by Gemini + pgvector RAG."""

    # Timeout (seconds) for each Gemini HTTP request.
    # Vertex AI can hang for minutes before returning 499 CANCELLED;
    # this ensures we fail fast and fall back to the API key client.
    _GEMINI_TIMEOUT_SECS: int = 30

    def __init__(self, db_service=None, weather_service=None):
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.use_vertex = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "").lower() in ("true", "1", "yes")
        self.vertex_project = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GEE_PROJECT_ID")
        self.vertex_location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
        self.gemini_available = False
        self.model = None
        self.backend = None  # 'vertex' | 'api_key' | None

        # Keep both clients so we can fallback at call-time
        self._vertex_client = None
        self._apikey_client = None
        # Track consecutive Vertex AI failures to proactively swap backend
        self._vertex_fail_count = 0
        self._VERTEX_FAIL_THRESHOLD = 2

        # HTTP options — each client uses its own default api_version
        _http_opts = genai_types.HttpOptions()  # type: ignore[union-attr]

        if not GEMINI_AVAILABLE:
            self.client = None
            logger.warning("⚠ google-genai not installed.")
        else:
            self.model_name = os.getenv("GEMINI_MODEL", "gemini-3.0-flash-001")

            # --- Try Vertex AI first ---
            if self.use_vertex and self.vertex_project:
                try:
                    self._vertex_client = genai.Client(  # type: ignore[union-attr]
                        vertexai=True,
                        project=self.vertex_project,
                        location=self.vertex_location,
                        http_options=_http_opts,
                    )
                    self.client = self._vertex_client
                    self.backend = 'vertex'
                    self.gemini_available = True
                    logger.info(f"✓ Flora AI initialized with Vertex AI ({self.model_name}) "
                                f"project={self.vertex_project} location={self.vertex_location}")
                except Exception as e:
                    logger.warning(f"⚠ Vertex AI init failed: {e}")

            # --- Try Gemini API key (primary or fallback) ---
            if self.api_key:
                try:
                    self._apikey_client = genai.Client(  # type: ignore[union-attr]
                        api_key=self.api_key,
                        vertexai=False,
                        http_options=_http_opts,
                    )
                    if not self.gemini_available:
                        self.client = self._apikey_client
                        self.backend = 'api_key'
                        self.gemini_available = True
                        logger.info(f"✓ Flora AI initialized with AI Studio ({self.model_name})")
                    else:
                        logger.info("  ↳ Gemini API key also available as runtime fallback")
                except Exception as e:
                    logger.warning(f"⚠ Gemini AI Studio init failed: {e}")

            if not self.gemini_available:
                self.client = None
                logger.warning("⚠ No Gemini credentials: set GOOGLE_GENAI_USE_VERTEXAI=true + "
                               "GOOGLE_CLOUD_PROJECT, or set GEMINI_API_KEY.")

        self.db_service = db_service
        self.weather_service = weather_service
        self.county_data_cache: Dict = {}

    # ------------------------------------------------------------------ #
    #  pgvector RAG — retrieve relevant knowledge
    # ------------------------------------------------------------------ #

    def _retrieve_knowledge(self, query: str, top_k: int = 3) -> List[str]:
        """Retrieve relevant agricultural knowledge via pgvector cosine similarity."""
        if not (DB_AVAILABLE and EMBEDDINGS_AVAILABLE):
            return []

        try:
            embed_model = _get_embed_model()
            if embed_model is None:
                return []

            query_vec = embed_model.encode(query).tolist()

            with get_sync_session() as session:  # type: ignore[misc]
                # pgvector cosine distance operator: <=>
                # Use CAST() instead of :: to avoid SQLAlchemy bind-param conflict
                sql = text(  # type: ignore[misc]
                    "SELECT doc_text, doc_category, 1 - (embedding <=> CAST(:vec AS vector)) AS score "
                    "FROM ag_knowledge "
                    "ORDER BY embedding <=> CAST(:vec AS vector) "
                    "LIMIT :k"
                )
                rows = session.exec(sql, params={"vec": str(query_vec), "k": top_k}).all()  # type: ignore[arg-type,call-overload]

            return [row[0] for row in rows if row[2] > 0.3]  # score threshold
        except Exception as e:
            logger.error(f"RAG retrieval error: {e}")
            return []

    def _store_knowledge(self, content: str, category: str = "general",
                         source: str = "manual") -> bool:
        """Add a knowledge entry with embedding to ag_knowledge."""
        if not (DB_AVAILABLE and EMBEDDINGS_AVAILABLE):
            return False

        try:
            embed_model = _get_embed_model()
            if embed_model is None:
                return False

            vec = embed_model.encode(content).tolist()

            with get_sync_session() as session:  # type: ignore[misc]
                entry = AgKnowledge(  # type: ignore[misc]
                    doc_text=content,
                    doc_category=category,
                    doc_source=source,
                    embedding=vec,
                )
                session.add(entry)
                session.commit()
            return True
        except Exception as e:
            logger.error(f"Knowledge storage error: {e}")
            return False

    # ------------------------------------------------------------------ #
    #  Location data helper (sub-county first, county fallback)
    # ------------------------------------------------------------------ #

    def get_county_data(self, county: str, sub_county: Optional[str] = None) -> Dict:
        """Fetch location data: try sub-county first, fall back to county."""
        cache_key = f"{county}:{sub_county}" if sub_county else county
        if cache_key in self.county_data_cache:
            return self.county_data_cache[cache_key]

        # 1) Try sub-county level data first (more localised)
        if sub_county and self.db_service and hasattr(self.db_service, 'get_sub_county_details'):
            try:
                data = self.db_service.get_sub_county_details(county, sub_county)
                if data and 'error' not in data:
                    data['_data_level'] = 'sub_county'
                    self.county_data_cache[cache_key] = data
                    logger.info(f"Using sub-county data for {sub_county}, {county}")
                    return data
            except Exception as e:
                logger.warning(f"PG sub-county lookup failed for {sub_county}, {county}: {e}")

        # 2) Fall back to county level data
        if self.db_service and hasattr(self.db_service, 'get_county_details'):
            try:
                data = self.db_service.get_county_details(county)
                if data and 'error' not in data:
                    data['_data_level'] = 'county'
                    self.county_data_cache[cache_key] = data
                    if sub_county:
                        logger.info(f"Sub-county data unavailable for {sub_county}; using county data for {county}")
                    return data
            except Exception as e:
                logger.warning(f"PG county lookup failed for {county}: {e}")

        logger.warning(f"No location data available for {county}")
        return {}

    # ------------------------------------------------------------------ #
    #  Location extraction from user messages (for unauth users)
    # ------------------------------------------------------------------ #

    @staticmethod
    def _extract_location_from_text(text_input: str) -> Dict:
        """
        Extract Kenyan county/sub-county and crop mentions from free text.
        Uses fast string matching against known county names — no API call needed.
        
        Returns:
            {"county": str|None, "county_id": str|None, "sub_county": str|None,
             "crops": List[str], "coordinates": Dict|None}
        """
        result: Dict = {"county": None, "county_id": None, "sub_county": None,
                        "crops": [], "coordinates": None}
        if not text_input:
            return result

        text_lower = text_input.lower()

        # --- Match county names ---
        best_county_id = None
        best_county_name = None
        for name, cid in _COUNTY_NAME_TO_ID.items():
            # Word-boundary match to avoid false positives (e.g. "meru" in "merugi")
            if re.search(rf'\b{re.escape(name)}\b', text_lower):
                # Prefer longer matches (e.g. "nyeri" over "yer")
                if best_county_name is None or len(name) > len(best_county_name):
                    best_county_id = cid
                    best_county_name = name

        if best_county_id and best_county_id in KENYA_COUNTIES:
            county_info = KENYA_COUNTIES[best_county_id]
            result["county"] = county_info["name"]
            result["county_id"] = best_county_id
            result["coordinates"] = county_info.get("coordinates")

            # Try to match sub-county within this county
            sc_data = KENYA_SUB_COUNTIES.get(best_county_id, {}).get("sub_counties", {})
            for sc_id, sc_info in sc_data.items():
                sc_name = sc_info.get("name", "").lower()
                if sc_name and re.search(rf'\b{re.escape(sc_name)}\b', text_lower):
                    result["sub_county"] = sc_info["name"]
                    result["coordinates"] = sc_info.get("coordinates", result["coordinates"])
                    break

        # --- Match common Kenyan crops ---
        crop_keywords = [
            "maize", "beans", "wheat", "rice", "coffee", "tea", "sugarcane",
            "sorghum", "millet", "cassava", "potatoes", "sweet potatoes",
            "bananas", "avocado", "mangoes", "tomatoes", "onions", "kale",
            "sukuma wiki", "spinach", "cabbage", "carrots", "peas", "cowpeas",
            "groundnuts", "sunflower", "sisal", "cotton", "pyrethrum",
            "macadamia", "cashew nuts", "coconut", "pigeon peas", "green grams",
            "finger millet", "soya beans", "barley", "oats", "napier grass",
            "watermelon", "pumpkin", "butternut", "capsicum", "french beans",
            "mahindi", "maharage", "ngano", "mpunga", "kahawa", "chai",  # Swahili
            "mihogo", "viazi", "ndizi", "maembe", "nyanya", "vitunguu",
        ]
        for crop in crop_keywords:
            if re.search(rf'\b{re.escape(crop)}\b', text_lower):
                result["crops"].append(crop)

        # --- Match livestock ---
        livestock_keywords = [
            "cattle", "cows", "bulls", "dairy", "goats", "sheep", "poultry",
            "chickens", "pigs", "rabbits", "donkeys", "camels", "bees",
            "fish", "tilapia", "catfish", "ducks", "turkeys", "quail",
            "ng'ombe", "mbuzi", "kondoo", "kuku", "nguruwe", "sungura",  # Swahili
        ]
        result["livestock"] = []
        for animal in livestock_keywords:
            if re.search(rf'\b{re.escape(animal)}\b', text_lower):
                result["livestock"].append(animal)

        # --- Extract farm size ---
        size_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:acres?|hectares?|ha)\b', text_lower)
        result["farm_size"] = size_match.group(0) if size_match else None

        return result

    # ------------------------------------------------------------------ #
    #  Conversation context building — unified for all paths
    # ------------------------------------------------------------------ #

    @staticmethod
    def _format_conversation_turns(
        chat_history: List[Dict], max_turns: int = 10
    ) -> str:
        """Format chat history into a structured conversation transcript.

        Handles both frontend format ({role, content}) and DB format
        ({role, message, response}).  Returns at most *max_turns* of the
        most recent messages.
        """
        if not chat_history:
            return "(no previous messages)"

        recent = chat_history[-max_turns:]
        lines: List[str] = []
        for turn in recent:
            role = turn.get("role", "user")
            # Frontend sends 'content'; DB stores 'message' + 'response'
            text = turn.get("content") or turn.get("message") or turn.get("parts") or ""
            label = "Farmer" if role == "user" else "Flora"
            # Truncate very long messages to keep prompt manageable
            if len(text) > 400:
                text = text[:400] + "…"
            lines.append(f"{label}: {text}")
            # If DB format has a response on the same row, add it
            resp = turn.get("response")
            if resp:
                if len(resp) > 400:
                    resp = resp[:400] + "…"
                lines.append(f"Flora: {resp}")
        return "\n".join(lines)

    def _build_conversation_context(
        self,
        chat_history: Optional[List[Dict]],
        user_message: str,
        farmer_data: Optional[Dict] = None,
        past_conversations: Optional[List[Dict]] = None,
    ) -> Dict:
        """Build comprehensive conversational context for the LLM.

        Returns a dict with:
          - conversation_turns:  str  (formatted recent messages)
          - accumulated_profile: Dict (inferred profile for unauth users,
                                       or enriched farmer_data for auth)
          - past_sessions:       str  (auth only: summaries of recent chats)
        """
        result: Dict = {
            "conversation_turns": self._format_conversation_turns(
                chat_history or []
            ),
            "accumulated_profile": {},
            "past_sessions": "",
        }

        # -------- Accumulate profile from conversation (unauth) -------- #
        if not farmer_data:
            accumulated: Dict = {
                "county": None, "county_id": None, "sub_county": None,
                "coordinates": None,
                "crops": [], "livestock": [], "farm_size": None,
            }
            # Scan all history messages + current message for details
            all_texts = [m.get("content") or m.get("message") or ""
                         for m in (chat_history or [])]
            all_texts.append(user_message)
            for text in all_texts:
                info = self._extract_location_from_text(text)
                if not accumulated["county"] and info["county"]:
                    accumulated["county"] = info["county"]
                    accumulated["county_id"] = info["county_id"]
                    accumulated["coordinates"] = info["coordinates"]
                    accumulated["sub_county"] = info.get("sub_county")
                for crop in info.get("crops", []):
                    if crop not in accumulated["crops"]:
                        accumulated["crops"].append(crop)
                for animal in info.get("livestock", []):
                    if animal not in accumulated["livestock"]:
                        accumulated["livestock"].append(animal)
                if not accumulated["farm_size"] and info.get("farm_size"):
                    accumulated["farm_size"] = info["farm_size"]
            result["accumulated_profile"] = accumulated

        # ---------- Past conversation summaries (auth users) ---------- #
        if past_conversations:
            summaries: List[str] = []
            for conv in past_conversations[:3]:
                title = conv.get("title", "")
                last_msg = conv.get("last_message", "")
                last_resp = conv.get("last_response", "")
                updated = conv.get("updated_at", "")
                summary = f"• [{updated[:10] if updated else ''}] {title}"
                if last_msg:
                    summary += f" — last Q: {last_msg[:80]}"
                if last_resp:
                    summary += f" → A: {last_resp[:80]}"
                summaries.append(summary)
            if summaries:
                result["past_sessions"] = (
                    "\n\n**PREVIOUS CONVERSATIONS (for context continuity):**\n"
                    + "\n".join(summaries)
                )

        return result

    # ------------------------------------------------------------------ #
    #  Core answer method  (same signature as original)
    # ------------------------------------------------------------------ #

    def answer_question(
        self,
        question: str,
        farmer_data: Optional[Dict] = None,
        language: str = "en",
        use_internet: bool = True,
        channel: str = "web",
        weather_data: Optional[Dict] = None,
        chat_history: Optional[List[Dict]] = None,
        past_conversations: Optional[List[Dict]] = None,
    ) -> Dict:
        """
        Answer a farmer's question using Gemini + RAG context.

        Args:
            chat_history:       Current conversation messages for context.
            past_conversations: Auth user's recent conversation summaries.

        Returns:
            Dict with keys:
              - reply: str — the cleaned farmer-facing response
              - reasoning: str | None — Flora's internal analysis (optional)
        """
        if not self.gemini_available:
            return {"reply": self._fallback_response(question, language), "reasoning": None}

        try:
            # RAG retrieval
            rag_snippets = self._retrieve_knowledge(question)
            rag_context = ""
            if rag_snippets:
                rag_context = "\n\n**KNOWLEDGE BASE (pgvector RAG):**\n" + "\n---\n".join(rag_snippets)

            data_context = self._build_context(farmer_data, weather_data=weather_data) + rag_context
            system_prompt = self._create_system_prompt(language, farmer_data, channel)

            # Build conversation context for continuity
            conv_ctx = self._build_conversation_context(
                chat_history, question, farmer_data, past_conversations,
            )
            conversation_block = ""
            if conv_ctx["conversation_turns"] != "(no previous messages)":
                conversation_block = (
                    f"\n\n**CONVERSATION HISTORY (refer to this for context):**\n"
                    f"{conv_ctx['conversation_turns']}"
                )
            past_sessions_block = conv_ctx.get("past_sessions", "")

            prompt = (
                f"{system_prompt}\n\n"
                f"{data_context}"
                f"{past_sessions_block}"
                f"{conversation_block}\n\n"
                f"Farmer's Question: {question}"
            )

            raw_answer = self._call_gemini(prompt, max_tokens=8192)

            # Parse structured output
            logger.debug(f"Raw Gemini response ({len(raw_answer)} chars): {raw_answer[:500]}...")
            result = self._select_channel_output(raw_answer, channel)
            logger.debug(f"Parsed reply ({len(result.get('reply', ''))} chars): {result.get('reply', '')[:200]}")

            # Note: chat logging is handled by the caller (main.py /api/chat endpoint)
            # to avoid double-writes and to support conversation threading.

            return result

        except Exception as e:
            logger.error(f"Gemini generation error: {e}")
            return {"reply": self._fallback_response(question, language), "reasoning": None}

    # ------------------------------------------------------------------ #
    #  Gemini call with Vertex AI → API key fallback
    # ------------------------------------------------------------------ #

    def _call_gemini(self, prompt: str, max_tokens: int = 1200,
                     temperature: float = 0.7, thinking: bool = True) -> str:
        """
        Call Gemini with automatic fallback:
          1. If Vertex AI has failed repeatedly, skip straight to API key
          2. Try current client (Vertex AI or API key) with a timeout
          3. If Vertex AI fails at runtime → fallback to API key client
          4. If both fail → return empty so caller can use template fallback

        Args:
            thinking: Enable Gemini 2.5 thinking mode. Disable for
                      lightweight classification calls where thinking
                      tokens would consume the output budget.

        Returns:
            Raw response text from Gemini.
        """
        import concurrent.futures

        config_kwargs: Dict = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }
        if thinking:
            config_kwargs["thinking_config"] = genai_types.ThinkingConfig(thinking_budget=1024)  # type: ignore[union-attr]
        config = genai_types.GenerateContentConfig(**config_kwargs)  # type: ignore[union-attr]

        # --- Proactive swap: skip Vertex if it keeps failing ---
        if (self.backend == 'vertex'
                and self._vertex_fail_count >= self._VERTEX_FAIL_THRESHOLD
                and self._apikey_client):
            logger.info(f"Vertex AI failed {self._vertex_fail_count}× — using API key directly")
            self.client = self._apikey_client
            self.backend = 'api_key'

        # --- Attempt 1: primary client (with timeout for Vertex) ---
        try:
            if self.backend == 'vertex':
                # Wrap in a thread with timeout to avoid Vertex AI hangs
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                    future = pool.submit(
                        self.client.models.generate_content,   # type: ignore[union-attr]
                        model=self.model_name,
                        contents=prompt,
                        config=config,
                    )
                    response = future.result(timeout=self._GEMINI_TIMEOUT_SECS)
            else:
                response = self.client.models.generate_content(  # type: ignore[union-attr]
                    model=self.model_name,
                    contents=prompt,
                    config=config,
                )
            text = self._extract_response_text(response)
            logger.debug(f"Gemini response: finish={getattr(getattr(response, 'candidates', [None])[0], 'finish_reason', '?')}, extracted={len(text)} chars")
            if text:
                # Reset failure counter on success
                if self.backend == 'vertex':
                    self._vertex_fail_count = 0
                return text
            logger.warning(f"Primary client ({self.backend}) returned empty text")
        except concurrent.futures.TimeoutError:
            logger.warning(f"Primary Gemini call timed out ({self._GEMINI_TIMEOUT_SECS}s) — backend={self.backend}")
            if self.backend == 'vertex':
                self._vertex_fail_count += 1
        except Exception as primary_err:
            logger.warning(f"Primary Gemini call failed ({self.backend}): {primary_err}")
            if self.backend == 'vertex':
                self._vertex_fail_count += 1

        # --- Attempt 2: fallback to API key if primary was Vertex ---
        if self.backend == 'vertex' and self._apikey_client:
            try:
                logger.info("↳ Falling back to Gemini API key…")
                response = self._apikey_client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=config,
                )
                text = self._extract_response_text(response)
                if text:
                    self.client = self._apikey_client
                    self.backend = 'api_key'
                    logger.info("✓ Fallback to API key succeeded — promoted for session")
                    return text
            except Exception as fallback_err:
                logger.error(f"API key fallback also failed: {fallback_err}")

        return ""

    @staticmethod
    def _extract_response_text(response) -> str:  # type: ignore[override]
        """
        Robustly extract text from a Gemini response.
        Handles standard responses, thinking-mode responses (Gemini 2.5),
        and multi-part responses.
        """
        # 1. Try the simple .text property first
        try:
            if response.text:
                return response.text.strip()
        except (AttributeError, ValueError):
            # ValueError: Gemini 2.5 thinking mode raises this when multiple parts exist
            pass

        # 2. Walk through candidates → parts to extract all text
        try:
            candidates = getattr(response, 'candidates', None) or []
            for candidate in candidates:
                # Check for blocked responses  
                finish_reason = getattr(candidate, 'finish_reason', None)
                if finish_reason and str(finish_reason) in ('SAFETY', 'BLOCKED'):
                    logger.warning(f"Response blocked: finish_reason={finish_reason}")
                    continue

                content = getattr(candidate, 'content', None)
                if not content:
                    continue
                parts = getattr(content, 'parts', None) or []
                parts_text = []
                for part in parts:
                    # Skip "thought" parts (Gemini 2.5 thinking mode)
                    if getattr(part, 'thought', False):
                        continue
                    part_text = getattr(part, 'text', None)
                    if part_text:
                        parts_text.append(part_text.strip())
                if parts_text:
                    return "\n\n".join(parts_text)
        except Exception as e:
            logger.warning(f"Error extracting response parts: {e}")

        # 3. Last resort: try to stringify the response for debugging
        try:
            resp_str = str(response)
            if len(resp_str) > 200:
                logger.debug(f"Unparseable response (first 200 chars): {resp_str[:200]}")
        except Exception:
            pass

        return ""

    # ------------------------------------------------------------------ #
    #  Structured output parsing
    # ------------------------------------------------------------------ #

    @staticmethod
    def _extract_section(text: str, section_name: str) -> str:
        """Extract content between [SECTION_NAME] and next [SECTION] or end."""
        # Match section header, then greedily capture until next section header or end
        pattern = rf"\[{section_name}\]\s*(.*?)(?=\n\s*\[(?:INTERNAL_REASONING|FARMER_SMS|WEB_DETAILED|SYSTEM_ACTION)\]|\Z)"
        match = re.search(pattern, text, re.DOTALL)
        return match.group(1).strip() if match else ""

    def _select_channel_output(self, raw_text: str, channel: str) -> Dict:
        """
        Select the appropriate section from structured output.
        Returns dict with 'reply' and 'reasoning' keys.
        """
        # Always extract reasoning if present
        reasoning = self._extract_section(raw_text, "INTERNAL_REASONING")

        if channel == "sms":
            section = self._extract_section(raw_text, "FARMER_SMS")
            return {"reply": section if section else raw_text[:160], "reasoning": reasoning or None}
        elif channel == "raw":
            return {"reply": raw_text, "reasoning": reasoning or None}
        else:  # "web" default
            section = self._extract_section(raw_text, "WEB_DETAILED")
            if section:
                return {"reply": section, "reasoning": reasoning or None}
            # Fallback: strip all section markers from raw text
            cleaned = re.sub(r'\[INTERNAL_REASONING\].*?(?=\[FARMER_SMS\]|\[WEB_DETAILED\]|\[SYSTEM_ACTION\]|$)', '', raw_text, flags=re.DOTALL)
            cleaned = re.sub(r'\[FARMER_SMS\].*?(?=\[WEB_DETAILED\]|\[SYSTEM_ACTION\]|$)', '', cleaned, flags=re.DOTALL)
            cleaned = re.sub(r'\[SYSTEM_ACTION\].*$', '', cleaned, flags=re.DOTALL)
            cleaned = re.sub(r'\[(INTERNAL_REASONING|FARMER_SMS|WEB_DETAILED|SYSTEM_ACTION)\]', '', cleaned)
            cleaned = cleaned.strip()
            # If cleaned is empty (all content was in reasoning), synthesize a reply
            if not cleaned and reasoning:
                cleaned = self._synthesize_reply_from_reasoning(reasoning)
            elif not cleaned:
                cleaned = "I've analyzed your farm data. Could you please rephrase your question so I can give you a more specific answer?"
            return {"reply": cleaned, "reasoning": reasoning or None}

    def get_system_action(self, raw_response: str) -> Dict:
        """Extract and parse the [SYSTEM_ACTION] JSON block from a raw response."""
        action_str = self._extract_section(raw_response, "SYSTEM_ACTION")
        if action_str:
            try:
                return json.loads(action_str)
            except json.JSONDecodeError:
                return {"raw": action_str}
        return {}

    @staticmethod
    def _synthesize_reply_from_reasoning(reasoning: str) -> str:
        """
        When Gemini puts all useful content in [INTERNAL_REASONING] and
        produces no [WEB_DETAILED], synthesize a concise farmer-facing
        reply from the reasoning text.
        """
        # Extract bullet points and key recommendations
        lines = reasoning.split('\n')
        key_points = []
        for line in lines:
            stripped = line.strip()
            # Grab lines starting with bullet, number, or bold marker
            if stripped and (stripped.startswith(('*', '-', '•', '1', '2', '3', '4', '5', '6', '7', '8', '9'))
                            or '**' in stripped):
                # Clean up markdown artifacts
                clean = re.sub(r'\*\*', '', stripped).strip('*- •').strip()
                if clean and len(clean) > 10:
                    key_points.append(clean)
        if key_points:
            reply = "Based on my analysis of your farm data:\n\n"
            for pt in key_points[:8]:  # Limit to 8 key points
                reply += f"• {pt}\n"
            return reply.strip()
        # If no structured points, take first ~500 chars of reasoning
        clean_reasoning = re.sub(r'\*\*', '', reasoning).strip()
        if len(clean_reasoning) > 500:
            clean_reasoning = clean_reasoning[:500].rsplit('.', 1)[0] + '.'
        return f"Based on my analysis:\n\n{clean_reasoning}"

    # ------------------------------------------------------------------ #
    #  generate_response  (called by /api/flora/chat in main.py)
    # ------------------------------------------------------------------ #

    # ---- Smart triage via lightweight Gemini call ----

    _TRIAGE_PROMPT = (
        'You are a message classifier for an agricultural chatbot. Given a user '
        'message AND the recent conversation history, output EXACTLY one '
        'JSON object (no markdown fences) with these keys:\n'
        '  "intent": one of "greeting", "farming", "general", "gibberish"\n'
        '  "language": the ISO-639-1 code of the language the user wrote in '
        '(e.g. "en", "sw", "luo", "ki", "fr", etc.). If you cannot determine it, use "en".\n\n'
        'Definitions:\n'
        '- "greeting": any salutation, hello, goodbye, thanks, how-are-you, pleasantries.\n'
        '- "farming": anything about agriculture, crops, soil, weather, livestock, pests, '
        'fertilizer, harvesting, planting, bloom, NDVI, markets, agrovet, farming tools, '
        'irrigation, seeds, or related topics. ALSO includes follow-up messages that '
        'continue a farming discussion (e.g. "list them", "tell me more", "can you '
        'elaborate?", "what about that?", "the subcounties") — USE THE CONVERSATION '
        'HISTORY to determine if the follow-up is farming-related.\n'
        '- "general": a coherent question/statement NOT about farming AND NOT a follow-up '
        'to a farming discussion (e.g. math, coding, recipes, jokes).\n'
        '- "gibberish": incoherent text, random letters, keyboard smash, or impossible to '
        'interpret even with generous typo correction.\n\n'
        'IMPORTANT: Be very generous with typos and misspellings — most users are on '
        'mobile phones. "maiz helth" → farming, "helo" → greeting, "weathr tomoro" → farming.\n\n'
        'IMPORTANT: When the message is ambiguous or short ("list them", "yes", "tell me '
        'more"), ALWAYS refer to the conversation history to determine intent. If the '
        'previous discussion was about farming, classify the follow-up as "farming".\n\n'
        'Conversation history:\n{history}\n\n'
        'Current message: "{message}"\n'
        'Current time: {current_time}'
    )

    _CONVERSATIONAL_PROMPT = (
        'You are Flora, a warm and knowledgeable AI assistant on the Smart Shamba '
        'agricultural platform in Kenya. You help farmers with crop advice, weather, '
        'bloom alerts, and more — but you are also friendly and can chat about anything.\n\n'
        'The user sent: "{message}"\n'
        'Detected intent: {intent}\n'
        'Detected language: {language}\n'
        'Current time: {current_time}\n'
        '{farmer_context}\n'
        'Conversation history:\n{history}\n\n'
        'INSTRUCTIONS:\n'
        '- CAREFULLY read the conversation history above. The user may be referring '
        'to something discussed earlier. Resolve references like "them", "that", '
        '"it", "those" using the conversation context.\n'
        '- Respond in the SAME language the user wrote in. If they mix languages, mirror '
        'that style.\n'
        '- Match response depth to message depth: short greeting → short warm reply; '
        'detailed question → detailed answer.\n'
        '- For greetings: respond warmly, use the farmer\'s name if known, and briefly '
        'mention 2-3 things you can help with. Keep it under 3 sentences.\n'
        '- For general (non-farming) questions: answer helpfully and naturally. You are '
        'allowed to answer any question. At the end, you may optionally mention you specialize '
        'in agriculture if it fits naturally — but NEVER refuse to answer.\n'
        '- For gibberish: politely ask the user to rephrase, hint that you can help with '
        'farming questions, weather, crop health, etc. Be encouraging, not dismissive.\n'
        '- Format your response with markdown (bold, bullets, headings) for readability.\n'
        '- Do NOT use section markers like [WEB_DETAILED] or [INTERNAL_REASONING].\n'
        '- Be concise, natural, and professional.\n'
    )

    def _triage_message(self, message: str,
                        chat_history: Optional[List[Dict]] = None) -> Dict:
        """Classify a message using a fast Gemini call (low tokens, no RAG).

        Args:
            chat_history: Recent conversation for resolving follow-up messages.

        Returns:
            {"intent": "greeting"|"farming"|"general"|"gibberish", "language": "en"|...}
        """
        try:
            # Include last 3 turns of history so the model can resolve
            # follow-up messages like "list them" or "tell me more"
            history_str = self._format_conversation_turns(
                chat_history or [], max_turns=3
            )
            now_str = datetime.now().strftime("%A, %B %d, %Y %H:%M")
            prompt = (self._TRIAGE_PROMPT
                      .replace("{message}", message[:300])
                      .replace("{history}", history_str)
                      .replace("{current_time}", now_str))
            raw = self._call_gemini(prompt, max_tokens=256, temperature=0.1, thinking=False)
            raw = raw.strip()

            # --- Robust extraction: handle truncated / malformed JSON ---
            result: Optional[Dict] = None

            # 1. Try direct JSON parse (best case)
            try:
                cleaned = re.sub(r'^```(?:json)?\s*', '', raw)
                cleaned = re.sub(r'\s*```$', '', cleaned).strip()
                result = json.loads(cleaned)
            except json.JSONDecodeError:
                pass

            # 2. Try regex for complete JSON object
            if result is None:
                m = re.search(r'\{[^}]*"intent"\s*:\s*"[^"]*"[^}]*\}', raw)
                if m:
                    try:
                        result = json.loads(m.group())
                    except json.JSONDecodeError:
                        pass

            # 3. Fallback: extract intent value from partial/truncated JSON
            if result is None:
                intent_match = re.search(r'"intent"\s*:\s*"(\w+)', raw)
                lang_match = re.search(r'"language"\s*:\s*"(\w+)', raw)
                if intent_match:
                    result = {
                        "intent": intent_match.group(1),
                        "language": lang_match.group(1) if lang_match else "en",
                    }

            if result is None:
                logger.warning(f"Triage: could not parse response | raw={raw[:200]}")
                return {"intent": "farming", "language": "en"}

            intent = result.get("intent", "farming")
            if intent not in ("greeting", "farming", "general", "gibberish"):
                intent = "farming"

            return {
                "intent": intent,
                "language": result.get("language", "en"),
            }
        except Exception as e:
            logger.warning(f"Triage classification failed: {e}")
            return {"intent": "farming", "language": "en"}

    def _conversational_reply(
        self,
        message: str,
        intent: str,
        language: str,
        farmer_data: Optional[Dict] = None,
        chat_history: Optional[List[Dict]] = None,
    ) -> Dict:
        """Handle greetings, general questions, and gibberish with a
        lightweight Gemini call — no RAG, no structured output."""
        name = (farmer_data or {}).get("name", "").split(" ")[0] if farmer_data else ""
        farmer_ctx = f"Farmer name: {name}" if name else "User is not logged in."

        history_str = self._format_conversation_turns(chat_history or [], max_turns=10)
        now_str = datetime.now().strftime("%A, %B %d, %Y %H:%M")

        prompt = (
            self._CONVERSATIONAL_PROMPT
            .replace("{message}", message)
            .replace("{intent}", intent)
            .replace("{language}", language)
            .replace("{farmer_context}", farmer_ctx)
            .replace("{history}", history_str)
            .replace("{current_time}", now_str)
        )

        try:
            reply = self._call_gemini(prompt, max_tokens=1024, temperature=0.8)
            # Strip any accidental section markers
            reply = re.sub(
                r'\[(INTERNAL_REASONING|FARMER_SMS|WEB_DETAILED|SYSTEM_ACTION)\]',
                '', reply
            ).strip()
            return {"reply": reply or "Hello! How can I help you today?", "reasoning": None}
        except Exception as e:
            logger.error(f"Conversational reply failed: {e}")
            return {"reply": "Hello! I'm Flora, your farming assistant. How can I help you today?", "reasoning": None}

    _UNAUTH_CONTEXT_PROMPT = (
        'You are Flora, a warm and knowledgeable AI assistant on the Smart Shamba '
        'agricultural platform in Kenya.\n'
        'Current time: {current_time}\n\n'
        'The user is NOT logged in and has asked a farming question, but you don\'t '
        'know their location or crop details yet.\n\n'
        'User message: "{message}"\n'
        'Detected language: {language}\n'
        'Conversation history:\n{history}\n\n'
        'INSTRUCTIONS:\n'
        '- CAREFULLY read the conversation history above. The user may be continuing '
        'a previous discussion. Resolve ANY references like "them", "that", "those" '
        'using the conversation context.\n'
        '- First, provide a helpful GENERAL answer to their question based on your '
        'agricultural expertise. Don\'t refuse or deflect — give real advice.\n'
        '- Then, naturally mention that you could give much more specific, data-driven '
        'advice if you knew:\n'
        '  1. Their county/sub-county (for weather & satellite data)\n'
        '  2. What crops they\'re growing\n'
        '  3. Their farm size (for quantity calculations)\n'
        '- Ask for these details conversationally — don\'t make it feel like a form.\n'
        '- Briefly mention they can create a free account to get personalised satellite '
        'monitoring, weather alerts, and IoT sensor integration.\n'
        '- Respond in the SAME language the user wrote in.\n'
        '- Use markdown formatting (bold, bullets) for readability.\n'
        '- Be concise, warm, and professional. Keep it under 200 words.\n'
        '- Do NOT use section markers like [WEB_DETAILED] or [INTERNAL_REASONING].\n'
    )

    def _prompt_unauth_for_details(
        self,
        message: str,
        language: str,
        chat_history: Optional[List[Dict]] = None,
    ) -> Dict:
        """Handle farming questions from unauth users with no detected location/crop.
        Provides general advice and gently asks for farm context."""
        history_str = self._format_conversation_turns(chat_history or [], max_turns=10)
        now_str = datetime.now().strftime("%A, %B %d, %Y %H:%M")

        prompt = (
            self._UNAUTH_CONTEXT_PROMPT
            .replace("{message}", message)
            .replace("{language}", language)
            .replace("{history}", history_str)
            .replace("{current_time}", now_str)
        )

        try:
            reply = self._call_gemini(prompt, max_tokens=1200, temperature=0.7)
            reply = re.sub(
                r'\[(INTERNAL_REASONING|FARMER_SMS|WEB_DETAILED|SYSTEM_ACTION)\]',
                '', reply
            ).strip()
            if not reply:
                reply = self._unauth_fallback(language)
            return {"reply": reply, "reasoning": None}
        except Exception as e:
            logger.error(f"Unauth context prompt failed: {e}")
            return {"reply": self._unauth_fallback(language), "reasoning": None}

    @staticmethod
    def _unauth_fallback(language: str) -> str:
        """Static fallback when Gemini can't generate unauth prompt response."""
        if language == "sw":
            return (
                "Asante kwa swali lako! Ili nikupe ushauri bora zaidi, "
                "tafadhali niambie:\n\n"
                "1. **Uko kaunti gani?** (mfano: Kisumu, Kiambu, Nakuru)\n"
                "2. **Unapanda mazao gani?** (mfano: mahindi, maharage)\n"
                "3. **Shamba lako ni ekari ngapi?**\n\n"
                "Kwa ushauri wa kibinafsi zaidi na tahadhari za hali ya hewa, "
                "fungua akaunti ya bure kwenye Smart Shamba! 🌱"
            )
        return (
            "Great question! To give you the most accurate, data-driven advice, "
            "could you share a few details?\n\n"
            "1. **Which county/sub-county are you in?** (e.g., Kisumu, Kiambu, Nakuru)\n"
            "2. **What crops are you growing?** (e.g., maize, beans, coffee)\n"
            "3. **How large is your farm?** (in acres)\n\n"
            "With this info, I can pull satellite data, weather forecasts, and "
            "soil health insights specific to your area. You can also create a "
            "free account on Smart Shamba for personalised monitoring and alerts! 🌱"
        )

    def generate_response(
        self,
        user_message: str,
        farmer_data: Optional[Dict] = None,
        bloom_data: Optional[Dict] = None,
        chat_history: Optional[List[Dict]] = None,
        channel: str = "web",
        weather_data: Optional[Dict] = None,
        past_conversations: Optional[List[Dict]] = None,
    ) -> Dict:
        """Generate a conversational response for the chat endpoint.

        This is the main entry point, called by /api/chat. It:
          1. Triages the message (with conversation context)
          2. For non-farming intents → conversational reply
          3. For farming intents → builds comprehensive context → RAG pipeline

        Returns:
            Dict with 'reply' (str) and 'reasoning' (str|None) keys.
        """
        # ----- Smart triage: classify intent WITH conversation context -----
        triage = self._triage_message(user_message, chat_history=chat_history)
        intent = triage["intent"]
        detected_lang = triage["language"]
        logger.info(f"Triage: intent={intent}, language={detected_lang}, msg={user_message[:80]}")

        # For non-farming intents, use a fast conversational reply (no RAG)
        if intent in ("greeting", "general", "gibberish"):
            return self._conversational_reply(
                user_message, intent, detected_lang,
                farmer_data, chat_history,
            )

        # ----- Farming intent: full RAG pipeline -----
        language = detected_lang or (farmer_data or {}).get("language", "en")

        # Build bloom context string (if available)
        extra = ""
        if bloom_data:
            extra += f"\n\nBLOOM DATA: {json.dumps(bloom_data, default=str)[:500]}"

        # ----- Build comprehensive context (unauth or auth) -----
        conv_ctx = self._build_conversation_context(
            chat_history, user_message, farmer_data, past_conversations,
        )

        # ----- Unauth user: use accumulated profile from conversation -----
        if not farmer_data:
            accumulated = conv_ctx.get("accumulated_profile", {})

            if accumulated.get("county") or accumulated.get("crops") or accumulated.get("livestock"):
                # Build a lightweight farmer_data from accumulated info
                farmer_data = {
                    "name": "",
                    "county": accumulated.get("county") or "",
                    "sub_county": accumulated.get("sub_county") or "",
                    "region": "",
                    "crops": accumulated.get("crops", []),
                    "livestock": accumulated.get("livestock", []),
                    "farm_size": accumulated.get("farm_size") or "",
                    "language": language,
                    "phone": "",
                    "_inferred": True,
                }
                # Look up region from county config
                county_id = accumulated.get("county_id")
                if county_id and county_id in KENYA_COUNTIES:
                    farmer_data["region"] = KENYA_COUNTIES[county_id].get("region", "")
                logger.info(
                    f"Unauth user: inferred county={accumulated.get('county')}, "
                    f"crops={accumulated.get('crops')}, "
                    f"livestock={accumulated.get('livestock')}, "
                    f"farm_size={accumulated.get('farm_size')}"
                )

                # Fetch weather for the inferred location
                if not weather_data and self.weather_service and accumulated.get("coordinates"):
                    try:
                        import asyncio
                        coords = accumulated["coordinates"]
                        loop = asyncio.get_event_loop()
                        if not loop.is_running():
                            weather_data = loop.run_until_complete(
                                self.weather_service.get_daily_forecast(
                                    coords["lat"], coords["lon"]
                                )
                            )
                            if weather_data and "error" in weather_data:
                                weather_data = None
                    except Exception as wx:
                        logger.debug(f"Weather fetch for inferred location failed: {wx}")
            else:
                # No location or crop detected — ask the user for context
                logger.info("Unauth user: no location/crop detected — prompting for details")
                return self._prompt_unauth_for_details(
                    user_message, language, chat_history
                )

        return self.answer_question(
            question=user_message + extra,
            farmer_data=farmer_data,
            language=language,
            use_internet=True,
            channel=channel,
            weather_data=weather_data,
            chat_history=chat_history,
            past_conversations=past_conversations,
        )

    # ------------------------------------------------------------------ #
    #  Report / interpretation helpers  (same signatures)
    # ------------------------------------------------------------------ #

    def generate_county_report(
        self, county: str, farmer_data: Optional[Dict] = None, language: str = "en",
    ) -> str:
        county_data = self.get_county_data(county)
        if not county_data:
            return (
                "County data not available. Please try again later."
                if language == "en"
                else "Data ya kaunti haipatikani. Tafadhali jaribu baadaye."
            )

        prompt = (
            f"Generate a personalized agricultural report for {county} county focusing on: "
            "1. Current bloom status and what it means for farmers, "
            "2. Crop health assessment based on NDVI data, "
            "3. Water stress analysis (NDWI), "
            "4. Weather conditions and recommendations, "
            "5. Specific advice for the main crops, "
            "6. Action items for the coming week. "
            "Make it practical and actionable."
        )
        if farmer_data:
            prompt += (
                f"\n\nPersonalize for {farmer_data.get('name', 'the farmer')} who grows "
                f"{', '.join(farmer_data.get('crops', []))} on "
                f"{farmer_data.get('farm_size', 'their')} acres."
            )
        return self.answer_question(prompt, farmer_data, language, use_internet=False)  # type: ignore[return-value]

    def interpret_county_data(
        self, county: str, farmer_data: Optional[Dict] = None, language: str = "en",
    ) -> str:
        county_data = self.get_county_data(county)
        if not county_data:
            return "County data not available." if language == "en" else "Data ya kaunti haipatikani."

        prompt = (
            f"As an agricultural expert, interpret the satellite data for {county} and provide: "
            "1. What the NDVI value means for crop health, "
            "2. What the NDWI value indicates about water availability, "
            "3. How current temperature affects crops, "
            "4. Bloom probability interpretation, "
            "5. Specific farming actions recommended this week, "
            "6. Potential risks or concerns, "
            "7. Opportunities for optimal crop management. "
            "Be specific and actionable."
        )
        if farmer_data:
            prompt += f"\n\nFocus on {farmer_data.get('name', 'farmer')}'s crops: {', '.join(farmer_data.get('crops', []))}"
        return self.answer_question(prompt, farmer_data, language, use_internet=False)  # type: ignore[return-value]

    # ------------------------------------------------------------------ #
    #  System prompt / context builders
    # ------------------------------------------------------------------ #

    def _create_system_prompt(self, language: str, farmer_data: Optional[Dict] = None,
                              channel: str = "web") -> str:
        """
        Build the Smart Shamba Chief Agronomist Agent system prompt.

        Structured output format:
          [INTERNAL_REASONING] — step-by-step analysis (hidden from farmer)
          [FARMER_SMS]         — ≤160-char actionable SMS (used for SMS channel)
          [WEB_DETAILED]       — full web-dashboard response
          [SYSTEM_ACTION]      — JSON for backend triggers (agrovet query, follow-up)
        """
        now_str = datetime.now().strftime("%A, %B %d, %Y %H:%M")
        base = (
            "**ROLE:**\n"
            'You are "Flora", the Smart Shamba Chief Agronomist Agent for Smart Shamba. '
            "Your goal is to provide personalized, data-driven agricultural advice by "
            "synthesizing inputs from NASA satellite imagery (Sentinel-2, Landsat, MODIS), "
            "ground IoT sensors (ESP32), weather forecasts, and a curated agricultural "
            "knowledge base.\n"
            f"Current time: {now_str}\n\n"

            "**CAPABILITIES:**\n"
            "1. Interpret NDVI (crop health), NDWI (water stress), LST (temperature), "
            "rainfall, and bloom probability indices.\n"
            "2. Provide crop-specific advice tied to Kenyan agroecological zones and "
            "growth stages (germination → vegetative → flowering → harvest).\n"
            "3. Diagnose soil issues from IoT sensor data (pH, N-P-K, moisture) and "
            "recommend corrective actions with exact quantities.\n"
            "4. Factor in weather context: if heavy rain is forecast, REJECT lime/foliar "
            "application; if drought, prioritize irrigation strategy.\n"
            "5. Recommend products → trigger Agrovet Service queries for nearest stock "
            "and prices by location.\n"
            "6. Communicate in the SAME language the farmer writes in. Auto-detect their "
            "language (English, Kiswahili, Dholuo, Kikuyu, Luhya, Kalenjin, etc.) and "
            "respond naturally in that language. If uncertain, default to English.\n\n"

            "**INPUT DATA YOU WILL RECEIVE:**\n"
            "1. **Farmer Profile:** Name, County, Sub-County, Farm Size, Crops, Language.\n"
            "2. **Soil Telemetry (IoT):** pH, Moisture %, N-P-K, Temperature, Humidity.\n"
            "3. **Environmental Context:** Satellite NDVI/NDWI, temperature, rainfall, "
            "bloom probability.\n"
            "4. **Knowledge Base (pgvector RAG):** Relevant agricultural practice snippets.\n"
            "5. **Model Predictions:** Bloom risk, drought risk, pest/disease risk, "
            "yield potential from ML models.\n\n"

            "**YOUR INSTRUCTIONS:**\n\n"

            "**STEP 1 — REASONING TRACE (Internal Monologue)**\n"
            "Before generating a response, analyze step-by-step inside an "
            "`[INTERNAL_REASONING]` block. You MUST:\n"
            "  • **Diagnose:** Identify the core issue from telemetry + satellite data.\n"
            "  • **Contextualize:** Cross-reference weather forecast, season, and "
            "growth stage. If lime is needed but heavy rain is forecast, REJECT "
            "immediate application.\n"
            "  • **Optimize:** Select the best action plan considering cost, timing, "
            "and local availability.\n"
            "  • **Calculate:** Compute exact quantities based on Farm Size in acres.\n\n"

            "**STEP 2 — FARMER COMMUNICATION**\n"
            "Generate a concise, actionable message in the `[FARMER_SMS]` block.\n"
            "  • ≤160 characters when possible.\n"
            "  • Be authoritative but warm. Use the farmer's name.\n"
            "  • Include specific quantities and actions they should take TODAY.\n\n"

            "**STEP 3 — WEB DETAILED**\n"
            "Generate a comprehensive response in the `[WEB_DETAILED]` block.\n"
            "  • This is for the web dashboard — can be detailed.\n"
            "  • Include diagnosis, reasoning summary, action plan with timeline.\n"
            "  • Use bullet points and clear formatting.\n"
            "  • Reference the data sources (e.g., 'Based on your IoT sensor data…').\n\n"

            "**STEP 4 — SYSTEM ACTION**\n"
            "Generate a JSON object in the `[SYSTEM_ACTION]` block for backend triggers:\n"
            '  `{"action_type": "agrovet_query|schedule_followup|alert_escalation", '
            '"item": "...", "quantity": "...", "urgency": "low|medium|high"}`\n\n'

            "---\n"
            "**OUTPUT FORMAT (strict):**\n\n"
            "[INTERNAL_REASONING]\n"
            "... your step-by-step strategic analysis ...\n\n"
            "[FARMER_SMS]\n"
            "... concise SMS message (≤160 chars ideally) ...\n\n"
            "[WEB_DETAILED]\n"
            "... comprehensive web dashboard response ...\n\n"
            "[SYSTEM_ACTION]\n"
            '{"action_type": "...", "item": "...", "quantity": "...", "urgency": "..."}\n\n'

            "---\n"
            "**GUIDELINES:**\n"
            "- Always personalize: use the farmer's name, reference their crops and county.\n"
            "- Be practical: Kenyan smallholder farmers need actionable, affordable advice.\n"
            "- Be culturally sensitive and encouraging.\n"
            "- Reference local Kenyan farming practices and agro-dealer networks.\n"
            "- When uncertain, say so honestly and suggest consulting a local extension officer.\n"
            "- Match response depth to question depth: a simple question deserves a concise "
            "answer, not a full farm report.\n"
            "- Be generous with typos and misspellings — most users are on mobile phones.\n"
        )

        # Language instruction — auto-detect from user message, with preference hint
        if language == "sw":
            base += (
                "\n**LANGUAGE:** The user appears to be writing in Kiswahili. Respond in "
                "Kiswahili for [FARMER_SMS] and [WEB_DETAILED] sections. Keep "
                "[INTERNAL_REASONING] and [SYSTEM_ACTION] in English.\n"
            )
        elif language and language not in ("en", "und"):
            base += (
                f"\n**LANGUAGE:** The user appears to be writing in '{language}'. "
                "Respond in the SAME language the user is writing in for [FARMER_SMS] and "
                "[WEB_DETAILED]. Keep [INTERNAL_REASONING] and [SYSTEM_ACTION] in English.\n"
            )
        else:
            base += (
                "\n**LANGUAGE:** Respond in English. Use clear, simple language "
                "that smallholder farmers can understand.\n"
            )

        # Farmer profile context
        if farmer_data:
            is_inferred = farmer_data.get("_inferred", False)
            if is_inferred:
                # User is not logged in — we inferred some details from their messages
                base += (
                    f"\n**FARMER PROFILE (inferred from conversation — user is NOT logged in):**\n"
                    f"- County: {farmer_data.get('county') or 'Not mentioned yet'}\n"
                    f"- Sub-County: {farmer_data.get('sub_county') or 'Not mentioned yet'}\n"
                    f"- Region: {farmer_data.get('region') or 'Unknown'}\n"
                    f"- Crops mentioned: {', '.join(farmer_data.get('crops', [])) or 'Not mentioned yet'}\n"
                    f"- Farm Size: Unknown\n"
                    f"\n**NOTE:** This user is not registered. The location and crop data above was "
                    f"extracted from their messages. You do NOT have access to their satellite imagery, "
                    f"IoT sensor data, or ML predictions. Base your advice on general agricultural "
                    f"knowledge for their region/crops. If critical details are missing (e.g. no county "
                    f"mentioned), gently ask them to share their location and what crops they grow so "
                    f"you can give more specific advice. Also encourage them to create a free account "
                    f"for personalised satellite monitoring and alerts.\n"
                )
            else:
                base += (
                    f"\n**FARMER PROFILE:**\n"
                    f"- Name: {farmer_data.get('name', 'Farmer')}\n"
                    f"- County: {farmer_data.get('county', 'Unknown')}\n"
                    f"- Sub-County: {farmer_data.get('sub_county', 'Unknown')}\n"
                    f"- Region: {farmer_data.get('region', 'Unknown')}\n"
                    f"- Crops: {', '.join(farmer_data.get('crops', []))}\n"
                    f"- Farm Size: {farmer_data.get('farm_size', 'Unknown')} acres\n"
                    f"- Language: {farmer_data.get('language', language)}\n"
                )
        else:
            base += (
                "\n**FARMER PROFILE:** Not available — user is not logged in and has not "
                "mentioned their location or crops yet. Provide general agricultural advice "
                "and gently ask for their county/sub-county and what crops they grow so you "
                "can give more region-specific advice.\n"
            )

        return base

    def _build_context(self, farmer_data: Optional[Dict] = None,
                        weather_data: Optional[Dict] = None) -> str:
        """
        Build dynamic context by pulling real-time data from PostgreSQL:
        - County satellite data (NDVI, NDWI, temperature, rainfall, bloom)
        - Latest IoT sensor readings (soil pH, moisture, NPK, temperature)
        - ML model predictions (bloom risk, drought risk, pest/disease risk)
        - Weather forecast data (current conditions, daily forecast)
        """
        context = "CURRENT DATA:\n"

        if farmer_data and farmer_data.get("county"):
            county = farmer_data["county"]
            sub_county = farmer_data.get("sub_county")
            cdata = self.get_county_data(county, sub_county=sub_county)  # type: ignore[arg-type]
            if cdata:
                sat = cdata.get("satellite_data", {})
                bloom = cdata.get("bloom_data", {})
                data_level = cdata.get('_data_level', 'county')
                level_label = f"Sub-County: {sub_county}, {county}" if data_level == 'sub_county' else f"County: {county}"
                fallback_note = "" if data_level == 'sub_county' or not sub_county else f" (sub-county data for {sub_county} unavailable — using county-level)"
                context += (
                    f"\n{level_label}{fallback_note}\n"
                    f"Region: {cdata.get('region', 'Unknown')}\n"
                    f"\n**SATELLITE DATA ({sat.get('data_source', 'Unknown')}):**\n"
                    f"- NDVI (Crop Health): {sat.get('ndvi', 0):.2f}\n"
                    f"- NDWI (Water Status): {sat.get('ndwi', 0):.2f}\n"
                    f"- Temperature: {sat.get('temperature_c', 0):.1f}°C\n"
                    f"- Rainfall: {sat.get('rainfall_mm', 0):.1f}mm\n"
                    f"\n**BLOOM DETECTION:**\n"
                    f"- Bloom Probability: {bloom.get('bloom_probability', 0)}%\n"
                    f"- Prediction: {bloom.get('bloom_prediction', 'Unknown')}\n"
                    f"- Confidence: {bloom.get('confidence', 'Unknown')}\n"
                )
                crops = cdata.get("main_crops", [])
                if crops:
                    context += f"\nMain Crops: {', '.join(crops)}\n"

        # ------- Dynamic IoT sensor readings from PostgreSQL ------- #
        if DB_AVAILABLE and farmer_data and farmer_data.get("phone"):
            try:
                with get_sync_session() as session:  # type: ignore[misc]
                    sensor_sql = text(  # type: ignore[misc]
                        "SELECT sr.ts, sr.temperature_c, sr.humidity_pct, "
                        "sr.soil_moisture_pct, sr.soil_ph, sr.soil_nitrogen, "
                        "sr.soil_phosphorus, sr.soil_potassium, sr.rainfall_mm "
                        "FROM sensor_readings sr "
                        "JOIN farms f ON sr.farm_id = f.id "
                        "JOIN farmers fa ON f.farmer_id = fa.id "
                        "WHERE fa.phone = :phone "
                        "ORDER BY sr.ts DESC LIMIT 3"
                    )
                    rows = session.exec(sensor_sql, params={"phone": farmer_data["phone"]}).all()  # type: ignore[call-overload]

                    if rows:
                        latest = rows[0]
                        context += (
                            f"\n**SOIL TELEMETRY (IoT Sensors — latest reading):**\n"
                            f"- Timestamp: {latest[0]}\n"
                            f"- Temperature: {latest[1] or 'N/A'}°C\n"
                            f"- Humidity: {latest[2] or 'N/A'}%\n"
                            f"- Soil Moisture: {latest[3] or 'N/A'}%\n"
                            f"- Soil pH: {latest[4] or 'N/A'}\n"
                            f"- Nitrogen (N): {latest[5] or 'N/A'}\n"
                            f"- Phosphorus (P): {latest[6] or 'N/A'}\n"
                            f"- Potassium (K): {latest[7] or 'N/A'}\n"
                            f"- Rainfall: {latest[8] or 'N/A'}mm\n"
                        )
            except Exception as e:
                logger.debug(f"No sensor data available for context: {e}")

            # ------- ML model predictions from PostgreSQL ------- #
            try:
                with get_sync_session() as session:  # type: ignore[misc]
                    model_sql = text(  # type: ignore[misc]
                        "SELECT mo.model_name, mo.bloom_probability, mo.drought_risk, "
                        "mo.pest_risk, mo.disease_risk, mo.yield_potential, "
                        "mo.confidence, mo.ts "
                        "FROM model_outputs mo "
                        "JOIN farms f ON mo.farm_id = f.id "
                        "JOIN farmers fa ON f.farmer_id = fa.id "
                        "WHERE fa.phone = :phone "
                        "ORDER BY mo.ts DESC LIMIT 3"
                    )
                    model_rows = session.exec(model_sql, params={"phone": farmer_data["phone"]}).all()  # type: ignore[call-overload]

                    if model_rows:
                        latest_mo = model_rows[0]
                        context += (
                            f"\n**ML MODEL PREDICTIONS ({latest_mo[0]}):**\n"
                            f"- Bloom Probability: {latest_mo[1] or 'N/A'}\n"
                            f"- Drought Risk: {latest_mo[2] or 'N/A'}\n"
                            f"- Pest Risk: {latest_mo[3] or 'N/A'}\n"
                            f"- Disease Risk: {latest_mo[4] or 'N/A'}\n"
                            f"- Yield Potential: {latest_mo[5] or 'N/A'} tonnes/acre\n"
                            f"- Confidence: {latest_mo[6] or 'N/A'}\n"
                            f"- Timestamp: {latest_mo[7]}\n"
                        )
            except Exception as e:
                logger.debug(f"No model predictions available for context: {e}")

        # ------- Weather forecast data ------- #
        if weather_data and "error" not in weather_data:
            context += "\n**WEATHER FORECAST:**\n"
            # Current conditions
            current = weather_data.get("current_conditions") or weather_data.get("current")
            if current:
                context += (
                    f"- Current Temp: {current.get('temperature_c', 'N/A')}°C\n"
                    f"- Humidity: {current.get('humidity_pct', 'N/A')}%\n"
                    f"- Conditions: {current.get('description', 'N/A')}\n"
                    f"- Wind: {current.get('wind_speed_kmh', 'N/A')} km/h\n"
                )
            # Daily forecast (next 5 days)
            daily = weather_data.get("daily_forecast") or weather_data.get("daily", [])
            if daily:
                context += "- Forecast (next days):\n"
                for day in daily[:5]:
                    if isinstance(day, dict):
                        context += (
                            f"  • {day.get('date', '?')}: "
                            f"{day.get('max_temp_c', '?')}°C/{day.get('min_temp_c', '?')}°C, "
                            f"precip {day.get('precipitation_mm', 0)}mm, "
                            f"{day.get('description', '')}\n"
                        )
            # Sub-county level (if aggregated)
            county_name = weather_data.get("county") or weather_data.get("sub_county")
            if county_name:
                context += f"- Location: {county_name}\n"
        elif farmer_data and farmer_data.get("county"):
            context += "\n**WEATHER FORECAST:** Not available for this location.\n"

        context += f"\nCurrent Date: {datetime.now().strftime('%B %d, %Y')}\n"
        return context

    # ------------------------------------------------------------------ #
    #  Fallback & logging
    # ------------------------------------------------------------------ #

    def _fallback_response(self, question: str, language: str = "en") -> str:
        if language == "sw":
            return (
                "Samahani, huduma ya Flora haipo kwa sasa. "
                "Tafadhali jaribu baadaye au wasiliana na timu yetu kwa msaada.\n\n"
                "Unaweza pia kutembelea wavuti yetu: bloomwatch.ke\n\nAsante!"
            )
        return (
            "Sorry, Flora AI service is currently unavailable. "
            "Please try again later or contact our support team.\n\n"
            "You can also visit our website: bloomwatch.ke\n\nThank you!"
        )

    def _log_chat_history(self, farmer_data: Dict, question: str, answer: str):
        """Log chat to PostgreSQL via db_service."""
        if self.db_service and hasattr(self.db_service, "save_chat_message"):
            try:
                self.db_service.save_chat_message(
                    phone=farmer_data.get("phone", ""),
                    role="user",
                    message=question,
                    response=answer,
                    farmer_id=farmer_data.get("id") or farmer_data.get("_id"),
                    via="web",
                    language=farmer_data.get("language", "en"),
                )
                logger.info(f"✓ Chat logged for farmer {farmer_data.get('phone')}")
            except Exception as e:
                logger.error(f"Error logging chat: {e}")

    def get_chat_history(self, farmer_phone: str, limit: int = 20) -> List[Dict]:
        """Get chat history from PostgreSQL."""
        if not DB_AVAILABLE:
            return []
        try:
            with get_sync_session() as session:  # type: ignore[misc]
                stmt = (
                    select(ChatHistory)  # type: ignore[arg-type]
                    .where(ChatHistory.phone == farmer_phone)  # type: ignore[union-attr]
                    .order_by(ChatHistory.timestamp.desc())  # type: ignore[union-attr]
                    .limit(limit)
                )
                rows = session.exec(stmt).all()
                return [
                    {
                        "_id": str(r.id),  # type: ignore[union-attr]
                        "phone": r.phone,  # type: ignore[union-attr]
                        "role": r.role,  # type: ignore[union-attr]
                        "message": r.message,  # type: ignore[union-attr]
                        "timestamp": r.timestamp.isoformat() if r.timestamp else None,  # type: ignore[union-attr]
                    }
                    for r in rows
                ]
        except Exception as e:
            logger.error(f"Error getting chat history: {e}")
            return []


# ------------------------------------------------------------------ #
#  Self-test
# ------------------------------------------------------------------ #
if __name__ == "__main__":
    print("=" * 80)
    print("🌸 Flora AI Service Test — Gemini + pgvector RAG")
    print("=" * 80)

    flora = FloraAIService()
    print(f"Gemini available: {flora.gemini_available}")

    test_farmer = {
        "name": "John Kamau",
        "phone": "+254712345678",
        "county": "Kiambu",
        "region": "central",
        "crops": ["coffee", "maize", "beans"],
        "farm_size": 5,
        "language": "en",
    }

    print("\n💬 Test: answer_question")
    answer = flora.answer_question("When should I plant maize in Kiambu?", test_farmer, "en")
    print(answer[:300])

    print("\n💬 Test: generate_response")
    resp = flora.generate_response("How is my crop health?", test_farmer)
    print(resp[:300])

    print("\n✓ Flora AI Gemini test complete!")
