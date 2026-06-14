import os
import re
import hashlib
import urllib.request
from urllib.parse import urlparse
from PIL import Image, ImageDraw, ImageFont

CACHE = "assets/thumbs"

_OG = [
    re.compile(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', re.I),
    re.compile(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']', re.I),
    re.compile(r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)["\']', re.I),
]
_UA = {"User-Agent": "Mozilla/5.0 (AInews bot)"}


def extract_og_image(html: str):
    for pat in _OG:
        m = pat.search(html)
        if m:
            return m.group(1).strip()
    return None


def _fetch(url, timeout=10):
    with urllib.request.urlopen(urllib.request.Request(url, headers=_UA), timeout=timeout) as r:
        return r.read(), r.geturl()


def _resolve_google_news(link, html):
    """Best-effort: turn a news.google.com redirect into the real article URL.
    NOTE: Google News obfuscates these; heuristic, may not always succeed."""
    host = urlparse(link).netloc
    if "news.google" not in host:
        return link
    m = (re.search(r'data-n-au=["\'](https?://[^"\']+)["\']', html)
         or re.search(r'<a[^>]+href=["\'](https?://(?!news\.google)[^"\']+)["\']', html))
    return m.group(1) if m else None


_PALETTE = [(0, 122, 255), (255, 149, 0), (52, 199, 89), (88, 86, 214),
            (255, 45, 85), (175, 82, 222), (255, 59, 48), (10, 132, 255)]


def _initial_tile(source: str) -> str:
    os.makedirs(CACHE, exist_ok=True)
    letter = (source.strip()[:1] or "?").upper()
    color = _PALETTE[abs(hash(source)) % len(_PALETTE)]
    path = os.path.join(CACHE, f"tile_{abs(hash(source)) % 10**8}.png")
    if not os.path.exists(path):
        t = Image.new("RGB", (400, 400), color)
        d = ImageDraw.Draw(t)
        try:
            f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 220)
        except Exception:
            f = ImageFont.load_default()
        bb = d.textbbox((0, 0), letter, font=f)
        d.text(((400 - (bb[2] - bb[0])) / 2 - bb[0], (400 - (bb[3] - bb[1])) / 2 - bb[1]),
               letter, font=f, fill="white")
        t.save(path)
    return path


def _download(img_url) -> str:
    os.makedirs(CACHE, exist_ok=True)
    ext = os.path.splitext(img_url.split("?")[0])[1] or ".jpg"
    path = os.path.join(CACHE, hashlib.md5(img_url.encode()).hexdigest()[:16] + ext)
    if not os.path.exists(path):
        data, _ = _fetch(img_url)
        with open(path, "wb") as f:
            f.write(data)
    return path


def attach_thumbnails(headlines):
    """Fill headline['image'] for every item. Tries the real article og:image;
    always guarantees a tile so no circle is ever empty."""
    for h in headlines:
        if h.get("image") or h.get("icon"):
            continue
        link = h.get("link") or h.get("url")
        try:
            if link:
                raw, final = _fetch(link)
                html = raw.decode("utf-8", "ignore")
                real = _resolve_google_news(final, html)
                if real and real != final:
                    raw, _ = _fetch(real)
                    html = raw.decode("utf-8", "ignore")
                img_url = extract_og_image(html)
                if img_url:
                    h["image"] = _download(img_url)
                    continue
        except Exception:
            pass
        h["image"] = _initial_tile(h.get("source", "AI"))
    return headlines