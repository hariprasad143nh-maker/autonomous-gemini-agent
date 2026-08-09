def generate_autonomous_post(agent_id, name, domain):
    try:
        # 1. Discover Topics (Pull the top 5 recent articles, not just 1)
        feed = feedparser.parse("https://hnrss.org/newest?q=AI")
        candidates = feed.entries[:5]
        articles_text = "\n".join([f"- {c.get('title')} (Link: {c.get('link')})" for c in candidates])
        
        # 2. Memory Check (Get previous posts to avoid repetition)
        recent_posts = database.get_feed(agent_id)[:5]
        memory_text = "\n".join([f"- {p['text']}" for p in recent_posts]) if recent_posts else "No previous posts."

        # 3. Editorial Judgment & Rationale
        prompt = f"""
        You are {name}, an expert in {domain}. 
        
        Here is what you recently published (DO NOT repeat these topics):
        {memory_text}
        
        Here are the latest news topics:
        {articles_text}
        
        Task:
        1. Evaluate these topics. Reject any that are low quality, irrelevant to {domain}, or too similar to your previous posts.
        2. Pick the SINGLE best topic to publish. If NONE meet your standards, return "NONE" in the text field.
        
        Respond ONLY in valid JSON format with three keys:
        "text": "A 1-paragraph exciting post about the chosen news in your voice. (Or type 'NONE' if you reject them all)",
        "rationale": "Explain why you selected this topic over the others, why it's relevant now, and how you used your editorial judgment to reject the rest.",
        "source": "The exact link of the chosen article"
        """
        
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        content = json.loads(response.choices[0].message.content)
        
        # 4. Enforce Editorial Standards
        if content.get("text") == "NONE" or not content.get("source"):
            print(f"[{name}] Agent demonstrated editorial judgment and rejected all current topics.")
            return # Skip publishing and wait for the next cycle!

        # 5. Publish to Memory
        post_id = f"p-{str(uuid.uuid4())[:8]}"
        database.save_post(
            post_id=post_id, 
            agent_id=agent_id, 
            text=content["text"], 
            rationale=content["rationale"], 
            sources=[content["source"]], 
            created_at=database.get_utc_now_iso()
        )
        print(f"[{name}] Successfully published a new post autonomously!")
        
    except Exception as e:
        print(f"Agent {agent_id} failed to post: {str(e)}")