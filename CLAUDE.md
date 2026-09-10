# Working in this repository

## Naming

Never put "claude" in a branch name, a commit message, or a commit trailer.
That includes `Co-Authored-By:` and `Claude-Session:` lines — strip them. If a
session starts you on a branch named `claude/...`, rename it before pushing.

Branch names describe the change: `bill-of-materials-update`, not a tool name.

## What generates what

`data/profile.toml` is the only file holding profile facts. `scripts/build.py`
lays it into `templates/README.md.tmpl` and renders every SVG in `assets/`.

    README.md      generated  — do not edit
    assets/*.svg   generated  — do not edit
    data/profile.toml         — edit this

So a change to the profile is a change to `data/profile.toml` and nothing else.
`.github/workflows/daily.yml` rebuilds and commits the output on every push to
`main` that touches `data/profile.toml` or `scripts/`, and again at 13:00 UTC
daily. Committing generated output by hand only creates a conflict with it.

The six sheets, in order: `titleblock`, `general`, `bom`, `frameworks`,
`composition`, `toolbox`. Sheet numbers derive from `cards.CARDS`, so reordering
that list renumbers everything.

## The rule this drawing set is built on

Every field on every sheet has to be something a stranger could check. No field
exists because a drawing usually has one.

That is not decoration, it is the reason several things here look the way they
do. The title block strip carries STATUS / BASED IN / ON THIS SHEET / LAST PUSH
/ BUILT rather than DRAWN BY / REV / SCALE / UNITS, because a person has no
scale and the revision letter only ever meant that somebody remembered to bump
it. The revision table holds real commit subjects with real dates rather than
repository names against N/A zones. On the frameworks matrix an unlisted part
would draw an empty column, and an empty column there already means "installs
nothing", so the build refuses a part no framework names rather than let an
oversight sit on the sheet looking like a claim.

Sheet 4 went through three subjects before it held. A project timeline was
perfectly accurate and mostly empty, because six of ten projects were built
inside five weeks against a window of two years. A typical assemblies sheet
grouped the parts into four shapes, and generalising is what let it letter
animAgent's stack as "SwiftUI, and SpriteKit" when animAgent contains no
SwiftUI at all. Accurate is necessary and not sufficient, and an abstraction
over the work is somewhere an error can hide. The matrix that replaced them has
nowhere: every mark is one framework in one project.

When adding to a sheet, the question is not "would a drawing have this" but
"can this be filled with something measured". If it cannot, it does not go on.

## Validating a config change

    python3 scripts/build.py --check      # config only, no network
    python3 scripts/build.py --offline    # render everything, no network

Standard library only, no install step. `--check` runs the real validators:
summary length against the BOM description column, the status/completion band
assertions, the notes-per-row cap, that every part is named by at least one
framework, and every project name a `[[tools]]` or `[[frameworks]]` row
cites. It prints `config ok: N projects` when the config is
sound.

`--offline` writes cards stamped `NOT FOR ISSUE / SAMPLE DATA`, because it fills
the live channels with fixtures. **Revert that output before committing:**

    git checkout -- README.md assets/
    git clean -f assets/          # new chips for any part you just added

For a real local build, give it a token so the language channel does not exhaust
the 60/hour anonymous budget:

    GITHUB_TOKEN="$(gh auth token)" python3 scripts/build.py

## Notes on the bill of materials

- Order in the file is the order on the sheet. It currently runs by descending
  `completion`; keep it that way.
- `status` is a band of `completion`, not an independent label. The build fails
  if they disagree. The QUALIFIED floor is 0.95, not 0.90, so that a row reading
  DONE means it.
- Reference designators are not recycled. A retired `TUL-01` leaves a gap; the
  next tool part is `TUL-05`.
- A new part needs at least one `[[frameworks]]` entry naming it as well as a
  BOM row. What a part is built on is keyed by framework, not by project, so
  there is one place to update rather than two that can disagree.
- The repo chip rail under the sheet is generated from whichever parts carry a
  `repo` URL. There is no separate list to update, and `pack_rows()` splits the
  rail into balanced rows when it outgrows the README column.
- Prose in `[about]`, `[notes]`, `[[tools]]` and `[[frameworks]]` names
  specific projects. When a part leaves the BOM, check all of them for
  references that just went stale. The `on` fields are checked by the build;
  the prose is not.

## Voice

The prose on this profile is written by a person about their own work, and it
has to read that way. Flat, specific, first person, no aphorisms. "Happiest in a
debugger" and "I work at the boundary between models and hardware" are both
things that came off this profile for sounding like a character rather than a
student who likes building things. Field notes in particular are annotations on
your own work, not jokes and not mottos.
