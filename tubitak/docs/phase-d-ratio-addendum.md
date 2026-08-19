# Phase D addendum — the Cappadocia/Ankara gain ratio (registered before any C2 generation at any Phase D site)

**Registered 2026-08-20.** The Phase D registration (phase-cd-preparation.md §3) predates Phase C's
outcome and did not anticipate needing to decompose C2's Ankara gain. This addendum registers one
derived quantity before C2 is generated at any Phase D site.

**State of the disk at registration, disclosed:** pretrained-weights KARIOS runs for both Phase D
sites (36SXJ Cappadocia, 36SWJ Tuz Gölü) already exist under `tubitak/data/tiles*/run/results/`,
produced during Phase D preparation. They have not been aggregated — no per-site statistic has
been computed or seen. C2 has not been generated at either site. This addendum is committed
before any aggregation of those results and before any C2 generation.

## The quantity

On matched information-content strata (the **Ankara fixed cut points** 0.09904 / 0.1588 / 0.2241 /
0.33222 applied to the canonical density measure — fraction of Sobel gradient magnitude > 20 on
the grayscale model-input render, **recomputed from the input renders** at both sites rather than
taken from any per-site CSV):

    gain(site, stratum) = median_resid(pretrained) − median_resid(C2), paired per chip
    R = [equal-weight mean over strata of gain(Cappadocia)] / [equal-weight mean over strata of gain(Ankara)]

R estimates the fraction of the Ankara gain that survives a change of scene and date
(36SXJ, 2026-05-27 — the only site in inventory where tile AND date are absent from fine-tuning).

## Registered reading (fixed before the number exists)

| R | reading |
|---|---|
| ≥ 0.7 | mostly real adaptation — the Ankara gain largely survives the scene change |
| 0.3 – 0.7 | mixed; scene match and transferable adaptation both material |
| ≤ 0.3 | mostly scene adaptation — **subject to the confound below** |

## Registered confound — stated so the number cannot carry more weight than it can hold

Cappadocia is also a **harder landform** (it was chosen as the morphological-OOD site precisely
because the pretrained model fails on its badlands texture). A low R therefore has two
explanations — scene-specificity of the fine-tune, or landform difficulty — and **R cannot
separate them on its own.** Partial leverage comes from the registered within-site anchoring:
Cappadocia's flat-agricultural chips were registered to behave like Ankara (±0.3 px), its
badlands chips to fail morphologically. If the flat chips show high gain while badlands chips
show low gain, the deficit is landform, not scene, and a low overall R should be read
accordingly. If even the flat chips show little gain, scene-specificity leads.

Second registered caveat: gains on sparse strata are small and noisy at n = 26 per stratum;
R is dominated by the mid and dense strata, and per-stratum gains are reported alongside R so
the aggregation hides nothing.

## Tuz Gölü caveat (per the work-package instruction, registered here)

Tuz Gölü (36SWJ, 2026-04-30) was itself a fine-tuning tile at the same date. It is **not a
generalisation test for C2**; a strong C2 result there is fully explained by scene adaptation.
It remains a valid compositional-OOD test for the **pretrained** weights. Its C2 numbers are
reported in the same table as everything else with this caveat attached inline, not in a footnote.

## Scoring discipline

The four pre-registered mechanism-separation outcomes of phase-cd-preparation.md §3 are scored
against the committed text of that file, not from memory. C2 = epoch 20 only. KARIOS config
unchanged. The checkerboard watch metric (phase-c-europe-registration.md) is recorded for every
generation at both sites.
