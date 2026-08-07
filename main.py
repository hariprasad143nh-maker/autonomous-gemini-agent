from contextlib import asynccontextmanager
from datetime import datetime
import os
import sqlite3
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, HTTPException
import feedparser
from google import genai
from google.genai import types
from pydantic import BaseModel

# ==========================================
# 1. MEMORY DATABASE (SQLite Setup)
# ==========================================
DB_FILE = "agent_memory.db"


def init_db():
  """Creates the database table if it doesn't exist."""
  conn = sqlite3.connect(DB_FILE)
  cursor = conn.cursor()
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            source TEXT,
            prompt TEXT,
            response TEXT
        )
    """)
  conn.commit()
  conn.close()


def log_interaction(source: str, prompt: str, response: str):
  """Saves a conversation or background task to the database."""
  conn = sqlite3.connect(DB_FILE)
  cursor = conn.cursor()
  cursor.execute(
      "INSERT INTO logs (timestamp, source, prompt, response) VALUES (?, ?, ?,"
      " ?)",
      (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), source, prompt, response),
  )
  conn.commit()
  conn.close()


# ==========================================
# 2. AGENT TOOLS (Functions Gemini Can Call)
# ==========================================
def get_current_time() -> str:
  """Returns the current date and time."""
  return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def fetch_tech_news() -> str:
  """Fetches the top 5 tech news headlines from an RSS feed."""
  try:
    feed = feedparser.parse("https://news.ycombinator.com/rss")
    headlines = []
    for entry in feed.entries[:5]:
      headlines.append(f"- {entry.title} ({entry.link})")
    return "\n".join(headlines) if headlines else "No headlines found."
  except Exception as e:
    return f"Error fetching news: {str(e)}"


def read_recent_memory() -> str:
  """Reads the last 3 stored logs from the database memory."""
  conn = sqlite3.connect(DB_FILE)
  cursor = conn.cursor()
  cursor.execute(
      "SELECT timestamp, source, prompt, response FROM logs ORDER BY id DESC"
      " LIMIT 3"
  )
  rows = cursor.fetchall()
  conn.close()

  if not rows:
    return "Memory is currently empty."

  output = ""
  for r in rows:
    output += (
        f"[{r[0]}] Source: {r[1]}\nPrompt: {r[2]}\nResponse: {r[3]}\n---\n"
    )
  return output


# ==========================================
# 3. BACKGROUND AUTOMATION (Scheduler)
# ==========================================
def automated_background_task():
  """Task that runs on a timer independently of user requests."""
  api_key = os.getenv("GEMINI_API_KEY")
  if not api_key:
    return

  print("\n[Scheduler] Running background task: Fetching news summary...")
  try:
    client = genai.Client(api_key=api_key)
    prompt = (
        "Fetch the latest tech news using your tool and give a brief summary."
    )
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            tools=[fetch_tech_news, get_current_time]
        ),
    )
    log_interaction("Automated Scheduler", prompt, response.text)
    print("[Scheduler] Summary created and saved to database!\n")
  except Exception as e:
    print(f"[Scheduler Error] {e}")


scheduler = BackgroundScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
  # Runs on server startup
  init_db()
  # Automatically runs every 30 minutes
  scheduler.add_job(automated_background_task, "interval", minutes=30)
  scheduler.start()
  print("[System] Database ready and Background Scheduler started.")
  yield
  # Runs on server shutdown
  scheduler.shutdown()


# ==========================================
# 4. FASTAPI SERVER & ENDPOINTS
# ==========================================
app = FastAPI(title="Autonomous AI Agent", lifespan=lifespan)


class PromptRequest(BaseModel):
  prompt: str


@app.get("/")
def read_root():
  return {"message": "Autonomous AI Agent server is live!"}


@app.get("/memory")
def view_memory():
  """View all stored logs in the database."""
  conn = sqlite3.connect(DB_FILE)
  cursor = conn.cursor()
  cursor.execute("SELECT * FROM logs ORDER BY id DESC")
  rows = cursor.fetchall()
  conn.close()
  return {"total_logs": len(rows), "logs": rows}


@app.post("/generate")
async def generate_response(request: PromptRequest):
  api_key = os.getenv("GEMINI_API_KEY")
  if not api_key:
    raise HTTPException(status_code=500, detail="GEMINI_API_KEY is missing.")

  if not request.prompt.strip():
    raise HTTPException(status_code=400, detail="Prompt cannot be empty.")

  try:
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=request.prompt,
        config=types.GenerateContentConfig(
            tools=[get_current_time, fetch_tech_news, read_recent_memory]
        ),
    )

    # Save interaction to SQLite database
    log_interaction("User Request", request.prompt, response.text)

    return {
        "status": "success",
        "prompt": request.prompt,
        "response": response.text,
    }
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))