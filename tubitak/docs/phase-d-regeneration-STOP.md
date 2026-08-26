# Phase D regeneration — STOPPED BEFORE RUNNING. Report.

**2026-08-26. Item 4 halted at the inventory stage, before any computation.** The stop
condition that fired is not the one that was anticipated. The instruction was to stop and
report if the regenerated numbers do not reproduce. **The regeneration cannot be attempted at
all**, because its inputs no longer exist either.

---

## 1. Target values, recorded before anything was run

Required by the instruction, and recorded here first so that the reproduction was never blind
and cannot later be presented as if it had been.

**Check 3 — restraint versus mechanical blur** (from `phase-c-europe-results.md`):

| quantity | published target |
|---|---|
| fitted global Gaussian sigma | **0.45** |
| recovered fraction, Europe (568 chips) | **−6.1%** |
| recovered fraction, Europe excluding empty-input stratum | **−7.6%** |
| recovered fraction, Cappadocia (130 chips) | **+1.7%** |
| blur's per-chip effect | 295 of 568 chips worse |
| blur's point-count effect | Δn median −1 |
| registered bands | ≥ 60% recovered kills the restraint claim; ≤ 25% supports it |

**Check 7b — systematic versus scatter decomposition, Europe:**

| quantity | published target |
|---|---|
| scatter change | **−0.473 ± 0.024 px** |
| systematic change | **+0.079 ± 0.018 px** (systematic slightly *worse* under C2) |
| share of gain that is scatter tightening | **~86%** |

**This is a reproduction with a known target and would have been declared as one in any
result it produced.** It is not blind, and no version of it could have been.

---

## 2. Why it stopped: the inputs are gone too

The Phase D audit established that the *outputs* were lost — `eu_per_chip.csv`,
`blur_control_per_chip.csv`, `eu_decomposition_per_chip.csv`, and no committed script. The
audit's recommendation assumed the procedures could simply be re-run from the registrations.
**Checking that assumption before running is what this stop rests on: the generated imagery
those procedures consume does not exist either.**

### The European hold-out set has no generated outputs at all

```
tubitak/data/eu_holdout/  →  eu_inventory.csv, inputs/ (568), ref/ (568), ref_warp/ (568)
```

**Four entries. Inputs and references only.** There is no arm output directory, no pretrained
render, no C2 render, and no KARIOS result set for the 568-chip European hold-out anywhere in
the repository. A repository-wide search for any directory holding ~568 generated images
returns only `inputs/`, `ref/`, `ref_warp/` and two upstream dataset folders.

### Every site run directory holds exactly ONE arm

```
tiles36SXJ/run/ (Cappadocia)  arms/ 130 .tif   inputs/ 130   ref/ 260   results/ 130
tiles36SWJ/run/ (Tuz Gölü)    arms/ 194 .tif   inputs/ 194   ref/ 388   results/ 194
ankara/run/                   arms/ 130 .tif   inputs/ 130   ref/ 260   results/ 130
```

`arms/` contains loose `.tif` files, not per-arm subdirectories — verified: no subdirectory
exists under any of them. **The surviving arm is the pretrained one** (the audit inventory
records the Cappadocia set recomputing to 3.452 px / 31 points, the Phase D pretrained row).
**No C2 output survives at any site.**

### What that means for each procedure

| procedure | needs | status |
|---|---|---|
| **Check 3, Europe leg** (the −6.1% headline) | pretrained renders for 568 EU chips, to blur; C2's gain as the denominator | **both ABSENT — cannot run** |
| **Check 3, Cappadocia leg** (+1.7%) | pretrained renders (present, 130) **and C2's gain as denominator** | **denominator ABSENT — cannot run** |
| **Check 7b** (~86% scatter) | per-point KARIOS for **both** arms on 568 EU chips | **both ABSENT — cannot run** |

**Not one of the three legs can be computed.** The blur control needs a C2 gain to express a
recovered *fraction* of, and no C2 render survives anywhere — so even the site whose
pretrained imagery is intact cannot produce the published quantity.

---

## 3. The obstacle that would remain even if the imagery were regenerated

**Re-running inference would produce a replication, not a reproduction, and could not confirm
the target values in §1.**

The inference path for this material is **stochastic — test-time dropout is active**, which
this project registered as a labelled property rather than a defect. Two runs of the same
checkpoint on the same input produce different images. The published Phase D numbers came from
one draw; a new draw is a different sample.

**For these particular quantities that matters more than usual**, because the blur control
reports a *ratio of two small gains*. The recovered fraction is −6.1%: a numerator near zero
divided by C2's gain. Draw-to-draw noise that would be immaterial to a 0.6 px main effect can
move a near-zero ratio by a large relative amount. **A regenerated −2% or −11% would neither
confirm nor refute the published −6.1%**, and reporting either as "the number reproduced"
would be false.

The project's own bound does not rescue this: registration A bounded the
**deterministic-versus-stochastic** gap at |Δ| ≤ 0.05 px at n = 30. **That is not a bound on
the difference between two stochastic draws**, and it is not a bound on a ratio.

**So the honest description of any regeneration is: a fresh experiment answering the same
registered question, whose agreement or disagreement with the 2026-08-20 numbers is
informative but not a reproduction.** That is a legitimate thing to run. It is not what item 4
specified, and it costs GPU inference on 568 × 2 EU chips plus 130 × 2 Cappadocia chips.

---

## 4. What the re-run could and could not recover — the three named items

| item | recoverable by re-running? | why |
|---|---|---|
| **Check 5's Ankara arm** (floor sweep 0/10/20/30 on Ankara) | **NO, not from surviving data** | Needs both arms' per-chip residuals and point counts on Ankara. Only the pretrained arm survives. Recoverable only by regenerating C2's Ankara renders — again a fresh draw, not a reproduction |
| **Check 7a's per-stratum gains** (the components of R = 1.188 / 1.258) | **NO, not from surviving data** | Needs both arms at Cappadocia *and* Ankara, per stratum. Same single-arm limitation |
| **Check 7b's undischarged conditional** ("if the improvement is mostly scatter, restraint/blur carries the burden") | **YES — fully, now, at zero cost** | It is a **writing** act, not a computation. The conditional was triggered by a published number and simply never stated. It can be discharged in a sentence without recomputing anything |

**One of the three is free and the other two are not recoverable as reproductions.** The free
one should be done regardless of what is decided about the rest.

---

## 5. Consequence for Table II — the branch is now decided against reproduction

The budget reconciliation set out two branches. **Neither is the one that occurred**, so the
reconciliation needs the third:

- The blur row and the corrected-georeferencing row **cannot be restored by re-running the
  analysis.** Their evidence is not merely uncommitted; it is unreconstructible from what
  survives.
- **They can only be restored by a new experiment**, which would produce new numbers under a
  new registration, and which cannot be described as confirming the published ones.

**The decision this forces is yours, and it is not a budget decision.** Three options, with
what each costs and claims:

1. **Both rows leave Table II.** The letter loses two of its four refuted candidates; Section
   IV falls to 250 against 320 and **the letter is under budget** (≈ 3,326 committed against
   3,300 after the Methods/Results split, so roughly at par). The cold-discriminator and
   matcher rows survive intact and both are fully evidenced. **The restraint claim then rests
   on the cross-family replication rather than on an active blur control**, which is weaker
   than the current draft claims but is defensible and is what the surviving evidence supports.
2. **Run the new experiment**, register it in advance as a replication rather than a
   reproduction, and report it with the disclosure that the original artifacts were lost and
   the question was re-asked on a fresh draw. Costs GPU inference on ~1,400 chip-arms plus
   scoring. **If it agrees, the rows return with a stronger provenance than they have now; if
   it disagrees, that is a finding about the original numbers.**
3. **Keep the rows with a provenance caveat and no regeneration.** **I recommend against
   this.** It publishes numbers no one can check, in a paper whose central methodological
   claim is that unverifiable single-run numbers should not be trusted. A reviewer who asks
   for the per-chip data would receive nothing.

**My recommendation is 1 if the letter must ship soon, and 2 if there is time**, because 2
converts the weakest evidence in the paper into the best-provenanced. **3 is the option that
contradicts the paper's own thesis.**

---

## 6. What was NOT done

**Nothing was computed, regenerated, reconstructed or estimated.** No inference was run, no
GPU was used, no number in any document was changed, and no corrections-log entry was applied.
The drafted entries 32–34 in [phase-d-audit.md](phase-d-audit.md) stand as drafted and are
**strengthened** by this finding: entry 32 recorded that the regenerability claim was false
because the scripts were not committed. **It is false for a second and larger reason — the
input imagery is gone as well**, and that should be added to the entry before it is applied.
