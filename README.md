# Autonomous AI Agent - Vibecodethon

This project is a fully autonomous AI agent that reads the latest AI and tech news, uses editorial judgment to select the best topics, and publishes posts without human intervention. 

## 🚀 Live Demo
**App URL:** https://vibecodethon-agent.onrender.com

## 🛠️ Tech Stack
*   **Backend:** Python, FastAPI
*   **Database:** SQLite
*   **AI Model:** Llama 3.3 (via Groq API)
*   **Automation:** APScheduler (Background tasks) & RSS Feeds

## 🧠 Core Features
*   **Topic Discovery:** Fetches the latest articles from HackerNews RSS.
*   **Memory:** Remembers its last 5 posts to avoid repeating the same news.
*   **Editorial Judgment:** Evaluates topics and actively rejects low-quality or irrelevant news.
*   **Full Autonomy:** Runs on a continuous 4-hour background loop.

## 🧪 How to Test (For Judges)

**1. Initialize the Agent:**
```bash
curl -X POST "[https://vibecodethon-agent.onrender.com/api/agent/init](https://vibecodethon-agent.onrender.com/api/agent/init)" -H "Content-Type: application/json" -d '{"persona": {"name": "Tech AI", "domain": "Artificial Intelligence"}}'