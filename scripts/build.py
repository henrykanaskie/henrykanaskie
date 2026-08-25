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


# Keys that must never appear inside a project or a telemetry table. Each one is
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

        for required in ("pn", "name", "lang", "status", "completion", "summary"):
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

        cap = cards.summary_capacity()
        if len(p.get("summary", "")) > cap:
            problems.append(
                f"{who}: summary is {len(p['summary'])} characters. The "
                f"description column fits {cap}, so it would be cut with an "
                f"ellipsis on the sheet. Trim it by "
                f"{len(p['summary']) - cap}.")

        if p.get("repo") and p.get("private"):
            problems.append(f"{who}: has both 'repo' and 'private'; pick one")
        if len(p.get("notes", [])) > 3:
            problems.append(
                f"{who}: {len(p['notes'])} notes; three is the most a row fits")

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
    for k in STRAY:
        if k in cfg.get("telemetry", {}).get("listening", {}):
            problems.append(
                f"[telemetry.listening] contains '{k}'. It needs its own table "
                f"header, or TOML binds it to the section above it")

    if not cfg.get("field_notes"):
        problems.append(
            "no field notes found. Expected a [notes] table with a `field` array")
    if not cfg.get("focus"):
        problems.append(
            "no focus areas found. Expected a [focus] table with an `areas` array")

    weighting = cfg.get("languages", {}).get("weighting", "equal")
    if weighting not in ("equal", "bytes"):
        problems.append(
            f"[languages] weighting is {weighting!r}; expected 'equal' or 'bytes'")

    if problems:
        raise ConfigError(
            "profile.toml has %d problem(s):\n  - %s"
            % (len(problems), "\n  - ".join(problems)))


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
    """A light/dark image pair for one card, each versioned independently."""
    w = f' width="{width}"' if width else ""
    return (
        '<picture>\n'
        f'  <source media="(prefers-color-scheme: dark)" '
        f'srcset="{asset_url(card + "-dark", vers)}">\n'
        f'  <img src="{asset_url(card + "-light", vers)}" alt="{alt}"{w}>\n'
        '</picture>'
    )


def chip_row(specs: list, vers: dict, label: str, slug: str) -> str:
    """A row of anchored chips, as one line of markdown with no gaps.

    The chips MUST be emitted with no whitespace between them. A newline or a
    space between two inline images becomes a rendered space, which would show
    up as a ragged gap in the strip. Each chip carries its own padding instead,
    so the line is long and unbroken on purpose.
    """
    parts = []
    lead = cards.rail_width(label)
    brk = cards.CHIP_BREAK
    if lead:
        parts.append(
            f'<picture>'
            f'<source media="(max-width: {brk}px)" '
            f'srcset="{asset_url("rail-blank", vers)}">'
            f'<source media="(prefers-color-scheme: dark)" '
            f'srcset="{asset_url(f"rail-{slug}-dark", vers)}">'
            f'<img src="{asset_url(f"rail-{slug}-light", vers)}" alt="">'
            f'</picture>')
    for slug_, label_, _short, href, _accent in specs:
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
    return "".join(parts)


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
        parts = ", ".join(
            f'{p["name"]} {p["status"].lower()} at {round(p["completion"]*100)}%'
            for p in cfg.get("projects", []))
        return f"Bill of materials. {parts}." if parts else "Bill of materials, empty."
    if card == "general":
        body = " ".join(" ".join(cfg.get("about", {}).get("body", [])).split())
        pts = ". ".join(x.replace("**", "")
                        for x in cfg.get("about", {}).get("points", []))
        foc = ", ".join(cfg.get("focus", []))
        return f"{body} {pts}. Focus areas: {foc}."
    if card == "telemetry":
        bits = []
        if data.get("launch"):
            bits.append(f'next launch {data["launch"].get("name")}')
        if data.get("humans") is not None:
            bits.append(f'{data["humans"]} people in space')
        if data.get("iss"):
            bits.append(f'ISS at {data["iss"]["lat"]:.1f} degrees latitude')
        if data.get("last_push"):
            bits.append(f'last push to {data["last_push"].get("repo")}')
        return "Daily telemetry. " + ("; ".join(bits) + "." if bits else "No data.")
    if card == "composition":
        langs = ", ".join(f"{n} {100*v:.0f}%" for n, v in
                          (data.get("languages") or [])[:6])
        return f"Language composition: {langs}." if langs else "Language composition, no data."
    if card == "activity":
        total = sum(c for _d, c in (data.get("activity") or []))
        return f"Push activity, {total} pushes over the last 30 days."
    if card == "notes":
        return "Notes. " + (cards.todays_note(cfg, data) or "No notes.")
    ident = cfg.get("identity", {})
    return (f'Title block. {ident.get("name")}. {ident.get("title")}. '
            f'{ident.get("tagline")} Revision {ident.get("revision")}.')


def render_readme(cfg: dict, data: dict, vers: dict | None = None) -> str:
    tmpl = TEMPLATE.read_text()
    now = data["generated_at"]
    vers = vers or {}

    ident = cfg["identity"]
    about = " ".join(" ".join(cfg["about"]["body"]).split())
    points = "\n".join(f"- {p}" for p in cfg["about"]["points"])
    focus = " · ".join(f"`{f}`" for f in cfg["focus"])

    subs = {
        "WEBSITE": ident["website"],
        "GITHUB": ident["github"],
        "REVISION": ident["revision"],
        "BUILT": now.strftime("%Y-%m-%d %H:%M UTC"),
        "SHEET_COUNT": len(cards.CARDS),
        "WEBSITE_LABEL": ident["website"].split("//")[-1].rstrip("/"),
        "LINK_CHIPS": chip_row(cards.link_chips(cfg), vers,
                               LINK_LABEL, "links"),
        "REPO_CHIPS": chip_row(cards.repo_chips(cfg, blueprint.GROUNDS["light"]),
                               vers, REPO_LABEL, "repos"),
        "CARD_TITLEBLOCK": picture("titleblock", card_alt("titleblock", cfg, data), vers),
        "CARD_GENERAL": picture("general", card_alt("general", cfg, data), vers),
        "CARD_NOTES": picture("notes", card_alt("notes", cfg, data), vers),
        "CARD_BOM": picture("bom", card_alt("bom", cfg, data), vers),
        "CARD_TELEMETRY": picture("telemetry", card_alt("telemetry", cfg, data), vers),
        "CARD_COMPOSITION": picture("composition", card_alt("composition", cfg, data), vers),
        "CARD_ACTIVITY": picture("activity", card_alt("activity", cfg, data), vers),
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

    # An offline build substitutes sample telemetry that is indistinguishable
    # from the real thing on the card. Stamp every sheet so an accidental commit
    # is obvious at a glance rather than three weeks later.
    if args.offline:
        print("\n  *** OFFLINE BUILD: cards contain SAMPLE DATA and are\n"
              "      stamped NOT FOR ISSUE. Do not commit this output.\n",
              file=sys.stderr)

    ASSETS.mkdir(exist_ok=True)
    written = 0
    vers: dict[str, str] = {}
    for name in cards.CARDS:
        for ground, t in blueprint.GROUNDS.items():
            svg = cards.render(name, cfg, data, t)
            if args.offline:
                # Injected here rather than inside each card so no renderer can
                # forget it, and so the stamp lands over finished content.
                w, h = _viewport(svg)
                svg = svg.replace(
                    "</svg>", blueprint.not_for_issue(w, h, t) + "</svg>")
            # Parse before writing. A malformed card renders as a broken image
            # on the profile, which is strictly worse than yesterday's card.
            xml.dom.minidom.parseString(svg)
            vers[f"{name}-{ground}"] = _version(svg)
            (ASSETS / f"{name}-{ground}.svg").write_text(svg)
            written += 1
            print(f"  wrote {name}-{ground}.svg  {len(svg):>6,} B")

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
            nw = cards.narrow_width(len(rspecs))
            for slug, label, short, _href, accent in rspecs:
                for suffix, text_, compact in ((f"{ground}", label, False),
                                               (f"narrow-{ground}", short, True)):
                    svg = cards.chip(text_, t, accent=accent, compact=compact,
                                     width=nw)
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
                print(f"  note: the {row} chip row is {total:.0f}px and will "
                      f"wrap below {total:.0f}px of column", file=sys.stderr)
    print(f"  wrote {written - len(cards.CARDS) * 2} chips")

    README.write_text(render_readme(cfg, data, vers))
    print(f"wrote {written} cards and README.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
