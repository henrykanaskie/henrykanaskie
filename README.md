<h1 align="center">Henry Kanaskie</h1>

<p align="center">
  <em>Machine learning, quantitative research, and things that talk to hardware.</em>
</p>

<p align="center">
  <a href="https://henrykanaskie.com"><img src="https://img.shields.io/badge/Website-1f6feb?style=for-the-badge&logo=googlechrome&logoColor=white" alt="Website"></a>
  <a href="https://github.com/henrykanaskie?tab=repositories"><img src="https://img.shields.io/badge/Repositories-8957e5?style=for-the-badge&logo=github&logoColor=white" alt="Repositories"></a>
  <img src="https://komarev.com/ghpvc/?username=henrykanaskie&style=for-the-badge&color=3fb950&label=PROFILE+VIEWS" alt="Profile views">
</p>

---

### About

I build things that sit at the boundary between models and hardware — a transformer written
from first principles, an optimizer that picks real capacitor networks, a habit tracker that
renders your streaks as a living neural graph. Most of my work starts as a question I
couldn't answer by reading, so I write the thing that answers it.

- Currently deepest in **quantitative research** — block bootstrapping, log-return modeling, correlation structure
- Recently built a **GPT from scratch** to stop treating attention as a black box
- Happiest in a debugger, at the point where the theory stops matching the trace

---

<a href="https://github.com/henrykanaskie?tab=repositories"><picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/stats-dark.svg">
  <img src="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/stats-light.svg" alt="By the numbers">
</picture></a>

<table>
<tr>
<td width="50%">

<a href="https://github.com/henrykanaskie?tab=repositories"><picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/languages-dark.svg">
  <img src="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/languages-light.svg" alt="Languages">
</picture></a>

</td>
<td width="50%">

<a href="https://github.com/henrykanaskie?tab=repositories"><picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/focus-dark.svg">
  <img src="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/focus-light.svg" alt="Focus areas">
</picture></a>

</td>
</tr>
</table>

---

### What I'm building

<sub>Click any project to expand.</sub>

<details>
<summary><b>gpt-scratch</b> &nbsp;·&nbsp; <code>Python</code> &nbsp;·&nbsp; 🟢 shipped &nbsp;—&nbsp; a GPT with nothing imported</summary>

<br>

Attention, tokenization, and the training loop written by hand rather than pulled from a
library. Built to replace a vague sense of how transformers work with the ability to derive
one. Grew out of my NeetCode ML coursework, then kept going past where the course stopped.

**→ [github.com/henrykanaskie/gpt-scratch](https://github.com/henrykanaskie/gpt-scratch)**

</details>

<details>
<summary><b>ML_quantitative_research</b> &nbsp;·&nbsp; <code>Python</code> &nbsp;·&nbsp; 🔵 active &nbsp;—&nbsp; which signals survive a resample</summary>

<br>

Financial time-series research: log-return modeling, Pearson correlation structure, Kalman
filtering, and block-bootstrap resampling measured against a Gaussian baseline. The whole
point is separating apparent signal from noise wearing a pattern — a correlation that
doesn't survive a block bootstrap was never there.

**→ [github.com/henrykanaskie/ML_quantitative_research](https://github.com/henrykanaskie/ML_quantitative_research)**

</details>

<details>
<summary><b>Cap_Match_Net</b> &nbsp;·&nbsp; <code>Python</code> &nbsp;·&nbsp; 🟢 shipped &nbsp;—&nbsp; impedance matching as a constraint problem</summary>

<br>

Capacitor matching networks solved with Google OR-Tools. Takes a target impedance and
returns a network built from components that actually exist in a parts bin, rather than the
ideal values a textbook would hand you.

**→ [github.com/henrykanaskie/Cap_Match_Net](https://github.com/henrykanaskie/Cap_Match_Net)**

</details>

<details>
<summary><b>small-shell</b> &nbsp;·&nbsp; <code>C</code> &nbsp;·&nbsp; 🟢 shipped &nbsp;—&nbsp; a Unix shell, signals and all</summary>

<br>

Job control, I/O redirection, and signal handling — including the parts that only start
misbehaving once a process is backgrounded and something sends it a SIGTSTP at the wrong
moment.

**→ [github.com/henrykanaskie/small-shell](https://github.com/henrykanaskie/small-shell)**

</details>

<details>
<summary><b>rLog</b> &nbsp;·&nbsp; <code>Python</code> &nbsp;·&nbsp; 🔵 active &nbsp;—&nbsp; talk at it, get LaTeX back</summary>

<br>

Voice-driven logging. Audio goes in, gets transcribed, an LLM structures it against a fixed
schema, and LaTeX comes out. CLI and web front ends over one shared store.

**→ [github.com/henrykanaskie/rLog](https://github.com/henrykanaskie/rLog)**

</details>

<details>
<summary><b>pitwall</b> &nbsp;·&nbsp; <code>Python</code> &nbsp;·&nbsp; 🟠 in progress &nbsp;·&nbsp; <i>private</i></summary>

<br>

Formula 1 telemetry built on FastF1 — currently a tire-degradation regression over stint
data, split backend/frontend. Aimed at the strategy question of when a set of tires stops
paying for itself.

</details>

<details>
<summary><b>me-tutor</b> &nbsp;·&nbsp; <code>Python</code> / <code>Astro</code> &nbsp;·&nbsp; 🔵 active &nbsp;·&nbsp; <i>private</i></summary>

<br>

An agent pipeline that writes a mechanical-engineering curriculum and builds a static site
around it. Every numerical claim in every lesson has a matching assertion executed at build
time — generated physics is confidently wrong at a low but non-zero rate, and unverified
output you study from for seven weeks is worse than no output at all.

</details>

<details>
<summary><b>GrowthApp</b> &nbsp;·&nbsp; <code>Swift</code> &nbsp;·&nbsp; 🟣 scaffold &nbsp;·&nbsp; <i>private</i></summary>

<br>

A SwiftUI habit tracker whose home screen is a living record: each habit a filament
radiating from the center, each kept day a node, the day just kept glowing gold. Full
WidgetKit suite over the same shared data.

</details>

---

<a href="https://github.com/henrykanaskie?tab=repositories"><picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/projects-dark.svg">
  <img src="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/projects-light.svg" alt="Project stage">
</picture></a>

---

### Contributions

<a href="https://github.com/henrykanaskie?tab=overview"><picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/activity-dark.svg">
  <img src="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/activity-light.svg" alt="Recent activity">
</picture></a>

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/output/github-snake-dark.svg">
    <img src="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/output/github-snake.svg" alt="Contribution graph being eaten by a snake">
  </picture>
</p>

---

<p align="center">
  <sub>
    Cards in <code>assets/</code> are built by <a href="./scripts/gen_cards.py"><code>scripts/gen_cards.py</code></a> and regenerated daily, so nothing here depends on a third-party renderer.<br>
    Cards animate on load (SMIL) and degrade to their final state where animation is unsupported. The snake is rebuilt daily by <a href="https://github.com/Platane/snk">Platane/snk</a>.
  </sub>
</p>
