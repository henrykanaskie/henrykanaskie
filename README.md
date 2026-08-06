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

I build things that sit at the boundary between models and hardware. A transformer written
from first principles, an optimizer that picks real capacitor networks, a habit tracker that
renders your streaks as a living neural graph. Most of my work starts as a question I
couldn't answer by reading, so I write the thing that answers it.

- Currently deepest in **quantitative research**: block bootstrapping, log-return modeling, correlation structure
- Recently built a **GPT from scratch** to stop treating attention as a black box
- Happiest in a debugger, at the point where the theory stops matching the trace

---

### What I'm building

<sub>Click a description to expand it.</sub>

<table>
<tr>
<td width="26" align="center">🟢</td>
<td width="210"><b>Cap_Match_Net</b></td>
<td width="96"><img src="https://img.shields.io/badge/Python-1f2328?style=flat-square&logo=python&logoColor=white" alt="Python"></td>
<td width="118"><img src="https://img.shields.io/badge/shipped-3fb950?style=flat-square&labelColor=3fb950&color=3fb950" alt="shipped"></td>
<td><details><summary><sub>impedance matching as a constraint problem</sub></summary><sub>Capacitor matching networks solved with Google OR-Tools. Takes a target impedance and returns a network built from components that actually exist in a parts bin, rather than the ideal values a textbook would hand you. <a href="https://github.com/henrykanaskie/Cap_Match_Net">View the repository &rarr;</a></sub></details></td>
</tr>
<tr>
<td width="26" align="center">🟢</td>
<td width="210"><b>small-shell</b></td>
<td width="96"><img src="https://img.shields.io/badge/C-1f2328?style=flat-square&logo=c&logoColor=white" alt="C"></td>
<td width="118"><img src="https://img.shields.io/badge/shipped-3fb950?style=flat-square&labelColor=3fb950&color=3fb950" alt="shipped"></td>
<td><details><summary><sub>a Unix shell, signals and all</sub></summary><sub>Job control, I/O redirection, and signal handling, including the parts that only start misbehaving once a process is backgrounded and something sends it a SIGTSTP at the wrong moment. <a href="https://github.com/henrykanaskie/small-shell">View the repository &rarr;</a></sub></details></td>
</tr>
<tr>
<td width="26" align="center">🔵</td>
<td width="210"><b>ML_quantitative_research</b></td>
<td width="96"><img src="https://img.shields.io/badge/Python-1f2328?style=flat-square&logo=python&logoColor=white" alt="Python"></td>
<td width="118"><img src="https://img.shields.io/badge/active-58a6ff?style=flat-square&labelColor=58a6ff&color=58a6ff" alt="active"></td>
<td><details><summary><sub>which signals survive a resample</sub></summary><sub>Log-return modeling, Pearson correlation structure, Kalman filtering, and block-bootstrap resampling measured against a Gaussian baseline. The point is separating apparent signal from noise wearing a pattern. A correlation that doesn't survive a block bootstrap was never there. <a href="https://github.com/henrykanaskie/ML_quantitative_research">View the repository &rarr;</a></sub></details></td>
</tr>
<tr>
<td width="26" align="center">🔵</td>
<td width="210"><b>rLog</b></td>
<td width="96"><img src="https://img.shields.io/badge/Python-1f2328?style=flat-square&logo=python&logoColor=white" alt="Python"></td>
<td width="118"><img src="https://img.shields.io/badge/active-58a6ff?style=flat-square&labelColor=58a6ff&color=58a6ff" alt="active"></td>
<td><details><summary><sub>talk at it, get LaTeX back</sub></summary><sub>Voice-driven logging. Audio goes in, gets transcribed, an LLM structures it against a fixed schema, and LaTeX comes out. CLI and web front ends over one shared store. The code is local; the repository is still empty.</sub></details></td>
</tr>
<tr>
<td width="26" align="center">🔵</td>
<td width="210"><b>gpt-scratch</b></td>
<td width="96"><img src="https://img.shields.io/badge/Python-1f2328?style=flat-square&logo=python&logoColor=white" alt="Python"></td>
<td width="118"><img src="https://img.shields.io/badge/active-58a6ff?style=flat-square&labelColor=58a6ff&color=58a6ff" alt="active"></td>
<td><details><summary><sub>a GPT with nothing imported</sub></summary><sub>Attention, tokenization, and the training loop written by hand rather than pulled from a library. The foundations and attention primitives are done; the transformer block, the GPT itself, and the training loop are still to come. <a href="https://github.com/henrykanaskie/gpt-scratch">View the repository &rarr;</a></sub></details></td>
</tr>
<tr>
<td width="26" align="center">🟠</td>
<td width="210"><b>me-tutor</b></td>
<td width="96"><img src="https://img.shields.io/badge/Python-1f2328?style=flat-square&logo=python&logoColor=white" alt="Python"></td>
<td width="118"><img src="https://img.shields.io/badge/in%20progress-d29922?style=flat-square&labelColor=d29922&color=d29922" alt="in progress"></td>
<td><details><summary><sub>agents writing a verified curriculum</sub></summary><sub>An agent pipeline that writes a mechanical-engineering curriculum and builds a static site around it. Every numerical claim has a matching assertion executed at build time, because generated physics is confidently wrong at a low but non-zero rate. Private. Three of roughly fourteen modules so far.</sub></details></td>
</tr>
<tr>
<td width="26" align="center">🟣</td>
<td width="210"><b>GrowthApp</b></td>
<td width="96"><img src="https://img.shields.io/badge/Swift-1f2328?style=flat-square&logo=swift&logoColor=white" alt="Swift"></td>
<td width="118"><img src="https://img.shields.io/badge/scaffold-bc8cff?style=flat-square&labelColor=bc8cff&color=bc8cff" alt="scaffold"></td>
<td><details><summary><sub>a habit tracker drawn as a neural graph</sub></summary><sub>Each habit is a filament radiating from the center, each kept day a node, the day just kept glowing gold. Full WidgetKit suite over the same shared data. Private repository.</sub></details></td>
</tr>
<tr>
<td width="26" align="center">🟣</td>
<td width="210"><b>pitwall</b></td>
<td width="96"><img src="https://img.shields.io/badge/Python-1f2328?style=flat-square&logo=python&logoColor=white" alt="Python"></td>
<td width="118"><img src="https://img.shields.io/badge/scaffold-bc8cff?style=flat-square&labelColor=bc8cff&color=bc8cff" alt="scaffold"></td>
<td><details><summary><sub>Formula 1 strategy and telemetry</sub></summary><sub>Built on FastF1, currently a tire-degradation regression over stint data. Aimed at the strategy question of when a set of tires stops paying for itself. Private repository.</sub></details></td>
</tr>
</table>

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
