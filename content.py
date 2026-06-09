import json
import feedparser
from openai import OpenAI
import os


def fetch_and_generate_post():
    # Fetch AI news
    feed = feedparser.parse(
        "https://news.google.com/rss/search?q=artificial+intelligence&hl=en-IN&gl=IN&ceid=IN:en"
    )

    headlines = []

    for entry in feed.entries[:5]:
        headlines.append({
            "title": entry.title,
            "link": entry.link,
            "source": getattr(entry, "source", {}).get("title", "Google News"),
            "published": entry.published
        })

    news_text = "\n".join(
        [f"- {h['title']}" for h in headlines]
    )

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"]
    )

    prompt = f"""
You are writing a LinkedIn AI newsletter.

Today's AI headlines:

{news_text}

Write a LinkedIn post:
- Max 220 words
- Strong hook
- Summarize the most important developments
- End with a takeaway
- Include 4-5 relevant hashtags

Return ONLY the post text.
"""

    response = client.chat.completions.create(
        model="google/gemini-2.5-flash",
        messages=[
            {"role": "user", "content": prompt}
        ],
        max_tokens=1000
    )

    post = response.choices[0].message.content.strip()

    return post, headlines