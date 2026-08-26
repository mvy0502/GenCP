# Registration — arms C4/C5: is the right level of description "adversarial" or "plausibility pressure"?

**Status: REGISTERED before any run. Committed before any number exists.**
Date: 23 Aug 2026. Conventions: Δ = candidate − baseline; **negative = candidate better**
(project-wide sign convention). Inference path and input provenance stated per row
(standing practice 5).

## The question

The measured mechanism is: *plausibility pressure causes invention where the input is
silent* — measured as edge density in input-silent regions relative to the real image
(pretrained 1.016, C1 1.023, C2 0.218; [headline-results.md](headline-results.md) B3,
ank130, OVP inputs). The C1–C2 contrast attributed this to **the adversarial term**. But
LPIPS is itself a plausibility pressure: it rewards matching the real image's perceptual
statistics, including in regions the input says nothing about. The mechanism therefore
predicts that an LPIPS-trained arm **without** a discriminator will also invent.

So the question this package decides is **not** "is the adversarial term harmful" — that is
measured. It is: **is the right level of description "adversarial" or "plausibility
pressure"?**

The design is a 2×2 factorial that turns the single C1–C2 observation into a replicated
main effect:

|                    | reconstruction = L1 | reconstruction = LPIPS |
|--------------------|---------------------|------------------------|
| adversarial ON     | C1 (measured)       | **C4 (new)**           |
| adversarial OFF    | C2 (measured)       | **C5 (new)**           |

C3 (L1-only + ~20% EU mix; [phase-c-config.md](phase-c-config.md)) is **not** a perceptual
variant — checked at gate time; no part of this package already exists.

**C5 is the most informative arm, not a control.** Its primary registered prediction is
that it **hallucinates** (edge ratio near 1.0, not near C2's 0.218). Both outcomes are
valuable and both are written down in advance:

- C5 hallucinates and scores worse than C2 → the claim **generalises** from "the
  adversarial term" to "any plausibility pressure" — stronger and more reusable.
- C5 stays near C2 (ratio well below 1.0) → something is specific to the adversarial term
  itself; the claim stays narrow, and that is its own finding.

## Gate 0 — the premise, verified from primary sources (PASS)

C4's justification is that the published GenCP HR model uses adversarial + LPIPS. Verified
before any GPU time, from the paper's text layer (local copy
`tubitak/data/paper/gencp_text.txt`, DOI 10.3390/rs18142356) and the upstream training
code:

1. **LPIPS confirmed, replacement not addition.** Paper, p. 15: *"the L1 reconstruction
   loss used in the classical Pix2Pix formulation was replaced by a Learned Perceptual
   Image Patch Similarity (LPIPS) loss"*. Table 5: HR GAN Loss = **"Adversarial Loss +
   λ LPIPS"**; VHR = "Adversarial Loss + λL1". The reconstruction term is LPIPS **alone**.
2. **λ = 100** (Table 5, both models). The code path agrees: `--LPIPS` reuses
   `--lambda_L1` (default 100) as the LPIPS weight
   ([models/pix2pix_model.py](../../models/pix2pix_model.py) lines 135–137).
3. **Backbone: the paper does not state it for the training loss.** The paper's
   AlexNet/VGG and "TorchMetrics 0.11.0" sentences (p. 15–16) are in the *validation
   metrics* section, about LPIPS as an evaluation measure. The training backbone is
   established from the upstream repository's own `--LPIPS` implementation instead:
   `LearnedPerceptualImagePatchSimilarity(net_type='vgg', reduction='mean')`
   ([models/pix2pix_model.py](../../models/pix2pix_model.py) line 85) — **VGG**, and the
   README's HR training example command passes `--LPIPS`. Residual uncertainty, disclosed:
   we cannot prove the released weights were produced by this exact code state; the repo is
   the paper's published code (data-availability statement, accessed 6 July 2026 per
   [published-paper-audit.md](published-paper-audit.md) item 10, no commit pinned). C4/C5
   therefore reproduce **the repository's executable definition** of the published
   objective, and are described that way — never as a certified reproduction of the
   released training run.
4. **Discriminator loss BCE** (Table 5). Our arms match: the fork's pix2pix defaults set
   `gan_mode='vanilla'` (= BCE-with-logits), and the C1 run log confirms
   `gan_mode: vanilla`. (The "lsgan" parenthetical in phase-c-config.md's arm table is a
   documentation error — corrections-log entry 18. The actual runs used vanilla/BCE, which
   *strengthens* comparability with the paper.)

**The pretrained weights already occupy the C4 cell** — the published HR generator is
adversarial + λ·LPIPS, trained on European data. We therefore have partial information
about that cell before running anything: edge ratio in input-silent regions 1.016 (n=130);
ank130 median residual 2.588 px; production-path 20-chip 1.370 px. C4 is accurately
described as **"the published objective, our fine-tuning data"**, not as an empty cell. If
C4's post-fine-tune edge ratio lands near the pretrained 1.016, that is consistent
continuity of the same objective, not new information about the objective itself.

Divergences from the published HR recipe, stated in advance: the paper trains from scratch
at lr 2e-4 for 120 epochs at batch [1,4,16]; C4/C5 are 20-epoch **fine-tunes** at lr 1e-4,
batch 4, from the released G — identical to C1/C2, because the comparison being replicated
is C1 vs C2, not the paper's training run. The paper's LPIPS library is TorchMetrics
0.11.0; the Kaggle image's torchmetrics version will be recorded from the run log and
reported with the results.

## Gate 1 — which comparison is being replicated (RECONCILED)

Two committed C1→C2 effects exist; they are different measurements, not a discrepancy:

| quantity | value | chip set | inputs | inference | source |
|---|---|---|---|---|---|
| C2 − C1 paired mean | **−0.638 ± 0.054 px** (median −0.524, t = −11.9, 9/130 worse) | ank130 (full Ankara evaluation set) | OVP (Overpass-rendered, archived) | STOCH (archived single-pass fakes) | [phase-c-results.md](phase-c-results.md) |
| C2 − C1 paired mean | **−0.171 ± 0.042 px** (19/20 chips) | 20-chip urban production subset | POST (production Geofabrik renders) | STOCH mean-of-8, K=8, BT.601 | [headline-results.md](headline-results.md) B2 |

Likewise C3: 0.982 px is its ank130 median ([phase-c3-results.md](phase-c3-results.md));
0.611 px is its production-path 20-chip figure (headline-results B2). Same arm, two
measurement paths.

**Registered choice: the comparison being replicated is the ank130 one — C2 − C1 =
−0.638 ± 0.054 px, n = 130, OVP inputs, STOCH archived-fake path.** Reasons, stated before
any number: (a) it is the phase-C registered main effect; (b) the mechanism measurement
(edge ratio) is defined on the same 130 chips and warps; (c) n = 130 carries the tighter
standard error, so "replicates at ≥ 2 SE" is the stronger claim. The 20-chip production
subset is evaluated too, for comparability with the on-path headline, but it is secondary
and carries no registered band.

## Registered predictions

**Primary — the adversarial main effect replicates under LPIPS.** Adversarial OFF beats
adversarial ON under both reconstruction terms:

- C2 < C1: already measured (−0.638 ± 0.054 px, ank130, per Gate 1).
- C5 < C4 (new). **Registered band: the main effect replicates if C5 − C4 (paired per-chip
  mean KARIOS residual, ank130, OVP inputs, same inference path as the archived C1/C2
  fakes) is negative at ≥ 2 SE.**

**Secondary — edge density in input-silent regions** (the mechanism measurement, and the
most important one here: it tests whether the *mechanism* is the same, not only whether the
outcome replicates). Same definition as B3 part 3: input-silent = canonical Sobel ≤ 20 on
the input render; edge fraction (Sobel > 20) of each arm's output vs the real chip on the
same pixels; per-chip ratio output/real, ank130. Registered reading bands: "near 1.0" =
mean ratio ≥ 0.8; "well below 1.0" = mean ratio ≤ 0.5; between = intermediate, reported as
measured.

- C1 and C4 both near 1.0 (C1 measured: 1.023).
- C2 well below 1.0 (measured: 0.218).
- **C5 near 1.0 as well — because LPIPS is itself a plausibility pressure.** This is the
  corrected framing: the mechanism *predicts* C5 invents. A C5 ratio ≤ 0.5 would instead
  localise the invention mechanism to the adversarial term specifically.

**Interaction — the mechanistically interesting quantity.** Define the adversarial penalty
under each reconstruction term, per chip (every chip carries all four arms):
D_L1 = C1 − C2 (measured +0.638 ± 0.054), D_LPIPS = C4 − C5 (new), interaction
I = D_LPIPS − D_L1 (paired per-chip mean ± SE). Reading bands, all registered now:

- **|I| < 2 SE(I): additive.** The two pressures are similar in magnitude — independent
  contributions, simple story.
- **I negative at ≥ 2 SE (penalty smaller under LPIPS), with D_LPIPS still positive at
  ≥ 2 SE: substitutes.** LPIPS already supplies plausibility pressure and the discriminator
  adds little — the two pressures act on the same lever. The richer mechanistic result.
- **I positive at ≥ 2 SE (penalty larger under LPIPS): super-additive.** Predicted by
  neither story; reported as its own finding, no post-hoc rescue.
- Degenerate case D_LPIPS not distinguishable from 0: the primary null branch below
  governs; the interaction is reported but not interpreted.

## Null interpretations — written before measuring

1. **C5 − C4 not significantly negative:** the adversarial effect does not replicate under
   LPIPS. The claim narrows to GAN+L1 configurations and is written that way everywhere.
   The C1–C2 finding is **not** retracted; the generalisation is.
2. **C5 worse than C2 (C5 − C2 positive at ≥ 2 SE):** perceptual reconstruction carries its
   own penalty. Separate finding, reported as such. (Note: this outcome plus a C5 edge
   ratio near 1.0 is exactly the generalisation case — the two readings are complementary,
   not in tension.)
3. **All four arms within noise of each other:** the entire loss-configuration claim is in
   danger and must be re-examined. **This is the retraction condition and it stays in this
   registration.**

## Invariance section — identical on both sides of every comparison

Same training data (the 5,577 Turkish pairs; zero EU mix), same packaged dataset
(`vedatyildirim/gencp-tr` v1), same schedule (C4 = C1's exactly: 2-epoch warm-up at 2e-5
with `--lr_policy step --lr_decay_iters 50`, then linear 10+10 at 1e-4, `epoch_count 3`;
C5 = C2's exactly: linear 10+10 at 1e-4, `epoch_count 1`), same seed (42, via the
sitecustomize hook), same initialisation (released `latest_net_G.pth`; C4's cold D built by
`make_cold_start_D()` seeded 42, provenance file written, exactly as C1), same batch 4,
load 286 / crop 256, direction BtoA, netG unet_256, norm batch, `gan_mode vanilla` (BCE)
where a D exists, λ = 100, save_epoch_freq 1, same Kaggle image and T4 machine shape, same
render path (archived OVP evaluation inputs; POST renders for the secondary 20-chip row),
same inference path per row (STOCH archived-fake procedure for ank130; STOCH mean-of-8
K=8 for the production subset), same evaluation chips (ank130; the 20-chip urban subset),
same matcher configuration (KARIOS config unchanged; BT.601 gray both sides), same analysis
scripts. **The only variable across the new columns is the reconstruction term; the only
variable across rows is the adversarial term.**

Known asymmetries, inherited from C1/C2 and disclosed rather than removed (they are part
of the comparison being replicated): the adversarial arms carry the 2-epoch warm-up and a
14.7% summed-LR disadvantage ([phase-c-config.md](phase-c-config.md)) — in the direction of
the registered prediction, identical in kind and size to the C1/C2 original, so the
replication is like-for-like; each stage's final epoch runs at lr 0 (upstream off-by-one,
symmetric across arms); D cold-start exists only where a D exists (inherent to the design).

New-to-this-package risks, named now: the LPIPS VGG weights download at metric
construction (internet on, as for C1/C2's torchmetrics guard); the image's torchmetrics
version is recorded from the log and reported; C4's stop rule is C1's with the term
renamed — if G degrades early despite the warm-up (G_LPIPS rising over the first two
main-stage epochs), the run stops and reports its curves, no rescue by improvisation.

> **AMENDMENT C45-a, 2026-08-24 — retrospective re-registration of the stop rule, written
> AFTER the runs completed and their results were read. This is not a preregistration and is
> not presented as one. The original rule above is preserved verbatim and is recorded as
> FAILED, not as satisfied. The replacement rule below binds FUTURE runs only and is not
> applied to the completed arms — scope statement at the end of this amendment.**
>
> *Revised 2026-08-24, second pass: the first version of this amendment argued from the
> two-epoch window, which is confounded (warm-up presence is collinear with discriminator
> presence), and stated C1 and C4 as behaving alike inside it, which they do not. The
> argument now rests on the sustained main-stage trend, the C1/C4 difference is stated, and
> the replacement rule is scoped to future runs. Nothing previously disclosed is withdrawn.*
>
> **What happened.** The coarse half of the stop rule above — "G_LPIPS rising over the first
> two main-stage epochs" — **fired**. C4's per-epoch G_LPIPS means are 56.24, 55.48
> (warm-up), then **54.37 → 54.65 → 55.02** across the first two main-stage transitions. The
> run was not stopped. That the run continued is dealt with here; that
> [phase-c-lpips-results.md](phase-c-lpips-results.md) reported the rule as "not triggered"
> is a separate reporting error and is **not** covered by this amendment — see
> corrections-log entry 27.
>
> **What the registered rule measured — the two-epoch window, and why it cannot carry the
> argument.** These are the numbers that fired the rule, and they are recorded as the
> description of what the rule looked at:
>
> | arm | discriminator | warm-up | first two main-stage transitions | behaviour in the window |
> |---|---|---|---|---|
> | C1 (GAN + L1) | yes | yes | 33.582 → **34.224** → 33.858 | **rise then fall** |
> | C4 (GAN + LPIPS) | yes | yes | 54.374 → **54.650** → **55.016** | **rises at both** |
> | C2 (L1 only) | no | no | 30.894 → 30.404 → 29.585 | falls at both |
> | C5 (LPIPS only) | no | no | 53.013 → 51.283 → 50.743 | falls at both |
>
> **This window is confounded and cannot be used as evidence.** Warm-up presence is perfectly
> collinear with discriminator presence in this design: C1 and C4 carry the 2-epoch warm-up at
> 2e-5, C2 and C5 do not. The first two main-stage transitions are therefore *exactly* where
> the learning rate jumps **2e-5 → 1e-4, a 5× increase**, in precisely the two arms that show
> a rise and in neither of the two that do not. The window cannot separate "the adversarial
> term competes with the reconstruction term" from "a 5× LR jump causes a transient bump".
> Note also that the two adversarial arms do **not** behave alike inside it: only C4 rises at
> both transitions; C1 rises then falls.
>
> **The argument rests on the sustained main-stage trend instead.** Over all eighteen
> main-stage epochs, after any LR transient has had time to decay:
>
> | arm | discriminator | main stage | trend slope | recovers below its main-stage start? |
> |---|---|---|---|---|
> | C1 (GAN + L1) | yes | 33.582 → 33.970, **+1.16%** | −0.001/epoch (flat, no trend) | **yes** — 4 epochs below it; minimum **33.118 at epoch 16**, −0.46 below the start |
> | C4 (GAN + LPIPS) | yes | 54.374 → 55.732, **+2.50%** | +0.056/epoch (rising) | **no — 0 of 18 epochs**; the main-stage start *is* the run minimum |
> | C2 (L1 only) | no | 30.894 → 28.455, **−7.90%** | −0.090/epoch | n/a (falling throughout) |
> | C5 (LPIPS only) | no | 53.013 → 49.014, **−7.54%** | −0.131/epoch | n/a (falling throughout) |
>
> **Neither adversarial arm reduces its reconstruction loss; both non-adversarial arms reduce
> it by roughly 8%.** That contrast is measured over the whole main stage and does not depend
> on the confounded window.
>
> **The transient explanation is refuted for C4 and not for C1, and the two must be written
> differently.** For C4 the discriminating detail is that its main-stage start of 54.374 is
> the run minimum: across twenty epochs it **never returns below where it began**. An LR-jump
> transient recovers below its starting value within a few epochs; this one never does, and
> instead drifts upward at +0.056/epoch (not monotonically — 13 of its 19 transitions
> are upward — but with no return to the starting level at any epoch). For **C1 the same test fails**: C1 does
> recover below its main-stage start, first at epoch 7 (33.536) and deepest at epoch 16
> (33.118, −0.46 below the start). C1's evidence is therefore the weaker one — not a
> sustained rise but a **flat** series with no trend, against its paired L1 arm C2 falling
> 7.90% under an otherwise identical schedule. So: **the non-transient reading is established
> for C4; for C1 the claim is only that the reconstruction loss fails to fall, not that it
> rises.**
>
> **The conclusion that survives, stated at the strength the evidence supports.** A gate that
> treats "reconstruction loss not falling" as a divergence symptom fires on the expected
> behaviour of an arm whose objective contains a competing term — i.e. **it fires precisely
> when the treatment under test is working**. That is a mis-specification, and it is why the
> run was allowed to stand. Under the rule as written, C1 — the phase-C arm this package
> replicates — should also have been stopped at its epoch 4; it was not, in a package
> registered five days earlier. The coarse half has never been applied literally.
>
> **Re-registered rule, for any future arm carrying an adversarial term.** The coarse half is
> replaced by: *the run stops if the per-epoch reconstruction loss rises more than **10%**
> above the **lowest value seen so far in the main stage** (a running minimum, not a
> hindsight one), **sustained over two consecutive epochs**.* Threshold and window are
> stated because "rising" has no threshold and fires on any positive difference; the running
> minimum is specified because a hindsight minimum would score an arm's own first epoch as an
> excursion — under that reading C2 and C5 would sit at +9.40% and +8.47% purely for
> starting high and falling, which is the opposite of what the gate is for. The sharp half
> (a generator-loss spike within the first few hundred iterations, the cold-D signature,
> [phase-c-config.md](phase-c-config.md)) is unchanged and remains the operative divergence
> test.
>
> **C45-a binds FUTURE runs only. It does not retroactively bless the completed arms.**
> Stated in those words because the alternative reading is the one a sceptical reader will
> reach on their own, and they would be right to: the 10% threshold **was chosen with all four
> completed arms' values already known, and all four pass it**. A gate that no arm triggers,
> whose threshold was set after seeing the arms, is a gate adjusted to pass — which is exactly
> what **standing practice 4** exists to forbid ("failed gates reported, never adjusted;
> mis-specified gates re-registered with the original preserved" — both halves of that
> practice are in play here, and only the second one licenses this amendment). So the scope is fixed here rather than left
> ambiguous:
>
> - **The completed seed-42 arms stand on the ORIGINAL rule**, which fired and was not acted
>   on. Their defence is the mis-specification argument above plus the epoch-2 and epoch-5
>   counterfactual below — **not** this amendment. C45-a is not evidence about them and is not
>   offered as any.
> - **C45-a is not a blind pre-specification** and must never be described as one. Its
>   threshold is calibrated, not registered-in-advance; the numbers it was calibrated against
>   are printed below so the calibration is visible rather than implied.
> - **Its first genuine test is the next set of runs** — an arm whose curves nobody has seen.
>   Until then it has been tested against nothing.
>
> Calibration values, printed so the reader can see what the threshold was set against —
> largest running excursion in each completed arm: **C1 +3.66%, C4 +2.50%, C2 +3.14%,
> C5 +0.73%.** No arm reaches 10% at any epoch, so under C45-a no arm would stop, and the
> rule no longer separates the adversarial arms from the others. **This is the arithmetic it
> is, after the fact; it is not evidence that the new rule was well chosen, only that it is
> explicit and that it does not fire on a working treatment.**
>
> **The counterfactual that makes the conclusion independent of this decision.** Had C4 been
> stopped at epoch 5 under the original rule, the registered primary band would still have
> fired: the dose-response sweep gives **C4 − C5 = +0.441 ± 0.039 px (11.3 SE) at epoch 5**
> and **+0.254 ± 0.040 px (6.4 SE) at epoch 2**. The effect is present at every epoch
> measured, at ≥ 6 SE throughout. Nothing in the package's conclusions turns on whether the
> run was stopped.

## Runs

Two fine-tuning runs on Kaggle (same pipeline as C1/C2/C3;
[build_kernels.py](../kaggle/build_kernels.py) / [train_c1_c2.py](../kaggle/train_c1_c2.py)
extended with arms C4/C5 — tubitak-side files only, no upstream file touched):

- **C4 (GAN + LPIPS):** C1's two-stage invocation + `--LPIPS`. Stock CLI flag; loss becomes
  GAN + 100·LPIPS(VGG) by the repository's own code path.
- **C5 (LPIPS only):** C2's single-stage invocation + `--LPIPS`, with the Kaggle-copy GAN-
  zeroing patch retargeted to the LPIPS branch
  (`self.loss_G = self.loss_G_GAN + self.loss_G_LPIPS` →
  `0.0 * self.loss_G_GAN + self.loss_G_LPIPS`), asserted to match exactly once, local
  pipeline files untouched.

Checkpoints every epoch (long runs checkpoint as they go); arms in separate sessions.

## Evaluation — no new metrics

The C1/C2 panel exactly, so the four arms are directly comparable: KARIOS positional
residual (ank130 primary; 20-chip urban production subset secondary), edge-density ratio in
input-silent regions (B3 part 3 definition, unchanged), KLT surviving-point counts, and —
if cheap — known-displacement recovery at the clean Cappadocia site so the new arms can
enter the paper's main table.

**The epoch sweep (1, 2, 5, 10, 20) is NOT run unless the primary band fires.** If it
does, endpoints first; the sweep then tests whether the dose–response relationship also
appears under LPIPS.
