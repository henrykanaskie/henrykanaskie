#!/usr/bin/env python3
"""Phone layouts for five sheets of the drawing set.

cards.py owns the wide layouts. This module owns the same five sheets redrawn
to cards.NARROW_W, and nothing here changes *what* a sheet says. A phone reader
and a desktop reader must come away with the same facts; only the fitting is
different. Where the wide sheet sets two things side by side, this one stacks
them, and where a column exists only to key the reader to another sheet it is
dropped rather than squeezed to four characters.

    _titleblock   name shrunk to the measure, revision table full width with
                  ZONE dropped, field strip as a 2 x 3 grid
    _general      the same prose, notes, and focus tags, rewrapped
    _notes        the numbered notes, rewrapped
    _composition  bar full width, legend down to one column
    _activity     the same plot, x labels and y ticks thinned

The usable measure is 264px: NARROW_W less the frame inset on both sides less a
10px margin inside the frame. Every column here is budgeted from that number,
and every height is accumulated from the content the way the wide sheets do it,
because a phone sheet that clips its last line is worse than no phone sheet.

Imports: cards imports this module from its own bottom, while cards itself is
still being defined. So helpers are reached through the module at call time
(`cards._fit(...)`) rather than bound at import time with a from-import, which
would look up names that do not exist yet and fail the import.
"""

from __future__ import annotations

try:                                    # scripts/ on sys.path (build.py's case)
    import blueprint as bp
except ModuleNotFoundError:             # imported as part of a package
    from . import blueprint as bp

import cards

# The drawing margin. bp.sheet's frame sits at the inset and writes the sheet
# label just inside it, so content starts one line below that and stops clear
# of the sheet number in the opposite corner.
X0 = cards.NARROW_INSET + 10
X1 = cards.NARROW_W - cards.NARROW_INSET - 10
SPAN = X1 - X0


def _sheet(name, h, t, body, *, defs="", label=""):
    """The narrow frame. One place so all five agree about inset and width."""
    return bp.sheet(cards.NARROW_W, h, t, body, defs=defs, label=label,
                    sheet_no=cards._sheet_no(name), inset=cards.NARROW_INSET)


# ── sheet 1: title block ─────────────────────────────────────────────────────

def _titleblock(cfg, data, t):
    ident = cfg.get("identity") or {}
    out = ""

    # The name is the one run that must never be cut, so it is shrunk to the
    # measure instead of fitted with an ellipsis.
    name = str(ident.get("name") or cards.DASH)
    nsize = cards._fit_size(name, SPAN, 22, 0.10, floor=11)
    y = 50
    out += cards._g(cards.D_LETTER,
                    bp.text(X0, y, name.upper(), t, size=nsize, weight=700,
                            track=nsize * 0.10), dur=0.55)
    y += int(nsize * 0.78) + 4

    title = str(ident.get("title") or "").strip()
    if title:
        for i, line in enumerate(cards._wrap(title.upper(), SPAN, 8.5, 0.9)):
            out += cards._g(cards.D_LETTER + 0.10 + i * 0.04,
                            bp.caps(X0, y, line, t, size=8.5, track=0.9,
                                    color="soft"))
            y += 13
        y += 3

    tagline = str(ident.get("tagline") or "").strip()
    if tagline:
        for i, line in enumerate(cards._wrap(tagline, SPAN, 8.2)):
            out += cards._g(cards.D_LETTER + 0.16 + i * 0.04,
                            bp.text(X0, y, line, t, size=8.2, color="soft"))
            y += 12
        y += 3

    links = " · ".join(s for s in (
        (f"github.com/{ident['github']}" if ident.get("github") else ""),
        str(ident.get("website") or "").replace("https://", ""),
    ) if s)
    if links:
        for i, line in enumerate(cards._wrap(links.upper(), SPAN, 7.2, 0.8)):
            out += cards._g(cards.D_LETTER + 0.22 + i * 0.04,
                            bp.caps(X0, y, line, t, size=7.2, track=0.8))
            y += 11

    # ── revision history, now full width ────────────────────────────────────
    #
    # ZONE is dropped. It cites where on the BOM sheet the changed part is
    # drawn, which is furniture at any width and useless on a phone, where the
    # reader cannot hold two sheets side by side anyway. REV, DESCRIPTION and
    # DATE are the three columns that say what actually changed and when, and
    # dropping the fourth is what buys DESCRIPTION enough room to letter a
    # repository name without cutting it.
    y += 18
    desc_x = X0 + 30
    desc_r = X1 - 52
    rrow_h = 20
    out += cards._g(cards.D_LETTER,
                    bp.caps(X0 + 2, y, "REV", t, size=6.5, track=1.0)
                    + bp.caps(desc_x, y, "DESCRIPTION", t, size=6.5, track=1.0)
                    + bp.caps(X1, y, "DATE", t, size=6.5, track=1.0,
                              anchor="end"))
    rule_y = y + 6
    out += cards._drawn_rule(X0, rule_y, X1, rule_y, t, cards.D_RULE, w=1.4,
                             color="rule")

    rows = cards._rev_rows(cfg, data)
    for i, row in enumerate(rows):
        ry = rule_y + (i + 1) * rrow_h - 6
        d = cards.D_DATA + i * 0.09
        if i:
            out += cards._g(cards.D_RULE + 0.1,
                            bp.rule(X0, ry - 14, X1, ry - 14, t, w=0.6,
                                    opacity=0.7))
        if row is None:
            # An unfilled revision block is ruled and voided, not blank.
            out += cards._g(d, bp.text(X0 + 2, ry, cards.DASH, t, size=8.5,
                                       color="faint")
                            + bp.text(desc_x, ry, cards.DASH, t, size=8.5,
                                      color="faint")
                            + bp.text(X1, ry, cards.DASH, t, size=8,
                                      color="faint", anchor="end"))
            continue
        letter, _zone, desc, date = row
        out += cards._g(d, bp.text(X0 + 2, ry, letter, t, size=9.5, weight=700))
        out += cards._g(d, bp.text(desc_x, ry,
                                   cards._fit(desc, desc_r - desc_x, 8.5), t,
                                   size=8.5))
        out += cards._g(d, bp.text(X1, ry, date or cards.DASH, t, size=8,
                                   color="soft" if date else "faint",
                                   anchor="end"))
    y = rule_y + len(rows) * rrow_h + 10

    # ── the field strip, folded into a 2 x 3 grid ───────────────────────────
    #
    # Six boxes in a line would be 44px each here, which is narrower than the
    # DRAWN BY value and would ellipsise the date. Folding to two columns keeps
    # every field at full value rather than dropping any of them.
    strip_y = y
    rows_n, cols_n, fh = 3, 2, 30
    fw = SPAN / cols_n
    date = cards._datestr(data.get("generated_at")) or cards.DASH
    fields = (("DRAWN BY", str(ident.get("drawn_by") or cards.DASH)),
              ("REV", str(ident.get("revision") or cards.DASH)),
              ("SHEET", "%d OF %d" % (cards.CARDS.index("titleblock") + 1,
                                      len(cards.CARDS))),
              ("DATE", date),
              # A drawing with no scale says so. NONE is the correct answer for
              # a sheet whose subject has no physical size.
              ("SCALE", "NONE"),
              ("UNITS", "UTC"))
    out += cards._g(cards.D_RULE + 0.2,
                    f'<rect x="{X0}" y="{strip_y}" width="{SPAN}" '
                    f'height="{rows_n * fh}" fill="none" '
                    f'stroke="{t["rule"]}" stroke-width="1.2"/>')
    out += cards._g(cards.D_RULE + 0.26,
                    bp.rule(X0 + fw, strip_y, X0 + fw,
                            strip_y + rows_n * fh, t, w=1.0))
    for r in range(1, rows_n):
        out += cards._g(cards.D_RULE + 0.26,
                        bp.rule(X0, strip_y + r * fh, X1, strip_y + r * fh, t,
                                w=1.0))
    for i, (key, val) in enumerate(fields):
        fx = X0 + (i % cols_n) * fw
        fy = strip_y + (i // cols_n) * fh
        out += cards._g(cards.D_LETTER + 0.3 + i * 0.05,
                        bp.field(fx, fy, fw, key,
                                 cards._fit(val, fw - 12, 9.5, 0.3), t,
                                 size=9.5, kh=10))

    H = strip_y + rows_n * fh + 26        # clears the sheet number in the corner
    return _sheet("titleblock", H, t, out, label="TITLE BLOCK")


# ── sheet 2: general notes ───────────────────────────────────────────────────

def _general(cfg, data, t):
    about = cfg.get("about") or {}
    # The body is wrapped in profile.toml for editing, not for the sheet, so the
    # file's own line breaks are collapsed out before it is re-wrapped.
    body = " ".join(" ".join(str(s) for s in (about.get("body") or [])).split())
    points = [str(p) for p in (about.get("points") or []) if str(p).strip()]
    areas = [str(a) for a in (cfg.get("focus") or []) if str(a).strip()]

    out, y = "", 48
    if body:
        for i, line in enumerate(cards._wrap(body, SPAN, 10)):
            out += cards._g(cards.D_LETTER + i * 0.04,
                            bp.text(X0, y, line, t, size=10))
            y += 14.5
        y += 6

    if points:
        if body:
            out += cards._drawn_rule(X0, y, X1, y, t, cards.D_RULE, w=0.8,
                                     dur=0.8)
            y += 20
        # One gutter for the whole block, sized to the widest number, so the
        # notes hang off a single margin. _numbered_note carries the bold runs
        # from the markdown through as weight-600 runs laid end to end.
        gutter = cards._w(f"{len(points)}. ", 9.5)
        for i, p in enumerate(points):
            svg, y = cards._numbered_note(X0, y, SPAN, f"{i + 1}.", p, t,
                                          cards.D_DATA + i * 0.08, size=9.5,
                                          lead=13.5, gutter=gutter)
            out += svg
            y += 8
        y += 4

    if areas:
        out += cards._drawn_rule(X0, y, X1, y, t, cards.D_RULE + 0.08, w=0.8,
                                 dur=0.8)
        y += 18
        out += cards._g(cards.D_LETTER + 0.2,
                        bp.caps(X0, y, "FOCUS", t, size=7, track=1.1))
        y += 12
        # Tags wrap to as many rows as the measure needs. More rows than the
        # wide sheet is the correct outcome, not a fault.
        svg, y = cards._focus_strip(X0, y, SPAN, areas, t, cards.D_DATA + 0.3)
        out += svg

    if not (body or points or areas):
        out += cards._nodata(X0, 48, SPAN, 46, t, label="NO GENERAL NOTES")
        y = 94

    H = int(y + 30)
    return _sheet("general", H, t, out, label="GENERAL NOTES")


# ── sheet 7: notes ───────────────────────────────────────────────────────────


def _composition(cfg, data, t):
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
    # Same rule as the wide sheet, and the condition is on `langs` rather than
    # `kept` for the same reason: with no language data at all, a remainder
    # computed from an empty `kept` comes out as 1.0 and the bar would letter
    # OTHER 100%, which is a fabricated measurement. No data has to reach the
    # voided-field branch below.
    rest = max(0.0, 1.0 - sum(s for _n, s in kept)) if langs else 0.0
    segments = kept + ([("OTHER", rest)] if rest > 0.005 else [])

    defs = ""
    for i, (name, _s) in enumerate(segments):
        c = t["faint"] if name == "OTHER" else cards._lang_color(cfg, name, t,
                                                                 spare_at=i)
        defs += bp.defs_hatch(i, c, angle=cards.HATCH_ANGLES[
            i % len(cards.HATCH_ANGLES)], gap=5, w=1.0)

    bar_y, bar_h = 46, 24
    out = ""
    if not segments:
        out += cards._nodata(X0, bar_y, SPAN, bar_h + 10, t,
                             label="NO LANGUAGE DATA")
        legend_y = bar_y + bar_h + 44
    else:
        out += cards._g(cards.D_RULE,
                        f'<rect x="{X0}" y="{bar_y}" width="{SPAN}" '
                        f'height="{bar_h}" fill="{t["fill"]}" '
                        f'stroke="{t["rule"]}" stroke-width="1"/>')
        sx = float(X0)
        for i, (name, share) in enumerate(segments):
            sw = SPAN * share
            c = t["faint"] if name == "OTHER" else cards._lang_color(
                cfg, name, t, spare_at=i)
            out += cards._g(cards.D_DATA + i * 0.10,
                            cards._grow_bar(sx, bar_y, sw, bar_h,
                                            f"url(#h{i})",
                                            cards.D_DATA + i * 0.10,
                                            stroke=c, sw=0.9))
            sx += sw
        # Dimension the whole run with the corpus it was measured over.
        out += cards._g(cards.D_DATA + 0.5,
                        bp.dim(X0, X1, bar_y + bar_h + 18,
                               cards._bytes(data.get("total_bytes")), t))
        legend_y = bar_y + bar_h + 54

    repos, since = data.get("repos"), data.get("since_year")
    meta = " · ".join(s for s in (
        f"{repos} REPOS" if repos else "",
        f"SINCE {since}" if since else "") if s)
    if meta:
        out += cards._g(cards.D_LETTER + 0.2,
                        bp.caps(X0, legend_y, meta, t, size=7, track=1.1))
    legend_y += 17

    # One legend column. Two would leave 125px a row, and a language name plus
    # its share does not fit in that without cutting the name, which is the one
    # thing the legend exists to state. The swatch still carries the hatch, so
    # the legend keys the bar by pattern and not only by colour.
    row_h = 17
    for i, (name, share) in enumerate(segments):
        ry = legend_y + i * row_h
        c = t["faint"] if name == "OTHER" else cards._lang_color(cfg, name, t,
                                                                 spare_at=i)
        d = cards.D_DATA + 0.35 + i * 0.05
        out += cards._g(d, f'<rect x="{X0:.1f}" y="{ry-9:.1f}" width="15" '
                           f'height="11" fill="url(#h{i})" stroke="{c}" '
                           f'stroke-width="0.9"/>')
        out += cards._g(d, bp.text(X0 + 21, ry,
                                   cards._fit(name, SPAN - 82, 9), t, size=9))
        out += cards._g(d, bp.text(X1, ry, cards._pct(share, 1), t, size=9,
                                   color="soft", anchor="end"))

    foot_y = legend_y + max(0, len(segments) - 1) * row_h + 22
    for i, line in enumerate(cards._wrap(
            "each repo weighted equally · generated and vendored excluded",
            SPAN, 6.9)):
        out += cards._g(cards.D_LETTER + 0.45 + i * 0.04,
                        bp.text(X0, foot_y, line, t, size=6.9, color="faint"))
        foot_y += 10

    H = int(foot_y + 22)
    return _sheet("composition", H, t, out, defs=defs,
                  label="MATERIAL COMPOSITION")


# ── sheet 6: push activity ───────────────────────────────────────────────────

def _activity(cfg, data, t):
    px0, px1 = X0 + 22, X1              # left gutter carries the axis labels
    pty, pby = 52, 150                  # plot top / baseline
    act = list(data.get("activity") or [])

    out = ""
    if not act:
        out += cards._nodata(px0, pty, px1 - px0, pby - pty, t,
                             label="NO ACTIVITY DATA")
    else:
        counts = [int(c or 0) for _d, c in act]
        peak = max(counts)
        # 18% headroom keeps the peak's dimension line clear of the plot border
        # instead of letting the label collide with the frame.
        scale = (peak * 1.18) if peak else 1.0

        out += cards._drawn_rule(px0, pby, px1, pby, t, cards.D_RULE, w=1.2,
                                 color="rule")
        out += cards._drawn_rule(px0, pty, px0, pby, t, cards.D_RULE + 0.06,
                                 w=1.2, color="rule")

        # Zero and peak only. The wide sheet also ticks the midpoint; at this
        # height three labels in 98px sit close enough to read as one smudge,
        # and the midpoint is the one a reader can infer.
        for v in sorted({0, peak}):
            gy = pby - (v / scale) * (pby - pty)
            out += cards._g(cards.D_RULE + 0.2,
                            bp.rule(px0 - 3.5, gy, px0, gy, t, w=0.9))
            out += cards._g(cards.D_LETTER,
                            bp.text(px0 - 6, gy + 3, str(v), t, size=7,
                                    color="faint", anchor="end"))

        slot = (px1 - px0) / len(act)
        bw = max(1.6, slot * 0.66)
        for i, c in enumerate(counts):
            cx = px0 + slot * i + (slot - bw) / 2
            h = (c / scale) * (pby - pty)
            if h > 0:
                out += cards._grow_col(cx, pby, bw, h, t["accent"],
                                       cards.D_DATA + i * 0.012)
            # A tick under every fifth day is a picket fence at this pitch, so
            # only the two days that carry a date label are ticked.
            if i in (0, len(counts) - 1):
                out += cards._g(cards.D_RULE + 0.25,
                                bp.rule(cx + bw / 2, pby, cx + bw / 2,
                                        pby + 3.5, t, w=0.8))

        if peak:
            ypk = pby - (peak / scale) * (pby - pty)
            out += cards._g(cards.D_DATA + 0.5,
                            bp.dim(px0, px1, ypk, f"PEAK {peak}", t,
                                   color="soft"))

        first = cards._datestr(act[0][0], "%m-%d") or ""
        last = cards._datestr(act[-1][0], "%m-%d") or ""
        out += cards._g(cards.D_LETTER + 0.2,
                        bp.caps(px0, pby + 14, first, t, size=6.8, track=0.8))
        out += cards._g(cards.D_LETTER + 0.2,
                        bp.caps(px1, pby + 14, last, t, size=6.8, track=0.8,
                                anchor="end"))

    # The GitHub events API does not carry per-push commit counts, so the axis
    # says PUSHES. Labelling it COMMITS would be a nicer number and a false one.
    lx, ly = X0 + 6, (pty + pby) / 2
    out += cards._g(cards.D_LETTER,
                    f'<g transform="rotate(-90 {lx} {ly:.1f})">'
                    + bp.caps(lx, ly, "PUSHES", t, size=7.4, track=1.6,
                              anchor="middle") + "</g>")

    # The footer stacks rather than setting MOST ACTIVE and LAST PUSH on one
    # line: side by side they would leave each about 130px, which cuts the
    # second repository name off every time.
    fy = pby + 30
    tops = [cards._repo_name(n) for n, _c in (data.get("top_repos") or [])][:3]
    out += cards._g(cards.D_LETTER + 0.35,
                    bp.caps(X0, fy, "MOST ACTIVE", t, size=6.8, track=1.1))
    out += cards._g(cards.D_DATA + 0.4,
                    bp.text(X0, fy + 13,
                            cards._fit(" · ".join(tops) if tops else cards.DASH,
                                       SPAN, 8.4), t, size=8.4, color="soft"))
    lp = data.get("last_push") or {}
    stamp = cards._datestr(lp.get("at"), "%Y-%m-%d %H:%M")
    out += cards._g(cards.D_DATA + 0.45,
                    bp.caps(X0, fy + 27, f"LAST PUSH {stamp or cards.DASH}", t,
                            size=6.8, track=0.9))

    H = int(fy + 50)
    return _sheet("activity", H, t, out, label="PUSH ACTIVITY / 30 D")


RENDERERS = {
    "titleblock": _titleblock,
    "general": _general,
    "composition": _composition,
    "activity": _activity,
}
