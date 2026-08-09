import os, uuid, feedparser, json, asyncio
from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI
import database
from apscheduler.schedulers.background import BackgroundScheduler

app = FastAPI()
database.init_db()

client = OpenAI(
    api_key=os.environ.get("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

class Persona(BaseModel):
    name: str
    domain: str

class InitRequest(BaseModel):
    persona: Persona

# --- THE AUTONOMOUS BRAIN ---
def generate_autonomous_post(agent_id, name, domain):
    try:
        # 1. Discover Topics
        feed = feedparser.parse("https://hnrss.org/newest?q=AI")
        candidate = feed.entries[0] # Grabbing the top AI news
        
        # 2. Editorial Judgment & Rationale
        prompt = f"""
        You are {name}, an expert in {domain}. 
        Evaluate this news: {candidate.get('title')}
        
        Respond ONLY in valid JSON format with two keys:
        "text": "A 1-paragraph exciting post about this news written in your persona's voice."
        "rationale": "Explain why you selected this topic, why it is relevant now, and how it fits your {domain} domain."
        """
        
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        content = json.loads(response.choices[0].message.content)
        
        # 3. Publish to Memory
        post_id = f"p-{str(uuid.uuid4())[:8]}"
        database.save_post(
            post_id=post_id, 
            agent_id=agent_id, 
            text=content["text"], 
            rationale=content["rationale"], 
            sources=[candidate.get("link")], 
            created_at=database.get_utc_now_iso()
        )
        print(f"[{name}] Successfully published a new post autonomously!")
    except Exception as e:
        print(f"Agent {agent_id} failed to post: {str(e)}")

# This runs every 4 hours in the background
def background_loop():
    agents = database.get_all_agents() # Assuming your DB has this, if not, we can adjust!
    for agent in agents:
        generate_autonomous_post(agent["id"], agent["name"], agent["domain"])

# Start the background timer when the app boots
scheduler = BackgroundScheduler()
scheduler.add_job(background_loop, 'interval', hours=4)
scheduler.start()

# --- API ENDPOINTS ---

@app.post("/api/agent/init")
def init_agent(req: InitRequest):
    agent_id = str(uuid.uuid4())
    database.save_agent(agent_id, req.persona.name, req.persona.domain)
    
    # Force a first post immediately upon initialization so the feed isn't empty
    generate_autonomous_post(agent_id, req.persona.name, req.persona.domain)
    
    return {"agentId": agent_id}

@app.get("/api/agent/feed")
def get_feed(agentId: str):
    return {"posts": database.get_feed(agentId)}

@app.post("/api/agent/force-run")
def force_run(agentId: str):
    # Kept just for testing!
    agent = database.get_agent(agentId)
    generate_autonomous_post(agentId, agent["name"], agent["domain"])
    return {"status": "SUCCESS"}