import os, uuid, feedparser
from fastapi import FastAPI
from pydantic import BaseModel
import google.genai as genai
import database

app = FastAPI()
database.init_db()

try:
    client = genai.Client()
except Exception as e:
    client = None

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
    if not client:
        return {"error": "GEMINI_API_KEY is missing."}
        
    agent = database.get_agent(agentId)
    
    try:
        feed = feedparser.parse("https://hnrss.org/newest?q=AI")
        candidate = feed.entries[0]
        
        prompt = f"You are {agent['name']}, an expert in {agent['domain']}. Write a 1-paragraph exciting post about this news: {candidate.get('title')}. Do not use JSON, just write a normal paragraph."
        
        # FIXED: Using a valid model name!
        response = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
        post_id = f"p-{str(uuid.uuid4())[:8]}"
        
        database.save_post(
            post_id=post_id, 
            agent_id=agentId, 
            text=response.text, 
            rationale="Bypassed rate limits and model errors!", 
            sources=[candidate.get("link")], 
            created_at=database.get_utc_now_iso()
        )
        return {"status": "SUCCESS"}
        
    except Exception as e:
        return {"error": f"Crash details: {str(e)}"}

@app.get("/api/agent/feed")
def get_feed(agentId: str):
    return {"posts": database.get_feed(agentId)}
