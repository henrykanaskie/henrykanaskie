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

**[gpt-scratch](https://github.com/henrykanaskie/gpt-scratch)** · `Python` · shipped
A GPT assembled from first principles — attention, tokenization, and the training loop
written by hand rather than imported. Built to replace a vague sense of how transformers
work with the ability to derive one.

**[ML_quantitative_research](https://github.com/henrykanaskie/ML_quantitative_research)** · `Python` · active
Financial time-series research: log-return modeling, Pearson correlation structure, Kalman
filtering, and block-bootstrap resampling measured against a Gaussian baseline. The point is
knowing which apparent signal survives a resample and which was noise wearing a pattern.

**[Cap_Match_Net](https://github.com/henrykanaskie/Cap_Match_Net)** · `Python` · shipped
Capacitor matching networks solved as a constraint problem with Google OR-Tools. Takes a
target impedance and returns a network of components that actually exist in a parts bin.

**[small-shell](https://github.com/henrykanaskie/small-shell)** · `C` · shipped
A working Unix shell — job control, I/O redirection, and signal handling, including the
parts that only misbehave once a process is backgrounded.

**[rLog](https://github.com/henrykanaskie/rLog)** · `Python` · active
Voice-driven logging. Audio goes in, gets transcribed, an LLM structures it against a
schema, and LaTeX comes out. CLI and web front ends over the same store.

**pitwall** · `Python` · in progress · *private*
Formula 1 telemetry built on FastF1, currently a tire-degradation regression over stint
data. Split backend/frontend, aimed at the strategy question of when a set of tires stops
paying for itself.

**me-tutor** · `Python` / `Astro` · active · *private*
An agent pipeline that writes a mechanical-engineering curriculum and builds a static site
around it. Every numerical claim in every lesson has a matching assertion executed at build
time — generated physics is confidently wrong often enough that unverified output is worse
than none.

**GrowthApp** · `Swift` · scaffold · *private*
A SwiftUI habit tracker whose home screen is a living record: each habit a filament from the
center, each kept day a node. Full WidgetKit suite over shared data.

---

<a href="https://github.com/henrykanaskie?tab=repositories"><picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/projects-dark.svg">
  <img src="https://raw.githubusercontent.com/henrykanaskie/henrykanaskie/main/assets/projects-light.svg" alt="Project stage">
</picture></a>

---

### Contributions

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
    The contribution snake is rebuilt daily by <a href="https://github.com/Platane/snk">Platane/snk</a>.
  </sub>
</p>
