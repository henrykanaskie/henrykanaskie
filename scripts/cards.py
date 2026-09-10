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

import datetime as dt
import math

try:                                    # scripts/ on sys.path (build.py's case)
    import blueprint as bp
except ModuleNotFoundError:             # imported as part of a package
    from . import blueprint as bp

esc, text, caps = bp.esc, bp.text, bp.caps
rule, dim, balloon, revcloud = bp.rule, bp.dim, bp.balloon, bp.revcloud
fade, grow, draw_on = bp.fade, bp.grow, bp.draw_on
sheet, field, defs_hatch = bp.sheet, bp.field, bp.defs_hatch

CARDS = ["titleblock", "general", "bom", "timeline", "composition",
         "toolbox"]


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
    """Humanised age, to one unit.

    Coarse on purpose. This lands in a title block field that answers "is this
    person still working on any of this", and the honest resolution for that
    question is hours or days. It used to carry a second unit and read "5h 00m
    ago", which spends four characters implying a precision the question does
    not have and looks broken on the hour.
    """
    if then is None or now is None or not hasattr(then, "strftime"):
        return None
    try:
        secs = (now - then).total_seconds()
    except TypeError:                    # naive/aware mismatch, not worth a crash
        return None
    secs = max(0.0, secs)
    if secs < 3600:
        return f"{int(secs // 60)}m ago"
    if secs < 86400:
        return f"{int(secs // 3600)}h ago"
    return f"{int(secs // 86400)}d ago"


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


# ── bill of materials geometry ──────────────────────────────────────────────
#
# The one number here anything outside this file depends on is COL_DESC_R, by
# way of summary_capacity(): build.py rejects a summary longer than the
# description column can hold, so the column width and the length check cannot
# disagree.

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


# ── sheet 1: title block ─────────────────────────────────────────────────────

def _rev_rows(cfg, data, n=3):
    """The most recent commit on each of the projects pushed to most recently.

    A revision block records what changed and when. This one is filled with the
    only change record this work actually has: the latest commit on each of the
    three projects touched most recently, its subject line, and the date it was
    authored. Every cell is measured and none of them can read N/A while the
    data is healthy.

    The version this replaced letters a revision LETTER against a repository
    NAME, a ZONE that only resolved for parts drawn on the BOM sheet, and a date
    on the first row only, because the events feed dates one push and not the
    rest. On a normal day that table drew N/A in five of its twelve cells. A
    table that cannot fill itself is not a record, it is a picture of one, and
    the whole claim of this drawing set is that its figures are real.

    Rows short of `n` come back as None and draw as a ruled, voided row, which
    is what a drawing does with a revision block it has not filled yet.
    """
    rows = []
    for rec in (data.get("revisions") or [])[:n]:
        repo = str(rec.get("repo") or "").strip()
        message = str(rec.get("message") or "").strip()
        at = _datestr(rec.get("at"))
        # Partial rows are dropped rather than dashed. A row is one commit, and
        # a commit with no message or no date is a parse failure, not a commit.
        if not repo or not message or not at:
            continue
        rows.append((repo, message, at))
    while len(rows) < n:
        rows.append(None)
    return rows


def _strip_fields(cfg, data):
    """The boxed fields under the title block, as (key, value, width weight).

    What a title block strip is for is telling a reader the things they would
    otherwise have to ask: who drew it, what it is, how current it is. The
    version this replaced carried DRAWN BY, REV, SHEET 1 OF 6, DATE, SCALE NONE
    and UNITS UTC. Four of those six are drafting furniture with no answer on a
    profile page: the scale of a person is not a quantity, the sheet number is
    already lettered in the corner of every sheet, and the revision letter was
    bumped by hand and therefore meant only that somebody remembered to bump it.

    These five all say something, and three of the five are measured rather than
    written down: the part counts come off the bill of materials, the push age
    off the API, and the date off the clock the build ran on.
    """
    ident = cfg.get("identity") or {}
    projects = cfg.get("projects") or []
    done = sum(1 for p in projects
               if str(p.get("status") or "").upper() == "QUALIFIED")

    lp = data.get("last_push") or {}
    age = _ago(lp.get("at"), data.get("generated_at"))

    return (
        ("STATUS", str(ident.get("status") or DASH), 2.3),
        ("BASED IN", str(ident.get("location") or DASH), 1.7),
        ("ON THIS SHEET", f"{len(projects)} PARTS, {done} DONE"
         if projects else DASH, 1.6),
        ("LAST PUSH", (age or DASH).upper(), 1.1),
        ("BUILT", _datestr(data.get("generated_at")) or DASH, 1.4),
    )


def _titleblock(cfg, data, t):
    W = 900
    ident = cfg.get("identity") or {}
    x0, x1 = 26, 874

    out = ""

    # ── who the drawing is by ───────────────────────────────────────────────
    #
    # There is no line of URLs under the tagline any more. There used to be one
    # lettering "github.com/henrykanaskie · henrykanaskie.com", and it looked
    # like two links and was neither: a sheet is served through <img>, so
    # nothing drawn inside one is clickable. It read as a broken link rather
    # than as a caption. The chip rail immediately under this sheet carries the
    # same two destinations as real anchors, which is where they belong.
    name = str(ident.get("name") or DASH)
    nsize = _fit_size(name, x1 - x0, 36, 0.10, floor=16)
    name_base = 92
    out += _g(D_LETTER, text(x0, name_base, name.upper(), t, size=nsize,
                             weight=700, track=nsize * 0.10), dur=0.55)

    y = name_base + 24
    title = str(ident.get("title") or "").strip()
    if title:
        out += _g(D_LETTER + 0.10,
                  caps(x0, y, _fit(title, x1 - x0, 11, 1.4), t, size=11,
                       track=1.4, color="soft"))
        y += 20
    tagline = str(ident.get("tagline") or "").strip()
    if tagline:
        out += _g(D_LETTER + 0.16,
                  text(x0, y, _fit(tagline, x1 - x0, 9), t, size=9,
                       color="soft"))
        y += 16

    # ── revision history, across the full width ─────────────────────────────
    #
    # It used to sit in a right-hand column beside the name, which left the
    # DESCRIPTION cell 150px wide. A commit subject does not fit in 150px, and
    # the column only ever held a repository name because that was the longest
    # thing that would go in. Given the whole measure it holds a real message,
    # which is what makes the table worth drawing at all.
    y += 30
    desc_x = x0 + 168
    desc_r = x1 - 96
    rrow_h = 23
    out += _g(D_LETTER,
              caps(x0, y, "PROJECT", t, size=7, track=1.1)
              + caps(desc_x, y, "LATEST COMMIT", t, size=7, track=1.1)
              + caps(x1, y, "DATE", t, size=7, track=1.1, anchor="end"))
    rule_y = y + 7
    out += _drawn_rule(x0, rule_y, x1, rule_y, t, D_RULE, w=1.4, color="rule")

    rows = _rev_rows(cfg, data)
    for i, row in enumerate(rows):
        ry = rule_y + (i + 1) * rrow_h - 7
        d = D_DATA + i * 0.09
        if i:
            out += _g(D_RULE + 0.1,
                      rule(x0, ry - 16, x1, ry - 16, t, w=0.6, opacity=0.7))
        if row is None:
            # An unfilled revision block is not blank on a real sheet. It is
            # ruled and voided, waiting for the next issue.
            out += _g(d, text(x0, ry, DASH, t, size=9, color="faint")
                      + text(desc_x, ry, DASH, t, size=9, color="faint")
                      + text(x1, ry, DASH, t, size=8.5, color="faint",
                             anchor="end"))
            continue
        repo, message, date = row
        out += _g(d, text(x0, ry, _fit(repo, desc_x - x0 - 14, 9), t, size=9,
                          weight=600))
        out += _g(d, text(desc_x, ry, _fit(message, desc_r - desc_x, 9), t,
                          size=9, color="soft"))
        out += _g(d, text(x1, ry, date, t, size=8.5, color="soft",
                          anchor="end"))
    y = rule_y + len(rows) * rrow_h + 22

    # ── the boxed field strip ───────────────────────────────────────────────
    strip_y = y
    strip_h = 38
    fields = _strip_fields(cfg, data)
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

    # The day's field note. It used to have a sheet of its own at the bottom of
    # the page; the sheet is gone and the note is not, because a rotating line in
    # the owner's own voice is the one thing on this drawing that says a person
    # is behind it. Set apart from the points above by a rule so it reads as an
    # annotation rather than a fourth point.
    note = todays_note(cfg, data)
    if note:
        if body or points or areas:
            out += _drawn_rule(x0, y, x1, y, t, D_RULE + 0.12, w=0.8, dur=0.8)
            y += 20
        out += _g(D_LETTER + 0.3, caps(x0, y, "FIELD NOTE", t, size=7, track=1.1))
        y += 14
        for i, line in enumerate(_wrap(note, span, 10.5)):
            out += _g(D_DATA + 0.4 + i * 0.05,
                      text(x0, y, line, t, size=10.5, color="soft"))
            y += 15

    if not (body or points or areas or note):
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
    #
    # A finished part is the exception: its bar is green. Completion is the one
    # figure on the sheet a reader scans for, and "done" is worth being able to
    # see without reading the status column. The hatch keeps the material's own
    # angle and only changes colour, so the row still says what it is made of.
    # Green is taken from the ground table, which is the same green the status
    # mark already uses, so the two agree rather than being two greens.
    langs, defs = [], ""
    for p in projects:
        lang = str(p.get("lang") or "")
        if lang and lang not in langs:
            langs.append(lang)
    for i, lang in enumerate(langs):
        c = _lang_color(cfg, lang, t, spare_at=i)
        angle = HATCH_ANGLES[i % len(HATCH_ANGLES)]
        defs += defs_hatch(i, c, angle=angle, gap=4.5, w=1.0)
        defs += defs_hatch(f"g{i}", t["green"], angle=angle, gap=4.5, w=1.0)
    # For a finished part with no material recorded at all.
    defs += defs_hatch("gx", t["green"], angle=45, gap=4.5, w=1.0)

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
            # rank 0 is the top of the configured status vocabulary, whatever it
            # is called, so renaming QUALIFIED does not quietly turn the green
            # off.
            done = rank == 0
            if done:
                fillref = f"url(#hg{hi})" if hi is not None else "url(#hgx)"
                stroke = t["green"]
            else:
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
        # rather than a note. LAST PUSH in the title block strip states the
        # same fact calmly, so nothing is lost by leaving this off.
        #
        # The flag used to read "REV G" off a hand-bumped identity field.
        # That field is gone, along with everything else on these sheets
        # that had to be remembered rather than measured, so the flag now
        # says what the mark actually means.
        if mark_last_push and changed and name.casefold() == changed:
            cloud = revcloud(BOM_X0 + 4, ty + 3, BOM_X1 - BOM_X0 - 8,
                             BOM_ROW_H - 8, t, delay=D_DATA + n * 0.05 + 0.35)
            flag = "LATEST"
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


# ── sheet 4: project timeline ────────────────────────────────────────────────
#
# Every part on the bill of materials drawn as a bar from its first commit to
# its most recent one. This replaced a daily telemetry sheet carrying the next
# orbital launch, the crew count in space, and the ISS ground track. Those were
# real, live figures and they were about somebody else's work, which is the
# whole reason they came off: a drawing set about these projects should spend
# its fourth sheet on these projects.
#
# Dates come from `started` / `last` / `commits` in profile.toml, read off real
# git history rather than estimated. Where a project has a public repository the
# build refreshes the end of its bar from the live push time, so an active bar
# grows without an edit. A private project has no live source and is drawn from
# the file, which the sheet says in its own footer rather than leaving the
# reader to assume both kinds of row are equally fresh.

TL_ROW_H = 30           # one project row: name line, then the span under it
TL_BAR_H = 9
TL_GUTTER = 196         # left column: designator, name, and the dates
TL_COMMITS = 62         # right column: commit count
TL_MIN_MONTHS = 6       # a window narrower than this is not a chart
TL_MIN_BAR = 5.0        # the width at which a bar still reads as one

# Every row letters its own date span in the gutter, under the project name,
# and that is not redundancy with the bar beside it. Six of these ten projects
# were built inside five weeks, against a window close to two years, so their
# bars come out a few pixels long and sit on top of each other at the right-hand
# edge whatever the scale does. The bar answers "when, relative to the others".
# The lettered span answers "when, exactly", which at this density is the only
# place that answer can live. Dimensioning the thing you drew is also just what
# a drawing does.
TL_SPAN_SIZE = 7.0


def _month_starts(first, last):
    """Every month boundary from `first`'s month through `last`'s, inclusive."""
    out, y, m = [], first.year, first.month
    while (y, m) <= (last.year, last.month):
        out.append(dt.date(y, m, 1))
        m += 1
        if m > 12:
            y, m = y + 1, 1
    return out


def _add_months(d, n):
    """`d` shifted by n months, snapped to the first of that month."""
    total = (d.year * 12 + d.month - 1) + n
    return dt.date(total // 12, total % 12 + 1, 1)


def _as_date(v):
    """A TOML date, a datetime, or an ISO string, as a plain date. Else None."""
    if v is None:
        return None
    if isinstance(v, dt.datetime):
        return v.date()
    if isinstance(v, dt.date):
        return v
    try:
        return dt.date.fromisoformat(str(v)[:10])
    except ValueError:
        return None


def _span_label(start, end):
    """A project's dates as one short run, or "" when it has none.

    A span inside one year drops the repeated year off the end: "2026-08-07 →
    08-27" rather than spelling 2026 twice in a 150px gutter.
    """
    if start is None:
        return ""
    if end is None or end == start:
        return start.isoformat()
    tail = end.strftime("%m-%d") if end.year == start.year else end.isoformat()
    return f"{start.isoformat()} → {tail}"


def _timeline_rows(cfg, data):
    """One row per project: (project, start, end, is_milestone, live).

    `live` records whether the end of the bar came from the API or from the
    config, because the footer says how many rows are which. A project missing
    `started` yields a row with no dates, which draws as a voided span rather
    than being silently dropped: a part on the BOM that is not on the timeline
    would read as an oversight in the drawing, and it is one.
    """
    follow = bool((cfg.get("timeline") or {}).get("follow_pushes", True))
    pushed = {str(k).lower(): v for k, v in (data.get("pushed_at") or {}).items()}

    rows = []
    for p in cfg.get("projects") or []:
        start = _as_date(p.get("started"))
        end = _as_date(p.get("last")) or start
        live = False
        if follow and p.get("repo"):
            slug = str(p["repo"]).rstrip("/").rsplit("/", 1)[-1].lower()
            at = pushed.get(slug)
            fresh = _as_date(at)
            # Only ever extends. A repository whose push time reads earlier
            # than the recorded last commit means the config is ahead of the
            # API, not that work was undone, so the later of the two wins.
            if fresh and (end is None or fresh > end):
                end, live = fresh, True
            elif fresh:
                live = True
        if start is None:
            rows.append((p, None, None, False, False))
            continue
        if end is None or end < start:
            end = start
        rows.append((p, start, end, end == start, live))
    return rows


def _timeline_window(rows, cfg, today):
    """(first, last) month boundaries the plot spans.

    The window is fitted to the data and then widened to a whole number of
    months, rather than being a fixed lookback. A fixed window is the version
    that was written first and it was wrong in the one way that matters here:
    the two oldest parts fell outside it and had to be clamped to the left edge
    with an open end, which draws a project as though it were still running off
    the side of the sheet when it was actually finished eighteen months ago.
    """
    starts = [r[1] for r in rows if r[1]]
    ends = [r[2] for r in rows if r[2]]
    if not starts:
        return _add_months(today, -TL_MIN_MONTHS), _add_months(today, 1)
    first = _add_months(min(starts), 0)
    last = _add_months(max(ends + [today]), 1)
    floor_months = max(TL_MIN_MONTHS,
                       int((cfg.get("timeline") or {}).get("months", 0) or 0))
    span = (last.year * 12 + last.month) - (first.year * 12 + first.month)
    if span < floor_months:
        first = _add_months(last, -floor_months)
    return first, last


def _timeline(cfg, data, t):
    W = 900
    x0, x1 = 26, 874
    px0 = x0 + TL_GUTTER
    px1 = x1 - TL_COMMITS
    today = (data.get("generated_at") or dt.datetime.now(dt.timezone.utc)).date()

    rows = _timeline_rows(cfg, data)
    first, last = _timeline_window(rows, cfg, today)
    total_days = max(1, (last - first).days)

    def px(d):
        """A date to an x coordinate, clamped to the plot."""
        frac = (d - first).days / total_days
        return px0 + max(0.0, min(1.0, frac)) * (px1 - px0)

    head_y = 52                     # the month scale
    body_y = head_y + 26            # first row's baseline band
    # Two footer lines and the sheet number in the corner. The first version
    # set the milestone legend right-aligned on the footer line and it landed
    # exactly on top of "SH 4 / 6".
    H = int(body_y + max(1, len(rows)) * TL_ROW_H + 76)
    axis_y = head_y + 12
    plot_b = body_y + len(rows) * TL_ROW_H

    defs = ""
    for i, (p, *_rest) in enumerate(rows):
        defs += defs_hatch(i, _lang_color(cfg, p.get("lang"), t, spare_at=i),
                           angle=HATCH_ANGLES[i % len(HATCH_ANGLES)], gap=4.5,
                           w=1.2)

    out = ""

    # ── month scale ─────────────────────────────────────────────────────────
    #
    # A tick at every month, a label only where there is room for one. Labelling
    # all nineteen months of a two-year window overlaps them into a smear, so
    # the quarters carry the lettering and January carries the year.
    months = _month_starts(first, last)
    step = 1
    while (px1 - px0) / max(1, len(months) / step) < 46:
        step += 1
    out += _drawn_rule(px0, axis_y, px1, axis_y, t, D_RULE, w=1.1, color="rule")
    labelled = False
    for i, m in enumerate(months):
        mx = px(m)
        if mx < px0 - 0.5 or mx > px1 + 0.5:
            continue
        is_year = m.month == 1
        out += _g(D_RULE + 0.1,
                  rule(mx, axis_y - 4 if is_year else axis_y - 2.5, mx, axis_y,
                       t, w=1.0 if is_year else 0.8))
        # A year boundary gets a full-height rule through the plot: it is the
        # one gridline a reader actually navigates by.
        if is_year:
            out += _g(D_RULE + 0.18,
                      rule(mx, axis_y, mx, plot_b + 6, t, color="grid", w=1.0))
        if i % step == 0 or is_year:
            # The first label carries its year even when it is not January.
            # Without it the axis reads FEB APR JUN AUG OCT DEC 2026 FEB, and
            # the only thing telling a reader which year the left half is in is
            # the word 2026 sitting in the middle of it. Every January after
            # that letters the year on its own, which is the point of a year
            # boundary rule.
            label = (m.strftime("%Y") if is_year
                     else m.strftime("%b %Y") if not labelled
                     else m.strftime("%b"))
            labelled = True
            out += _g(D_LETTER + 0.02 * i,
                      caps(mx, axis_y - 8, label, t, size=6.8, track=0.8,
                           anchor="middle",
                           color="soft" if is_year or label != m.strftime("%b")
                           else "faint"))

    # ── today ───────────────────────────────────────────────────────────────
    tx = px(today)
    out += _g(D_DATA + 0.1,
              rule(tx, axis_y, tx, plot_b + 6, t, color="accent", w=1.0,
                   dash="3 3", opacity=0.85))
    out += _g(D_DATA + 0.1, caps(tx, plot_b + 18, "TODAY", t, size=6.6,
                                 track=1.0, anchor="middle", color="accent"))

    # ── one row per part ────────────────────────────────────────────────────
    live_rows = 0
    for i, (p, start, end, milestone, live) in enumerate(rows):
        ry = body_y + i * TL_ROW_H
        cy = ry + TL_BAR_H + 1          # baseline of the name line
        d = D_DATA + i * 0.07
        color = _lang_color(cfg, p.get("lang"), t, spare_at=i)

        out += _g(D_LETTER + i * 0.03,
                  caps(x0, cy, p.get("pn") or DASH, t, size=7, track=0.9))
        out += _g(D_LETTER + i * 0.03,
                  text(x0 + 46, cy,
                       _fit(str(p.get("name") or DASH), TL_GUTTER - 56, 8.6),
                       t, size=8.6))
        span = _span_label(start, end)
        if span:
            out += _g(D_DATA + i * 0.05,
                      text(x0 + 46, cy + 11, span, t, size=TL_SPAN_SIZE,
                           color="faint"))

        if start is None:
            out += _nodata(px0, ry + 1, px1 - px0, TL_BAR_H + 4, t, delay=d,
                           label="NO DATES")
            continue
        if live:
            live_rows += 1

        bx, ex = px(start), px(end)
        if milestone:
            # A project whose entire history landed on one day has a date and
            # no duration, and that is exactly what a Gantt milestone is. Drawn
            # as the diamond rather than as a bar rounded up to something wide
            # enough to see, which would be a made-up duration.
            r = TL_BAR_H * 0.72
            # A milestone on the first or last day of the window would
            # otherwise be drawn half outside the plot, which reads as a mark
            # trailing off the sheet rather than as a date.
            bx = min(px1 - r, max(px0 + r, bx))
            my = ry + 1 + TL_BAR_H / 2
            out += _g(d, f'<path d="M{bx:.1f} {my-r:.1f} L{bx+r:.1f} {my:.1f} '
                         f'L{bx:.1f} {my+r:.1f} L{bx-r:.1f} {my:.1f} Z" '
                         f'fill="{color}" stroke="{color}" stroke-width="1"/>')
        else:
            # Floor the width at five pixels. Most of this work happened inside
            # a couple of weeks and the window is closer to two years, so a
            # truthful bar for a fortnight is about four pixels and a reader
            # cannot tell it from the one next to it. Five is the width at
            # which a bar still reads as a bar. Anything the floor is doing is
            # visible in the commit column beside it, which is not scaled.
            bw = max(TL_MIN_BAR, ex - bx)
            out += _g(d, _grow_bar(bx, ry + 1, bw, TL_BAR_H, f"url(#h{i})", d,
                                   stroke=color, sw=1.0))
            # An end cap that says whether the bar stopped or is still running:
            # a closed tick for finished work, an open chevron for a part still
            # in flight.
            done = str(p.get("status") or "").upper() == "QUALIFIED"
            if done:
                out += _g(d + 0.1, rule(bx + bw, ry - 1, bx + bw,
                                        ry + TL_BAR_H + 2, t, color="rule",
                                        w=1.3))
            else:
                out += _g(d + 0.1,
                          f'<path d="M{bx+bw+1.5:.1f} {ry+0.5:.1f} '
                          f'L{bx+bw+6.5:.1f} {ry+1+TL_BAR_H/2:.1f} '
                          f'L{bx+bw+1.5:.1f} {ry+TL_BAR_H+1.5:.1f}" '
                          f'fill="none" stroke="{color}" stroke-width="1.4" '
                          f'opacity="0.9"/>')

        n = p.get("commits")
        out += _g(d + 0.14,
                  text(x1, cy, f"{int(n):,}" if isinstance(n, int) and n
                       else DASH, t, size=8, anchor="end",
                       color="soft" if n else "faint"))

    out += _g(D_LETTER + 0.2, caps(x1, axis_y - 8, "COMMITS", t, size=6.6,
                                   track=0.9, anchor="end"))

    # ── footer ──────────────────────────────────────────────────────────────
    #
    # It says where the right-hand end of each bar came from. Some of these rows
    # are refreshed from the API every morning and some are as current as the
    # last hand edit, and a reader who cannot tell which is which has to treat
    # all of them as the weaker claim. A row is only refreshable if the account
    # owns the repository and it is public, which is why the count is not simply
    # the public parts.
    stale = sum(1 for r in rows if r[1] and not r[4])
    fy = plot_b + 38
    out += _g(D_LETTER + 0.4,
              text(x0, fy, "first commit to most recent · "
                           f"{live_rows} row{'' if live_rows == 1 else 's'} "
                           f"refreshed from GitHub, {stale} from the config "
                           "(private, or somebody else's repository)", t,
                   size=6.9,
                   color="faint"))
    if any(r[3] for r in rows):
        out += _g(D_LETTER + 0.45,
                  text(x0, fy + 12, "◆ whole history pushed in one day, so it "
                                    "has a date and no duration", t, size=6.9,
                       color="faint"))

    return sheet(W, H, t, out, defs=defs, label="PROJECT TIMELINE",
                 sheet_no=_sheet_no("timeline"))


# ── sheet 5: material composition ────────────────────────────────────────────

# These two used to be 440 wide and sat side by side in a markdown table. GitHub
# keeps a two column table at two columns on a phone, so each of them landed in
# half of an already narrow column and rendered at 119px, which was worse than
# what the phone layouts were written to fix. The table is gone and both sheets
# are full width like the rest of the set.
#
# The floor stays: it stops the pair looking needlessly mismatched when one has
# little to show.
SIDE_MIN_H = 248


def _composition(cfg, data, t):
    W = 900
    x0, x1 = 26, 874
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


# ── sheet 6: toolbox ─────────────────────────────────────────────────────────
#
# What gets reached for, and what for. This replaced a thirty-day push-activity
# chart, which measured how often the account was busy and said nothing about
# what any of it was. A bar chart of pushes is a chart about diligence; this is
# a chart about work.
#
# The rule for the middle column is that it says what the tool does in THIS
# work. "Python: a general purpose language" is a row that could sit on anyone's
# profile, which is the definition of a row not worth drawing. Every entry here
# has to name the thing that would not exist without it.
#
# The right-hand column cites parts from the bill of materials by name, and
# build.py rejects a name that is not on it, so the two sheets cannot drift out
# of agreement. A tool used somewhere off this drawing set letters as such
# rather than being given a citation it does not have.

TB_ROW_H = 26
TB_SWATCH = 15
TB_TOOL_X = 22          # from x0, past the swatch
TB_TOOL_W = 118
TB_FOR_X = 146
TB_FOR_W = 420
TB_ON_X = 578


def _toolbox(cfg, data, t):
    W = 900
    x0, x1 = 26, 874
    tools = list(cfg.get("tools") or [])

    head_y = 54
    body_y = head_y + 22
    H = int(body_y + max(1, len(tools)) * TB_ROW_H + 52)

    # Hatches are keyed to the language palette, and to the same colour that
    # language carries on the composition sheet, so a reader who learned that
    # Python is this blue two sheets ago is not re-taught it here.
    defs = ""
    for i, tool in enumerate(tools):
        lang = tool.get("lang")
        if lang:
            defs += defs_hatch(i, _lang_color(cfg, lang, t, spare_at=i),
                               angle=HATCH_ANGLES[i % len(HATCH_ANGLES)],
                               gap=4.5, w=1.1)

    out = ""
    if not tools:
        return sheet(W, 200, t,
                     _nodata(x0, 60, x1 - x0, 90, t, label="NO TOOLS LISTED"),
                     label="TOOLBOX", sheet_no=_sheet_no("toolbox"))

    cols = ((x0 + TB_TOOL_X, "TOOL"), (x0 + TB_FOR_X, "WHAT I USE IT FOR"),
            (x0 + TB_ON_X, "ON"))
    out += _g(D_LETTER, "".join(caps(cx, head_y, key, t, size=6.8, track=1.1)
                                for cx, key in cols))
    out += _drawn_rule(x0, head_y + 8, x1, head_y + 8, t, D_RULE, w=1.4,
                       color="rule")

    for i, tool in enumerate(tools):
        ry = body_y + i * TB_ROW_H + 12
        d = D_DATA + i * 0.06
        if i:
            out += _g(D_RULE + 0.1,
                      rule(x0, ry - 17, x1, ry - 17, t, w=0.6, opacity=0.6))

        lang = tool.get("lang")
        if lang:
            c = _lang_color(cfg, lang, t, spare_at=i)
            out += _g(d, f'<rect x="{x0:.1f}" y="{ry-9:.1f}" '
                         f'width="{TB_SWATCH}" height="11" fill="url(#h{i})" '
                         f'stroke="{c}" stroke-width="0.9"/>')
        else:
            # No swatch rather than a grey one. A swatch on this sheet means
            # "this language has a share of the bar two sheets back", and
            # OR-Tools does not.
            out += _g(d, rule(x0 + 3, ry - 3.5, x0 + TB_SWATCH - 3, ry - 3.5,
                              t, color="faint", w=1.0, opacity=0.7))

        out += _g(d, text(x0 + TB_TOOL_X, ry,
                          _fit(str(tool.get("name") or DASH), TB_TOOL_W, 9),
                          t, size=9, weight=600))
        out += _g(d + 0.04, text(x0 + TB_FOR_X, ry,
                                 _fit(str(tool.get("for") or DASH), TB_FOR_W,
                                      8.4), t, size=8.4, color="soft"))

        on = [str(s) for s in (tool.get("on") or []) if str(s).strip()]
        if on:
            out += _g(d + 0.08,
                      text(x0 + TB_ON_X, ry,
                           _fit(" · ".join(on), x1 - (x0 + TB_ON_X), 7.8), t,
                           size=7.8, color="soft"))
        else:
            out += _g(d + 0.08,
                      caps(x0 + TB_ON_X, ry, "not on this sheet", t, size=7,
                           track=0.8))

    fy = body_y + len(tools) * TB_ROW_H + 24
    out += _g(D_LETTER + 0.4,
              text(x0, fy, "projects named here are parts on sheet "
                           f"{CARDS.index('bom') + 1}; the build fails on a "
                           "name that isn't", t, size=6.9, color="faint"))
    return sheet(W, H, t, out, defs=defs, label="TOOLBOX",
                 sheet_no=_sheet_no("toolbox"))


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

# A phone gets a different chip. The full row is 680 to 739 wide and GitHub's
# README column on a 375pt phone is 293, so desktop chips wrap one or two to a
# line at whatever width each label happens to be, which reads as debris.
#
# The phone chip keeps the full label and takes the whole column instead, one
# per line. Equal-width tiles were tried first and the labels had to shrink to
# their designators to fit, which cost the reader the repository name for the
# sake of a grid. The longest name is ML_QUANTITATIVE_RESEARCH: any tile wide
# enough to hold it is already most of a 293px column, so one per line is what
# the content was going to force anyway. Stacked full-width rows also read as a
# parts list, which is what this is.
#
# <picture> takes a max-width media query and GitHub's sanitiser keeps it, which
# is the only reason any of this is possible.
CHIP_NARROW_TEXT = 10.5
CHIP_BREAK = 500      # px; below this the compact chips are served
PHONE_COL = 293       # README column on a 375pt phone, measured
CHIP_NARROW_W = 280   # inside PHONE_COL, and scales down on a smaller one


def chip_width(label: str, *, accent: bool = False) -> float:
    """Total advance of a chip, padding and arrow included."""
    w = _w(str(label).upper(), CHIP_TEXT, CHIP_TRACK)
    return CHIP_GAP * 2 + 13 + w + 15 + (5 if accent else 0)


def chip(label: str, t: dict, *, accent: str | None = None,
         compact: bool = False, width: int = CHIP_NARROW_W) -> str:
    """One clickable-looking tag, drawn to match the sheets.

    `accent` is a colour for the left edge bar, used by the repository chips so
    a part's chip carries the same material colour as its BOM row. `compact`
    draws the fixed width phone variant: centred label, no arrow.
    """
    if compact:
        return _chip_compact(str(label).upper(), t, accent=accent, width=width)
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


def _chip_compact(label: str, t: dict, *, accent: str | None = None,
                  width: int = CHIP_NARROW_W) -> str:
    """The phone chip: one full-column row, full label, arrow at the right.

    Left aligned rather than centred, because stacked rows of centred text read
    as a poster and stacked rows of left aligned text read as a list.
    """
    w, bar = int(width), (5 if accent else 0)
    y0, h = 1.0, CHIP_H - 2
    inner = CHIP_GAP + bar
    right = w - CHIP_GAP
    size = CHIP_NARROW_TEXT
    avail = right - (inner + 9) - 18
    label = _fit(label, avail, size, 0.6)

    body = (f'<rect x="{CHIP_GAP}" y="{y0}" width="{w - CHIP_GAP * 2}" '
            f'height="{h}" rx="2" fill="{t["ground"]}" stroke="{t["rule"]}" '
            f'stroke-width="1"/>')
    if accent:
        body += (f'<clipPath id="cn"><rect x="{CHIP_GAP}" y="{y0}" '
                 f'width="{w - CHIP_GAP * 2}" height="{h}" rx="2"/></clipPath>'
                 f'<rect x="{CHIP_GAP}" y="{y0}" width="{bar}" height="{h}" '
                 f'fill="{accent}" clip-path="url(#cn)"/>')
    body += caps(inner + 9, CHIP_H / 2 + 3.4, label, t, size=size, track=0.6,
                 color="ink")
    body += text(right - 9, CHIP_H / 2 + 3.6, "\u2192", t, size=10.5,
                 color="accent", anchor="end")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" '
            f'height="{CHIP_H}" viewBox="0 0 {w} {CHIP_H}" '
            f'font-family="{bp.MONO}" role="img">{body}</svg>')


def blank_rail(t: dict) -> str:
    """A one pixel transparent rail, served to phones.

    The rail is a label and a leader, which is furniture worth having on a wide
    row and pure obstruction on a narrow one: it would take a whole tile slot
    and push the grid out of alignment. There is no way to drop an element with
    a media query, so the phone gets a rail that is effectively not there.
    """
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="1" '
            f'height="{CHIP_H}" viewBox="0 0 1 {CHIP_H}" role="presentation"/>')


def link_chips(cfg: dict) -> list:
    """The chips under the title block: where to go from here."""
    ident = cfg.get("identity") or {}
    site = str(ident.get("website") or "")
    user = str(ident.get("github") or "")
    out = []
    if site:
        out.append(("site", site.split("//")[-1].rstrip("/"), "SITE", site, None))
    if user:
        out.append(("repos", "repositories", "REPOS",
                    f"https://github.com/{user}?tab=repositories", None))
    out.append(("setup", "how this is built", "SETUP", "SETUP.md", None))
    out.append(("source", "the source of truth", "CONFIG", "data/profile.toml",
                None))
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
                    str(pr.get("name")), str(pr.get("pn") or pr.get("name")),
                    repo, _lang_color(cfg, pr.get("lang"), t)))
    return out



# A chip row left on its own floats in the middle of the page, belonging to
# neither the sheet above nor the one below. A label and a short leader fixes
# that, which is what a drawing would do anyway.
#
# What does NOT work is padding the row out to the sheet width. A sheet is one
# image and scales down to whatever the container is: GitHub's README column is
# 846 CSS pixels, so a 900 wide sheet renders at 846. A row of small images does
# not scale, it wraps, so a row built to total 900 breaks onto two lines and the
# trailing rule lands alone on the second one. Measured on the live profile, a
# row built to 900 wrapped as 679 + 220.
#
# So there is no trailing rule and the row is deliberately narrower than the
# sheet. It has to survive wrapping anyway, because on a phone it will wrap no
# matter what it totals, and a row of chips flowing onto a second line reads
# fine as long as no rule fragment goes with them.
#
# The rail is a plain <img>, not an anchor. Only the chips are links.

SHEET_W = 900


def chip_rail(width: float, t: dict, *, label: str = "") -> str:
    """A rule segment that pads a chip row out to the sheet width.

    Transparent: it sits on the page ground, not on a card ground, so filling it
    would draw a visible box edge where the drawing wants a bare line.
    """
    width = max(1.0, float(width))
    y = CHIP_H / 2
    body = ""
    x = 0.0
    if label:
        body += caps(2, y + 3.2, label, t, size=7.5, track=1.3, color="faint")
        x = _w(str(label).upper(), 7.5, 1.3) + 10
    if width - x > 4:
        body += rule(x, y, width - 2, y, t, color="rule", w=1.0, opacity=0.8)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" '
            f'height="{CHIP_H}" viewBox="0 0 {width:.1f} {CHIP_H}" '
            f'font-family="{bp.MONO}" role="presentation">{body}</svg>')


def rail_width(label: str) -> float:
    """Width of the leading rail: the label plus a short leader stub.

    Fixed, and short. It does not stretch to fill the row, because the row has
    no fixed width to fill.
    """
    return _w(str(label).upper(), 7.5, 1.3) + 34 if label else 0.0


def row_width(specs: list, label: str) -> float:
    """Total advance of a chip row, for checking it clears the README column."""
    return rail_width(label) + sum(
        chip_width(lab, accent=bool(acc)) for _s, lab, _sh, _h, acc in specs)


# ── narrow sheets ────────────────────────────────────────────────────────────
#
# A sheet is 900 wide and GitHub's README column on a 375pt phone is 293, so a
# phone scales the whole drawing to a third of its size and the body lettering
# lands around 5px. Legible on paper, not on a phone.
#
# So each sheet has a second layout drawn at NARROW_W, reflowed rather than
# scaled: columns become stacked blocks, panels become rows. Served by the same
# max-width <picture> query as the chips.
#
# NARROW_W is 300 because the phone column is 293. Slightly over means a phone
# scales it by 0.98 rather than upscaling a smaller drawing into blur, and a
# 320pt phone still only takes it to 0.82.
#
# A card with no narrow layout falls back to its wide one. That is a real
# fallback, not a placeholder: it keeps the set renderable while the layouts are
# written one at a time.

NARROW_W = 300
NARROW_INSET = 8


_NARROW_RENDERERS: dict = {}


_RENDERERS = {
    "titleblock": _titleblock,
    "general": _general,
    "bom": _bom,
    "timeline": _timeline,
    "composition": _composition,
    "toolbox": _toolbox,
}


def render(name: str, cfg: dict, data: dict, t: dict, *,
           narrow: bool = False) -> str:
    """Render one card as a complete SVG document.

    `name` is one of CARDS, `cfg` the parsed profile.toml, `data` the payload
    from sources.py (any value may be None or empty), and `t` one of
    blueprint.GROUNDS. `narrow` asks for the phone layout, falling back to the
    wide one where no phone layout exists yet.
    """
    if name not in _RENDERERS:
        raise ValueError(f"unknown card {name!r}; expected one of {CARDS}")
    fn = _NARROW_RENDERERS.get(name) if narrow else None
    return (fn or _RENDERERS[name])(cfg or {}, data or {}, t)


def has_narrow(name: str) -> bool:
    """Whether `name` has its own phone layout rather than falling back."""
    return name in _NARROW_RENDERERS


# The phone layouts live in their own modules. They are a second full set of
# layouts, not a tweak of these, and putting them here would have doubled the
# length of the longest file in the repo.
#
# They do `import cards` and reach helpers through the module at call time
# rather than `from cards import ...` at import time, because this import runs
# while cards is still being defined and a from-import would bind names that do
# not exist yet.
for _mod in ("narrow", "narrow_bom"):
    try:
        _m = __import__(_mod)
    except ModuleNotFoundError:
        continue                      # layout not written yet; wide is the fallback
    _NARROW_RENDERERS.update(getattr(_m, "RENDERERS", {}))
