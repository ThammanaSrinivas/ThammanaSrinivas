"""Generate the profile README SVGs (text outlined to paths, so no web fonts are needed).

Two brands, same rule as the portfolio site:
  * Personal (banner, headings, work, toolbox, footer): read straight from the portfolio's brand
    files, so the README can't drift from thammanasrinivas.com:
      <portfolio>/src/theme/colors.json       active palette (Calm Glow)
      <portfolio>/src/theme/typography.json   active type set (Builder) + font files
      <portfolio>/src/components/zen/monogramPath.ts   the logo
  * ZenMode OS (features, stats): the ZenMode v3 brand, fonts from the zenmode app.

Usage:  python3 scripts/gen_assets.py assets
Env:    PORTFOLIO (default ~/Srinivas/github/tech-metaverse-canvas)
        ZENMODE_FONTS (default ~/Srinivas/github/zenmode/zenmode/app/src/main/res/font/)
Needs:  pip install fonttools brotli   (the portfolio fonts are woff2)
"""
import colorsys, json, math, os, re, sys
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

PORTFOLIO = os.environ.get("PORTFOLIO", os.path.expanduser("~/Srinivas/github/tech-metaverse-canvas"))
ZM_FONTS = os.environ.get("ZENMODE_FONTS", os.path.expanduser("~/Srinivas/github/zenmode/zenmode/app/src/main/res/font/"))
OUT = sys.argv[1]

# ---------------------------------------------------------------- brand files (single source of truth)
COLORS = json.load(open(f"{PORTFOLIO}/src/theme/colors.json"))
TYPO = json.load(open(f"{PORTFOLIO}/src/theme/typography.json"))
PAL = next(p for p in COLORS["palettes"] if p["name"] == COLORS["active"])
SYS = COLORS["system"]
SET = next(s for s in TYPO["sets"] if s["name"] == TYPO["active"]["set"])
_logo = open(f"{PORTFOLIO}/src/components/zen/monogramPath.ts").read()
LOGO_PATH = re.search(r"MONOGRAM_PATH =\s*'([^']+)'", _logo).group(1)
LOGO_DOT = tuple(float(v) for v in re.search(r"MONOGRAM_DOT = \{ cx: ([\d.]+), cy: ([\d.]+), r: ([\d.]+) \}", _logo).groups())

ZEN = COLORS["zenmode"]["zen"]["700"]


# ---------------------------------------------------------------- colour maths (ported from src/theme/color.ts)
def rgb(h):
    h = h.lstrip("#")
    return [int(h[i:i + 2], 16) for i in (0, 2, 4)]


def hexc(c):
    return "#" + "".join(f"{max(0, min(255, round(v))):02X}" for v in c)


def mix(a, b, t):
    A, B = rgb(a), rgb(b)
    return hexc([A[i] + (B[i] - A[i]) * t for i in range(3)])


def lum(h):
    c = [v / 255 for v in rgb(h)]
    c = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def contrast(a, b):
    x, y = sorted([lum(a), lum(b)], reverse=True)
    return (x + 0.05) / (y + 0.05)


def readable_on(col, grounds, minimum=4.5):
    """Shade lightness (keeping hue) until it reads on every ground: same rule as the site."""
    if all(contrast(col, g) >= minimum for g in grounds):
        return col
    r, g, b = [v / 255 for v in rgb(col)]
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    lighten = all(lum(gr) < 0.18 for gr in grounds)
    for step in range(1, 101):
        L = min(1, max(0, l + (1 if lighten else -1) * step * 0.01))
        c = hexc([v * 255 for v in colorsys.hls_to_rgb(h, L, s)])
        if all(contrast(c, gr) >= minimum for gr in grounds):
            return c
    return SYS["white"] if lighten else SYS["black"]


def best_on(bg, cands):
    return max(cands, key=lambda c: contrast(c, bg))


def personal(mode):
    """The site's light / dark scopes (tokens.ts), for the README's light and dark variants."""
    p = PAL
    bg, fg = (p["light"], p["dark"]) if mode == "light" else (p["dark"], p["light"])
    card = mix(bg, SYS["white"], 0.55) if mode == "light" else mix(bg, fg, 0.05)
    sunk = mix(bg, fg, 0.06 if mode == "light" else 0.07)
    line = mix(bg, fg, 0.13 if mode == "light" else 0.16)
    tint = mix(bg, p["secondary"], 0.55 if mode == "light" else 0.16)
    return dict(bg=bg, card=card, sunk=sunk, line=line, ink=fg, tint=tint, tintline=mix(tint, fg, 0.12),
                muted=readable_on(mix(fg, bg, 0.42), [bg, card, sunk]),
                accent=readable_on(p["primary"], [bg, card, tint]),
                hi=p["highlight"])


# ZenMode OS v3 (features + stats): the product keeps its own brand, as on the site.
ZM = {
    "light": dict(bg="#FAF9F5", card="#FFFFFF", sunk="#F2F1ED", line="#DBD9D2", ink="#111111",
                  muted="#666861", accent=ZEN, tint="#E6F6E7", tintline="#C8E7CA",
                  amber="#7A5A00", amberfill="#FFC800", amberbg="#FFF8E1"),
    "dark": dict(bg="#111111", card="#1A1A1A", sunk="#161616", line="#2B2B2B", ink="#F5F5F1",
                 muted="#9E9E98", accent="#5BDF62", tint="#16210F", tintline="#23391F",
                 amber="#FFC800", amberfill="#FFC800", amberbg="#2A2410"),
}


# ---------------------------------------------------------------- fonts
def _file(family, style="normal"):
    f = next(x for x in TYPO["faces"] if x["family"] == family and x.get("style", "normal") == style)
    return PORTFOLIO + "/public" + f["file"]


FONTS = {
    "display": (_file(SET["display"]), {"wght": SET.get("weight", 700), "opsz": 48}),
    "accent": (_file(SET["accent"], "italic"), None),
    "body": (_file(SET["sans"]), {"wght": 400}),
    "body-strong": (_file(SET["sans"]), {"wght": 600}),
    "mono": (_file(SET["mono"]), None),
    "zm-display": (ZM_FONTS + "clash_display_medium.otf", None),
    "zm-body": (ZM_FONTS + "geist_variable.ttf", {"wght": 400}),
    "zm-mono": (ZM_FONTS + "departure_mono_regular.otf", None),
}
_cache = {}


def font(key):
    if key not in _cache:
        path, axes = FONTS[key]
        f = TTFont(path)
        if axes and "fvar" in f:
            have = {a.axisTag for a in f["fvar"].axes}
            f = instancer.instantiateVariableFont(f, {k: v for k, v in axes.items() if k in have})
        _cache[key] = (f, f.getGlyphSet(), f.getBestCmap(), f["head"].unitsPerEm)
    return _cache[key]


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


def rich(parts, size, x, y, ink, accent):
    """Heading text with an accent word: [('What I\\'m ', False), ('building', True)]."""
    out = []
    for s, acc in parts:
        ff, sz = ("accent", size * 1.08) if acc else ("display", size)
        out.append(text(s, ff, sz, x, y, accent if acc else ink))
        x += measure(s, ff, sz)
    return "".join(out), x


# ---------------------------------------------------------------- shared svg bits
ANIM = """<style>
.rise{opacity:0;animation:rise .8s cubic-bezier(.22,1,.36,1) forwards}
@keyframes rise{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:none}}
.draw{transform-box:fill-box;transform-origin:left;transform:scaleX(0);animation:draw 1.2s .3s cubic-bezier(.22,1,.36,1) forwards}
@keyframes draw{to{transform:scaleX(1)}}
.sweep{transform-box:fill-box;transform-origin:left;transform:scaleX(0);animation:draw .9s 1s cubic-bezier(.22,1,.36,1) forwards}
.ring{stroke-dasharray:107;stroke-dashoffset:107;animation:ring 1.6s .5s cubic-bezier(.22,1,.36,1) forwards}
@keyframes ring{to{stroke-dashoffset:32}}
.flicker{transform-box:fill-box;transform-origin:bottom;animation:flicker 2.4s ease-in-out infinite}
@keyframes flicker{30%{transform:scale(.95,1.07)}60%{transform:scale(1.03,.97)}}
.shine{animation:shine 3.6s ease-in-out infinite}
@keyframes shine{0%,60%{transform:translateX(0)}100%{transform:translateX(60px)}}
.pulse{animation:pulse 1.8s ease-in-out infinite}
@keyframes pulse{50%{opacity:.25}}
.dotdrop{transform-box:fill-box;transform-origin:center;transform:scale(0);animation:pop .5s .9s cubic-bezier(.34,1.56,.64,1) forwards}
@keyframes pop{to{transform:scale(1)}}
@media (prefers-reduced-motion:reduce){.rise,.draw,.sweep,.ring,.flicker,.shine,.pulse,.dotdrop{animation:none;opacity:1}.draw,.sweep,.dotdrop{transform:none}.ring{stroke-dashoffset:32}}
</style>"""


def rise(content, delay):
    return f'<g class="rise" style="animation-delay:{delay:.2f}s">{content}</g>'


def svg(W, H, title, parts, defs=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img">'
            f"<title>{title}</title>{ANIM}<defs>{defs}</defs>" + "".join(parts) + "</svg>")


def logo(x, y, size, tile=None, ink=None, dot=None, animate=False):
    """The personal logo (platform T + the highlighter dot), from the site's monogramPath.ts."""
    tile, ink, dot = tile or PAL["primary"], ink or best_on(PAL["primary"], [PAL["dark"], PAL["light"]]), dot or PAL["highlight"]
    cx, cy, r = LOGO_DOT
    d = f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{dot}"/>'
    if animate:
        d = f'<g class="dotdrop">{d}</g>'
    return (f'<g transform="translate({x} {y}) scale({size / 1024})"><rect width="1024" height="1024" rx="230" fill="{tile}"/>'
            f'<path fill="{ink}" d="{LOGO_PATH}"/>{d}</g>')


def pill(x, y, label, fill, stroke, color, dot=None, ff="mono"):
    w = measure(label, ff, 14, 0.08) + 32 + (18 if dot else 0)
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="34" rx="17" fill="{fill}" stroke="{stroke}"/>']
    tx = x + 16
    if dot:
        out.append(f'<circle class="pulse" cx="{tx + 4}" cy="{y + 17}" r="4" fill="{dot}"/>')
        tx += 18
    out.append(text(label, ff, 14, tx, y + 22, color, 0.08))
    return out, w


# ---------------------------------------------------------------- banner (personal, same in light and dark)
def banner():
    """Ink hero like thammanasrinivas.com: logo, name, the highlighted brand line, role pills."""
    W, H = 1280, 440
    p = PAL
    defs = (
        f'<radialGradient id="g1" cx="0.92" cy="-0.1" r="0.75"><stop offset="0" stop-color="{p["primary"]}" stop-opacity="0.32"/>'
        f'<stop offset="1" stop-color="{p["primary"]}" stop-opacity="0"/></radialGradient>'
        f'<radialGradient id="g2" cx="0.05" cy="1.15" r="0.55"><stop offset="0" stop-color="{p["highlight"]}" stop-opacity="0.16"/>'
        f'<stop offset="1" stop-color="{p["highlight"]}" stop-opacity="0"/></radialGradient>'
        f'<linearGradient id="rule" x1="0" x2="1"><stop offset="0" stop-color="{p["primary"]}" stop-opacity="0"/>'
        f'<stop offset="0.4" stop-color="{p["primary"]}"/><stop offset="0.85" stop-color="{p["highlight"]}"/>'
        f'<stop offset="1" stop-color="{p["highlight"]}" stop-opacity="0"/></linearGradient>'
        f'<clipPath id="c"><rect width="{W}" height="{H}" rx="28"/></clipPath>'
    )
    light, dark, hi = p["light"], p["dark"], p["highlight"]
    accent = readable_on(p["primary"], [dark])
    out = [f'<g clip-path="url(#c)"><rect width="{W}" height="{H}" fill="{dark}"/>'
           f'<rect width="{W}" height="{H}" fill="url(#g1)"/><rect width="{W}" height="{H}" fill="url(#g2)"/>'
           f'<rect x="0" y="{H - 3}" width="{W}" height="3" fill="url(#rule)"/></g>']
    x = 88
    out.append(rise(logo(x, 70, 84, animate=True), 0.05))
    out.append(rise(text("Thammana Srinivas", "display", 74, x, 246, light, -0.03), 0.2))

    # "I build [innovative systems at scale]." with the highlighter swept in behind the phrase
    y, size = 300, 27
    lead = "I build "
    phrase = "innovative systems at scale"
    w0, w1 = measure(lead, "body-strong", size), measure(phrase, "body-strong", size)
    pad = 7  # the highlighter's inner padding; the phrase moves right by the same amount
    px = x + w0 + pad
    out.append(rise(
        text(lead, "body-strong", size, x, y, light)
        + f'<rect class="sweep" x="{px - pad}" y="{y - size + 2}" width="{w1 + 2 * pad}" height="{size + 9}" rx="5" fill="{hi}"/>'
        + text(phrase, "body-strong", size, px, y, dark)
        + text(".", "body-strong", size, px + w1 + pad + 2, y, light), 0.35))
    out.append(rise(text("Platforms at PayPal by day, ZenMode OS on my own time.", "body", 21, x, 338, light, opacity=0.72), 0.45))

    a, w = pill(x, 362, "SWE @ PAYPAL", f"{light}10", f"{light}33", light, dot=hi)
    b, w2 = pill(x + w + 12, 362, "FOUNDER, ZENMODE OS", mix(dark, p["primary"], 0.22), mix(dark, p["primary"], 0.45), accent)
    c, _ = pill(x + w + w2 + 24, 362, "OPEN SOURCE", "none", f"{light}33", f"{light}B0")
    out += [rise("".join(a), 0.55), rise("".join(b), 0.62), rise("".join(c), 0.69)]

    vx = W - 72
    out.append(rise(
        text("CURIOSITY · CLARITY · OWNERSHIP", "mono", 14, vx, 102, light, 0.14, "end", opacity=0.72)
        + text("THAMMANASRINIVAS.COM", "mono", 14, vx, 128, accent, 0.14, "end"), 0.85))
    return svg(W, H, "Thammana Srinivas. I build innovative systems at scale: platforms at PayPal by day, ZenMode OS on my own time.", out, defs)


# ---------------------------------------------------------------- section heading (personal)
def section(num, parts, t, title):
    W, H = 1280, 64
    out = [f'<rect x="0" y="12" width="44" height="30" rx="8" fill="{t["tint"]}" stroke="{t["tintline"]}"/>',
           text(num, "mono", 15, 22, 32, t["accent"], 0.05, "middle")]
    head, x_end = rich(parts, 32, 62, 39, t["ink"], t["accent"])
    out.append(head)
    x0 = x_end + 24
    out.append(f'<g class="draw"><rect x="{x0}" y="27" width="{W - x0}" height="1" fill="{t["line"]}"/>'
               f'<rect x="{x0}" y="27" width="40" height="1" fill="{t["accent"]}"/></g>')
    return svg(W, H, title, out)


# ---------------------------------------------------------------- ZenMode features + stats (ZenMode brand)
def zm_mark_glyph(fg, hole=None):
    polys = ["214,214 416,214 214,416", "810,810 607,810 810,607",
             "600.6,216 810,216 810,423.4 423.4,810 214,810 214,602.6"]
    s = "".join(f'<polygon points="{q}" fill="{fg}" stroke="{fg}" stroke-width="80" stroke-linejoin="round"/>' for q in polys)
    return s + (f'<circle cx="510" cy="510" r="40" fill="{hole}"/>' if hole else "")


def icon(kind, cx, cy, t, col):
    if kind == "score":
        return (f'<circle cx="{cx}" cy="{cy}" r="17" fill="none" stroke="{t["line"]}" stroke-width="5"/>'
                f'<g transform="rotate(-90 {cx} {cy})"><circle class="ring" cx="{cx}" cy="{cy}" r="17" fill="none" '
                f'stroke="{col}" stroke-width="5" stroke-linecap="round"/></g>')
    if kind == "streak":
        return (f'<g transform="translate({cx - 14} {cy - 20})"><g class="flicker"><path fill="{col}" d="M14 0C16 9 28 14 28 26'
                f'A14 14 0 0 1 0 26C0 18 6 14 8 8C10 14 12 16 14 16C13 10 12 5 14 0Z"/></g></g>')
    if kind == "circle":
        return "".join(f'<circle cx="{cx + dx}" cy="{cy + dy}" r="10" fill="{col}" opacity="{o}"/>'
                       for dx, dy, o in [(-10, 6, 0.55), (10, 6, 0.8), (0, -9, 1)])
    return (f'<clipPath id="coin"><circle cx="{cx}" cy="{cy}" r="18"/></clipPath>'
            f'<circle cx="{cx}" cy="{cy}" r="18" fill="{t["amberfill"]}"/>'
            f'<circle cx="{cx}" cy="{cy}" r="12" fill="none" stroke="#7A5A00" stroke-opacity="0.45" stroke-width="2"/>'
            f'<g clip-path="url(#coin)"><g class="shine"><rect x="{cx - 34}" y="{cy - 20}" width="8" height="40" '
            f'fill="#FFF8E1" opacity="0.7" transform="skewX(-20)"/></g></g>')


def features(t):
    W, H = 1280, 196
    items = [("score", "Zen Score", "07/10", "Your day, out of 10", False),
             ("streak", "Streaks", "13 DAYS", "Promises kept", False),
             ("circle", "ZenCircle", "2 OF 5", "Accountability with friends", False),
             ("gold", "Gold Invest", "+ GOLD", "Time saved becomes gold", True)]
    gap, n = 16, len(items)
    cw = (W - gap * (n - 1)) / n
    out = []
    for i, (k, name, stat, desc, reward) in enumerate(items):
        x = i * (cw + gap)
        fill, stroke = (t["amberbg"], t["amberfill"] + "55") if reward else (t["card"], t["line"])
        col = t["amber"] if reward else t["accent"]
        out.append(rise(
            f'<rect x="{x + 0.5}" y="0.5" width="{cw - 1}" height="{H - 1}" rx="22" fill="{fill}" stroke="{stroke}"/>'
            + icon(k, x + 44, 50, t, col)
            + text(stat, "zm-mono", 16, x + cw - 24, 56, col, 0.08, "end")
            + text(name, "zm-display", 28, x + 24, 128, t["ink"])
            + text(desc, "zm-body", 17, x + 24, 160, t["muted"]), 0.1 * i))
    return svg(W, H, "Zen Score, Streaks, ZenCircle, Gold Invest", out)


# Public numbers only: Play listing and the Product Hunt leaderboard (26 Sep 2026).
ZM_STATS = [("4.6★", "Play Store rating", "24 reviews", True),
            ("1K+", "installs", "Google Play", False),
            ("#14", "of 711 on Product Hunt", "launch day · #1 in Open Source", False),
            ("#7", "most discussed", "top 1% of the day", False)]


def star(cx, cy, r, fill):
    """Five-point star polygon (none of the fonts has a ★ glyph)."""
    pts = []
    for k in range(10):
        a = -math.pi / 2 + k * math.pi / 5
        rr = r if k % 2 == 0 else r * 0.45
        pts.append(f"{cx + rr * math.cos(a):.1f},{cy + rr * math.sin(a):.1f}")
    return f'<polygon points="{" ".join(pts)}" fill="{fill}" stroke="{fill}" stroke-width="2" stroke-linejoin="round"/>'


def zm_stats(t):
    W, H = 1280, 176
    gap, n = 16, len(ZM_STATS)
    cw = (W - gap * (n - 1)) / n
    out = []
    for i, (big, label, sub, reward) in enumerate(ZM_STATS):
        x = i * (cw + gap)
        col = t["amber"] if reward else t["accent"]
        num = big.replace("★", "")
        out.append(rise(
            f'<rect x="{x + 0.5}" y="0.5" width="{cw - 1}" height="{H - 1}" rx="20" fill="{t["tint"]}" stroke="{t["tintline"]}"/>'
            + text(num, "zm-mono", 48, x + 24, 72, col)
            + (star(x + 24 + measure(num, "zm-mono", 48) + 20, 54, 15, col) if "★" in big else "")
            + text(label, "zm-body", 20, x + 24, 120, t["ink"])
            + text(sub, "zm-body", 16, x + 24, 148, t["muted"]), 0.12 * i))
    return svg(W, H, "ZenMode OS: 4.6 star Play rating, 1K+ installs, #14 of 711 on Product Hunt launch day (#1 in Open Source), #7 most discussed.", out)


# ---------------------------------------------------------------- day job (personal)
def job(t, y, now, company, role, when, stats):
    W, H = 1280, 236
    fill, stroke = (t["tint"], t["tintline"]) if now else (t["card"], t["line"])
    out = [f'<rect x="0.5" y="{y + 0.5}" width="{W - 1}" height="{H - 1}" rx="22" fill="{fill}" stroke="{stroke}"/>']
    a, _ = (pill(24, y + 24, "NOW", t["card"], t["tintline"], t["accent"], dot=t["hi"]) if now
            else pill(24, y + 24, "PREVIOUSLY", t["sunk"], t["line"], t["muted"]))
    out += a
    out.append(text(company, "display", 44, 24, y + 140, t["ink"], -0.02))
    out.append(text(role, "body", 20, 24, y + 176, t["muted"]))
    out.append(text(when, "mono", 14, 24, y + 210, t["accent"] if now else t["muted"], 0.08))
    sx, gap = 380, 16
    sw = (W - 20 - sx - gap * (len(stats) - 1)) / len(stats)
    tile = t["card"] if now else t["sunk"]
    for i, (big, lab, sub) in enumerate(stats):
        bx = sx + i * (sw + gap)
        out.append(f'<rect x="{bx}" y="{y + 20}" width="{sw}" height="{H - 40}" rx="20" fill="{tile}" stroke="{stroke}"/>')
        out.append(text(big, "mono", 52, bx + 24, y + 104, t["accent"] if now else t["ink"]))
        out.append(text(lab, "body-strong", 19, bx + 24, y + 150, t["ink"]))
        out.append(text(sub, "body", 16, bx + 24, y + 178, t["muted"]))
    return out, H


def work(t):
    p1, h = job(t, 0, True, "PayPal", "Software Engineer 2", "MAY 2025 — PRESENT", [
        ("40%", "faster tenant onboarding", "SCM multi-tenancy"),
        ("+3", "API maturity levels", "zero breaking changes"),
        ("500K+", "records benchmarked", "Bigtable POC")])
    p2, h2 = job(t, h + 16, False, "Zoho", "Member of Technical Staff", "JAN 2022 — APR 2025", [
        ("10M+", "cron jobs a day", "Kafka + Redis scheduler"),
        ("1h→1m", "min schedule interval", "fault-tolerant, distributed"),
        ("10x", "faster job dispatch", "50ms → 5ms latency")])
    return svg(1280, h + 16 + h2, "PayPal, Software Engineer since May 2025: 40% faster tenant onboarding, "
               "API maturity up 3 levels, 500K+ record Bigtable POC. Previously Zoho: 10M+ cron jobs a day, "
               "scheduling interval cut from 1 hour to 1 minute, dispatch latency 50ms to 5ms.", p1 + p2)


# ---------------------------------------------------------------- toolbox (personal)
def toolbox(t):
    rows = [("BACKEND", ["Java", "Spring Boot", "Golang", "Kafka", "Redis", "PostgreSQL", "Distributed systems"]),
            ("CLOUD", ["GCP", "Bigtable", "Docker", "Kubernetes", "Serverless", "Cloud migration", "Multi-tenancy"]),
            ("ANDROID", ["Kotlin", "Jetpack Compose", "Firebase", "Cloud Functions"]),
            ("AI + WEB", ["LLM agents", "RAG", "MCP", "TypeScript", "Node.js", "Python"])]
    W, rh = 1280, 60
    H = rh * len(rows) + 40
    out = [f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="22" fill="{t["card"]}" stroke="{t["line"]}"/>']
    for i, (lab, chips) in enumerate(rows):
        y = 20 + i * rh
        out.append(text(lab, "mono", 14, 28, y + 36, t["accent"], 0.1))
        x = 170
        for c in chips:
            w = measure(c, "body", 17) + 32
            out.append(f'<rect x="{x}" y="{y + 10}" width="{w}" height="40" rx="8" fill="{t["sunk"]}" stroke="{t["line"]}"/>')
            out.append(text(c, "body", 17, x + 16, y + 36, t["ink"]))
            x += w + 10
        if i < len(rows) - 1:
            out.append(f'<rect x="28" y="{y + rh}" width="{W - 56}" height="1" fill="{t["line"]}" opacity="0.6"/>')
    return svg(W, H, "Toolbox: Java, Spring, Kafka, Redis, Kotlin, Jetpack Compose, Firebase, TypeScript, Node.js, Python, RAG, MCP", out)


# ---------------------------------------------------------------- footer (personal)
def footer(t):
    W, H = 1280, 90
    gap = 30  # the divider breaks around the logo (no background patch, so it sits on GitHub's own page colour)
    out = [f'<rect x="0" y="20" width="{W / 2 - gap}" height="1" fill="{t["line"]}"/>',
           f'<rect x="{W / 2 + gap}" y="20" width="{W / 2 - gap}" height="1" fill="{t["line"]}"/>',
           logo(W / 2 - 15, 6, 30),
           text("I BUILD INNOVATIVE SYSTEMS AT SCALE.", "mono", 14, W / 2, 72, t["muted"], 0.16, "middle")]
    return svg(W, H, "I build innovative systems at scale.", out)


os.makedirs(OUT, exist_ok=True)
for name in os.listdir(OUT):
    os.remove(os.path.join(OUT, name))
for mode in ("light", "dark"):
    t, z = personal(mode), ZM[mode]
    files = {
        "features": features(z), "zm-stats": zm_stats(z),
        "work": work(t), "toolbox": toolbox(t), "footer": footer(t),
        "h-now": section("01", [("What I'm ", False), ("building", True)], t, "01 What I'm building"),
        "h-work": section("02", [("Day ", False), ("job", True)], t, "02 Day job"),
        "h-how": section("03", [("How I ", False), ("build", True)], t, "03 How I build"),
        "h-stack": section("04", [("Toolbox", False)], t, "04 Toolbox"),
    }
    for k, v in files.items():
        open(f"{OUT}/{k}-{mode}.svg", "w").write(v)
open(f"{OUT}/banner.svg", "w").write(banner())
print("ok:", PAL["name"], "/", SET["name"])
