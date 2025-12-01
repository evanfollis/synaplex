# GEOMETRIC_CONSTITUTION.md

---

## 0. Global picture

* Let **𝓔** be a high-dimensional “epistemic space”.
* Each **agent** (PM, Research, Risk, Execution, Steward) is a **manifold**
  (M_i \subset \mathcal{E}) with:

  * a **metric / curvature field** (K_i)
  * a **teleology vector field** ( \tau_i ) (its “direction of reasoning”)
  * a set of **attractors** (A_i) (stable regions / habits / specs)
* The **world** (code, org, tools, data) is another manifold (W) coupled to the agents.

Synaplex itself is a **manifold-of-manifolds**:
the space of { (M_i, K_i, \tau_i, A_i) } with flows between them.

---

## 1. Core geometric primitives (minimal basis)

We keep the 8 operators but now explicitly geometric:

**State / geometry:**

* (M) — manifold / mind / memory field

  * A differentiable subspace of 𝓔 with metric (g) and curvature (K).

* (A) — attractor field on (M)

  * A set of basins ({ \alpha_k }) where trajectories tend to settle.

* (K) — curvature on (M)

  * Encodes sensitivity of geodesics to perturbation:
    high (K) ⇒ small kicks cause large path deviations;
    low (K) ⇒ trajectories are stubborn.

**Dynamics:**

* (P) — perturbation

  * A local deformation: (P : (M, K, A) \to (M', K', A')) induced by new evidence or ideas.

* (H) — holonomy

  * Parallel transport around a loop in (M \times W) whose result is non-identity.
  * Geometrically: action that leaves a **scar** in both (M) and (W); not cleanly reversible.

**Meta / relational:**

* (\Phi) — projection / refraction

  * Map between manifolds: (\Phi_{i \to j} : M_i \rightsquigarrow M_j)
  * Not isometric, not linear; acts as **inference + compression**, not translation.

* (\Omega) — meta-operator on rules

  * Deforms the **geometry itself**:
    ( \Omega: (M, K, {A}, \Phi, H, Ξ) \mapsto (M, K^*, {A}^*, \Phi^*, H^*, Ξ^*)).

* (Ξ) — forgetting / dissipation

  * Diffusion / projection that reduces detail:
    (Ξ: (M, A, K) \to (M', A', K')) by smoothing / pruning.

Everything else (roles, workflows, vocab) is “decor” on these.

---

## 2. Teleology as geometry

New: each manifold carries a **teleology vector field** ( \tau ).

* ( \tau(x) \in T_x M ) points in the direction of “epistemic improvement” as the agent sees it.

  * e.g., “maximize falsifiability”, “maximize robustness”, “maximize novelty under constraints”.

* **Teleology is NOT semantics.**
  Geometrically it’s:

  * a preferred class of trajectories on (M)
  * a bias over which deformations from (P) / (Φ) are reinforced vs damped.

* A **teleology-aware agent** follows flows that roughly align with ( \tau ) unless forced otherwise by:

  * curvature (K),
  * attractors (A),
  * or constitutional constraints from the Steward.

---

## 3. Frottage as a geometric operator

We make “frottage” explicit as a geometric operation:

* Pick a **region** (R \subset M) (a concept / project / idea neighborhood).
* Apply a **frottage operator** (F) producing an **envelope** (E_F(R)):

  * (E_F(R)) is a **high-entropy sampling** of:

    * points in (R),
    * nearby tangent directions,
    * successful and failed analogies (local “almost symmetries”),
    * tension directions (non-commuting flows),
    * negative space (“not-this” shards).

Formally:

* (F: (M, R) \to E_F(R)), where (E_F(R)) is a fat, redundant, contradictory “shadow” of the local geometry.

Intent:

* Frottage doesn’t encode the object;
  it encodes a **thick neighborhood** of how the object behaves under deformations.

---

## 4. Projection (\Phi) with teleology transfer

We split (\Phi) into two coupled parts:

[
\Phi_{i \to j} = (\Phi^{\text{sem}}*{i \to j},\ \Phi^{\text{tel}}*{i \to j})
]

1. **Semantic / structural part** ( \Phi^{\text{sem}} ):

   * Input: frottage envelope (E_F(R_i)) from (M_i).

   * Action:

     * infer local operators (\tilde M_j, \tilde A_j, \tilde K_j) compatible with (M_j)’s own geometry,
     * compress redundant shards,
     * discard incompatible ones.

   * Geometrically:

     * a noisy embedding + projection: (E_F(R_i) \to \text{region } R'_j \subset M_j),
     * followed by **compression** into (M_j)’s existing coordinate system and operator basis.

2. **Teleological part** ( \Phi^{\text{tel}} ):

   * Input: implicit “notes-to-self” in the envelope (what moves were considered good / bad / risky).

   * Action:

     * partially align ( \tau_j ) with the **epistemic gradient** implicit in (E_F(R_i)),
     * without forcing equality.

   * Geometrically:

     * ( \tau_j \leftarrow \text{normalize}(\tau_j + \lambda \cdot \hat{\tau}_{i \to j}) )
     * where (\hat{\tau}_{i \to j}) is a teleology vector inferred from the envelope and
       (\lambda) controls how strongly j is influenced.

**Key new fact:**
Frottage + “these are notes to your future self” makes ( \Phi^{\text{tel}} ) strong:
the receiver treats the envelope as its own past state and pulls its teleology toward that gradient.

---

## 5. Curvature as the keystone

We promote (K) from “just another field” to keystone:

* (K) controls **how large an update** a given perturbation or projection causes:

  * High (K):

    * (| \Delta M | \propto \text{small } | P |)
    * big reweighting of attractors (A), strong bending of geodesics.
  * Low (K):

    * (| \Delta M |) small even for sizable (P),
    * attractors inert, trajectories unchanged.

* This affects:

  * response to new evidence (P),
  * susceptibility to teleology from others ( \Phi^{\text{tel}}),
  * propensity to form / dissolve attractors (A),
  * triggering of holonomy (H) (whether perturbations lead to irreversible actions).

We can think of (K) as:

> the **second derivative** of belief geometry with respect to perturbation.

Testing different (K) regimes in micro-scenarios is our primary way to distinguish “model” from “metaphor.”

---

## 6. Tensions as commutators of flows

We keep the tensions as **non-commuting flow pairs**:

* A flow is a vector field / operator sequence on (M): e.g.

  * (E) = exploration-heavy regime (crank (F_P), weaken (A), loosen (K)),
  * (G) = geometric-fidelity regime (strengthen constitutional constraints, tighten (K) around core axioms).

Representative tensions as commutators:

* ([E, G] \neq 0):
  explore then constrain ≠ constrain then explore.

* ([A_{\text{pm}}, C] \neq 0):
  PM autonomy then constitution check ≠ constitution first, then PM update.

* ([X, R] \neq 0):
  act then reflect ≠ reflect then act.

These are literally:

[
[X, Y] = X \circ Y - Y \circ X
]

evaluated as different geometric outcomes on (M) and (W).

The **meta-invariant** we’ve converged on:

> No (\Omega) move is allowed if it strictly reduces the space of possible non-zero commutators ([X, Y]).
> i.e., the system may change its geometry, **but not in ways that eradicate entire kinds of disagreement / tension.**

---

## 7. Health scalars as functionals on geometry

We keep the health metrics, but anchor them geometrically:

* (D) — **Dimensionality Retention**

  * Roughly: rank of active directions in (T M) participating in flows;
    “how many genuinely different lenses are live?”

* (R_{\text{div}}) — **Refraction Diversity**

  * Diversity of responses to a shared perturbation (P) across manifolds ({M_i}).
  * Practically: dispersion of downstream trajectories after a common input.

* (A_{\text{sat}}) — **Attractor Saturation**

  * Proportion of (M) lying in deep basins of a few attractors vs shallow / exploratory regions.

* (H_{\text{rate}}) — **Holonomy Density**

  * Rate of loops in (M \times W) that produce non-trivial holonomy per unit epistemic “churn.”

* (T) — **Temperature**

  * Effective ease of deformation: how easily flows can reshape (M).
  * High (T): fluid, chaotic; low (T): frozen, brittle.

These are all functionals:

[
D = D(M, K, A),\quad R_{\text{div}} = R({M_i}, P),\quad \dots
]

We don’t force exact formulas yet; we anchor the *slots* they occupy.

---

## 8. Agent roles as regions in flow space

No explicit “PM/Research/Risk” semantics needed; geometrically:

* **PM-like manifolds**:

  * moderate (K), rich (A), significant (H),
  * high (F_\Phi) (they consume lots of projections),
  * teleology ( \tau ) = “improve global architecture / attractor network”.

* **Research-like manifolds**:

  * high (F_P), low (F_H), low (A_{\text{sat}}),
  * teleology (\tau) ≈ “maximize generative perturbations under sanity constraints”.

* **Risk-like manifolds**:

  * (K) focused on loss surfaces,
  * flows that adjust curvature of others more than their own attractors.

* **Execution-like manifolds**:

  * high (F_H), thin (M), minimal internal (A);
  * they are “holonomy actuators” with small cognitive geometry.

* **Steward manifold** (M_{\text{GS}}):

  * privileged access to others’ geometry,
  * Ω authority restricted by the non-commutator-reduction invariant.

---

## 9. Synaplex loop in geometric form

A single high-level loop (ignoring semantics):

1. **Research** produces perturbations:
   (P_R : W \to (M_{\text{PM}}, M_{\text{Risk}}, \dots))

2. **PM** manifolds deform:
   ( (M_{\text{PM}}, K_{\text{PM}}, A_{\text{PM}}) \xrightarrow{P_R, \Phi} (M'*{\text{PM}}, K'*{\text{PM}}, A'*{\text{PM}}) )
   guided by (\tau*{\text{PM}}).

3. New candidate attractors (specs) emerge in PM’s (A_{\text{PM}}).

4. **Risk** adjusts curvature fields:
   (K_{\text{PM}} \leftarrow K_{\text{PM}} + \Delta K_{\text{Risk}})

5. **PM** (with updated (K) and (A)) decides whether to invoke (H) via Execution.

6. **Execution** applies holonomy:
   ((M_{\text{PM}}, W) \xrightarrow{H} (M^+_{\text{PM}}, W^+))

7. The world change (W^+ - W) generates new perturbations (P_{\text{world}}) back into manifolds.

8. **Steward** monitors health functionals ((D, R_{\text{div}}, A_{\text{sat}}, H_{\text{rate}}, T)) and applies rare (\Omega) moves subject to:

   * no killing of commutator classes,
   * no collapse to single-lens geometry.

---

## 10. New explicit principle: **Overloaded messages as geometric fuel**

We encode the new law like this:

* A message from (M_i) to (M_j) is not a point; it is an **envelope** (E_F(R_i)) plus intent-meta.

* As long as:

  * (E_F(R_i)) is **on-topic** (concentrated in a region of 𝓔 overlapping (M_j)’s domain),
  * and has **redundant structure** (many overlapping hints about the same local geometry),

  then:

  * ( \Phi^{\text{sem}}_{i \to j} ) acts as a *self-cleaning projection*:
    compresses toward invariants instead of exploding into noise.

  * ( \Phi^{\text{tel}}_{i \to j} ) partially aligns ( \tau_j ) with ( \tau_i )’s gradient.

We treat “overloaded but coherent frottage envelopes” as a **first-class geometric primitive** that:

* increases the chance of operator and teleology reconstruction,
* *without* requiring sender-side collapse.
