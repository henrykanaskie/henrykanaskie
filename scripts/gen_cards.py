#!/usr/bin/env python3
"""Generate the profile's SVG cards.

Everything here is committed into the repo, so the README never depends on a
third-party rendering service at display time. Each card is emitted twice, in a
light and a dark variant, and the README picks between them with <picture>.

The cards animate on load using SMIL (<animate>), which is the one form of
motion GitHub's markdown pipeline preserves — an SVG referenced by <img> is
rendered non-interactively, so CSS :hover and <script> are inert, but
declarative animation still runs.

    python3 scripts/gen_cards.py
"""

import collections
import datetime as dt
import json
import os
import urllib.request
import xml.dom.minidom
from pathlib import Path

USER = "henrykanaskie"
OUT = Path(__file__).resolve().parent.parent / "assets"

# personal_webpage used to commit its Next.js build output, which put 21 MB of
# compiled JS ahead of every hand-written line. That is untracked now and its
# generated path data is marked linguist-generated, so GitHub's own numbers are
# honest and nothing needs excluding here.
EXCLUDE_REPOS = set()
EXCLUDE_LANGS = {"CSS", "HTML"}

THEMES = {
    "light": dict(name="light", bg="#ffffff", border="#d0d7de", title="#1f2328",
                  text="#1f2328", muted="#656d76", track="#eaeef2"),
    "dark":  dict(name="dark", bg="#0d1117", border="#30363d", title="#e6edf3",
                  text="#e6edf3", muted="#8b949e", track="#21262d"),
}

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
    ("small-shell", "Unix shell in C: jobs, signals, redirection", "shipped", 1.00),
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

ACTIVITY_DAYS = 30


# ── helpers ───────────────────────────────────────────────────────────────

def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


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
    k = 0.55
    return "#%02x%02x%02x" % tuple(round(c + (255 - c) * k) for c in (r, g, b))


def fade(delay, dur=0.45):
    """Staggered fade-in.

    The element keeps its normal opacity as the base attribute — the animation
    starts from 0 and freezes at 1. If SMIL never runs (a renderer that only
    rasterizes static SVG), the base value shows and the card is merely still
    rather than blank.
    """
    return (f'<animate attributeName="opacity" from="0" to="1" dur="{dur}s" '
            f'begin="{delay:.2f}s" fill="freeze"/>')


def grow(attr, to, delay, dur=0.85):
    return (f'<animate attributeName="{attr}" from="0" to="{to}" dur="{dur}s" '
            f'begin="{delay:.2f}s" fill="freeze" '
            f'calcMode="spline" keySplines="0.22 1 0.36 1" keyTimes="0;1"/>')


def shell(w, h, t, body, defs=""):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" font-family="-apple-system,BlinkMacSystemFont,'
        f'Segoe UI,Helvetica,Arial,sans-serif">'
        f"<defs>{defs}</defs>"
        f'<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="12" '
        f'fill="{t["bg"]}" stroke="{t["border"]}"/>'
        f"{body}</svg>"
    )


def api(url):
    """GET as JSON.

    Unauthenticated GitHub API access is capped at 60 requests/hour and this
    script makes one call per repo, so it uses GITHUB_TOKEN when the workflow
    provides one (5000/hour) and falls back to anonymous locally.
    """
    headers = {"User-Agent": "profile-cards"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=headers)))


# ── data ──────────────────────────────────────────────────────────────────

def fetch_languages():
    repos = api(f"https://api.github.com/users/{USER}/repos?per_page=100")
    totals = {}
    for r in repos:
        if r["fork"] or r["name"] in EXCLUDE_REPOS:
            continue
        for k, v in api(r["languages_url"]).items():
            if k not in EXCLUDE_LANGS:
                totals[k] = totals.get(k, 0) + v
    return sorted(totals.items(), key=lambda kv: -kv[1])


def fetch_activity():
    """Push events per day. The anonymous events API strips per-push commit
    counts, so this counts pushes, not commits — labelled as such on the card.
    """
    events = api(f"https://api.github.com/users/{USER}/events/public?per_page=100")
    per_day = collections.Counter()
    repos = collections.Counter()
    last = None
    for e in events:
        if e["type"] != "PushEvent":
            continue
        day = e["created_at"][:10]
        per_day[day] += 1
        repos[e["repo"]["name"]] += 1
        last = max(last, e["created_at"]) if last else e["created_at"]

    today = dt.date.today()
    series = []
    for i in range(ACTIVITY_DAYS - 1, -1, -1):
        d = today - dt.timedelta(days=i)
        series.append((d, per_day.get(d.isoformat(), 0)))
    return series, repos.most_common(3), last


def fetch_stats(langs, activity):
    u = api(f"https://api.github.com/users/{USER}")
    total = sum(v for _, v in langs) or 1
    top_name, top_val = langs[0] if langs else ("n/a", 0)
    recent = sum(n for _, n in activity)

    return [
        ("Public repos", str(u.get("public_repos", "n/a")), "#58a6ff"),
        ("Languages", str(len(langs)), "#bc8cff"),
        (f"{top_name}", f"{100*top_val/total:.0f}%", "#3572A5"),
        ("Code written", f"{total/1024:.0f} KB", "#3fb950"),
        (f"Pushes, last {ACTIVITY_DAYS}d", str(recent), "#f34b7d"),
        ("On GitHub since", str(u.get("created_at", "----"))[:4], "#d29922"),
    ]


# ── cards ─────────────────────────────────────────────────────────────────

def card_languages(langs, t):
    w, pad = 440, 20
    total = sum(v for _, v in langs) or 1
    shown = langs[:6]

    body = (f'<text x="{pad}" y="34" fill="{t["title"]}" font-size="15" '
            f'font-weight="600">Languages</text>')

    bar_y, bar_w, bar_h = 50, w - 2 * pad, 10
    defs = (f'<clipPath id="bar"><rect x="{pad}" y="{bar_y}" width="{bar_w}" '
            f'height="{bar_h}" rx="5"/></clipPath>'
            f'<clipPath id="reveal"><rect x="{pad}" y="{bar_y}" width="{bar_w}" '
            f'height="{bar_h}">{grow("width", bar_w, 0.15, 1.0)}</rect></clipPath>')

    body += (f'<rect x="{pad}" y="{bar_y}" width="{bar_w}" height="{bar_h}" '
             f'rx="5" fill="{t["track"]}"/>')
    body += '<g clip-path="url(#bar)"><g clip-path="url(#reveal)">'
    x = pad
    for name, val in shown:
        seg = bar_w * val / total
        col = adapt(LANG_COLORS.get(name, "#8b949e"), t["name"])
        body += (f'<rect x="{x:.2f}" y="{bar_y}" width="{seg:.2f}" '
                 f'height="{bar_h}" fill="{col}"/>')
        x += seg
    body += "</g></g>"

    # Percentage sits at a fixed column rather than after the name — estimating
    # text width packed "C++" against "0.3%".
    for i, (name, val) in enumerate(shown):
        col_i, row = i % 2, i // 2
        lx = pad + col_i * (bar_w / 2)
        ly = 88 + row * 26
        pct = 100 * val / total
        dot = adapt(LANG_COLORS.get(name, "#8b949e"), t["name"])
        d = 0.4 + i * 0.07
        body += (f'<g>{fade(d)}'
                 f'<circle cx="{lx+5}" cy="{ly-4}" r="5" fill="{dot}"/>'
                 f'<text x="{lx+18}" y="{ly}" fill="{t["text"]}" font-size="12.5" '
                 f'font-weight="500">{esc(name)}</text>'
                 f'<text x="{lx+150:.0f}" y="{ly}" fill="{t["muted"]}" '
                 f'font-size="12.5" text-anchor="end">{pct:.1f}%</text></g>')

    h = 88 + ((len(shown) + 1) // 2) * 26 + 26
    body += (f'<text x="{pad}" y="{h-12}" fill="{t["muted"]}" font-size="10.5">'
             f'by bytes across public repos · generated and vendored files excluded</text>')
    return shell(w, h, t, body, defs)


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
             f'Where each project actually sits. A status readout, not a roadmap.</text>')

    bar_x, bar_w = 470, 250
    for i, (name, desc, stage, frac) in enumerate(PROJECTS):
        y = top + i * row_h + 22
        c1, c2 = STAGE_COLORS[stage]
        gid = "g" + stage.replace(" ", "")
        delay = 0.2 + i * 0.09

        body += (f'<text x="{pad}" y="{y}" fill="{t["text"]}" font-size="13" '
                 f'font-weight="600">{esc(name)}</text>')
        body += (f'<text x="{pad}" y="{y+15}" fill="{t["muted"]}" font-size="11">'
                 f'{esc(desc)}</text>')

        body += (f'<rect x="{bar_x}" y="{y-9}" width="{bar_w}" height="9" rx="4.5" '
                 f'fill="{t["track"]}"/>')
        body += (f'<rect x="{bar_x}" y="{y-9}" width="{bar_w*frac:.1f}" height="9" rx="4.5" '
                 f'fill="url(#{gid})">{grow("width", f"{bar_w*frac:.1f}", delay)}</rect>')
        body += (f'<text x="{bar_x+bar_w+12}" y="{y}" fill="{t["muted"]}" '
                 f'font-size="11.5" font-weight="500">{fade(delay+0.5)}'
                 f'{int(frac*100)}%</text>')

        px = bar_x + bar_w + 56
        pw = 8 + len(stage) * 6.6
        body += (f'<g>{fade(delay+0.55)}'
                 f'<rect x="{px}" y="{y-13}" width="{pw:.0f}" height="18" rx="9" '
                 f'fill="{c2}" fill-opacity="0.16" stroke="{c2}" '
                 f'stroke-opacity="0.45"/>'
                 f'<text x="{px+pw/2:.0f}" y="{y}" fill="{c1}" font-size="10.5" '
                 f'font-weight="600" text-anchor="middle">{esc(stage)}</text></g>')

    return shell(w, h, t, body, defs)


def card_stats(stats, t):
    w, pad = 900, 24
    cols = 3
    rows = (len(stats) + cols - 1) // cols
    cell_w = (w - 2 * pad) / cols
    cell_h, top = 62, 56

    body = (f'<text x="{pad}" y="34" fill="{t["title"]}" font-size="15" '
            f'font-weight="600">By the numbers</text>')

    for i, (label, value, raw) in enumerate(stats):
        c = adapt(raw, t["name"])
        cx = pad + (i % cols) * cell_w
        cy = top + (i // cols) * cell_h
        body += (f'<g>{fade(0.15 + i * 0.08)}'
                 f'<rect x="{cx}" y="{cy}" width="{cell_w-12:.0f}" height="{cell_h-12}" '
                 f'rx="8" fill="{c}" fill-opacity="0.08" stroke="{c}" '
                 f'stroke-opacity="0.28"/>'
                 f'<text x="{cx+16}" y="{cy+30}" fill="{c}" font-size="21" '
                 f'font-weight="700">{esc(value)}</text>'
                 f'<text x="{cx+16}" y="{cy+44}" fill="{t["muted"]}" '
                 f'font-size="10.5">{esc(label)}</text></g>')

    return shell(w, top + rows * cell_h + 8, t, body)


def card_activity(series, top_repos, last, t):
    w, pad = 900, 24
    top, chart_h = 66, 76
    h = top + chart_h + 46

    peak = max((n for _, n in series), default=0) or 1
    slot = (w - 2 * pad) / len(series)
    bw = slot * 0.62

    body = (f'<text x="{pad}" y="34" fill="{t["title"]}" font-size="15" '
            f'font-weight="600">Recent activity</text>')
    body += (f'<text x="{pad}" y="52" fill="{t["muted"]}" font-size="11.5">'
             f'Pushes per day, last {len(series)} days · live from the public '
             f'events feed</text>')

    base = top + chart_h
    body += (f'<line x1="{pad}" y1="{base+0.5}" x2="{w-pad}" y2="{base+0.5}" '
             f'stroke="{t["border"]}"/>')

    for i, (d, n) in enumerate(series):
        x = pad + i * slot
        bh = 0 if n == 0 else max(4, (chart_h - 10) * n / peak)
        c = "#3fb950" if n else t["track"]
        if n == 0:
            body += (f'<rect x="{x:.1f}" y="{base-3}" width="{bw:.1f}" height="3" '
                     f'rx="1.5" fill="{t["track"]}"/>')
        else:
            body += (f'<rect x="{x:.1f}" y="{base}" width="{bw:.1f}" height="0" '
                     f'rx="2" fill="{c}">'
                     f'<animate attributeName="height" from="0" to="{bh:.1f}" '
                     f'dur="0.7s" begin="{0.2+i*0.02:.2f}s" fill="freeze" '
                     f'calcMode="spline" keySplines="0.22 1 0.36 1" keyTimes="0;1"/>'
                     f'<animate attributeName="y" from="{base}" to="{base-bh:.1f}" '
                     f'dur="0.7s" begin="{0.2+i*0.02:.2f}s" fill="freeze" '
                     f'calcMode="spline" keySplines="0.22 1 0.36 1" keyTimes="0;1"/>'
                     f'</rect>')

    # Month ticks.
    seen = set()
    for i, (d, _) in enumerate(series):
        if d.strftime("%b") not in seen:
            seen.add(d.strftime("%b"))
            body += (f'<text x="{pad+i*slot:.0f}" y="{base+16}" fill="{t["muted"]}" '
                     f'font-size="10">{d.strftime("%b %-d")}</text>')

    foot = "most active: " + ", ".join(
        r.split("/")[-1] for r, _ in top_repos) if top_repos else ""
    if last:
        foot += f"  ·  last push {last[:10]}"
    body += (f'<text x="{pad}" y="{h-14}" fill="{t["muted"]}" font-size="10.5">'
             f'{fade(1.0)}{esc(foot)}</text>')

    return shell(w, h, t, body)


def card_focus(t):
    w, pad = 440, 20
    body = (f'<text x="{pad}" y="34" fill="{t["title"]}" font-size="15" '
            f'font-weight="600">Focus areas</text>')

    x, y = pad, 58
    for i, (label, raw) in enumerate(FOCUS):
        color = adapt(raw, t["name"])
        pw = 20 + len(label) * 6.5
        if x + pw > w - pad:
            x, y = pad, y + 30
        body += (f'<g>{fade(0.2 + i * 0.06)}'
                 f'<rect x="{x}" y="{y-14}" width="{pw:.0f}" height="22" rx="11" '
                 f'fill="{color}" fill-opacity="0.15" stroke="{color}" '
                 f'stroke-opacity="0.5"/>'
                 f'<text x="{x+pw/2:.0f}" y="{y+1}" fill="{color}" font-size="11.5" '
                 f'font-weight="600" text-anchor="middle">{esc(label)}</text></g>')
        x += pw + 8

    return shell(w, y + 30, t, body)


def main():
    OUT.mkdir(exist_ok=True)
    langs = fetch_languages()
    series, top_repos, last = fetch_activity()
    stats = fetch_stats(langs, series)
    print("languages:", langs[:6])
    print("stats:", [(l, v) for l, v, _ in stats])
    print("activity: %d pushes over %d days" % (sum(n for _, n in series), len(series)))

    for theme, t in THEMES.items():
        for name, svg in (
            ("languages", card_languages(langs, t)),
            ("projects", card_projects(t)),
            ("focus", card_focus(t)),
            ("stats", card_stats(stats, t)),
            ("activity", card_activity(series, top_repos, last, t)),
        ):
            # Parse before writing — a malformed card renders as a broken
            # image on the profile, which is worse than an unchanged one.
            xml.dom.minidom.parseString(svg)
            (OUT / f"{name}-{theme}.svg").write_text(svg)
            print("wrote", f"{name}-{theme}.svg", len(svg), "bytes")


if __name__ == "__main__":
    main()
