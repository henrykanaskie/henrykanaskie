#!/usr/bin/env python3
"""Data collection for the profile build.

Every number that appears on a card comes from here, and nothing here draws
anything. The split exists so the renderer can be developed against
`collect(cfg, offline=True)` without touching the network, and so a dead API is
a data problem rather than a rendering one.

The governing rule is that this module never raises. A profile that fails to
build because someone else's API returned a 502 at 13:00 UTC is worse than a
profile with one dashed "NO DATA" cell, so each channel is fetched inside
`_channel()`, which converts any failure into a None value and a short line in
`errors`. The daily workflow therefore has no failure mode that involves an
unpublished README.

Everything fetched here is GitHub's own API about one account. There used to be
three more channels on this profile: the next orbital launch, the number of
people currently in space, and the ISS ground track. They worked, and they were
real, and none of them were about the person whose profile this is. They are
gone, and so is the sheet that carried them.

Standard library only. The workflow installs nothing, so there is no
requirements file to drift and no cache to warm.

    collect(cfg)                  # live
    collect(cfg, offline=True)    # sample data, no sockets opened

The GitHub channel is gated by `[sources] github` in data/profile.toml. Off
there returns empty values with *no* entry in `errors`: off by design and broken
are different states, and a caller should not have to guess which one it is
looking at.
"""

from __future__ import annotations

import collections
import datetime as dt
import json
import os
import urllib.error
import urllib.request

TIMEOUT = 10

# How many rows the title block's revision table holds. Each one costs a request
# for that repository's most recent commit, so this is a budget as well as a
# layout number.
REVISIONS = 3

# Identifying the build is a courtesy to the API it leans on.
UA = "henrykanaskie-profile-build/1.0 (+https://github.com/henrykanaskie)"

GH = "https://api.github.com"


# ── transport ────────────────────────────────────────────────────────────────

def _get_json(url, headers=None, cache=None):
    """GET and parse JSON, with a timeout and an optional in-process cache.

    The cache is keyed by full URL and lives for one `collect()` call. It
    matters because three channels want the repository list and re-fetching it
    would spend two more requests against a 60/hour anonymous budget.
    """
    if cache is not None and url in cache:
        return cache[url]
    hdrs = {"User-Agent": UA, "Accept": "application/json"}
    if headers:
        hdrs.update(headers)
    req = urllib.request.Request(url, headers=hdrs)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        data = json.load(resp)
    if cache is not None:
        cache[url] = data
    return data


def _gh_headers():
    """Headers for a GitHub URL, authenticated when a token is in the env."""
    headers = {"Accept": "application/vnd.github+json"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _gh(path, cache):
    """GitHub API GET.

    Unauthenticated access is capped at 60 requests/hour and the language
    channel makes one call per repository, so a GITHUB_TOKEN from the
    environment is used when present (5000/hour) and anonymous access is the
    local fallback. The workflow passes the token it already has; nothing here
    needs a secret configured by hand.
    """
    return _get_json(GH + path, _gh_headers(), cache)


def _reason(exc):
    """One short phrase describing a failure, fit to print in a notes block."""
    if isinstance(exc, urllib.error.HTTPError):
        if exc.code in (403, 429):
            return f"HTTP {exc.code}, rate limited"
        return f"HTTP {exc.code}"
    if isinstance(exc, urllib.error.URLError):
        return f"unreachable ({exc.reason})"
    if isinstance(exc, TimeoutError):
        return f"no response in {TIMEOUT}s"
    if isinstance(exc, (json.JSONDecodeError, ValueError)):
        return "malformed response"
    # AttributeError is the usual shape of a schema change: a list arriving
    # where an object was documented, so .get() is missing rather than the key.
    if isinstance(exc, (KeyError, IndexError, TypeError, AttributeError)):
        return "unexpected response shape"
    return type(exc).__name__


def _channel(errors, label, fallback, fn, *args, **kwargs):
    """Run one channel, degrading to `fallback` and a note instead of raising.

    This is the whole graceful-degradation story. Every fetch below goes
    through it, which is why none of them carry their own try/except and why
    adding a channel cannot introduce a new way for the build to die.
    """
    try:
        return fn(*args, **kwargs)
    except Exception as exc:                       # deliberately broad: see above
        errors.append(f"{label}: {_reason(exc)}")
        return fallback


def _iso(value):
    """Parse an ISO 8601 timestamp to an aware UTC datetime, or None.

    fromisoformat only learned to read a trailing "Z" in 3.11, so it is
    rewritten here rather than relying on the runner's Python being recent.
    """
    if not value:
        return None
    stamp = dt.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=dt.timezone.utc)
    return stamp.astimezone(dt.timezone.utc)


def _slug(url_or_name):
    """`owner/name` out of a repository URL, or None if it isn't one."""
    if not url_or_name:
        return None
    parts = [s for s in str(url_or_name).rstrip("/").split("/") if s]
    if len(parts) < 2:
        return None
    return f"{parts[-2]}/{parts[-1]}"


def _tracked(cfg):
    """Every project on the bill of materials that has a public repository.

    Returns a list of (project name, "owner/repo"). Projects with no `repo` are
    private or unpushed and cannot be looked up, so they are simply absent: the
    timeline falls back to the dates written in profile.toml for those, and the
    revision table never mentions them.
    """
    out = []
    for project in cfg.get("projects") or []:
        slug = _slug(project.get("repo"))
        if slug:
            out.append((str(project.get("name") or slug), slug))
    return out


# ── GitHub: languages ────────────────────────────────────────────────────────

def _fetch_languages(cfg, user, cache):
    """Language mix with every repository weighted equally.

    Summing raw bytes lets one verbose project speak for the whole profile: the
    personal site was 359 KB of the 787 KB total and so read as 46% TypeScript,
    against Python being the primary language in seven of nine repositories.
    Bytes measure how much a language types, not how much it is used. So each
    repository contributes its *own* percentage breakdown and those breakdowns
    are averaged across repositories. One repo, one vote.

    Forks are skipped because they are someone else's line count, and a repo
    whose kept bytes fall under `min_bytes` is skipped because a placeholder
    should not get a vote equal to a real project. `total_bytes` still counts
    those bytes: it is a measure of code written, not a measure of who votes.

    `min_share` and `show` from the same config table are deliberately not
    applied here. They decide what fits on a card, which is the renderer's
    problem. This returns the complete normalized distribution.

    Set `weighting = "bytes"` in [languages] to sum raw bytes instead. The two
    answer different questions and the gap is not small. Measured 2026-08-24:

                    equal        bytes
        Python      64.7%        23.3%
        Swift        7.9%        49.4%
        C            9.1%         0.2%

    Equal weighting says "Python is what I reach for", byte weighting says "the
    Swift apps are where the code actually is". Both are true. Equal is the
    default because a finished 700-line C shell disappearing to 0.2% behind two
    large GUI apps reads as inaccurate to anyone who knows the work, but the
    choice is yours and the card footnote states which one is in force.
    """
    lang_cfg = cfg.get("languages", {}) or {}
    exclude = set(lang_cfg.get("exclude", []))
    min_bytes = int(lang_cfg.get("min_bytes", 0))
    by_bytes = str(lang_cfg.get("weighting", "equal")).lower() == "bytes"

    repos = _gh(f"/users/{user}/repos?per_page=100", cache)
    shares, total_bytes = collections.defaultdict(float), 0
    for repo in repos:
        if repo.get("fork"):
            continue
        url = repo.get("languages_url")
        if not url:
            continue
        kept = {k: v for k, v in _get_json(url, _gh_headers(), cache).items()
                if k not in exclude}
        repo_bytes = sum(kept.values())
        total_bytes += repo_bytes
        if repo_bytes < min_bytes:
            continue
        for name, count in kept.items():
            # One repo one vote, or one byte one vote. The normalization below
            # is the same either way, so only the increment differs.
            shares[name] += count if by_bytes else count / repo_bytes

    # Each repo contributed 1.0 in total, so dividing by the number of voting
    # repos is the same normalization as dividing by the sum. Done by sum so a
    # rounding difference can never leave the shares off 1.0.
    grand = sum(shares.values())
    if not grand:
        return [], total_bytes
    ranked = sorted(((k, v / grand) for k, v in shares.items()),
                    key=lambda kv: (-kv[1], kv[0]))
    return ranked, total_bytes


# ── GitHub: account ──────────────────────────────────────────────────────────

def _fetch_account(user, cache):
    profile = _gh(f"/users/{user}", cache)
    # Insisted on rather than defaulted: without it the sheet would print
    # "----" for the founding year and `errors` would claim nothing was wrong,
    # which is the one degraded state that looks identical to a healthy one.
    if "created_at" not in profile:
        raise KeyError("created_at")
    created = str(profile.get("created_at") or "")
    # "----" rather than an empty string: it reads as a dashed placeholder in
    # the title block, which is what a drawing does with a value it lacks.
    return int(profile.get("public_repos") or 0), (created[:4] or "----")


def _fetch_last_push(user, cache):
    """The most recent push this account made, to anything.

    Read from the public events feed rather than from the repository list,
    because the events feed is the only source that dates a push to the minute.
    The feed is capped at 300 events and roughly 90 days; an account quiet for
    longer than that returns None, which is the correct answer for a field that
    says how long ago the last push was.
    """
    events = _gh(f"/users/{user}/events/public?per_page=100", cache)
    best = None
    for event in events:
        if event.get("type") != "PushEvent":
            continue
        at = _iso(event.get("created_at"))
        if at is None:
            continue
        # A full repo path is "owner/name"; the owner is redundant on a card
        # about this user's own pushes.
        name = str(event.get("repo", {}).get("name", "")).split("/")[-1]
        if best is None or at > best["at"]:
            best = {"repo": name, "at": at}
    return best


def _fetch_pushed_at(user, cache):
    """When each visible repository was last pushed to, keyed by lowercase name.

    The timeline uses this to extend an active project's bar to its real most
    recent commit without anyone editing profile.toml. Reuses the cached
    repository list, so it costs no additional request.

    Private repositories are not in this list. That is not a failure: a private
    project's bar is drawn from the dates in the config, and the sheet says so.
    """
    out = {}
    for repo in _gh(f"/users/{user}/repos?per_page=100", cache):
        name = str(repo.get("name") or "")
        at = _iso(repo.get("pushed_at"))
        if name and at:
            out[name.lower()] = at
    return out


def _fetch_revisions(cfg, cache, pushed_at, limit=REVISIONS):
    """The most recent commit on each of the projects pushed to most recently.

    This is what the title block's revision table draws, and every cell of it is
    measured: the repository, the subject line of the commit, and the time it
    was authored.

    It is NOT read from the events feed, which is where the obvious
    implementation goes first. The public events API strips `payload.commits`
    for unauthenticated reads and returns an empty array, so a revision table
    built on it letters three blank descriptions and looks like a bug in the
    renderer. One request per repository against `/commits?per_page=1` is the
    only source that carries the message, so the row count is deliberately
    small.

    Only projects on the bill of materials are eligible. The table is a record
    of what changed in the work this drawing set is about, not a feed of
    everything the account touched, and without that scope the top three rows
    would be this repository's own daily rebuild commit three times over.
    """
    tracked = _tracked(cfg)
    if not tracked:
        return []

    # Ordered by the push time already in hand, so choosing which three
    # repositories to ask about costs nothing.
    ranked = sorted(
        tracked,
        key=lambda item: pushed_at.get(item[1].split("/")[-1].lower())
        or dt.datetime.min.replace(tzinfo=dt.timezone.utc),
        reverse=True)

    rows = []
    for name, slug in ranked[:limit]:
        try:
            commits = _get_json(f"{GH}/repos/{slug}/commits?per_page=1",
                                _gh_headers(), cache)
        except Exception:
            # One unreachable repository must not cost the other two their
            # rows. The table draws what it has and voids the rest.
            continue
        if not commits:
            continue
        commit = (commits[0] or {}).get("commit") or {}
        # Only the subject line. A commit body is paragraphs long and the
        # column is one line, so taking the first line is the honest cut.
        message = str(commit.get("message") or "").strip().split("\n")[0]
        at = _iso((commit.get("author") or {}).get("date"))
        if not message or at is None:
            continue
        rows.append({"repo": name, "message": message, "at": at})
    return rows


# ── offline sample ───────────────────────────────────────────────────────────

def _sample(cfg, now):
    """Plausible values with no sockets opened.

    Every field is non-None so the renderer exercises its populated path rather
    than its NO DATA path. Anything derived from a date is built off `now`, so
    the sample never drifts into looking stale.
    """
    tracked = _tracked(cfg)
    # Push times come from each project's own recorded last commit rather than
    # from a spread of days off `now`. Inventing them put a bar on the timeline
    # running to today for a project finished eighteen months ago, so the one
    # sheet an offline build exists to let you lay out was the one sheet it
    # drew wrongly.
    by_name = {str(p.get("name") or ""): p for p in (cfg.get("projects") or [])}
    pushed = {}
    for name, slug in tracked:
        last = (by_name.get(name) or {}).get("last")
        if isinstance(last, dt.datetime):
            last = last.date()
        if isinstance(last, dt.date):
            pushed[slug.split("/")[-1].lower()] = dt.datetime(
                last.year, last.month, last.day, tzinfo=dt.timezone.utc)
    revisions = [
        {"repo": name, "message": msg, "at": now - dt.timedelta(hours=3 + 20 * i)}
        for i, ((name, _slug), msg) in enumerate(zip(tracked[:REVISIONS], (
            "Score last week's predictions against the closing line",
            "Watchdog holds the pipe so the server dies with the app",
            "Seat lattice keeps a character inside its own column")))]
    return {
        "generated_at": now,
        "languages": [("Python", 0.52), ("Swift", 0.18), ("C", 0.12),
                      ("JavaScript", 0.10), ("TypeScript", 0.05),
                      ("Shell", 0.03)],
        "total_bytes": 787_000,
        "repos": 12,
        "since_year": "2021",
        "last_push": {"repo": tracked[0][0] if tracked else "aggregateAnalytics",
                      "at": now - dt.timedelta(hours=5)},
        "pushed_at": pushed,
        "revisions": revisions,
        "errors": ["offline: sample data, no network calls made"],
    }


# ── entry point ──────────────────────────────────────────────────────────────

def collect(cfg, *, offline=False):
    """Gather everything the cards need. Never raises.

    `cfg` is the parsed data/profile.toml. The return value has a fixed set of
    keys whatever happens: a channel that fails or is switched off is None (or
    [] / {} / 0), so the renderer branches on the value rather than on key
    presence.
    """
    now = dt.datetime.now(dt.timezone.utc)
    if offline:
        return _sample(cfg, now)

    errors = []
    cache = {}
    user = (cfg.get("identity", {}) or {}).get("github", "")
    enabled = bool((cfg.get("sources", {}) or {}).get("github", True))

    languages, total_bytes = [], 0
    repos, since_year = 0, "----"
    last_push, pushed_at, revisions = None, {}, []

    if user and enabled:
        languages, total_bytes = _channel(
            errors, "languages", ([], 0), _fetch_languages, cfg, user, cache)
        repos, since_year = _channel(
            errors, "account", (0, "----"), _fetch_account, user, cache)
        last_push = _channel(
            errors, "last push", None, _fetch_last_push, user, cache)
        pushed_at = _channel(
            errors, "push times", {}, _fetch_pushed_at, user, cache)
        # Ordered after push times deliberately: it picks which repositories to
        # ask about from that result, and an empty one just means the rows come
        # out in bill-of-materials order instead of by recency.
        revisions = _channel(
            errors, "revisions", [], _fetch_revisions, cfg, cache, pushed_at)

    return {
        "generated_at": now,
        "languages": languages,
        "total_bytes": total_bytes,
        "repos": repos,
        "since_year": since_year,
        "last_push": last_push,
        "pushed_at": pushed_at,
        "revisions": revisions,
        "errors": errors,
    }


if __name__ == "__main__":
    import pprint
    import sys
    import tomllib

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(root, "data", "profile.toml"), "rb") as fh:
        pprint.pp(collect(tomllib.load(fh), offline="--offline" in sys.argv))
