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
description length against the BOM description column, the status/completion band
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

Each part gets one `description` on the bill of materials: one or two sentences
covering what it does and what it is useful for, as prose. It is deliberately
not two fields. Splitting it into a clipped `summary` and a separate `why` was
tried and read like a spec sheet, which is a shape nobody writing about their
own project would choose.

Anything written into this config that no sheet renders is worse than writing
nothing, because it reads as work and reaches nobody. A `detail` field held a
paragraph per project and was rendered on precisely nothing.

Every entry says what the thing does and why it is worth having. That is the whole
shape of it, and the failure mode is writing anything else.

Two specific habits to avoid, because both got written into this profile and
both had to come out:

**Selling.** A description describes; it does not pitch. "Picks the capacitor
values for an RF impedance matching network" is the job. "Picks matching-network
capacitors from values you can actually buy" is an advertisement for the same
function, and the word doing the selling is "actually".

**The catchy ending.** Every entry had grown a closing line that summed it up
with a turn of phrase: "watching it is the entire feature", "which is the
part of the job it was actually meant to fix", "instead of my word for it". They
read as written-to-be-quoted. An entry should stop once it has said why the
thing was built.

Watch for: "actually", "real", "the whole point", "the part that matters", a
final sentence shorter than the ones before it, and any comparison that exists
to flatter (1.9 MB "rather than 150 MB of Electron").

Field notes are annotations on your own drawing: one fact, stated flat. The test
is whether it would still be worth writing down if nobody else read it.
