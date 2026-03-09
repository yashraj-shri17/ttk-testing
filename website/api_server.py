"""
Flask API server for Talk to Krishna web interface.
This provides a REST API endpoint for the web frontend.
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os

# Add parent directory to path to import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.gita_api import GitaAPI
from src.config import settings
import edge_tts
import asyncio
import uuid
from flask import send_file

# Create audio cache directory
AUDIO_DIR = os.path.join(os.path.dirname(__file__), 'audio_cache')
if not os.path.exists(AUDIO_DIR):
    os.makedirs(AUDIO_DIR)

# In-memory audio cache for fast serving
audio_cache = {}
import threading

def _clean_text_for_tts(text: str) -> str:
    """
    Clean answer text before TTS:
    1. Remove all emoji characters.
    2. Remove any trailing shloka citation that the LLM may have duplicated at the end.
       e.g. "...कदम उठाओ।\n\nभगवद गीता, अध्याय 2, श्लोक 47" → strip the trailing citation.
    """
    import re

    # 1. Remove emojis (covers BMP + supplementary emoji ranges)
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map
        "\U0001F1E0-\U0001F1FF"  # flags
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "\u2600-\u26FF"          # misc symbols
        "\u2700-\u27BF"          # dingbats
        "\uFE00-\uFE0F"          # variation selectors
        "\u200d"                 # zero width joiner
        "]+",
        flags=re.UNICODE,
    )
    text = emoji_pattern.sub('', text)

    # 2. Strip a trailing shloka citation that appears AFTER the verse block
    #    Pattern: optional newlines + "भगवद गीता[,، ،]*अध्याय..." at end of string
    trailing_citation = re.compile(
        r'\s*भगवद\s*गीता[,،\s]*अध्याय\s*\d+[,،\s]*श्लोक\s*\d+\s*$',
        re.UNICODE
    )
    text = trailing_citation.sub('', text).strip()

    # 3. Strip redundant shloka numbers at the end of verse lines (e.g., ॥25॥ or | 15 |)
    #    Supports both Western (0-9) and Devanagari (०-९) digits
    text = re.sub(r'[।॥|]\s*[0-9०-९]+\s*[।॥|]', '॥', text)

    return text


def _split_text_for_tts(text: str):
    """
    Split answer text into:
      - parts_before_verse: text before the Sanskrit verse lines
      - verse_lines: the Sanskrit verse itself (to be read slower)
      - parts_after_verse: text after the verse block

    The shloka block starts with a line like:
      "भगवद गीता, अध्याय X, श्लोक Y" OR "Bhagavad Gita, Chapter X, Shloka Y"
    followed by Sanskrit verse lines (containing | or ॥ or Devanagari + pipe characters).

    Returns (before, verse, after, lang_hint) as strings/bool.
    """
    import re

    lines = text.split('\n')

    citation_pattern_hi = re.compile(r'भगवद\s*गीता.*?अध्याय.*?श्लोक', re.UNICODE)
    citation_pattern_en = re.compile(r'Bhagavad\s*Gita.*?Chapter.*?Shloka', re.IGNORECASE)
    
    # Sanskrit lines are identified by having | (pipe used as verse separator) or ॥
    sanskrit_line_pattern = re.compile(r'[|॥।]', re.UNICODE)

    before_lines = []
    header_lines = []   # Citation line
    verse_lines = []
    after_lines = []

    state = 'before'  # states: before → citation → verse → after
    is_english = False

    for line in lines:
        stripped = line.strip()
        if state == 'before':
            if citation_pattern_hi.search(stripped):
                header_lines.append(line)
                state = 'citation'
                is_english = False
            elif citation_pattern_en.search(stripped):
                header_lines.append(line)
                state = 'citation'
                is_english = True
            else:
                before_lines.append(line)
        elif state == 'citation':
            # Next non-blank line after citation header is the verse
            if stripped == '':
                header_lines.append(line)
            elif sanskrit_line_pattern.search(stripped) or (
                # Accept any Devanagari-heavy line following citation as verse
                len([c for c in stripped if '\u0900' <= c <= '\u097F']) > len(stripped) * 0.3
            ):
                verse_lines.append(line)
                state = 'verse'
            else:
                # Couldn't find verse — treat rest as after
                after_lines.append(line)
                state = 'after'
        elif state == 'verse':
            if stripped == '' and not verse_lines:
                verse_lines.append(line)
            elif sanskrit_line_pattern.search(stripped) or (
                len([c for c in stripped if '\u0900' <= c <= '\u097F']) > len(stripped) * 0.3
                and stripped != ''
            ):
                verse_lines.append(line)
            else:
                after_lines.append(line)
                state = 'after'
        else:  # after
            after_lines.append(line)

    before_text = '\n'.join(before_lines).strip()
    
    # In English response case, we want to split the Header (English) from Verse (Sanskrit)
    # to use different voices. So we return them separately or handle them in the caller.
    header_text = '\n'.join(header_lines).strip()
    verse_text = '\n'.join(verse_lines).strip()
    after_text = '\n'.join(after_lines).strip()

    # Determine if the 'before' text is primarily English (to double check)
    if not is_english and len(before_text) > 0:
        english_chars = len(re.findall(r'[a-zA-Z]', before_text))
        if english_chars > len(before_text) * 0.5:
            is_english = True

    return before_text, header_text, verse_text, after_text, is_english


def _generate_audio_async(text: str) -> str:
    """
    Generate audio asynchronously and cache it.
    Returns audio_id immediately while generation happens in background.
    
    For shloka verses, uses a slower TTS rate so they are easier to follow.
    For the rest of the text, normal slightly-faster rate is used.
    Emojis and trailing duplicate shloka citations are cleaned before TTS.
    """
    audio_id = str(uuid.uuid4())
    
    def generate():
        try:
            import time
            gen_start = time.time()
            print(f"Starting TTS generation for audio_id: {audio_id}")
            
            import re
            import io

            # 1. Clean text (remove emojis, strip trailing duplicate citation)
            cleaned = _clean_text_for_tts(text)
            # Remove residual HTML tags
            cleaned = re.sub(r'<[^>]*>', '', cleaned).strip()
            print(f"Text length after cleaning: {len(cleaned)} characters")

            # 2. Split into parts and language hint
            before_text, header_text, verse_text, after_text, is_english = _split_text_for_tts(cleaned)
            
            # 3. Choose voices
            # Krishna English voice: mature, calm
            main_voice = "en-US-GuyNeural" if is_english else "hi-IN-MadhurNeural"
            shloka_voice = "hi-IN-MadhurNeural" # Always Hindi pronunciation for Sanskrit

            async def _gen_part(part_text: str, voice: str, rate: str) -> bytes:
                if not part_text.strip():
                    return b''
                buf = io.BytesIO()
                communicate = edge_tts.Communicate(part_text, voice, rate=rate, pitch="+0Hz")
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        buf.write(chunk["data"])
                return buf.getvalue()

            async def _gen_all():
                """Generate all parts and concatenate audio bytes."""
                parts = []
                rate = "+12%"

                if before_text:
                    parts.append(await _gen_part(before_text, main_voice, rate))

                if header_text:
                    # Recommendation: Shloka citation ("Chapter X, Shloka Y") in main voice
                    parts.append(await _gen_part(header_text, main_voice, rate))

                if verse_text:
                    # Sanskrit verse always in Hindi voice
                    parts.append(await _gen_part(verse_text, shloka_voice, rate))

                if after_text:
                    parts.append(await _gen_part(after_text, main_voice, rate))

                if not parts and cleaned:
                    # Fallback: whole cleaned text
                    parts.append(await _gen_part(cleaned, main_voice, rate))

                return b''.join([p for p in parts if p])

            # Run async generation
            tts_start = time.time()
            audio_bytes = asyncio.run(_gen_all())
            tts_time = time.time() - tts_start

            # Cache the audio data
            audio_cache[audio_id] = audio_bytes

            total_time = time.time() - gen_start
            audio_size = len(audio_cache[audio_id]) / 1024
            print(f"TTS complete: {tts_time:.2f}s, Total: {total_time:.2f}s, Size: {audio_size:.1f}KB")

        except Exception as e:
            print(f"Audio generation error: {e}")
            import traceback
            traceback.print_exc()
            audio_cache[audio_id] = None
    
    # Start generation in background thread
    thread = threading.Thread(target=generate, daemon=True)
    thread.start()
    
    return audio_id



app = Flask(__name__)

# CORS configuration for production
from dotenv import load_dotenv

load_dotenv()

import re
frontend_url = os.getenv('FRONTEND_URL')
allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

if frontend_url:
    # Add the provided URL and also a version without trailing slash
    allowed_origins.append(frontend_url)
    if frontend_url.endswith('/'):
        allowed_origins.append(frontend_url[:-1])
    else:
        allowed_origins.append(frontend_url + '/')
else:
    # Fallback to allow all during setup, but MUST reflect origin for credentials
    # This is a bit looser but prevents the absolute "CORS error" blockade
    allowed_origins = [re.compile(r'.*')]

CORS(app, origins=allowed_origins, supports_credentials=True)

# Initialize GitaAPI once
print("Initializing Talk to Krishna API...")
gita_api = GitaAPI()
gita_api._load_resources()
print("API Ready!\n")

@app.route('/api/ask', methods=['POST'])
def ask_question():
    """
    Handle question from web interface.
    
    Request JSON:
        {
            "question": "user's question here",
            "include_audio": true/false (optional, default: false),
            "user_id": 123 (optional, for logged-in users)
        }
    
    Response JSON:
        {
            "answer": "Krishna's response",
            "shlokas": [...],
            "audio_url": "/api/audio/<id>" (if include_audio=true),
            "success": true
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'question' not in data:
            return jsonify({
                'error': 'No question provided',
                'success': False
            }), 400
        
        question = data['question'].strip()
        include_audio = data.get('include_audio', False)
        user_id = data.get('user_id')  # Optional: for logged-in users
        
        session_id = data.get('session_id')  # New: Session ID for context filtering
        
        if not question:
            return jsonify({
                'error': 'Question cannot be empty',
                'success': False
            }), 400

        # --- FAST GREETING CHECK (Backup) ---
        # This ensures we catch greetings at the API layer 
        # to guarantee instant response without DB lookup.
        english_greetings = {
            "hi", "hello", "hey", "hii", "hiii", "helo", "heyy", "heya", "yo",
            "greetings", "good morning", "good afternoon", "good evening", "good night",
            "gm", "ge", "gn", "ga", "morning", "evening", "afternoon",
            "sup", "wassup", "whatsup", "howdy", "hola"
        }
        
        hindi_greetings = {
            "namaste", "namaskar", "namaskaram", "pranam", "pranaam", "pranaams",
            "radhe radhe", "radhey radhey", "radhe", "radhey",
            "jai shri krishna", "jai shree krishna", "jai sri krishna", 
            "hare krishna", "hare krsna", "krishna", "krsna",
            "jai", "jay", "om", "aum",
            "हेलो", "हेल्लो", "हाय", "हाई", "हलो",
            "नमस्ते", "नमस्कार", "नमस्कारम", "प्रणाम", "प्रनाम",
            "राधे राधे", "राधे", "राधेय राधेय",
            "जय श्री कृष्ण", "जय श्रीकृष्ण", "जय कृष्ण",
            "हरे कृष्ण", "हरे कृष्णा", "कृष्ण",
            "जय", "ओम", "ॐ",
            "सुप्रभात", "शुभ संध्या", "शुभ रात्रि",
            "कैसे हो", "कैसे हैं", "क्या हाल", "क्या हाल है",
            "kaise ho", "kaise hain", "kya haal", "kya hal", "namaskaar"
        }
        
        greetings_backup = english_greetings.union(hindi_greetings)
        
        import unicodedata
        q_lower = "".join(c for c in question.lower() if c.isalnum() or c.isspace() or unicodedata.category(c).startswith('M'))
        q_words = q_lower.split()
        
        is_greeting = False
        greeting_language = "hi"
        
        if q_words:
            full_query = ' '.join(q_words)
            if full_query in greetings_backup:
                is_greeting = True
                if full_query in english_greetings:
                    greeting_language = "en"
            
            elif len(q_words) >= 2:
                two_word = f"{q_words[0]} {q_words[1]}"
                if two_word in greetings_backup:
                    if len(q_words) <= 3:
                        is_greeting = True
                        if two_word in english_greetings: greeting_language = "en"
                    else:
                        q_words_set = {'what', 'how', 'why', 'who', 'when', 'where', 
                                     'kya', 'kyun', 'kaise', 'kab', 'kahan', 'kaun',
                                     'explain', 'tell', 'batao', 'bataiye', 'btao'}
                        if not any(qw in q_words for qw in q_words_set):
                            is_greeting = True
                            if two_word in english_greetings: greeting_language = "en"
            
            elif len(q_words) <= 3 and any(w in greetings_backup for w in q_words):
                is_greeting = True
                greeting_word = next(w for w in q_words if w in greetings_backup)
                if greeting_word in english_greetings: greeting_language = "en"
                
            elif len(q_words) <= 6 and q_words[0] in greetings_backup:
                q_words_set = {'what', 'how', 'why', 'who', 'when', 'where', 
                             'kya', 'kyun', 'kaise', 'kab', 'kahan', 'kaun',
                             'explain', 'tell', 'batao', 'bataiye', 'btao',
                             'is', 'are', 'can', 'should', 'would', 'could'}
                if not any(qw in q_words for qw in q_words_set):
                    is_greeting = True
                    if q_words[0] in english_greetings: greeting_language = "en"

        if is_greeting:
            print(f"Greeting detected in API: {question} [{greeting_language}]")
            if greeting_language == "en":
                greeting_text = "Radhe Radhe! I am Lord Krishna. Tell me, how can I help you today?"
            else:
                greeting_text = "राधे राधे! मैं श्री कृष्ण हूँ। कहिये, मैं आपकी क्या सहायता कर सकता हूँ?"
                
            response = {
                'success': True,
                'answer': greeting_text,
                'shlokas': [],
                'llm_used': True 
            }
            
            if user_id:
                save_conversation(user_id, question, greeting_text, [], session_id=session_id)
            
            if include_audio:
                audio_id = _generate_audio_async(greeting_text)
                response['audio_url'] = f'/api/audio/{audio_id}'
                print(f"Greeting audio generated: {audio_id}")
            
            return jsonify(response)
        # ------------------------------------
        
        # Get user's conversation history if logged in
        conversation_history = []
        # if user_id:
        #     # Filter history by session_id if provided (Disabled for faster response times)
        #     conversation_history = get_user_history(user_id, session_id=session_id, limit=5)
        #     print(f"Retrieved {len(conversation_history)} previous conversations for user {user_id} (Session: {session_id})")
        
        # Get answer from GitaAPI with conversation context
        import time
        start_time = time.time()
        result = gita_api.search_with_llm(question, conversation_history=conversation_history)
        llm_time = time.time() - start_time
        
        answer_text = result.get('answer')
        shlokas = result.get('shlokas', [])
        
        # Save conversation if user is logged in
        if user_id and answer_text:
            save_conversation(user_id, question, answer_text, shlokas, session_id=session_id)
            print(f"Saved conversation for user {user_id}")
        
        # Format response
        response = {
            'success': True,
            'answer': answer_text,
            'shlokas': shlokas,
            'llm_used': result.get('llm_used', False)
        }
        
        # Generate audio in parallel if requested
        if include_audio and answer_text:
            audio_start = time.time()
            audio_id = _generate_audio_async(answer_text)
            audio_time = time.time() - audio_start
            response['audio_url'] = f'/api/audio/{audio_id}'
            print(f"Timing: LLM={llm_time:.2f}s, Audio={audio_time:.2f}s")
        
        return jsonify(response)
        
    except Exception as e:
        print(f"Error processing request: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': str(e),
            'success': False
        }), 500

@app.route('/api/speak', methods=['POST'])
def speak_text():
    """
    Generate audio from text using Neural TTS in-memory (no files saved).
    Handles shloka speed and cleaning consistently with background generation.
    """
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400

        import io
        import re

        # 1. Clean and Split
        cleaned = _clean_text_for_tts(text)
        cleaned = re.sub(r'<[^>]*>', '', cleaned).strip()
        before_text, header_text, verse_text, after_text, is_english = _split_text_for_tts(cleaned)

        main_voice = "en-US-GuyNeural" if is_english else "hi-IN-MadhurNeural"
        shloka_voice = "hi-IN-MadhurNeural"

        async def _gen_part(part_text: str, voice: str, rate: str) -> bytes:
            if not part_text.strip():
                return b''
            buf = io.BytesIO()
            communicate = edge_tts.Communicate(part_text, voice, rate=rate, pitch="+0Hz")
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    buf.write(chunk["data"])
            return buf.getvalue()

        async def _gen_all():
            parts = []
            rate = "+12%"
            if before_text:
                parts.append(await _gen_part(before_text, main_voice, rate))
            if header_text:
                parts.append(await _gen_part(header_text, main_voice, rate))
            if verse_text:
                parts.append(await _gen_part(verse_text, shloka_voice, rate))
            if after_text:
                parts.append(await _gen_part(after_text, main_voice, rate))
            if not parts and cleaned:
                parts.append(await _gen_part(cleaned, main_voice, rate))
            return b''.join([p for p in parts if p])

        # Run generation
        audio_bytes = asyncio.run(_gen_all())
        audio_buffer = io.BytesIO(audio_bytes)
        audio_buffer.seek(0)

        return send_file(
            audio_buffer,
            mimetype="audio/mpeg",
            as_attachment=False,
            download_name="response.mp3"
        )

    except Exception as e:
        print(f"TTS Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/transcribe', methods=['POST'])
def transcribe_audio():
    """
    Transcribe audio using Groq Whisper-large-v3.
    """
    try:
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided', 'success': False}), 400
        
        audio_file = request.files['audio']
        
        # Save temp file
        temp_path = os.path.join(AUDIO_DIR, f"temp_{uuid.uuid4()}.webm")
        audio_file.save(temp_path)
        
        # Call Groq
        with open(temp_path, "rb") as file:
            transcription = gita_api.groq_client.audio.transcriptions.create(
                file=(audio_file.filename, file.read()),
                model="whisper-large-v3",
                prompt="The user is speaking in Hindi and English. Please transcribe Hindi in Devanagari script (हिंदी) only. No Urdu. नमस्ते, आप कैसे हैं? Hello, how are you?",
            )
        
        # Cleanup
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
        print(f"Transcribed Text: {transcription.text}")
        return jsonify({'text': transcription.text, 'success': True})
        
    except Exception as e:
        print(f"Transcription error: {e}")
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/api/audio/<audio_id>', methods=['GET'])
def get_audio(audio_id):
    """
    Serve pre-generated audio from cache.
    Polls for audio to be ready if still generating.
    """
    import time
    max_wait = 20  # Increased to 20 seconds for Edge TTS
    start_time = time.time()
    
    print(f"Audio request for ID: {audio_id}")
    
    while time.time() - start_time < max_wait:
        if audio_id in audio_cache:
            audio_data = audio_cache[audio_id]
            
            if audio_data is None:
                print(f"Audio generation failed for {audio_id}")
                return jsonify({'error': 'Audio generation failed'}), 500
            
            elapsed = time.time() - start_time
            print(f"Audio ready after {elapsed:.2f}s")
            
            # Serve from memory
            import io
            audio_buffer = io.BytesIO(audio_data)
            audio_buffer.seek(0)
            
            return send_file(
                audio_buffer,
                mimetype="audio/mpeg",
                as_attachment=False,
                download_name="response.mp3"
            )
        
        # Wait a bit before checking again
        time.sleep(0.1)
    
    elapsed = time.time() - start_time
    print(f"Audio timeout after {elapsed:.2f}s for {audio_id}")
    return jsonify({'error': 'Audio not ready yet', 'waited': f'{elapsed:.2f}s'}), 404


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'Talk to Krishna API',
        'version': '2.0.0'
    })

@app.route('/')
def index():
    """Serve basic info."""
    return jsonify({
        'message': 'Talk to Krishna API',
        'endpoints': {
            '/api/ask': 'POST - Ask a question',
            '/api/health': 'GET - Health check'
        }
    })

import sqlite3
try:
    import psycopg2
    from psycopg2 import sql
except ImportError:
    psycopg2 = None
from werkzeug.security import generate_password_hash, check_password_hash
import json
from datetime import datetime
import re
from collections import defaultdict
import time

# Database setup
# Allow overriding db path for production environments (like Render persistent disks)
import os
DB_NAME = os.environ.get("DB_PATH", "users.db")
DATABASE_URL = os.environ.get("DATABASE_URL")
USE_POSTGRES = bool(DATABASE_URL and psycopg2)

pg_pool = None
if USE_POSTGRES:
    try:
        from psycopg2.pool import ThreadedConnectionPool
        # Pool with min 1 and max 20 connections
        pg_pool = ThreadedConnectionPool(1, 20, DATABASE_URL)
        print("✅ PostgreSQL Connection Pool initialized successfully.")
    except Exception as e:
        print(f"❌ Error initializing DB pool: {e}")

def execute_db(query, params=(), commit=False, fetchone=False, fetchall=False):
    import sqlite3
    conn = None
    is_pooled = False
    
    if USE_POSTGRES:
        if query.count('?') > 0:
            query = query.replace('?', '%s')
            
        if pg_pool:
            conn = pg_pool.getconn()
            is_pooled = True
        else:
            conn = psycopg2.connect(DATABASE_URL)
    else:
        conn = sqlite3.connect(DB_NAME)
    
    c = conn.cursor()
    try:
        c.execute(query, params)
        result = None
        if fetchone:
            result = c.fetchone()
        elif fetchall:
            result = c.fetchall()
        if commit:
            conn.commit()
        return result
    except Exception as e:
        if commit:
            conn.rollback()
        raise e
    finally:
        c.close()
        if is_pooled:
            pg_pool.putconn(conn)
        else:
            conn.close()


# Rate limiting setup
login_attempts = defaultdict(list)
signup_attempts = defaultdict(list)
MAX_ATTEMPTS = 5  # Maximum attempts
WINDOW_SECONDS = 300  # 5 minutes window

def check_rate_limit(ip_address, attempts_dict):
    """Check if IP has exceeded rate limit."""
    now = time.time()
    # Clean old attempts
    attempts_dict[ip_address] = [
        timestamp for timestamp in attempts_dict[ip_address]
        if now - timestamp < WINDOW_SECONDS
    ]
    
    if len(attempts_dict[ip_address]) >= MAX_ATTEMPTS:
        return False, f"Too many attempts. Please try again in {int(WINDOW_SECONDS/60)} minutes."
    
    return True, None

def record_attempt(ip_address, attempts_dict):
    """Record an attempt from IP."""
    attempts_dict[ip_address].append(time.time())

def validate_password(password):
    """
    Validate password strength.
    Requirements:
    - At least 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one number
    - At least one special character
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character (!@#$%^&*...)"
    
    return True, "Password is strong"

def validate_email(email):
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False, "Invalid email format"
    return True, None

def init_db():
    if USE_POSTGRES:
        conn = psycopg2.connect(DATABASE_URL)
        c = conn.cursor()
        
        # Postgres tables using SERIAL
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT DEFAULT 'user',
                has_chat_access BOOLEAN DEFAULT TRUE
            )
        ''')
        
        # Add role column if missing in Postgres
        try:
            c.execute('SELECT role FROM users LIMIT 1')
        except Exception:
            conn.rollback()
            print("Migrating Postgres DB: Adding role column...")
            c.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'")
            conn.commit()

        # Add has_chat_access column if missing in Postgres
        try:
            c.execute('SELECT has_chat_access FROM users LIMIT 1')
        except Exception:
            conn.rollback()
            print("Migrating Postgres DB: Adding chat access column...")
            c.execute("ALTER TABLE users ADD COLUMN has_chat_access BOOLEAN DEFAULT TRUE")
            conn.commit()
            
        c.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users (id),
                session_id TEXT,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                shlokas TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Add session_id if missing (simple check)
        try:
            c.execute('SELECT session_id FROM conversations LIMIT 1')
        except Exception:
            conn.rollback()
            print("Migrating Postgres DB: Adding session_id column...")
            c.execute('ALTER TABLE conversations ADD COLUMN session_id TEXT')
            conn.commit()
            
        c.execute('''
            CREATE TABLE IF NOT EXISTS reset_tokens (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users (id),
                token TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                used BOOLEAN DEFAULT FALSE
            )
        ''')
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS coupons (
                id SERIAL PRIMARY KEY,
                code TEXT UNIQUE NOT NULL,
                discount_type TEXT NOT NULL,
                discount_value NUMERIC NOT NULL,
                active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
    else:
        import sqlite3
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        # SQLite tables
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT DEFAULT 'user',
                has_chat_access BOOLEAN DEFAULT 1
            )
        ''')
        conn.commit()

        # Check for role column in SQLite
        c.execute("PRAGMA table_info(users)")
        cols = [col[1] for col in c.fetchall()]
        if 'role' not in cols:
            print("Migrating SQLite DB: Adding role column...")
            c.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'")
            conn.commit()

        # Check for chat access column in SQLite
        if 'has_chat_access' not in cols:
            print("Migrating SQLite DB: Adding chat access column...")
            c.execute("ALTER TABLE users ADD COLUMN has_chat_access BOOLEAN DEFAULT 1")
            conn.commit()
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users (id),
                session_id TEXT,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                shlokas TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        
        c.execute("PRAGMA table_info(conversations)")
        conv_cols = [col[1] for col in c.fetchall()]
        if 'session_id' not in conv_cols:
            print("Migrating SQLite DB: Adding session_id column...")
            c.execute("ALTER TABLE conversations ADD COLUMN session_id TEXT")
            conn.commit()
            
        c.execute('''
            CREATE TABLE IF NOT EXISTS reset_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users (id),
                token TEXT UNIQUE NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME NOT NULL,
                used BOOLEAN DEFAULT 0
            )''')
            
        c.execute('''
            CREATE TABLE IF NOT EXISTS coupons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                discount_type TEXT NOT NULL,
                discount_value REAL NOT NULL,
                active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()


def get_user_history(user_id, session_id=None, limit=5):
    """Get recent conversation history for a user, optionally filtered by session."""
    
    if session_id:
        history = execute_db('''
            SELECT question, answer, shlokas, timestamp 
            FROM conversations 
            WHERE user_id = ? AND session_id = ?
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (user_id, session_id, limit), fetchall=True)
    else:
        history = execute_db('''
            SELECT question, answer, shlokas, timestamp 
            FROM conversations 
            WHERE user_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (user_id, limit), fetchall=True)
    
    # Format history for LLM context
    formatted_history = []
    for q, a, shlokas, ts in reversed(history):  # Reverse to get chronological order
        # Convert datetime objects to string if needed
        if hasattr(ts, 'isoformat'):
            ts = ts.isoformat()
            
        formatted_history.append({
            'question': q,
            'answer': a,
            'timestamp': ts
        })
    return formatted_history

def save_conversation(user_id, question, answer, shlokas, session_id=None):
    """Save a conversation to the database."""
    from datetime import datetime, timedelta
    # Generate current time in IST (UTC+5:30)
    ist_time = datetime.utcnow() + timedelta(hours=5, minutes=30)
    ist_str = ist_time.strftime('%Y-%m-%d %H:%M:%S')
    
    shlokas_json = json.dumps(shlokas) if shlokas else None
    execute_db('''
        INSERT INTO conversations (user_id, session_id, question, answer, shlokas, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, session_id, question, answer, shlokas_json, ist_str), commit=True)

def generate_reset_token():
    """Generate a secure random token."""
    import secrets
    return secrets.token_urlsafe(32)

def create_reset_token(user_id):
    """Create a password reset token for a user."""
    token = generate_reset_token()
    from datetime import datetime, timedelta
    
    # Token expires in 1 hour
    expires_at = datetime.now() + timedelta(hours=1)
    
    execute_db('''
        INSERT INTO reset_tokens (user_id, token, expires_at)
        VALUES (?, ?, ?)
    ''', (user_id, token, expires_at.isoformat()), commit=True)
    
    return token

def validate_reset_token(token):
    """Validate a reset token and return user_id if valid."""
    from datetime import datetime
    
    result = execute_db('''
        SELECT user_id, expires_at, used 
        FROM reset_tokens 
        WHERE token = ?
    ''', (token,), fetchone=True)
    
    if not result:
        return None, "Invalid reset token"
    
    user_id, expires_at, used = result
    
    if used:
        return None, "This reset link has already been used"
    
    # Check if token has expired
    expires_datetime = datetime.fromisoformat(expires_at)
    if datetime.now() > expires_datetime:
        return None, "This reset link has expired"
    
    return user_id, None

def mark_token_used(token):
    """Mark a reset token as used."""
    if USE_POSTGRES:
        execute_db("UPDATE reset_tokens SET used = TRUE WHERE token = ?", (token,), commit=True)
    else:
        execute_db("UPDATE reset_tokens SET used = 1 WHERE token = ?", (token,), commit=True)

# Initialize DB
init_db()

def seed_admin_user():
    admin_email = 'abhishek@justlearnindia.in'
    default_password = 'AdminPassword123!'
    hashed_pw = generate_password_hash(default_password)
    
    try:
        user = execute_db('SELECT id, role FROM users WHERE email = ?', (admin_email,), fetchone=True)
        if not user:
            execute_db('INSERT INTO users (name, email, password, role, has_chat_access) VALUES (?, ?, ?, ?, ?)', 
                       ('Abhishek Admin', admin_email, hashed_pw, 'admin', True), commit=True)
            print(f"✅ Admin user seeded: {admin_email} / {default_password}")
        elif user[1] != 'admin':
            execute_db("UPDATE users SET role = 'admin', has_chat_access = TRUE WHERE email = ?", (admin_email,), commit=True)
            print(f"✅ User {admin_email} promoted to admin")
    except Exception as e:
        print(f"Admin seeding error: {e}")

# Seed the admin user
seed_admin_user()

from functools import wraps

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        json_data = request.get_json(silent=True) or {}
        user_id = request.args.get('user_id') or json_data.get('user_id')
        if not user_id:
            return jsonify({'error': 'User ID is required', 'success': False}), 400
            
        user = execute_db('SELECT role FROM users WHERE id = ?', (user_id,), fetchone=True)
        if not user or user[0] != 'admin':
            return jsonify({'error': 'Unauthorized: Admin access required', 'success': False}), 403
        return f(*args, **kwargs)
    return decorated_function

@app.route('/api/admin/metrics', methods=['GET'])
def get_admin_metrics():
    user_id = request.args.get('user_id')
    print(f"Admin Metrics Request from user_id: {user_id}")
    
    try:
        # Verify user is an admin
        user = execute_db('SELECT email, role FROM users WHERE id = ?', (user_id,), fetchone=True)
        if not user:
            print(f"Unauthorized: No user found for id {user_id}")
            return jsonify({'error': 'Unauthorized: User not found', 'success': False}), 403
            
        if user[1] != 'admin':
            print(f"Unauthorized: User {user[0]} is not an admin (role: {user[1]})")
            return jsonify({'error': 'Unauthorized: Admin role required', 'success': False}), 403
            
        print(f"Authorized: Metrics request from admin {user[0]}")
            
        # Total users
        total_users_row = execute_db('SELECT COUNT(*) FROM users', fetchone=True)
        total_users = total_users_row[0] if total_users_row else 0
        
        # Today's users (DAU)
        from datetime import datetime, timedelta
        # Get start of today in IST
        now = datetime.utcnow() + timedelta(hours=5, minutes=30)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_start_str = today_start.strftime('%Y-%m-%d %H:%M:%S')
        
        dau_row = execute_db('''
            SELECT COUNT(DISTINCT user_id) 
            FROM conversations 
            WHERE timestamp >= ?
        ''', (today_start_str,), fetchone=True)
        today_users = dau_row[0] if dau_row else 0
        
        # Total conversations
        total_conv_row = execute_db('SELECT COUNT(*) FROM conversations', fetchone=True)
        total_conv = total_conv_row[0] if total_conv_row else 0
        
        # Group conversations by user, also include their status
        all_convs = execute_db('''
            SELECT c.id, u.id, u.name, u.email, c.question, c.answer, c.timestamp, u.role, u.has_chat_access
            FROM conversations c
            JOIN users u ON c.user_id = u.id
            ORDER BY c.timestamp DESC
        ''', fetchall=True)
        
        user_grouped = {}
        for conv in all_convs:
            uid = conv[1]
            if uid not in user_grouped:
                user_grouped[uid] = {
                    'user_id': uid,
                    'user_name': conv[2],
                    'user_email': conv[3],
                    'role': conv[7],
                    'has_chat_access': bool(conv[8]),
                    'conversation_count': 0,
                    'last_active': None,
                    'conversations': []
                }
            
            ts = conv[6]
            if hasattr(ts, 'isoformat'):
                ts = ts.isoformat()
            elif isinstance(ts, str):
                pass # Already a string
                
            if user_grouped[uid]['last_active'] is None:
                user_grouped[uid]['last_active'] = ts
                
            user_grouped[uid]['conversations'].append({
                'id': conv[0],
                'question': conv[4],
                'answer': conv[5],
                'timestamp': ts,
                'model_used': 'llama-3.3-70b-versatile'
            })
            user_grouped[uid]['conversation_count'] += 1
            
        # Fetch users who haven't started any conversation yet
        inactive_users = execute_db('''
            SELECT id, name, email, role, has_chat_access 
            FROM users 
            WHERE id NOT IN (SELECT DISTINCT user_id FROM conversations)
        ''', fetchall=True)
        
        for u in inactive_users:
            user_grouped[u[0]] = {
                'user_id': u[0],
                'user_name': u[1],
                'user_email': u[2],
                'role': u[3],
                'has_chat_access': bool(u[4]),
                'conversation_count': 0,
                'last_active': 'Never',
                'conversations': []
            }
            
        users_list = list(user_grouped.values())
        # Sort users: Admins first, then by last active
        users_list.sort(key=lambda x: (0 if x['role'] == 'admin' else 1, x['last_active'] if x['last_active'] != 'Never' else '0' ), reverse=True)
            
        return jsonify({
            'success': True, 
            'metrics': {
                'total_users': total_users,
                'today_users': today_users,
                'total_conversations': total_conv,
                'user_interactions': users_list
            }
        })
    except Exception as e:
        print(f"❌ Error fetching admin metrics: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': f'Backend error: {str(e)}', 
            'success': False,
            'traceback': traceback.format_exc() if app.debug else None
        }), 500

@app.route('/api/admin/create-admin', methods=['POST'])
def create_new_admin():
    data = request.get_json()
    admin_id = data.get('admin_id') # Current admin doing the operation
    new_email = data.get('email', '').strip()
    temp_password = data.get('password', '')
    
    try:
        # Verify requester is an admin
        requester = execute_db('SELECT role FROM users WHERE id = ?', (admin_id,), fetchone=True)
        if not requester or requester[0] != 'admin':
            return jsonify({'error': 'Unauthorized', 'success': False}), 403
            
        if not new_email or not temp_password:
            return jsonify({'error': 'Email and temporary password are required', 'success': False}), 400
            
        hashed_pw = generate_password_hash(temp_password)
        
        # Check if user already exists
        user = execute_db('SELECT id FROM users WHERE email = ?', (new_email,), fetchone=True)
        if user:
            # Promote existing user to admin
            execute_db("UPDATE users SET role = 'admin', password = ? WHERE id = ?", (hashed_pw, user[0]), commit=True)
            return jsonify({'success': True, 'message': f'User {new_email} promoted to admin with new password'})
        else:
            # Create new admin user
            execute_db('INSERT INTO users (name, email, password, role, has_chat_access) VALUES (?, ?, ?, ?, ?)', 
                       (new_email.split('@')[0], new_email, hashed_pw, 'admin', True), commit=True)
            return jsonify({'success': True, 'message': f'New admin {new_email} created successfully'})
            
    except Exception as e:
        print(f"Error creating admin: {e}")
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/api/admin/grant-access', methods=['POST'])
def grant_chat_access():
    data = request.get_json()
    admin_id = data.get('admin_id')
    user_email = data.get('email', '').strip()
    has_access = data.get('access', True)
    temp_password = data.get('password', '') # Optional: set new password
    
    try:
        # Verify requester is an admin
        requester = execute_db('SELECT role FROM users WHERE id = ?', (admin_id,), fetchone=True)
        if not requester or requester[0] != 'admin':
            return jsonify({'error': 'Unauthorized', 'success': False}), 403
            
        if not user_email:
            return jsonify({'error': 'User email is required', 'success': False}), 400
            
        # Check if user exists
        user = execute_db('SELECT id FROM users WHERE email = ?', (user_email,), fetchone=True)
        if user:
            if temp_password:
                hashed_pw = generate_password_hash(temp_password)
                execute_db("UPDATE users SET has_chat_access = ?, password = ? WHERE id = ?", (has_access, hashed_pw, user[0]), commit=True)
            else:
                execute_db("UPDATE users SET has_chat_access = ? WHERE id = ?", (has_access, user[0]), commit=True)
            
            status = "granted" if has_access else "revoked"
            return jsonify({'success': True, 'message': f'Chat access {status} for {user_email}'})
        else:
            # Create new user with access
            if not temp_password:
                return jsonify({'error': 'Temporary password is required for new users', 'success': False}), 400
                
            hashed_pw = generate_password_hash(temp_password)
            execute_db('INSERT INTO users (name, email, password, role, has_chat_access) VALUES (?, ?, ?, ?, ?)', 
                       (user_email.split('@')[0], user_email, hashed_pw, 'user', has_access), commit=True)
            return jsonify({'success': True, 'message': f'New user {user_email} created with chat access'})
            
    except Exception as e:
        print(f"Error granting access: {e}")
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/api/history', methods=['GET'])
def get_user_chat_history():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'User ID is required', 'success': False}), 400
    try:
        # Fetch up to 50 previous messages
        history = get_user_history(int(user_id), limit=50)
        # Reverse history so oldest is first
        history.reverse()
        return jsonify({'success': True, 'history': history})
    except Exception as e:
        print(f"Error fetching history: {e}")
        return jsonify({'error': 'Failed to fetch history', 'success': False}), 500

@app.route('/api/history', methods=['DELETE'])
def clear_user_chat_history():
    data = request.get_json() or {}
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({'error': 'User ID is required', 'success': False}), 400
    
    try:
        execute_db("DELETE FROM conversations WHERE user_id = ?", (user_id,), commit=True)
        return jsonify({'success': True, 'message': 'History cleared'})
    except Exception as e:
        print(f"Error clearing history: {e}")
        return jsonify({'error': 'Failed to clear history', 'success': False}), 500

@app.route('/api/signup', methods=['POST'])
def signup():
    # Get client IP for rate limiting
    client_ip = request.remote_addr
    
    # Check rate limit
    allowed, error_msg = check_rate_limit(client_ip, signup_attempts)
    if not allowed:
        return jsonify({'error': error_msg, 'success': False}), 429
    
    # Record this attempt
    record_attempt(client_ip, signup_attempts)
    
    data = request.get_json()
    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')

    # Validate required fields
    if not name or not email or not password:
        return jsonify({'error': 'All fields are required', 'success': False}), 400
    
    # Validate name length
    if len(name) < 2:
        return jsonify({'error': 'Name must be at least 2 characters', 'success': False}), 400
    
    if len(name) > 100:
        return jsonify({'error': 'Name is too long', 'success': False}), 400

    # Validate email format
    email_valid, email_error = validate_email(email)
    if not email_valid:
        return jsonify({'error': email_error, 'success': False}), 400

    # Validate password strength
    password_valid, password_error = validate_password(password)
    if not password_valid:
        return jsonify({'error': password_error, 'success': False}), 400

    # Hash password
    hashed_pw = generate_password_hash(password)

    try:
        execute_db('INSERT INTO users (name, email, password) VALUES (?, ?, ?)', (name, email, hashed_pw), commit=True)
        
        print(f"New user registered: {email}")
        return jsonify({'message': 'Account created successfully!', 'success': True}), 201
    except Exception as e:
        if 'UNIQUE' in str(e).upper() or 'INTEGRITY' in str(e).upper():
            return jsonify({'error': 'This email is already registered', 'success': False}), 409
        print(f"Signup error: {e}")
        return jsonify({'error': 'Registration failed. Please try again.', 'success': False}), 500
    # Dummy block to avoid syntax errors if previous except was replaced
    except ValueError:
        return jsonify({'error': 'This email is already registered', 'success': False}), 409
    except Exception as e:
        print(f"Signup error: {e}")
        return jsonify({'error': 'Registration failed. Please try again.', 'success': False}), 500

@app.route('/api/login', methods=['POST'])
def login():
    # Get client IP for rate limiting
    client_ip = request.remote_addr
    
    # Check rate limit
    allowed, error_msg = check_rate_limit(client_ip, login_attempts)
    if not allowed:
        return jsonify({'error': error_msg, 'success': False}), 429
    
    # Record this attempt
    record_attempt(client_ip, login_attempts)
    
    data = request.get_json()
    email = data.get('email', '').strip()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'error': 'Email and password are required', 'success': False}), 400
    
    # Validate email format
    email_valid, email_error = validate_email(email)
    if not email_valid:
        return jsonify({'error': 'Invalid email format', 'success': False}), 400

    try:
        user = execute_db('SELECT id, name, email, password, role, has_chat_access FROM users WHERE email = ?', (email,), fetchone=True)

        if user and check_password_hash(user[3], password):
            print(f"Successful login: {email}")
            return jsonify({
                'message': 'Login successful',
                'success': True,
                'user': {
                    'id': user[0],
                    'name': user[1],
                    'email': user[2],
                    'role': user[4],
                    'has_chat_access': bool(user[5])
                }
            }), 200
        else:
            print(f"Failed login attempt: {email}")
            return jsonify({'error': 'Invalid email or password', 'success': False}), 401
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({'error': 'Login failed. Please try again.', 'success': False}), 500

@app.route('/api/forgot-password', methods=['POST'])
def forgot_password():
    """Request a password reset token."""
    data = request.get_json()
    email = data.get('email', '').strip()
    
    if not email:
        return jsonify({'error': 'Email is required', 'success': False}), 400
    
    # Validate email format
    email_valid, email_error = validate_email(email)
    if not email_valid:
        return jsonify({'error': 'Invalid email format', 'success': False}), 400
    
    try:
        user = execute_db('SELECT id FROM users WHERE email = ?', (email,), fetchone=True)
        
        # Always return success to prevent email enumeration
        # But only create token if user exists
        if user:
            user_id = user[0]
            token = create_reset_token(user_id)
            
            # In production, send this token via email
            # For now, we'll return it in the response (NOT SECURE FOR PRODUCTION)
            print(f"Password reset requested for: {email}")
            print(f"Reset token: {token}")
            
            # TODO: Send email with reset link
            # reset_link = f"http://localhost:3000/reset-password?token={token}"
            
            return jsonify({
                'success': True,
                'message': 'If an account exists with this email, a reset link has been sent.'
            }), 200
        else:
            # Return same message to prevent email enumeration
            return jsonify({
                'success': True,
                'message': 'If an account exists with this email, a reset link has been sent.'
            }), 200
            
    except Exception as e:
        print(f"Forgot password error: {e}")
        return jsonify({'error': 'Request failed. Please try again.', 'success': False}), 500

@app.route('/api/reset-password', methods=['POST'])
def reset_password():
    """Reset password using a valid token."""
    data = request.get_json()
    token = data.get('token', '').strip()
    new_password = data.get('password', '')
    
    if not token or not new_password:
        return jsonify({'error': 'Token and new password are required', 'success': False}), 400
    
    # Validate password strength
    password_valid, password_error = validate_password(new_password)
    if not password_valid:
        return jsonify({'error': password_error, 'success': False}), 400
    
    # Validate token
    user_id, error = validate_reset_token(token)
    if error:
        return jsonify({'error': error, 'success': False}), 400
    
    try:
        # Update password
        hashed_pw = generate_password_hash(new_password)
        execute_db('UPDATE users SET password = ? WHERE id = ?', (hashed_pw, user_id), commit=True)
        
        # Mark token as used
        mark_token_used(token)
        
        print(f"Password reset successful for user ID: {user_id}")
        return jsonify({
            'success': True,
            'message': 'Password has been reset successfully. You can now log in with your new password.'
        }), 200
        
    except Exception as e:
        print(f"Reset password error: {e}")
        return jsonify({'error': 'Password reset failed. Please try again.', 'success': False}), 500

# ==========================================
# Coupon Management (Admin & Validation)
# ==========================================

@app.route('/api/admin/coupons', methods=['GET'])
@admin_required
def get_coupons():
    try:
        user_id = request.args.get('user_id')
        coupons = execute_db('SELECT id, code, discount_type, discount_value, active, created_at FROM coupons ORDER BY created_at DESC', fetchall=True)
        coupons_list = []
        for c in coupons:
            # Handle datetime objects for JSON serialization
            created_at = c[5]
            if created_at and hasattr(created_at, 'isoformat'):
                created_at = created_at.isoformat()
            elif created_at is not None:
                created_at = str(created_at)
                
            coupons_list.append({
                'id': c[0],
                'code': c[1],
                'discount_type': c[2],
                'discount_value': float(c[3]),
                'is_active': bool(c[4]), # Keep key name 'is_active' for frontend compatibility
                'created_at': created_at
            })
            
        return jsonify({
            'success': True,
            'coupons': coupons_list
        }), 200
    except Exception as e:
        print(f"[ERROR] Fetch coupons failed: {e}")
        return jsonify({'error': 'Failed to fetch coupons', 'success': False}), 500

@app.route('/api/admin/coupons', methods=['POST'])
@admin_required
def create_coupon():
    """Create a new coupon (admin only)"""
    data = request.get_json()
    code = data.get('code', '').strip().upper()
    discount_type = data.get('discount_type')
    discount_value = data.get('discount_value')
    
    if not code or not discount_type or discount_value is None:
        return jsonify({'error': 'Code, type, and value are required', 'success': False}), 400
        
    if discount_type not in ['flat', 'percent']:
        return jsonify({'error': 'Invalid discount type', 'success': False}), 400
        
    try:
        execute_db(
            'INSERT INTO coupons (code, discount_type, discount_value) VALUES (?, ?, ?)',
            (code, discount_type, discount_value),
            commit=True
        )
        return jsonify({
            'success': True,
            'message': f'Coupon {code} created successfully'
        }), 201
    except Exception as e:
        error_str = str(e).upper()
        if 'UNIQUE' in error_str or 'ALREADY EXISTS' in error_str:
            return jsonify({'error': f'Coupon code "{code}" already exists', 'success': False}), 409
            
        print(f"Error creating coupon: {e}")
        return jsonify({'error': 'Failed to create coupon due to system error', 'success': False}), 500

@app.route('/api/admin/coupons/<int:coupon_id>', methods=['DELETE'])
@admin_required
def delete_coupon(coupon_id):
    """Delete a coupon (admin only)"""
    try:
        execute_db('DELETE FROM coupons WHERE id = ?', (coupon_id,), commit=True)
        return jsonify({'success': True, 'message': 'Coupon deleted successfully'}), 200
    except Exception as e:
        print(f"Error deleting coupon: {e}")
        return jsonify({'error': 'Failed to delete coupon', 'success': False}), 500

@app.route('/api/coupons/validate', methods=['POST'])
def validate_coupon():
    """Validate a coupon code"""
    data = request.get_json()
    code = data.get('code', '').strip().upper()
    
    if not code:
        return jsonify({'error': 'Coupon code is required', 'success': False}), 400
        
    try:
        # In Postgres, use a compatible boolean check for column 'active'
        active_check = "TRUE" if USE_POSTGRES else "1"
        query = f'SELECT discount_type, discount_value FROM coupons WHERE code = ? AND active = {active_check}'
        
        coupon = execute_db(query, (code,), fetchone=True)
        
        if not coupon:
            return jsonify({'error': 'Invalid or inactive coupon code', 'success': False}), 404
            
        return jsonify({
            'success': True,
            'coupon': {
                'code': code,
                'type': coupon[0],
                'discount': float(coupon[1])
            }
        }), 200
    except Exception as e:
        print(f"[ERROR] Validation failed: {e}")
        return jsonify({'error': 'Failed to validate coupon', 'success': False}), 500

if __name__ == '__main__':
    print("\n" + "="*70)
    print("Talk to Krishna - Web API Server")
    print("="*70)
    print("\nStarting server on http://localhost:5000")
    print("Open website/index.html in your browser to use the web interface\n")
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False  # Set to True for development
    )
