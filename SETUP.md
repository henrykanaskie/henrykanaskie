# SETUP

How this profile is put together, and the handful of things you might want to change.

---

## The one-file control model

`data/profile.toml` is the only file with facts in it. Your name, the project list,
the toolbox, the palette. All of it lives there.

Everything else is output:

| Generated                          | By                  | From               |
| ---------------------------------- | ------------------- | ------------------ |
| `assets/<card>-light.svg`           | `scripts/build.py`  | `data/profile.toml` |
| `assets/<card>-dark.svg`            | `scripts/build.py`  | `data/profile.toml` |
| `README.md`                         | `scripts/build.py`  | `data/profile.toml` |

Six sheets, in this order: `titleblock`, `general`, `bom`, `timeline`,
`composition`, `toolbox`. Each is drawn in a light and a dark variant, and in a wide
and a narrow layout. Sheet numbers come from that order, so adding or reordering a card in
`CARDS` renumbers every sheet automatically.

The README has no markdown headings and no horizontal rules. Each sheet carries its own
label inside the drawing frame, so a GitHub heading in the default UI font above a
monospace drawing made the page read as two documents. The only things outside a card
are the two chip rows.

An SVG served through `<img>` gives a screen reader nothing but its alt text, so the
alt text is written to carry the sheet's content rather than to name the picture: the
bill of materials reads out its parts and their status, the timeline reads out each
project's dates and commit count. `card_alt()` in `build.py` is where that lives. If
you add a sheet, give it a branch there.

**Do not hand-edit `README.md` or anything in `assets/`.** The next build overwrites
them and your edit is gone. Edit the TOML.

### Running it locally

```sh
python3 scripts/build.py            # full build, reads the GitHub API
python3 scripts/build.py --offline  # skip every network call; uses SAMPLE data
python3 scripts/build.py --check    # validate profile.toml and stop
```

Pure standard library: `tomllib`, `urllib`, `json`. There is nothing to `pip install`,
no virtualenv, no lockfile. Python 3.12 (3.11+ for `tomllib`).

Use `--offline` when you are iterating on layout or wording. It is much faster and it
does not spend your unauthenticated GitHub rate limit.

> **`--offline` does not blank the live figures. It invents them.** It substitutes a
> plausible language mix and a set of recent commits so the layout has something to
> render. Those look exactly as real as the real ones. (The timeline is the exception:
> its sample push times are read from each project's own `last` date in the config, so
> that one sheet is honest offline.)
>
> Every card from an offline build is therefore stamped **NOT FOR ISSUE** in red,
> and the build prints a warning. If you see that stamp on the profile, someone
> committed an offline build. Rerun `python3 scripts/build.py` without the flag
> and commit that. Never commit `--offline` output.

### Running it in CI

`.github/workflows/daily.yml` runs the same command once a day and commits `assets/`
and `README.md` if they changed. If nothing changed it exits clean and commits nothing.

---

## The revision cloud

`[bom] mark_last_push` draws a red drafting revision cloud around whichever project
was pushed to most recently. It is **off**. The mark is real drafting practice and the
data behind it is real, but red is the loudest thing on the sheet and it moves to a
different row every day, so it reads as an alarm rather than a note. The title block
strip already says the same thing calmly under LAST PUSH. Set it to `true` if you want
it back.

---

## Adding a project

Projects are the bill of materials on the drawing. Add a `[[projects]]` block to
`data/profile.toml`. Order in the file is order on the sheet, kept descending by `completion`.

```toml
[[projects]]
pn         = "QNT-03"
name       = "repo-name"
lang       = "Python"
status     = "FLIGHT"
completion = 0.60
summary    = "one line, shown collapsed, at most 81 characters"
detail     = """
The expanded paragraph. What it is, and the actual interesting problem in it."""
notes      = ["tolerance callout", "another one", "at most three"]
repo       = "https://github.com/henrykanaskie/repo-name"
started    = 2026-08-31
last       = 2026-09-09
commits    = 100
```

The three date fields are what the timeline sheet draws. Read them off the repository
rather than estimating:

```sh
git log --reverse --format=%aI | head -1   # started
git log -1 --format=%aI                    # last
git rev-list --count HEAD                  # commits
```

| Field        | Notes                                                              |
| ------------ | ------------------------------------------------------------------ |
| `pn`         | Reference designator, `CLASS-NN`. The prefix says what the thing is before you read its name: `OPT` solver, `SYS` systems, `QNT` quantitative, `MDL` model from scratch, `APP` application, `TUL` tool, `EDU` teaching. Invent a class when none fits. |
| `name`       | Repository name.                                                   |
| `lang`       | Must exist in `[palette.lang]` further down the file, or the build fails. |
| `status`     | One of the `[[status]]` keys. See the band rule below.              |
| `completion` | `0.0` to `1.0`.                                                        |
| `summary`    | One line. Shown collapsed.                                          |
| `detail`     | The expanded paragraph.                                             |
| `notes`      | Short, factual. Three maximum.                                      |
| `repo`       | **Omit entirely** for a private or unpushed project.                |
| `private`    | Optional. One line explaining why there is no link.                 |
| `started`    | Date of the first commit. Required: without it the project has no bar on the timeline. |
| `last`       | Date of the most recent commit. Refreshed from the live push time when `repo` is set. |
| `commits`    | Commit count, as measured on the same day as `last`.                |

### The status / completion band rule

Status is not a label you set independently. It is a band of the completion figure.
`build.py` asserts this and **fails the build** if you break it:

```
CONCEPT  <  0.25  <=  BREADBOARD  <  0.45  <=  FLIGHT  <  0.95  <=  QUALIFIED
```

So a project at `completion = 0.30` cannot be `CONCEPT`, and one at `0.96` cannot be
`FLIGHT`. This is deliberate: it stops the sheet drifting into optimism, where
everything is somehow "in flight" forever.

The QUALIFIED floor is `0.95` rather than `0.90` on purpose. Two projects here sit at
exactly `0.90`, which is the number you would give somebody who asked, and it is not
the same claim as "done". A vocabulary that rounds 90% up to DONE cannot be trusted on
the rows where it says DONE.

The bounds themselves are the `floor` values on the `[[status]]` blocks. Change a floor
there and the check moves with it. You never have to touch Python.

Adding a language that is not in `[palette.lang]` yet? Add it there first, borrowing a
pair from `spare` at the bottom of the palette section.

---

## Changing the daily schedule

One line, in `.github/workflows/daily.yml`:

```yaml
on:
  schedule:
    - cron: "0 13 * * *"
```

Fields are `minute hour day-of-month month day-of-week`.

**The caveat that bites everyone:** GitHub Actions cron is *always* UTC and never
observes daylight saving. `0 13 * * *` is 06:00 Pacific during PDT (UTC−7) and drifts
to 05:00 Pacific during PST (UTC−8). If you want 06:00 local year-round you would need
two cron entries plus a date guard in the job, which is not worth it for a card refresh.

Also, scheduled runs on GitHub are best-effort. A run can be delayed by several minutes
under load, and scheduled workflows are disabled automatically after 60 days of no
repository activity. The daily commit counts as activity, so in practice it keeps itself
alive.

The workflow also fires on `workflow_dispatch` (the **Run workflow** button in the
Actions tab) and on any push to `main` touching `data/profile.toml` or `scripts/**`,
so editing the config regenerates the profile within a minute rather than tomorrow.

---

## Adding a tool

The toolbox sheet is a `[[tools]]` list in the same file.

```toml
[[tools]]
name = "polars"
for  = "season-scale football data, because pandas was the slow half of the loop"
on   = ["aggregateAnalytics"]
lang = "Python"          # optional
```

| Field  | Notes                                                                    |
| ------ | ------------------------------------------------------------------------ |
| `name` | The tool.                                                                |
| `for`  | What you use it for, in one line. See the rule below.                    |
| `on`   | Projects it is used on. **Every name must match a `[[projects]]` name**, or the build fails and prints the ones it knows. An empty list letters as NOT ON THIS SHEET. |
| `lang` | Optional. When set, the row takes the same hatch and colour that language carries on the composition sheet, so the two sheets agree about what colour Python is. |

The rule for `for` is that it says what the tool does in **your** work. "Python: a
general purpose language" is a row that could sit on anybody's profile, which is the
definition of a row not worth drawing. Each entry should name the thing that would not
exist without it.

---

## The timeline sheet

Each part of the bill of materials becomes a bar running from its first commit to its
most recent one. Two settings, both in `[timeline]`:

```toml
[timeline]
months        = 14      # minimum window, in months
follow_pushes = true    # refresh the end of a bar from the live push time
```

`months` is a **floor**, not a lookback. The window is fitted to the data and then
widened to whole months, so nothing ever falls off the left edge; `months` only stops
a profile with three weeks of history drawing a three-week-wide chart. A fixed lookback
was the first version and it was wrong in the way that mattered: the two oldest parts
fell outside it and had to be clamped to the edge with an open end, which draws a
finished project as though it were still running off the side of the sheet.

`follow_pushes` extends the right-hand end of a bar to the live GitHub push time where
the project has a public `repo`. It only ever extends, never retracts, so a repository
whose push time reads earlier than the recorded last commit means the config is ahead
of the API rather than that work was undone. A row is only refreshable if this account
owns the repository and it is public: private projects and projects living in somebody
else's repository are drawn from the file, and the sheet's own footer says how many
rows are which.

**A project whose whole history landed on one day draws as a milestone diamond, not a
bar.** `Cap_Match_Net` and `small-shell` are both like this: the work happened over
months in a lab and a course and then went to GitHub in a single push. A bar one day
wide would be a true statement about the repository and a false one about the work, so
it gets the mark a drawing uses for a thing with a date and no duration.

Bars have a five-pixel minimum width. Most of this work happened inside a couple of
weeks against a window closer to two years, and a truthful bar for a fortnight is about
four pixels. Every row also letters its exact date span next to its name, which is
where the precision actually lives, and the commit column beside it is not scaled at
all.

---

## What the build fetches

Everything comes from one place: GitHub's own API about this account. There used to be
three more channels on this profile, carrying the next orbital launch, the number of
people currently in space, and the ISS ground track. They worked and they were real,
and none of them were about the person whose profile this is, so they came off along
with the sheet that carried them.

The whole toggle is one line:

```toml
[sources]
github = true
```

| Reading                     | Endpoint                                | Cost                  |
| --------------------------- | --------------------------------------- | --------------------- |
| Language mix                | `/users/:u/repos` + one `languages_url` per repo | ~1 per repository |
| Repo count, account age     | `/users/:u`                             | 1                     |
| Last push and its age       | `/users/:u/events/public`               | 1                     |
| Push time per repository    | `/users/:u/repos` (cached)              | 0                     |
| Latest commit per project   | `/repos/:o/:r/commits?per_page=1`       | 1 per revision row    |

In CI this uses the built-in `GITHUB_TOKEN`, which Actions provides automatically;
there is nothing to set up and there are no other secrets in this repository. Running
locally without a token falls back to unauthenticated access (60 requests/hour), which
is tight once the language channel makes a call per repository. Export a token if you
hit it:

```sh
GITHUB_TOKEN="$(gh auth token)" python3 scripts/build.py
```

A classic token with no scopes at all is enough for public data.

### Why the revision table costs a request per row

The obvious implementation reads the public events feed, which already carries a
`PushEvent` per push. It does not work: GitHub strips `payload.commits` for
unauthenticated reads and returns an empty array, so a revision table built on it
letters three blank descriptions and looks like a renderer bug. `/commits?per_page=1`
is the only source that carries the message, which is why the table is three rows and
not ten.

### Every channel degrades, none of them break the build

This is the important property. If an upstream service is down, rate limited, slow, or
returns something unparseable, that channel renders as a dashed **`NO DATA`** cell and
`build.py` still exits 0. The other channels are unaffected and the rest of the drawing
renders normally.

That is why the workflow does *not* wrap the build in `continue-on-error`: transient API
trouble is already absorbed by the script, so a non-zero exit from `build.py` means a real
problem: a malformed TOML, a status band violation, a bug. It should show a red X so you
actually find out. See the comments in `daily.yml`.

---

## Where the cards are served from

### Two layouts per sheet

A sheet is 900px wide and GitHub's README column on a 375pt phone is 293, so a phone
was scaling the whole drawing to a third of its size and the body lettering landed
around 5px. Each sheet therefore has a second layout drawn at 300px and REFLOWED
rather than scaled: table columns become stacked blocks, side-by-side panels become
rows. `<picture>` picks between them with the same `max-width: 500px` query the chips
use, so there are four files per sheet: light and dark, wide and narrow.

The phone layouts live in `scripts/narrow.py` and `scripts/narrow_bom.py` rather than
in `cards.py`. They are a second full set of layouts, not a variation, and folding them
into `cards.py` would have doubled the length of the longest file in the repo. Both
modules export a `RENDERERS` dict that `cards.py` merges at the bottom of the file. A
sheet with no phone layout registered falls back to its wide one, so the set always
renders.

If you add a sheet, add its phone layout too, or accept that phones will scale it.

### Links

Every link on the page is a chip: a small SVG wrapped in an anchor, because an
`<img>` is inert and GitHub's sanitiser strips inline `<svg>`, `<object>` and
`<map>`. Each chip ships in four variants, picked by `<picture>`: light and dark, wide and
narrow. Below 500px a phone gets the narrow variant, which keeps the full label and
takes the whole column, one chip per line. The longest name is
`ML_QUANTITATIVE_RESEARCH`, so any tile wide enough to hold it is already most of a
phone column; one per line is what the content forces anyway, and stacked rows read
as a parts list.

On the bill of materials, a part at the top of the status vocabulary draws its
completion bar in green instead of its material colour, so "done" is visible without
reading the status column. It follows the status *rank*, not the name, so renaming
`QUALIFIED` does not turn it off. The MATL swatch still shows the language.

A chip row wider than GitHub's 846px README column is split into rows **here**, not
by the browser. Letting it wrap produced a first row packed to the edge and a second
row holding one chip, which reads as a mistake rather than as a layout. `pack_rows()`
in `build.py` balances the break instead, aiming for rows of roughly equal length, and
the build prints how many rows it decided on. The leading rail label only ever appears
on the first row.

Every asset URL in `README.md` carries a `?v=` that is a hash of that file's own
bytes. README images are cached hard, so without it a rebuild stays invisible. It
used to be the build date, which was wrong the moment it mattered: iterating on the
design changed the cards twenty-one times in one day while every URL still read
`v=20260824`. A content hash changes when the bytes change and not otherwise.

The committed SVGs in `assets/` are the real artifact. `README.md` embeds them directly
from this repository, and the website route at `henrykanaskie.com/api/cards/<card>` is a
thin proxy that fetches the same committed files. There is exactly one renderer, the
Python in `scripts/`, and nothing re-implements it.

---

## Troubleshooting

**A card shows `NO DATA` every day.** The channel's upstream is failing consistently, not
transiently. Run `python3 scripts/build.py` locally and read the warning it prints for that
channel.

**A timeline row draws a dashed NO DATES span.** That project has no `started` date in
`data/profile.toml`. `--check` catches it before a build, and prints the `git log`
incantation that gets you the date.

**The toolbox build fails naming a project.** A `[[tools]]` entry cites a name that is
not on the bill of materials, usually a case difference. The error prints every name
it does know.

**The workflow is green but nothing changes.** Correct behaviour when the output is
byte-identical to what is already committed, meaning nothing on the card moved that day. Check the
run log for `No changes to assets/ or README.md`.

**The workflow fails on the build step.** A real error. The log has the traceback. Most
often it is a `completion` value that no longer matches its `status` band, or a `lang` that
is not in `[palette.lang]`.

**Scheduled runs stopped.** GitHub disables schedules after 60 days of repository
inactivity. Open the Actions tab and re-enable the workflow.
