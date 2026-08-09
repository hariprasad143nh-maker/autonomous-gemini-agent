import os, uuid, feedparser
from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI
import database

app = FastAPI()
database.init_db()

# Initialize Groq client using OpenAI-compatible SDK
client = OpenAI(
    api_key=os.environ.get("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

class Persona(BaseModel):
    name: str
    domain: str

class InitRequest(BaseModel):
    persona: Persona

@app.get("/")
def root(): 
    return {"status": "awake and running"}

@app.post("/api/agent/init")
def init_agent(req: InitRequest):
    agent_id = str(uuid.uuid4())
    database.save_agent(agent_id, req.persona.name, req.persona.domain)
    return {"agentId": agent_id}

@app.post("/api/agent/force-run")
def force_run(agentId: str):
    agent = database.get_agent(agentId)
    if not agent:
        return {"error": "Agent not found."}
    
    try:
        feed = feedparser.parse("https://hnrss.org/newest?q=AI")
        candidate = feed.entries[0]
        
        prompt = f"You are {agent['name']}, an expert in {agent['domain']}. Write a 1-paragraph exciting post about this news: {candidate.get('title')}."
        
        # Call Groq's high-speed Llama 3 model
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}]
        )
        post_text = response.choices[0].message.content
        
        post_id = f"p-{str(uuid.uuid4())[:8]}"
        database.save_post(
            post_id=post_id, 
            agent_id=agentId, 
            text=post_text, 
            rationale="Generated via Groq free tier!", 
            sources=[candidate.get("link")], 
            created_at=database.get_utc_now_iso()
        )
        return {"status": "SUCCESS"}
        
    except Exception as e:
        return {"error": f"Crash details: {str(e)}"}

@app.get("/api/agent/feed")
def get_feed(agentId: str):
    return {"posts": database.get_feed(agentId)}