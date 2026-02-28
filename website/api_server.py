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

def _generate_audio_async(text: str) -> str:
    """
    Generate audio asynchronously and cache it.
    Returns audio_id immediately while generation happens in background.
    """
    audio_id = str(uuid.uuid4())
    
    def generate():
        try:
            import time
            gen_start = time.time()
            print(f"Starting TTS generation for audio_id: {audio_id}")
            
            # Clean text
            import re
            clean_text = re.sub(r'<[^>]*>', '', text).replace('\n', ' ')
            print(f"Text length: {len(clean_text)} characters")
            
            # Buffer to hold audio in memory
            import io
            audio_buffer = io.BytesIO()
            
            async def _gen():
                # Faster speech rate for quicker delivery (25% faster)
                communicate = edge_tts.Communicate(clean_text, "hi-IN-MadhurNeural", rate="+25%", pitch="+0Hz")
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        audio_buffer.write(chunk["data"])
            
            # Run async generation
            tts_start = time.time()
            asyncio.run(_gen())
            tts_time = time.time() - tts_start
            
            # Reset buffer pointer
            audio_buffer.seek(0)
            
            # Cache the audio data
            audio_cache[audio_id] = audio_buffer.getvalue()
            
            total_time = time.time() - gen_start
            audio_size = len(audio_cache[audio_id]) / 1024
            print(f"TTS complete: {tts_time:.2f}s, Total: {total_time:.2f}s, Size: {audio_size:.1f}KB")
            
        except Exception as e:
            print(f"Audio generation error: {e}")
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
        greetings_backup = {
            # English greetings
            "hi", "hello", "hey", "hii", "hiii", "helo", "heyy", "heya", "yo",
            "greetings", "good morning", "good afternoon", "good evening", "good night",
            "gm", "ge", "gn", "ga", "morning", "evening", "afternoon",
            
            # Hindi/Sanskrit greetings (Romanized)
            "namaste", "namaskar", "namaskaram", "pranam", "pranaam", "pranaams",
            "radhe radhe", "radhey radhey", "radhe", "radhey",
            "jai shri krishna", "jai shree krishna", "jai sri krishna", 
            "hare krishna", "hare krsna", "krishna", "krsna",
            "jai", "jay", "om", "aum",
            
            # Hindi Devanagari Script Greetings
            "हेलो", "हेल्लो", "हाय", "हाई", "हलो",
            "नमस्ते", "नमस्कार", "नमस्कारम", "प्रणाम", "प्रनाम",
            "राधे राधे", "राधे", "राधेय राधेय",
            "जय श्री कृष्ण", "जय श्रीकृष्ण", "जय कृष्ण",
            "हरे कृष्ण", "हरे कृष्णा", "कृष्ण",
            "जय", "ओम", "ॐ",
            "सुप्रभात", "शुभ संध्या", "शुभ रात्रि",
            "कैसे हो", "कैसे हैं", "क्या हाल", "क्या हाल है",
            
            # Casual/Informal
            "sup", "wassup", "whatsup", "howdy", "hola",
            "kaise ho", "kaise hain", "kya haal", "kya hal", "namaskaar"
        }
        
        import unicodedata
        q_lower = "".join(c for c in question.lower() if c.isalnum() or c.isspace() or unicodedata.category(c).startswith('M'))
        q_words = q_lower.split()
        
        is_greeting = False
        if q_words:
            # Check if entire query is a greeting phrase
            full_query = ' '.join(q_words)
            if full_query in greetings_backup:
                is_greeting = True
            
            # Check for two-word greeting phrases
            elif len(q_words) >= 2:
                two_word = f"{q_words[0]} {q_words[1]}"
                if two_word in greetings_backup:
                    if len(q_words) <= 3:
                        is_greeting = True
                    else:
                        q_words_set = {'what', 'how', 'why', 'who', 'when', 'where', 
                                     'kya', 'kyun', 'kaise', 'kab', 'kahan', 'kaun',
                                     'explain', 'tell', 'batao', 'bataiye', 'btao'}
                        if not any(qw in q_words for qw in q_words_set):
                            is_greeting = True
            
            # Case 1: Very short (just greeting)
            elif len(q_words) <= 3 and any(w in greetings_backup for w in q_words):
                is_greeting = True
                
            # Case 2: Greeting start, no question words
            elif len(q_words) <= 6 and q_words[0] in greetings_backup:
                q_words_set = {'what', 'how', 'why', 'who', 'when', 'where', 
                             'kya', 'kyun', 'kaise', 'kab', 'kahan', 'kaun',
                             'explain', 'tell', 'batao', 'bataiye', 'btao',
                             'is', 'are', 'can', 'should', 'would', 'could'}
                if not any(qw in q_words for qw in q_words_set):
                    is_greeting = True



        if is_greeting:
            print(f"Greeting detected in API: {question}")
            greeting_text = "राधे राधे! मैं श्री कृष्ण हूँ। कहिये, मैं आपकी क्या सहायता कर सकता हूँ?"
            response = {
                'success': True,
                'answer': greeting_text,
                'shlokas': [],
                'llm_used': True 
            }
            
            # Save greeting conversation if user is logged in
            if user_id:
                save_conversation(user_id, question, greeting_text, [], session_id=session_id)
            
            # Generate audio if requested
            if include_audio:
                audio_id = _generate_audio_async(greeting_text)
                response['audio_url'] = f'/api/audio/{audio_id}'
                print(f"Greeting audio generated: {audio_id}")
            
            return jsonify(response)
        # ------------------------------------
        
        # Get user's conversation history if logged in
        conversation_history = []
        if user_id:
            # Filter history by session_id if provided
            conversation_history = get_user_history(user_id, session_id=session_id, limit=5)
            print(f"Retrieved {len(conversation_history)} previous conversations for user {user_id} (Session: {session_id})")
        
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
    """
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400

        # Voices: hi-IN-MadhurNeural (Male)
        voice = "hi-IN-MadhurNeural" 
        
        # Buffer to hold audio in memory
        import io
        audio_buffer = io.BytesIO()

        async def _generate():
            # Speed up speech rate for faster delivery (25% faster)
            communicate = edge_tts.Communicate(text, voice, rate="+25%", pitch="+0Hz")
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_buffer.write(chunk["data"])

        # Run async generation
        asyncio.run(_generate())

        # Reset buffer pointer to beginning
        audio_buffer.seek(0)

        # Return file from memory
        return send_file(
            audio_buffer,
            mimetype="audio/mpeg",
            as_attachment=False,
            download_name="response.mp3"
        )

    except Exception as e:
        print(f"TTS Error: {e}")
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
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    
    # Conversations table
    c.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            session_id TEXT,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            shlokas TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Check if session_id column exists (migration for existing DB)
    try:
        c.execute('SELECT session_id FROM conversations LIMIT 1')
    except sqlite3.OperationalError:
        print("Migrating DB: Adding session_id column...")
        c.execute('ALTER TABLE conversations ADD COLUMN session_id TEXT')
    
    # Password reset tokens table
    c.execute('''
        CREATE TABLE IF NOT EXISTS reset_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT UNIQUE NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            expires_at DATETIME NOT NULL,
            used BOOLEAN DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def get_user_history(user_id, session_id=None, limit=5):
    """Get recent conversation history for a user, optionally filtered by session."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    if session_id:
        # If session_id provided, only get history for THAT session
        c.execute('''
            SELECT question, answer, shlokas, timestamp 
            FROM conversations 
            WHERE user_id = ? AND session_id = ?
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (user_id, session_id, limit))
    else:
        # Fallback to global history (or maybe just empty if we want strict sessions?)
        c.execute('''
            SELECT question, answer, shlokas, timestamp 
            FROM conversations 
            WHERE user_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (user_id, limit))
        
    history = c.fetchall()
    conn.close()
    
    # Format history for LLM context
    formatted_history = []
    for q, a, shlokas, ts in reversed(history):  # Reverse to get chronological order
        formatted_history.append({
            'question': q,
            'answer': a,
            'timestamp': ts
        })
    return formatted_history

def save_conversation(user_id, question, answer, shlokas, session_id=None):
    """Save a conversation to the database."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    shlokas_json = json.dumps(shlokas) if shlokas else None
    c.execute('''
        INSERT INTO conversations (user_id, session_id, question, answer, shlokas)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, session_id, question, answer, shlokas_json))
    conn.commit()
    conn.close()

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
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        INSERT INTO reset_tokens (user_id, token, expires_at)
        VALUES (?, ?, ?)
    ''', (user_id, token, expires_at.isoformat()))
    conn.commit()
    conn.close()
    
    return token

def validate_reset_token(token):
    """Validate a reset token and return user_id if valid."""
    from datetime import datetime
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        SELECT user_id, expires_at, used 
        FROM reset_tokens 
        WHERE token = ?
    ''', (token,))
    result = c.fetchone()
    conn.close()
    
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
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        UPDATE reset_tokens 
        SET used = 1 
        WHERE token = ?
    ''', (token,))
    conn.commit()
    conn.close()

# Initialize DB
init_db()

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
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('INSERT INTO users (name, email, password) VALUES (?, ?, ?)', (name, email, hashed_pw))
        conn.commit()
        conn.close()
        
        print(f"New user registered: {email}")
        return jsonify({'message': 'Account created successfully!', 'success': True}), 201
    except sqlite3.IntegrityError:
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
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('SELECT id, name, email, password FROM users WHERE email = ?', (email,))
        user = c.fetchone()
        conn.close()

        if user and check_password_hash(user[3], password):
            print(f"Successful login: {email}")
            return jsonify({
                'message': 'Login successful',
                'success': True,
                'user': {
                    'id': user[0],
                    'name': user[1],
                    'email': user[2]
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
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('SELECT id FROM users WHERE email = ?', (email,))
        user = c.fetchone()
        conn.close()
        
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
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('UPDATE users SET password = ? WHERE id = ?', (hashed_pw, user_id))
        conn.commit()
        conn.close()
        
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
