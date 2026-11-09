# Qinetic Research Lab — Application Drafts

> Status: **DRAFT — paused 2026-06-17.** Picking this up later.
> Lab: research collective at the intersection of quantum physics + ML.
> Focus: physics-informed neural networks (PINNs) applied to quantum systems.
> Signals it's a student/volunteer collective (Discord contact, age/education
> asked, 0–5 hr/week option) → they recruit for **curiosity + ability to
> self-teach**, not an established publication record. Win with honest
> enthusiasm + evidence you ship working code on unfamiliar topics.

## Fixed form fields (already known)
- Email / Contact: cdw8481@nyu.edu
- Name: David White Wolf
- Age & year of education: 37, 2nd year
- Resume: David White Wolf Resume.pdf
- Hours/week: (decide — 5–10 is a safe, credible commit)

---

## GROUND RULE
Background/Skills answers must be **true** — swap bracketed bits for real
coursework/history before submitting. The PINN answer must be in David's own
words so it survives a follow-up question.

---

## Q1 — Research Background (MAX 75 words)  [≈68 words]

I'm a returning student at NYU (2nd year) and a career-changer with a
hands-on engineering background. My self-directed work centers on building
diagnostic and data-analysis tools in Python — including a fleet-operations
toolkit that applies robust statistics to sensor telemetry. I have no formal
publications yet; my research has been independent and project-based. I'm now
seeking structured experience in computational physics and machine learning.

> TODO: insert real major + any math/physics/ML courses taken.

---

## Q2 — Skills/qualities that set you apart + how you'll apply them (MAX 250)  [≈235 words]

Three things set me apart: I build tools from scratch, I debug methodically,
and I teach myself hard material under my own steam.

Most of my technical work is independent and project-based. I recently built
a complete fleet-operations toolkit in Python — including an anomaly detector
that uses the modified z-score (median/MAD) instead of a naive one, because a
naive z-score gets dragged down by the very outlier it's meant to catch. That
instinct — questioning the obvious method and reaching for the more robust
one — is exactly what PINN work demands, where balancing physics and data
loss terms is rarely as simple as it first looks.

I'm also relentless about root cause. I don't patch symptoms; I instrument,
measure, and find the underlying reason something fails. PINN training is
notoriously finicky — spectral bias, stiff gradients, loss imbalance — and
that's a debugging problem before it's a physics problem.

Finally, I'm 37 and back in school by choice. Everything in my portfolio is
self-taught. I'm not arriving as an expert in quantum systems; I'm arriving
as someone who has proven, repeatedly, that he can go from zero to a working
artifact on an unfamiliar topic.

At Qinetic I'd apply that to the unglamorous core of the work: writing clean
simulation code, building the tooling that makes experiments reproducible,
and chasing down why a model isn't converging.

---

## Q3 — A challenge in this field that PINNs could overcome (MAX 200)  [≈190 words]
> REQUIRED. This is the real test — the "go research quantum computing" line
> is them checking whether you actually read up. Rewrite in your own words.

A central challenge in quantum simulation is the curse of dimensionality in
the many-body Schrödinger equation. The wavefunction lives in a space that
grows exponentially with particle count, so traditional grid- or mesh-based
solvers (finite-difference, exact diagonalization) become intractable for
even modest systems. Because PINNs are mesh-free — they represent the
solution as a continuous function parametrized by network weights rather than
values on a grid — they can, in principle, approximate high-dimensional
wavefunctions without exponential memory cost. They also naturally handle
inverse problems: inferring an unknown potential or Hamiltonian from sparse,
expensive measurements by treating it as a trainable parameter. The open
difficulty is that PINNs struggle with the high-frequency, oscillatory
solutions quantum systems produce (spectral bias) — making training PINNs
reliably on quantum problems a live research question, which is precisely
where a lab like Qinetic adds value.

---

## Q4 — "Any questions?"

1. What does onboarding look like for someone strong on building/coding but
   newer to quantum-physics theory — is there a ramp-up path, or is
   graduate-level PDE/quantum mechanics assumed from day one?
2. What's the stack — JAX, PyTorch, DeepXDE, or NVIDIA Modulus for the PINN work?
3. What does a "research phase" look like end-to-end, and what would a first
   contribution from a new researcher typically be?

---

## Background knowledge — PINNs (so the answers are genuinely yours)

- **What a PINN is:** a neural net that solves a differential equation by
  putting the physics into the loss function. Penalized for violating the
  governing equation (PDE residual) + boundary/initial conditions, using
  automatic differentiation for the derivatives. Solves physics problems with
  little/no labeled data, and is mesh-free. (Raissi, Perdikaris, Karniadakis,
  2019.)
- **Loss =** data loss + physics-residual loss + boundary/initial-condition loss.
- **Quantum link:** Schrödinger equation is a PDE; many-body version is
  exponentially hard (curse of dimensionality). Related idea: neural-network
  quantum states (Carleo & Troyer, 2017).
- **Known PINN weaknesses:** spectral bias (high-frequency solutions),
  stiff/multiscale PDEs, balancing loss terms, training stability.

---

## OPEN ITEMS before submitting
- [ ] Fill in David's real major + math/physics/ML coursework (Q1 & Q2).
- [ ] Decide hours/week (recommend 5–10).
- [ ] David rewrites Q3 in his own words after reading the PINN notes.
- [ ] Honest-fit gut check: PINNs sit on PDEs + multivariable calculus +
      linear algebra; quantum side adds Schrödinger/Hilbert-space math. Go in
      as the eager builder, ready to ramp — don't claim fluency to defend.
- [ ] Optional resume tailoring once major/courses known.
