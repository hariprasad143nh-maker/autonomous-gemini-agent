import os
import uuid
import json
import feedparser
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from apscheduler.schedulers.background import BackgroundScheduler
import google.genai as genai

import database

app = FastAPI(title="Autonomous AI Creator")
database.init_db()

client = genai.Client()

RSS_FEEDS = [
    "https://hnrss.org/newest?q=AI+OR+LLM+OR+Security",
    "https://rss.arxiv.org/rss/cs.CR",
    "https://rss.arxiv.org/rss/cs.AI",
    "https://techcrunch.com/category/artificial-intelligence/feed/"
]

class Persona(BaseModel):
    name: str
    domain: str

class InitRequest(BaseModel):
    persona: Persona

@app.get("/")
def health_check():
    return {"status": "awake and running"}

@app.post("/api/agent/init")
def init_agent(req: InitRequest):
    agent_id = str(uuid.uuid4())
    database.save_agent(agent_id, req.persona.name, req.persona.domain)
    run_autonomous_cycle_for_agent(agent_id, force=True)
    return {"agentId": agent_id}

@app.post("/api/agent/force-run")
def force_run(agentId: str):
    run_autonomous_cycle_for_agent(agentId, force=True)
    return {"status": "cycle completed"}

@app.get("/api/agent/feed")
def get_agent_feed(agentId: str):
    agent = database.get_agent(agentId)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    posts = database.get_feed(agentId)
    return {"posts": posts}

def run_autonomous_cycle_for_agent(agent_id: str, force: bool = False):
    agent = database.get_agent(agent_id)
    if not agent:
        print(f"Agent {agent_id} not found.", flush=True)
        return

    name = agent["name"]
    domain = agent["domain"]

    discovered_items = []
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:5]:
                link = entry.get("link")
                title = entry.get("title")
                summary = entry.get("summary", "")
                
                if link and (force or not database.is_topic_processed(link)):
                    discovered_items.append({
                        "title": title,
                        "summary": summary,
                        "url": link
                    })
        except Exception as e:
            print(f"Error fetching feed {feed_url}: {e}", flush=True)

    if not discovered_items:
        print("No new candidate topics discovered.", flush=True)
        return

    recent_posts, recent_topics = database.get_memory_context(agent_id)
    history_posts_str = "\n---\n".join(recent_posts) if recent_posts else "No previous posts."
    history_topics_str = "\n".join(recent_topics) if recent_topics else "No previous topics logged."

    for candidate in discovered_items:
        prompt = f"""
You are {name}, a premier researcher and expert in {domain}.
You have strict publishing standards. You only publish posts that offer high technical depth, critical safety/security analysis, or fresh industry insights. You intentionally reject shallow fluff or generic news.

Candidate Topic to Evaluate:
Title: {candidate['title']}
Summary: {candidate['summary']}
URL: {candidate['url']}

Memory - Previously Published Posts:
{history_posts_str}

Memory - Recently Processed/Rejected Topics:
{history_topics_str}

Task:
1. Evaluate whether this topic meets your publishing standards and aligns with your domain expertise.
2. Ensure it does not duplicate ideas or themes from previously published posts.

Return ONLY a valid JSON object with:
- "should_publish": true or false
- "rejection_reason": (if false, give a detailed reason why it failed your standards; if true, leave empty)
- "post_text": (if true, write an insightful, engaging 2-3 paragraph post in your unique editorial voice)
- "rationale": (if true, explicitly cover: 1) Why you selected this topic, 2) Why it is relevant right now, 3) Why it was chosen over other candidate topics evaluated)
"""
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config={"response_mime_type": "application/json"}
            )
            
            raw_text = response.text.strip()
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:-3].strip()
            elif raw_text.startswith("```"):
                raw_text = raw_text[3:-3].strip()
                
            result = json.loads(raw_text)
            
            if not result.get("should_publish"):
                reason = result.get("rejection_reason", "Failed editorial standards")
                print(f"Topic Rejected: {candidate['title']} | Reason: {reason}", flush=True)
                database.record_topic(candidate['url'], agent_id, candidate['title'], "REJECTED", reason)
                continue

            post_id = f"p-{str(uuid.uuid4())[:8]}"
            created_at = database.get_utc_now_iso()
            
            database.save_post(
                post_id=post_id,
                agent_id=agent_id,
                text=result["post_text"],
                rationale=result["rationale"],
                sources=[candidate["url"]],
                created_at=created_at
            )
            
            database.record_topic(candidate['url'], agent_id, candidate['title'], "PUBLISHED")
            print(f"Successfully published post: {post_id} for agent: {name}", flush=True)
            break

        except Exception as e:
            print(f"Error evaluating candidate {candidate['title']}: {e}", flush=True)

def global_autonomous_job():
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM agents")
    agents = cursor.fetchall()
    conn.close()
    
    for agent in agents:
        run_autonomous_cycle_for_agent(agent["id"])

scheduler = BackgroundScheduler()
scheduler.add_job(global_autonomous_job, 'interval', minutes=30)
scheduler.start()
