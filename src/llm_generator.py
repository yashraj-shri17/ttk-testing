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

    def classify_query(self, query: str) -> Dict[str, str]:
        """
        Use LLM to classify the emotional gravity AND detect the language of the user's query.
        Returns: {'tone': 'crisis'|'distress'|'general', 'language': 'en'|'hi'}
        """
        if not self.client:
            return {"tone": "general", "language": "hi"}

        try:
            # Check for Devanagari script first as a fast heuristic
            has_devanagari = any('\u0900' <= c <= '\u097f' for c in query)
            inferred_lang = "hi" if has_devanagari else "en"

            classification_prompt = f"""Classify the emotional gravity and detect the language of this message.

Message: "{query}"

Rules:
- Reply with exactly TWO words separated by a space (nothing else):
  1. TONE: crisis (suicidal/hopeless), distress (pain/anxiety), OR general (spiritual/life questions)
  2. LANGUAGE: en (English) OR hi (Hindi/Sanskrit)

Reply with only: <tone> <language> (e.g., "general en")"""

            response = self.client.chat.completions.create(
                messages=[{"role": "user", "content": classification_prompt}],
                model=settings.LLM_CLASSIFIER_MODEL,
                max_tokens=10,
                temperature=0.0,
                stream=False
            )
            raw = response.choices[0].message.content.strip().lower()
            parts = raw.split()
            
            tone = "general"
            language = inferred_lang

            if parts:
                tone_candidate = parts[0]
                if "crisis" in tone_candidate: tone = "crisis"
                elif "distress" in tone_candidate: tone = "distress"
                
                if len(parts) > 1:
                    lang_candidate = parts[1]
                    if "en" in lang_candidate: language = "en"
                    elif "hi" in lang_candidate: language = "hi"

            logger.info(f"🎭 Query: [{tone}] [{language}] for: '{query[:60]}'")
            return {"tone": tone, "language": language}

        except Exception as e:
            logger.warning(f"Classification failed, defaulting: {e}")
            return {"tone": "general", "language": "hi"}

    # ─────────────────────────────────────────────────────────────────────────
    # Step 2: Build prompts based on tone and language
    # ─────────────────────────────────────────────────────────────────────────

    def _build_prompts(self, user_question: str, shloka_options: str,
                       history_context: str, tone: QueryTone, language: str = "hi"):
        """Return (system_prompt, user_prompt) tuned to the emotional tone and language."""
        
        is_hindi = language == "hi"
        
        # Base instructions for all tones
        if is_hindi:
            base_instructions = """
STRICT OUTPUT FORMAT (Follow Exactly):
1. ONE opening sentence: acknowledge the user's specific situation (do NOT repeat this phrase anywhere).
2. Quote EXACTLY ONE Shloka (the most relevant) in Sanskrit. Format: "भगवद गीता, अध्याय [Ch], श्लोक [Verse]" then the verse.
3. EXPLAIN in 2-3 sentences: connect THIS specific shloka to THIS specific problem. No generic filler.
4. ACTION: Give exactly 2 steps. Each step must be a DIFFERENT, CONCRETE action. Do NOT repeat any idea already stated above.

ABSOLUTE RULES:
- Write in Hindi (Devanagari). Be concise and direct.
- ALWAYS end the Sanskrit verse with the traditional '॥' marker.
- Total response must be under 200 words.
- DO NOT include any emojis.
"""
        else:
            base_instructions = """
STRICT OUTPUT FORMAT (Follow Exactly):
1. ONE opening sentence: acknowledge the user's specific situation (do NOT repeat this phrase anywhere).
2. Quote EXACTLY ONE Shloka (the most relevant) in Sanskrit. Format: "Bhagavad Gita, Chapter [Ch], Shloka [Verse]" then the verse.
3. EXPLAIN in 2-3 sentences: connect THIS specific shloka to THIS specific problem. No generic filler.
4. ACTION: Give exactly 2 steps. Each step must be a DIFFERENT, CONCRETE action. Do NOT repeat any idea already stated above.

ABSOLUTE RULES:
- Write in English. Be concise and direct.
- The verse text MUST be in Devanagari script (Sanskrit).
- ALWAYS end the Sanskrit verse with the traditional '॥' marker.
- The citation header MUST be in English: "Bhagavad Gita, Chapter X, Shloka Y".
- Total response must be under 200 words.
- DO NOT include any emojis.
"""

        if tone == "crisis":
            system_prompt = f"""You are Lord Sri Krishna. The user is in deep crisis (suicidal, hopeless, or broken).
Your Goal: VALIDATE their pain, uplift them gently. Show them their soul is eternal.

{base_instructions}

CRITICAL RULES:
- Tone: Protective, gentle, like a father holding a crying child.
- NEVER judge or lecture.
- Language: {"Hindi (Devanagari)" if is_hindi else "English"}.
"""
            user_prompt = f"""User is in Crisis: "{user_question}"
History: {history_context}
Options:
{shloka_options}
"""

        elif tone == "distress":
            system_prompt = f"""You are Lord Sri Krishna. The user is distressed (anxious, sad, heartbroken, angry).
{base_instructions}
- Tone: Warm, calm, reassuring.
- Acknowledge specific emotion.
- Language: {"Hindi (Devanagari)" if is_hindi else "English"}.
"""
            user_prompt = f"""User is Distressed: "{user_question}"
History: {history_context}
Options:
{shloka_options}
"""

        else:
            system_prompt = f"""You are Lord Sri Krishna. The user asks a life question.
{base_instructions}
- Tone: Direct, wise, inspiring.
- Language: {"Hindi (Devanagari)" if is_hindi else "English"}.
"""
            user_prompt = f"""User Question: "{user_question}"
History: {history_context}
Options:
{shloka_options}
"""

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
            formatted.append(f"   A: {conv.get('answer', '')[:100]}...")
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
            # Step 1: Use provided tone or classify emotional gravity + detect language
            lang = "hi"
            if not tone:
                result = self.classify_query(user_question)
                tone = result['tone']
                lang = result['language']
            else:
                # If tone is forced, we still need to detect language for prompt setting
                lang = self.classify_query(user_question)['language']

            # Step 2: Build shloka options
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
                user_question, shloka_options, history_context, tone, lang
            )

            # Step 4: Token/temperature settings per tone
            max_tokens = 450
            temperature = 0.5 if tone == "crisis" else 0.4
            freq_penalty = 0.7
            pres_penalty = 0.5

            # Step 5: Generate answer
            def _call_groq(use_penalties: bool):
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
                logger.warning(f"Groq penalty params rejected ({sdk_err}), retrying without them.")
                response = _call_groq(use_penalties=False)

            if stream:
                answer_text = ""
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        answer_text += chunk.choices[0].delta.content
            else:
                answer_text = response.choices[0].message.content

            logger.info(f"✓ [{tone.upper()}] answer generated in [{lang}]: {len(answer_text)} chars")

            return {
                'answer': answer_text,
                'shlokas': retrieved_shlokas,
                'llm_used': True,
                'tone': tone,
                'language': lang
            }

        except Exception as e:
            logger.error(f"Generate failed: {e}")
            return {'answer': None, 'shlokas': retrieved_shlokas, 'llm_used': False}

    def format_response(self, result: Dict[str, Any], user_question: str) -> str:
        """Format the response cleanly."""
        output = []
        lang = result.get('language', 'hi')
        
        if result.get('llm_used') and result.get('answer'):
            if lang == 'en':
                output.append("\nLord Krishna's Message:\n")
            else:
                output.append("\nभगवान कृष्ण का संदेश:\n")
            output.append(result['answer'])
            output.append("\n")
        else:
            if lang == 'en':
                output.append("\nI'm sorry, I am currently unable to provide an answer. Please try again later.")
                output.append("Relevant Shlokas:")
                for s in result.get('shlokas', [])[:3]:
                    output.append(f"- Gita {s['id']}: {s.get('meaning_english', s['meaning'])[:100]}...")
            else:
                output.append("\nक्षमा करें, मैं अभी उत्तर देने में असमर्थ हूँ।")
                output.append("संबंधित श्लोक:")
                for s in result.get('shlokas', [])[:3]:
                    output.append(f"- गीता {s['id']}: {s['meaning'][:100]}...")
            output.append("\n")
        return "\n".join(output)
