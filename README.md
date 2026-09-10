<!--
  ╔══════════════════════════════════════════════════════════════════════════╗
  ║  GENERATED FILE. DO NOT EDIT.                                            ║
  ║                                                                          ║
  ║  Every word below comes from data/profile.toml, laid into                ║
  ║  templates/README.md.tmpl by scripts/build.py. Edits made here are       ║
  ║  overwritten by the next daily build.                                    ║
  ║                                                                          ║
  ║      change the words   ->  data/profile.toml                            ║
  ║      change the layout  ->  templates/README.md.tmpl                     ║
  ║      change the cards   ->  scripts/cards.py                             ║
  ╚══════════════════════════════════════════════════════════════════════════╝

  LAYOUT NOTE

  There are no markdown headings and no horizontal rules in this file, and that
  is deliberate. Every sheet carries its own label inside the drawing frame, and
  the frames already separate one sheet from the next. A GitHub `###` heading
  set in the default UI font, sitting directly above a monospace drawing, was
  the single thing making the page read as two documents stapled together.

  Links are drawings too. An <img> is inert, so nothing inside a sheet is
  clickable, and GitHub's sanitiser removes inline <svg>, <object> and <map>.
  What it keeps is an <a> around a <picture>, so every link on this page is its
  own small chip SVG wrapped in an anchor. They are emitted with no whitespace
  between them, because a newline between two inline images renders as a gap.

  There is no plain-text copy of the sheets any more. What a screen reader gets
  is the alt text, so the alt text is written to carry the content rather than
  to name the picture: the bill of materials lists its parts and their status,
  the timeline reads out each project's dates and commit count. Keep it that
  way when adding a sheet.
-->

<div align="center">

<picture>
  <source media="(max-width: 500px) and (prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/titleblock-narrow-dark.svg?v=c71475ece6">
  <source media="(max-width: 500px)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/titleblock-narrow-light.svg?v=a8ef948086">
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/titleblock-dark.svg?v=49fab6279c">
  <img src="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/titleblock-light.svg?v=8c78e207a3" alt="Title block. Henry Kanaskie. MACHINE LEARNING · SIGNAL PROCESSING · TOOLS I USE MYSELF. I like building things and taking them apart to see how they work. MS STUDENT, OREGON STATE, CORVALLIS, OREGON. Recent commits: aggregateAnalytics, Lines snapshot 2026-09-09 23:34 UTC; Ground-Control, Give each colour one job; animAgent, feat(scene): compact rooms, and a room that says whose it is.">
</picture>

<picture><source media="(max-width: 500px)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/rail-blank.svg?v=9059e608fe"><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/rail-links-dark.svg?v=97d92cb020"><img src="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/rail-links-light.svg?v=6a349416aa" alt=""></picture><a href="https://henrykanaskie.com"><picture><source media="(max-width: 500px) and (prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-site-narrow-dark.svg?v=20c4c5c1c8"><source media="(max-width: 500px)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-site-narrow-light.svg?v=b2cea950d1"><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-site-dark.svg?v=5956186fbb"><img src="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-site-light.svg?v=2f0fec82c8" alt="henrykanaskie.com"></picture></a><a href="https://github.com/henrykanaskie?tab=repositories"><picture><source media="(max-width: 500px) and (prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-repos-narrow-dark.svg?v=97c99b5425"><source media="(max-width: 500px)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-repos-narrow-light.svg?v=937b74f8ca"><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-repos-dark.svg?v=13d5c8f635"><img src="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-repos-light.svg?v=98b2e93e34" alt="repositories"></picture></a><a href="SETUP.md"><picture><source media="(max-width: 500px) and (prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-setup-narrow-dark.svg?v=459a84d22c"><source media="(max-width: 500px)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-setup-narrow-light.svg?v=b716ad92ac"><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-setup-dark.svg?v=e823c0f080"><img src="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-setup-light.svg?v=78b2aece65" alt="how this is built"></picture></a><a href="data/profile.toml"><picture><source media="(max-width: 500px) and (prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-source-narrow-dark.svg?v=26f5efe254"><source media="(max-width: 500px)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-source-narrow-light.svg?v=410f0eba46"><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-source-dark.svg?v=4ddaae53c8"><img src="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-source-light.svg?v=bb53ba5025" alt="the source of truth"></picture></a>

<picture>
  <source media="(max-width: 500px) and (prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/general-narrow-dark.svg?v=edacdb80e2">
  <source media="(max-width: 500px)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/general-narrow-light.svg?v=a83d436ecf">
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/general-dark.svg?v=3c23e8b8a3">
  <img src="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/general-light.svg?v=122d666e70" alt="I'm a computer science student at Oregon State, working on a master's after finishing my undergrad there. Most of what's on this sheet exists because I wanted to use it, or because I didn't understand something well enough and building it was the only way I was going to. Some of it came out of research: a matching-network solver for the plasma lab, signal processing for thruster data. The rest is tools I open every day, and a leaderboard for my group chat. Master's in CS at Oregon State, after two years of undergrad research in the plasma lab. Six months at DZYNE Technologies on embedded C/C++ and the test framework around it. Away from a keyboard I'm usually behind a camera, on skis, or in the gym. Focus areas: machine learning, signal processing, embedded C, optimization, time series, FPGA / VHDL, SwiftUI, agents, data pipelines.">
</picture>

<picture>
  <source media="(max-width: 500px) and (prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/bom-narrow-dark.svg?v=c38cfad9c9">
  <source media="(max-width: 500px)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/bom-narrow-light.svg?v=3c0dc58543">
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/bom-dark.svg?v=fea2e44eba">
  <img src="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/bom-light.svg?v=a4baa662ab" alt="Bill of materials. Cap_Match_Net qualified at 100%, small-shell qualified at 100%, floralytics qualified at 100%, accliMate qualified at 100%, animAgent qualified at 100%, groupStat qualified at 100%, Ground-Control flight at 90%, orchestrate flight at 90%, GrowthApp flight at 62%, aggregateAnalytics flight at 60%.">
</picture>

<picture><source media="(max-width: 500px)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/rail-blank.svg?v=9059e608fe"><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/rail-repos-dark.svg?v=621fb8f42a"><img src="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/rail-repos-light.svg?v=ffef6631fe" alt=""></picture><a href="https://github.com/henrykanaskie/Cap_Match_Net"><picture><source media="(max-width: 500px) and (prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-opt-01-narrow-dark.svg?v=8793ecee82"><source media="(max-width: 500px)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-opt-01-narrow-light.svg?v=b766758828"><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-opt-01-dark.svg?v=73fabb660c"><img src="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-opt-01-light.svg?v=77ea9499da" alt="Cap_Match_Net"></picture></a><a href="https://github.com/henrykanaskie/small-shell"><picture><source media="(max-width: 500px) and (prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-sys-01-narrow-dark.svg?v=70fd952e8c"><source media="(max-width: 500px)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-sys-01-narrow-light.svg?v=8cd0a24d9d"><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-sys-01-dark.svg?v=bf35265418"><img src="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-sys-01-light.svg?v=18ba65dcca" alt="small-shell"></picture></a><a href="https://github.com/Kellen-Sullivan/bee-plant-data-exploration"><picture><source media="(max-width: 500px) and (prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-mdl-02-narrow-dark.svg?v=49a37efed0"><source media="(max-width: 500px)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-mdl-02-narrow-light.svg?v=f40239cbe4"><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-mdl-02-dark.svg?v=7a46209371"><img src="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-mdl-02-light.svg?v=e65c957f97" alt="floralytics"></picture></a>

<a href="https://github.com/henrykanaskie/accliMate"><picture><source media="(max-width: 500px) and (prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-app-03-narrow-dark.svg?v=b4a5c65301"><source media="(max-width: 500px)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-app-03-narrow-light.svg?v=9b565359af"><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-app-03-dark.svg?v=9df5a1084c"><img src="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-app-03-light.svg?v=927b02865a" alt="accliMate"></picture></a><a href="https://github.com/henrykanaskie/animAgent"><picture><source media="(max-width: 500px) and (prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-app-01-narrow-dark.svg?v=018870e318"><source media="(max-width: 500px)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-app-01-narrow-light.svg?v=e34b36cd40"><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-app-01-dark.svg?v=00a69dee00"><img src="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-app-01-light.svg?v=1ee5e0b1a9" alt="animAgent"></picture></a><a href="https://github.com/henrykanaskie/Ground-Control"><picture><source media="(max-width: 500px) and (prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-tul-03-narrow-dark.svg?v=bf1e39aff6"><source media="(max-width: 500px)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-tul-03-narrow-light.svg?v=c84363713f"><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-tul-03-dark.svg?v=7a4e9026fe"><img src="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-tul-03-light.svg?v=8337403ac4" alt="Ground-Control"></picture></a><a href="https://github.com/henrykanaskie/aggregateAnalytics"><picture><source media="(max-width: 500px) and (prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-qnt-01-narrow-dark.svg?v=0e4e58a751"><source media="(max-width: 500px)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-qnt-01-narrow-light.svg?v=ca8a8077a1"><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-qnt-01-dark.svg?v=2dafee07a6"><img src="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-qnt-01-light.svg?v=fdb9a9ec46" alt="aggregateAnalytics"></picture></a>

</div>

<div align="center">

<picture>
  <source media="(max-width: 500px) and (prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/timeline-narrow-dark.svg?v=3e588bf30b">
  <source media="(max-width: 500px)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/timeline-narrow-light.svg?v=13f408983d">
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/timeline-dark.svg?v=0484c90550">
  <img src="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/timeline-light.svg?v=9b866514a7" alt="Project timeline, first commit to most recent. Cap_Match_Net, February 2026, 2 commits; small-shell, February 2025, 3 commits; floralytics, October 2025 to May 2026, 313 commits; accliMate, May 2026 to May 2026, 88 commits; animAgent, August 2026 to August 2026, 186 commits; groupStat, August 2026 to September 2026, 48 commits; Ground-Control, August 2026 to September 2026, 41 commits; orchestrate, August 2026 to September 2026, 128 commits; GrowthApp, July 2026 to August 2026, 1 commits; aggregateAnalytics, August 2026 to September 2026, 100 commits.">
</picture>

<picture>
  <source media="(max-width: 500px) and (prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/composition-narrow-dark.svg?v=eb78bfa1b3">
  <source media="(max-width: 500px)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/composition-narrow-light.svg?v=b32fa29e1e">
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/composition-dark.svg?v=94a125a042">
  <img src="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/composition-light.svg?v=cebdec66c9" alt="Language composition: Python 65%, TypeScript 11%, JavaScript 9%, C 8%, Swift 7%, Shell 0%.">
</picture>

<picture>
  <source media="(max-width: 500px) and (prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/toolbox-narrow-dark.svg?v=08d0204ba1">
  <source media="(max-width: 500px)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/toolbox-narrow-light.svg?v=ff8494adf4">
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/toolbox-dark.svg?v=92bf381e6e">
  <img src="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/toolbox-light.svg?v=34616f33e2" alt="Toolbox. Python for models, data pipelines, and anything that ends in a number I have to trust; C / C++ for embedded work and the OS-level projects, where the details are the point; Swift / SwiftUI for native macOS and iOS apps, and the small app shells I wrap servers in; Node, no deps for local dashboards that have to still run in a year with no install step; OR-Tools for constraint problems where the answer has to be a part you can order; polars for season-scale football data, because pandas was the slow half of the loop; tree-sitter for splitting code by function and class instead of by line count; MATLAB for plasma thruster signal processing in the lab, and only in the lab; VHDL for FPGA modules for reading sensors nobody could measure before.">
</picture>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/output/github-snake-dark.svg">
  <img src="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/output/github-snake.svg" alt="A snake eating the contribution graph">
</picture>

<sub>
6 SHEETS &nbsp;·&nbsp; BUILT 2026-09-10 07:28 UTC<br>
Drawn from <code>data/profile.toml</code> by <code>scripts/build.py</code>, rebuilt every morning.<br>
The sheets draw themselves in when they load. Where SMIL is unsupported they arrive finished.
</sub>

<br><br>

<img src="https://komarev.com/ghpvc/?username=henrykanaskie&style=flat-square&color=1f6feb&labelColor=16202b&label=sheet+views" alt="Sheet views">

</div>
