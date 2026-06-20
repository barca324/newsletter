from PIL import Image, ImageDraw, ImageFont
from datetime import date
import os
import re


def _load_system_font(size, bold=False):
    candidates_bold = [
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/ubuntu/Ubuntu-B.ttf",
        "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
    ]
    candidates_reg = [
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf",
        "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
    ]
    candidates = candidates_bold if bold else candidates_reg
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _text_w(draw, text, font):
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0]


def _wrap_full(draw, text, font, max_width):
    words = str(text).split()
    lines, cur = [], ""
    for w in words:
        trial = f"{cur} {w}".strip()
        if not cur or _text_w(draw, trial, font) <= max_width:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def _wrap_clamp(draw, text, font, max_width, max_lines):
    lines = _wrap_full(draw, text, font, max_width)
    if len(lines) <= max_lines:
        return lines
    lines = lines[:max_lines]
    last = lines[-1]
    while last and _text_w(draw, last + "\u2026", font) > max_width:
        last = last[:-1].rstrip()
    lines[-1] = last + "\u2026"
    return lines


def _prepare_logo(max_w=240, max_h=100):
    """Return an RGBA logo with a dark background keyed out, so it sits on white."""
    logo = Image.open("assets/logo.png").convert("RGBA")
    rgb = logo.convert("RGB")
    w0, h0 = rgb.size
    corners = [(2, 2), (w0 - 3, 2), (2, h0 - 3), (w0 - 3, h0 - 3)]
    avg = sum(sum(rgb.getpixel(c)) / 3 for c in corners) / 4
    if avg < 90:  # dark background -> make it transparent
        gray = logo.convert("L")
        mask = gray.point(lambda p: 0 if p < 60 else (255 if p > 105 else int((p - 60) / 45 * 255)))
        logo.putalpha(mask)
    logo.thumbnail((max_w, max_h), Image.LANCZOS)
    return logo


def generate_news_image(headlines, post, takeaway=None):
    WIDTH, HEIGHT = 1080, 1350
    MARGIN = 44
    BG = (255, 255, 255)
    BLUE = (10, 61, 145)
    LBLUE = (245, 247, 251)
    GRAY = (90, 90, 90)
    BLACK = (20, 20, 20)
    HAIR = (224, 224, 224)

    img = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(img)

    f_title    = _load_system_font(78, bold=True)
    f_num      = _load_system_font(24, bold=True)
    f_headline = _load_system_font(38, bold=True)
    f_sub      = _load_system_font(27, bold=False)
    f_date     = _load_system_font(30, bold=False)
    f_tk_title = _load_system_font(30, bold=True)
    f_tk       = _load_system_font(26, bold=False)

    # ── Logo on white (dark background keyed out) ──
    try:
        logo = _prepare_logo()
        img.paste(logo, (MARGIN, 34), logo)
    except Exception:
        draw.text((MARGIN, 55), "AInews.in", font=f_title, fill=BLACK)

    # ── Date ──
    today = date.today().strftime("%B %d, %Y")
    dw = _text_w(draw, today, f_date)
    dx = WIDTH - MARGIN - dw
    draw.line((dx - 30, 40, dx - 30, 120), fill="#CCCCCC", width=2)
    draw.text((dx, 62), today, font=f_date, fill=GRAY)

    # ── Title + rule ──
    draw.text((MARGIN, 150), "DAILY AI BRIEF", font=f_title, fill=BLUE)
    draw.line((MARGIN, 258, WIDTH - MARGIN, 258), fill=BLUE, width=3)

    # ── Reserve the takeaway zone, then flow headlines above it ──
    TK_H = 300
    tk_top = HEIGHT - MARGIN - TK_H
    content_top = 290
    content_bottom = tk_top - 24

    items = (headlines or [])[:5]
    n = max(len(items), 1)
    row_h = (content_bottom - content_top) / n

    badge_w, badge_h = 56, 40
    text_x = MARGIN + badge_w + 26            # badge | text  (no image circle)
    text_max_w = WIDTH - MARGIN - text_x

    for idx, h in enumerate(items, start=1):
        row_top = content_top + (idx - 1) * row_h
        title = h.get("title", "")
        snippet = h.get("snippet", "")

        title_lines = _wrap_clamp(draw, title, f_headline, text_max_w, 2)
        snip_lines = _wrap_clamp(draw, snippet, f_sub, text_max_w, 2) if snippet else []

        th = len(title_lines) * 46 + (len(snip_lines) * 36 if snip_lines else 0)
        block_top = row_top + (row_h - th) / 2
        row_mid = row_top + row_h / 2

        # number badge, vertically centered with the text block
        badge_cy = block_top + 23
        draw.rounded_rectangle(
            (MARGIN, badge_cy - badge_h / 2, MARGIN + badge_w, badge_cy + badge_h / 2),
            radius=9, fill=BLUE,
        )
        nlabel = f"{idx:02d}"
        nw = _text_w(draw, nlabel, f_num)
        draw.text((MARGIN + (badge_w - nw) / 2, badge_cy - 14), nlabel, font=f_num, fill="white")

        # text
        ty = block_top
        for line in title_lines:
            draw.text((text_x, ty), line, font=f_headline, fill=BLACK)
            ty += 46
        for line in snip_lines:
            draw.text((text_x, ty), line, font=f_sub, fill=GRAY)
            ty += 36

        if idx < len(items):
            dy = row_top + row_h
            draw.line((MARGIN, dy, WIDTH - MARGIN, dy), fill=HAIR, width=1)

    # ── Takeaway box ──
    draw.rounded_rectangle(
        (MARGIN, tk_top, WIDTH - MARGIN, HEIGHT - MARGIN), radius=20, fill=LBLUE,
    )
    draw.text((MARGIN + 20, tk_top + 26), "TODAY'S TAKEAWAY", font=f_tk_title, fill=BLUE)

    summary = takeaway or post
    summary = re.sub(r'[^\x00-\x7F]+', ' ', " ".join(str(summary).split("\n")[:6])).strip()
    sy = tk_top + 68
    for line in _wrap_clamp(draw, summary, f_tk, WIDTH - 2 * MARGIN - 40, 6):
        draw.text((MARGIN + 20, sy), line, font=f_tk, fill=BLACK)
        sy += 36

    output_path = "daily_news.png"
    img.save(output_path, quality=95)
    return output_path