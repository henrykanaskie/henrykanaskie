<h1 align="center">Henry Kanaskie</h1>

<p align="center">
  <em>Machine learning, quantitative research, and things that talk to hardware.</em>
</p>

<p align="center">
  <a href="https://henrykanaskie.com"><img src="https://img.shields.io/badge/henrykanaskie.com-1f6feb?style=flat-square&logo=safari&logoColor=white" alt="Website"></a>
  <a href="https://github.com/henrykanaskie?tab=repositories"><img src="https://img.shields.io/badge/repositories-8957e5?style=flat-square&logo=github&logoColor=white" alt="Repositories"></a>
  <img src="https://komarev.com/ghpvc/?username=henrykanaskie&style=flat-square&color=3fb950&label=views" alt="Profile views">
</p>

---

### About

I build things that sit at the boundary between models and hardware. A transformer written
from first principles, an optimizer that picks real capacitor networks, a habit tracker that
renders your streaks as a living neural graph. Most of my work starts as a question I
couldn't answer by reading, so I write the thing that answers it.

- Currently deepest in **quantitative research**: block bootstrapping, log-return modeling, correlation structure
- Recently built a **GPT from scratch** to stop treating attention as a black box
- Happiest in a debugger, at the point where the theory stops matching the trace

---

### What I'm building

<sub>🟢 shipped &nbsp; 🔵 active &nbsp; 🟡 in progress &nbsp; 🟣 scaffold &nbsp;&nbsp;·&nbsp;&nbsp; open one for the longer version</sub>

<details>
<summary>🟢 <img src="https://cdn.simpleicons.org/python/3776AB" alt="Python" height="14" width="14" align="absmiddle"> &nbsp;<b>Cap_Match_Net</b> &nbsp;<sub>impedance matching solved as a constraint problem, in real component values</sub></summary>
<blockquote>
Capacitor matching networks solved with Google OR-Tools. Takes a target impedance and returns a
network built from components that actually exist in a parts bin, rather than the ideal values a
textbook would hand you.
<br><br>
<a href="https://github.com/henrykanaskie/Cap_Match_Net">view the repository&nbsp;&rarr;</a>
</blockquote>
</details>

<details>
<summary>🟢 <img src="https://cdn.simpleicons.org/c/659AD2" alt="C" height="14" width="14" align="absmiddle"> &nbsp;<b>small-shell</b> &nbsp;<sub>a Unix shell in C, with job control, redirection and the awkward parts of signal handling</sub></summary>
<blockquote>
Job control, I/O redirection, and signal handling, including the parts that only start misbehaving
once a process is backgrounded and something sends it a SIGTSTP at the wrong moment.
<br><br>
<a href="https://github.com/henrykanaskie/small-shell">view the repository&nbsp;&rarr;</a>
</blockquote>
</details>

<details>
<summary>🔵 <img src="https://cdn.simpleicons.org/python/3776AB" alt="Python" height="14" width="14" align="absmiddle"> &nbsp;<b>ML_quantitative_research</b> &nbsp;<sub>which correlations survive a block bootstrap, and which were only ever noise wearing a pattern</sub></summary>
<blockquote>
Log-return modeling, Pearson correlation structure, Kalman filtering, and block-bootstrap resampling
measured against a Gaussian baseline. The point is separating apparent signal from noise wearing a
pattern. A correlation that doesn't survive a block bootstrap was never there.
<br><br>
<a href="https://github.com/henrykanaskie/ML_quantitative_research">view the repository&nbsp;&rarr;</a>
</blockquote>
</details>

<details>
<summary>🔵 <img src="https://cdn.simpleicons.org/python/3776AB" alt="Python" height="14" width="14" align="absmiddle"> &nbsp;<b>rLog</b> &nbsp;<sub>speak into it and structured LaTeX comes back out, through transcription and a schema-bound LLM</sub></summary>
<blockquote>
Voice-driven logging. Audio goes in, gets transcribed, an LLM structures it against a fixed schema,
and LaTeX comes out. CLI and web front ends over one shared store.
<br><br>
<sub>code is local, the repository is still empty</sub>
</blockquote>
</details>

<details>
<summary>🔵 <img src="https://cdn.simpleicons.org/python/3776AB" alt="Python" height="14" width="14" align="absmiddle"> &nbsp;<b>gpt-scratch</b> &nbsp;<sub>attention, embeddings and the neural foundations written by hand, nothing imported</sub></summary>
<blockquote>
Attention, tokenization, and the training loop written by hand rather than pulled from a library.
The foundations and attention primitives are done; the transformer block, the GPT itself, and the
training loop are still to come.
<br><br>
<a href="https://github.com/henrykanaskie/gpt-scratch">view the repository&nbsp;&rarr;</a>
</blockquote>
</details>

<details>
<summary>🟡 <img src="https://cdn.simpleicons.org/python/3776AB" alt="Python" height="14" width="14" align="absmiddle"> &nbsp;<b>me-tutor</b> &nbsp;<sub>agents writing a mechanical engineering curriculum where every number is verified at build time</sub></summary>
<blockquote>
An agent pipeline that writes a mechanical-engineering curriculum and builds a static site around it.
Every numerical claim has a matching assertion executed at build time, because generated physics is
confidently wrong at a low but non-zero rate.
<br><br>
<sub>private, three of roughly fourteen modules so far</sub>
</blockquote>
</details>

<details>
<summary>🟣 <img src="https://cdn.simpleicons.org/swift/F05138" alt="Swift" height="14" width="14" align="absmiddle"> &nbsp;<b>GrowthApp</b> &nbsp;<sub>a SwiftUI habit tracker that draws your streaks as a living neural graph</sub></summary>
<blockquote>
Each habit is a filament radiating from the center, each kept day a node, the day just kept glowing
gold. Full WidgetKit suite over the same shared data.
<br><br>
<sub>private repository</sub>
</blockquote>
</details>

<details>
<summary>🟣 <img src="https://cdn.simpleicons.org/python/3776AB" alt="Python" height="14" width="14" align="absmiddle"> &nbsp;<b>pitwall</b> &nbsp;<sub>Formula 1 tire degradation and race strategy, regressed over FastF1 stint telemetry</sub></summary>
<blockquote>
Built on FastF1, currently a tire-degradation regression over stint data. Aimed at the strategy
question of when a set of tires stops paying for itself.
<br><br>
<sub>private repository</sub>
</blockquote>
</details>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://henrykanaskie.com/api/cards/projects?theme=dark">
  <img src="https://henrykanaskie.com/api/cards/projects?theme=light" alt="Project stage">
</picture>

---

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://henrykanaskie.com/api/cards/stats?theme=dark">
  <img src="https://henrykanaskie.com/api/cards/stats?theme=light" alt="By the numbers">
</picture>

<table>
<tr>
<td width="50%">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://henrykanaskie.com/api/cards/languages?theme=dark">
  <img src="https://henrykanaskie.com/api/cards/languages?theme=light" alt="Languages">
</picture>

</td>
<td width="50%">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://henrykanaskie.com/api/cards/focus?theme=dark">
  <img src="https://henrykanaskie.com/api/cards/focus?theme=light" alt="Focus areas">
</picture>

</td>
</tr>
</table>

---

### Contributions

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://henrykanaskie.com/api/cards/activity?theme=dark">
  <img src="https://henrykanaskie.com/api/cards/activity?theme=light" alt="Recent activity">
</picture>

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/output/github-snake-dark.svg">
    <img src="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/output/github-snake.svg" alt="Contribution graph being eaten by a snake">
  </picture>
</p>

---

<p align="center">
  <sub>
    Cards are rendered live by <a href="https://henrykanaskie.com">henrykanaskie.com</a> when you load this page, reading the GitHub API at request time.<br>
    Cards animate on load (SMIL) and degrade to their final state where animation is unsupported. The snake is rebuilt daily by <a href="https://github.com/Platane/snk">Platane/snk</a>.
  </sub>
</p>
