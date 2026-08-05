#!/usr/bin/env python3
"""Generate the profile's SVG cards.

Everything here is committed into the repo, so the README never depends on a
third-party rendering service at display time. Each card is emitted twice, in a
light and a dark variant, and the README picks between them with <picture>.

    python3 scripts/gen_cards.py
"""

import json
import urllib.request
from pathlib import Path

USER = "henrykanaskie"
OUT = Path(__file__).resolve().parent.parent / "assets"

# personal_webpage has node_modules committed — 21.4 MB of vendored JS/TS that
# would otherwise drown out every line of real work in the byte counts.
EXCLUDE_REPOS = {"personal_webpage"}
EXCLUDE_LANGS = {"CSS", "HTML"}

THEMES = {
    "light": dict(name="light", bg="#ffffff", border="#d0d7de", title="#1f2328",
                  text="#1f2328", muted="#656d76", track="#eaeef2"),
    "dark":  dict(name="dark", bg="#0d1117", border="#30363d", title="#e6edf3",
                  text="#e6edf3", muted="#8b949e", track="#21262d"),
}

# GitHub's own linguist colors.
LANG_COLORS = {
    "Python": "#3572A5", "C": "#555555", "C++": "#f34b7d", "JavaScript": "#f1e05a",
    "TypeScript": "#3178c6", "Swift": "#F05138", "R": "#198CE7", "Shell": "#89e051",
    "HTML": "#e34c26", "CSS": "#563d7c", "Jupyter Notebook": "#DA5B0B",
}

STAGE_COLORS = {
    "shipped":     ("#3fb950", "#2ea043"),
    "active":      ("#58a6ff", "#1f6feb"),
    "in progress": ("#d29922", "#bb8009"),
    "scaffold":    ("#bc8cff", "#8957e5"),
}

PROJECTS = [
    ("gpt-scratch", "GPT built from first principles", "shipped", 1.00),
    ("Cap_Match_Net", "Capacitor matching via OR-Tools", "shipped", 1.00),
    ("small-shell", "Unix shell in C — jobs, signals, redirection", "shipped", 1.00),
    ("ML_quantitative_research", "Block bootstrap, log-return modeling", "active", 0.70),
    ("rLog", "Voice-driven logging tool", "active", 0.60),
    ("me-tutor", "Agents generating a verified ME curriculum", "active", 0.50),
    ("pitwall", "Motorsport strategy and telemetry", "in progress", 0.40),
    ("GrowthApp", "SwiftUI habit tracker, WidgetKit suite", "scaffold", 0.30),
]

FOCUS = [
    ("machine learning", "#3572A5"), ("transformers", "#8957e5"),
    ("quantitative research", "#3fb950"), ("time series", "#1f6feb"),
    ("optimization", "#d29922"), ("embedded C", "#555555"),
    ("signal processing", "#f34b7d"), ("SwiftUI", "#F05138"),
    ("agents", "#bc8cff"), ("numerical methods", "#198CE7"),
]


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def adapt(color, theme):
    """Lift very dark accents so they stay legible on a dark card.

    Several linguist colors (C is #555555) are tuned for white backgrounds and
    all but vanish against #0d1117, so mix them toward white in the dark theme.
    """
    if theme != "dark":
        return color
    r, g, b = (int(color[i:i + 2], 16) for i in (1, 3, 5))
    lum = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255
    if lum >= 0.38:
        return color
    k = 0.55                                   # blend toward white
    return "#%02x%02x%02x" % tuple(
        round(c + (255 - c) * k) for c in (r, g, b)
    )


def shell(w, h, t, body, defs=""):
    """Card chrome: rounded background, 1px border, then body."""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" font-family="-apple-system,BlinkMacSystemFont,'
        f'Segoe UI,Helvetica,Arial,sans-serif">'
        f"<defs>{defs}</defs>"
        f'<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="12" '
        f'fill="{t["bg"]}" stroke="{t["border"]}"/>'
        f"{body}</svg>"
    )


def fetch_languages():
    url = f"https://api.github.com/users/{USER}/repos?per_page=100"
    repos = json.load(urllib.request.urlopen(url))
    totals = {}
    for r in repos:
        if r["fork"] or r["name"] in EXCLUDE_REPOS:
            continue
        for k, v in json.load(urllib.request.urlopen(r["languages_url"])).items():
            if k not in EXCLUDE_LANGS:
                totals[k] = totals.get(k, 0) + v
    return sorted(totals.items(), key=lambda kv: -kv[1])


def card_languages(langs, t):
    w, pad = 440, 20
    total = sum(v for _, v in langs) or 1
    shown = langs[:6]

    body = (f'<text x="{pad}" y="34" fill="{t["title"]}" font-size="15" '
            f'font-weight="600">Languages</text>')

    # Stacked bar, clipped to a rounded rect so the ends are capped.
    bar_y, bar_w, bar_h = 50, w - 2 * pad, 10
    body += (f'<clipPath id="bar"><rect x="{pad}" y="{bar_y}" width="{bar_w}" '
             f'height="{bar_h}" rx="5"/></clipPath>')
    body += (f'<rect x="{pad}" y="{bar_y}" width="{bar_w}" height="{bar_h}" '
             f'rx="5" fill="{t["track"]}"/>')
    body += f'<g clip-path="url(#bar)">'
    x = pad
    for name, val in shown:
        seg = bar_w * val / total
        col = adapt(LANG_COLORS.get(name, "#8b949e"), t["name"])
        body += (f'<rect x="{x:.2f}" y="{bar_y}" width="{seg:.2f}" '
                 f'height="{bar_h}" fill="{col}"/>')
        x += seg
    body += "</g>"

    # Two-column legend. The percentage sits at a fixed column rather than
    # after the name — estimating text width packed "C++" against "0.3%".
    for i, (name, val) in enumerate(shown):
        col_i, row = i % 2, i // 2
        lx = pad + col_i * (bar_w / 2)
        ly = 88 + row * 26
        pct = 100 * val / total
        dot = adapt(LANG_COLORS.get(name, "#8b949e"), t["name"])
        body += f'<circle cx="{lx+5}" cy="{ly-4}" r="5" fill="{dot}"/>'
        body += (f'<text x="{lx+18}" y="{ly}" fill="{t["text"]}" font-size="12.5" '
                 f'font-weight="500">{esc(name)}</text>')
        body += (f'<text x="{lx+150:.0f}" y="{ly}" fill="{t["muted"]}" '
                 f'font-size="12.5" text-anchor="end">{pct:.1f}%</text>')

    h = 88 + ((len(shown) + 1) // 2) * 26 + 26
    body += (f'<text x="{pad}" y="{h-12}" fill="{t["muted"]}" font-size="10.5">'
             f'by bytes across public repos · vendored node_modules excluded</text>')
    return shell(w, h, t, body)


def card_projects(t):
    w, pad = 900, 24
    row_h, top = 46, 62
    h = top + len(PROJECTS) * row_h + 24

    defs = ""
    for stage, (c1, c2) in STAGE_COLORS.items():
        gid = "g" + stage.replace(" ", "")
        defs += (f'<linearGradient id="{gid}" x1="0" x2="1">'
                 f'<stop offset="0" stop-color="{c1}"/>'
                 f'<stop offset="1" stop-color="{c2}"/></linearGradient>')

    body = (f'<text x="{pad}" y="34" fill="{t["title"]}" font-size="15" '
            f'font-weight="600">Project stage</text>')
    body += (f'<text x="{pad}" y="52" fill="{t["muted"]}" font-size="11.5">'
             f'Where each project actually sits — a status readout, not a roadmap.</text>')

    bar_x, bar_w = 470, 250
    for i, (name, desc, stage, frac) in enumerate(PROJECTS):
        y = top + i * row_h + 22
        c1, c2 = STAGE_COLORS[stage]
        gid = "g" + stage.replace(" ", "")

        body += (f'<text x="{pad}" y="{y}" fill="{t["text"]}" font-size="13" '
                 f'font-weight="600">{esc(name)}</text>')
        body += (f'<text x="{pad}" y="{y+15}" fill="{t["muted"]}" font-size="11">'
                 f'{esc(desc)}</text>')

        body += (f'<rect x="{bar_x}" y="{y-9}" width="{bar_w}" height="9" rx="4.5" '
                 f'fill="{t["track"]}"/>')
        body += (f'<rect x="{bar_x}" y="{y-9}" width="{bar_w*frac:.1f}" height="9" '
                 f'rx="4.5" fill="url(#{gid})"/>')
        body += (f'<text x="{bar_x+bar_w+12}" y="{y}" fill="{t["muted"]}" '
                 f'font-size="11.5" font-weight="500">{int(frac*100)}%</text>')

        # Stage pill.
        px = bar_x + bar_w + 56
        pw = 8 + len(stage) * 6.6
        body += (f'<rect x="{px}" y="{y-13}" width="{pw:.0f}" height="18" rx="9" '
                 f'fill="{c2}" fill-opacity="0.16" stroke="{c2}" '
                 f'stroke-opacity="0.45"/>')
        body += (f'<text x="{px+pw/2:.0f}" y="{y}" fill="{c1}" font-size="10.5" '
                 f'font-weight="600" text-anchor="middle">{esc(stage)}</text>')

    return shell(w, h, t, body, defs)


def card_focus(t):
    w, pad = 440, 20
    body = (f'<text x="{pad}" y="34" fill="{t["title"]}" font-size="15" '
            f'font-weight="600">Focus areas</text>')

    x, y = pad, 58
    for label, raw in FOCUS:
        color = adapt(raw, t["name"])
        pw = 20 + len(label) * 6.5
        if x + pw > w - pad:          # wrap
            x, y = pad, y + 30
        body += (f'<rect x="{x}" y="{y-14}" width="{pw:.0f}" height="22" rx="11" '
                 f'fill="{color}" fill-opacity="0.15" stroke="{color}" '
                 f'stroke-opacity="0.5"/>')
        body += (f'<text x="{x+pw/2:.0f}" y="{y+1}" fill="{color}" font-size="11.5" '
                 f'font-weight="600" text-anchor="middle">{esc(label)}</text>')
        x += pw + 8

    return shell(w, y + 30, t, body)


def main():
    OUT.mkdir(exist_ok=True)
    langs = fetch_languages()
    print("languages:", [(k, v) for k, v in langs[:6]])

    for theme, t in THEMES.items():
        for name, svg in (
            ("languages", card_languages(langs, t)),
            ("projects", card_projects(t)),
            ("focus", card_focus(t)),
        ):
            p = OUT / f"{name}-{theme}.svg"
            p.write_text(svg)
            print("wrote", p.name, len(svg), "bytes")


if __name__ == "__main__":
    main()
