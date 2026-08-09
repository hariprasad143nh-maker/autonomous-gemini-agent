# Vibe-Coding Prompts Log

Here are the core prompts and discussions used to generate, debug, and refine this autonomous AI agent:

### 1. Core API & Database Setup
> "Help me build a FastAPI backend in Python with a SQLite database. I need an `/init` endpoint to create an AI agent based on a persona, and a `/feed` endpoint to return the agent's generated posts."

### 2. Autonomy & Background Loops
> "How do I make the agent run automatically in the background without human interaction? Let's use APScheduler to trigger the post generation every 4 hours."

### 3. Memory & Context (Avoiding Repetition)
> "The AI keeps repeating the same topics. How can I pull the last 5 posts from the SQLite database and feed them into the LLM prompt so it knows what it already wrote about?"

### 4. Editorial Judgment & RSS Parsing
> "The agent needs to demonstrate editorial judgment. Let's pull 5 articles from a tech RSS feed. Write a strict system prompt for the Groq Llama 3 model that forces it to evaluate the articles, pick the best one, provide a rationale, or return 'NONE' if they all lack quality."

### 5. Deployment & Uptime Troubleshooting
> "My Render web service goes to sleep after 15 minutes of inactivity, which kills the background scheduler. How can I set up a pinging service to keep the FastAPI server awake?"
