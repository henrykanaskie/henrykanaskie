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

## Validating a config change

    python3 scripts/build.py --offline

Standard library only, no install step. This runs the real validators —
summary length against the BOM description column, the status/completion band
assertions, the notes-per-row cap — and prints `config ok: N projects` when the
config is sound.

It writes cards stamped `NOT FOR ISSUE / SAMPLE DATA`, because offline mode
fills the telemetry channels with fixtures. **Revert that output before
committing:**

    git checkout -- README.md assets/
    git clean -f assets/          # new chips for any part you just added

## Notes on the bill of materials

- Order in the file is the order on the sheet. It currently runs by descending
  `completion`; keep it that way.
- `status` is a band of `completion`, not an independent label. The build fails
  if they disagree.
- Reference designators are not recycled. A retired `MDL-01` leaves a gap; the
  next model part is `MDL-02`.
- The repo chip rail under the sheet is generated from whichever parts carry a
  `repo` URL. There is no separate list to update.
- Prose in `[about]` and `[notes]` names specific projects. When a part leaves
  the BOM, check those two tables for references that just went stale.
- Bump `identity.revision` by hand for a change worth marking. Nothing
  automates it.
