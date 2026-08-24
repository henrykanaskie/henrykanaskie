#!/usr/bin/env python3
"""The sheets of the drawing set.

blueprint.py owns the look. Frame, grounds, rule weights, and motion all live
there. This module owns the *layout*: what goes on each sheet and where. Nothing
here invents a colour or a border; if a card needs a mark that isn't a blueprint
primitive, that is a sign the primitive is missing rather than a licence to draw
it locally.

    CARDS                       the sheet names, in sheet order
    render(name, cfg, data, t)  -> a complete SVG document string
    todays_note(cfg, data)      -> the day's field note, shared with build.py

Three rules run through every card:

1.  Heights are computed, never assumed. A BOM of two parts and a BOM of twenty
    are both correct sheets; a card sized for nine projects that clips the tenth
    is not. Every layout here accumulates y downward and the frame closes under
    whatever it ended up with.

2.  Missing data draws as a voided field. Any channel can be down: the launch
    API, the ISS API, GitHub, all of it. The honest drafting answer to an empty
    field is a dashed box reading NO DATA. Never a fabricated value, and never
    a card left off the set. The one exception is the audio channel, which is
    off by configuration rather than broken, so it is omitted entirely.

3.  Nothing on these sheets is a joke. The character is supposed to come from
    real mechanisms doing something charming with true data: completion drawn
    as an actual dimension, the ISS track drawn from the orbit's real
    inclination, each material given its own section hatch.

Text metrics: an SVG loaded through <img> cannot measure text, so column fits
are computed from the monospace advance width (0.60 em for every family in
blueprint.MONO). That is exact for monospace and is the only reason fitting
long repository names into fixed columns works without a rendering pass.
"""

from __future__ import annotations

import math

try:                                    # scripts/ on sys.path (build.py's case)
    import blueprint as bp
except ModuleNotFoundError:             # imported as part of a package
    from . import blueprint as bp

esc, text, caps = bp.esc, bp.text, bp.caps
rule, dim, balloon, revcloud = bp.rule, bp.dim, bp.balloon, bp.revcloud
fade, grow, draw_on = bp.fade, bp.grow, bp.draw_on
sheet, field, defs_hatch = bp.sheet, bp.field, bp.defs_hatch

CARDS = ["titleblock", "general", "bom", "telemetry", "composition",
         "activity", "notes"]


def _sheet_no(name: str) -> str:
    """`SH n / total`, derived from the card's own place in CARDS.

    Written out by hand this goes wrong the moment a sheet is added or the set
    is reordered, and a sheet numbered 3 of 5 in a set of seven is the kind of
    error that makes a reader distrust every other figure on the drawing.
    """
    return f"SH {CARDS.index(name) + 1} / {len(CARDS)}"


# ── shared metrics ───────────────────────────────────────────────────────────

CW = 0.60          # monospace advance, as a fraction of font-size
INSET = 12         # must match blueprint.sheet's frame inset
DASH = "N/A"  # what a field with no value letters as

# Delay bands. The sheet is supposed to assemble the way it would be drawn:
# frame first (it is static, so it is simply there), then the rules that carve
# the sheet up, then the lettering, then the data the lettering is about.
D_RULE, D_LETTER, D_DATA = 0.10, 0.30, 0.58

# Section-hatch angles, in the order materials get assigned them. Adjacent
# angles are far apart so two neighbouring segments never read as one region.
# That is also what keeps the composition card legible in greyscale.
HATCH_ANGLES = (45, 135, 0, 90, 30, 120, 60, 15)

# Status colours are assigned by rank within the configured vocabulary rather
# than by matching key names, so renaming a status in profile.toml does not
# silently drop it to the fallback colour.
STATUS_COLORS = ("green", "accent", "amber", "faint")


def _w(s, size, track=0.0) -> float:
    """Rendered width of a monospace run, in px."""
    n = len(str(s))
    return n * size * CW + max(0, n - 1) * track


def _fit(s, px, size, track=0.0) -> str:
    """Truncate a run to fit `px`, with an ellipsis only when it has to cut."""
    s = str(s)
    if _w(s, size, track) <= px:
        return s
    per = size * CW + track
    n = max(1, int((px - size * CW) / per))
    return s[:n].rstrip() + "…"


def _chars_per_line(px, size, track=0.0) -> int:
    """How many characters of a monospace run fit in `px`.

    A run of k characters is k advances wide with the tracking between them,
    so k*(size*CW + track) - track <= px. Solved for k.
    """
    per = size * CW + track
    return max(1, int((px + track) / per)) if per > 0 else 1


def _wrap_spans(s, px, size, track=0.0):
    """Word-wrap `s` to `px`, as (start, end) index pairs into `s`.

    Indices rather than strings because the caller may be carrying a parallel
    per-character mask (which characters were bold) that has to stay aligned
    with the text after wrapping.
    """
    n = _chars_per_line(px, size, track)
    spans, i, L = [], 0, len(s)
    while i < L:
        while i < L and s[i] == " ":
            i += 1                       # a wrapped line never opens on a space
        if i >= L:
            break
        end = min(L, i + n)
        if end < L and s[end] != " ":
            brk = s.rfind(" ", i, end)
            # No break point means one word is longer than the whole line, and
            # the only options are a hard cut or an overflowing sheet.
            if brk > i:
                end = brk
        j = end
        while j > i and s[j - 1] == " ":
            j -= 1
        spans.append((i, j))
        i = end
    return spans


def _wrap(s, px, size, track=0.0):
    """Word-wrap `s` to `px`, as a list of lines."""
    return [s[a:b] for a, b in _wrap_spans(s, px, size, track)]


def _demark(s):
    """Strip markdown `**bold**` markers, keeping track of what was inside.

    Returns the plain text and a per-character flag saying whether that
    character was emphasised. The markers must not survive to the sheet, and
    neither must the emphasis be lost, so the two are separated here and put
    back together as weighted runs at draw time.
    """
    plain, mask, bold, i = [], [], False, 0
    s = str(s)
    while i < len(s):
        if s[i:i + 2] == "**":
            bold = not bold
            i += 2
            continue
        plain.append(s[i])
        mask.append(bold)
        i += 1
    return "".join(plain), mask


def _mask_runs(mask, a, b):
    """Group mask[a:b] into (start, end, bold) runs of one weight each."""
    runs, i = [], a
    while i < b:
        j = i
        while j < b and mask[j] == mask[i]:
            j += 1
        runs.append((i, j, mask[i]))
        i = j
    return runs


def _fit_size(s, px, size, track_ratio=0.10, floor=11) -> float:
    """Shrink a headline until it fits its column. Long names must not clip."""
    while size > floor and _w(s, size, size * track_ratio) > px:
        size -= 1
    return size


def _g(delay, body, dur=0.4) -> str:
    """Group + staggered fade. Base opacity is the final value, so a static
    rasterizer shows the finished drawing rather than an empty sheet."""
    return f'<g opacity="1">{fade(delay, dur)}{body}</g>'


def _drawn_rule(x1, y1, x2, y2, t, delay, *, dur=0.7, **kw) -> str:
    """A rule that traces itself. The dasharray is the line's own length, so
    the static value (offset 0) is an unbroken line."""
    length = math.hypot(x2 - x1, y2 - y1)
    return rule(x1, y1, x2, y2, t, dash=f"{length:.1f}",
                anim=draw_on(length, delay, dur), **kw)


def _nodata(x, y, w, h, t, *, delay=D_DATA, label="NO DATA") -> str:
    """A voided field: dashed box, one diagonal, and the reason it is empty."""
    body = (f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" '
            f'fill="none" stroke="{t["faint"]}" stroke-width="0.9" '
            f'stroke-dasharray="4 3" opacity="0.7"/>')
    body += rule(x, y + h, x + w, y, t, color="faint", w=0.6, dash="3 4",
                 opacity=0.28)
    body += caps(x + w / 2, y + h / 2 + 3.4, label, t, size=8.5,
                 anchor="middle", track=1.5, color="faint")
    return _g(delay, body)


def _grow_bar(x, y, w, h, fill, delay, *, stroke=None, sw=0.8) -> str:
    """A bar that grows rightward from its left edge, ending at its base width."""
    st = "" if stroke is None else f' stroke="{stroke}" stroke-width="{sw}"'
    return (f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.2f}" height="{h:.1f}" '
            f'fill="{fill}"{st}>{grow("width", w, delay)}</rect>')


def _grow_col(x, base, w, h, fill, delay) -> str:
    """A column that grows upward off the axis.

    grow() animates one attribute from zero, which is wrong for a rect anchored
    at its bottom: growing height alone extends it downward. So y is animated
    alongside it. Both keep their final value as the base attribute.
    """
    y = base - h
    a = (f'<animate attributeName="y" from="{base:.1f}" to="{y:.1f}" dur="0.8s" '
         f'begin="{delay:.2f}s" fill="freeze" calcMode="spline" '
         f'keySplines="0.22 1 0.36 1" keyTimes="0;1"/>')
    return (f'<rect x="{x:.2f}" y="{y:.1f}" width="{w:.2f}" height="{h:.1f}" '
            f'fill="{fill}">{a}{grow("height", h, delay)}</rect>')


def _numbered_note(x, y, px, num, s, t, delay, *, size=10.5, lead=15.5,
                   gutter=None, color="ink"):
    """One numbered note, hung off its number. Returns (svg, y after the note).

    Continuation lines indent past the number instead of running back to the
    margin, which is how a numbered note is set on a real sheet and the only
    way the reader can tell where note 2 stops and note 3 starts.

    `s` may carry markdown bold markers. They are stripped and redrawn as
    weighted runs laid end to end at measured x, so the emphasis survives and
    the markers do not.
    """
    # Whitespace is collapsed before the markers are read, because SVG collapses
    # runs of spaces inside a <text> as well, and a run measured with two spaces
    # that draws with one puts every later run on the line out of position.
    plain, mask = _demark(" ".join(str(s).split()))
    g = _w(f"{num} ", size) if gutter is None else gutter
    spans = _wrap_spans(plain, px - g, size)
    body = text(x, y, num, t, size=size, color=color)
    for k, (a, b) in enumerate(spans):
        xx, yy = x + g, y + k * lead
        for rs, re_, bold in _mask_runs(mask, a, b):
            run = plain[rs:re_]
            # A <text> drops its own leading space, so the space that follows a
            # bold run would close the gap between the two words. The advance is
            # measured on the full run and the space is spent as an offset
            # instead, which keeps the runs abutting at the right distance.
            drawn = run.strip(" ")
            if drawn:
                lead_px = (len(run) - len(run.lstrip(" "))) * size * CW
                body += text(xx + lead_px, yy, drawn, t, size=size, color=color,
                             weight=600 if bold else 400)
            xx += _w(run, size)
    return _g(delay, body), y + max(1, len(spans)) * lead


# ── formatting ───────────────────────────────────────────────────────────────

def _datestr(v, fmt="%Y-%m-%d") -> str | None:
    """Dates arrive as datetimes, but tolerate strings so a cached payload that
    round-tripped through JSON still letters correctly."""
    if v is None:
        return None
    if hasattr(v, "strftime"):
        return v.strftime(fmt)
    s = str(v)
    return s[:10] if fmt == "%Y-%m-%d" else s


def _ago(then, now) -> str | None:
    """Humanised age, coarse on purpose: nobody reads a push age to the second."""
    if then is None or now is None or not hasattr(then, "strftime"):
        return None
    try:
        secs = (now - then).total_seconds()
    except TypeError:                    # naive/aware mismatch, not worth a crash
        return None
    if secs < 0:
        secs = 0
    m, h = int(secs // 60) % 60, int(secs // 3600)
    if h < 1:
        return f"{m}m ago"
    if h < 24:
        return f"{h}h {m:02d}m ago"
    return f"{h // 24}d {h % 24:02d}h ago"


def _countdown(net, now) -> str | None:
    """`T− 02d 14h 09m`, or T+ once the window has opened. A launch that
    already flew is still the correct answer to "next launch" for a few hours,
    so the sign flips rather than the panel voiding."""
    if net is None or now is None or not hasattr(net, "strftime"):
        return None
    try:
        secs = (net - now).total_seconds()
    except TypeError:
        return None
    sign = "−" if secs >= 0 else "+"
    secs = abs(secs)
    d, rem = divmod(int(secs), 86400)
    h, rem = divmod(rem, 3600)
    return f"T{sign} {d:02d}d {h:02d}h {rem // 60:02d}m"


def _bytes(n) -> str:
    if not n:
        return DASH
    n = float(n)
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} GB"


def _pct(x, places=0) -> str:
    return f"{x * 100:.{places}f}%"


def _repo_name(s) -> str:
    """`owner/repo` and `repo` both name the same part."""
    return str(s or "").rstrip("/").split("/")[-1]


# ── configuration readers ────────────────────────────────────────────────────

def _ground_idx(t) -> int:
    """Palette entries are [light, dark]. Index by the ground we are drawing."""
    return 0 if t.get("name") == "light" else 1


def _lang_color(cfg, lang, t, spare_at=0):
    pal = ((cfg.get("palette") or {}).get("lang") or {})
    i = _ground_idx(t)
    pair = pal.get(lang)
    if not pair:
        spares = (cfg.get("palette") or {}).get("spare") or []
        pair = spares[spare_at % len(spares)] if spares else [t["accent"]] * 2
    return pair[i] if len(pair) > i else pair[0]


def _status_map(cfg) -> dict:
    """key -> (rank, entry), ranked by floor descending."""
    st = sorted((cfg.get("status") or []),
                key=lambda s: -float(s.get("floor") or 0.0))
    return {str(s.get("key")): (i, s) for i, s in enumerate(st)}


# ── bill of materials geometry, shared ────────────────────────────────────────────────
#
# The revision table on sheet 1 cites zones on the BOM sheet, so the two have
# to agree about where a part sits. These constants are the single source of
# that agreement. _bom_zone() derives the zone from the same numbers the BOM
# actually lays itself out with, so the citation is true rather than plausible.

BOM_W = 900
BOM_X0, BOM_X1 = 26, 874
BOM_HEAD_Y = 58                 # header lettering baseline
BOM_HEAD_RULE = 64
BOM_BODY_Y = 66                 # top of the first row
BOM_ROW_H = 50
COL_ITEM = 46                   # balloon centre
COL_PN = 66
COL_DESC, COL_DESC_R = 108, 508
COL_MATL = 516
COL_STAT = 632
COL_COMP0, COL_COMP1 = 726, 866

SUMMARY_SIZE = 8.2


def summary_capacity() -> int:
    """How many characters of `summary` the BOM description column holds.

    Exported so build.py can reject an over-long summary during validation
    instead of letting it reach the sheet as a silent ellipsis. A truncated
    description is the one failure here that looks deliberate. Nothing about
    "…the not…" says "your config is too long". That is worth failing the build
    over, and the check belongs next to the metrics it depends on rather than
    living as a magic number in the validator.
    """
    return int((COL_DESC_R - COL_DESC) / (SUMMARY_SIZE * CW))


def _bom_height(n_rows: int) -> int:
    # The 54 is the footer band: the status legend, plus clearance for the
    # sheet number blueprint.sheet() writes into the bottom-right corner.
    return BOM_BODY_Y + max(1, n_rows) * BOM_ROW_H + 54


def _bom_zone(cfg, repo, sheet_no=None) -> str:
    """Zone reference for a part on the BOM sheet, e.g. `3-C1`.

    Recomputes blueprint.zone_marks' own division of the sheet (inset 12, pitch
    88) against the BOM's real height, so the letter is the zone the part is
    genuinely drawn in.

    The sheet number comes from the BOM's own place in CARDS. A citation that
    names the wrong sheet is worse than no citation, and adding a sheet ahead
    of the BOM is exactly the edit that would break a literal.
    """
    if sheet_no is None:
        sheet_no = CARDS.index("bom") + 1
    projects = cfg.get("projects") or []
    idx = next((i for i, p in enumerate(projects)
                if str(p.get("name", "")).casefold() == str(repo).casefold()),
               None)
    if idx is None:
        return DASH
    h = _bom_height(len(projects))
    rows = max(2, int((h - 2 * INSET) / 88))
    rh = (h - 2 * INSET) / rows
    cy = BOM_BODY_Y + idx * BOM_ROW_H + BOM_ROW_H / 2
    j = min(rows - 1, max(0, int((cy - INSET) / rh)))
    cols = max(2, int((BOM_W - 2 * INSET) / 88))
    cw = (BOM_W - 2 * INSET) / cols
    k = min(cols - 1, max(0, int((COL_PN - INSET) / cw)))
    return f"{sheet_no}-{chr(65 + j)}{k + 1}"


# ── sheet 1: title block ─────────────────────────────────────────────────────

def _rev_rows(cfg, data, n=3):
    """The three most recent pushes, as revision rows.

    A revision block records what changed and where. Pushes are the only real
    change record this repository has, so the most recent one becomes the
    current revision letter and the ones behind it step back through the
    alphabet. Only the newest push carries a timestamp, because the API does not
    date the rest. An undated revision row letters as N/A rather than an
    invented date.
    """
    ident = cfg.get("identity") or {}
    rev = str(ident.get("revision") or "A").strip()[:1].upper()
    lp = data.get("last_push") or {}

    order, seen = [], set()
    for cand in ([lp.get("repo")] if lp.get("repo") else []) + \
                [nm for nm, _c in (data.get("top_repos") or [])]:
        name = _repo_name(cand)
        if name and name.casefold() not in seen:
            seen.add(name.casefold())
            order.append(name)

    rows = []
    for i, name in enumerate(order[:n]):
        letter = chr(max(65, ord(rev) - i)) if rev.isalpha() else rev
        date = _datestr(lp.get("at")) if i == 0 else None
        rows.append((letter, _bom_zone(cfg, name), name, date))
    while len(rows) < n:
        rows.append(None)                # a blank revision block still gets rows
    return rows


def _titleblock(cfg, data, t):
    W = 900
    ident = cfg.get("identity") or {}
    x0, x1 = 26, 874
    lcol_r = 512                          # left column stops well clear of the
    rev_x0 = 548                          # revision table's first rule

    out = ""

    # ── left: who the drawing is by ─────────────────────────────────────────
    name = str(ident.get("name") or DASH)
    nsize = _fit_size(name, lcol_r - x0, 36, 0.10, floor=16)
    name_base = 92
    out += _g(D_LETTER, text(x0, name_base, name.upper(), t, size=nsize,
                             weight=700, track=nsize * 0.10), dur=0.55)

    y = name_base + 24
    title = str(ident.get("title") or "").strip()
    if title:
        out += _g(D_LETTER + 0.10,
                  caps(x0, y, _fit(title, lcol_r - x0, 11, 1.4), t, size=11,
                       track=1.4, color="soft"))
        y += 19
    tagline = str(ident.get("tagline") or "").strip()
    if tagline:
        out += _g(D_LETTER + 0.16,
                  text(x0, y, _fit(tagline, lcol_r - x0, 8.6), t, size=8.6,
                       color="soft"))
        y += 17
    links = " · ".join(s for s in (
        (f"github.com/{ident['github']}" if ident.get("github") else ""),
        str(ident.get("website") or "").replace("https://", ""),
    ) if s)
    if links:
        out += _g(D_LETTER + 0.22,
                  caps(x0, y, _fit(links, lcol_r - x0, 7.6, 0.9), t, size=7.6,
                       track=0.9, color="faint"))
        y += 14
    left_bottom = y

    # ── right: revision history ─────────────────────────────────────────────
    rev_head, rev_rule = 58, 64
    rrow_h = 22
    cols = ((rev_x0 + 6, "REV", 30), (rev_x0 + 44, "ZONE", 56),
            (rev_x0 + 108, "DESCRIPTION", 150))
    out += _g(D_LETTER, "".join(
        caps(cx, rev_head, key, t, size=7, track=1.1) for cx, key, _w_ in cols))
    out += _g(D_LETTER, caps(x1, rev_head, "DATE", t, size=7, track=1.1,
                             anchor="end"))
    out += _drawn_rule(rev_x0, rev_rule, x1, rev_rule, t, D_RULE, w=1.4,
                       color="rule")

    rows = _rev_rows(cfg, data)
    for i, row in enumerate(rows):
        ry = rev_rule + (i + 1) * rrow_h - 7
        d = D_DATA + i * 0.09
        if i:
            out += _g(D_RULE + 0.1,
                      rule(rev_x0, ry - 15, x1, ry - 15, t, w=0.6, opacity=0.7))
        if row is None:
            # An unfilled revision block is not blank on a real sheet. It is
            # ruled and voided, waiting for the next issue.
            out += _g(d, "".join(
                text(cx, ry, DASH, t, size=9, color="faint")
                for cx, _k, _wd in cols)
                + text(x1, ry, DASH, t, size=8.5, color="faint", anchor="end"))
            continue
        letter, zone, desc, date = row
        out += _g(d, text(cols[0][0], ry, letter, t, size=10, weight=700))
        out += _g(d, text(cols[1][0], ry, zone, t, size=8.5, color="soft"))
        out += _g(d, text(cols[2][0], ry, _fit(desc, cols[2][2], 9), t, size=9))
        out += _g(d, text(x1, ry, date or DASH, t, size=8.5,
                          color="soft" if date else "faint", anchor="end"))
    rev_bottom = rev_rule + len(rows) * rrow_h + 6

    # ── bottom: the boxed field strip ───────────────────────────────────────
    strip_y = max(left_bottom, rev_bottom) + 20
    strip_h = 38
    date = _datestr(data.get("generated_at")) or DASH
    fields = (("DRAWN BY", str(ident.get("drawn_by") or DASH), 2.2),
              ("REV", str(ident.get("revision") or DASH), 0.7),
              ("SHEET", "%d OF %d" % (CARDS.index("titleblock") + 1,
                                      len(CARDS)), 1.0),
              ("DATE", date, 1.5),
              # A drawing with no scale says so. NONE is the correct answer for
              # a sheet whose subject has no physical size, not a missing value.
              ("SCALE", "NONE", 0.9),
              ("UNITS", "UTC", 1.0))
    total = sum(f[2] for f in fields)
    out += _g(D_RULE + 0.2,
              f'<rect x="{x0-2}" y="{strip_y}" width="{x1-x0+4}" '
              f'height="{strip_h}" fill="none" stroke="{t["rule"]}" '
              f'stroke-width="1.2"/>')
    fx = x0 - 2
    for i, (key, val, weight) in enumerate(fields):
        fw = (x1 - x0 + 4) * weight / total
        if i:
            out += _g(D_RULE + 0.26,
                      rule(fx, strip_y, fx, strip_y + strip_h, t, w=1.0))
        out += _g(D_LETTER + 0.3 + i * 0.05,
                  field(fx, strip_y, fw, key, _fit(val, fw - 12, 10, 0.3), t))
        fx += fw

    H = strip_y + strip_h + 30            # clears the sheet number in the corner
    return sheet(W, H, t, out, label="TITLE BLOCK",
                 sheet_no=_sheet_no("titleblock"))


# ── sheet 2: general notes ───────────────────────────────────────────────────

# Focus tags are drawn in one muted colour rather than keyed to the language
# palette. Those colours already mean something two sheets later, where a hatch
# and a swatch identify a material; reusing them here, where "transformers" is
# not a material and has no share of anything, would key the reader to a legend
# that does not exist.
FOCUS_SIZE = 7.4
FOCUS_TRACK = 0.9
FOCUS_PAD = 8           # each side of the tag lettering
FOCUS_H = 17
FOCUS_GAP = 7           # between tags on a row
FOCUS_PITCH = 24        # row to row


def _focus_strip(x, y, px, areas, t, delay):
    """The focus areas as outlined tags, wrapping to as many rows as needed.

    Returns (svg, y below the last row). Widths come from the monospace metric,
    so a row is packed against a real measurement and cannot spill past `px`.
    """
    out, rows = "", [[]]
    row_w = 0.0
    for a in areas:
        # A tag wider than the whole strip has nowhere to wrap to, so it is cut
        # to the strip instead of hanging over the frame. Nothing in the config
        # is close to this; it is here so nothing added later can break out.
        s = _fit(str(a).upper(), px - 2 * FOCUS_PAD, FOCUS_SIZE, FOCUS_TRACK)
        w = _w(s, FOCUS_SIZE, FOCUS_TRACK) + 2 * FOCUS_PAD
        if rows[-1] and row_w + FOCUS_GAP + w > px:
            rows.append([])
            row_w = 0.0
        rows[-1].append((s, w))
        row_w += w + (FOCUS_GAP if len(rows[-1]) > 1 else 0)

    i = 0
    for r, row in enumerate(rows):
        tx = x
        for s, w in row:
            d = delay + i * 0.04
            out += _g(d, f'<rect x="{tx:.1f}" y="{y + r * FOCUS_PITCH:.1f}" '
                         f'width="{w:.1f}" height="{FOCUS_H}" rx="2" '
                         f'fill="none" stroke="{t["rule"]}" '
                         f'stroke-width="0.9"/>')
            out += _g(d, caps(tx + w / 2, y + r * FOCUS_PITCH + 11.5, s, t,
                              size=FOCUS_SIZE, track=FOCUS_TRACK,
                              anchor="middle", color="soft"))
            tx += w + FOCUS_GAP
            i += 1
    return out, y + (len(rows) - 1) * FOCUS_PITCH + FOCUS_H


def _general(cfg, data, t):
    W = 900
    x0, x1 = 26, 874
    span = x1 - x0

    about = cfg.get("about") or {}
    # The body is wrapped in profile.toml for editing, not for the sheet, so the
    # file's own line breaks are collapsed out before it is re-wrapped to the
    # measured column width.
    body = " ".join(" ".join(str(s) for s in (about.get("body") or [])).split())
    points = [str(p) for p in (about.get("points") or []) if str(p).strip()]
    areas = [str(a) for a in (cfg.get("focus") or []) if str(a).strip()]

    out, y = "", 60
    if body:
        for i, line in enumerate(_wrap(body, span, 13)):
            out += _g(D_LETTER + i * 0.05, text(x0, y, line, t, size=13))
            y += 19
        y += 6

    if points:
        if body:
            out += _drawn_rule(x0, y, x1, y, t, D_RULE, w=0.8, dur=0.8)
            y += 24
        # One gutter for the whole block, sized to the widest number, so the
        # notes hang off a single margin instead of stepping right at note 10.
        gutter = _w(f"{len(points)}. ", 10.5)
        for i, p in enumerate(points):
            svg, y = _numbered_note(x0, y, span, f"{i + 1}.", p, t,
                                    D_DATA + i * 0.08, gutter=gutter)
            out += svg
            y += 8
        y += 6

    if areas:
        out += _drawn_rule(x0, y, x1, y, t, D_RULE + 0.08, w=0.8, dur=0.8)
        y += 20
        out += _g(D_LETTER + 0.2, caps(x0, y, "FOCUS", t, size=7, track=1.1))
        y += 12
        svg, y = _focus_strip(x0, y, span, areas, t, D_DATA + 0.3)
        out += svg

    if not (body or points or areas):
        out += _nodata(x0, 60, span, 46, t, label="NO GENERAL NOTES")
        y = 106

    H = int(y + 34)                       # clears the sheet number in the corner
    return sheet(W, H, t, out, label="GENERAL NOTES",
                 sheet_no=_sheet_no("general"))


# ── sheet 3: bill of materials ───────────────────────────────────────────────

def _bom(cfg, data, t):
    projects = list(cfg.get("projects") or [])
    n = len(projects)
    H = _bom_height(n)
    statuses = _status_map(cfg)

    # One hatch per distinct material, angle by first appearance. The completion
    # bar reuses its row's material hatch, so a part's progress is literally
    # drawn in the stuff the part is made of.
    langs, defs = [], ""
    for p in projects:
        lang = str(p.get("lang") or "")
        if lang and lang not in langs:
            langs.append(lang)
    for i, lang in enumerate(langs):
        c = _lang_color(cfg, lang, t, spare_at=i)
        defs += defs_hatch(i, c, angle=HATCH_ANGLES[i % len(HATCH_ANGLES)],
                           gap=4.5, w=1.0)

    out = ""
    heads = ((COL_ITEM, "ITEM", "middle"), (COL_PN, "DES", "start"),
             (COL_DESC, "DESCRIPTION", "start"), (COL_MATL, "MATL", "start"),
             (COL_STAT, "STATUS", "start"), (COL_COMP0, "COMPLETION", "start"))
    out += _g(D_LETTER, "".join(
        caps(x, BOM_HEAD_Y, s, t, size=7.4, track=1.2, anchor=a)
        for x, s, a in heads))
    # Heavier under the header, hairlines between rows. Standard table weight.
    out += _drawn_rule(BOM_X0, BOM_HEAD_RULE, BOM_X1, BOM_HEAD_RULE, t, D_RULE,
                       w=1.6, color="rule", dur=0.9)

    if not projects:
        out += _nodata(BOM_X0, BOM_BODY_Y + 10, BOM_X1 - BOM_X0,
                       BOM_ROW_H - 16, t, label="NO PARTS LISTED")
        return sheet(BOM_W, H, t, out, defs=defs, label="BILL OF MATERIALS",
                     sheet_no=_sheet_no("bom"))

    changed = _repo_name((data.get("last_push") or {}).get("repo")).casefold()
    cloud = ""
    mark_last_push = bool((cfg.get("bom") or {}).get("mark_last_push", False))

    for i, p in enumerate(projects):
        ty = BOM_BODY_Y + i * BOM_ROW_H
        d = D_DATA + i * 0.05
        if i:
            out += _g(D_RULE + 0.15 + i * 0.02,
                      rule(BOM_X0, ty, BOM_X1, ty, t, w=0.6, opacity=0.75))

        out += _g(d, balloon(COL_ITEM, ty + 19, i + 1, t, r=8.5))
        out += _g(d, text(COL_PN, ty + 22, str(p.get("pn") or DASH), t, size=9,
                          color="soft", track=0.4))

        name = str(p.get("name") or DASH)
        out += _g(d, text(COL_DESC, ty + 17, _fit(name, COL_DESC_R - COL_DESC,
                                                  12, 0.2), t, size=12,
                          weight=700, track=0.2))
        summary = str(p.get("summary") or "").strip()
        if summary:
            out += _g(d + 0.05,
                      text(COL_DESC, ty + 30,
                           _fit(summary, COL_DESC_R - COL_DESC, SUMMARY_SIZE), t,
                           size=SUMMARY_SIZE, color="soft"))
        # Tolerance callouts: the project's own notes, run out right-aligned
        # under the description the way a tolerance block sits under a feature.
        notes = [str(x) for x in (p.get("notes") or []) if str(x).strip()][:3]
        if notes:
            run = " · ".join(notes)
            out += _g(d + 0.1,
                      text(COL_DESC_R, ty + 41,
                           _fit(run, COL_DESC_R - COL_DESC, 7.4, 0.2), t,
                           size=7.4, color="faint", anchor="end", track=0.2))

        lang = str(p.get("lang") or "")
        if lang:
            hi = langs.index(lang)
            lc = _lang_color(cfg, lang, t, spare_at=hi)
            out += _g(d, f'<rect x="{COL_MATL}" y="{ty+11}" width="17" '
                         f'height="12" fill="url(#h{hi})" stroke="{lc}" '
                         f'stroke-width="0.9"/>')
            out += _g(d, text(COL_MATL + 24, ty + 21,
                              _fit(lang, COL_STAT - COL_MATL - 30, 9), t,
                              size=9))
        else:
            hi = None
            out += _g(d, text(COL_MATL, ty + 21, DASH, t, size=9,
                              color="faint"))

        key = str(p.get("status") or "")
        rank, entry = statuses.get(key, (len(STATUS_COLORS) - 1, {}))
        scol = STATUS_COLORS[min(rank, len(STATUS_COLORS) - 1)]
        out += _g(d, text(COL_STAT, ty + 22, entry.get("mark") or "○", t,
                          size=11, color=scol))
        out += _g(d, caps(COL_STAT + 15, ty + 21, _fit(key or DASH, 72, 8, 0.8),
                          t, size=8, track=0.8, color="ink"))

        # ── completion, dimensioned ─────────────────────────────────────────
        # The one figure on the sheet that is a measurement, so it is drawn the
        # way a measurement is drawn: a dimension line across the full column
        # with the value broken into it, and a hatched bar underneath showing
        # how much of the run is filled.
        try:
            frac = min(1.0, max(0.0, float(p.get("completion") or 0.0)))
        except (TypeError, ValueError):
            frac = 0.0
        span = COL_COMP1 - COL_COMP0
        out += _g(d + 0.12, dim(COL_COMP0, COL_COMP1, ty + 26, _pct(frac), t))
        out += _g(d + 0.12,
                  f'<rect x="{COL_COMP0}" y="{ty+31}" width="{span}" '
                  f'height="7" fill="{t["fill"]}" stroke="{t["rule"]}" '
                  f'stroke-width="0.7"/>')
        if frac > 0:
            fillref = f"url(#h{hi})" if hi is not None else t["accent"]
            stroke = _lang_color(cfg, lang, t, spare_at=hi or 0) if lang \
                else t["accent"]
            out += _grow_bar(COL_COMP0, ty + 31, span * frac, 7, fillref,
                             d + 0.3, stroke=stroke, sw=0.7)

        # ── revision cloud ──────────────────────────────────────────────────
        # Off by default: [bom] mark_last_push in profile.toml. The mark itself
        # is genuine drafting practice, a scalloped outline around whatever
        # moved since the last issue. But red is the loudest thing on the sheet
        # and it lands on a different row every day, so it reads as an alarm
        # rather than a note. LAST CONTACT on the telemetry sheet states the
        # same fact calmly, so nothing is lost by leaving this off.
        if mark_last_push and changed and name.casefold() == changed:
            cloud = revcloud(BOM_X0 + 4, ty + 3, BOM_X1 - BOM_X0 - 8,
                             BOM_ROW_H - 8, t, delay=D_DATA + n * 0.05 + 0.35)
            rev_letter = str((cfg.get("identity") or {}).get("revision") or "")
            flag = f"REV {rev_letter}".strip()
            cloud += _g(D_DATA + n * 0.05 + 0.8,
                        f'<rect x="816" y="{ty+4}" width="46" height="13" '
                        f'rx="1.5" fill="{t["ground"]}" stroke="{t["red"]}" '
                        f'stroke-width="1"/>'
                        f'<text x="839" y="{ty+13.5}" fill="{t["red"]}" '
                        f'font-size="7.5" text-anchor="middle" '
                        f'letter-spacing="0.8" font-weight="700">'
                        f'{esc(flag)}</text>')

    body_end = BOM_BODY_Y + n * BOM_ROW_H
    out += _g(D_RULE + 0.2, rule(BOM_X0, body_end, BOM_X1, body_end, t, w=1.2))
    out += cloud

    # Footer: the status vocabulary, so the marks in the STATUS column are
    # readable without the README next to it.
    legend, lx = "", BOM_X0
    for skey, (rank, entry) in sorted(statuses.items(), key=lambda kv: kv[1][0]):
        c = STATUS_COLORS[min(rank, len(STATUS_COLORS) - 1)]
        legend += text(lx, body_end + 22, entry.get("mark") or "", t, size=9,
                       color=c)
        legend += caps(lx + 12, body_end + 21, skey, t, size=7, track=0.9)
        lx += 22 + _w(skey, 7, 0.9)
    legend += caps(BOM_X1, body_end + 21, f"{n} PARTS", t, size=7, track=1.1,
                   anchor="end")
    out += _g(D_LETTER + 0.4, legend)

    return sheet(BOM_W, H, t, out, defs=defs, label="BILL OF MATERIALS",
                 sheet_no=_sheet_no("bom"))


# ── sheet 4: telemetry ───────────────────────────────────────────────────────

ISS_INCL = 51.64        # ISS orbital inclination, degrees


def _iss_track(lat0, lon0, x, y, w, h, t, delay):
    """Plot the ISS ground track through the live sub-satellite point.

    For a circular orbit the geodetic latitude is a pure function of the
    argument of latitude u (the angle travelled from the ascending node):

        sin(lat) = sin(i) * sin(u),     i = 51.64 deg for the ISS

    and over a single pass u advances almost linearly with longitude, which is
    why an equirectangular ground track is the familiar sinusoid bounded by
    +/- i rather than anything more exotic. Plotting lat against a phase-shifted
    longitude is therefore the correct shape, not a decorative sine wave.

    The phase is solved so the curve passes exactly through the observed point:

        u0    = asin( sin(lat0) / sin(i) )
        phase = u0 - lon0

    asin returns the ascending branch; the descending branch (pi - u0) is the
    other valid solution, and a single sample cannot distinguish them, so the
    ascending one is drawn and the readout carries the sample time.
    """
    inc = math.radians(ISS_INCL)
    si = math.sin(inc)
    # A reported latitude outside the inclination is sensor noise, not physics.
    s = max(-1.0, min(1.0, math.sin(math.radians(lat0)) / si))
    phase = math.asin(s) - math.radians(lon0)

    pts = []
    for step in range(0, 181):
        lon = -180 + step * 2
        lat = math.degrees(math.asin(si * math.sin(math.radians(lon) + phase)))
        pts.append((x + (lon + 180) / 360 * w, y + (90 - lat) / 180 * h))

    d = "M" + " L".join(f"{px:.1f} {py:.1f}" for px, py in pts)
    length = sum(math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1])
                 for i in range(len(pts) - 1))
    out = (f'<path d="{d}" fill="none" stroke="{t["accent"]}" '
           f'stroke-width="1.4" stroke-linejoin="round" '
           f'stroke-dasharray="{length:.0f}" stroke-dashoffset="0">'
           f'{draw_on(length, delay, 1.3)}</path>')

    mx = x + (lon0 + 180) / 360 * w
    my = y + (90 - lat0) / 180 * h
    out += _g(delay + 0.9,
              f'<circle cx="{mx:.1f}" cy="{my:.1f}" r="7" fill="none" '
              f'stroke="{t["accent"]}" stroke-width="0.9" opacity="0.65"/>'
              f'<circle cx="{mx:.1f}" cy="{my:.1f}" r="2.6" '
              f'fill="{t["accent"]}"/>'
              + rule(mx - 11, my, mx + 11, my, t, color="accent", w=0.7,
                     opacity=0.55)
              + rule(mx, my - 11, mx, my + 11, t, color="accent", w=0.7,
                     opacity=0.55))
    return out


def _graticule(x, y, w, h, t, delay):
    """Equirectangular graticule, 30 degree spacing, equator emphasised."""
    out = (f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" '
           f'fill="{t["fill"]}" stroke="{t["rule"]}" stroke-width="1" '
           f'opacity="0.9"/>')
    for lon in range(-150, 180, 30):
        gx = x + (lon + 180) / 360 * w
        out += rule(gx, y, gx, y + h, t, w=0.6, opacity=0.65)
    for lat in range(-60, 90, 30):
        gy = y + (90 - lat) / 180 * h
        out += rule(x, gy, x + w, gy, t, w=0.6,
                    opacity=0.95 if lat == 0 else 0.6)
    # The equator gets a name rather than a number: a bare "0°" sitting at the
    # left edge of a lon/lat plot reads as longitude zero, which is the wrong
    # axis and lands on the frame besides.
    out += caps(x + 4, y + h / 2 - 4, "EQ", t, size=6, track=0.6, opacity=0.8)

    # The orbit's latitude limits, drawn as the dashed extremes they are. The
    # track is tangent to these two lines and never crosses them. That is the
    # whole reason the sinusoid peaks where it does, and showing it turns the
    # curve from a decorative wave into a consequence of the inclination.
    for lat in (ISS_INCL, -ISS_INCL):
        gy = y + (90 - lat) / 180 * h
        out += rule(x, gy, x + w, gy, t, color="soft", w=0.7, dash="3 3",
                    opacity=0.55)
    out += caps(x + w - 4, y + (90 - ISS_INCL) / 180 * h - 4,
                f"INC {ISS_INCL:.1f}°", t, size=6, track=0.4,
                anchor="end", opacity=0.75)

    for lon, anchor, dx in ((-180, "start", 1), (0, "middle", 0),
                            (180, "end", -1)):
        out += caps(x + (lon + 180) / 360 * w + dx, y + h + 8,
                    f"{lon}°", t, size=6, track=0.4, anchor=anchor)
    return _g(delay, out)


def _panel_launch(x, w, y, t, d, data):
    launch = data.get("launch") or None
    if not launch:
        return "", 104, "NO LAUNCH DATA"
    cd = _countdown(launch.get("net"), data.get("generated_at"))
    out = ""
    if cd:
        size = _fit_size(cd, w, 20, 0.06, floor=12)
        out += _g(d, text(x, y + 20, cd, t, size=size, weight=700,
                          track=size * 0.06), dur=0.5)
    else:
        out += _g(d, text(x, y + 20, DASH, t, size=20, color="faint"))
    out += _g(d + 0.05, rule(x, y + 30, x + w, y + 30, t, w=0.7, opacity=0.8))

    # The launch API's list mode returns "Vehicle | Mission" as one string and
    # omits the pad object entirely, so splitting the name is the normal path
    # and the site is normally unknown. Rows are built from what is actually
    # there rather than reserving a line that would be blank every day.
    vehicle, _, mission = str(launch.get("name") or DASH).partition("|")
    rows = [(vehicle.strip() or DASH, 11, "ink", 700)]
    if mission.strip():
        rows.append((mission.strip(), 8.6, "soft", 400))
    if launch.get("provider"):
        rows.append((str(launch["provider"]), 8.6, "soft", 400))
    if launch.get("pad"):
        rows.append((str(launch["pad"]), 8.0, "faint", 400))

    ry = y + 48
    for s, size, color, weight in rows:
        out += _g(d + 0.1, text(x, ry, _fit(s, w, size), t, size=size,
                                color=color, weight=weight))
        ry += 14
    status = str(launch.get("status") or "").strip()
    out += _g(d + 0.15, caps(x, ry + 8, "STATUS", t, size=6.8, track=1.0))
    out += _g(d + 0.18, caps(x, ry + 22, _fit(status or DASH, w, 11, 1.2), t,
                             size=11, track=1.2,
                             color="accent" if status else "faint"))
    return out, (ry + 26) - y, None


def _panel_humans(x, w, y, t, d, data):
    humans = data.get("humans")
    if humans is None:
        return "", 96, "NO DATA"
    out = _g(d, text(x + w / 2, y + 46, str(humans), t, size=48, weight=700,
                     anchor="middle", track=1.0), dur=0.6)
    out += _g(d + 0.1, caps(x + w / 2, y + 64, "HUMANS", t, size=8,
                            anchor="middle", track=1.3))
    out += _g(d + 0.1, caps(x + w / 2, y + 76, "IN SPACE", t, size=8,
                            anchor="middle", track=1.3))
    return out, 84, None


def _panel_iss(x, w, y, t, d, data):
    iss = data.get("iss") or None
    gw = w
    gh = min(126.0, gw / 2.0)             # equirectangular is 2:1 by definition
    if not iss:
        return "", gh + 60, "NO ISS FIX"
    out = _graticule(x, y, gw, gh, t, d)
    try:
        lat0 = float(iss.get("lat"))
        lon0 = float(iss.get("lon"))
    except (TypeError, ValueError):
        return "", gh + 60, "NO ISS FIX"
    out += _iss_track(lat0, lon0, x, y, gw, gh, t, d + 0.25)

    vel = iss.get("vel_kmh")
    alt = iss.get("alt_km")
    readout = (("LAT", f"{lat0:+.2f}°"),
               ("LON", f"{lon0:+.2f}°"),
               ("ALT", f"{float(alt):.1f} KM" if alt is not None else DASH),
               ("VEL", f"{float(vel):,.0f} KM/H".replace(",", " ")
                if vel is not None else DASH))
    # No leader from the marker down to this readout: it has to cross the
    # graticule to get here, and at the same weight and colour as the track it
    # reads as a second plotted line. The crosshair on the point does the job.
    ry = y + gh + 24
    half = w / 2
    for i, (k, v) in enumerate(readout):
        cx = x + (i % 2) * half
        yy = ry + (i // 2) * 13
        out += _g(d + 0.35 + i * 0.04, caps(cx, yy, k, t, size=7, track=1.0))
        # Values stop well short of the next column's key so the pairs read as
        # four readings rather than one run of alternating words.
        out += _g(d + 0.35 + i * 0.04,
                  text(cx + half - 18, yy, v, t, size=8.4, color="ink",
                       anchor="end"))
    stamp = _datestr(iss.get("at"), "%H:%M:%S")
    # An orbital fix is an observation at an instant, not a live feed. Saying so
    # is the difference between a reading and a claim.
    out += _g(d + 0.5, caps(x, ry + 30, f"SAMPLED {stamp or DASH} UTC", t,
                            size=6.8, track=0.9))
    return out, (ry + 34) - y, None


def _stat(x, w, y, label, value, t, d, *, size=15, color="ink"):
    out = _g(d, caps(x, y, label, t, size=7, track=1.1))
    out += _g(d + 0.06, text(x, y + 19, _fit(value, w, size, 0.3), t, size=size,
                             weight=600, color=color, track=0.3))
    return out


def _panel_contact(x, w, y, t, d, data):
    lp = data.get("last_push") or {}
    age = _ago(lp.get("at"), data.get("generated_at"))
    act = data.get("activity") or []
    out, yy = "", y + 10

    if age or lp.get("repo"):
        out += _stat(x, w, yy, "LAST CONTACT", age or DASH, t, d)
        out += _g(d + 0.1, text(x, yy + 32, _fit(_repo_name(lp.get("repo"))
                                                 or DASH, w, 8.6), t, size=8.6,
                                color="soft"))
    else:
        out += _nodata(x, yy - 8, w, 44, t, delay=d, label="NO CONTACT")
    yy += 52

    streak = data.get("streak")
    sval = f"{streak} DAY{'S' if streak != 1 else ''}" if streak is not None \
        else DASH
    out += _stat(x, w, yy, "STREAK", sval, t, d + 0.12, size=14)
    yy += 40

    last24 = act[-1][1] if act else None
    out += _stat(x, w, yy, "PUSHES / 24 H",
                 str(last24) if last24 is not None else DASH, t, d + 0.2,
                 size=14)
    yy += 40

    # The far end of the same measurement: the part nobody has touched in
    # longest. Three-digit day counts are normal here, so the value is fitted
    # to the column like every other run rather than assumed short.
    q = data.get("quietest") or {}
    days = q.get("days")
    out += _stat(x, w, yy, "QUIETEST",
                 f"{days} DAYS" if days is not None else DASH, t, d + 0.26,
                 size=14)
    if q.get("repo"):
        out += _g(d + 0.3, text(x, yy + 32, _fit(_repo_name(q["repo"]), w, 8.6),
                                t, size=8.6, color="soft"))
    return out, (yy + 38) - y, None


def _panel_audio(x, w, y, t, d, data):
    li = data.get("listening") or {}
    out = _g(d, text(x, y + 20, _fit(str(li.get("track") or DASH), w, 11), t,
                     size=11, weight=700))
    out += _g(d + 0.06, text(x, y + 36, _fit(str(li.get("artist") or DASH), w,
                                             8.8), t, size=8.8, color="soft"))
    if li.get("now_playing"):
        out += _g(d + 0.12, caps(x, y + 58, "NOW DECODING", t, size=8.5,
                                 track=1.2, color="green"))
    else:
        stamp = _datestr(li.get("at"), "%Y-%m-%d %H:%M") or DASH
        out += _g(d + 0.12, caps(x, y + 58, stamp, t, size=7.6, track=0.9))
    return out, 70, None


def _telemetry(cfg, data, t):
    W = 900
    x0, x1 = 26, 874
    head_y, body_y = 52, 78

    # Panels reflow: weights are relative demands on the width, normalised over
    # whichever panels are actually present. The graticule asks for the most
    # because it is the only panel whose content has a fixed aspect ratio.
    panels = [("LAUNCH WINDOW", 1.20, _panel_launch),
              ("OFF-PLANET", 0.68, _panel_humans),
              ("ISS GROUND TRACK", 1.62, _panel_iss),
              ("CONTACT", 1.00, _panel_contact)]
    # The audio channel is off by configuration, not broken, so it is omitted
    # rather than voided. A NO DATA cell would imply a failure that never
    # happened.
    if data.get("listening"):
        panels.append(("AUDIO CHANNEL", 0.88, _panel_audio))

    total = sum(p[1] for p in panels)
    span = x1 - x0
    bodies, edges = [], []
    px = x0
    for i, (title, weight, fn) in enumerate(panels):
        pw = span * weight / total
        inner_x = px + (10 if i else 0)
        inner_w = pw - (10 if i else 0) - 12
        svg, h, void = fn(inner_x, inner_w, body_y, t, D_DATA + i * 0.08, data)
        bodies.append([title, px, pw, inner_x, inner_w, svg, h,
                       (void, D_DATA + i * 0.08)])
        if i:
            edges.append(px)
        px += pw

    body_h = max(b[6] for b in bodies)
    H = int(body_y + body_h + 34)

    # A voided panel is sized once the tallest panel is known, so the dashed
    # cells square off against each other instead of leaving a ragged edge on
    # the day every channel is down.
    for b in bodies:
        label, delay = b[7]
        if label:
            b[5] = _nodata(b[3], body_y, b[4], body_h, t, delay=delay,
                           label=label)

    out = ""
    for x in edges:
        out += _drawn_rule(x, head_y - 20, x, H - 30, t, D_RULE + 0.12, w=0.9,
                           dur=0.9)
    for i, (title, ppx, pw, inner_x, inner_w, svg, _h, _v) in enumerate(bodies):
        out += _g(D_LETTER + i * 0.06,
                  caps(inner_x, head_y, _fit(title, inner_w, 7.6, 1.3), t,
                       size=7.6, track=1.3))
        out += _drawn_rule(inner_x, head_y + 8, inner_x + inner_w, head_y + 8,
                           t, D_RULE + 0.05 + i * 0.04, w=0.8, dur=0.6)
        out += svg

    stamp = _datestr(data.get("generated_at"), "%Y-%m-%d %H:%M") or DASH
    # The sheet's own timestamp, distinct from the ISS panel's fix time.
    out += _g(D_LETTER + 0.5, caps(x0, H - 22, f"GENERATED {stamp} UTC", t,
                                   size=6.8, track=1.0))
    return sheet(W, H, t, out, label="DAILY TELEMETRY",
                 sheet_no=_sheet_no("telemetry"))


# ── sheet 5: material composition ────────────────────────────────────────────

# The two narrow sheets sit side by side in the README, so both are floored at a
# common height. Content can still push either one taller; this only stops them
# from being *needlessly* mismatched on a normal day.
SIDE_MIN_H = 248


def _composition(cfg, data, t):
    W = 440
    x0, x1 = 26, 414
    langs = list(data.get("languages") or [])
    lcfg = cfg.get("languages") or {}
    try:
        min_share = float(lcfg.get("min_share") or 0.0)
    except (TypeError, ValueError):
        min_share = 0.0
    try:
        show = int(lcfg.get("show") or 6)
    except (TypeError, ValueError):
        show = 6

    kept = [(str(n), float(s)) for n, s in langs
            if s is not None and float(s) >= min_share][:show]
    # Whatever the filters cut is still part of the material, so it is drawn as
    # a remainder segment rather than quietly renormalising the bar to 100%.
    #
    # Conditioned on `langs`, not on `kept`, and that distinction is the whole
    # point: with no language data at all, a remainder computed from an empty
    # `kept` comes out as 1.0 and the card draws a full bar reading OTHER 100%.
    # That is a fabricated measurement. It is the exact failure this sheet
    # exists to make impossible. No data must reach the voided-field branch
    # below.
    # Languages that arrived but all fell under min_share are a different case:
    # there really is material, it is really all in the tail, and OTHER 100% is
    # then the honest answer.
    rest = max(0.0, 1.0 - sum(s for _n, s in kept)) if langs else 0.0
    segments = kept + ([("OTHER", rest)] if rest > 0.005 else [])

    defs = ""
    for i, (name, _s) in enumerate(segments):
        c = t["faint"] if name == "OTHER" else _lang_color(cfg, name, t,
                                                           spare_at=i)
        defs += defs_hatch(i, c, angle=HATCH_ANGLES[i % len(HATCH_ANGLES)],
                           gap=5, w=1.0)

    bar_y, bar_h = 56, 26
    out = ""
    if not segments:
        out += _nodata(x0, bar_y, x1 - x0, bar_h + 10, t,
                       label="NO LANGUAGE DATA")
        legend_y = bar_y + bar_h + 46
    else:
        out += _g(D_RULE, f'<rect x="{x0}" y="{bar_y}" width="{x1-x0}" '
                          f'height="{bar_h}" fill="{t["fill"]}" '
                          f'stroke="{t["rule"]}" stroke-width="1"/>')
        sx = float(x0)
        for i, (name, share) in enumerate(segments):
            sw = (x1 - x0) * share
            c = t["faint"] if name == "OTHER" else _lang_color(cfg, name, t,
                                                               spare_at=i)
            out += _g(D_DATA + i * 0.10,
                      _grow_bar(sx, bar_y, sw, bar_h, f"url(#h{i})",
                                D_DATA + i * 0.10, stroke=c, sw=0.9))
            sx += sw
        # Dimension the whole run with the corpus it was measured over.
        out += _g(D_DATA + 0.5,
                  dim(x0, x1, bar_y + bar_h + 20, _bytes(data.get("total_bytes")),
                      t))
        legend_y = bar_y + bar_h + 58

    repos, since = data.get("repos"), data.get("since_year")
    meta = " · ".join(s for s in (
        f"{repos} REPOS" if repos else "",
        f"SINCE {since}" if since else "") if s)
    if meta:
        out += _g(D_LETTER + 0.2, caps(x0, legend_y, meta, t, size=7, track=1.1))
    legend_y += 18

    # Legend in two columns: the swatch carries the hatch, so the legend keys
    # the bar by pattern and not only by colour.
    col_w = (x1 - x0 - 14) / 2
    rows = (len(segments) + 1) // 2
    for i, (name, share) in enumerate(segments):
        cx = x0 + (i % 2) * (col_w + 14)
        ry = legend_y + (i // 2) * 19
        c = t["faint"] if name == "OTHER" else _lang_color(cfg, name, t,
                                                           spare_at=i)
        d = D_DATA + 0.35 + i * 0.05
        out += _g(d, f'<rect x="{cx:.1f}" y="{ry-9:.1f}" width="15" '
                     f'height="11" fill="url(#h{i})" stroke="{c}" '
                     f'stroke-width="0.9"/>')
        out += _g(d, text(cx + 21, ry, _fit(name, col_w - 66, 8.6), t,
                          size=8.6))
        out += _g(d, text(cx + col_w, ry, _pct(share, 1), t, size=8.6,
                          color="soft", anchor="end"))

    foot_y = legend_y + max(0, rows - 1) * 19 + 24
    out += _g(D_LETTER + 0.45,
              text(x0, foot_y,
                   "each repo weighted equally · generated and vendored "
                   "excluded", t, size=6.9, color="faint"))

    H = max(SIDE_MIN_H, int(foot_y + 28))
    return sheet(W, H, t, out, defs=defs, label="MATERIAL COMPOSITION",
                 sheet_no=_sheet_no("composition"))


# ── sheet 6: push activity ───────────────────────────────────────────────────

def _activity(cfg, data, t):
    W = 440
    x0, x1 = 26, 414
    px0, px1 = 62, x1                     # left gutter carries the axis labels
    pty, pby = 62, 178                    # plot top / baseline
    act = list(data.get("activity") or [])

    out = ""
    if not act:
        out += _nodata(px0, pty, px1 - px0, pby - pty, t,
                       label="NO ACTIVITY DATA")
    else:
        counts = [int(c or 0) for _d, c in act]
        peak = max(counts)
        # 18% headroom keeps the peak's dimension line clear of the plot border
        # instead of letting the label collide with the frame.
        scale = (peak * 1.18) if peak else 1.0

        out += _drawn_rule(px0, pby, px1, pby, t, D_RULE, w=1.2, color="rule")
        out += _drawn_rule(px0, pty, px0, pby, t, D_RULE + 0.06, w=1.2,
                           color="rule")

        ticks = [0, peak] if peak < 2 else [0, peak // 2, peak]
        for v in sorted(set(ticks)):
            gy = pby - (v / scale) * (pby - pty)
            # No gridline at the peak: the dimension line already runs there,
            # and two rules on one level read as a drafting error.
            if v and v != peak:
                out += _g(D_RULE + 0.2,
                          rule(px0, gy, px1, gy, t, color="grid", w=0.8))
            out += _g(D_RULE + 0.2, rule(px0 - 3.5, gy, px0, gy, t, w=0.9))
            out += _g(D_LETTER, text(px0 - 7, gy + 3, str(v), t, size=7,
                                     color="faint", anchor="end"))

        slot = (px1 - px0) / len(act)
        bw = max(2.0, slot * 0.66)
        for i, c in enumerate(counts):
            cx = px0 + slot * i + (slot - bw) / 2
            h = (c / scale) * (pby - pty)
            if h > 0:
                out += _grow_col(cx, pby, bw, h, t["accent"],
                                 D_DATA + i * 0.012)
            if i % 5 == 0:                # tick every five days, under the axis
                out += _g(D_RULE + 0.25,
                          rule(cx + bw / 2, pby, cx + bw / 2, pby + 3.5, t,
                               w=0.8))

        if peak:
            ypk = pby - (peak / scale) * (pby - pty)
            out += _g(D_DATA + 0.5,
                      dim(px0, px1, ypk, f"PEAK {peak}", t, color="soft"))

        first = _datestr(act[0][0], "%m-%d") or ""
        last = _datestr(act[-1][0], "%m-%d") or ""
        out += _g(D_LETTER + 0.2, caps(px0, pby + 15, first, t, size=6.8,
                                       track=0.8))
        out += _g(D_LETTER + 0.2, caps(px1, pby + 15, last, t, size=6.8,
                                       track=0.8, anchor="end"))

    # The GitHub events API does not carry per-push commit counts, so the axis
    # says PUSHES. Labelling it COMMITS would be a nicer number and a false one.
    lx, ly = 34, (pty + pby) / 2
    out += _g(D_LETTER, f'<g transform="rotate(-90 {lx} {ly:.1f})">'
                        + caps(lx, ly, "PUSHES", t, size=7.4, track=1.6,
                               anchor="middle") + '</g>')

    fy = pby + 34
    tops = [_repo_name(n) for n, _c in (data.get("top_repos") or [])][:3]
    out += _g(D_LETTER + 0.35, caps(x0, fy, "MOST ACTIVE", t, size=6.8,
                                    track=1.1))
    out += _g(D_DATA + 0.4,
              text(x0, fy + 14, _fit(" · ".join(tops) if tops else DASH,
                                     x1 - x0, 8.4), t, size=8.4, color="soft"))
    lp = data.get("last_push") or {}
    stamp = _datestr(lp.get("at"), "%Y-%m-%d %H:%M")
    out += _g(D_DATA + 0.45,
              caps(x1, fy, f"LAST PUSH {stamp or DASH}", t, size=6.8,
                   track=0.9, anchor="end"))

    H = max(SIDE_MIN_H, int(fy + 40))
    return sheet(W, H, t, out, label="PUSH ACTIVITY / 30 D",
                 sheet_no=_sheet_no("activity"))


# ── sheet 7: notes ───────────────────────────────────────────────────────────

# Note 1 never changes. It is the sheet's own provenance statement: which
# figures are measured, and which are a person's judgement written down by hand.
NOTE_PROVENANCE = (
    "All figures are read from the GitHub API at build time. Status and "
    "completion are hand-set in data/profile.toml and reviewed, not inferred.")


def todays_note(cfg: dict, data: dict) -> str:
    """The day's field note, or "" when no notes are configured.

    Exported so build.py can put the same note in the README without keeping a
    second copy of the selection rule.

    The index is the date's ordinal, never a random draw. Two builds on the same
    day must produce identical bytes, otherwise the workflow's "commit if
    changed" step commits a new note every run and the history fills with diffs
    that say nothing.
    """
    pool = [str(s) for s in ((cfg or {}).get("field_notes") or [])
            if str(s).strip()]
    if not pool:
        return ""
    now = (data or {}).get("generated_at")
    # A payload that round-tripped through JSON carries a string, which has no
    # ordinal. Falling back to the first note keeps the sheet reproducible.
    ordinal = now.date().toordinal() if hasattr(now, "date") else 0
    return pool[ordinal % len(pool)]


def _notes(cfg, data, t):
    W = 900
    x0, x1 = 26, 874
    span = x1 - x0

    items = [NOTE_PROVENANCE]
    note = todays_note(cfg, data)
    if note:
        items.append(note)
    errors = list((data or {}).get("errors") or [])
    if errors:
        n = len(errors)
        items.append(
            f"This build degraded {n} telemetry channel"
            f"{'s' if n != 1 else ''}; those cells read NO DATA rather than "
            f"showing stale values.")

    # Numbered straight through whatever is present. A notes block that skips
    # from 1 to 3 reads as a note someone deleted.
    gutter = _w(f"{len(items)}. ", 11)
    out, y = "", 62
    for i, item in enumerate(items):
        svg, y = _numbered_note(x0, y, span, f"{i + 1}.", item, t,
                                D_DATA + i * 0.10, size=11, lead=16.5,
                                gutter=gutter)
        out += svg
        y += 12

    y += 4
    out += _drawn_rule(x0, y, x1, y, t, D_RULE, w=0.8, dur=0.8)

    stamp = _datestr((data or {}).get("generated_at"), "%Y-%m-%d %H:%M") or DASH
    out += _g(D_LETTER + 0.4, caps(x0, y + 18, f"GENERATED {stamp} UTC", t,
                                   size=6.8, track=1.0))
    H = int(y + 44)
    return sheet(W, H, t, out, label="NOTES", sheet_no=_sheet_no("notes"))


# ── entry point ──────────────────────────────────────────────────────────────


# ── link chips ───────────────────────────────────────────────────────────────
#
# A sheet is served through <img>, and an <img> is inert: no link inside an SVG
# is clickable once GitHub renders it that way. Inline <svg>, <object> and
# <map>/<area> are all removed by GitHub's HTML sanitiser, so none of them can
# carry a link either. What does survive is an <a> wrapping a <picture>, and two
# of those set side by side with no whitespace between them stay touching.
#
# So a link is its own small drawing. Each chip is one SVG, anchored in the
# markdown, and a row of them tiles into a strip that belongs to the drawing
# instead of a line of default-font markdown links sitting underneath it.
#
# Padding is baked into each chip rather than added between them, because the
# markdown emits them with no separating whitespace and there is nowhere else
# for the gap to come from.

CHIP_H = 30
CHIP_GAP = 5        # half-gap per side, so neighbours sit CHIP_GAP * 2 apart
CHIP_TEXT = 9.5
CHIP_TRACK = 1.1


def chip_width(label: str, *, accent: bool = False) -> float:
    """Total advance of a chip, padding and arrow included."""
    w = _w(str(label).upper(), CHIP_TEXT, CHIP_TRACK)
    return CHIP_GAP * 2 + 13 + w + 15 + (5 if accent else 0)


def chip(label: str, t: dict, *, accent: str | None = None) -> str:
    """One clickable-looking tag, drawn to match the sheets.

    `accent` is a colour for the left edge bar, used by the repository chips so
    a part's chip carries the same material colour as its BOM row.
    """
    label = str(label).upper()
    bar = 5 if accent else 0
    inner_x = CHIP_GAP + bar
    tw = _w(label, CHIP_TEXT, CHIP_TRACK)
    w = chip_width(label, accent=bool(accent))
    y0, h = 1.0, CHIP_H - 2

    body = (f'<rect x="{CHIP_GAP}" y="{y0}" width="{w - CHIP_GAP * 2:.1f}" '
            f'height="{h}" rx="2" fill="{t["ground"]}" stroke="{t["rule"]}" '
            f'stroke-width="1"/>')
    if accent:
        # Clipped to the chip so the bar keeps the rounded left corners.
        body += (f'<clipPath id="cc"><rect x="{CHIP_GAP}" y="{y0}" '
                 f'width="{w - CHIP_GAP * 2:.1f}" height="{h}" rx="2"/></clipPath>'
                 f'<rect x="{CHIP_GAP}" y="{y0}" width="{bar}" height="{h}" '
                 f'fill="{accent}" clip-path="url(#cc)"/>')
    body += caps(inner_x + 7, CHIP_H / 2 + 3.4, label, t, size=CHIP_TEXT,
                 track=CHIP_TRACK, color="ink")
    # The arrow is the only thing saying "this goes somewhere", since a drawing
    # has no hover state and the sheet cannot underline anything.
    body += text(inner_x + 7 + tw + 7, CHIP_H / 2 + 3.6, "\u2192", t,
                 size=10, color="accent")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.0f}" '
            f'height="{CHIP_H}" viewBox="0 0 {w:.1f} {CHIP_H}" '
            f'font-family="{bp.MONO}" role="img">{body}</svg>')


def link_chips(cfg: dict) -> list:
    """The chips under the title block: where to go from here."""
    ident = cfg.get("identity") or {}
    site = str(ident.get("website") or "")
    user = str(ident.get("github") or "")
    out = []
    if site:
        out.append(("site", site.split("//")[-1].rstrip("/"), site, None))
    if user:
        out.append(("repos", "repositories",
                    f"https://github.com/{user}?tab=repositories", None))
    out.append(("setup", "how this is built", "SETUP.md", None))
    out.append(("source", "the source of truth", "data/profile.toml", None))
    return out


def repo_chips(cfg: dict, t: dict) -> list:
    """One chip per part that has somewhere to go.

    Parts without a repository are skipped rather than drawn dead. A chip that
    goes nowhere is worse than no chip, and the written index already explains
    why those repositories are missing.
    """
    out = []
    for pr in cfg.get("projects") or []:
        repo = pr.get("repo")
        if not repo:
            continue
        out.append((str(pr.get("pn") or pr.get("name")).lower().replace("/", "-"),
                    str(pr.get("name")), repo,
                    _lang_color(cfg, pr.get("lang"), t)))
    return out


_RENDERERS = {
    "titleblock": _titleblock,
    "general": _general,
    "bom": _bom,
    "telemetry": _telemetry,
    "composition": _composition,
    "activity": _activity,
    "notes": _notes,
}


def render(name: str, cfg: dict, data: dict, t: dict) -> str:
    """Render one card as a complete SVG document.

    `name` is one of CARDS, `cfg` the parsed profile.toml, `data` the payload
    from sources.py (any value may be None or empty), and `t` one of
    blueprint.GROUNDS.
    """
    try:
        fn = _RENDERERS[name]
    except KeyError:
        raise ValueError(f"unknown card {name!r}; expected one of {CARDS}")
    return fn(cfg or {}, data or {}, t)
