import json
import os
import feedparser
from openai import OpenAI


def _parse_json(text: str):
    """Strip code fences and parse the model's JSON, tolerating stray prose."""
    t = text.strip().replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        start, end = t.find("{"), t.rfind("}")
        if start != -1 and end != -1:
            return json.loads(t[start:end + 1])
        raise


def _clean_text(text: str) -> str:
    return text.strip().replace("```", "").replace("```json", "").strip()


def _generate_takeaway(client, post: str) -> str:
    if not post or not post.strip():
        return "AI headlines today underline the fast pace of innovation and strategic momentum across the industry."

    prompt = f"""You are the editor of an AI newsletter called AInews.in.

Here is the full LinkedIn post produced earlier:
{post}

Return ONLY one complete paragraph (no markdown, no hashtags, no bullet list).
The takeaway should be a standalone closing insight that summarizes today's AI news in 2 sentences.
It must be distinct from the original post and fully complete on its own.
"""

    response = client.chat.completions.create(
        model="google/gemini-2.5-flash",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300,
    )
    return _clean_text(response.choices[0].message.content)


def fetch_and_generate_post():
    feed = feedparser.parse(
        "https://news.google.com/rss/search?q=artificial+intelligence&hl=en-IN&gl=IN&ceid=IN:en"
    )

    # raw items from the feed (Google News links + source kept for later)
    raw = []
    for entry in feed.entries[:5]:
        raw.append({
            "raw_title": entry.title,
            "link": entry.link,
            "source": getattr(entry, "source", {}).get("title", "Google News"),
            "published": getattr(entry, "published", ""),
        })

    numbered = "\n".join(f"{i}. {r['raw_title']}" for i, r in enumerate(raw, 1))

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"],
    )

    prompt = f"""You are the editor of an AI newsletter called AInews.in.

Today's raw AI headlines (numbered):
{numbered}

Return ONLY valid JSON (no markdown, no commentary) in exactly this shape:
{{
  "post": "<LinkedIn post, max 220 words, strong hook, summary of the key
            developments, a closing takeaway, and 4-5 relevant hashtags>",
  "items": [
    {{"n": 1, "title": "<punchy 4-7 word headline>", "snippet": "<one plain
      sentence, max 14 words, no source name>"}}
  ]
}}

Rules:
- One item per numbered headline above, keep the same "n".
- "title" must be short and readable (NOT the raw title, NOT the source name).
- "snippet" explains the story in plain words.
"""

    response = client.chat.completions.create(
        model="google/gemini-2.5-flash",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1200,
    )
    content = response.choices[0].message.content.strip()

    # ---- merge model output back onto the raw feed items ----
    try:
        data = _parse_json(content)
        post = data["post"].strip()
        by_n = {int(it["n"]): it for it in data.get("items", [])}
    except Exception as e:
        # graceful fallback: keep raw titles, no snippet, post = raw text
        print(f"[content] JSON parse failed ({e}); falling back to raw titles")
        post, by_n = content, {}

    headlines = []
    for i, r in enumerate(raw, 1):
        it = by_n.get(i, {})
        headlines.append({
            "title": it.get("title") or r["raw_title"],
            "snippet": it.get("snippet", ""),
            "link": r["link"],
            "source": r["source"],
            "published": r["published"],
        })

    takeaway = _generate_takeaway(client, post)
    return post, takeaway, headlines