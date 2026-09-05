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
  the telemetry sheet reads out its channels. Keep it that way when adding a
  sheet.
-->

<div align="center">

<picture>
  <source media="(max-width: 500px) and (prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/titleblock-narrow-dark.svg?v=4a5b94923a">
  <source media="(max-width: 500px)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/titleblock-narrow-light.svg?v=76002eb2ac">
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/titleblock-dark.svg?v=6533da90f0">
  <img src="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/titleblock-light.svg?v=8a5bd06ebb" alt="Title block. Henry Kanaskie. MODELS / HARDWARE / THE BOUNDARY BETWEEN. Machine learning and things that talk to hardware. Revision G.">
</picture>

<picture><source media="(max-width: 500px)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/rail-blank.svg?v=9059e608fe"><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/rail-links-dark.svg?v=97d92cb020"><img src="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/rail-links-light.svg?v=6a349416aa" alt=""></picture><a href="https://henrykanaskie.com"><picture><source media="(max-width: 500px) and (prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-site-narrow-dark.svg?v=20c4c5c1c8"><source media="(max-width: 500px)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-site-narrow-light.svg?v=b2cea950d1"><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-site-dark.svg?v=5956186fbb"><img src="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-site-light.svg?v=2f0fec82c8" alt="henrykanaskie.com"></picture></a><a href="https://github.com/henrykanaskie?tab=repositories"><picture><source media="(max-width: 500px) and (prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-repos-narrow-dark.svg?v=97c99b5425"><source media="(max-width: 500px)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-repos-narrow-light.svg?v=937b74f8ca"><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-repos-dark.svg?v=13d5c8f635"><img src="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-repos-light.svg?v=98b2e93e34" alt="repositories"></picture></a><a href="SETUP.md"><picture><source media="(max-width: 500px) and (prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-setup-narrow-dark.svg?v=459a84d22c"><source media="(max-width: 500px)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-setup-narrow-light.svg?v=b716ad92ac"><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-setup-dark.svg?v=e823c0f080"><img src="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-setup-light.svg?v=78b2aece65" alt="how this is built"></picture></a><a href="data/profile.toml"><picture><source media="(max-width: 500px) and (prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-source-narrow-dark.svg?v=26f5efe254"><source media="(max-width: 500px)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-source-narrow-light.svg?v=410f0eba46"><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-source-dark.svg?v=4ddaae53c8"><img src="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-source-light.svg?v=bb53ba5025" alt="the source of truth"></picture></a>

<picture>
  <source media="(max-width: 500px) and (prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/general-narrow-dark.svg?v=ca43ce30ee">
  <source media="(max-width: 500px)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/general-narrow-light.svg?v=980a2a95bd">
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/general-dark.svg?v=000bc24f14">
  <img src="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/general-light.svg?v=58d3193a62" alt="I work at the boundary between models and hardware. A transformer written from first principles, an optimizer that picks capacitor values you can actually buy, a habit tracker that draws your streaks as a neural graph. Most of it starts as a question I couldn't answer by reading, so I write the thing that answers it. Mostly on retrieval over code right now: AST-aware chunking, embeddings, citations that hold up. Just finished Floralytics, which factors Oregon's bee-plant records into habitat advice. Happiest in a debugger, at the point where the theory stops matching the trace. Focus areas: machine learning, transformers, time series, optimization, embedded C, signal processing, SwiftUI, agents, numerical methods.">
</picture>

<picture>
  <source media="(max-width: 500px) and (prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/bom-narrow-dark.svg?v=d57df999f6">
  <source media="(max-width: 500px)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/bom-narrow-light.svg?v=660810a40b">
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/bom-dark.svg?v=15bbca1d7a">
  <img src="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/bom-light.svg?v=ddb64e556c" alt="Bill of materials. Cap_Match_Net qualified at 100%, small-shell qualified at 100%, floralytics qualified at 100%, acclimate qualified at 100%, animAgent qualified at 100%, GrowthApp flight at 62%, rLog flight at 55%.">
</picture>

<picture><source media="(max-width: 500px)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/rail-blank.svg?v=9059e608fe"><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/rail-repos-dark.svg?v=621fb8f42a"><img src="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/rail-repos-light.svg?v=ffef6631fe" alt=""></picture><a href="https://github.com/henrykanaskie/Cap_Match_Net"><picture><source media="(max-width: 500px) and (prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-opt-01-narrow-dark.svg?v=8793ecee82"><source media="(max-width: 500px)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-opt-01-narrow-light.svg?v=b766758828"><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-opt-01-dark.svg?v=73fabb660c"><img src="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-opt-01-light.svg?v=77ea9499da" alt="Cap_Match_Net"></picture></a><a href="https://github.com/henrykanaskie/small-shell"><picture><source media="(max-width: 500px) and (prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-sys-01-narrow-dark.svg?v=70fd952e8c"><source media="(max-width: 500px)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-sys-01-narrow-light.svg?v=8cd0a24d9d"><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-sys-01-dark.svg?v=bf35265418"><img src="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-sys-01-light.svg?v=18ba65dcca" alt="small-shell"></picture></a><a href="https://github.com/Kellen-Sullivan/bee-plant-data-exploration"><picture><source media="(max-width: 500px) and (prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-mdl-02-narrow-dark.svg?v=49a37efed0"><source media="(max-width: 500px)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-mdl-02-narrow-light.svg?v=f40239cbe4"><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-mdl-02-dark.svg?v=7a46209371"><img src="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-mdl-02-light.svg?v=e65c957f97" alt="floralytics"></picture></a><a href="https://github.com/henrykanaskie/beaverhacks26"><picture><source media="(max-width: 500px) and (prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-app-03-narrow-dark.svg?v=b4a5c65301"><source media="(max-width: 500px)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-app-03-narrow-light.svg?v=9b565359af"><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-app-03-dark.svg?v=9df5a1084c"><img src="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-app-03-light.svg?v=927b02865a" alt="acclimate"></picture></a><a href="https://github.com/henrykanaskie/animAgent"><picture><source media="(max-width: 500px) and (prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-app-01-narrow-dark.svg?v=018870e318"><source media="(max-width: 500px)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-app-01-narrow-light.svg?v=e34b36cd40"><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-app-01-dark.svg?v=00a69dee00"><img src="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/chip-app-01-light.svg?v=1ee5e0b1a9" alt="animAgent"></picture></a>

</div>

<div align="center">

<picture>
  <source media="(max-width: 500px) and (prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/telemetry-narrow-dark.svg?v=1c39ce2ca9">
  <source media="(max-width: 500px)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/telemetry-narrow-light.svg?v=91d8c3e448">
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/telemetry-dark.svg?v=4d9f6f03f7">
  <img src="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/telemetry-light.svg?v=187f6f2591" alt="Daily telemetry. next launch Onward and Upward; 11 people in space; ISS at 17.3 degrees latitude; last push to nfl_predictor.">
</picture>

<picture>
  <source media="(max-width: 500px) and (prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/composition-narrow-dark.svg?v=f65071f8c6">
  <source media="(max-width: 500px)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/composition-narrow-light.svg?v=63b95e9892">
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/composition-dark.svg?v=3100b7298d">
  <img src="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/composition-light.svg?v=5605e96629" alt="Language composition: Python 68%, JavaScript 9%, C 8%, TypeScript 8%, Swift 7%, Shell 0%.">
</picture>

<picture>
  <source media="(max-width: 500px) and (prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/activity-narrow-dark.svg?v=e9de4cfad1">
  <source media="(max-width: 500px)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/activity-narrow-light.svg?v=2e54ff0a69">
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/activity-dark.svg?v=2d3e962de7">
  <img src="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/activity-light.svg?v=78d55bb1ee" alt="Push activity, 80 pushes over the last 30 days.">
</picture>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/output/github-snake-dark.svg">
  <img src="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/output/github-snake.svg" alt="A snake eating the contribution graph">
</picture>

<sub>
REV G &nbsp;·&nbsp; 6 SHEETS &nbsp;·&nbsp; BUILT 2026-09-05 15:44 UTC &nbsp;·&nbsp; SCALE NONE<br>
Drawn from <code>data/profile.toml</code> by <code>scripts/build.py</code>, rebuilt every morning.<br>
The sheets draw themselves in when they load. Where SMIL is unsupported they arrive finished.
</sub>

<br><br>

<img src="https://komarev.com/ghpvc/?username=henrykanaskie&style=flat-square&color=1f6feb&labelColor=16202b&label=sheet+views" alt="Sheet views">

</div>
