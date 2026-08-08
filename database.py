import os
import json
import psycopg2
from psycopg2.extras import RealDictConnection
from datetime import datetime, timezone

DB_URL = os.environ.get("DATABASE_URL")

def get_db_connection():
    return psycopg2.connect(DB_URL, connection_factory=RealDictConnection)

def init_db():
    if not DB_URL:
        return
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS agents (id TEXT PRIMARY KEY, name TEXT, domain TEXT, created_at TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS posts (id TEXT PRIMARY KEY, agent_id TEXT, text TEXT, rationale TEXT, sources TEXT, created_at TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS topic_history (url TEXT PRIMARY KEY, agent_id TEXT, title TEXT, status TEXT, rejection_reason TEXT, created_at TEXT)''')
    conn.commit()
    conn.close()

def get_utc_now_iso(): return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def save_agent(agent_id, name, domain):
    conn = get_db_connection(); cursor = conn.cursor()
    cursor.execute("INSERT INTO agents (id, name, domain, created_at) VALUES (%s, %s, %s, %s)", (agent_id, name, domain, get_utc_now_iso()))
    conn.commit(); conn.close()

def get_agent(agent_id):
    conn = get_db_connection(); cursor = conn.cursor()
    cursor.execute("SELECT * FROM agents WHERE id = %s", (agent_id,))
    agent = cursor.fetchone(); conn.close(); return agent

def save_post(post_id, agent_id, text, rationale, sources, created_at):
    conn = get_db_connection(); cursor = conn.cursor()
    cursor.execute("INSERT INTO posts (id, agent_id, text, rationale, sources, created_at) VALUES (%s, %s, %s, %s, %s, %s)", (post_id, agent_id, text, rationale, json.dumps(sources), created_at))
    conn.commit(); conn.close()

def get_feed(agent_id):
    conn = get_db_connection(); cursor = conn.cursor()
    cursor.execute("SELECT id, text, rationale, sources, created_at FROM posts WHERE agent_id = %s ORDER BY created_at DESC", (agent_id,))
    rows = cursor.fetchall(); conn.close()
    return [{"id": r["id"], "createdAt": r["created_at"], "text": r["text"], "rationale": r["rationale"], "sources": json.loads(r["sources"])} for r in rows]

def is_topic_processed(url):
    conn = get_db_connection(); cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM topic_history WHERE url = %s", (url,))
    res = cursor.fetchone(); conn.close(); return res is not None

def record_topic(url, agent_id, title, status, rejection_reason=""):
    conn = get_db_connection(); cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO topic_history (url, agent_id, title, status, rejection_reason, created_at) 
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (url) DO UPDATE 
        SET status = EXCLUDED.status, rejection_reason = EXCLUDED.rejection_reason, created_at = EXCLUDED.created_at
    """, (url, agent_id, title, status, rejection_reason, get_utc_now_iso()))
    conn.commit(); conn.close()

def get_memory_context(agent_id, limit=5):
    conn = get_db_connection(); cursor = conn.cursor()
    cursor.execute("SELECT text FROM posts WHERE agent_id = %s ORDER BY created_at DESC LIMIT %s", (agent_id, limit))
    posts = [r["text"] for r in cursor.fetchall()]
    cursor.execute("SELECT title, status, rejection_reason FROM topic_history WHERE agent_id = %s ORDER BY created_at DESC LIMIT 10", (agent_id,))
    topics = [f"- {r['title']} [{r['status']}] Reason: {r['rejection_reason']}" for r in cursor.fetchall()]
    conn.close(); return posts, topics
