import re

with open('website/api_server.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Make sure we import psycopg2
if "import psycopg2" not in code:
    code = code.replace("import sqlite3\n", "import sqlite3\ntry:\n    import psycopg2\n    from psycopg2 import sql\nexcept ImportError:\n    psycopg2 = None\n")

# Database setup logic
db_setup = """# Database setup
# Allow overriding db path for production environments (like Render persistent disks)
import os
DB_NAME = os.environ.get("DB_PATH", "users.db")
DATABASE_URL = os.environ.get("DATABASE_URL")
USE_POSTGRES = bool(DATABASE_URL and psycopg2)

def execute_db(query, params=(), commit=False, fetchone=False, fetchall=False):
    import sqlite3
    if USE_POSTGRES:
        conn = psycopg2.connect(DATABASE_URL)
        if query.count('?') > 0:
            query = query.replace('?', '%s')
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
    finally:
        c.close()
        conn.close()
"""
if "def execute_db" not in code:
    code = code.replace("import os\nDB_NAME = os.environ.get(\"DB_PATH\", \"users.db\")", db_setup)

# We need to replace init_db implementation entirely
init_db_new = """def init_db():
    if USE_POSTGRES:
        conn = psycopg2.connect(DATABASE_URL)
        c = conn.cursor()
        
        # Postgres tables using SERIAL
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        
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
                password TEXT NOT NULL
            )
        ''')
        
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
        
        try:
            c.execute('SELECT session_id FROM conversations LIMIT 1')
        except sqlite3.OperationalError:
            print("Migrating SQLite DB: Adding session_id column...")
            c.execute('ALTER TABLE conversations ADD COLUMN session_id TEXT')
            
        c.execute('''
            CREATE TABLE IF NOT EXISTS reset_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users (id),
                token TEXT UNIQUE NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME NOT NULL,
                used BOOLEAN DEFAULT 0
            )''')
        conn.commit()
        conn.close()
"""

# We'll use re.sub for init_db
code = re.sub(r'def init_db\(\):.*?conn\.close\(\)', init_db_new, code, flags=re.DOTALL)


code = code.replace('''    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    if session_id:
        # If session_id provided, only get history for THAT session
        c.execute(\'\'\'
            SELECT question, answer, shlokas, timestamp 
            FROM conversations 
            WHERE user_id = ? AND session_id = ?
            ORDER BY timestamp DESC 
            LIMIT ?
        \'\'\', (user_id, session_id, limit))
    else:
        # Fallback to global history (or maybe just empty if we want strict sessions?)
        c.execute(\'\'\'
            SELECT question, answer, shlokas, timestamp 
            FROM conversations 
            WHERE user_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        \'\'\', (user_id, limit))
        
    history = c.fetchall()
    conn.close()''', '''    
    if session_id:
        history = execute_db(\'\'\'
            SELECT question, answer, shlokas, timestamp 
            FROM conversations 
            WHERE user_id = ? AND session_id = ?
            ORDER BY timestamp DESC 
            LIMIT ?
        \'\'\', (user_id, session_id, limit), fetchall=True)
    else:
        history = execute_db(\'\'\'
            SELECT question, answer, shlokas, timestamp 
            FROM conversations 
            WHERE user_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        \'\'\', (user_id, limit), fetchall=True)''')


code = code.replace('''    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    shlokas_json = json.dumps(shlokas) if shlokas else None
    c.execute(\'\'\'
        INSERT INTO conversations (user_id, session_id, question, answer, shlokas)
        VALUES (?, ?, ?, ?, ?)
    \'\'\', (user_id, session_id, question, answer, shlokas_json))
    conn.commit()
    conn.close()''', '''    shlokas_json = json.dumps(shlokas) if shlokas else None
    execute_db(\'\'\'
        INSERT INTO conversations (user_id, session_id, question, answer, shlokas)
        VALUES (?, ?, ?, ?, ?)
    \'\'\', (user_id, session_id, question, answer, shlokas_json), commit=True)''')


code = code.replace('''    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(\'\'\'
        INSERT INTO reset_tokens (user_id, token, expires_at)
        VALUES (?, ?, ?)
    \'\'\', (user_id, token, expires_at.isoformat()))
    conn.commit()
    conn.close()''', '''    execute_db(\'\'\'
        INSERT INTO reset_tokens (user_id, token, expires_at)
        VALUES (?, ?, ?)
    \'\'\', (user_id, token, expires_at.isoformat()), commit=True)''')


code = code.replace('''    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(\'\'\'
        SELECT user_id, expires_at, used 
        FROM reset_tokens 
        WHERE token = ?
    \'\'\', (token,))
    result = c.fetchone()
    conn.close()''', '''    result = execute_db(\'\'\'
        SELECT user_id, expires_at, used 
        FROM reset_tokens 
        WHERE token = ?
    \'\'\', (token,), fetchone=True)''')


code = code.replace('''    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(\'\'\'
        UPDATE reset_tokens 
        SET used = 1 
        WHERE token = ?
    \'\'\', (token,))
    conn.commit()
    conn.close()''', '''    if USE_POSTGRES:
        execute_db("UPDATE reset_tokens SET used = TRUE WHERE token = ?", (token,), commit=True)
    else:
        execute_db("UPDATE reset_tokens SET used = 1 WHERE token = ?", (token,), commit=True)''')

code = code.replace('''        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('INSERT INTO users (name, email, password) VALUES (?, ?, ?)', (name, email, hashed_pw))
        conn.commit()
        conn.close()''', '''        execute_db('INSERT INTO users (name, email, password) VALUES (?, ?, ?)', (name, email, hashed_pw), commit=True)''')

code = code.replace('''    except sqlite3.IntegrityError:''', '''    except Exception as e:
        if 'UNIQUE' in str(e).upper() or 'INTEGRITY' in str(e).upper():
            return jsonify({'error': 'This email is already registered', 'success': False}), 409
        print(f"Signup error: {e}")
        return jsonify({'error': 'Registration failed. Please try again.', 'success': False}), 500
    # Dummy block to avoid syntax errors if previous except was replaced
    except ValueError:''')

code = code.replace('''        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('SELECT id, name, email, password FROM users WHERE email = ?', (email,))
        user = c.fetchone()
        conn.close()''', '''        user = execute_db('SELECT id, name, email, password FROM users WHERE email = ?', (email,), fetchone=True)''')

code = code.replace('''        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('SELECT id FROM users WHERE email = ?', (email,))
        user = c.fetchone()
        conn.close()''', '''        user = execute_db('SELECT id FROM users WHERE email = ?', (email,), fetchone=True)''')

code = code.replace('''        hashed_pw = generate_password_hash(new_password)
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('UPDATE users SET password = ? WHERE id = ?', (hashed_pw, user_id))
        conn.commit()
        conn.close()''', '''        hashed_pw = generate_password_hash(new_password)
        execute_db('UPDATE users SET password = ? WHERE id = ?', (hashed_pw, user_id), commit=True)''')

with open('website/api_server.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Modified api_server.py")
