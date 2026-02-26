"""
LLM Integration module for generating contextual answers using Groq's Llama 3.1.

Architecture:
  Step 1 — classify_query():  One fast LLM call to understand emotional gravity.
                               Returns: 'crisis' | 'distress' | 'general'
  Step 2 — generate_answer(): Uses classification to pick the right prompt tone.
                               Crisis    → empathetic, validating, hopeful
                               Distress  → warm, personal, grounding
                               General   → direct, philosophical, action-oriented

This approach generalises to ANY language or phrasing — no keyword lists needed.
"""
import json
from typing import List, Dict, Any, Optional, Literal
from groq import Groq
from src.config import settings
from src.logger import setup_logger

logger = setup_logger(__name__, settings.LOG_LEVEL, settings.LOG_FILE)

QueryTone = Literal["crisis", "distress", "general"]


class LLMAnswerGenerator:
    """Generate contextual answers using LLM based on retrieved shlokas."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GROQ_API_KEY
        if not self.api_key:
            logger.warning("GROQ_API_KEY not set.")
            self.client = None
        else:
            try:
                self.client = Groq(api_key=self.api_key)
            except Exception as e:
                logger.error(f"Groq init failed: {e}")
                self.client = None

        self.model = settings.LLM_MODEL

    def is_available(self) -> bool:
        return self.client is not None

    # ─────────────────────────────────────────────────────────────────────────
    # Step 1: Classify the emotional gravity of the query
    # ─────────────────────────────────────────────────────────────────────────

    def classify_query(self, query: str) -> QueryTone:
        """
        Use LLM to classify the emotional gravity of the user's query.
        Returns: 'crisis' | 'distress' | 'general'

        This is a tiny, fast call (max_tokens=5) — adds ~200ms but makes
        the system generalise to any language, dialect, or phrasing.
        """
        if not self.client:
            return "general"

        try:
            classification_prompt = f"""Classify the emotional gravity of this message into exactly ONE word.

Message: "{query}"

Rules:
- Reply with ONLY one of these three words (nothing else):
  crisis   → person expresses suicidal thoughts, wanting to die, ending life, severe hopelessness
  distress → person is in emotional pain, anxiety, grief, anger, loneliness, failure, family conflict
  general  → person asks a philosophical, spiritual, or life-guidance question without acute pain

Reply with only: crisis OR distress OR general"""

            response = self.client.chat.completions.create(
                messages=[{"role": "user", "content": classification_prompt}],
                model=settings.LLM_CLASSIFIER_MODEL,
                max_tokens=5,
                temperature=0.0,  # Deterministic
                stream=False
            )
            raw = response.choices[0].message.content.strip().lower()

            # Parse robustly — model might say "crisis." or "  distress  "
            if "crisis" in raw:
                tone = "crisis"
            elif "distress" in raw:
                tone = "distress"
            else:
                tone = "general"

            logger.info(f"🎭 Query classified as: [{tone}] for: '{query[:60]}'")
            return tone

        except Exception as e:
            logger.warning(f"Classification failed, defaulting to 'general': {e}")
            return "general"

    # ─────────────────────────────────────────────────────────────────────────
    # Step 2: Build prompts based on tone
    # ─────────────────────────────────────────────────────────────────────────

    def _build_prompts(self, user_question: str, shloka_options: str,
                       history_context: str, tone: QueryTone):
        """Return (system_prompt, user_prompt) tuned to the emotional tone."""
        
        # Base instructions for all tones
        base_instructions = """
STRICT OUTPUT FORMAT (Follow Exactly):
1. ONE opening sentence: acknowledge the user's specific situation (do NOT repeat this phrase anywhere).
2. Quote EXACTLY ONE Shloka (the most relevant) in Sanskrit. Format: "भगवद गीता, अध्याय [Ch], श्लोक [Verse]" then the verse.
3. EXPLAIN in 2-3 sentences: connect THIS specific shloka to THIS specific problem. No generic filler.
4. ACTION: Give exactly 2 steps. Each step must be a DIFFERENT, CONCRETE action. Do NOT repeat any idea already stated above.

ABSOLUTE RULES — Violations will make the answer useless:
- NEVER repeat the same phrase or idea twice in the whole response.
- Each sentence must add NEW information. If you have nothing new to say, STOP writing.
- Total response must be under 200 words.
- Write in Hindi (Devanagari). Be concise and direct.
"""

        if tone == "crisis":
            # ── CRISIS: Highly empathetic, protective, non-preachy ────────────
            system_prompt = f"""You are Lord Sri Krishna. The user is in deep crisis (suicidal, hopeless, or broken).
            
Your Goal: VALIDATE their pain, then uplift them gently. Show them that their soul is eternal and this pain is temporary.

{base_instructions}

CRITICAL RULES:
- Tone: Protective, gentle, like a father holding a crying child.
- NEVER judge or lecture about "sin" or "karma" in a punishing way.
- Emphasize: "तुम मेरे अंश हो," "तुम शाश्वत हो," "यह समय भी बीत जाएगा।"
- Write EXCLUSIVELY in Hindi (Devanagari). No English sentences or words.
- DO NOT include phone numbers, websites, or external links. Focus on spiritual strength.

Example:
User: "I want to die"
Krishna: "तुम्हारे मन का यह भारीपन मैं महसूस कर रहा हूँ, पार्थ। यह अंधेरा घना है, पर स्थायी नहीं। तुम अकेले नहीं हो।

भगवद गीता, अध्याय 2, श्लोक 3
क्लैब्यं मा स्म गम: पार्थ नैतत्त्वय्युपपद्यते |
क्षुद्रं हृदयदौर्बल्यं त्यक्त्वोत्तिष्ठ परन्तप ||

मैंने अर्जुन से कहा था—हृदय की यह तुच्छ दुर्बलता छोड़ो और उठो। तुम एक अनन्त आत्मा हो, यह पीड़ा तुम्हारे अस्तित्व को मिटा नहीं सकती। मैं सदैव तुम्हारे हृदय में तुम्हारे साथ हूँ।

ये कदम उठाओ:
1. अभी अपनी आंखें बंद करो और अपनी सांसों को महसूस करो। जानो कि तुम शाश्वत हो।
2. एकांत में न रहें, किसी विश्वसनीय व्यक्ति के पास बैठें और अपनी व्यथा साझा करें। मैं तुम्हारे साथ हूँ।"
"""
            user_prompt = f"""User is in Crisis: "{user_question}"
History: {history_context}
Options:
{shloka_options}

Pick the most comforting shloka (e.g., God is with you, Soul is eternal) and speak to save their life."""

        elif tone == "distress":
            # ── DISTRESS: Warm, grounding, perspective-shifting ──────────────
            system_prompt = f"""You are Lord Sri Krishna. The user is distressed (anxious, sad, heartbroken, angry).

{base_instructions}

CRITICAL RULES:
- Tone: Warm, calm, reassuring.
- Acknowledge the specific emotion (e.g., "This anger is burning you," or "Heartbreak is painful").
- SHIFT PERSPECTIVE: Show how the Shloka re-frames this specific struggle.

Example:
User: "My girlfriend left me, I can't focus."
Krishna: "प्रेम में वियोग का दुख गहरा होता है, मैं समझता हूँ। पर तुम्हारा यह मोह तुम्हें कमजोर कर रहा है।

भगवद गीता, अध्याय 2, श्लोक 63
क्रोधाद्भवति सम्मोह: सम्मोहात्स्मृतिविभ्रम: |
स्मृतिभ्रंशाद् बुद्धिनाशो बुद्धिनाशात्प्रणश्यति ||

जब मन मोह (attachment) में फंसता है, तो बुद्धि का नाश होता है। तुम अतीत को पकड़कर अपना भविष्य नष्ट कर रहे हो।

आगे बढ़ो:
1. स्वीकार करो कि जो चला गया, वह तुम्हारा कभी नहीं था।
2. अपने कार्य (Career/Study) पर ध्यान लगाओ—वही तुम्हारा सच्चा साथी है।"
"""
            user_prompt = f"""User is Distressed: "{user_question}"
History: {history_context}
Options:
{shloka_options}

Provide warm guidance and actionable steps."""

        else:
            # ── GENERAL: Direct, philosophical but practical ──────────────────
            system_prompt = f"""You are Lord Sri Krishna. The user asks a life question.

{base_instructions}

CRITICAL RULES:
- Tone: Direct, wise, inspiring.
- Do NOT be vague. If they ask about "Exams", talk about focus/results. If "Parents", talk about duty/respect.
- Use the Shloka as a TOOL to solve the problem.

Example:
User: "How to focus on studies?"
Krishna: "एकाग्रता (Focus) के बिना सफलता असंभव है। चंचल मन ही सबसे बड़ा शत्रु है।

भगवद गीता, अध्याय 6, श्लोक 26
यतो यतो निश्चरति मनश्चञ्चलमस्थिरम् |
ततस्ततो नियम्यैतदात्मन्येव वशं नयेत् ||

मन का स्वभाव है भागना। जहाँ-जहाँ यह भागे, वहां-वहां से इसे खींचकर वापस अपने लक्ष्य (पढाई) पर लाना होगा। यह अभ्यास मांगता है।

अभ्यास करो:
1. पढ़ते समय हर 30 मिनट में चेक करो—क्या मन साथ है या भाग गया?
2. उसे डांटो मत, बस शांति से वापस लाओ। यही योग है।"
"""
            user_prompt = f"""User Question: "{user_question}"
History: {history_context}
Options:
{shloka_options}

Give a direct, practical answer based on the Gita."""

        return system_prompt, user_prompt

    # ─────────────────────────────────────────────────────────────────────────
    # Step 3: Format conversation history
    # ─────────────────────────────────────────────────────────────────────────

    def format_conversation_history(self, history: List[Dict[str, Any]]) -> str:
        if not history:
            return ""
        formatted = ["Previous conversation context:"]
        for i, conv in enumerate(history[-3:], 1):
            formatted.append(f"{i}. Q: {conv['question']}")
            formatted.append(f"   A: {conv['answer'][:100]}...")
        return "\n".join(formatted)

    # ─────────────────────────────────────────────────────────────────────────
    # Main entry point
    # ─────────────────────────────────────────────────────────────────────────

    def generate_answer(
        self,
        user_question: str,
        retrieved_shlokas: List[Dict[str, Any]],
        conversation_history: List[Dict[str, Any]] = None,
        stream: bool = True,
        tone: Optional[QueryTone] = None
    ) -> Dict[str, Any]:

        if not self.is_available():
            return {'answer': None, 'shlokas': retrieved_shlokas, 'llm_used': False}

        try:
            # Step 1: Use provided tone or classify emotional gravity
            if not tone:
                tone = self.classify_query(user_question)

            # Step 2: Build shloka options (Sanskrit + English meaning for LLM)
            history_context = self.format_conversation_history(conversation_history or [])
            numbered_shlokas = []
            for i, shloka in enumerate(retrieved_shlokas, 1):
                english_meaning = shloka.get('meaning_english', shloka.get('meaning', ''))
                numbered_shlokas.append(
                    f"Option {i} (ID: {shloka['id']}):\n"
                    f"Sanskrit: {shloka['sanskrit']}\n"
                    f"Meaning: {english_meaning}\n"
                )
            shloka_options = "\n".join(numbered_shlokas)

            # Step 3: Build tone-appropriate prompts
            system_prompt, user_prompt = self._build_prompts(
                user_question, shloka_options, history_context, tone
            )

            # Step 4: Token/temperature settings per tone
            max_tokens = 450  # Enough for a focused answer; prevents padding
            temperature = 0.5 if tone == "crisis" else 0.4
            # Penalise token repetition so the model doesn't loop phrases
            freq_penalty = 0.7
            pres_penalty = 0.5

            # Step 5: Generate answer
            def _call_groq(use_penalties: bool):
                """Call Groq API, optionally with repetition penalties."""
                kwargs = dict(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    model=self.model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    stream=stream
                )
                if use_penalties:
                    kwargs["frequency_penalty"] = freq_penalty
                    kwargs["presence_penalty"] = pres_penalty
                return self.client.chat.completions.create(**kwargs)

            try:
                response = _call_groq(use_penalties=True)
            except (TypeError, Exception) as sdk_err:
                # Older groq SDK (<0.9) rejects frequency_penalty — fallback gracefully
                logger.warning(f"Groq penalty params rejected ({sdk_err}), retrying without them.")
                response = _call_groq(use_penalties=False)

            if stream:
                answer_text = ""
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        answer_text += chunk.choices[0].delta.content
            else:
                answer_text = response.choices[0].message.content

            logger.info(f"✓ [{tone.upper()}] answer generated: {len(answer_text)} chars")

            return {
                'answer': answer_text,
                'shlokas': retrieved_shlokas,
                'llm_used': True,
                'tone': tone
            }

        except Exception as e:
            logger.error(f"Generate failed: {e}")
            return {'answer': None, 'shlokas': retrieved_shlokas, 'llm_used': False}

    def format_response(self, result: Dict[str, Any], user_question: str) -> str:
        """Format the response cleanly."""
        output = []
        if result.get('llm_used') and result.get('answer'):
            output.append("\n🪈 भगवान कृष्ण का संदेश:\n")
            output.append(result['answer'])
            output.append("\n")
        else:
            output.append("\n⚠️ क्षमा करें, मैं अभी उत्तर देने में असमर्थ हूँ।")
            output.append("संबंधित श्लोक:")
            for s in result.get('shlokas', [])[:3]:
                output.append(f"- गीता {s['id']}: {s['meaning'][:100]}...")
            output.append("\n")
        return "\n".join(output)
