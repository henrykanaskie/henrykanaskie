#!/usr/bin/env python3
"""Phone layouts for the two sheets built out of side-by-side columns.

The wide BOM is a six-column table and the wide telemetry sheet is four or five
vertical panels standing next to each other. Both depend on having 900px to
divide up. At 300 there is nothing to divide, so neither sheet is rescaled here:
the BOM's row becomes a stacked block and telemetry's panel becomes a full-width
row, and everything the wide sheet says is said again in the same words.

Nothing in here is a second, looser version of the drawing. The completion
figure is still a real dimension line with a hatched fill under it, the fill is
still the part's own material hatch, and the ground track is still plotted from
the orbit's inclination rather than drawn as a wave. Those are the sheets; a
phone layout that dropped them would be a different drawing.

`cards` is reached through the module at call time rather than by from-import.
This module is imported from the bottom of cards.py, while cards is still being
defined, so `from cards import _w` would bind a name that does not exist yet.
"""

from __future__ import annotations

try:                                    # scripts/ on sys.path (build.py's case)
    import blueprint as bp
    import cards
except ModuleNotFoundError:             # imported as part of a package
    from . import blueprint as bp
    from . import cards


# ── shared narrow metrics ────────────────────────────────────────────────────
#
# The frame inset is 8, and content is held 10 further in so the lettering does
# not crowd the border rule. That leaves 264px, which is what every column
# budget on both sheets is measured against.

X0 = cards.NARROW_INSET + 10
X1 = cards.NARROW_W - cards.NARROW_INSET - 10
CONTENT_W = X1 - X0


def _wrap_capped(s, px, size, track, limit):
    """Word-wrap `s` to at most `limit` lines, cutting the last one to fit.

    Wrapping alone would let a long run push the block taller than the space
    budgeted for it; truncating alone would throw away text that the width can
    genuinely hold. Doing both means a two-line note sets as two lines and a
    six-line one ends in an ellipsis instead of running off the sheet.
    """
    spans = cards._wrap_spans(s, px, size, track)
    if not spans:
        return []
    if len(spans) <= limit:
        return [s[a:b] for a, b in spans]
    out = [s[a:b] for a, b in spans[:limit - 1]]
    out.append(cards._fit(s[spans[limit - 1][0]:], px, size, track))
    return out


# ── sheet 3: bill of materials ───────────────────────────────────────────────

BOM_TX = X0 + 22        # text column: clear of the balloon on the identity line
BOM_TW = X1 - BOM_TX

BOM_NAME_SIZE = 12
BOM_SUM_SIZE = 8.6
BOM_NOTE_SIZE = 7.6


def _bom_block(cfg, p, i, langs, statuses, top, d, t):
    """One part, stacked. Returns (svg, height, status_y).

    The wide sheet reads left to right across six columns; this reads top to
    bottom through the same six facts in the same order, so a reader who knows
    one sheet knows the other. Height is returned rather than assumed because
    the summary and the tolerance callouts both wrap, and a block sized for one
    line of each would clip every part that has two.

    `status_y` is where the status line starts. It is the one row of the block
    whose right half is always empty, so it is where the revision flag goes if
    the flag is switched on. The block has to say where that is, because only
    the block knows how far the description wrapped.
    """
    out = ""
    y = top

    # ── identity line: balloon, designator, material ────────────────────────
    out += cards._g(d, bp.balloon(X0 + 8, y + 9, i + 1, t, r=8))
    pn = str(p.get("pn") or cards.DASH)
    out += cards._g(d, bp.text(BOM_TX, y + 12.5, pn, t, size=9, color="soft",
                               track=0.4))

    lang = str(p.get("lang") or "")
    hi = langs.index(lang) if lang in langs else None
    if lang:
        # The swatch hangs off the right edge with its label, so the material
        # reads as a property of the part rather than as another line of prose.
        avail = X1 - (BOM_TX + cards._w(pn, 9, 0.4) + 8) - 20
        shown = cards._fit(lang, max(20.0, avail), 8.5)
        lw = cards._w(shown, 8.5)
        lc = cards._lang_color(cfg, lang, t, spare_at=hi)
        out += cards._g(d, bp.text(X1, y + 12.5, shown, t, size=8.5,
                                   anchor="end"))
        sx = X1 - lw - 5 - 15
        out += cards._g(d, f'<rect x="{sx:.1f}" y="{y+3.5:.1f}" width="15" '
                           f'height="11" fill="url(#h{hi})" stroke="{lc}" '
                           f'stroke-width="0.9"/>')
    else:
        out += cards._g(d, bp.text(X1, y + 12.5, cards.DASH, t, size=8.5,
                                   color="faint", anchor="end"))
    y += 22

    # ── name ────────────────────────────────────────────────────────────────
    name = str(p.get("name") or cards.DASH)
    nsize = cards._fit_size(name, BOM_TW, BOM_NAME_SIZE, 0.02, floor=9)
    out += cards._g(d, bp.text(BOM_TX, y + 10, name, t, size=nsize, weight=700,
                               track=0.2))
    y += 15

    # ── description ─────────────────────────────────────────────────────────
    summary = " ".join(str(p.get("summary") or "").split())
    if summary:
        lines = _wrap_capped(summary, BOM_TW, BOM_SUM_SIZE, 0.0, 3)
        for k, line in enumerate(lines):
            out += cards._g(d + 0.05, bp.text(BOM_TX, y + 8, line, t,
                                              size=BOM_SUM_SIZE, color="soft"))
            y += 10.5
        y += 2

    # ── tolerance callouts ──────────────────────────────────────────────────
    # The project's own notes. On the wide sheet they run out right-aligned the
    # way a tolerance block sits under a feature; at 264 a right-aligned wrapped
    # run reads as ragged prose, so they hang off the same text column instead.
    notes = [str(x) for x in (p.get("notes") or []) if str(x).strip()][:3]
    if notes:
        run = " · ".join(notes)
        for line in _wrap_capped(run, BOM_TW, BOM_NOTE_SIZE, 0.2, 2):
            out += cards._g(d + 0.1, bp.text(BOM_TX, y + 7, line, t,
                                             size=BOM_NOTE_SIZE, color="faint",
                                             track=0.2))
            y += 9.5
        y += 3

    # ── status ──────────────────────────────────────────────────────────────
    status_y = y
    key = str(p.get("status") or "")
    rank, entry = statuses.get(key, (len(cards.STATUS_COLORS) - 1, {}))
    scol = cards.STATUS_COLORS[min(rank, len(cards.STATUS_COLORS) - 1)]
    out += cards._g(d, bp.text(BOM_TX, y + 9, entry.get("mark") or "○", t,
                               size=11, color=scol))
    out += cards._g(d, bp.caps(BOM_TX + 15, y + 8,
                               cards._fit(key or cards.DASH, BOM_TW - 15, 8.5,
                                          0.9),
                               t, size=8.5, track=0.9, color="ink"))
    y += 15

    # ── completion, dimensioned ─────────────────────────────────────────────
    # Still a measurement, so still drawn as one: a dimension line across the
    # text column with the value broken into it, and a hatched bar underneath
    # showing how much of the run is filled.
    try:
        frac = min(1.0, max(0.0, float(p.get("completion") or 0.0)))
    except (TypeError, ValueError):
        frac = 0.0
    span = BOM_TW
    out += cards._g(d + 0.12, bp.dim(BOM_TX, X1, y + 13, cards._pct(frac), t))
    out += cards._g(d + 0.12,
                    f'<rect x="{BOM_TX:.1f}" y="{y+17:.1f}" width="{span:.1f}" '
                    f'height="7" fill="{t["fill"]}" stroke="{t["rule"]}" '
                    f'stroke-width="0.7"/>')
    if frac > 0:
        # rank 0 is the top of the configured status vocabulary, whatever it is
        # called, so renaming QUALIFIED does not quietly turn the green off.
        # The hatch keeps the material's own angle and only changes colour.
        if rank == 0:
            fillref = f"url(#hg{hi})" if hi is not None else "url(#hgx)"
            stroke = t["green"]
        else:
            fillref = f"url(#h{hi})" if hi is not None else t["accent"]
            stroke = cards._lang_color(cfg, lang, t, spare_at=hi or 0) \
                if lang else t["accent"]
        out += cards._grow_bar(BOM_TX, y + 17, span * frac, 7, fillref,
                               d + 0.3, stroke=stroke, sw=0.7)
    y += 27

    return out, (y + 6) - top, status_y


def _bom(cfg, data, t):
    projects = list(cfg.get("projects") or [])
    n = len(projects)
    statuses = cards._status_map(cfg)

    # One hatch per distinct material, angle by first appearance, exactly as the
    # wide sheet assigns them, plus a green twin of each for finished parts and
    # one fallback for a finished part with no material recorded at all.
    langs, defs = [], ""
    for p in projects:
        lang = str(p.get("lang") or "")
        if lang and lang not in langs:
            langs.append(lang)
    for i, lang in enumerate(langs):
        c = cards._lang_color(cfg, lang, t, spare_at=i)
        angle = cards.HATCH_ANGLES[i % len(cards.HATCH_ANGLES)]
        defs += bp.defs_hatch(i, c, angle=angle, gap=4.5, w=1.0)
        defs += bp.defs_hatch(f"g{i}", t["green"], angle=angle, gap=4.5, w=1.0)
    defs += bp.defs_hatch("gx", t["green"], angle=45, gap=4.5, w=1.0)

    # Column headers are meaningless once the columns are gone, but the two that
    # bracket every block still are: a part starts at its balloon and ends at its
    # completion. Keeping those two words keeps the sheet's vocabulary.
    out = cards._g(cards.D_LETTER,
                   bp.caps(X0, 44, "ITEM", t, size=7.4, track=1.2)
                   + bp.caps(X1, 44, "COMPLETION", t, size=7.4, track=1.2,
                             anchor="end"))
    out += cards._drawn_rule(X0, 50, X1, 50, t, cards.D_RULE, w=1.6,
                             color="rule", dur=0.9)

    if not projects:
        out += cards._nodata(X0, 66, CONTENT_W, 34, t, label="NO PARTS LISTED")
        return bp.sheet(cards.NARROW_W, 132, t, out, defs=defs,
                        label="BILL OF MATERIALS",
                        sheet_no=cards._sheet_no("bom"),
                        inset=cards.NARROW_INSET)

    changed = cards._repo_name((data.get("last_push") or {}).get("repo")) \
        .casefold()
    mark_last_push = bool((cfg.get("bom") or {}).get("mark_last_push", False))
    cloud = ""

    y = 56
    for i, p in enumerate(projects):
        d = cards.D_DATA + i * 0.05
        if i:
            out += cards._g(cards.D_RULE + 0.15 + i * 0.02,
                            bp.rule(X0, y, X1, y, t, w=0.6, opacity=0.75))
        block, bh, sy = _bom_block(cfg, p, i, langs, statuses, y, d, t)
        out += block

        # Off by default: [bom] mark_last_push in profile.toml. Genuine drafting
        # practice, but red is the loudest mark on the sheet and it lands on a
        # different part every day, so it reads as an alarm rather than a note.
        name = str(p.get("name") or "")
        if mark_last_push and changed and name.casefold() == changed:
            cd = cards.D_DATA + n * 0.05 + 0.35
            cloud = bp.revcloud(X0 + 2, y + 2, CONTENT_W - 4, bh - 8, t,
                                delay=cd)
            rev_letter = str((cfg.get("identity") or {}).get("revision") or "")
            flag = f"REV {rev_letter}".strip()
            # On the status line, not the identity line: the identity line's
            # right half is the material swatch, and the flag would sit on it.
            cloud += cards._g(cd + 0.45,
                              f'<rect x="{X1-44:.1f}" y="{sy:.1f}" width="42" '
                              f'height="13" rx="1.5" fill="{t["ground"]}" '
                              f'stroke="{t["red"]}" stroke-width="1"/>'
                              f'<text x="{X1-23:.1f}" y="{sy+9.5:.1f}" '
                              f'fill="{t["red"]}" font-size="7.5" '
                              f'text-anchor="middle" letter-spacing="0.8" '
                              f'font-weight="700">{bp.esc(flag)}</text>')
        y += bh

    out += cards._g(cards.D_RULE + 0.2, bp.rule(X0, y, X1, y, t, w=1.2))
    out += cloud

    # Footer: the status vocabulary, so the marks above are readable without the
    # README next to it. It wraps, because four statuses fit on one line and six
    # would not, and a vocabulary running off the frame is worse than two lines.
    legend, lx, ly = "", X0, y + 20
    for skey, (rank, entry) in sorted(statuses.items(), key=lambda kv: kv[1][0]):
        adv = 11 + cards._w(skey, 7, 0.9) + 11
        if lx > X0 and lx + adv > X1:
            lx, ly = X0, ly + 13
        c = cards.STATUS_COLORS[min(rank, len(cards.STATUS_COLORS) - 1)]
        legend += bp.text(lx, ly, entry.get("mark") or "", t, size=9, color=c)
        legend += bp.caps(lx + 11, ly - 1, skey, t, size=7, track=0.9)
        lx += adv
    legend += bp.caps(X1, ly + 15, f"{n} PARTS", t, size=7, track=1.1,
                      anchor="end")
    out += cards._g(cards.D_LETTER + 0.4, legend)

    # The part count and the sheet number are both right-aligned runs of caps,
    # and blueprint.sheet writes the sheet number 16px off the bottom edge. The
    # footer is deep enough to keep a clear line between the two.
    return bp.sheet(cards.NARROW_W, ly + 52, t, out, defs=defs,
                    label="BILL OF MATERIALS", sheet_no=cards._sheet_no("bom"),
                    inset=cards.NARROW_INSET)


# ── sheet 4: telemetry ───────────────────────────────────────────────────────
#
# Each panel is a function of (x, w, y, t, delay, data) returning (svg, height),
# the same shape the wide panels have, except that a narrow panel voids itself
# at a height it picks rather than being squared off against its neighbours.
# There are no neighbours to square off against once they are stacked, and a
# dashed box as tall as the tallest row would be a large empty rectangle
# claiming more attention than the channel that is actually down.


def _p_launch(x, w, y, t, d, data):
    launch = data.get("launch") or None
    if not launch:
        return cards._nodata(x, y, w, 52, t, delay=d,
                             label="NO LAUNCH DATA"), 52

    cd = cards._countdown(launch.get("net"), data.get("generated_at"))
    if cd:
        # The countdown is the headline of the panel and stays large. At 264 the
        # full T-minus run still sets at 24px, so the fit is a guard rather than
        # the normal path.
        size = cards._fit_size(cd, w, 24, 0.06, floor=13)
        out = cards._g(d, bp.text(x, y + 22, cd, t, size=size, weight=700,
                                  track=size * 0.06), dur=0.5)
    else:
        out = cards._g(d, bp.text(x, y + 22, cards.DASH, t, size=24,
                                  color="faint"))
    out += cards._g(d + 0.05, bp.rule(x, y + 31, x + w, y + 31, t, w=0.7,
                                      opacity=0.8))

    # The launch API's list mode returns "Vehicle | Mission" as one string, and
    # the pad is always absent, so rows are built from what is there rather than
    # reserving a line that would be blank every day.
    vehicle, _, mission = str(launch.get("name") or cards.DASH).partition("|")
    rows = [(vehicle.strip() or cards.DASH, 11, "ink", 700)]
    if mission.strip():
        rows.append((mission.strip(), 8.6, "soft", 400))
    if launch.get("provider"):
        rows.append((str(launch["provider"]), 8.6, "soft", 400))

    ry = y + 47
    for s, size, color, weight in rows:
        out += cards._g(d + 0.1, bp.text(x, ry, cards._fit(s, w, size), t,
                                         size=size, color=color, weight=weight))
        ry += 14

    # Full width buys a label and its value on one line, which the wide panel
    # cannot do in a column a third this wide.
    status = str(launch.get("status") or "").strip()
    out += cards._g(d + 0.15, bp.caps(x, ry + 8, "STATUS", t, size=6.8,
                                      track=1.0))
    out += cards._g(d + 0.18,
                    bp.caps(x + w, ry + 8,
                            cards._fit(status or cards.DASH, w - 60, 9.5, 1.2),
                            t, size=9.5, track=1.2, anchor="end",
                            color="accent" if status else "faint"))
    return out, (ry + 14) - y


def _p_humans(x, w, y, t, d, data):
    humans = data.get("humans")
    if humans is None:
        return cards._nodata(x, y, w, 44, t, delay=d, label="NO DATA"), 44
    # The count is the figure; the words are its unit. Side by side rather than
    # stacked under a centred numeral, which at 264 would leave the row mostly
    # empty on both sides.
    val = str(humans)
    out = cards._g(d, bp.text(x, y + 38, val, t, size=44, weight=700,
                              track=1.0), dur=0.6)
    lx = x + cards._w(val, 44, 1.0) + 14
    out += cards._g(d + 0.1, bp.caps(lx, y + 22, "HUMANS", t, size=9,
                                     track=1.3))
    out += cards._g(d + 0.1, bp.caps(lx, y + 36, "IN SPACE", t, size=9,
                                     track=1.3))
    return out, 48


def _p_iss(x, w, y, t, d, data):
    iss = data.get("iss") or None
    gh = w / 2.0                          # equirectangular is 2:1 by definition
    if not iss:
        return cards._nodata(x, y, w, 96, t, delay=d, label="NO ISS FIX"), 96
    try:
        lat0 = float(iss.get("lat"))
        lon0 = float(iss.get("lon"))
    except (TypeError, ValueError):
        return cards._nodata(x, y, w, 96, t, delay=d, label="NO ISS FIX"), 96

    # Both take their geometry as arguments, so the narrow plot is the same
    # graticule and the same solved sinusoid, drawn into a smaller box. Nothing
    # about the maths is width-dependent.
    out = cards._graticule(x, y, w, gh, t, d)
    out += cards._iss_track(lat0, lon0, x, y, w, gh, t, d + 0.25)

    vel, alt = iss.get("vel_kmh"), iss.get("alt_km")
    readout = (("LAT", f"{lat0:+.2f}°"),
               ("LON", f"{lon0:+.2f}°"),
               ("ALT", f"{float(alt):.1f} KM" if alt is not None else cards.DASH),
               ("VEL", f"{float(vel):,.0f} KM/H".replace(",", " ")
                if vel is not None else cards.DASH))
    # The graticule letters its longitude ticks just under its own frame, so the
    # readout clears them rather than landing on them.
    ry = y + gh + 22
    half = w / 2
    for i, (k, v) in enumerate(readout):
        cx = x + (i % 2) * half
        yy = ry + (i // 2) * 13
        out += cards._g(d + 0.35 + i * 0.04, bp.caps(cx, yy, k, t, size=7,
                                                     track=1.0))
        out += cards._g(d + 0.35 + i * 0.04,
                        bp.text(cx + half - 14, yy, v, t, size=8.4, color="ink",
                                anchor="end"))
    stamp = cards._datestr(iss.get("at"), "%H:%M:%S")
    # An orbital fix is an observation at an instant, not a live feed.
    out += cards._g(d + 0.5,
                    bp.caps(x, ry + 30, f"SAMPLED {stamp or cards.DASH} UTC", t,
                            size=6.8, track=0.9))
    return out, (ry + 34) - y


def _p_contact(x, w, y, t, d, data):
    lp = data.get("last_push") or {}
    age = cards._ago(lp.get("at"), data.get("generated_at"))
    act = data.get("activity") or []
    out, yy = "", y + 10

    if age or lp.get("repo"):
        out += cards._stat(x, w, yy, "LAST CONTACT", age or cards.DASH, t, d)
        out += cards._g(d + 0.1,
                        bp.text(x, yy + 32,
                                cards._fit(cards._repo_name(lp.get("repo"))
                                           or cards.DASH, w, 8.6), t, size=8.6,
                                color="soft"))
    else:
        out += cards._nodata(x, yy - 8, w, 44, t, delay=d, label="NO CONTACT")
    yy += 50

    # Two readings that are both short pair up across the width; the quietest
    # part carries a repository name under it and takes the full row.
    half = w / 2
    streak = data.get("streak")
    sval = f"{streak} DAY{'S' if streak != 1 else ''}" if streak is not None \
        else cards.DASH
    out += cards._stat(x, half - 8, yy, "STREAK", sval, t, d + 0.12, size=14)

    last24 = act[-1][1] if act else None
    out += cards._stat(x + half, half, yy, "PUSHES / 24 H",
                       str(last24) if last24 is not None else cards.DASH, t,
                       d + 0.2, size=14)
    yy += 38

    # The far end of the same measurement: the part nobody has touched in
    # longest. Three-digit day counts are normal, so the value is fitted.
    q = data.get("quietest") or {}
    days = q.get("days")
    out += cards._stat(x, w, yy, "QUIETEST",
                       f"{days} DAYS" if days is not None else cards.DASH, t,
                       d + 0.26, size=14)
    if q.get("repo"):
        out += cards._g(d + 0.3,
                        bp.text(x, yy + 32,
                                cards._fit(cards._repo_name(q["repo"]), w, 8.6),
                                t, size=8.6, color="soft"))
    return out, (yy + 38) - y


def _p_audio(x, w, y, t, d, data):
    # The wide audio panel is already a single narrow column of three runs, so
    # it reflows to 264 unchanged. Rewriting it here would only be a second
    # place for the same three lines to drift apart.
    svg, h, _void = cards._panel_audio(x, w, y, t, d, data)
    return svg, h


def _telemetry(cfg, data, t):
    panels = [("LAUNCH WINDOW", _p_launch),
              ("OFF-PLANET", _p_humans),
              ("ISS GROUND TRACK", _p_iss),
              ("CONTACT", _p_contact)]
    # The audio channel is off by configuration, not broken, so it is omitted
    # rather than voided. A NO DATA cell would imply a failure that never
    # happened.
    if data.get("listening"):
        panels.append(("AUDIO CHANNEL", _p_audio))

    out, y = "", 42
    for i, (title, fn) in enumerate(panels):
        d = cards.D_DATA + i * 0.08
        out += cards._g(cards.D_LETTER + i * 0.06,
                        bp.caps(X0, y, cards._fit(title, CONTENT_W, 7.6, 1.3),
                                t, size=7.6, track=1.3))
        # The same head rule the wide panels carry. Stacked, it is also the rule
        # between one row and the one above it.
        out += cards._drawn_rule(X0, y + 8, X1, y + 8, t,
                                 cards.D_RULE + 0.05 + i * 0.04, w=0.8, dur=0.6)
        svg, h = fn(X0, CONTENT_W, y + 16, t, d, data)
        out += svg
        y += 16 + h + 20

    stamp = cards._datestr(data.get("generated_at"), "%Y-%m-%d %H:%M") \
        or cards.DASH
    # The sheet's own timestamp, distinct from the ISS panel's fix time.
    out += cards._g(cards.D_LETTER + 0.5,
                    bp.caps(X0, y, f"GENERATED {stamp} UTC", t, size=6.8,
                            track=1.0))
    return bp.sheet(cards.NARROW_W, y + 22, t, out, label="DAILY TELEMETRY",
                    sheet_no=cards._sheet_no("telemetry"),
                    inset=cards.NARROW_INSET)


RENDERERS = {"bom": _bom, "telemetry": _telemetry}
