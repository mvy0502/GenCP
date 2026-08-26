# Evidence manifest — tracked numerical artifacts

**Created 2026-08-26, in response to the Phase D audit
([phase-d-audit.md](../phase-d-audit.md) §C).** Every file in this directory is a numerical
artifact that a published number depends on. They live under `docs/` because
`.gitignore:54–57` excludes `tubitak/data/*` and `tubitak/outputs/*` wholesale, so **nothing
under those paths has ever been tracked.**

## Why this directory exists

Phase D's evidence loss was not a Phase D failure. It was **the first casualty of a repository
policy that was still in force at the moment the loss was found.** Six of seven Phase D checks
and the veto rule have no surviving artifact; the files their results documents name by
filename do not exist; and the claim that they were "regenerable end-to-end from committed
scripts" was false, because those scripts were not committed either.

At the moment that audit was written, **the six-seed Modal block — 26 arm-units, one night,
$23 of GPU — was protected by nothing but sha256 strings printed in a markdown file.** A hash
proves identity if the file survives. **It does not preserve the file.** Every per-chip CSV in
this project was one `rm -rf` or one machine change from being exactly as recoverable as
Phase D's.

The escape route was found by accident: the warm-up loss logs were committed to
`docs/gates/loss_logs/` because the originals sat in a temporary directory. That precedent is
now the policy — see **standing practice 9** in
[standing-practices.md](../standing-practices.md).

## Verification performed at commit time

**All 14 sha256 values that had already been published in the results record were checked
against the committed copies. All 14 MATCH. Zero mismatches.** Those are seed 42's and the six
Modal seeds' `C45_per_chip.csv` and `C45_edge_ratio.csv`, whose hashes were printed by the
frozen `seed_analysis.py` provenance block.

Every copy was additionally verified byte-identical to its source with `cmp` before commit.

## Two integrity observations, recorded and NOT resolved

Reported rather than fixed, per the standing rule that an audit records what it finds:

1. **`capp_c1/reliability.csv` and `capp_c2/reliability.csv` are byte-identical**
   (`d84036ac…`), as are **`odtu/reliability.csv` and `odtu_c1/reliability.csv`**
   (`a559d7e9…`), and **`gate2/30TXQ_0830_00/`, `seedtest_a/` and `seedtest_b/`** all share
   `d96b3ebd…`. Identical files across nominally different arms may be legitimate — a
   reliability raster can be reference-side only and therefore arm-independent — or may be a
   copy error. **Not investigated here; flagged so it is not discovered later as a surprise.**
2. **`C45_s42_repro/C45_edge_ratio.csv` is byte-identical to `C45/C45_edge_ratio.csv`**
   (`0a7525a9…`) while its `C45_per_chip.csv` differs. Consistent with the edge ratio being
   deterministic given the same fakes, but stated rather than assumed.

## What is MISSING — the true extent of the loss

Searched exhaustively: every filename appearing in backticks in `tubitak/docs/*.md`, checked
against every file in the repository. **128 filenames referenced; 12 not found; of those, 6
are real losses**, listed by name below.

| file | named in | status |
|---|---|---|
| `blur_control_per_chip.csv` | phase-c-europe-results.md:63 | **LOST.** Table II blur row (σ = 0.45, −6.1% / +1.7%) rests on it |
| `eu_decomposition_per_chip.csv` | phase-c-europe-results.md:63 | **LOST.** Table II corrected-georeferencing row (~86% scatter) rests on it |
| `eu_per_chip.csv` | phase-c-europe-results.md:63 | **LOST.** The European per-chip layer |
| `veto_features.csv` | gcp-veto-rule-results.md:29 | **LOST.** The veto rule's feature matrix |
| `veto_rule.py` | gcp-veto-rule-results.md:29 | **LOST.** The veto rule's script |
| `B3_run.py` | corrections-log.md:80, headline-results.md:91 | **LOST, already recorded** as corrections-log **entry 22**. Four registered matcher parameters remain unverifiable |

**Not losses, checked and cleared:**

- `pd_36SXJ_per_chip.csv` (T3-reliability-results.md:48) — **already disclosed and resolved.**
  That document records the loss to the scratchpad purge and states that the data was
  **regenerated** from the C2 checkpoint rather than reused, with the regeneration fidelity
  bounded. Handled correctly at the time.
- `karios/accuracy_analysis/accuracy_statistics.py`, `karios/report/circular_error_plot.py` —
  upstream KARIOS library files, not ours, resident in the KARIOS install.
- `_summary.json` — a glob fragment in prose, not a filename.

**No Phase D check-3 or check-7b artifact was regenerated for this rescue.** Regenerating them
is item 4 of the current work list and is a separate, registered operation; this directory
preserves what survives and names what does not.

## Manifest

sha256, size in bytes, path relative to this directory.

| file | sha256 | bytes |
|---|---|---|
| `B1/B1_per_chip.csv` | `fb4703b23914dcbc384f491896a4c175d1413760e3ef5428f689d1c1644243a2` | 32,848 |
| `B1/B1_summary.json` | `e5460417b8f508d44c43e560f67a2be5dad9e22dd5d2183f675292b24751de18` | 5,787 |
| `B2/B2_per_chip.csv` | `335b077be011204af77688291bcc7abbcec771a6b9f0ae890acafb1c8ee1dbad` | 4,013 |
| `B2/B2_summary.json` | `4b76f4df19bad95aa90fa276b2b214bd731f8da888791bcf0f2eaf3d0a2da444` | 2,386 |
| `B3/B3_scores.csv` | `c7d4c71d4a5d7715fabe16cb15605891364952cf9b84d11fecc7f5bc1441c6f0` | 37,558 |
| `B3/B3_summary.json` | `d33f56d382b77624137c7d9a5289d7084fde181ec1f988511ea6b0f11d3b0416` | 5,018 |
| `C45/C45_b2_per_chip.csv` | `97be08b82678d0985884008cb1e892ae9ed5cc383370e5bf41b425b69f918a99` | 3,008 |
| `C45/C45_b2_summary.json` | `fa1a1b9648491483f9a7a16d9582af30c1e912b262acc161c11d7bd1eb595a4c` | 1,675 |
| `C45/C45_e1_per_chip.csv` | `19d125b3dfad96cd0655fb0da535d05efec85ea2620da18ee14aee288f74be22` | 11,853 |
| `C45/C45_e1_summary.json` | `d56f7e5043203a46386ff8c7f717bc79f4d6466eb8bed5c2015a1b9820efeb68` | 825 |
| `C45/C45_edge_ratio.csv` | `0a7525a9082079a74cf4af6e044a02c01eeda278f77cb544d8c8cc488f238a59` | 18,508 |
| `C45/C45_edge_summary.json` | `a06f94f37b762c391ebfd41350487784c9553548f32ec46c577e6a70d59c7972` | 1,059 |
| `C45/C45_per_chip.csv` | `fede1c5080ed91392c82aa394d9a98fc8764c3925b8d61b9d1bfd808236ab945` | 15,529 |
| `C45/C45_summary.json` | `2a31f70b8e46b3890419adb88f4df699dfd02aab3269060020f6593d4b12eea1` | 2,383 |
| `C45/C45_sweep_per_chip.csv` | `45dc469a4284b14eec47351ee8a0392a01598306a8209b90959a8bf70068125a` | 30,032 |
| `C45/C45_sweep_summary.json` | `b57f3844f602b0c7a0d0b47d83ad89d5b206f93856eb97d19ac1215205165ec5` | 1,383 |
| `C45_s42_repro/C45_edge_ratio.csv` | `0a7525a9082079a74cf4af6e044a02c01eeda278f77cb544d8c8cc488f238a59` | 18,508 |
| `C45_s42_repro/C45_per_chip.csv` | `be1360cd6a22233087e5baffaf00c448c118a230ba7e75ec4e94edd4239dd598` | 15,551 |
| `C45_s43/C45_edge_ratio.csv` | `526a48b6eacd17ee0dd934ea866b4ae93f7f21e6c00f6c843b2e56d00653b153` | 18,479 |
| `C45_s43/C45_per_chip.csv` | `20fc88e4ac3412ed46052bcf56b083438d18ec3990e8735ee44fef6743d4c192` | 15,575 |
| `C45_s43_modal/C45_edge_ratio.csv` | `ad1e1cdf18e75e19461e7b7f3714b175506be45fef67a101b06ca29cec4a917c` | 18,507 |
| `C45_s43_modal/C45_per_chip.csv` | `8e1db40d9a015eb3df74e4c46207de3960dd70adbe923e86b9a341990dac0eb9` | 15,563 |
| `C45_s43_modal_unsorted/C45_edge_ratio.csv` | `76e2b4bceea78a135f202dd0beb111c5572d4461efcdc9a3ad28c9efc53dbd9d` | 11,165 |
| `C45_s43_modal_unsorted/C45_per_chip.csv` | `40140b74c68c3ee5273780a11806749a7cba090ea6f89cc6ac1f159fa85f2c26` | 6,959 |
| `C45_s44/C45_edge_ratio.csv` | `ea4cf93aadf3d9ec65eea32daf85f793dd25af7791ef2919cb9ed9d93b49a6d3` | 18,487 |
| `C45_s44/C45_per_chip.csv` | `c30f9123f5c39cd2c5f9fe22c478f2276ded773a29fb733d84165638afe19b78` | 15,578 |
| `C45_s45_modal/C45_edge_ratio.csv` | `3492d8d1799c0d435ab97c8bba808995c4241d6278e93e58541ae918e33fae63` | 18,494 |
| `C45_s45_modal/C45_per_chip.csv` | `ac4003136ab30ab1ed8317e6ed0694d03a64c7c777a51d4fd04cdff175d68bbf` | 15,536 |
| `C45_s46_modal/C45_edge_ratio.csv` | `d55a8164652ef53daff78ae733aa911c2612a43c9ee80cdf986c920552be27b8` | 18,488 |
| `C45_s46_modal/C45_per_chip.csv` | `e1b838713a9e1743b03f6449c9827e415512e2e6b81e908b7d297b3359eb5f48` | 15,553 |
| `C45_s47_modal/C45_edge_ratio.csv` | `e5cb5b21eb19ad6943933b1d82edcb02ec0cde3464a4b91b7ea2e39ae826bee7` | 18,512 |
| `C45_s47_modal/C45_per_chip.csv` | `3c091ad0b4cdb5582ba6f87cf4467544971208c32a13ceb4be01bcae260349ae` | 15,579 |
| `C45_s48_modal/C45_edge_ratio.csv` | `d021137e06e742bc2ae17817a25fefed47d0b1cca7a48fb6a47cbb904015a5c0` | 18,495 |
| `C45_s48_modal/C45_per_chip.csv` | `9dc33fab0a92da262c055e30618a39b8eb5b988a059a3e2110e6cd0fcf9de193` | 15,546 |
| `C45_s49_modal/C45_edge_ratio.csv` | `d370868dbce96545b8e9ae97176c024bccebf180bbf9bb24b7c19ffcf2eec2cb` | 18,475 |
| `C45_s49_modal/C45_per_chip.csv` | `6b8b13ae1b43531d1f9c6a60abb7be7be838c9ff4c84411c074d8361c64ab3eb` | 15,555 |
| `C45_s50_modal/C45_edge_ratio.csv` | `a5a8b14a5f883ffafb0fa747ccbeb030b9028ecbcec4783ba6f82f504c042d2f` | 18,514 |
| `C45_s50_modal/C45_per_chip.csv` | `505e8f94a9f9710756e66c85813a228621833e183a6ffd45f978d931c493432d` | 15,536 |
| `E2/E2_summary.json` | `4dce5e1283d448792c60ec808ebace8f246a33ab13ca033fdb415b63b759567f` | 99 |
| `E2/gencp/reliability.csv` | `abf6000d40fd364605a831f0c60cfbd17d4bfe6ab664255ccebb3203b956f043` | 4,004 |
| `E3/E3_summary.json` | `5a365f013a6d735c6c14918a368b9e924a451a801c3f3eef0a83393727906106` | 559 |
| `E3/E3a_summary.json` | `31b44f1b3a40e1bbe333cd0b0e0518bc1fcb958342bcdd65b0f976ed61a53e40` | 397 |
| `E3/E3b_summary.json` | `93a22a79b57a57d803d311f8549f1ba044a3ff292321591164ed96e8da2674d2` | 475 |
| `T3/T3_curve.csv` | `5b56168122e33de22e23dd509cfeb3eda6761474de1e659e091636e82080de8e` | 852 |
| `T3/T3_curve_cappadocia.csv` | `1b675289502483b1a7c7020a6f840c48d04bc5f01e66a3da3e5378da96bbd374` | 197 |
| `T3/T3_per_chip.csv` | `0af48ff86aa6678f52b30f026b45b9242b53ce62207b8d5e6c5376d2fd2e47d6` | 23,985 |
| `T3/T3_per_chip_cappadocia_scored.csv` | `5041c53d0ba5fb83fbf2c17391b875085339831465c30e085c77a07ed64c31c5` | 17,102 |
| `T3/T3_run.py` | `dd97d22284bfea76bad3b56b32e1eaaa70961340ee5b62df8f5454d06332a248` | 6,010 |
| `_chip_lists/tiles36SWJ_eval_salt_annex.csv` | `e3f5d3f64842c888b2b4586f97caa0f5b371860a55e7960b1eb9c7987a831e30` | 2,829 |
| `_chip_lists/tiles36SWJ_eval_selection.csv` | `93e4d8ee6a46727aafd79633ffedb16d1acfc3018d281ffd86fc9847a44e0cdf` | 6,121 |
| `_chip_lists/tiles36SXJ_chip_grid.csv` | `546d98e6fee6ee9d39cac72107c81ffefda5854daded970fb8c00e3d67479f86` | 66,835 |
| `_chip_lists/tiles36SXJ_dem_ruggedness_labels.csv` | `21ae50dbf200bbe9e10da40d93769e9cfbaa27b720ceb52d37f8503b3390ba66` | 5,074 |
| `_chip_lists/tiles36SXJ_eval_selection.csv` | `b0ed0f05afa3888510eca3e0d60658648b11d2e97bd33de6a7ccfcb6c6f51587` | 3,616 |
| `capp_c1/reliability.csv` | `d84036ac57ceb5543c18e9b5a9aaed80e66d8570d4aec30395074bb12115622d` | 1,131 |
| `capp_c2/reliability.csv` | `d84036ac57ceb5543c18e9b5a9aaed80e66d8570d4aec30395074bb12115622d` | 1,131 |
| `gate0/reliability.csv` | `8a29385c6b845b0501fa9bd1db566f6f0daf5ba65091c560e2b999986f8a10ef` | 225 |
| `gate2/30TXQ_0830_00/reliability.csv` | `d96b3ebdfc7aefb4fe3570126d77332ebc919afdc41fe7ef944c83b5aa71bb62` | 138 |
| `gate2/30TXQ_0879_00/reliability.csv` | `be0935d20274638587d40525567d26076fb8a03d7530745432249d65daeeda4b` | 141 |
| `gate2/30TXQ_0934_00/reliability.csv` | `8831e6a3cc15e753dff9eebccade38f840fcfd8556ceb3ef6e3895dd603885ae` | 148 |
| `odtu/reliability.csv` | `a559d7e9b1561a8c9f491a2c583370c719d7a9a1cfd43812f55b9947e0582a4e` | 1,361 |
| `odtu_c1/reliability.csv` | `a559d7e9b1561a8c9f491a2c583370c719d7a9a1cfd43812f55b9947e0582a4e` | 1,361 |
| `pkgA/pkgA_report.txt` | `a918e8670cb5e4792f324ace65835745e6902c8abef7d4e3380aca466dec8486` | 9,488 |
| `pkgA/pkgA_scores.csv` | `2d8cf4b0794c4cdaa14fb7651a4e0152f3c3a9fb066aff5bf5556f8112f2553a` | 354,087 |
| `pkgA/pkgA_summary.json` | `b777ed050ccdbea2c6e96d64f6741fb6627cfaed3d8de3805ab96d69426249f4` | 33,331 |
| `regA/regA_per_chip.csv` | `ab0dab756769587d82e85d66d939706c7f166a76a831dc94b54cfc8b7ad95867` | 10,498 |
| `regB/regB_per_chip.csv` | `55ef40b8b538b04dbe649fd6db810527aea52443c8f8de2c987349851902b807` | 3,807 |
| `regC/regC_per_chip.csv` | `91deaa0bcd04cc820467edc9f4fada1347660a3e831da0284b7ec374f3e75284` | 70,614 |
| `regC/regC_summary.json` | `66f1b2310655dff0911a6ef231b17e3c713741f0197a1ad072db4e5ccdae668f` | 10,624 |
| `regD/regD_per_chip.csv` | `aeaf22158d2fa10c1e55e897842fc7aef73ddadee303ab09e9d558d68d6c1124` | 70,612 |
| `regD/regD_summary.json` | `c1e343ec3a2aef03c0f02620050b766af3270a1d00cce0a8f6c19b7f9fdd589c` | 11,663 |
| `seed_eval/seed_per_seed.csv` | `56838567799c33af1cf40f8137fa709a93502c9454ef8ed8748593686e340af9` | 959 |
| `seed_eval/seed_summary.json` | `858b5ec36821292ec4604f1bc14afc9e040a24974a5c90d4b6268c793403a2da` | 10,273 |
| `seedtest_a/reliability.csv` | `d96b3ebdfc7aefb4fe3570126d77332ebc919afdc41fe7ef944c83b5aa71bb62` | 138 |
| `seedtest_b/reliability.csv` | `d96b3ebdfc7aefb4fe3570126d77332ebc919afdc41fe7ef944c83b5aa71bb62` | 138 |
| `task2/ov0/reliability.csv` | `61c33863df235f16f0a0d3746cc145899f5f25c1751184fc3fdcaa1f6c221fda` | 785 |
| `task2/ov160/reliability.csv` | `1bc4896640e53fcbdb76c7a655a3e70b178fb300d731c69c2065293287821613` | 1,327 |
| `task2/ov320/reliability.csv` | `454e79c92ee0aec487e669ba97a0cede7b959e44ad355c315348f43236568d9e` | 1,340 |
| `task2/ov640/reliability.csv` | `f4aba75ffa2a255de450657a7f458647fd3186840cc5f88cc811aefdd56c8d1b` | 1,347 |
| `task2/ov960/reliability.csv` | `1718584916611e90ba3b43231c5911e9191ff78833838ac24cb547715f2905f9` | 2,075 |
| `task3/task3_per_chip.csv` | `46eeb60678f920a90cd9286de80694781788badb3ed8f508d17910fe69bee7c9` | 6,367 |
| `C45_s43_modalwarmup/C45_per_chip.csv` | `736bb74648d9bc01650aadc01a403d8642b1aa31613a0d8983828844d310c970` | 9,834 |
| `C45_s43_modalwarmup/C45_edge_ratio.csv` | `f124f9c800cbe2238594472d56f563c7062fd795ab8f1ebe3ebeea50599ec62a` | 13,598 |

| `common_support/common_support.json` | `4998dcc9de15a6e03d26836e7c39e615bd921774c363c7c35fcd6e02c0aecbce` | 16,427 |

**83 files, 1.4 MB.** (2 added by the LR-confound probe, 1 by the common-support re-scoring, 2026-08-26.) (2 added 2026-08-26 by the LR-confound probe.) Regenerate this table with `shasum -a 256` over the directory.
