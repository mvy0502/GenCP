# The learning-rate confound at the positional outcome — results

Written 26 August 2026, immediately after
[lr-confound-registration.md](lr-confound-registration.md) was committed and pushed
(`c937d462`) and the checkpoints were scored. The registration's branch text was fixed before
any positional number for these arms existed.

**Outcome: BRANCH 2. The confound is answered at the positional outcome.** Giving a
non-adversarial arm the adversarial arm's exact learning-rate schedule moves its positional
residual by **+0.0065 px** in the L1 family and **−0.0360 px** in the LPIPS family — 1.0% and
−6.8% of the adversarial gaps they would have to explain, neither reaching the registered
0.10 px threshold, neither reaching 2 SE.

**Nothing is withdrawn and no follow-up is triggered.** The `C1_nowarmup` / `C4_nowarmup`
package is not launched.

---

## 1. What ran

**Zero GPU training.** Volume read plus local scoring, exactly as registered.

Frozen `seed_eval_run.py` (commit `6418febc`), unchanged, through its own documented
ROUTING-ONLY flags:

```
seed_eval_run.py --seed 43 --variant modalwarmup --arms C2,C5
```

**Zero failures: 130/130 chips inferred, 390/390 warps, 260/260 KARIOS runs, 0 skipped in the
edge-ratio pass.**

**The disclosed routing rename was applied and verified.** The Volume stores these arms at
`seed43/C2_warmup/C2_warmup/` and `seed43/C5_warmup/C5_warmup/`; they were copied to
`c{2,5}_checkpoints_s43_modalwarmup/checkpoints/{C2,C5}/` so the frozen runner's arm routing
resolves. **The directories were renamed; the checkpoint files were not modified.** Every
number below names the arm as `C2_warmup` or `C5_warmup`.

**Checkpoint identity check passed**, as registered: `latest_net_G.pth` is **tensor-equal** to
`20_net_G.pth` for both arms, all 82 tensors. Note that the two files' **sha256 values differ**
(`255a752e…` vs `b3155d90…` for C2_warmup; `7f11b5eb…` vs `122fc636…` for C5_warmup) while
their tensor contents are identical — pickle metadata, not weights. **Recorded because a
reader comparing file hashes alone would reach the wrong conclusion**, and because the
project's `verify_latest` practice checks tensors rather than bytes for exactly this reason.

**Baseline validation.** Both published adversarial gaps reproduce **exactly** from the
committed seed-43 Modal per-chip file: D_L1 = C1 − C2 = **+0.6473 px**, D_LPIPS = C4 − C5 =
**+0.5292 px**. The comparison is therefore against the same numbers the hardware gate
published, not against a re-derivation of them.

---

## 2. The registered reading

Per-arm mean over 130 chips of the per-chip median KARIOS residual. Δ is a paired per-chip
difference, sign fixed in advance so that **positive = toward the adversarial arm (worse)**.

### Arm means (px), all six arms at seed 43 Modal

| arm | adversarial | integrated LR | mean residual | median |
|---|---|---|---|---|
| C1 | yes | 13.40 | 2.0172 | 1.8273 |
| C2 | no | 15.00 | 1.3699 | 0.9091 |
| **C2_warmup** | **no** | **13.40** | **1.3764** | 1.0316 |
| C4 | yes | 13.40 | 2.0077 | 1.7963 |
| C5 | no | 15.00 | 1.4785 | 1.1665 |
| **C5_warmup** | **no** | **13.40** | **1.4425** | 1.1142 |

### The two tests

| | **L1 family** | **LPIPS family** |
|---|---|---|
| adversarial gap to explain | D_L1 = C1 − C2 = **+0.6473 px** | D_LPIPS = C4 − C5 = **+0.5292 px** |
| Δ = warmed − un-warmed | **+0.0065 ± 0.0335 px** | **−0.0360 ± 0.0383 px** |
| distance from zero | **0.19 SE** | **0.94 SE** |
| condition 1: \|Δ\| ≥ 0.10 px toward adversarial | **NO** | **NO** |
| condition 2: \|Δ\| ≥ 2 SE | **NO** | **NO** |
| **MATERIAL?** | **NO** | **NO** |
| f = Δ/D *(reported, not required)* | **+0.010** | **−0.068** |

**Neither family shows material movement. Neither condition is met in either family.
BRANCH 2 fires.**

### The LPIPS sign, handled as registered

C5_warmup's residual is **lower** than C5's — movement *away* from the adversarial arm. The
registration anticipated this case and fixed its treatment in advance: negative movement is
neither branch's evidence, counts as branch 2 for the confound question, and is flagged as its
own observation rather than folded into a story.

**Here it is not an observation worth much: −0.0360 px at 0.94 SE is indistinguishable from
zero.** It is reported because it was registered to be reported, not because it means
anything. **It must not be written up as "the shorter schedule helps."**

### Mechanism measure, reported alongside

The edge-ratio means barely move either, which is consistent with the same conclusion:

| arm | edge ratio | vs un-warmed |
|---|---|---|
| C2 | 0.2803 | — |
| **C2_warmup** | **0.2730** | −0.0074 |
| C5 | 1.1584 | — |
| **C5_warmup** | **1.1553** | −0.0031 |

C2_warmup remains far below the registered 0.5 threshold and C5_warmup remains high. **The
schedule does not move the invention measure any more than it moves the residual.** These are
descriptive; no mechanism reading was registered for this probe.

---

## 3. What this establishes, and what it does not

**Established.** The ~11% integrated-LR deficit carried by the adversarial arms
(13.40 against 15.00, a 10.67% shortfall computed from pix2pix's own `lambda_rule`) **does not
account for the adversarial main effect.** A non-adversarial arm given that exact deficit
moves 1.0% of the L1 gap and −6.8% of the LPIPS gap. To explain the main effect the schedule
would have to move an arm by roughly 0.6 px; it moves it by roughly 0.01.

**The manuscript therefore states the LR asymmetry as a disclosed design asymmetry**, with
this probe cited as the test that bounded it, and **the adversarial attribution stands.** The
asymmetry was already listed among the "known asymmetries, inherited and disclosed rather than
removed" in [seed-replication-registration.md](seed-replication-registration.md); what changes
is that its consequence is now measured rather than assumed to be small.

**Not established, and the registration said so in advance.** This probe tests the schedule's
effect **on the non-adversarial arms only.** It asks whether the schedule alone can produce an
adversarial-sized penalty, and the answer is no. **It does not establish that the adversarial
arms would be unaffected by the reverse manipulation** — that requires `C1_nowarmup` /
`C4_nowarmup`, which is not run and whose launch is not triggered by this outcome.

**Scope, repeated because this number will travel.** **n = 1 seed. A mechanism probe, not a
confirmatory estimate.** It enters no registered contrast, modifies no published number, and
cannot repair or strengthen the failed interaction reading. Within platform and within seed
(Modal, seed 43, both sides) — the control the warm-up package's first attempt lacked.

**One thing this probe could not have overturned, recorded before it ran.** The **secondary**
contrast C5 − C2 compares two un-warmed 20-epoch arms with **identical integrated LR
(15.00 each)** and is therefore structurally immune to this confound. The registration states
this ahead of the numbers. Had branch 1 fired, the secondary — and with it the LPIPS-alone
penalty and the title — would still have stood.

---

## 4. Artifacts

Per standing practice 10, committed to `tubitak/docs/evidence/C45_s43_modalwarmup/`:

| file | sha256 |
|---|---|
| `C45_per_chip.csv` | `736bb74648d9bc01650aadc01a403d8642b1aa31613a0d8983828844d310c970` |
| `C45_edge_ratio.csv` | `f124f9c800cbe2238594472d56f563c7062fd795ab8f1ebe3ebeea50599ec62a` |

Both hashes are as printed by the frozen runner at the end of its own scoring step.

**This is not a corrections-log entry.** A registered probe returning its registered
branch is the system working.
