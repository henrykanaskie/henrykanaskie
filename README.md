<!--
  ╔══════════════════════════════════════════════════════════════════════════╗
  ║  GENERATED FILE — DO NOT EDIT                                            ║
  ║                                                                          ║
  ║  Every word below comes from data/profile.toml, laid into                ║
  ║  templates/README.md.tmpl by scripts/build.py. Edits made here are       ║
  ║  overwritten by the next daily build.                                    ║
  ║                                                                          ║
  ║      change the words   ->  data/profile.toml                            ║
  ║      change the layout  ->  templates/README.md.tmpl                     ║
  ║      change the cards   ->  scripts/cards.py                             ║
  ╚══════════════════════════════════════════════════════════════════════════╝
-->

<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/titleblock-dark.svg?v=20260824">
  <img src="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/titleblock-light.svg?v=20260824" alt="Title block">
</picture>

<em>Machine learning, quantitative research, and things that talk to hardware.</em>

<a href="https://henrykanaskie.com"><img src="https://img.shields.io/badge/henrykanaskie.com-16202b?style=flat-square&logo=safari&logoColor=white&labelColor=16202b" alt="Website"></a>
<a href="https://github.com/henrykanaskie?tab=repositories"><img src="https://img.shields.io/badge/repositories-16202b?style=flat-square&logo=github&logoColor=white&labelColor=16202b" alt="Repositories"></a>
<img src="https://komarev.com/ghpvc/?username=henrykanaskie&style=flat-square&color=1f6feb&label=sheet+views" alt="Profile views">

</div>

---

### `A1` &nbsp; GENERAL

I build things that sit at the boundary between models and hardware. A transformer written from first principles, an optimizer that picks real capacitor networks, a habit tracker that renders your streaks as a living neural graph. Most of my work starts as a question I couldn't answer by reading, so I write the thing that answers it.

- Currently deepest in **quantitative research**: block bootstrapping, log-return modeling, correlation structure
- Recently built a **GPT from scratch** to stop treating attention as a black box
- Happiest in a debugger, at the point where the theory stops matching the trace

---

### `B1` &nbsp; BILL OF MATERIALS

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/bom-dark.svg?v=20260824">
  <img src="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/bom-light.svg?v=20260824" alt="Bill of materials">
</picture>

<sub>Completion is dimensioned, not asserted. The red revision cloud marks whichever part was
last pushed to. Expand a row for the full description.</sub>

<table>
<tbody>
<tr>
<td align="center"><code>0x01</code></td>
<td align="center">✓</td>
<td><details><summary><b>Cap_Match_Net</b> — impedance matching solved as a constraint problem, in real component values</summary><br>
Capacitor matching networks solved with Google OR-Tools. Takes a target impedance and returns a network built from components that actually exist in a parts bin, rather than the ideal values a textbook would hand you.
<br><sub>OR-Tools CP-SAT · E12 series parts only</sub><br><br>
<a href="https://github.com/henrykanaskie/Cap_Match_Net">view the repository&nbsp;&rarr;</a>
</details></td>
</tr>
<tr>
<td align="center"><code>0x02</code></td>
<td align="center">✓</td>
<td><details><summary><b>small-shell</b> — a Unix shell in C: job control, redirection, and the awkward parts of signals</summary><br>
Job control, I/O redirection, and signal handling, including the parts that only start misbehaving once a process is backgrounded and something sends it a SIGTSTP at the wrong moment.
<br><sub>POSIX job control · SIGTSTP / SIGINT handled</sub><br><br>
<a href="https://github.com/henrykanaskie/small-shell">view the repository&nbsp;&rarr;</a>
</details></td>
</tr>
<tr>
<td align="center"><code>0x03</code></td>
<td align="center">▲</td>
<td><details><summary><b>animAgent</b> — Sprite Room: your agents as pixel-art characters, dropping from the notch</summary><br>
A macOS app that turns live Claude Code activity into a small pixel-art room of working characters — each agent a character, each tool call something it's visibly doing. Read-only by design: it never controls an agent and never shows prompt or response content.
<br><sub>M5 of M6 · 396 / 396 tests pass · art pipeline not integrated</sub><br><br>
<a href="https://github.com/henrykanaskie/animAgent">view the repository&nbsp;&rarr;</a>
</details></td>
</tr>
<tr>
<td align="center"><code>0x04</code></td>
<td align="center">▲</td>
<td><details><summary><b>ML_quantitative_research</b> — which correlations survive a block bootstrap, and which were only noise</summary><br>
Log-return modeling, Pearson correlation structure, Kalman filtering, and block-bootstrap resampling measured against a Gaussian baseline. The point is separating apparent signal from noise wearing a pattern. A correlation that doesn't survive a block bootstrap was never there.
<br><sub>block bootstrap · Gaussian baseline</sub><br><br>
<a href="https://github.com/henrykanaskie/ML_quantitative_research">view the repository&nbsp;&rarr;</a>
</details></td>
</tr>
<tr>
<td align="center"><code>0x05</code></td>
<td align="center">▲</td>
<td><details><summary><b>rLog</b> — speak into it, and structured LaTeX comes back out of a schema-bound LLM</summary><br>
Voice-driven logging. Audio goes in, gets transcribed, an LLM structures it against a fixed schema, and LaTeX comes out. CLI and web front ends over one shared store.
<br><sub>schema-bound output</sub><br><br>
<sub>code is local, the repository is still empty</sub>
</details></td>
</tr>
<tr>
<td align="center"><code>0x06</code></td>
<td align="center">▲</td>
<td><details><summary><b>gpt-scratch</b> — attention, embeddings and the neural foundations, written by hand</summary><br>
Attention, tokenization, and the training loop written by hand rather than pulled from a library. The foundations and attention primitives are done; the transformer block, the GPT itself, and the training loop are still to come.
<br><sub>no autograd library · foundations complete</sub><br><br>
<a href="https://github.com/henrykanaskie/gpt-scratch">view the repository&nbsp;&rarr;</a>
</details></td>
</tr>
<tr>
<td align="center"><code>0x07</code></td>
<td align="center">◗</td>
<td><details><summary><b>me-tutor</b> — agents writing a mechanical engineering curriculum, verified at build time</summary><br>
An agent pipeline that writes a mechanical-engineering curriculum and builds a static site around it. Every numerical claim has a matching assertion executed at build time, because generated physics is confidently wrong at a low but non-zero rate.
<br><sub>3 of ~14 modules · every number asserted</sub><br><br>
<sub>private repository</sub>
</details></td>
</tr>
<tr>
<td align="center"><code>0x08</code></td>
<td align="center">○</td>
<td><details><summary><b>GrowthApp</b> — a SwiftUI habit tracker that draws your streaks as a living neural graph</summary><br>
Each habit is a filament radiating from the center, each kept day a node, the day just kept glowing gold. Full WidgetKit suite over the same shared data.
<br><sub>WidgetKit suite · one orb variant real</sub><br><br>
<sub>private repository</sub>
</details></td>
</tr>
<tr>
<td align="center"><code>0x09</code></td>
<td align="center">○</td>
<td><details><summary><b>pitwall</b> — Formula 1 tire degradation, regressed over FastF1 stint telemetry</summary><br>
Built on FastF1, currently a tire-degradation regression over stint data. Aimed at the strategy question of when a set of tires stops paying for itself.
<br><sub>FastF1 stint data · frontend not populated</sub><br><br>
<sub>private repository</sub>
</details></td>
</tr>
</tbody>
</table>

---

### `C1` &nbsp; TELEMETRY

<sub>Rebuilt every morning. Orbital data from <a href="https://thespacedevs.com">thespacedevs</a>
and <a href="https://wheretheiss.at">wheretheiss.at</a>; push activity from the GitHub API. Any
channel that cannot be reached reads NO DATA rather than showing a stale figure.</sub>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/telemetry-dark.svg?v=20260824">
  <img src="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/telemetry-light.svg?v=20260824" alt="Daily telemetry">
</picture>

---

### `D1` &nbsp; MATERIALS AND ACTIVITY

<table>
<tr>
<td width="50%" valign="top">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/composition-dark.svg?v=20260824">
  <img src="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/composition-light.svg?v=20260824" alt="Language composition">
</picture>

</td>
<td width="50%" valign="top">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/activity-dark.svg?v=20260824">
  <img src="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/activity-light.svg?v=20260824" alt="Push activity">
</picture>

</td>
</tr>
</table>

<sub>Focus:</sub> `machine learning` · `transformers` · `quantitative research` · `time series` · `optimization` · `embedded C` · `signal processing` · `SwiftUI` · `agents` · `numerical methods`

---

### `E1` &nbsp; NOTES

1. All figures are read from the GitHub API at build time. Status and completion are hand-set in [`data/profile.toml`](data/profile.toml) and reviewed, not inferred.
2. The pixel-art agents are read-only on purpose. Watching is the whole feature.

---

### `F1` &nbsp; CONTRIBUTION GRAPH

<div align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/output/github-snake-dark.svg">
    <img src="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/output/github-snake.svg" alt="A snake eating the contribution graph">
  </picture>
</div>

---

<div align="center">
<sub>
REV D &nbsp;·&nbsp; SHEET 1 OF 1 &nbsp;·&nbsp; BUILT 2026-08-24 08:10 UTC &nbsp;·&nbsp; SCALE NONE<br>
Drawn from <a href="data/profile.toml"><code>data/profile.toml</code></a> by
<a href="scripts/build.py"><code>scripts/build.py</code></a>, rebuilt daily at 06:00 Pacific.<br>
Cards animate as they draw themselves in; they degrade to their finished state where
SMIL is unsupported.
</sub>
</div>
