#!/usr/bin/env python3
"""render.py — news-image-20261119: deterministic Pillow front page.

Draws a dense newspaper front page summing up Thursday 19 November 2026
from the 27 verified stories in STORY-POOL-19NOV.md (event date = 19 Nov
2026 for every story; see the EXCLUDED table in that file for what was
rejected). 100% Pillow flat illustrations — no photos, no AI images, no
network, no timestamps, no randomness. Output: entry.png, 1024x1024, <1 MiB.
"""
import os
import random
from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
M = 36                      # margin
X0, X1 = M, W - M
CW = X1 - X0                # content width = 952

PAPER = (248, 246, 240)
INK = (17, 17, 17)
GRAY = (68, 68, 68)
RED = (139, 26, 26)
FAINT = (120, 116, 108)

F_SERIF_BLACK = "/usr/share/fonts/truetype/noto/NotoSerifDisplay-Black.ttf"
F_SERIF_B = "/usr/share/fonts/truetype/noto/NotoSerif-Bold.ttf"
F_SERIF = "/usr/share/fonts/truetype/noto/NotoSerif-Regular.ttf"
F_SERIF_I = "/usr/share/fonts/truetype/noto/NotoSerif-Italic.ttf"
F_SANS_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
F_SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

_cache = {}


def font(path, size):
    key = (path, size)
    if key not in _cache:
        _cache[key] = ImageFont.truetype(path, size)
    return _cache[key]


def text_w(draw, s, f):
    return draw.textlength(s, font=f)


def wrap(draw, s, f, width):
    """Greedy word wrap; returns list of lines that fit width."""
    lines, cur = [], ""
    for word in s.split():
        trial = (cur + " " + word).strip()
        if draw.textlength(trial, font=f) <= width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def fit_font(draw, s, path, size, width):
    """Largest size <= `size` whose text fits `width`."""
    while size > 8 and draw.textlength(s, font=font(path, size)) > width:
        size -= 1
    return font(path, size)


def rule(draw, y, x0=X0, x1=X1, w=1, fill=INK):
    draw.rectangle([x0, y, x1, y + w - 1], fill=fill)


def vrule(draw, x, y0, y1, w=1, fill=INK):
    draw.rectangle([x, y0, x + w - 1, y1], fill=fill)


def centered(draw, y, s, f, fill=INK, x0=X0, x1=X1):
    w = draw.textlength(s, font=f)
    draw.text(((x0 + x1 - w) / 2, y), s, font=f, fill=fill)
    return y + f.size


def draw_kicker(draw, x, y, s, size=11):
    f = font(F_SANS_B, size)
    draw.text((x, y), s, font=f, fill=RED)
    return y + size + 3


def draw_headline(draw, x, y, w, s, size=15, max_lines=2, lh=None):
    """Sans-bold headline: wrap at the given size, shrinking only when the
    wrapped lines exceed max_lines."""
    while True:
        f = font(F_SANS_B, size)
        lh = lh or int(size * 1.18)
        lines = wrap(draw, s, f, w)
        if len(lines) <= max_lines or size <= 10:
            break
        size -= 1
    for ln in lines[:max_lines]:
        draw.text((x, y), ln, font=f, fill=INK)
        y += lh
    return y


def draw_body(draw, x, y, w, s, size=12, max_lines=3, lh=None, fill=INK):
    """Serif body, wrapped, capped at max_lines (last line gets an ellipsis
    if text was cut)."""
    lh = lh or int(size * 1.28)
    f = font(F_SERIF, size)
    lines = wrap(draw, s, f, w)
    cut = len(lines) > max_lines
    lines = lines[:max_lines]
    if cut and lines:
        while lines and draw.textlength(lines[-1] + "...", font=f) > w:
            lines[-1] = lines[-1].rsplit(" ", 1)[0]
        lines[-1] += "..."
    for ln in lines:
        draw.text((x, y), ln, font=f, fill=fill)
        y += lh
    return y


# ---------------------------------------------------------------- illustrations
# All flat vector-style drawings. Deterministic: fixed coordinates, seeded
# pseudo-random only where noted (seed 19).

def _gradient(img, top, bottom):
    w, h = img.size
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / max(h - 1, 1)
        c = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
        d.line([(0, y), (w, y)], fill=c)


def _flag_us(d, x, y, w, h):
    stripe = max(1, h // 13)
    for i in range(13):
        c = (178, 34, 52) if i % 2 == 0 else (240, 240, 235)
        d.rectangle([x, y + i * stripe, x + w, y + (i + 1) * stripe], fill=c)
    cw, ch = int(w * 0.4), stripe * 7
    d.rectangle([x, y, x + cw, y + ch], fill=(30, 40, 90))
    for r in range(4):
        for c_ in range(5):
            sx = x + 4 + c_ * (cw - 8) // 4
            sy = y + 3 + r * (ch - 6) // 3
            d.ellipse([sx, sy, sx + 2, sy + 2], fill=(240, 240, 235))


def _flag_cn(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(222, 41, 16))
    d.ellipse([x + 3, y + 3, x + 9, y + 9], fill=(255, 222, 0))
    for sx, sy in [(x + w - 9, y + 3), (x + w - 6, y + 8),
                   (x + w - 9, y + 12), (x + w - 5, y + 13)]:
        d.ellipse([sx, sy, sx + 3, sy + 3], fill=(255, 222, 0))


def _flag_ru(d, x, y, w, h):
    for i, c in enumerate([(240, 240, 235), (0, 57, 166), (213, 0, 50)]):
        d.rectangle([x, y + i * h // 3, x + w, y + (i + 1) * h // 3], fill=c)


def hero_shenzhen(w, h):
    """Three flags on stage in Shenzhen, skyline behind. Story #1."""
    img = Image.new("RGB", (w, h), (24, 32, 54))
    _gradient(img, (38, 52, 84), (16, 22, 40))
    d = ImageDraw.Draw(img)
    rng = random.Random(19)
    floor = max(8, h // 4)         # stage floor height
    base = h - floor
    # skyline silhouettes with lit windows
    x = 0
    while x < w:
        bw = rng.randint(28, 64)
        bh = rng.randint(max(6, h // 4), max(7, base - 6))
        d.rectangle([x, base - bh, x + bw, base], fill=(10, 14, 26))
        for wy in range(base - bh + 3, base - 3, 7):
            for wx in range(x + 3, x + bw - 2, 7):
                if rng.random() < 0.35:
                    d.rectangle([wx, wy, wx + 2, wy + 3], fill=(255, 196, 90))
        x += bw + rng.randint(2, 10)
    # stage floor
    d.rectangle([0, base, w, h], fill=(52, 44, 36))
    d.rectangle([0, base, w, base + 2], fill=(255, 196, 90))
    # three flag poles, centred
    fh = max(16, h - floor - 12)
    fw = int(fh * 1.6)
    gap = 26
    total = 3 * fw + 2 * gap
    x0 = (w - total) // 2
    for i, fn in enumerate((_flag_us, _flag_cn, _flag_ru)):
        fx = x0 + i * (fw + gap)
        d.rectangle([fx - 2, 4, fx, base], fill=(200, 190, 170))
        d.ellipse([fx - 4, 2, fx + 2, 8], fill=(255, 222, 0))
        fn(d, fx, 6, fw, fh)
    return img


def gta_vice(w, h):
    """Neon Vice City dusk: pink sky, sun, art-deco towers, palms. #3."""
    img = Image.new("RGB", (w, h))
    _gradient(img, (255, 120, 160), (90, 40, 130))
    d = ImageDraw.Draw(img)
    sun = max(18, h - 8)
    d.ellipse([w - sun - 10, 2, w - 10, 2 + sun], fill=(255, 214, 130))
    rng = random.Random(19)
    # towers with neon edges
    neons = [(0, 255, 255), (255, 80, 200), (120, 255, 200)]
    x = 0
    i = 0
    while x < w:
        bw = rng.randint(30, 58)
        bh = rng.randint(max(8, h // 3), max(9, h - 6))
        d.rectangle([x, h - bh, x + bw, h], fill=(28, 12, 44))
        nc = neons[i % 3]
        d.line([(x, h - bh), (x + bw, h - bh)], fill=nc, width=2)
        d.line([(x, h - bh), (x, h)], fill=nc, width=1)
        for wy in range(h - bh + 4, h - 3, 7):
            for wx in range(x + 4, x + bw - 3, 8):
                if rng.random() < 0.4:
                    d.rectangle([wx, wy, wx + 2, wy + 3], fill=(255, 220, 120))
        x += bw + 2
        i += 1
    # palms
    for px in (w // 4, 3 * w // 4):
        top = h - max(12, h // 2)
        d.line([(px, h), (px - 3, top)], fill=(16, 8, 26), width=3)
        d.arc([px - 16, top - 8, px + 16, h - 6], start=200, end=340,
              fill=(16, 8, 26), width=2)
    return img


def voyager(w, h):
    """Voyager 1 in deep space: starfield, gold dish, Earth dot. #4."""
    img = Image.new("RGB", (w, h), (4, 6, 14))
    d = ImageDraw.Draw(img)
    rng = random.Random(19)
    for _ in range(90):
        sx, sy = rng.randint(0, w - 1), rng.randint(0, h - 1)
        s = rng.choice([1, 1, 2])
        d.ellipse([sx, sy, sx + s, sy + s], fill=(220, 225, 255))
    # Earth dot
    d.ellipse([16, h - 12, 23, h - 5], fill=(80, 140, 255))
    d.ellipse([18, h - 11, 21, h - 8], fill=(160, 220, 160))
    # probe: bus + dish + boom
    cx, cy = w // 2 + 60, h // 2
    ry = max(9, h // 2 - 4)
    rx = 24
    d.line([(cx - 90, cy + 10), (cx + 40, cy - 4)], fill=(200, 170, 90),
           width=3)
    d.rectangle([cx - 12, cy - 6, cx + 12, cy + 8], fill=(210, 180, 100))
    d.ellipse([cx + 12, cy - ry, cx + 12 + rx, cy + ry],
              outline=(240, 210, 130), width=3)
    import math
    for t in range(0, 181, 30):
        a = math.radians(t)
        d.line([(cx + 12 + rx // 2, cy),
                (cx + 12 + rx // 2 + int(rx * 0.9 * math.cos(a)),
                 cy + int(ry * 0.9 * math.sin(a)))], fill=(240, 210, 130))
    d.ellipse([cx + 12 + rx // 2 - 3, cy - 3, cx + 12 + rx // 2 + 3, cy + 3],
              fill=(240, 210, 130))
    return img


def berlin(w, h):
    """Brandenburg Gate silhouette + five allied flags. #8."""
    img = Image.new("RGB", (w, h), (214, 226, 238))
    d = ImageDraw.Draw(img)
    d.rectangle([0, h - 6, w, h], fill=(150, 160, 150))
    # gate
    gh = max(16, h - 14)
    gx, gw = w // 2 - 90, 180
    top = h - 6 - gh
    d.rectangle([gx, top, gx + gw, top + 5], fill=(90, 92, 96))
    for i in range(6):
        cx = gx + 8 + i * 30
        d.rectangle([cx, top + 5, cx + 10, h - 6], fill=(90, 92, 96))
    d.rectangle([gx - 6, top - 3, gx + gw + 6, top], fill=(90, 92, 96))
    d.ellipse([gx + gw // 2 - 4, top - 9, gx + gw // 2 + 4, top - 1],
              fill=(90, 92, 96))
    # five small flags bottom-left, above the ground band
    flags = [[(0, 0, 0), (221, 0, 0), (255, 206, 0)],
             [(0, 85, 164), (255, 255, 255), (239, 65, 53)],
             [(0, 36, 125), (255, 255, 255), (207, 20, 43)],
             [(255, 255, 255), (220, 20, 60)],
             [(0, 146, 70), (255, 255, 255), (206, 43, 55)]]
    fx = 10
    for fl in flags:
        for j, c in enumerate(fl):
            d.rectangle([fx, h - 14 + j * 2, fx + 16, h - 14 + (j + 1) * 2],
                        fill=c)
        fx += 22
    return img


def drones(w, h):
    """Three long-range drones over a map field, dotted flight paths. #9."""
    img = Image.new("RGB", (w, h), (232, 236, 228))
    d = ImageDraw.Draw(img)
    d.rectangle([0, h - 5, w, h], fill=(170, 185, 150))
    for tx in (30, 120, 300, 420):
        d.ellipse([tx, h - 11, tx + 7, h - 5], fill=(110, 140, 90))
    # dotted paths
    for (x0, y0, x1, y1) in [(20, 8, 180, 20), (140, 6, 320, 15),
                             (260, 10, 440, 24)]:
        steps = 24
        for i in range(steps + 1):
            px = x0 + (x1 - x0) * i // steps
            py = y0 + (y1 - y0) * i // steps
            d.ellipse([px, py, px + 2, py + 2], fill=(139, 26, 26))
    # quadcopter silhouettes
    for (cx, cy, s) in [(90, 18, 9), (240, 14, 11), (390, 21, 8)]:
        d.rectangle([cx - s, cy - 3, cx + s, cy + 3], fill=(40, 44, 52))
        d.rectangle([cx - 3, cy - s, cx + 3, cy + s], fill=(40, 44, 52))
        for (rx, ry) in [(-s, -s), (s, -s), (-s, s), (s, s)]:
            d.ellipse([cx + rx - 5, cy + ry - 2, cx + rx + 5, cy + ry + 2],
                      outline=(40, 44, 52), width=1)
    return img


def mini_bars(d, x, y, w, h, vals=(8, 14, 20, 26), color=RED):
    """Tiny rising bar chart (Anthropic debut)."""
    bw = w // len(vals)
    mx = max(vals)
    for i, v in enumerate(vals):
        bh = max(2, int(h * v / mx))
        d.rectangle([x + i * bw + 1, y + h - bh, x + (i + 1) * bw - 1, y + h],
                    fill=color)


def mini_spark(d, x, y, w, h, pts=(0.2, 0.5, 0.35, 0.7, 0.55, 0.85),
               color=RED):
    """Tiny sparkline (Asia markets)."""
    n = len(pts)
    xy = []
    for i, p in enumerate(pts):
        xy.append((x + i * w // (n - 1), y + h - int(h * p)))
    d.line(xy, fill=color, width=2)


# ------------------------------------------------------------------- content
# All 27 verified stories from STORY-POOL-19NOV.md. No outcome is claimed
# for events whose result was not yet known at print time (ICJ, summit,
# COP31 deal, Spain debate, McDavid game). #27 carries a Shenzhen dateline
# only — its interview was given Thu 19 Nov in Shenzhen (Wed 18 Nov US).

LEAD_HEADLINE = ["TRUMP, XI AND PUTIN", "MEET IN SHENZHEN"]
LEAD_STANDFIRST = ("The three leaders hold the first trilateral talks in "
                    "Shenzhen — nuclear arms and the Iran war on the agenda. "
                    "No deal expected.")
HERO_CAPTION = ("The flags of the United States, China and Russia on stage "
                "in Shenzhen.")

PHOTO_A = [
    dict(kicker="GAMES", headline="WELCOME BACK TO VICE CITY", illu=gta_vice,
         body="Grand Theft Auto VI began its global rollout at midnight on "
              "Thursday, starting in New Zealand — the most anticipated "
              "launch in gaming history."),
    dict(kicker="SPACE", headline="VOYAGER 1 REACHES ONE LIGHT-DAY",
         illu=voyager,
         body="NASA confirms on Thursday that Voyager 1 is one light-day "
              "from Earth — 16.1 billion miles out — after nearly 50 years "
              "in space."),
]

TEXT_B = [
    dict(kicker="MARKETS", headline="ANTHROPIC DEBUTS AT $83", chart="bars",
         body="Claude-maker Anthropic begins trading on Nasdaq as ANT on "
              "Thursday after pricing its IPO at $83 — $81.3bn raised, the "
              "largest offering on record."),
    dict(kicker="THE HAGUE", headline="WORLD COURT RULES ON MYANMAR",
         body="The ICJ delivers its judgment in The Gambia v. Myanmar — "
              "whether Myanmar committed genocide against the Rohingya — in "
              "The Hague."),
    dict(kicker="CLIMATE", headline="COP31 ENTERS FINAL HOURS",
         body="COP31 in Antalya reaches its penultimate day with 21 issues "
              "unresolved; new draft texts on finance and adaptation are "
              "due early Thursday."),
]

PHOTO_C = [
    dict(kicker="EUROPE",
         headline="COALITION OF THE WILLING MEETS IN BERLIN", illu=berlin,
         body="Leaders of Germany, France, Britain, Poland and Italy, with "
              "NATO's Rutte, meet in Berlin on security guarantees for "
              "Kyiv after a ceasefire."),
    dict(kicker="DEFENCE", headline="UK GIVES UKRAINE 1,000+ DRONES",
         illu=drones,
         body="PM Burnham announces a £260m package in Berlin: more than "
              "1,000 long-range strike drones, plus maritime, logistics "
              "and surveillance drones."),
]

TEXT_D = [
    dict(kicker="WAR", headline="UKRAINE HITS CRIMEAN BRIDGE AGAIN",
         body="A third attack on the Crimean Bridge this week: traffic is "
              "suspended after an early-Thursday strike."),
    dict(kicker="CHILDREN", headline="1 IN 4 CHILDREN IN CONFLICT ZONES",
         body="A record 589 million children lived in conflict zones in "
              "2025, the most since 1990, Save the Children reports."),
    dict(kicker="THE GULF", headline="HOUTHI MISSILE AT RIYADH",
         body="The Saudi-led coalition says it dealt with a Houthi missile "
              "threat towards Riyadh after a loud blast in the capital."),
    dict(kicker="ECONOMY", headline="AUSTRALIA JOBLESS RATE HITS 4.9%",
         body="Unemployment jumps to 4.9% in October, a five-year high, "
              "with employment down 43,500 and youth joblessness at 11.3%."),
]

TEXT_E = [
    dict(kicker="SOUTH ASIA", headline="BANGLADESH UNDER LOCKDOWN",
         body="The banned Awami League's lockdown day: troops hold the "
              "streets and 565 are arrested in Dhaka in 24 hours."),
    dict(kicker="ASIA", headline="INDIA, JAPAN HOLD 2+2 IN TOKYO",
         body="Rajnath Singh and Jaishankar meet Japan's Koizumi and Motegi "
              "for the fourth India–Japan 2+2 dialogue."),
    dict(kicker="MARKETS", headline="ASIA MARKETS: OIL HOLDS, BITCOIN SLIPS",
         chart="spark",
         body="Brent holds near $92 as Gulf attacks mount; gold futures "
              "slip near $3,730 and bitcoin falls about 1% to near $63,700."),
    dict(kicker="SHENZHEN", headline="TRUMP: IRAN EYES CHEM-BIO WEAPONS",
         body="Trump, in Shenzhen on Thursday, says Iran is 'looking at "
              "gases, looking at bio' after US strikes shut its nuclear "
              "path."),
]

BRIEFS = [
    ("HOCKEY", "Women's Asian Champions Trophy opens in Bhopal; champions "
               "India face Malaysia."),
    ("SPAIN", "Sánchez v Feijóo: the only TV debate, 22:00 in Madrid, 10 "
              "days before the vote."),
    ("LIBERIA", "Liberia opens a two-day maritime safety dialogue in "
                "Marshall; Boakai keynotes."),
    ("FICCI", "Modi opens FICCI's centenary meeting in New Delhi; theme "
             "'Bharat 2047'."),
    ("NIA", "Shah opens the NIA anti-terror conference in New Delhi on "
          "cross-border terror."),
    ("NHL", "McDavid goes for a 24th straight game with a point in Tampa "
           "Bay tonight."),
    ("KOREA", "550,000 sit the Suneung exam under AI-cheating curbs; 22 "
              "phones found first."),
    ("TENNIS", "Ash Barty is elected to the International Tennis Hall of "
               "Fame, class of 2027."),
    ("TONGA", "Tonga declares a state of emergency as the El Niño drought "
             "bites."),
    ("SCIENCE", "Two Alzheimer's studies land: a protein atlas, and "
               "hibernating-hamster clues."),
    ("CRICKET", "India win the toss and bowl in Wellington as Bumrah "
                "returns to Test cricket."),
    ("THE DAY", "27 stories, one day — every event dated Thursday, "
               "November 19, 2026."),
]

# --------------------------------------------------------------------- layout
HERO_H = 44
PHOTO_H = 32
GAP = 20


def photo_row(draw, y, stories, img):
    """Two photo panels side by side. Returns y after the row + rule."""
    cw = (CW - GAP) // 2
    row_h = 0
    for i, st in enumerate(stories):
        x = X0 + i * (cw + GAP)
        illu = st["illu"](cw, PHOTO_H)
        img.paste(illu, (x, y))
        yy = y + PHOTO_H + 4
        yy = draw_kicker(draw, x, yy, st["kicker"])
        yy = draw_headline(draw, x, yy, cw, st["headline"], size=16,
                           max_lines=2, lh=19)
        yy = draw_body(draw, x, yy + 1, cw, st["body"], size=12,
                       max_lines=2, lh=15)
        row_h = max(row_h, yy - y)
    y += row_h + 5
    rule(draw, y)
    return y + 6


def text_row(draw, y, stories, body_lines=3, body_size=12):
    """N text columns. Returns y after the row + rule."""
    n = len(stories)
    cw = (CW - GAP * (n - 1)) // n
    row_h = 0
    for i, st in enumerate(stories):
        x = X0 + i * (cw + GAP)
        yy = draw_kicker(draw, x, y, st["kicker"])
        if st.get("chart") == "bars":
            mini_bars(draw, x + cw - 62, y - 1, 60, 12)
        elif st.get("chart") == "spark":
            mini_spark(draw, x + cw - 62, y - 1, 60, 12)
        yy = draw_headline(draw, x, yy, cw, st["headline"], size=14,
                           max_lines=2, lh=17)
        yy = draw_body(draw, x, yy + 1, cw, st["body"], size=body_size,
                       max_lines=body_lines,
                       lh=int(body_size * 1.15))
        row_h = max(row_h, yy - y)
        if i < n - 1:
            vrule(draw, x + cw + GAP // 2, y + 2, yy - 2)
    y += row_h + 5
    rule(draw, y)
    return y + 6


def briefs_grid(draw, y, items):
    """'AROUND THE WORLD' — 3 rows x 4 columns of one-line briefs."""
    f = font(F_SANS_B, 13)
    draw.text((X0, y), "AROUND THE WORLD", font=f, fill=INK)
    y += 18
    rule(draw, y)
    y += 5
    ncols = 4
    cw = (CW - GAP * (ncols - 1)) // ncols
    for r in range(3):
        row_top = y
        row_h = 0
        for c in range(ncols):
            label, text = items[r * ncols + c]
            x = X0 + c * (cw + GAP)
            yy = draw_kicker(draw, x, row_top, label, size=10)
            yy = draw_body(draw, x, yy, cw, text, size=11, max_lines=2,
                           lh=12)
            row_h = max(row_h, yy - row_top)
        y += row_h + 5
    return y


def build():
    img = Image.new("RGB", (W, H), PAPER)
    draw = ImageDraw.Draw(img)
    y = 22
    # top bar
    f_top = font(F_SERIF_B, 13)
    draw.text((X0, y), "NEWS PAPER EDITION", font=f_top, fill=INK)
    s = "NEWS PAPER EDITION"
    draw.text((X1 - draw.textlength(s, font=f_top), y), s, font=f_top,
              fill=INK)
    cx = (X0 + X1) // 2
    draw.polygon([(cx, y + 2), (cx + 5, y + 7), (cx, y + 12), (cx - 5, y + 7)],
                 fill=INK)
    y += 18
    rule(draw, y)
    y += 3
    rule(draw, y, w=3)
    y += 7
    # masthead
    f_mast = fit_font(draw, "WORLD'S NEWS", F_SERIF_BLACK, 74, CW)
    draw.text((X0, y), "WORLD'S NEWS", font=f_mast, fill=INK)
    y += f_mast.size + 2
    rule(draw, y, w=3)
    y += 5
    rule(draw, y)
    y += 4
    # dateline row
    f_date = font(F_SERIF_B, 14)
    draw.text((X0, y), "EST 2000", font=f_date, fill=INK)
    s = "THURSDAY, NOVEMBER 19, 2026"
    draw.text((X1 - draw.textlength(s, font=f_date), y), s, font=f_date,
              fill=INK)
    f_pub = font(F_SERIF_I, 14)
    centered(draw, y, "THYNK UNLIMITED", f_pub, fill=INK)
    y += 18
    rule(draw, y)
    y += 5
    # kicker
    kick = " ".join(list("SUMMING UP 19 NOVEMBER'S WORLD NEWS"))
    f_kick = fit_font(draw, kick, F_SANS_B, 15, CW)
    centered(draw, y, kick, f_kick, fill=INK)
    y += 18
    # lead headline (2 lines)
    f_lead = font(F_SANS_B, 35)
    for ln in LEAD_HEADLINE:
        centered(draw, y, ln, f_lead, fill=INK)
        y += 40
    y += 2
    # standfirst
    f_sf = font(F_SERIF_I, 14)
    for ln in wrap(draw, LEAD_STANDFIRST, f_sf, CW):
        centered(draw, y, ln, f_sf, fill=GRAY)
        y += 18
    y += 4
    rule(draw, y)
    y += 5
    # hero panel + caption
    img.paste(hero_shenzhen(CW, HERO_H), (X0, y))
    y += HERO_H + 4
    f_cap = font(F_SERIF_I, 13)
    centered(draw, y, HERO_CAPTION, f_cap, fill=GRAY)
    y += 15
    rule(draw, y)
    y += 6
    # story rows: 2 + 3 + 2 + 4 + 4 = 15 stories + 1 lead + 11 briefs = 27
    y = photo_row(draw, y, PHOTO_A, img)
    y = text_row(draw, y, TEXT_B, body_lines=3, body_size=12)
    y = photo_row(draw, y, PHOTO_C, img)
    y = text_row(draw, y, TEXT_D, body_lines=3, body_size=11)
    y = text_row(draw, y, TEXT_E, body_lines=3, body_size=11)
    y = briefs_grid(draw, y, BRIEFS)
    rule(draw, y, w=3)
    print("final y:", y, "| bottom margin:", H - y)
    return img


def main():
    out = os.environ.get("RENDER_OUT", "entry.png")
    img = build()
    img.save(out, "PNG", optimize=True)
    print("wrote", out, os.path.getsize(out), "bytes")


if __name__ == "__main__":
    main()
