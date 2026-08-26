# Related work and positioning

Status: first full pass, 2026-08-24. Closes `paper-context-addendum.md` §16's "not done at all".
Four independent survey legs were run: perception-distortion theory, hallucination
measurement, upstream citation tracking, and the remote-sensing matching neighbourhood.
Every item below was read or fetched; items that could not be verified are marked.

Scope decision this document assumes: the GRSL letter is the **loss-function letter**
(2x2 factorial, mechanism, alternatives ruled out, design rule). E1/E2 appear as two
sentences of scope. T1, the contamination pair and E3 go to the second paper.

---

## 1. Verdict on pre-emption

**Nothing pre-empts the core claim.** No paper measures the perception-distortion tradeoff
on a geometric-matching outcome, and no paper crosses an adversarial term with a
reconstruction term and reads out a task-level positional metric.

Three novelty claims are defensible, in descending strength. All three keep the
"to our knowledge" qualifier until a Scopus or Web of Science structured query is run,
which is the one leg not yet done.

1. **Matchability as the yardstick for hallucination.** No precedent found from either
   direction. The generative-matching literature uses translation to *increase* matching
   yield and never asks whether a matched point originates in fabricated structure.
2. **Input-silent regions as the measurement domain.** Every existing hallucination metric
   references the ground truth or an ensemble. None masks by what the conditioning input
   actually specified. The nearest miss is OSCAR's aleatoric-uncertainty map, used as a
   training weight rather than as an evaluation instrument.
3. **Filling a gap the SAR-to-optical field stated explicitly in 2019 and has not filled.**

---

## 2. The three papers that must be cited, or a reviewer will supply them

**Liu, Zhang, Xiong, "On the Classification-Distortion-Perception Tradeoff", NeurIPS 2019,
arXiv:1904.08816.** Proves distortion, perceptual divergence and classification error
cannot be minimised together. This is the tradeoff already reaching a downstream task.

Why it does not pre-empt us, in one sentence the letter must carry: the task is semantic
classification with an error *rate*, and a hallucinated texture that stays in-class costs
nothing there, whereas in a geometric task an invented edge is a confident, well-localised
observation of something that does not exist. Not citing this is a larger risk than citing it.

**Arar, Ginger, Danon, Bermano, Cohen-Or, "Unsupervised Multi-Modal Image Registration via
Geometry Preserving Image-to-Image Translation", CVPR 2020.** The most dangerous neighbour.
It is the only work found that ablates loss terms against a registration-accuracy metric,
and its finding runs the other way: reconstruction-only gives sharp but unrealistic images
with noisy deformation fields, adversarial-only gives realistic images with inexact
alignment, and the combination wins.

The distinction is structural and must be stated explicitly. There, translation and
registration are trained *jointly*, so the adversarial term is doing representation-alignment
work inside the training loop. Here, the generated image is a frozen deliverable and the
matcher is exogenous. Their metric is roughly 7 px on deformable registration; ours is
sub-pixel on rigid georeferencing, the regime where invented edges dominate. A reviewer who
knows this paper will otherwise read our result as contradicted by CVPR 2020.

**Chen, Ohayon et al., "Looks Too Good To Be True: An Information-Theoretic Analysis of
Hallucinations in Generative Restoration Models", NeurIPS 2024, arXiv:2405.16475.** Ties
hallucination directly to the pursuit of perceptual quality: as the output distribution is
pushed toward the true prior, uncertainty about the ground truth is converted into
confidently rendered false detail.

This is the best available theoretical citation for our mechanism. "An invented edge is a
false control point" is the geometric instantiation of exactly this. It makes the mechanism
section stronger, not weaker, because it means we are measuring a predicted effect rather
than asserting an unmotivated one.

---

## 3. The anchor, and how to stand relative to it

**Blau & Michaeli, "The Perception-Distortion Tradeoff", CVPR 2018, pp. 6228-6237,
arXiv:1711.06077, DOI 10.1109/CVPR.2018.00652.**

Two citation hazards. First, the theorem is Theorem 1 in the CVPR proceedings version and
Theorem 3 in the arXiv journal-length version; cite the proceedings version and its
numbering, and do not mix. Second, and more important for framing: Blau and Michaeli sell
GANs as the *solution*, writing that adversarial nets "provide a principled way to approach
the perception-distortion bound."

**Position the result as identifying the consumer, not as contradicting the theory.** A
matcher lives on the distortion axis, so for a matcher the perceptual end of the bound is
the wrong end. That reading is fully consistent with the theorem and is the safest place to
stand. Claiming to contradict Blau and Michaeli would be both wrong and easy to attack.

~~What the factorial adds that the theory does not have: PD treats plausibility as one axis
and says nothing about *substitutability between sources of plausibility pressure*. The
interaction term (I = -0.212 +/- 0.069) is a measurement of exactly that, and it has no
counterpart in the theory. Freirich, Michaeli, Meir (NeurIPS 2021, arXiv:2107.02555) is the
closest formal statement that the axis is a single traversable lever, and is the right
supporting citation for the "same lever" half of the claim.~~

**SUPERSEDED 2026-08-26.** Struck, preserved verbatim above. The interaction reading failed
at 5/6 across six confirmatory seeds and the pre-committed consequence withdrew the "same
lever" half of the claim ([seed-block-results.md](seed-block-results.md) §4), so the
factorial can no longer be positioned as supplying a measurement of substitutability, and
**the Freirich, Michaeli, Meir citation loses the half of the claim it was recruited to
support**. Do not cite it for that purpose.

**What the factorial adds, restated on what six seeds establish:** PD theory treats
plausibility as one axis and does not identify which downstream consumers sit on the wrong
end of it. The factorial identifies one — a geometric matcher — and establishes each
plausibility pressure separately, at n = 6 with the sign fixed in advance. That is a
contribution about *who pays* for movement along the axis, not about how sources of pressure
substitute for one another. It is the weaker of the two framings and it is the one the
evidence carries.

Adjacent, worth one clause each: Blau & Michaeli ICML 2019 (rate-distortion-perception,
arXiv:1901.07821); Ohayon, Michaeli, Elad, "The Perception-Robustness Tradeoff in
Deterministic Image Restoration", ICML 2024, arXiv:2311.09253, which proves plausibility
pressure buys instability and shows the cost-of-realism literature is broader than
distortion; Niu et al., Entropy 27(4):373, 2025, as a single umbrella survey citation to
save word budget.

---

## 4. The hallucination-measurement neighbourhood

Ranked by how hard a reviewer will push.

**sFRC (scanning Fourier Ring Correlation), arXiv:2603.04673, FDA/CDRH regulatory science
tool, code at DIDSR/sfrc.** Patch-wise Fourier ring correlation, threshold-based, outputs
candidate hallucinated regions with bounding boxes, no training. The closest methodological
cousin: cheap, localised, non-parametric. The distinction is the denominator. sFRC compares
output against *reference*; ours compares output against *what the input specified*. sFRC
cannot distinguish "invented where nothing was known" from "wrong where something was
known". Medical imaging only, no geometric task.

**Hallucination Score, arXiv:2507.14367 (preprint, Waterloo + Samsung AI Toronto).** Owns
the name and the input-conditioned definition, but implements it as a GPT-4o opinion score
from 1 to 5. Expensive, closed-API, non-reproducible, global rather than localised, natural
images only. Cite approvingly and position ours as its cheap deterministic counterpart.
Recheck its venue status near submission; a Samsung AI preprint is likely to land somewhere.

**Sayez et al., "Mitigating hallucination with non-adversarial strategies for image-to-image
translation in solar physics", Astronomy & Astrophysics 702, 2025,
DOI 10.1051/0004-6361/202555324.** The closest paper in spirit to the whole argument:
scientific instrument imagery, hallucination specifically in regions where the input lacks
contrast, validated against a downstream scientific task rather than PSNR, and the
non-adversarial variant preferred. No metric, no silent-region mask, no geometric framing.
Cite as evidence that the concern generalises across scientific image translation, and as
prior art for validating hallucination against the task rather than against a perceptual score.

**Also in the neighbourhood:** Hallucination Index (Tivnan et al., MICCAI 2024,
DOI 10.1007/978-3-031-72117-5_42) needs posterior sampling and degenerates on a
deterministic cGAN; HalluGen (arXiv:2512.03345) contributes the intrinsic/extrinsic split,
the cleanest published articulation of "consistent with the input or not", but is a
benchmark synthesiser plus learned detector rather than a metric; AQuA (Nature Biomedical
Engineering 2025, DOI 10.1038/s41551-025-01421-9) is the most relevant non-SR translation
detector but requires training a reverse generator plus a classifier ensemble.

---

## 5. The remote-sensing side, and the one gap that carries the letter

**The stated gap we fill.** Fuentes Reyes, Auer, Merkle, Henry, Schmitt, "SAR-to-Optical
Image Translation Based on Conditional Generative Adversarial Networks: Optimization,
Opportunities and Limits", Remote Sensing 11(17):2067, 2019, DOI 10.3390/rs11172067. They
name the phenomenon "fiction" and describe it precisely: the network generates "houses,
roads, forests, etc., in regions where these do not really exist". They do not measure it,
and they say why: **"There are currently no suitable metrics to evaluate the result in terms
of interpretability."** Seven years later OSCAR (arXiv:2601.06835, 2026) still ships FID and
LPIPS. This is the cleanest available statement that the metric we propose was asked for and
never built. Lead the related-work section with it. GENCP does not cite it.

**The precedent our metric warns about.** Merkle, Auer, Muller, Reinartz, "Exploring the
Potential of Conditional Adversarial Networks for Optical and SAR Image Matching", IEEE
JSTARS 11(6):1811-1820, 2018, DOI 10.1109/JSTARS.2018.2803212. Canonical precedent for
feeding translation output into a matching pipeline, with matching yield as the objective to
maximise, never as a diagnostic. The same pattern holds across the optical-SAR matching
literature. None of it audits the generated content for invention.

**The blur mechanism now has precedent, which it did not have when the claim was drafted.**
`paper-context-addendum.md` §5 states the mechanistic reading (a blurred template gives a broad
correlation peak, invented structure gives a sharp peak in the wrong place, and a broad peak
in the right place localises better) as our own observation. No remote-sensing registration
paper states it. But two adjacent fields do, and citing them turns an isolated assertion into
a generalisation of established practice:

- **Pan, B., "Bias error reduction of digital image correlation using Gaussian pre-filtering",
  Optics and Lasers in Engineering 51(10):1161-1167, 2013,
  DOI 10.1016/j.optlaseng.2013.04.009.** Deliberately Gaussian-blurring images *reduces
  systematic (bias) error* in subpixel displacement estimation, at the cost of increased
  random error. This is our mechanism, in a measurement science, thirteen years early.
- **Berg & Malik, "Geometric blur for template matching", CVPR 2001,
  DOI 10.1109/CVPR.2001.990529.** Blur applied deliberately to improve template matching;
  establishes blur as a feature rather than a defect.
- **Hu, Zhu, Sun, Li, Xiang, "Optical and SAR Image Registration Based on Pseudo-SAR Image
  Generation Strategy", Remote Sensing 15(14):3528, 2023, DOI 10.3390/rs15143528.** Uses a
  plain L2 translator, no adversarial term, specifically because the output feeds matching,
  and reports +30% correct matches. An existing practice with no articulated reason. Our
  result explains it.

**Caveat that must be pre-empted in one sentence.** The classical Cramer-Rao result for shift
estimation says variance scales inversely with gradient energy, i.e. sharper is better, for a
*correct* model. Our claim is a bias-versus-variance argument, not a variance argument, and
the letter should say so explicitly before a reviewer raises it.

**Citations a GRSL reviewer expects and will complain about if absent.** Li, Han, Ye, Xiang,
Zhang, "Deep learning in remote sensing image matching: A survey", ISPRS J. Photogramm.
Remote Sens. 225:88-112, 2025, DOI 10.1016/j.isprsjprs.2025.04.001. Ye, Bruzzone, Shan,
Bovolo, Zhu, "Fast and Robust Matching for Multimodal Remote Sensing Image Registration"
(CFOG), IEEE TGRS 57(11):9059-9070, 2019. Sommervold, Gazzea, Arghandeh, "A Survey on SAR and
Optical Satellite Image Registration", Remote Sensing 15(3):850, 2023, which explicitly flags
GAN translation to pseudo-optical as showing "great promise", i.e. the framing our letter
complicates. Corley, Stoken, Berton, "Are Pretrained Image Matchers Good Enough for
SAR-Optical Satellite Registration?", arXiv:2604.10217, 2026, which finds protocol choices
shift accuracy by up to 33x, strong support for the claim that setup rather than visual
quality dominates positional accuracy.

**Reference-data baselines the letter should benchmark against in one clause.** Sentinel-2
GRI: 8 m absolute geolocation at 95% circular error, 5 m multi-temporal co-registration
(ESA, PB 03.00, 2021); Gaudel et al., ISPRS Archives XLII-1/W1:447-454, 2017 for the GRI
itself. Rengarajan, Choate, Hasan, Denevan, "Co-registration accuracy between Landsat-8 and
Sentinel-2 orthorectified products", Remote Sensing of Environment 301:113947, 2024, which
reports under 6 m CE90 with GRI against over 12 m without.

**KARIOS.** No peer-reviewed paper exists. Cite Saunier, Canonicy, Louis, Debaecker, Albinet,
"KARIOS: A fast and efficient open source tool for geometric deformation analysis", v1.0,
Zenodo, 2024, DOI 10.5281/zenodo.10598329, plus the repository. Method citations underneath:
Lucas & Kanade (IJCAI 1981); Shi & Tomasi, "Good Features to Track" (CVPR 1994); Bouguet
(Intel, 2001). Bridge citation to the upstream group's own methodology: Kocaman & Seiz,
Remote Sensing 15(18):4575, 2023.

---

## 6. Upstream findings that change what we can write

**The LPIPS substitution is asserted, not measured.** Verified from the paper text: it states
only that "to improve the performance of the HR model, the L1 reconstruction loss used in the
classical Pix2Pix formulation was replaced by a Learned Perceptual Image Patch Similarity
(LPIPS) loss", and presents no comparative evidence. No L1-versus-LPIPS numbers on KARIOS or
on any image metric, and no ablation of the adversarial term.

This is favourable in two ways and should be stated in exactly these terms, which are
verifiable and non-inflammatory: our C5-C2 result contradicts an unevidenced design choice
rather than a published measurement, and our factorial supplies the ablation the upstream
work did not run.

**Objective confirmed independently.** Table 5 of the paper: HR uses adversarial + lambda x
LPIPS with lambda = 100 and a BCE discriminator; VHR uses adversarial + lambda x L1. The
released code corroborates: `gan_mode` default vanilla (BCE-with-logits), `lambda_L1` default
100, LPIPS with VGG backbone, `loss_G = loss_G_GAN + loss_G_LPIPS`. This closes corrections-log
entry 18 from the other direction: the published objective and our C4 are the same objective.

**Bibliography audit, with one qualification to `paper-context-addendum.md` §16.** The complete
54-entry reference list was obtained from the Crossref deposit. Confirmed: no
perception-distortion literature, no GAN-hallucination literature, and the word
"hallucination" never appears; the only artifact discussion is "blurring artifacts".
Cited metric references are LPIPS (Zhang et al., CVPR 2018), MS-SSIM (Wang, Simoncelli, Bovik,
2003), and PSNR-versus-SSIM comparisons (Hore & Ziou, ICPR 2010; Setiadi, MTA 2021); the
original SSIM paper is not cited.

**The qualification:** §16 currently says the bibliography contains no
adversarial-robustness-for-geometric-applications literature. Strictly, it contains exactly
one adversarial-attack paper, ref [47] Fan, Khairuddin, Liu, Hasikin, "Perceptual
Carlini-Wagner Attack: A Robust and Imperceptible Adversarial Attack Using LPIPS", IEEE Access
2025, and it is cited only as a supporting reference for the claim that LPIPS reflects human
perception, not as robustness work. **Write "no adversarial-robustness-for-geometric-
applications literature; the single adversarial-attack reference is cited only in support of
LPIPS as a perceptual metric."** The narrower statement is true and unattackable; the broader
one can be refuted by anyone with the reference list.

**Nearest neighbour in the upstream bibliography:** Sidlauskas et al., "Continuous Satellite
Image Generation from Standard Layer Maps Using Conditional Generative Adversarial Networks",
ISPRS Int. J. Geo-Inf. 13(12):448, 2024, DOI 10.3390/ijgi13120448. Map-layer to satellite
image via cGAN, and the closest published work in the same direction; it does not evaluate
georeferencing accuracy. No prior peer-reviewed work generates GCPs with a GAN for
georeferencing other than the GENCP line itself.

**Citation tracking, closed except one index.** Crossref 0, Semantic Scholar 0, OpenAlex 0,
as of 2026-08-24; the paper was published 15 July 2026. Google Scholar is blocked by
robots.txt and MDPI's own "Cited By" section could not be retrieved. So there is no citing
literature to position against, and the only residual check is a manual Google Scholar look
by a human.

**Zenodo record 15044428 read directly.** Titled "GenCP - Development of AI-generated Ground
Control Point (GCP) for EO Satellites Cal/Val", dated 6 December 2024, CC-BY 4.0, five files:
`GenCP_HR_DB.zip` 1.7 GB, `GenCP_HR_Model_Weights.zip` 404.7 MB, `GenCP_VHR_DB.zip` 3.4 GB,
`GenCP_VHR_Model_Weights.zip` 202.1 MB, `VH-RODA_2024_GENCP.pdf` 1.6 MB. This is the December
2024 VH-RODA-era deposit and therefore predates the 2026 article; **neither the record nor the
paper states whether the deposited weights correspond to the models reported in Tables 5 to 12.**
That is worth one sentence in the methods section, since our pretrained baseline is that deposit.

---

## 7. Two verification items before any of §19's numbers are quoted

**Item 1, resolved as a likely reconciliation but not yet confirmed.** An independent read of
the *preprint* (preprints.org/manuscript/202604.1240) found no CE90 or CE95 anywhere and no
keypoint counts, by targeted full-text search. `published-paper-audit.md` §6 and §7 record
both: keypoints 2912 / 2798 at the training site dropping to 957 / 978 at the independent
site, CE90 35.70 / 35.23 / 39.69 / 39.46 m, CE95 42.14 / 41.90 / 45.16 / 46.12 m.

The reconciliation is almost certainly that these numbers live in the **KARIOS figure panels**,
not in the tables or body text, which is consistent with §19's own statement that Figures 22
and 25 are the anchor. A text search finds table and prose numbers and misses figure content.

**Consequence for the manuscript:** every one of these numbers must be cited to its figure,
not to a table, and the figure number must be verified against the *published* version rather
than the preprint. Quoting them as though they were tabulated is an error a reviewer with the
PDF open will catch immediately.

**Item 2, new.** The preprint's Table 8 prints independent-site RMSE of 4.4 and 4.3 m against
a standard deviation of 23.7 and 23.2 m in the same column, which is arithmetically impossible.
`published-paper-audit.md` uses approximately 24.4 m, i.e. it reads this as a dropped leading
digit. **Check whether the published version carries the same typo.** If it does, it belongs in
§19's published-text-versus-published-artifact table as a fourth row, and it is a cleaner
example than the others because it is internally self-refuting.

---

## 8. What is still required before novelty language can harden

`paper-context-addendum.md` §16's rule stands: **"to our knowledge", never "first"**, until the
following are done.

- A structured Scopus or Web of Science query. This is the one leg of §16 not yet executed and
  it is the only one that requires institutional access.
- A manual Google Scholar citation check on the upstream paper, since the automated indices are
  all at zero but Scholar could not be reached.
- Verification of the *Int. J. Appl. Earth Obs. Geoinf.* 2026 systematic review of generative
  SAR-optical translation (Wang, Zhang, Shan, Wei, Tang, 146:105009,
  DOI 10.1016/j.jag.2025.105009) through institutional access. ScienceDirect blocks automated
  fetch, and this is the best survey-level backing for the statement that the field evaluates
  translation with perceptual metrics and has no hallucination metric.
