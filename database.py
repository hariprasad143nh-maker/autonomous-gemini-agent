import sqlite3
import json
from datetime import datetime, timezone

DB_NAME = "agent_data.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Create agents table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS agents (
            id TEXT PRIMARY KEY,
            name TEXT,
            domain TEXT
        )
    ''')
    # Create posts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id TEXT PRIMARY KEY,
            agent_id TEXT,
            text TEXT,
            rationale TEXT,
            sources TEXT,
            created_at TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_utc_now_iso():
    # Returns strict ISO 8601 UTC time as required by the hackathon
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def save_agent(agent_id, name, domain):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO agents (id, name, domain) VALUES (?, ?, ?)', (agent_id, name, domain))
    conn.commit()
    conn.close()

def get_agent(agent_id):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM agents WHERE id = ?', (agent_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def get_all_agents():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM agents')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def save_post(post_id, agent_id, text, rationale, sources, created_at):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # SQLite can't save lists directly, so we convert sources to a JSON string
    sources_json = json.dumps(sources)
    cursor.execute('INSERT INTO posts (id, agent_id, text, rationale, sources, created_at) VALUES (?, ?, ?, ?, ?, ?)', 
                   (post_id, agent_id, text, rationale, sources_json, created_at))
    conn.commit()
    conn.close()

def get_feed(agent_id):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    # Retrieve posts in reverse chronological order
    cursor.execute('SELECT * FROM posts WHERE agent_id = ? ORDER BY created_at DESC', (agent_id,))
    rows = cursor.fetchall()
    conn.close()
    
    posts = []
    for row in rows:
        post = dict(row)
        # Format exact output required by hackathon rules
        posts.append({
            "id": post["id"],
            "createdAt": post["created_at"],
            "text": post["text"],
            "rationale": post["rationale"],
            "sources": json.loads(post["sources"])
        })
    return posts