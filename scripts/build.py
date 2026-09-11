#!/usr/bin/env python3
"""Build the profile: validate the config, fetch the day's data, emit the cards
and the README.

    python3 scripts/build.py             # full build, hits the network
    python3 scripts/build.py --offline   # sample data, no network calls
    python3 scripts/build.py --check     # validate the config and stop

Everything on the profile is derived from data/profile.toml. Nothing downstream
of this script holds a project fact, so a wrong status on the profile is a wrong
status in that one file.

Standard library only, on purpose: the daily workflow installs nothing, so there
is no dependency that can break the build at 6am while nobody is looking.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import re
import sys
import tomllib
import xml.dom.minidom
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import blueprint  # noqa: E402
import cards      # noqa: E402
import sources    # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "data" / "profile.toml"
ASSETS = ROOT / "assets"
TEMPLATE = ROOT / "templates" / "README.md.tmpl"
README = ROOT / "README.md"

RAW = "https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets"

# Labels on the two chip rails. They read as drawing furniture, so they are set
# in the same small caps as the zone letters rather than as a sentence.
LINK_LABEL = "REFERENCES"
REPO_LABEL = "SOURCE"

# GitHub renders a README into an 846 CSS pixel column on a desktop profile page
# and 861 in the blob view. Measured, not guessed.
README_COL = 846


# ── validation ───────────────────────────────────────────────────────────────

class ConfigError(Exception):
    """A problem in profile.toml, reported with the offending project named."""


def normalize(cfg: dict) -> dict:
    """Flatten the two list-valued sections onto the top level.

    `field_notes` and `focus` are declared as [notes].field and [focus].areas
    rather than as bare top-level arrays. TOML binds a bare key to the most
    recent table header, so an array written after the last [[projects]] block
    silently becomes a field of that project instead of a top-level key, and
    the profile then renders with no notes and no explanation. Wrapping each in
    its own table makes their position in the file irrelevant.

    Everything downstream still reads cfg["field_notes"] and cfg["focus"].
    """
    cfg["field_notes"] = cfg.get("notes", {}).get("field", [])
    cfg["focus"] = cfg.get("focus", {}).get("areas", [])
    return cfg


# Keys that must never appear inside a project or a tool table. Each one is
# a top-level array someone moved without moving its table header with it.
STRAY = ("field_notes", "focus", "areas", "field")


def validate(cfg: dict) -> None:
    """Check the config before anything is rendered from it.

    A malformed config that renders anyway produces a profile that is quietly
    wrong, which is worse than a build that stops and says why. Each check names
    the project it failed on so the fix is obvious without reading this file.
    """
    problems: list[str] = []

    statuses = {s["key"]: s for s in cfg.get("status", [])}
    if not statuses:
        raise ConfigError("no [[status]] entries defined")

    # Bands are declared by floor. Sorting descending gives each status the
    # half-open interval [floor, next_floor_above).
    ordered = sorted(statuses.values(), key=lambda s: -s["floor"])
    ceilings = {}
    prev = 1.01
    for s in ordered:
        ceilings[s["key"]] = prev
        prev = s["floor"]

    langs = cfg.get("palette", {}).get("lang", {})
    seen_pn, seen_name = set(), set()

    for p in cfg.get("projects", []):
        who = p.get("name", "<unnamed>")

        for required in ("pn", "name", "lang", "status", "completion",
                         "description"):
            if not p.get(required) and p.get(required) != 0:
                problems.append(f"{who}: missing required field '{required}'")

        st = p.get("status")
        if st and st not in statuses:
            problems.append(
                f"{who}: status '{st}' is not one of {sorted(statuses)}")
        elif st:
            c = p.get("completion")
            if not isinstance(c, (int, float)) or not 0.0 <= c <= 1.0:
                problems.append(f"{who}: completion {c!r} is not within 0.0 to 1.0")
            elif not statuses[st]["floor"] <= c < ceilings[st]:
                problems.append(
                    f"{who}: completion {c} falls outside the {st} band "
                    f"[{statuses[st]['floor']}, {ceilings[st]})")

        if p.get("lang") and p["lang"] not in langs:
            problems.append(
                f"{who}: language '{p['lang']}' has no colour in [palette.lang]")

        if p.get("pn") in seen_pn:
            problems.append(f"{who}: duplicate part number {p.get('pn')}")
        seen_pn.add(p.get("pn"))
        if p.get("name") in seen_name:
            problems.append(f"{who}: duplicate project name")
        seen_name.add(p.get("name"))

        description = " ".join(str(p.get("description") or "").split())
        if not description:
            problems.append(
                f"{who}: no 'description'. One or two sentences saying what it "
                f"does and what it is useful for")
        else:
            lines = cards.description_lines(description)
            if lines > cards.DESC_LINES:
                problems.append(
                    f"{who}: the description wraps to {lines} lines and the "
                    f"row holds {cards.DESC_LINES}, so it would be cut with an "
                    f"ellipsis on the sheet. Trim it")

        if p.get("repo") and p.get("private"):
            problems.append(f"{who}: has both 'repo' and 'private'; pick one")
        if len(p.get("notes", [])) > 3:
            problems.append(
                f"{who}: {len(p['notes'])} notes; three is the most a row fits")
        run = " · ".join(str(x) for x in (p.get("notes") or []))
        ncap = cards.notes_capacity()
        if len(run) > ncap:
            problems.append(
                f"{who}: the notes run to {len(run)} characters joined and the "
                f"row letters {ncap}, so it would be cut with an ellipsis. "
                f"Trim by {len(run) - ncap}")

    # A stray key is the TOML table-binding trap: an array that drifted below a
    # table header and got absorbed by it. It parses cleanly and produces an
    # empty section on the profile, so nothing but this check will catch it.
    for p in cfg.get("projects", []):
        for k in STRAY:
            if k in p:
                problems.append(
                    f"{p.get('name', '<unnamed>')}: contains '{k}', which belongs "
                    f"at the top level. Move it above the [[projects]] blocks or "
                    f"give it its own table header")
    for tool in cfg.get("tools", []):
        for k in STRAY:
            if k in tool:
                problems.append(
                    f"tool {tool.get('name', '<unnamed>')!r}: contains '{k}', "
                    f"which belongs at the top level. Give it its own table "
                    f"header, or TOML binds it to the section above it")

    if not cfg.get("field_notes"):
        problems.append(
            "no field notes found. Expected a [notes] table with a `field` array")
    if not cfg.get("focus"):
        problems.append(
            "no focus areas found. Expected a [focus] table with an `areas` array")

    # The title block strip draws these two directly. They are the only fields
    # on it a build cannot measure, so an empty one letters as N/A on the sheet
    # and there is nothing downstream that would notice.
    for key in ("status", "location"):
        if not str(cfg.get("identity", {}).get(key) or "").strip():
            problems.append(
                f"[identity] has no '{key}'. It is a field in the title block "
                f"strip and nothing else can supply it")

    # The frameworks matrix is drawn one row per framework, so a project is on
    # it only by being named. A part nobody names gets a column of blanks, which
    # on this sheet reads as "installs nothing and uses nothing", and one of
    # those two is a claim and the other is an oversight that looks identical.
    known = {str(p.get("name", "")) for p in cfg.get("projects", [])}
    seen = set()
    for fw in cfg.get("frameworks", []):
        who = fw.get("name", "<unnamed>")
        if not str(fw.get("name") or "").strip():
            problems.append("a [[frameworks]] entry has no 'name'")
        if not isinstance(fw.get("bundled"), bool):
            problems.append(
                f"framework {who!r}: 'bundled' is {fw.get('bundled')!r}, "
                f"expected true (ships with the platform) or false (installed)")
        on = fw.get("on") or []
        if not on:
            problems.append(
                f"framework {who!r}: used by nothing, so it would draw an "
                f"empty row. Remove it or name the part that uses it")
        for name in on:
            if str(name) not in known:
                problems.append(
                    f"framework {who!r}: cites '{name}', which is not a part "
                    f"on the bill of materials. Known parts: "
                    f"{', '.join(sorted(known))}")
            else:
                seen.add(str(name))
    if cfg.get("frameworks"):
        for missing in sorted(known - seen):
            problems.append(
                f"{missing}: named by no framework, so its column on sheet "
                f"{cards.CARDS.index('frameworks') + 1} would be empty. An "
                f"empty column there means 'installs nothing', so a part that "
                f"is merely unlisted reads as a claim")

    weighting = cfg.get("languages", {}).get("weighting", "equal")
    if weighting not in ("equal", "bytes"):
        problems.append(
            f"[languages] weighting is {weighting!r}; expected 'equal' or 'bytes'")

    if problems:
        raise ConfigError(
            "profile.toml has %d problem(s):\n  - %s"
            % (len(problems), "\n  - ".join(problems)))


def _date(v):
    """A TOML date, a datetime, or an ISO string, as a plain date. Else None.

    tomllib hands back a real `datetime.date` for an unquoted date, so this is
    mostly a guard for a value someone quoted by habit.
    """
    if v is None:
        return None
    if isinstance(v, datetime.datetime):
        return v.date()
    if isinstance(v, datetime.date):
        return v
    try:
        return datetime.date.fromisoformat(str(v)[:10])
    except ValueError:
        return None


def _version(svg: str) -> str:
    """Short content hash used as the cache-busting query on an asset URL."""
    return hashlib.sha256(svg.encode()).hexdigest()[:10]


def _viewport(svg: str) -> tuple[float, float]:
    """Width and height of a rendered card, read back off its own root element.

    The stamp has to be centred on the card, and card heights are computed from
    content rather than fixed, so the only reliable source for the size is the
    SVG that was just produced.
    """
    m = re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', svg)
    if not m:
        raise ConfigError("rendered card has no parseable viewBox")
    return float(m.group(1)), float(m.group(2))


# ── README ───────────────────────────────────────────────────────────────────

def asset_url(stem: str, vers: dict) -> str:
    """URL for one written asset, versioned by the hash of its own bytes.

    The ?v= is not decoration. README images are cached hard, so without a URL
    that changes when the content does, a rebuild stays invisible for hours.

    This used to be the build date, and that was wrong at exactly the moment it
    mattered: iterating on the design changed the cards twenty-one times in one
    day while every URL still said v=20260824, so anyone who had loaded the page
    that morning kept seeing the first version. A content hash changes when, and
    only when, the bytes change. It is also stable across a rebuild that
    produces identical output, which keeps the workflow's "commit if changed"
    quiet on a day nothing moved.
    """
    return f"{RAW}/{stem}.svg?v={vers.get(stem, '0')}"


def picture(card: str, alt: str, vers: dict, width: str | None = None) -> str:
    """Four variants of one sheet: light and dark, wide and phone.

    Order matters. The browser takes the first <source> whose media matches, so
    the narrow pair has to come before the wide pair or a phone in dark mode
    would match the wide dark source and never reach its own layout.
    """
    w = f' width="{width}"' if width else ""
    brk = cards.CHIP_BREAK
    out = "<picture>\n"
    if cards.has_narrow(card):
        out += (f'  <source media="(max-width: {brk}px) and '
                f'(prefers-color-scheme: dark)" '
                f'srcset="{asset_url(card + "-narrow-dark", vers)}">\n'
                f'  <source media="(max-width: {brk}px)" '
                f'srcset="{asset_url(card + "-narrow-light", vers)}">\n')
    out += (f'  <source media="(prefers-color-scheme: dark)" '
            f'srcset="{asset_url(card + "-dark", vers)}">\n'
            f'  <img src="{asset_url(card + "-light", vers)}" alt="{alt}"{w}>\n'
            '</picture>')
    return out


def pack_rows(specs: list, label: str, width: int = README_COL) -> list:
    """Split a chip row into as many rows as the README column needs.

    Emitting every chip on one markdown line and letting the browser wrap it
    produced a first row packed to the edge and a second row holding one chip,
    which reads as a mistake rather than as a layout. Splitting here means the
    break is chosen rather than discovered, and the rows come out close to the
    same length.

    The leading rail only belongs to the first row. Repeating it would label
    each row as though they were different sets of things.

    Rows are balanced by target width rather than greedily: greedy packing is
    what produced the stranded chip in the first place. `n` rows of roughly
    `total / n` each is the same break a person would pick by eye.
    """
    if not specs:
        return []
    widths = [cards.chip_width(lab, accent=bool(acc))
              for _s, lab, _sh, _h, acc in specs]
    total = cards.rail_width(label) + sum(widths)
    n = max(1, -(-int(total) // width))
    if n == 1:
        return [specs]

    target = total / n
    rows, current, run = [], [], cards.rail_width(label)
    for spec, w in zip(specs, widths):
        # Start a new row when this chip would push the run past its share, but
        # never leave a row empty and never open a row that cannot be filled.
        if current and run + w > target and len(rows) < n - 1:
            rows.append(current)
            current, run = [], 0.0
        current.append(spec)
        run += w
    if current:
        rows.append(current)
    return rows


def chip_row(specs: list, vers: dict, label: str, slug: str) -> str:
    """Anchored chips, as one markdown line per row with no gaps inside a row.

    The chips MUST be emitted with no whitespace between them. A newline or a
    space between two inline images becomes a rendered space, which would show
    up as a ragged gap in the strip. Each chip carries its own padding instead,
    so each line is long and unbroken on purpose.

    Rows are separated by a blank line, which markdown reads as a paragraph
    break, so each row is centred on its own rather than reflowing into the one
    above it.
    """
    brk = cards.CHIP_BREAK
    lines = []
    for r, row in enumerate(pack_rows(specs, label)):
        parts = []
        if r == 0 and cards.rail_width(label):
            parts.append(
                f'<picture>'
                f'<source media="(max-width: {brk}px)" '
                f'srcset="{asset_url("rail-blank", vers)}">'
                f'<source media="(prefers-color-scheme: dark)" '
                f'srcset="{asset_url(f"rail-{slug}-dark", vers)}">'
                f'<img src="{asset_url(f"rail-{slug}-light", vers)}" alt="">'
                f'</picture>')
        for slug_, label_, _short, href, _accent in row:
            parts.append(
                f'<a href="{esc_attr(href)}">'
                f'<picture>'
                f'<source media="(max-width: {brk}px) and '
                f'(prefers-color-scheme: dark)" '
                f'srcset="{asset_url(f"chip-{slug_}-narrow-dark", vers)}">'
                f'<source media="(max-width: {brk}px)" '
                f'srcset="{asset_url(f"chip-{slug_}-narrow-light", vers)}">'
                f'<source media="(prefers-color-scheme: dark)" '
                f'srcset="{asset_url(f"chip-{slug_}-dark", vers)}">'
                f'<img src="{asset_url(f"chip-{slug_}-light", vers)}" '
                f'alt="{esc_attr(label_)}">'
                f'</picture></a>')
        lines.append("".join(parts))
    return "\n\n".join(lines)


def esc_attr(v: str) -> str:
    return (str(v).replace("&", "&amp;").replace('"', "&quot;")
            .replace("<", "&lt;").replace(">", "&gt;"))




def card_alt(card: str, cfg: dict, data: dict) -> str:
    """Alt text that carries the sheet's content, not its name.

    Removing the plain-text index made this the only thing a screen reader gets,
    so "Bill of materials" is not good enough: the alt has to say what is on the
    sheet. Kept to one flowing sentence per sheet, because a screen reader reads
    alt text straight through with no punctuation pauses to lean on.
    """
    if card == "bom":
        # The row's two description lines go in too. Alt text is the whole of
        # what a screen reader gets from this sheet, and a list of names and
        # percentages is the sheet's index rather than its content.
        parts = " ".join(
            f'{p["name"]}, {p["status"].lower()} at '
            f'{round(p["completion"]*100)}%. {p.get("description", "")}'.strip()
            for p in cfg.get("projects", []))
        return f"Bill of materials. {parts}" if parts else "Bill of materials, empty."
    if card == "general":
        body = " ".join(" ".join(cfg.get("about", {}).get("body", [])).split())
        pts = ". ".join(x.replace("**", "")
                        for x in cfg.get("about", {}).get("points", []))
        foc = ", ".join(cfg.get("focus", []))
        return f"{body} {pts}. Focus areas: {foc}."
    if card == "frameworks":
        bits, used = [], set()
        for band, rows in cards._fw_bands(cfg):
            for fw, parts in rows:
                names = ", ".join(str(p.get("name")) for p in parts)
                bits.append(f'{fw.get("name")} ({band.lower()}) in {names}')
                if not fw.get("bundled"):
                    used |= {str(p.get("name")) for p in parts}
        projects = cfg.get("projects", [])
        bare = len({str(p.get("name")) for p in projects} - used)
        tail = (f" {bare} of {len(projects)} install nothing at all."
                if projects else "")
        return ("Frameworks, and which project uses each. "
                + ("; ".join(bits) + "." if bits else "None listed.") + tail)
    if card == "composition":
        langs = ", ".join(f"{n} {100*v:.0f}%" for n, v in
                          (data.get("languages") or [])[:6])
        return f"Language composition: {langs}." if langs else "Language composition, no data."
    if card == "toolbox":
        bits = [f'{t["name"]} for {t.get("for", "")}'.rstrip()
                for t in cfg.get("tools", [])]
        return "Toolbox. " + ("; ".join(bits) + "." if bits else "Nothing listed.")
    ident = cfg.get("identity", {})
    revs = "; ".join(f'{r["repo"]}, {r["message"]}'
                     for r in (data.get("revisions") or []))
    return (f'Title block. {ident.get("name")}. {ident.get("title")}. '
            f'{ident.get("tagline")} {ident.get("status")}, '
            f'{ident.get("location")}.'
            + (f' Recent commits: {revs}.' if revs else ""))


def render_readme(cfg: dict, data: dict, vers: dict | None = None) -> str:
    tmpl = TEMPLATE.read_text()
    now = data["generated_at"]
    vers = vers or {}

    # The prose used to be laid into the README as markdown as well as being
    # drawn on the general notes sheet, so a screen reader had something real to
    # read. The alt text carries that now (see card_alt), and these three ran on
    # as dead locals after the plain-text copy came out.
    ident = cfg["identity"]

    subs = {
        "WEBSITE": ident["website"],
        "GITHUB": ident["github"],
        "BUILT": now.strftime("%Y-%m-%d %H:%M UTC"),
        "SHEET_COUNT": len(cards.CARDS),
        "WEBSITE_LABEL": ident["website"].split("//")[-1].rstrip("/"),
        "LINK_CHIPS": chip_row(cards.link_chips(cfg), vers,
                               LINK_LABEL, "links"),
        "REPO_CHIPS": chip_row(cards.repo_chips(cfg, blueprint.GROUNDS["light"]),
                               vers, REPO_LABEL, "repos"),
        "CARD_TITLEBLOCK": picture("titleblock", card_alt("titleblock", cfg, data), vers),
        "CARD_GENERAL": picture("general", card_alt("general", cfg, data), vers),
        "CARD_BOM": picture("bom", card_alt("bom", cfg, data), vers),
        "CARD_FRAMEWORKS": picture("frameworks", card_alt("frameworks", cfg, data), vers),
        "CARD_COMPOSITION": picture("composition", card_alt("composition", cfg, data), vers),
        "CARD_TOOLBOX": picture("toolbox", card_alt("toolbox", cfg, data), vers),
    }

    out = tmpl
    for k, v in subs.items():
        out = out.replace("{{" + k + "}}", str(v))

    # A token that survives substitution means the template asked for something
    # the config no longer provides. Left alone it ships to the profile as
    # literal "{{FOCUS}}", so it is a build failure rather than a warning.
    left = sorted(set(re.findall(r"\{\{(\w+)\}\}", out)))
    if left:
        raise ConfigError("template has unsubstituted tokens: " + ", ".join(left))
    return out


# ── main ─────────────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--offline", action="store_true",
                    help="use sample data, make no network calls")
    ap.add_argument("--check", action="store_true",
                    help="validate profile.toml and exit")
    args = ap.parse_args()

    with CONFIG.open("rb") as fh:
        cfg = normalize(tomllib.load(fh))

    try:
        validate(cfg)
    except ConfigError as e:
        print(f"config error: {e}", file=sys.stderr)
        return 2
    print(f"config ok: {len(cfg['projects'])} projects, "
          f"{len(cfg['field_notes'])} field notes")
    if args.check:
        return 0

    data = sources.collect(cfg, offline=args.offline)
    for note in data.get("errors", []):
        print(f"  degraded: {note}", file=sys.stderr)

    # An offline build substitutes sample data that is indistinguishable from
    # the real thing on the card. Stamp every sheet so an accidental commit is
    # obvious at a glance rather than three weeks later.
    if args.offline:
        print("\n  *** OFFLINE BUILD: cards contain SAMPLE DATA and are\n"
              "      stamped NOT FOR ISSUE. Do not commit this output.\n",
              file=sys.stderr)

    ASSETS.mkdir(exist_ok=True)
    written = 0
    vers: dict[str, str] = {}
    for name in cards.CARDS:
        variants = [("", False)]
        if cards.has_narrow(name):
            variants.append(("-narrow", True))
        for suffix, narrow in variants:
          for ground, t in blueprint.GROUNDS.items():
            svg = cards.render(name, cfg, data, t, narrow=narrow)
            if args.offline:
                # Injected here rather than inside each card so no renderer can
                # forget it, and so the stamp lands over finished content.
                w, h = _viewport(svg)
                svg = svg.replace(
                    "</svg>", blueprint.not_for_issue(w, h, t) + "</svg>")
            # Parse before writing. A malformed card renders as a broken image
            # on the profile, which is strictly worse than yesterday's card.
            xml.dom.minidom.parseString(svg)
            vers[f"{name}{suffix}-{ground}"] = _version(svg)
            (ASSETS / f"{name}{suffix}-{ground}.svg").write_text(svg)
            written += 1
            print(f"  wrote {name}{suffix}-{ground}.svg  {len(svg):>6,} B")

    blank = cards.blank_rail(blueprint.GROUNDS["light"])
    xml.dom.minidom.parseString(blank)
    vers["rail-blank"] = _version(blank)
    (ASSETS / "rail-blank.svg").write_text(blank)
    written += 1

    # Chips are per link rather than per card, and there is one file per chip
    # per ground. They are small, and it is the only construct GitHub leaves
    # intact that can both carry a link and look like part of the drawing.
    for ground, t in blueprint.GROUNDS.items():
        # The narrow width is computed PER ROW, not across both rows together.
        # Four chips want a width that fits four across; five want one that fits
        # three then two. Sizing them from the combined list of nine gives both
        # rows the five-chip answer and costs the four-chip row its single line.
        for rspecs in (cards.link_chips(cfg), cards.repo_chips(cfg, t)):
            for slug, label, _short, _href, accent in rspecs:
                # The phone chip keeps the full label. Shortening it to the
                # designator bought a tidy grid at the cost of telling the
                # reader which repository they were about to open.
                for suffix, compact in ((f"{ground}", False),
                                        (f"narrow-{ground}", True)):
                    svg = cards.chip(label, t, accent=accent, compact=compact)
                    xml.dom.minidom.parseString(svg)
                    vers[f"chip-{slug}-{suffix}"] = _version(svg)
                    (ASSETS / f"chip-{slug}-{suffix}.svg").write_text(svg)
                    written += 1
        for row, rlabel, rspecs in (
                ("links", LINK_LABEL, cards.link_chips(cfg)),
                ("repos", REPO_LABEL, cards.repo_chips(cfg, t))):
            svg = cards.chip_rail(cards.rail_width(rlabel), t, label=rlabel)
            xml.dom.minidom.parseString(svg)
            vers[f"rail-{row}-{ground}"] = _version(svg)
            (ASSETS / f"rail-{row}-{ground}.svg").write_text(svg)
            written += 1
            # The README column is 846 CSS pixels on a desktop profile. A row
            # wider than that wraps, which is survivable but not intended, so
            # say so at build time rather than discovering it on the page.
            total = cards.row_width(rspecs, rlabel)
            if ground == "light" and total > README_COL:
                n = len(pack_rows(rspecs, rlabel))
                print(f"  note: the {row} chips are {total:.0f}px against a "
                      f"{README_COL}px column, so they are laid out as {n} "
                      f"rows", file=sys.stderr)
    print(f"  wrote {written - len(cards.CARDS) * 2} chips")

    README.write_text(render_readme(cfg, data, vers))
    print(f"wrote {written} cards and README.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
