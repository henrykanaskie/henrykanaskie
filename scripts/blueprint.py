#!/usr/bin/env python3
"""Drawing primitives shared by every card.

The cards are meant to read as sheets of one drawing set rather than five
unrelated widgets, so everything that carries the visual identity lives here and
nothing in cards.py invents its own frame, rule weight, or colour.

Two grounds, picked by the README with <picture> and prefers-color-scheme:

    vellum      warm paper, dark ink       (GitHub's light theme)
    cyanotype   deep navy, pale cyan ink   (GitHub's dark theme)

Cyanotype is the reason this works as a dark theme at all. A blueprint is
already a light-on-dark medium, so the dark variant is the historically correct
one and the light variant is the drafting-vellum original. Neither is a tinted
copy of the other.

Motion: cards animate on load with SMIL (<animate>), which is the one form of
animation GitHub's markdown pipeline preserves. An SVG referenced by <img> is
rendered non-interactively, so CSS :hover and <script> are inert, but
declarative animation still runs. Every animated element carries its final value
as the base attribute and animates to it with fill="freeze", so a renderer that
only rasterizes static SVG shows the finished drawing rather than a blank one.
"""

from __future__ import annotations

# Monospace only, and only families that ship with the OS. An SVG loaded through
# <img> cannot fetch a webfont, so anything not already installed silently falls
# back. Naming real stacks is the whole of font handling here.
MONO = ("ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,"
        "'DejaVu Sans Mono',monospace")

GROUNDS = {
    # ── vellum: ink on warm paper ────────────────────────────────────────────
    "light": dict(
        name="light", sheet="vellum",
        ground="#fbf9f4",     # paper
        ink="#16202b",        # primary linework and lettering
        soft="#5c6873",       # dimensions, secondary lettering
        faint="#8d8577",      # sheet furniture: zone letters, tick labels
        rule="#c9c0b0",       # frame and table rules
        grid="#e9e2d4",       # graph grid
        fill="#efe9dc",       # unfilled track / hatch ground
        accent="#1f6feb",     # the one saturated blue
        red="#c0392b",        # revision marks only
        green="#1a7f45",
        amber="#b07503",
    ),
    # ── cyanotype: pale cyan on deep navy ───────────────────────────────────
    "dark": dict(
        name="dark", sheet="cyanotype",
        ground="#0b141d",
        ink="#d7e6f2",
        soft="#8ba3b8",
        faint="#5d788f",
        rule="#27415a",
        grid="#152331",
        fill="#152331",
        accent="#4da3ff",
        red="#ff6b5e",
        green="#3fb950",
        amber="#d29922",
    ),
}

def esc(s) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


# ── motion ───────────────────────────────────────────────────────────────────

def fade(delay: float, dur: float = 0.4) -> str:
    """Staggered fade-in that freezes at full opacity."""
    return (f'<animate attributeName="opacity" from="0" to="1" dur="{dur}s" '
            f'begin="{delay:.2f}s" fill="freeze"/>')


def grow(attr: str, to: float, delay: float, dur: float = 0.8) -> str:
    """Ease-out growth of a single attribute, from zero to its final value."""
    return (f'<animate attributeName="{attr}" from="0" to="{to:.2f}" '
            f'dur="{dur}s" begin="{delay:.2f}s" fill="freeze" calcMode="spline" '
            f'keySplines="0.22 1 0.36 1" keyTimes="0;1"/>')


def draw_on(length: float, delay: float, dur: float = 0.9) -> str:
    """Trace a stroke as if it were being drawn.

    Applied to a path whose stroke-dasharray is its own length: animating the
    offset from `length` to 0 walks the ink along the path. This is the effect
    the whole aesthetic rests on, so it is worth the two extra attributes.
    """
    return (f'<animate attributeName="stroke-dashoffset" from="{length:.1f}" '
            f'to="0" dur="{dur}s" begin="{delay:.2f}s" fill="freeze" '
            f'calcMode="spline" keySplines="0.3 0.9 0.3 1" keyTimes="0;1"/>')


# ── lettering ────────────────────────────────────────────────────────────────

def text(x, y, s, t, *, size=11, color="ink", weight=400, anchor="start",
         track=0.0, opacity=None, anim="") -> str:
    """A run of monospace lettering.

    `track` is letter-spacing in px. Drawing lettering is spaced out, and the
    caps runs in this set are tracked between 0.5 and 1.6.
    """
    op = "" if opacity is None else f' opacity="{opacity}"'
    tr = "" if not track else f' letter-spacing="{track}"'
    return (f'<text x="{x:.1f}" y="{y:.1f}" fill="{t[color]}" '
            f'font-size="{size}" font-weight="{weight}" text-anchor="{anchor}"'
            f'{tr}{op}>{anim}{esc(s)}</text>')


def caps(x, y, s, t, **kw) -> str:
    """Lettering in caps with drawing-standard tracking."""
    kw.setdefault("track", 1.2)
    kw.setdefault("size", 9.5)
    kw.setdefault("color", "faint")
    return text(x, y, str(s).upper(), t, **kw)


# ── linework ─────────────────────────────────────────────────────────────────

def rule(x1, y1, x2, y2, t, *, color="rule", w=1.0, dash=None, opacity=1.0,
         anim="") -> str:
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="{t[color]}" stroke-width="{w}"{d} '
            f'opacity="{opacity}">{anim}</line>')


def dim(x1, x2, y, label, t, *, color="soft", size=8.5, above=True) -> str:
    """A dimension line: tick, extension, run, value, run, extension, tick.

    The value sits in a gap cut out of the middle of the run, the way a
    dimension is actually annotated, rather than floating above an unbroken
    line. Width of the gap is measured from the label, so it fits the text.
    """
    c = t[color]
    mid = (x1 + x2) / 2
    gap = max(14.0, len(str(label)) * size * 0.62) / 2 + 4
    ty = y - 4 if above else y + size + 2
    seg = ""
    if mid - gap > x1:
        seg += (f'<line x1="{x1:.1f}" y1="{y:.1f}" x2="{mid-gap:.1f}" '
                f'y2="{y:.1f}" stroke="{c}" stroke-width="0.9"/>')
    if mid + gap < x2:
        seg += (f'<line x1="{mid+gap:.1f}" y1="{y:.1f}" x2="{x2:.1f}" '
                f'y2="{y:.1f}" stroke="{c}" stroke-width="0.9"/>')
    for x in (x1, x2):                       # end ticks, drafting-style slashes
        seg += (f'<line x1="{x-2.5:.1f}" y1="{y+3.5:.1f}" x2="{x+2.5:.1f}" '
                f'y2="{y-3.5:.1f}" stroke="{c}" stroke-width="1.1"/>')
    seg += (f'<text x="{mid:.1f}" y="{ty:.1f}" fill="{c}" font-size="{size}" '
            f'text-anchor="middle" letter-spacing="0.4">{esc(label)}</text>')
    return seg


def leader(x1, y1, x2, y2, t, *, color="soft", w=0.9) -> str:
    """A leader line with a dot at the thing it points at."""
    return (f'<g><circle cx="{x1:.1f}" cy="{y1:.1f}" r="1.8" fill="{t[color]}"/>'
            f'<path d="M{x1:.1f} {y1:.1f} L{x2:.1f} {y2:.1f}" '
            f'stroke="{t[color]}" stroke-width="{w}" fill="none"/></g>')


def balloon(x, y, s, t, *, r=9, color="soft") -> str:
    """A circled callout number, as used to key a part to its BOM row."""
    return (f'<g><circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{t["ground"]}" '
            f'stroke="{t[color]}" stroke-width="1"/>'
            f'<text x="{x:.1f}" y="{y+3.2:.1f}" fill="{t[color]}" font-size="9" '
            f'text-anchor="middle" font-weight="600">{esc(s)}</text></g>')


def revcloud(x, y, w, h, t, *, delay=0.0, scallop=7.0) -> str:
    """A revision cloud: the scalloped outline drafters draw around whatever
    changed since the last issue of the sheet.

    Always red, on both grounds, because that is the one thing a revision mark
    is. It is drawn on rather than faded in, so it reads as annotation added
    after the fact instead of part of the original linework.
    """
    pts, per = [], max(1, int(w / scallop))
    step_x, step_y = w / per, h / max(1, int(h / scallop))
    per_y = max(1, int(h / scallop))
    for i in range(per):                       # top, left to right
        pts.append((x + i * step_x, y, step_x, 0))
    for i in range(per_y):                     # right, top to bottom
        pts.append((x + w, y + i * step_y, 0, step_y))
    for i in range(per):                       # bottom, right to left
        pts.append((x + w - i * step_x, y + h, -step_x, 0))
    for i in range(per_y):                     # left, bottom to top
        pts.append((x, y + h - i * step_y, 0, -step_y))

    d = f"M{x:.1f} {y:.1f}"
    for px, py, dx, dy in pts:
        # Each scallop is a half-circle bulging outward from the rectangle.
        d += f" A {abs(dx or dy)/2:.1f} {abs(dx or dy)/2:.1f} 0 0 1 {px+dx:.1f} {py+dy:.1f}"
    length = 2 * (w + h) * 1.6                 # arcs are longer than the chord
    return (f'<path d="{d}" fill="none" stroke="{t["red"]}" stroke-width="1.1" '
            f'stroke-linecap="round" stroke-dasharray="{length:.0f}" '
            f'stroke-dashoffset="0">{draw_on(length, delay, 1.1)}</path>')


# ── fills ────────────────────────────────────────────────────────────────────

def defs_hatch(idx: int, color: str, *, angle=45, gap=5, w=0.9) -> str:
    """A section-hatch pattern. Section lining is how a drawing shows material,
    so filled regions here are hatched rather than flooded with colour."""
    return (f'<pattern id="h{idx}" patternUnits="userSpaceOnUse" '
            f'width="{gap}" height="{gap}" '
            f'patternTransform="rotate({angle})">'
            f'<line x1="0" y1="0" x2="0" y2="{gap}" stroke="{color}" '
            f'stroke-width="{w}"/></pattern>')


def defs_grid(t, gap=8) -> str:
    """The faint graph grid the whole sheet sits on."""
    return (f'<pattern id="grid" patternUnits="userSpaceOnUse" '
            f'width="{gap}" height="{gap}">'
            f'<path d="M{gap} 0 L0 0 0 {gap}" fill="none" stroke="{t["grid"]}" '
            f'stroke-width="0.6"/></pattern>')


# ── the sheet ────────────────────────────────────────────────────────────────

def zone_marks(w, h, t, *, inset=12, pitch=88) -> str:
    """Zone letters down the sides and numbers across the top and bottom.

    Every real engineering sheet is gridded into zones so a note can say "see
    detail B3". Nothing here references a zone. They are furniture, and they
    are what makes the frame read as a drawing at a glance rather than a box.
    """
    out = ""
    cols = max(2, int((w - 2 * inset) / pitch))
    rows = max(2, int((h - 2 * inset) / pitch))
    cw, rh = (w - 2 * inset) / cols, (h - 2 * inset) / rows
    for i in range(cols):
        cx = inset + cw * (i + 0.5)
        for y in (inset - 3.5, h - inset + 8.5):
            out += caps(cx, y, i + 1, t, size=7, anchor="middle", track=0,
                        opacity=0.75)
        if i:                                  # tick between zones
            x = inset + cw * i
            out += rule(x, 0, x, inset, t, w=0.7, opacity=0.5)
            out += rule(x, h - inset, x, h, t, w=0.7, opacity=0.5)
    for j in range(rows):
        cy = inset + rh * (j + 0.5) + 2.5
        for x in (inset - 4.5, w - inset + 4.5):
            out += caps(x, cy, chr(65 + j), t, size=7, anchor="middle", track=0,
                        opacity=0.75)
        if j:
            y = inset + rh * j
            out += rule(0, y, inset, y, t, w=0.7, opacity=0.5)
            out += rule(w - inset, y, w, y, t, w=0.7, opacity=0.5)
    return out


def sheet(w, h, t, body, *, defs="", label=None, sheet_no=None, grid=True,
          zones=True, inset=12) -> str:
    """Wrap card content in the drawing frame.

    The frame is a double border: an outer trim edge and an inner drawing
    border with the zone strip between them. Four rectangles, and they do more
    to make the card read as a drawing than anything else here.
    """
    d = defs_grid(t) + defs
    out = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
           f'viewBox="0 0 {w} {h}" font-family="{MONO}" role="img">'
           f"<defs>{d}</defs>")

    out += (f'<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="4" '
            f'fill="{t["ground"]}" stroke="{t["rule"]}" stroke-width="1"/>')
    if grid:
        out += (f'<rect x="{inset}" y="{inset}" width="{w-2*inset}" '
                f'height="{h-2*inset}" fill="url(#grid)" opacity="0.85"/>')
    if zones:
        out += zone_marks(w, h, t, inset=inset)
    out += (f'<rect x="{inset}.5" y="{inset}.5" width="{w-2*inset-1}" '
            f'height="{h-2*inset-1}" fill="none" stroke="{t["rule"]}" '
            f'stroke-width="1.2"/>')

    # Corner registration ticks, drawn into the drawing area.
    for cx, cy, sx, sy in ((inset, inset, 1, 1), (w - inset, inset, -1, 1),
                           (inset, h - inset, 1, -1), (w - inset, h - inset, -1, -1)):
        out += (f'<path d="M{cx+sx*7:.1f} {cy:.1f} L{cx:.1f} {cy:.1f} '
                f'L{cx:.1f} {cy+sy*7:.1f}" fill="none" stroke="{t["ink"]}" '
                f'stroke-width="1.4" opacity="0.55"/>')

    if label:
        out += caps(inset + 10, inset + 15, label, t, size=8, track=1.6,
                    color="faint")
    if sheet_no:
        out += caps(w - inset - 10, h - inset - 8, sheet_no, t, size=7.5,
                    anchor="end", track=1.2, color="faint")

    return out + body + "</svg>"


def not_for_issue(w, h, t, *, note="SAMPLE DATA") -> str:
    """The stamp drafters put on a drawing that must not be built from.

    This exists because `--offline` does not blank the telemetry. It substitutes
    plausible sample values (a language mix, a crew count, an ISS fix) so layout
    can be worked on without burning rate limit. Those numbers look real at a
    glance, and a sheet whose entire claim is that every figure is measured
    cannot afford to ship invented ones because someone iterated on spacing and
    committed the result.

    So an offline build is stamped, the way a preliminary drawing is stamped, and
    the stamp is the loudest thing on the card.
    """
    cx, cy = w / 2, h / 2
    return (
        f'<g transform="rotate(-24 {cx:.1f} {cy:.1f})" opacity="0.9">'
        f'<rect x="{cx-190:.1f}" y="{cy-34:.1f}" width="380" height="68" rx="4" '
        f'fill="{t["ground"]}" fill-opacity="0.82" stroke="{t["red"]}" '
        f'stroke-width="3"/>'
        f'<text x="{cx:.1f}" y="{cy-4:.1f}" fill="{t["red"]}" font-size="26" '
        f'font-weight="700" text-anchor="middle" letter-spacing="3">'
        f'NOT FOR ISSUE</text>'
        f'<text x="{cx:.1f}" y="{cy+20:.1f}" fill="{t["red"]}" font-size="12" '
        f'text-anchor="middle" letter-spacing="2">{esc(note)}</text></g>')


def field(x, y, w, key, val, t, *, size=10, kh=11) -> str:
    """One boxed field of a title block: small caps key over a larger value."""
    return (caps(x + 6, y + kh, key, t, size=6.8, track=1.1, color="faint")
            + text(x + 6, y + kh + size + 6, val, t, size=size, weight=600,
                   color="ink", track=0.3))
