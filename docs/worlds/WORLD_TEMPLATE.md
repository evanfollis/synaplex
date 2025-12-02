# WORLD\_TEMPLATE — Skeleton for a Synaplex World

> This document is a template for defining a Synaplex world.
> Replace domain-specific nouns, but keep the **Material Physics ($S, T, \Phi, K$)**.

-----

## 1\. Domain & Purpose

  * **World Name:** `YOUR_WORLD_NAME`
  * **Domain:** e.g., "Personal Knowledge," "High-Frequency Trading," "Fiction Writing."
  * **Primary Objective:** e.g., "Crystallize vague intuitions into specs," "Generate diverging plotlines."

-----

## 2\. Material Physics (The Constants)

Define how the generic Synaplex physics manifest in this specific world:

  * **$S$ (Substrate):** What makes up the sediment? (e.g., Code snippets, prose, financial tensors).
  * **$A$ (Basins):** What kinds of thoughts "stick" and form habits? (e.g., "Bullish Thesis," "Plot Hole").
  * **$K$ (Viscosity):** What makes a Mind "hard" vs "soft" here? (e.g., "Risk Aversion," "Skepticism").
  * **$P$ (Impact):** What external forces strike the substrate? (e.g., Market ticks, User prompts).
  * **$H$ (Holonomy):** What irreversible "scars" can we leave on reality? (e.g., Trades executed, Files committed).
  * **$T$ (Texture):** What does the output look like? (e.g., "Messy frottage of price action").
  * **$\Phi$ (Interference):** How do Lenses work? (e.g., "A Bearish lens looks at a Bullish texture").
  * **$\Xi$ (Erosion):** How quickly does old sediment decay?

-----

## 3\. Mind Types (DNA Templates)

List the primary geological roles. For each:

  * **Name:** e.g., `Synthesizer`, `Critic`, `Scout`.
  * **Substrate ($S$):** What history does it accumulate?
  * **Viscosity ($K$):** Is it Granite (stubborn) or Clay (impressionable)?
  * **Lenses ($L$):** What specific filters does it use to observe others?
  * **Impact ($P$):** What raw feeds does it consume?
  * **Holonomy ($H$):** What tools is it allowed to fire?
  * **Texture ($T$):** What does its frottage dump look like?

-----

## 4\. Loop Dynamics

Describe the specific flavor of the Unified Loop:

  * **Interference (Input):**
      * What **Textures** are flying around?
      * How strictly do **Lenses** filter noise?
  * **Reasoning (Churn):**
      * Does the Mind use personas to generate internal friction?
      * How does it reconcile contradictions?
  * **Resurfacing (Update):**
      * What triggers a "Hardening" of Viscosity?
      * What triggers a "Softening" (surprise)?

*Note: There are no "modes." Every agent runs the full loop.*

-----

## 5\. Holonomy & Execution

Define the interface with reality:

  * **Triggers:** What basin depth ($A_{sat}$) is required to fire a tool?
  * **Actions:** Deployments, PRs, API calls.
  * **Feedback:** How does the result strike back as a new Impact ($P$)?

-----

## 6\. Tectonics ($\Omega$) and Erosion ($\Xi$)

  * **Tectonics ($\Omega$):**
      * Who can move the graph edges?
      * Who can spawn new Minds?
  * **Erosion ($\Xi$):**
      * Does sediment rot if not referenced?
      * Do shallow basins fill with silt?

-----

## 7\. File Layout

Document where this world lives in the repo:

```text
synaplex/worlds/YOUR_WORLD_NAME/
  config.py           # Wiring & Physics constants
  dna_templates.py    # Role definitions
  lenses.py           # Optical filters
  agents.py           # Mind factories
  tools.py            # Sources of Impact/Holonomy
  bootstrap.py        # Big Bang script
docs/worlds/YOUR_WORLD_NAME.md
```

-----