\# Autonomous AI Agent with FastAPI \& Gemini



A fully functional autonomous AI agent built with Python, FastAPI, and Google's Gemini 3.6 Flash model. This agent goes beyond simple chat by utilizing \*\*function calling (tools)\*\*, \*\*long-term SQLite memory\*\*, and \*\*automated background scheduling\*\* to execute tasks independently.



\## 🚀 Features



\* \*\*Tool Calling Capabilities:\*\* The agent can dynamically execute Python functions to gather real-time data before responding.

&#x20; \* \*Web Retrieval:\* Fetches live tech news from HackerNews RSS.

&#x20; \* \*Time Awareness:\* Accesses the system clock for real-time context.

&#x20; \* \*Memory Access:\* Reads past interactions from the database.

\* \*\*Automated Background Tasks:\*\* Uses `APScheduler` to run a chron-job every 30 minutes, fetching news, summarizing it, and logging it automatically without user input.

\* \*\*Persistent Memory:\*\* Uses `SQLite3` to log all user interactions and automated tasks, allowing the agent to remember past context.

\* \*\*FastAPI Backend:\*\* Fast, modern API with automatic interactive documentation (Swagger UI).



\## 🛠️ Tech Stack



\* \*\*Language:\*\* Python 3

\* \*\*Framework:\*\* FastAPI, Uvicorn

\* \*\*AI Model:\*\* Google Gemini API (`gemini-3.6-flash`)

\* \*\*Database:\*\* SQLite3

\* \*\*Task Scheduling:\*\* APScheduler



\## ⚙️ Local Setup \& Installation



1\. \*\*Clone the repository\*\*

&#x20;  ```bash

&#x20;  git clone \[https://github.com/hariprasad143nh-maker/autonomous-gemini-agent.git](https://github.com/hariprasad143nh-maker/autonomous-gemini-agent.git)

&#x20;  cd autonomous-gemini-agent

