# SETUP

How this profile is put together, and the handful of things you might want to change.

---

## The one-file control model

`data/profile.toml` is the only file with facts in it. Your name, the project list,
which telemetry channels are on, the palette. All of it lives there.

Everything else is output:

| Generated                          | By                  | From               |
| ---------------------------------- | ------------------- | ------------------ |
| `assets/<card>-light.svg`           | `scripts/build.py`  | `data/profile.toml` |
| `assets/<card>-dark.svg`            | `scripts/build.py`  | `data/profile.toml` |
| `README.md`                         | `scripts/build.py`  | `data/profile.toml` |

Five cards: `titleblock`, `bom`, `telemetry`, `composition`, `activity`. Each in a
light and a dark variant, ten SVGs total.

**Do not hand-edit `README.md` or anything in `assets/`.** The next build overwrites
them and your edit is gone. Edit the TOML.

### Running it locally

```sh
python3 scripts/build.py            # full build, hits the network for telemetry
python3 scripts/build.py --offline  # skip every network call; uses SAMPLE data
```

Pure standard library: `tomllib`, `urllib`, `json`. There is nothing to `pip install`,
no virtualenv, no lockfile. Python 3.12 (3.11+ for `tomllib`).

Use `--offline` when you are iterating on layout or wording. It is much faster and it
does not spend your anonymous rate limit against the space APIs.

> **`--offline` does not blank the telemetry. It invents it.** It substitutes a
> plausible language mix, crew count and ISS fix so the layout has something to
> render. Those numbers look exactly as real as the real ones.
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
different row every day, so it reads as an alarm rather than a note. The telemetry
sheet already says the same thing calmly under LAST CONTACT. Set it to `true` if you
want it back.

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

### The status / completion band rule

Status is not a label you set independently. It is a band of the completion figure.
`build.py` asserts this and **fails the build** if you break it:

```
CONCEPT  <  0.25  <=  BREADBOARD  <  0.45  <=  FLIGHT  <  0.90  <=  QUALIFIED
```

So a project at `completion = 0.30` cannot be `CONCEPT`, and one at `0.95` cannot be
`FLIGHT`. This is deliberate: it stops the sheet drifting into optimism, where
everything is somehow "in flight" forever.

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

## The one optional secret: `LASTFM_API_KEY`

This is the **only** secret in the repo, and it is optional. Everything works without
it. The listening channel simply does not appear on the telemetry card.

**You have to do this yourself.** It is tied to your own Last.fm account, and repository
secrets can only be set by the repo owner in the GitHub web UI. Nobody else can do it
for you, and the key should never be committed to the repo.

1. Sign in to Last.fm and go to <https://www.last.fm/api/account/create>.
   Fill in an application name; "profile card" is fine. Submit it.
   Copy the **API key** it gives you. Ignore the shared secret; this build only reads.

2. In this repository on GitHub, go to
   **Settings → Secrets and variables → Actions → New repository secret**.
   Name it exactly `LASTFM_API_KEY`, paste the key as the value, and save.

3. Turn the channel on in `data/profile.toml`:

   ```toml
   [telemetry.listening]
   enabled  = true
   provider = "lastfm"
   user     = "your-lastfm-username"
   ```

4. Commit. The push to `main` touches `data/profile.toml`, so the workflow runs on its
   own and the channel appears on the next build.

To test locally before committing:

```sh
LASTFM_API_KEY=your-key-here python3 scripts/build.py
```

To turn it back off, set `enabled = false`. You can leave the secret in place.

---

## Telemetry channels and what they depend on

The telemetry card is a band of live readouts. Each is an independent channel with its
own upstream service, toggled in `[telemetry]` in `data/profile.toml`.

| Channel           | Toggle              | Service                    | Key needed          |
| ----------------- | ------------------- | -------------------------- | ------------------- |
| Next launch window | `launch_window`    | thespacedevs Launch Library 2 | No                |
| Humans in space    | `humans_in_space`  | thespacedevs Launch Library 2 | No                |
| ISS ground track   | `iss_track`        | wheretheiss.at             | No                  |
| Push activity      | `repo_telemetry`   | GitHub REST API            | Built-in token      |
| Now listening      | `[telemetry.listening] enabled` | Last.fm       | **Yes**, optional   |

**thespacedevs (LL2)**, <https://ll.thespacedevs.com>. Powers both the next-orbital-launch
countdown and the humans-currently-in-space count. No account, no key. Anonymous access is
rate limited to roughly **15 requests per hour per IP**, which is generous for one build a
day but is exactly why you should use `--offline` while iterating locally. If you do get
rate limited, the channel renders `NO DATA` and the build still succeeds.

**wheretheiss.at**, <https://wheretheiss.at/w/developer>. Returns the ISS sub-satellite
point (lat/lon). No key. The position is sampled once at build time and stamped with that
timestamp on the card. A static SVG cannot track it live, so the stamp is there to make
clear the reading is a snapshot rather than a claim about right now.

**GitHub API**, for push activity over the recent window. In CI this uses the built-in
`GITHUB_TOKEN`, which Actions provides automatically; there is nothing to set up. Running
locally without a token falls back to unauthenticated access (60 requests/hour), which is
usually enough for one build. If you hit that limit locally, export a personal access token
as `GITHUB_TOKEN`. A classic token with no scopes at all is enough for public data.

**Last.fm**, optional. See the section above.

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

The committed SVGs in `assets/` are the real artifact. `README.md` embeds them directly
from this repository, and the website route at `henrykanaskie.com/api/cards/<card>` is a
thin proxy that fetches the same committed files. There is exactly one renderer, the
Python in `scripts/`, and nothing re-implements it.

---

## Troubleshooting

**A card shows `NO DATA` every day.** The channel's upstream is failing consistently, not
transiently. Run `python3 scripts/build.py` locally and read the warning it prints for that
channel.

**The workflow is green but nothing changes.** Correct behaviour when the output is
byte-identical to what is already committed, meaning nothing on the card moved that day. Check the
run log for `No changes to assets/ or README.md`.

**The workflow fails on the build step.** A real error. The log has the traceback. Most
often it is a `completion` value that no longer matches its `status` band, or a `lang` that
is not in `[palette.lang]`.

**Scheduled runs stopped.** GitHub disables schedules after 60 days of repository
inactivity. Open the Actions tab and re-enable the workflow.
