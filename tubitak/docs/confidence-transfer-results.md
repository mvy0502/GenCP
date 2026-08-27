# Do the European confidence bands transfer to Turkey? And how do the arms compare?

Executes [`confidence-registration-3.md`](confidence-registration-3.md), committed
(`0822926`) before any number here existed. Boundaries applied **unchanged**; nothing
re-derived, nothing re-inferred.

**Sign convention: higher confidence = better = lower expected matching error.** All errors
are KARIOS median radial residual in pixels; 1 px = 10 m. Lower is better.

---

## 1. Band transfer — two of three criteria pass, and the failure is not where it hurts

European boundaries on `z(conf_D)` (mean 0.716106, std 0.514109, `red_hi` -0.982375,
`green_lo` -0.245312), applied as they stand to the 130 Ankara chips.

| band | n (EU) | median EU | IQR EU | n (ANK) | median ANK | IQR ANK | ANK vs EU |
|---|---|---|---|---|---|---|---|
| **Red** | 19 | 3.3093 | 0.692 | 20 | **3.0861** | 0.648 | **-6.7%** |
| **Amber** | 55 | 2.6310 | 1.085 | 50 | 1.3949 | 1.324 | -47.0% |
| **Green** | 76 | 1.3310 | 0.996 | 60 | 0.5902 | 0.281 | -55.7% |

| registered criterion | result |
|---|---|
| 1. Ordinal — `red > amber > green` | **PASS** — 3.0861 > 1.3949 > 0.5902 |
| 2. Separation — `red/green >= 1.5` | **PASS** — Ankara **5.23x**, 95% CI [4.62, 5.72], against Europe's 2.49x |
| 3. Absolute — `\|ANK - EU\| / EU <= 0.50` every band | **FAIL** — red 6.7%, amber 47.0%, green **55.7%** |

Criterion 3 was registered as an expected failure and it failed, though only on green.

### What actually transferred, in one line

**The ordering transfers, the separation transfers and gets *better*, and the red band's
absolute number transfers almost exactly. Amber and green do not.**

The red band is the one the dialog uses to tell a user *do not use this*, and its European
figure of 3.31 px predicts Ankara's 3.09 px to within 7%. The band populations barely move
either (19/55/76 in Europe against 20/50/60 in Ankara), so the boundaries are not
mis-scaled for Turkey.

What shifts is the easy end. Ankara's green chips match at 0.59 px where Europe's manage
1.33 px. That is the corpus, not the score: Ankara's overall median is 0.94 px against
Europe's 1.98 px, and the score is z-normalised on European statistics. **The European
green figure is pessimistic in Turkey** — a user told "1.33 px" gets 0.59 px. Wrong, but
wrong in the safe direction; the red figure, which is the dangerous one to get wrong, is
the one that holds.

Separation improving from 2.49x to 5.23x means the layer discriminates *more* sharply in
Turkey than where it was calibrated.

### What the dialog says now, and the decision left open

The dialog quoted per-band medians with no corpus attached. That is now known to be
misleading for two of three bands, so the **minimum factual correction has been applied**:
every per-band figure names the corpus it came from.

Current text, per band, e.g. red:

> Ayrık ölçümde bu bandın eşleştirme hatası ortancası: **Avrupa 3,3 piksel**.

**The richer option, not applied, for you to decide:** show both corpora, since both are
now measured.

> Ayrık ölçümde bu bandın eşleştirme hatası ortancası: **Avrupa 3,3 piksel · Ankara
> 3,1 piksel**.

That is more informative and makes the transfer visible to the reader, at the cost of a
longer line in a box people need to read quickly. Say which you want and it is a
one-string change in `qgis_plugin/strings.py`.

### Scope

Ankara is **one city**. 130 chips from a single site do not establish "transfers to
Turkey", whatever these numbers say, and this document does not claim it.

---

## 2. Arm comparison

One table, same corpus, same inference path, same error column (`med_mean32`), arms
compared on the chips they share. **Lower is better.**

### Held-out European corpus — the only one that is genuinely held out

150 chips, `sitevar == "eu"`.

| arm | median px | mean px | IQR | median matched points | held-out EU errors exist? |
|---|---|---|---|---|---|
| **C2** | **1.9802** | 1.9998 | 1.555 | 74 | **yes** |
| C1 | 2.5329 | 2.4329 | 1.417 | 52 | **yes** |
| pretrained | — | — | — | — | **no** |
| C3 | — | — | — | — | **no** |
| C4 | — | — | — | — | **no** |
| C5 | — | — | — | — | **no** |

Paired on the same 150 chips: **C2 - C1 = -0.3380 px median**, C2 better on **117 of 150**
chips, Wilcoxon p = 3.2e-13.

### Ankara corpus, for context — not held out

130 chips, `sitevar == "ank_overpass"`. Ankara was the C-phase's reporting corpus, so these
are **not** a held-out measurement and are included only because they add a third arm.

| arm | median px | mean px | IQR | median matched points |
|---|---|---|---|---|
| **C2** | **0.9418** | 1.3816 | 1.483 | 73 |
| C1 | 1.7061 | 2.0112 | 2.025 | 62 |
| pretrained | 2.5253 | 2.5560 | 1.247 | 52 |

Paired: C2 - C1 = -0.5615 px (116/130 better, p = 5.2e-19); pretrained - C2 = +1.2554 px
(C2 better on 122/130, p = 8.2e-22).

### The caveat that belongs in the same breath as the table

**The arms do not contribute equal numbers of matched points**, and this project has
already produced one false result through exactly that mechanism. C2's median point count
is 74 against C1's 52 on the European corpus, and 73 against 52 for `pretrained` on Ankara.
A median over more points is not the same measurement as a median over fewer, and part of
C2's apparent advantage may be that KARIOS simply finds more to match on its output.

`tubitak/scripts/common_support/common_support_rescore.py` implements the project's
equal-count truncation for exactly this, and
[`arm-common-support-results.md`](arm-common-support-results.md) applied it to the Ankara
six-seed block. **It has not been applied to the European corpus**, and doing so is a real
piece of work, not a footnote. Until it is, the European C2-vs-C1 gap should be read as
*C2 is better on this measurement*, not *C2 is better by 0.34 px*.

No recommendation is offered here, and nothing was re-trained.

### What calibrating the confidence layer for another arm would cost

The layer needs, for the arm in question:

1. **Held-out European KARIOS errors** — generate 150 chips through that arm (minutes;
   inference is ~0.3 s per chip) and run KARIOS over them against the same references. The
   KARIOS run is the real cost and it is a run, not a decision.
2. **Re-derive the bands** on those errors by the rule already registered — minutes, and the
   code exists (`tubitak/scripts/confidence_validate.py`).
3. **Update `CALIBRATION`** with the new boundaries, per-band medians and the new model's
   SHA-256.

`conf_D` itself is computed from the rasterised **input** and does not depend on the model
at all, so nothing about the score has to be re-derived — only the mapping from score to
expected error, which is what the bands are. That is why this is a bounded job rather than
a repeat of the whole exercise.

**Nothing here says which arm should ship.** C2 leads on the one held-out corpus available,
and C2 is also the calibrated arm — those two facts have a common cause worth naming: C2
was chosen for calibration *because* it had held-out errors, and it has held-out errors
because of how the C-phase was run. The product decision is yours.
