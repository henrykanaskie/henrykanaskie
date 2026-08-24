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

Standard library only. The workflow installs nothing, so there is no
requirements file to drift and no cache to warm.

    collect(cfg)                  # live
    collect(cfg, offline=True)    # sample data, no sockets opened

Channels are gated by the [telemetry] table in data/profile.toml. A channel
switched off there returns None with *no* entry in `errors`. Off by design and
broken are different states, and a caller should not have to guess which one it
is looking at.
"""

from __future__ import annotations

import collections
import datetime as dt
import json
import os
import urllib.error
import urllib.parse
import urllib.request

ACTIVITY_DAYS = 30
TIMEOUT = 10

# Identifying the build is a courtesy to the free APIs it leans on, and
# thespacedevs in particular will refuse an anonymous request without one.
UA = "henrykanaskie-profile-build/1.0 (+https://github.com/henrykanaskie)"

GH = "https://api.github.com"
LL = "https://ll.thespacedevs.com/2.3.0"
ISS_URL = "https://api.wheretheiss.at/v1/satellites/25544"
LASTFM = "https://ws.audioscrobbler.com/2.0/"


# ── transport ────────────────────────────────────────────────────────────────

def _get_json(url, headers=None, cache=None):
    """GET and parse JSON, with a timeout and an optional in-process cache.

    The cache is keyed by full URL and lives for one `collect()` call. It
    matters because two channels want the repository list and re-fetching it
    would spend a second request against a 60/hour anonymous budget.
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


def _gh(path, cache):
    """GitHub API GET.

    Unauthenticated access is capped at 60 requests/hour and the language
    channel makes one call per repository, so a GITHUB_TOKEN from the
    environment is used when present (5000/hour) and anonymous access is the
    local fallback. The workflow passes the token it already has; nothing here
    needs a secret configured by hand.
    """
    headers = {"Accept": "application/vnd.github+json"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return _get_json(GH + path, headers, cache)


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


def _gh_headers():
    """Headers for a GitHub URL that arrives fully-formed (languages_url)."""
    headers = {"Accept": "application/vnd.github+json"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


# ── GitHub: account and activity ─────────────────────────────────────────────

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


def _fetch_activity(user, cache):
    """Per-day push counts over the trailing 30 days, plus what they imply.

    These are PUSHES, not commits. The public events API strips per-push commit
    counts for unauthenticated reads, so `payload.size` cannot be trusted and is
    not consulted. Nothing downstream should say "commits". One push carrying
    nine commits counts once here, so any other label on this number is wrong.

    The series is dense and zero-filled so the renderer can index it by position
    without reasoning about gaps.
    """
    events = _gh(f"/users/{user}/events/public?per_page=100", cache)

    today = dt.datetime.now(dt.timezone.utc).date()
    first = today - dt.timedelta(days=ACTIVITY_DAYS - 1)

    per_day = collections.Counter()
    per_repo = collections.Counter()
    last = None
    for event in events:
        if event.get("type") != "PushEvent":
            continue
        at = _iso(event.get("created_at"))
        if at is None:
            continue
        # A full repo path is "owner/name"; the owner is redundant on a card
        # about this user's own pushes.
        name = str(event.get("repo", {}).get("name", "")).split("/")[-1]
        if last is None or at > last[1]:
            last = (name, at)
        day = at.date()
        # top_repos is scoped to the same window as the chart, so the ranking
        # and the bars can never describe different stretches of time.
        if first <= day <= today:
            per_day[day] += 1
            if name:
                per_repo[name] += 1

    days = [first + dt.timedelta(days=i) for i in range(ACTIVITY_DAYS)]
    series = [(day, per_day.get(day, 0)) for day in days]
    top = per_repo.most_common(3)
    last_push = {"repo": last[0], "at": last[1]} if last else None
    return series, top, last_push, _streak(series)


def _streak(series):
    """Consecutive days ending today or yesterday with at least one push.

    Today is allowed to be empty without breaking the streak, because the build
    runs at 13:00 UTC and a day's work has usually not happened yet.
    """
    counts = [n for _, n in series]
    i = len(counts) - 1
    if i < 0:
        return 0
    if counts[i] == 0:
        i -= 1
    run = 0
    while i >= 0 and counts[i] > 0:
        run += 1
        i -= 1
    return run


def _fetch_quietest(cfg, user, cache, now):
    """The tracked project that has gone longest without a push.

    Only projects listed in profile.toml with a `repo` URL are eligible: the
    point is a nudge about work the sheet claims to be doing, not a report on
    every repository the account happens to hold. Reuses the cached repo list,
    so this channel costs no additional request.
    """
    tracked = set()
    for project in cfg.get("projects", []) or []:
        url = project.get("repo")
        if url:
            tracked.add(str(url).rstrip("/").rsplit("/", 1)[-1].lower())
    if not tracked:
        return None

    oldest = None
    for repo in _gh(f"/users/{user}/repos?per_page=100", cache):
        name = str(repo.get("name") or "")
        if name.lower() not in tracked:
            continue
        at = _iso(repo.get("pushed_at"))
        if at is None:
            continue
        if oldest is None or at < oldest[1]:
            oldest = (name, at)
    if oldest is None:
        return None
    return {"repo": oldest[0], "days": max(0, (now - oldest[1]).days)}


# ── space ────────────────────────────────────────────────────────────────────

def _fetch_launch():
    """The next orbital launch worldwide.

    Anonymous access to thespacedevs is roughly 15 requests/hour, so this makes
    exactly one call and asks for exactly one result. `mode=list` keeps the
    response small enough to be polite, at the cost of dropping the `pad`
    object. That is what the fallback below is for, and it is the normal path
    rather than an edge case.
    """
    data = _get_json(f"{LL}/launches/upcoming/?limit=1&mode=list")
    results = data.get("results") or []
    if not results:
        return None
    launch = results[0]

    # Names arrive as "Long March 6C | Unknown Payload": provider before the
    # pipe, mission after it. In list mode this split is the only source for
    # either.
    raw = str(launch.get("name") or "")
    provider, _, mission = raw.partition(" | ")
    provider = provider.strip() or None
    name = (mission.strip() or raw.strip()) or None

    pad = None
    pad_obj = launch.get("pad") or {}
    if isinstance(pad_obj, dict):
        location = pad_obj.get("location") or {}
        pad = (location.get("name") if isinstance(location, dict) else None) \
            or pad_obj.get("name")

    status = (launch.get("status") or {}).get("abbrev")
    return {
        "name": name,
        "provider": provider,
        "pad": pad,
        "net": _iso(launch.get("net")),
        "status": status,
    }


def _fetch_humans():
    """How many people are off the planet, per thespacedevs' own count.

    Not api.open-notify.org: it still serves a 2024 crew roster and would put a
    confidently wrong number on the sheet. Only `count` is read, so limit=1 is
    enough and the single result row is discarded.
    """
    data = _get_json(f"{LL}/astronauts/?in_space=true&limit=1&mode=list")
    count = data.get("count")
    if count is None:
        raise KeyError("count")
    return int(count)


def _fetch_iss(now):
    data = _get_json(ISS_URL)
    return {
        "lat": float(data["latitude"]),
        "lon": float(data["longitude"]),
        "alt_km": float(data["altitude"]),
        "vel_kmh": float(data["velocity"]),
        # The API stamps its own fix; prefer it over the local clock so the
        # position and its time are the same instant.
        "at": (dt.datetime.fromtimestamp(data["timestamp"], dt.timezone.utc)
               if data.get("timestamp") else now),
    }


# ── listening ────────────────────────────────────────────────────────────────

def _fetch_listening(user, key):
    query = urllib.parse.urlencode({
        "method": "user.getrecenttracks", "user": user,
        "api_key": key, "format": "json", "limit": 1,
    })
    data = _get_json(f"{LASTFM}?{query}")
    tracks = (data.get("recenttracks") or {}).get("track") or []
    if isinstance(tracks, dict):        # Last.fm unwraps a single-item list
        tracks = [tracks]
    if not tracks:
        return None
    track = tracks[0]

    attr = track.get("@attr") or {}
    now_playing = str(attr.get("nowplaying", "")).lower() == "true"
    at = None
    uts = (track.get("date") or {}).get("uts")
    if uts:
        at = dt.datetime.fromtimestamp(int(uts), dt.timezone.utc)
    return {
        "artist": (track.get("artist") or {}).get("#text"),
        "track": track.get("name"),
        # A now-playing track carries no date; that absence is the signal, so
        # `at` stays None rather than being faked to the current time.
        "now_playing": now_playing,
        "at": at,
    }


# ── offline sample ───────────────────────────────────────────────────────────

def _sample(now):
    """Plausible values with no sockets opened.

    Every field is non-None so the renderer exercises its populated path rather
    than its NO DATA path. Anything derived from a date is built off `now`, so
    the sample never drifts into looking stale.
    """
    today = now.date()
    first = today - dt.timedelta(days=ACTIVITY_DAYS - 1)
    # A fixed, uneven pattern: a real chart has gaps and spikes, and a smooth
    # ramp would hide a renderer bug that a lumpy series exposes.
    shape = [0, 2, 1, 0, 0, 4, 3, 1, 0, 6, 2, 0, 0, 1, 5,
             3, 0, 2, 7, 1, 0, 0, 3, 4, 2, 1, 0, 5, 3, 2]
    return {
        "generated_at": now,
        "languages": [("Python", 0.52), ("Swift", 0.18), ("C", 0.12),
                      ("TypeScript", 0.10), ("JavaScript", 0.05),
                      ("Shell", 0.03)],
        "total_bytes": 787_000,
        "repos": 12,
        "since_year": "2021",
        "activity": [(first + dt.timedelta(days=i), shape[i])
                     for i in range(ACTIVITY_DAYS)],
        "top_repos": [("animAgent", 14), ("me-tutor", 9), ("gpt-scratch", 5)],
        "last_push": {"repo": "animAgent", "at": now - dt.timedelta(hours=5)},
        "streak": 3,
        "quietest": {"repo": "small-shell", "days": 214},
        "launch": {
            "name": "Unknown Payload",
            "provider": "Long March 6C",
            "pad": None,
            "net": now + dt.timedelta(hours=14),
            "status": "Go",
        },
        "humans": 11,
        "iss": {"lat": 51.7041, "lon": -40.0826, "alt_km": 418.76,
                "vel_kmh": 27609.2, "at": now},
        "listening": {"artist": "Nils Frahm", "track": "Says",
                      "now_playing": False, "at": now - dt.timedelta(minutes=22)},
        "errors": ["offline: sample data, no network calls made"],
    }


# ── entry point ──────────────────────────────────────────────────────────────

def collect(cfg, *, offline=False):
    """Gather everything the cards need. Never raises.

    `cfg` is the parsed data/profile.toml. The return value has a fixed set of
    keys whatever happens: a channel that fails or is switched off is None (or
    [] / 0), so the renderer branches on the value rather than on key presence.
    """
    now = dt.datetime.now(dt.timezone.utc)
    if offline:
        return _sample(now)

    errors = []
    cache = {}
    telemetry = cfg.get("telemetry", {}) or {}
    user = (cfg.get("identity", {}) or {}).get("github", "")

    languages, total_bytes = [], 0
    repos, since_year = 0, "----"
    top_repos, last_push, streak, quietest = [], None, 0, None

    # The failure fallback for activity is an EMPTY series, deliberately, and
    # not a 30-day run of zeros.
    #
    # Thirty zeros is a measurement. It says this person pushed nothing for
    # thirty days, and it plots as a flat line, which is the honest picture of a
    # quiet month. An unreachable events API says nothing at all, and it must
    # not borrow that flat line: the line is a claim the outage cannot support.
    # Handing zeros to the renderer on failure turns downtime into an accusation.
    #
    # An empty list cannot be plotted, so it forces the card into its
    # voided-field branch and the cell reads NO DATA. A genuinely quiet month
    # still arrives from _fetch_activity as thirty real zeros and still gets its
    # flat line.
    activity = []

    if user and telemetry.get("repo_telemetry", True):
        languages, total_bytes = _channel(
            errors, "languages", ([], 0), _fetch_languages, cfg, user, cache)
        repos, since_year = _channel(
            errors, "account", (0, "----"), _fetch_account, user, cache)
        activity, top_repos, last_push, streak = _channel(
            errors, "activity", ([], [], None, 0),
            _fetch_activity, user, cache)
        quietest = _channel(
            errors, "quietest", None, _fetch_quietest, cfg, user, cache, now)

    launch = None
    if telemetry.get("launch_window", True):
        launch = _channel(errors, "launch", None, _fetch_launch)

    humans = None
    if telemetry.get("humans_in_space", True):
        humans = _channel(errors, "humans in space", None, _fetch_humans)

    iss = None
    if telemetry.get("iss_track", True):
        iss = _channel(errors, "ISS", None, _fetch_iss, now)

    # Off unless both halves are present. A missing key is the documented
    # default state, not a fault, so it adds nothing to `errors`.
    listening = None
    music = telemetry.get("listening", {}) or {}
    key = os.environ.get("LASTFM_API_KEY")
    if music.get("enabled") and key and music.get("user"):
        listening = _channel(errors, "listening", None,
                             _fetch_listening, music["user"], key)

    return {
        "generated_at": now,
        "languages": languages,
        "total_bytes": total_bytes,
        "repos": repos,
        "since_year": since_year,
        "activity": activity,
        "top_repos": top_repos,
        "last_push": last_push,
        "streak": streak,
        "quietest": quietest,
        "launch": launch,
        "humans": humans,
        "iss": iss,
        "listening": listening,
        "errors": errors,
    }


if __name__ == "__main__":
    import pprint
    import sys
    import tomllib

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(root, "data", "profile.toml"), "rb") as fh:
        pprint.pp(collect(tomllib.load(fh), offline="--offline" in sys.argv))
