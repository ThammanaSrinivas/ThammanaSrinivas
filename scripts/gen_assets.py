"""Generate profile README SVGs in the ZenMode v3 style (text outlined to paths, no web fonts).

Usage: python3 scripts/gen_assets.py assets  (set ZENMODE_FONTS to the zenmode app res/font dir)
"""
import os, sys
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

FONTS = os.environ.get("ZENMODE_FONTS", os.path.expanduser("~/Srinivas/github/zenmode/zenmode/app/src/main/res/font/"))
OUT = sys.argv[1]
CLASH, GEIST, MONO = "clash_display_medium.otf", "geist_variable.ttf", "departure_mono_regular.otf"
BRAND = "#0F7A18"
_cache = {}


def font(name):
    if name not in _cache:
        f = TTFont(FONTS + name)
        _cache[name] = (f, f.getGlyphSet(), f.getBestCmap(), f["head"].unitsPerEm)
    return _cache[name]


def measure(s, ff, size, tracking=0.0):
    f, _, cmap, upm = font(ff)
    return sum(f["hmtx"][cmap[ord(c)]][0] for c in s) * size / upm + tracking * size * max(len(s) - 1, 0)


def text(s, ff, size, x, y, fill, tracking=0.0, anchor="start", opacity=None):
    f, gs, cmap, upm = font(ff)
    scale = size / upm
    w = measure(s, ff, size, tracking)
    x -= {"start": 0, "middle": w / 2, "end": w}[anchor]
    pen = SVGPathPen(gs)
    for c in s:
        g = cmap[ord(c)]
        gs[g].draw(TransformPen(pen, (scale, 0, 0, -scale, x, y)))
        x += f["hmtx"][g][0] * scale + tracking * size
    op = f' opacity="{opacity}"' if opacity is not None else ""
    return f'<path fill="{fill}"{op} d="{pen.getCommands()}"/>'


MARK_POLYS = ["214,214 416,214 214,416", "810,810 607,810 810,607",
              "600.6,216 810,216 810,423.4 423.4,810 214,810 214,602.6"]


def glyph(fg, hole=None):
    """ZenMode mark shapes on a 1024 grid (traced from app_icon.png)."""
    s = "".join(f'<polygon points="{p}" fill="{fg}" stroke="{fg}" stroke-width="80" stroke-linejoin="round"/>'
                for p in MARK_POLYS)
    if hole:
        s += f'<circle cx="510" cy="510" r="40" fill="{hole}"/>'
    return s


def mark(x, y, size):
    return (f'<g transform="translate({x} {y}) scale({size / 1024})">'
            f'<rect width="1024" height="1024" rx="230" fill="{BRAND}"/>{glyph("#FFFFFF", BRAND)}</g>')


THEMES = {
    "light": dict(bg="#FAF9F5", card="#FFFFFF", sunk="#F2F1ED", line="#DBD9D2", ink="#111111",
                  muted="#666861", accent="#0F7A18", tint="#E6F6E7", tintline="#C8E7CA",
                  wash="#2AA136", washop="0.22", amber="#7A5A00", amberfill="#FFC800", amberbg="#FFF8E1"),
    "dark": dict(bg="#111111", card="#1A1A1A", sunk="#161616", line="#2B2B2B", ink="#F5F5F1",
                 muted="#9E9E98", accent="#5BDF62", tint="#16210F", tintline="#23391F",
                 wash="#2AA136", washop="0.30", amber="#FFC800", amberfill="#FFC800", amberbg="#2A2410"),
}


def svg(W, H, title, parts, defs=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img">'
            f"<title>{title}</title><defs>{defs}</defs>" + "".join(parts) + "</svg>")


def pill(x, y, label, t, fill, stroke, color, dot=None):
    w = measure(label, MONO, 15, 0.08) + 32 + (18 if dot else 0)
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="34" rx="17" fill="{fill}" stroke="{stroke}"/>']
    tx = x + 16
    if dot:
        out.append(f'<circle cx="{tx + 4}" cy="{y + 17}" r="4" fill="{dot}"/>')
        tx += 18
    out.append(text(label, MONO, 15, tx, y + 22, color, 0.08))
    return out, w


# ---------------------------------------------------------------- banner
def banner():
    """Brand-green banner, identical in light and dark: the one loud block at the top of the page,
    matching the portfolio hero (srinivas-t.web.app). Everything below stays on paper/ink."""
    W, H = 1280, 440
    white = "#FFFFFF"
    defs = (
        f'<radialGradient id="wash" cx="0.9" cy="0" r="1.1">'
        f'<stop offset="0" stop-color="#2AA136"/><stop offset="0.45" stop-color="{BRAND}"/>'
        f'<stop offset="1" stop-color="#0B5C12"/></radialGradient>'
        f'<linearGradient id="fade" x1="0" x2="1"><stop offset="0.35" stop-color="#fff" stop-opacity="0"/>'
        f'<stop offset="1" stop-color="#fff" stop-opacity="1"/></linearGradient>'
        f'<mask id="m"><rect width="{W}" height="{H}" fill="url(#fade)"/></mask>'
        f'<clipPath id="c"><rect width="{W}" height="{H}" rx="28"/></clipPath>'
    )
    p = [f'<g clip-path="url(#c)"><rect width="{W}" height="{H}" fill="url(#wash)"/>']
    # pattern of mark shapes, fading in from the left, like the hero image
    tiles = []
    for row in range(4):
        for col in range(8):
            x, y = 560 + col * 128 - (row % 2) * 64, -40 + row * 128
            tiles.append(f'<g transform="translate({x} {y}) scale({104 / 1024})">{glyph(white)}</g>')
    p.append(f'<g mask="url(#m)" opacity="0.09">{"".join(tiles)}</g></g>')

    x = 88
    # inverse mark: white tile, green glyph
    p.append(f'<g transform="translate({x} 88) scale({104 / 1024})"><rect width="1024" height="1024" rx="230" fill="{white}"/>'
             f'{glyph(BRAND, white)}</g>')
    p.append(text("Thammana Srinivas", CLASH, 76, x, 276, white))
    p.append(text("Software engineer. Building a calmer phone.", GEIST, 28, x, 324, white, opacity=0.8))
    a, w = pill(x, 358, "SWE @ PAYPAL", None, "#FFFFFF1A", "#FFFFFF40", white, dot="#5BDF62")
    b, w2 = pill(x + w + 12, 358, "FOUNDER, ZENMODE OS", None, white, white, BRAND)
    c, _ = pill(x + w + w2 + 24, 358, "OPEN SOURCE", None, "none", "#FFFFFF40", "#FFFFFFCC")
    p += a + b + c
    p.append(text("QUIET THE NOISE,", MONO, 16, W - 72, 120, white, 0.14, "end", opacity=0.7))
    p.append(text("TOGETHER.", MONO, 16, W - 72, 144, white, 0.14, "end"))
    return svg(W, H, "Thammana Srinivas. Software engineer at PayPal, founder of ZenMode OS.", p, defs)


# ---------------------------------------------------------------- section heading
def section(num, title, t):
    W, H = 1280, 64
    p = [f'<rect x="0" y="12" width="44" height="30" rx="8" fill="{t["tint"]}" stroke="{t["tintline"]}"/>',
         text(num, MONO, 16, 22, 33, t["accent"], 0.05, "middle"),
         text(title, CLASH, 32, 62, 39, t["ink"])]
    x0 = 62 + measure(title, CLASH, 32) + 24
    p.append(f'<rect x="{x0}" y="27" width="{W - x0}" height="1" fill="{t["line"]}"/>')
    return svg(W, H, title, p)


# ---------------------------------------------------------------- zenmode feature widgets
def icon(kind, cx, cy, t, col):
    if kind == "score":
        return (f'<circle cx="{cx}" cy="{cy}" r="17" fill="none" stroke="{t["line"]}" stroke-width="5"/>'
                f'<circle cx="{cx}" cy="{cy}" r="17" fill="none" stroke="{col}" stroke-width="5" stroke-linecap="round" '
                f'stroke-dasharray="75 107" transform="rotate(-90 {cx} {cy})"/>')
    if kind == "streak":
        return (f'<path transform="translate({cx - 14} {cy - 20})" fill="{col}" d="M14 0C16 9 28 14 28 26A14 14 0 0 1 0 26'
                f'C0 18 6 14 8 8C10 14 12 16 14 16C13 10 12 5 14 0Z"/>')
    if kind == "circle":
        return "".join(f'<circle cx="{cx + dx}" cy="{cy + dy}" r="10" fill="{col}" opacity="{o}"/>'
                       for dx, dy, o in [(-10, 6, 0.55), (10, 6, 0.8), (0, -9, 1)])
    return (f'<circle cx="{cx}" cy="{cy}" r="18" fill="{t["amberfill"]}"/>'
            f'<circle cx="{cx}" cy="{cy}" r="12" fill="none" stroke="#7A5A00" stroke-opacity="0.45" stroke-width="2"/>')


def features(t):
    W, H = 1280, 196
    items = [("score", "Zen Score", "07/10", "Your day, out of 10", False),
             ("streak", "Streaks", "13 DAYS", "Promises kept", False),
             ("circle", "ZenCircle", "2 OF 5", "Accountability with friends", False),
             ("gold", "Gold Pay", "+ GOLD", "Time saved becomes gold", True)]
    gap, n = 16, len(items)
    cw = (W - gap * (n - 1)) / n
    p = []
    for i, (k, name, stat, desc, reward) in enumerate(items):
        x = i * (cw + gap)
        fill, stroke = (t["amberbg"], t["amberfill"] + "55") if reward else (t["card"], t["line"])
        col = t["amber"] if reward else t["accent"]
        p.append(f'<rect x="{x + 0.5}" y="0.5" width="{cw - 1}" height="{H - 1}" rx="22" fill="{fill}" stroke="{stroke}"/>')
        p.append(icon(k, x + 44, 50, t, col))
        p.append(text(stat, MONO, 16, x + cw - 24, 56, col, 0.08, "end"))
        p.append(text(name, CLASH, 28, x + 24, 128, t["ink"]))
        p.append(text(desc, GEIST, 17, x + 24, 160, t["muted"]))
    return svg(W, H, "Zen Score, Streaks, ZenCircle, Gold Pay", p)


# ---------------------------------------------------------------- day job
def job(t, y, now, company, role, when, tag, stats):
    """One full-width job card: identity block on the left, stat tiles on the right."""
    W, H = 1280, 236
    fill, stroke = (t["tint"], t["tintline"]) if now else (t["card"], t["line"])
    p = [f'<rect x="0.5" y="{y + 0.5}" width="{W - 1}" height="{H - 1}" rx="22" fill="{fill}" stroke="{stroke}"/>']
    a, _ = (pill(24, y + 24, "NOW", t, t["card"], t["tintline"], t["accent"], dot=t["accent"]) if now
            else pill(24, y + 24, "PREVIOUSLY", t, t["sunk"], t["line"], t["muted"]))
    p += a
    p.append(text(company, CLASH, 44, 24, y + 140, t["ink"]))
    p.append(text(role, GEIST, 20, 24, y + 176, t["muted"]))
    p.append(text(when, MONO, 15, 24, y + 210, t["accent"] if now else t["muted"], 0.08))
    sx, gap = 380, 16
    sw = (W - 20 - sx - gap * (len(stats) - 1)) / len(stats)
    tile = t["card"] if now else t["sunk"]
    for i, (big, lab, sub) in enumerate(stats):
        bx = sx + i * (sw + gap)
        p.append(f'<rect x="{bx}" y="{y + 20}" width="{sw}" height="{H - 40}" rx="20" fill="{tile}" stroke="{stroke}"/>')
        p.append(text(big, MONO, 60, bx + 24, y + 108, t["accent"] if now else t["ink"]))
        p.append(text(lab, GEIST, 20, bx + 24, y + 152, t["ink"]))
        p.append(text(sub, GEIST, 17, bx + 24, y + 180, t["muted"]))
    return p, H


def work(t):
    p1, h = job(t, 0, True, "PayPal", "Software Engineer 2", "MAY 2025 — PRESENT", None, [
        ("40%", "faster tenant onboarding", "SCM multi-tenancy"),
        ("+3", "API maturity levels", "zero breaking changes"),
        ("500K+", "records benchmarked", "Bigtable POC")])
    p2, h2 = job(t, h + 16, False, "Zoho", "Member of Technical Staff", "JAN 2022 — APR 2025", None, [
        ("10M+", "cron jobs a day", "Kafka + Redis scheduler"),
        ("1h→1m", "min schedule interval", "fault-tolerant, distributed"),
        ("10x", "faster job dispatch", "50ms → 5ms latency")])
    return svg(1280, h + 16 + h2, "PayPal, Software Engineer since May 2025: 40% faster tenant onboarding, "
               "API maturity up 3 levels, 500K+ record Bigtable POC. Previously Zoho: 10M+ cron jobs a day, "
               "scheduling interval cut from 1 hour to 1 minute, dispatch latency 50ms to 5ms.", p1 + p2)


# ---------------------------------------------------------------- toolbox
def toolbox(t):
    rows = [("BACKEND", ["Java", "Spring Boot", "Golang", "Kafka", "Redis", "PostgreSQL", "Distributed systems"]),
            ("CLOUD", ["GCP", "Bigtable", "Docker", "Kubernetes", "Serverless", "Cloud migration", "Multi-tenancy"]),
            ("ANDROID", ["Kotlin", "Jetpack Compose", "Firebase", "Cloud Functions"]),
            ("AI + WEB", ["LLM agents", "RAG", "MCP", "TypeScript", "Node.js", "Python"])]
    W, rh = 1280, 60
    H = rh * len(rows) + 40
    p = [f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="22" fill="{t["card"]}" stroke="{t["line"]}"/>']
    for i, (lab, chips) in enumerate(rows):
        y = 20 + i * rh
        p.append(text(lab, MONO, 15, 28, y + 36, t["accent"], 0.1))
        x = 170
        for c in chips:
            w = measure(c, GEIST, 18) + 32
            p.append(f'<rect x="{x}" y="{y + 10}" width="{w}" height="40" rx="8" fill="{t["sunk"]}" stroke="{t["line"]}"/>')
            p.append(text(c, GEIST, 18, x + 16, y + 36, t["ink"]))
            x += w + 10
        if i < len(rows) - 1:
            p.append(f'<rect x="28" y="{y + rh}" width="{W - 56}" height="1" fill="{t["line"]}" opacity="0.6"/>')
    return svg(W, H, "Toolbox: Java, Spring, Kafka, Redis, Kotlin, Jetpack Compose, Firebase, TypeScript, Node.js, Python, RAG, MCP", p)


# ---------------------------------------------------------------- footer
def footer(t):
    W, H = 1280, 90
    p = [f'<rect x="0" y="20" width="{W}" height="1" fill="{t["line"]}"/>',
         f'<g transform="translate({W / 2 - 14} 6) scale({28 / 1024})"><rect width="1024" height="1024" rx="230" fill="{BRAND}"/>'
         f'{glyph("#FFFFFF", BRAND)}</g>',
         text("LESS SCROLLING. MORE LIVING.", MONO, 15, W / 2, 72, t["muted"], 0.16, "middle")]
    return svg(W, H, "Less scrolling. More living.", p)


os.makedirs(OUT, exist_ok=True)
for name in os.listdir(OUT):
    os.remove(os.path.join(OUT, name))
for name, t in THEMES.items():
    files = {"features": features(t), "work": work(t), "toolbox": toolbox(t), "footer": footer(t),
             "h-now": section("01", "What I'm building", t), "h-work": section("02", "Day job", t),
             "h-stack": section("03", "Toolbox", t)}
    for k, v in files.items():
        open(f"{OUT}/{k}-{name}.svg", "w").write(v)
open(f"{OUT}/banner.svg", "w").write(banner())
open(f"{OUT}/zenmode-mark.svg", "w").write(svg(96, 96, "ZenMode OS", [mark(0, 0, 96)]))
print("ok")
