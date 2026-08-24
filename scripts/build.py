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
import datetime as dt
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

def picture(card: str, alt: str, stamp: str, width: str | None = None) -> str:
    """A light/dark image pair for one card.

    The ?v= stamp is not decoration. GitHub proxies README images through camo,
    which caches aggressively. Without a URL that changes when the content does,
    a daily rebuild stays invisible for hours and there is no point building it
    daily. The stamp is the build date, so the URL changes exactly as often as
    the card does.
    """
    w = f' width="{width}"' if width else ""
    return (
        '<picture>\n'
        f'  <source media="(prefers-color-scheme: dark)" '
        f'srcset="{RAW}/{card}-dark.svg?v={stamp}">\n'
        f'  <img src="{RAW}/{card}-light.svg?v={stamp}" alt="{alt}"{w}>\n'
        '</picture>'
    )


def bom_table(cfg: dict) -> str:
    """The project list as collapsible markdown rows.

    The bom card already draws the same projects, but a card is an image: it is
    not selectable, not searchable, and a screen reader gets only the alt text.
    So the card carries the drawing and this carries the words, and the detail
    stays behind <details> so the section is scannable at rest.
    """
    marks = {s["key"]: s.get("mark", "") for s in cfg["status"]}
    rows = []
    for p in cfg["projects"]:
        link = (f'<a href="{p["repo"]}">view the repository&nbsp;&rarr;</a>'
                if p.get("repo") else f'<sub>{p.get("private", "private")}</sub>')
        notes = " · ".join(p.get("notes", []))
        notes = f'<br><sub>{notes}</sub>' if notes else ""
        rows.append(
            f'<tr>\n'
            f'<td align="center"><code>{p["pn"]}</code></td>\n'
            f'<td align="center">{marks.get(p["status"], "")}</td>\n'
            f'<td><details><summary><b>{p["name"]}</b>: {p["summary"]}</summary>'
            f'<br>\n{" ".join(p["detail"].split())}\n{notes}<br><br>\n{link}\n'
            f'</details></td>\n'
            f'</tr>'
        )
    return ("<table>\n<tbody>\n" + "\n".join(rows) + "\n</tbody>\n</table>")


def notes_block(cfg: dict, data: dict, today: dt.date) -> str:
    """The drawing's numbered notes.

    Note 1 is fixed and note 2 rotates through field_notes by date, so the sheet
    reads differently day to day without anyone editing it. Indexing by ordinal
    rather than at random means the same day always yields the same note. That
    keeps the build reproducible: two runs on one day produce identical output
    and the workflow's "commit if changed" stays quiet.
    """
    pool = cfg["field_notes"]
    note = pool[today.toordinal() % len(pool)]
    lines = [
        "1. All figures are read from the GitHub API at build time. Status and "
        "completion are hand-set in "
        "[`data/profile.toml`](data/profile.toml) and reviewed, not inferred.",
        f"2. {note}",
    ]
    if data.get("errors"):
        lines.append(
            f"3. This build degraded {len(data['errors'])} telemetry "
            f"channel(s); those cells read NO DATA rather than stale values.")
    return "\n".join(lines)


def render_readme(cfg: dict, data: dict) -> str:
    tmpl = TEMPLATE.read_text()
    now = data["generated_at"]
    stamp = now.strftime("%Y%m%d")

    ident = cfg["identity"]
    about = " ".join(" ".join(cfg["about"]["body"]).split())
    points = "\n".join(f"- {p}" for p in cfg["about"]["points"])
    focus = " · ".join(f"`{f}`" for f in cfg["focus"])

    subs = {
        "NAME": ident["name"],
        "TAGLINE": ident["tagline"],
        "WEBSITE": ident["website"],
        "GITHUB": ident["github"],
        "REVISION": ident["revision"],
        "ABOUT": about,
        "POINTS": points,
        "FOCUS": focus,
        "BOM_TABLE": bom_table(cfg),
        "NOTES": notes_block(cfg, data, now.date()),
        "STAMP": stamp,
        "BUILT": now.strftime("%Y-%m-%d %H:%M UTC"),
        "CARD_TITLEBLOCK": picture("titleblock", "Title block", stamp),
        "CARD_BOM": picture("bom", "Bill of materials", stamp),
        "CARD_TELEMETRY": picture("telemetry", "Daily telemetry", stamp),
        "CARD_COMPOSITION": picture("composition", "Language composition", stamp),
        "CARD_ACTIVITY": picture("activity", "Push activity", stamp),
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
            (ASSETS / f"{name}-{ground}.svg").write_text(svg)
            written += 1
            print(f"  wrote {name}-{ground}.svg  {len(svg):>6,} B")

    README.write_text(render_readme(cfg, data))
    print(f"wrote {written} cards and README.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
