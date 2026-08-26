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

| `input_render_warped/ank_0_10.tif` | `a1ec648f716f29cb1a9e27dc8f178457d9b1ff0edcf61e351e7fcca4d0389d20` | 156,450 |
| `input_render_warped/ank_0_16.tif` | `a57de26d84885ccdaad72691c0e5c7ad06ba1e949779e3db32a9325946899ec8` | 156,450 |
| `input_render_warped/ank_0_30.tif` | `09002bc60df5d19282bab3f02928a00042ba64a33b5ad723b9ba9c98b75cd84c` | 156,450 |
| `input_render_warped/ank_0_41.tif` | `3c3016e86dbc401bb5c0e24089bfa799e6a9d079fd13a098defca11c1c06a1e1` | 156,450 |
| `input_render_warped/ank_10_1.tif` | `5d709b3aa077a1608f813e1ed9f7d97683c59f00c51ac360e91f725b546ba973` | 156,450 |
| `input_render_warped/ank_11_14.tif` | `cff9b9ec7a786cd2bd1d3486c7af4f439c0a9668434f0ef2e9c86983ef9b07d8` | 156,450 |
| `input_render_warped/ank_12_21.tif` | `af9c807b3f1a80b996138077deaab5008fce117d93bbacff695946b3cad5c062` | 156,450 |
| `input_render_warped/ank_12_28.tif` | `9ff1e9faf0ad6dc94495e7d4628f2b4e4d19a919e37687c6f8c271699dadfde8` | 156,450 |
| `input_render_warped/ank_12_35.tif` | `61966dc4967bd9383dd204327225578f06f656af02b6c5d93d6eed85aeb81b50` | 156,450 |
| `input_render_warped/ank_13_12.tif` | `218294dfde73d57633f7fb8103fea416b6c299d619bf527a7c7c890109668e03` | 156,450 |
| `input_render_warped/ank_13_17.tif` | `81d37771398563099c13276930855cb366a54e2b8b9b86a26f47c42dcb7a91cb` | 156,450 |
| `input_render_warped/ank_13_21.tif` | `60f9c17f53107361602daec0033772abb6e5a02423054aee61b063d150cd9bd4` | 156,450 |
| `input_render_warped/ank_13_29.tif` | `a6091ed0c55e0ca7e46a2e8be162bd6cbf1e0e28a648b5633e74b4ec3e879d15` | 156,450 |
| `input_render_warped/ank_13_34.tif` | `a2893139a7255388760a429add322f5af391eee99506e65e94fff8e60d371a9a` | 156,450 |
| `input_render_warped/ank_13_6.tif` | `78ea5252c3d68cbb567f1cd0c5147a7ae623c9c8782eacb7f3955e945f853f6a` | 156,450 |
| `input_render_warped/ank_14_33.tif` | `3891384702d43eb88c2ee95416c7dbc23e368043afe20141dd865b4cb8db746f` | 156,450 |
| `input_render_warped/ank_14_9.tif` | `3370c4f8599b476ba2e293bfabb415042a288f27f144974b9dbf6836763ada7e` | 156,450 |
| `input_render_warped/ank_15_22.tif` | `d67a08633101ef7f4e2389ca8d25af9ea086dc32f719253cd43518aa21a4e122` | 156,450 |
| `input_render_warped/ank_15_41.tif` | `664418957968124a9c698eac7fd08edb819f397a4cfcdd536cdf4b11aae1ddd9` | 156,450 |
| `input_render_warped/ank_15_6.tif` | `4f52814d319a74430caadb8a5d870b760e8ffc51dad017a4f202e7d31e3242a4` | 156,450 |
| `input_render_warped/ank_16_36.tif` | `78f099b39e84a57b098f2b8c488d3de02f3acf51026eda61f06df5fe1c6952a7` | 156,450 |
| `input_render_warped/ank_16_9.tif` | `bafd7153ba6a59fb6b7b11d990276e071d2b2a4ff2a01a70a9d2dd1aee9edc84` | 156,450 |
| `input_render_warped/ank_17_17.tif` | `2913dc093bf345e678d5847fe43a3c52bfd958b78e564cd99f92f788e55f8be9` | 156,450 |
| `input_render_warped/ank_17_19.tif` | `dc5f366f8ecaa1d782b003b6bdcac6788ac6041a487981980543f76e31ac0eb0` | 156,450 |
| `input_render_warped/ank_17_22.tif` | `992310dc799861b966ee0ba469df13d2232e5e1c796e80980a62eea01ac577c7` | 156,450 |
| `input_render_warped/ank_17_31.tif` | `9435ad38d46d05c52ac41d6bd2c862c0aea25cc3991d6242e4824e8969860ba2` | 156,450 |
| `input_render_warped/ank_17_32.tif` | `9d850553e7e055e1ce44ce85120923c4008a133a9fcebcee5334e32bd092c872` | 156,450 |
| `input_render_warped/ank_18_16.tif` | `24d2b1f385c516e8c3f5f21663de849a0b868accf98bf29de12a83406e4e1a29` | 156,450 |
| `input_render_warped/ank_18_27.tif` | `0ef2978a2a380320b5226012079d7634b2f470fd1bfcd88710c7ed9c340fa21e` | 156,450 |
| `input_render_warped/ank_18_29.tif` | `b1c05258bc433a9dd472951e57f1b3a6e50c409912cc95214335967b3fca5474` | 156,450 |
| `input_render_warped/ank_18_37.tif` | `b7b19d559a8493f8ad6d09a2715cc0e02bffdd732ac25eb46a14159617c3c348` | 156,450 |
| `input_render_warped/ank_18_39.tif` | `4630b4e2318c20f12aeddcab7b63e4fd678baaeb31698528153bf1589f35929b` | 156,450 |
| `input_render_warped/ank_18_7.tif` | `765dbe5f9894db420a56a08e3e39a0fec375bfc93a64bb39518a97ee031bf065` | 156,450 |
| `input_render_warped/ank_19_15.tif` | `49fa237526cdeb825f59ecafa69c2ab56526e7c4b96d21398405b19456b1a9e9` | 156,450 |
| `input_render_warped/ank_19_33.tif` | `626c8e74302e1375f5476550a15d156e77b4c453a641f57f7b6a26b3087b864d` | 156,450 |
| `input_render_warped/ank_19_6.tif` | `95ac71742618513af3ee9a51cd2d0fecf0ce7181e9ae1e01648ad10beda6bbfd` | 156,450 |
| `input_render_warped/ank_19_9.tif` | `0e5158db83cb3ef778f2fc3bf36a63d8d5af35410ff83130137fb520a57271c7` | 156,450 |
| `input_render_warped/ank_1_34.tif` | `17557ab3a5ba8882b11f5337b76b52eaf45ffcd00101dcc24dded585801df406` | 156,450 |
| `input_render_warped/ank_20_10.tif` | `cfdadd41ce03c7a188016becb9f44b11f580decffca4c50d2dc71e1eb7ae7dec` | 156,450 |
| `input_render_warped/ank_20_19.tif` | `1552124174b1673c109e3fb09087f2a535795b07ba986d800554909669d7787d` | 156,450 |
| `input_render_warped/ank_20_37.tif` | `f0eb7e8a0ab3b90c477d16a19ac1ea25d2c9aa5516efaf7b59403f9b8ba12cf7` | 156,450 |
| `input_render_warped/ank_20_6.tif` | `12db93b537cd9fd31d4999b7c8dc9bde26e4d6c19df250168e80b84a3c6763d7` | 156,450 |
| `input_render_warped/ank_22_10.tif` | `7a378bfa9faf06fbd329e032114873eae147b20f14b2e359d945058a36bb8a95` | 156,450 |
| `input_render_warped/ank_22_16.tif` | `d709c7bf1dd2e5fabf30c516455bfe206cdfd5ef054e7ad577c975801a4779fa` | 156,450 |
| `input_render_warped/ank_22_37.tif` | `4ede902b34f6c6f64286f2c31099579ca2ae9a88b2663315bcfa747641670eb5` | 156,450 |
| `input_render_warped/ank_23_14.tif` | `e998bb0fc0203063309e2a823dbc5a1c338d2458b796e7405ef31161f438fed1` | 156,450 |
| `input_render_warped/ank_23_28.tif` | `d081ad1e1240174e3e14408cc204882c647c4e05cf1ebe5c33708d5cdb182e85` | 156,450 |
| `input_render_warped/ank_24_0.tif` | `6ec4767ee613b70c221f3212a84238459bd0f857246fecd636d9404d69040709` | 156,450 |
| `input_render_warped/ank_24_12.tif` | `219bcf7abc2a67f09d5de49f63b82a3234a5340c8ec30594e68ce6a73289f048` | 156,450 |
| `input_render_warped/ank_24_14.tif` | `f604f502002747fa483e1843319a0479fe83a459f5c5b2036cb5fa842ab914ce` | 156,450 |
| `input_render_warped/ank_24_3.tif` | `77882d5a522c8fe0300f510d8dceba308f7f28185689ae2410aaad1d88c37fd1` | 156,450 |
| `input_render_warped/ank_25_1.tif` | `f5aab02c8594dd0cb3997c5ab2b45969ffe2fe31ca85a5bb06546acf7a8315be` | 156,450 |
| `input_render_warped/ank_25_14.tif` | `0b9bebf83a53b559a4f477bbf4b0987c03f87aabb18db1d1b42b0720743d896f` | 156,450 |
| `input_render_warped/ank_25_16.tif` | `4aae0a398adf6fa73f740cced392c4127ef1504831afb95e9777a0c3b57e8afb` | 156,450 |
| `input_render_warped/ank_25_37.tif` | `9017d54cf3de435a73cd513200665d26265ddbe2e6b2e7d9d4f962696c5245e5` | 156,450 |
| `input_render_warped/ank_26_21.tif` | `5bf341c1ed0b21a8cb6b1c3496cec0a018c6f5acc0f23289506b94ab163ef23d` | 156,450 |
| `input_render_warped/ank_26_22.tif` | `603ca8187d9b367f7d5b7cd86adcfd559364d126c9a2d97ea3caa8f70708b1da` | 156,450 |
| `input_render_warped/ank_26_29.tif` | `87ca3db3ed1ae8c573759af760c08f4e7265168493eeabfed3976fe0d4756a8c` | 156,450 |
| `input_render_warped/ank_26_3.tif` | `09b1e67761c4d990fa7495c6c9b448eb15b2fa673c696ea76bf46f83a6ebc4e7` | 156,450 |
| `input_render_warped/ank_26_35.tif` | `e9409175c65f1d12f3646559431e4cbe1bf0b636a35f6354ddaece6bcad8fbaf` | 156,450 |
| `input_render_warped/ank_26_5.tif` | `2a476004a7e4e3966864ad29c850ffef243ad797b1f046546d69d61fa166ac35` | 156,450 |
| `input_render_warped/ank_27_14.tif` | `129d453ee83d453a9bd4a3a18b19381d67087b71c6d618aba0d65602721c4afd` | 156,450 |
| `input_render_warped/ank_27_40.tif` | `345d8244593c69dbee5ce4f7450d1c7902da99aae35f61ef810238c11422fa86` | 156,450 |
| `input_render_warped/ank_28_27.tif` | `8749c9ea443c44c0221d74e853492d26a743d0fa21c4795a5452a8020ed1f0d0` | 156,450 |
| `input_render_warped/ank_28_37.tif` | `515dd65fddfe85676bc829db60b454d9973119263322d674ae7749c3a8a3c3b0` | 156,450 |
| `input_render_warped/ank_28_38.tif` | `faf1e5bb92bf9cf2451eb44d1f4cef637a22b0c965aecd3b91459d993ecebb90` | 156,450 |
| `input_render_warped/ank_28_9.tif` | `94019f3bc8cb36cb75fc6770174d2da67d31ecb2aba5637934c72de109a442b2` | 156,450 |
| `input_render_warped/ank_29_0.tif` | `2a9a58d96bf9d79e1c45908e57acbc975faa0af0153173dc7ebe39cba184c96c` | 156,450 |
| `input_render_warped/ank_29_11.tif` | `6078eebd689350c4ab10e6a6a486b36c391f8d822cd4ecd41b00225083b091b5` | 156,450 |
| `input_render_warped/ank_29_21.tif` | `5b687224f0943e21c0c1da6a11c5bd514bb0121b6f274ee7d8c7f8ad09f73018` | 156,450 |
| `input_render_warped/ank_29_24.tif` | `01aa02e0e6975109f9a74e2fb4e313a9240146f8db9b77a04b28a5f8386a3729` | 156,450 |
| `input_render_warped/ank_29_26.tif` | `a5ffb74ddf10f0e309394bec31296a010a79c361430fc4cc1aa0ad9375687650` | 156,450 |
| `input_render_warped/ank_2_12.tif` | `9a10ec0610e1be1d73a9662cb9aba2fac7ff39d2b11b8483ce8857b40b9823e0` | 156,450 |
| `input_render_warped/ank_2_23.tif` | `51e8fc50bf2430e5af657d5a0e7baed0ef07bc4dc831622a4407ec8d34011720` | 156,450 |
| `input_render_warped/ank_30_30.tif` | `5fc4195f1f3d4142480095a500d0ce06af7454513cba84d5fc3e3f9cd5044812` | 156,450 |
| `input_render_warped/ank_30_7.tif` | `1f43405cce70af51a583b723dde1278f48100196e8ac67e4b88564c520018902` | 156,450 |
| `input_render_warped/ank_31_32.tif` | `c38c5c8aaaac8c2e0edf0ffcedd625b9da9c08263fc16d422e331091f67ee376` | 156,450 |
| `input_render_warped/ank_31_7.tif` | `ff8929c53909af6d46f7614fe36fd9e7b56ecf2aa1481721f6db215016112f68` | 156,450 |
| `input_render_warped/ank_32_12.tif` | `c5241a2e08b9f78705c72ca0778e8a6b71fb7ada6d7809d04bbd1b8906d4947e` | 156,450 |
| `input_render_warped/ank_32_21.tif` | `5116210bc90ae5802c73ee61fe0e351051f8d4843d1291391b6e0623485e5b76` | 156,450 |
| `input_render_warped/ank_32_37.tif` | `71ec522f04ff8a28343b14a1a85cffbec4162f2965f34afa56e956746e66eeea` | 156,450 |
| `input_render_warped/ank_33_25.tif` | `d26a2566775792e9db6a288a4f727b8360ea8145097aba38fbf1b713f701960c` | 156,450 |
| `input_render_warped/ank_33_3.tif` | `9a50b22ca0dae336a56a7450fc2de0e822f8441afed573256fb9cb690479303e` | 156,450 |
| `input_render_warped/ank_33_34.tif` | `e970027615fe3c65352c10adecb669b13335a2db37a0d83aceb947c3469cbd14` | 156,450 |
| `input_render_warped/ank_33_36.tif` | `c6b7d843a64dafccb962d93c5b4815e3cc7bec5863b05704c0ba6a5d1225e49e` | 156,450 |
| `input_render_warped/ank_34_11.tif` | `6b25bf0c44d9f910644c6fc6ae85de18177bd0619b4e7cc33b58912ad1311f22` | 156,450 |
| `input_render_warped/ank_34_15.tif` | `fc18d2436d69fd5adf338a2601a11d251168f0f81e0b1b28e5effd13e5143fb2` | 156,450 |
| `input_render_warped/ank_34_21.tif` | `b31b3d5becc8f664782d75e23136b6eeeabc96a41b48ff724e843603d066753a` | 156,450 |
| `input_render_warped/ank_34_30.tif` | `48e07de307f27d01d761fd7f22fe2be25ca4f30ce6df17a802ba7ec4658c8f7e` | 156,450 |
| `input_render_warped/ank_35_11.tif` | `537ed05c4e8877c96e504bdd18d3bb2c25d3954821006b5d2007810b68e701ec` | 156,450 |
| `input_render_warped/ank_35_28.tif` | `757a1c1d0bea3041b03d99013dbbf33bb863c722eb5061d097a9441d96325170` | 156,450 |
| `input_render_warped/ank_35_39.tif` | `b87485fcdfd6bb11bdf6ccf3d165ed5d907ba8365b8bc6c9e4ccac4124f7b699` | 156,450 |
| `input_render_warped/ank_35_7.tif` | `e6e59defb5a8c182a0b799c2b597ffda62ea1542c6d3af663d8c2b9baddc87fd` | 156,450 |
| `input_render_warped/ank_36_40.tif` | `0e86d5e3801de3523cec41840900cbf111d2829e9656352b20fe6600f3ce114f` | 156,450 |
| `input_render_warped/ank_38_19.tif` | `1822d8a4c069de477b415f0f1d187e9857c1a9b9eb9e0b5a0bf689bce7fb9d87` | 156,450 |
| `input_render_warped/ank_38_22.tif` | `8bcd7457595028045c7235bdf7ab25786f7cffaecf74f65c94e18a0c1439ed71` | 156,450 |
| `input_render_warped/ank_38_24.tif` | `60ab62cc4736cde71c743bd7ccbb6692af2605a276502f6ddb43f77fe77eb294` | 156,450 |
| `input_render_warped/ank_38_27.tif` | `28dc28bd44fa165dbd8c7e78d0271a290d4c4825856ae6211f6079f83c7cccb4` | 156,450 |
| `input_render_warped/ank_38_40.tif` | `79b6eefe78cbccae8b5cfc0b407e02b9418a4b99b4712fdc8493da565c4e1bc1` | 156,450 |
| `input_render_warped/ank_38_9.tif` | `2dada7d51cd03d9aaf3db24f5593453cf41fd6c843b9b72e7cfa5633ef22a9da` | 156,450 |
| `input_render_warped/ank_39_1.tif` | `5993e690ebc72db63bc2685141a4dbcf154f22c7bffd2b7e21b448953ded5f26` | 156,450 |
| `input_render_warped/ank_3_13.tif` | `8ceda796cdef2285849ae80e205dca40ad81770f79f8f33a1f0e87619e450920` | 156,450 |
| `input_render_warped/ank_3_25.tif` | `39b04eb8f823512a83610decad556c7161a917001940356ee6ac42f5caeda2a1` | 156,450 |
| `input_render_warped/ank_3_29.tif` | `0896d6da0bda82704840b24934303c8a7ab0f4676da46ed8223a506c41ebe97c` | 156,450 |
| `input_render_warped/ank_3_34.tif` | `684f845b82bae4377feb0afef96061c47a7d6f03829d0571736412df0892ed1e` | 156,450 |
| `input_render_warped/ank_3_39.tif` | `ca8df7d9ba1748e4002281cf3f86c9b77936426a8c27396823af77ec1cd9176c` | 156,450 |
| `input_render_warped/ank_3_9.tif` | `37f32276a96db34fd39af20a3896b0b51ad9ccd91775374f8e12afb46c1be0fa` | 156,450 |
| `input_render_warped/ank_40_19.tif` | `87c99d69d43c5aebf0e7a2c016a5c2c586945a97a283c576216d1a9f08c3c440` | 156,450 |
| `input_render_warped/ank_40_2.tif` | `635ea772d02e155d0fb19d91e9e56b29091dc2bfaf5651a96eb87a2f61cf48f1` | 156,450 |
| `input_render_warped/ank_40_40.tif` | `99bb18f7f57b957e4dea72d53630ed5f55b15f859b12a58ee502c807f84e7e6e` | 156,450 |
| `input_render_warped/ank_41_0.tif` | `6ccd0c1035d5a2a153e9c3257800b0179276972a9ceb98210bcffbf33e1e8a54` | 156,450 |
| `input_render_warped/ank_41_1.tif` | `d7b8bbb3ba8694d2ef14e5743122986546adcb93d4305a8701de3fb64958f70c` | 156,450 |
| `input_render_warped/ank_41_19.tif` | `4235dbacca6934560a4eb102f415949e3b5b80ab5a28073331dbfe1d26f0d7bc` | 156,450 |
| `input_render_warped/ank_41_40.tif` | `ec5c207b5354a453b0d4250b1ab4198dd00fef4d3c462cd1323b1678c1b2a8c8` | 156,450 |
| `input_render_warped/ank_4_23.tif` | `d63fdea8392f9e4331b30d408c48797e6b11bf48716653825001838af36132f5` | 156,450 |
| `input_render_warped/ank_4_41.tif` | `95a31f20088c4ebeaf9231589ddbd5008ab8a101766200d4f51bc8d5e8fba740` | 156,450 |
| `input_render_warped/ank_5_12.tif` | `5e5dcd7d66765d58f6a7677f02bbd919932ed7d0cb5e3c2cfb9139ccf5a43a8e` | 156,450 |
| `input_render_warped/ank_5_40.tif` | `46f70b1a7b770f5277902fc983a7af4a3b86e0f23151db02a0fed3312ccb2170` | 156,450 |
| `input_render_warped/ank_5_5.tif` | `f1293649d12ff51593406b54bc1eaa06da7c3ed686fc4f5cc0d60af08bfc7c80` | 156,450 |
| `input_render_warped/ank_6_10.tif` | `d88d104618c122727f43075cb1f9d071657c63b2ebc6ebd740816e45a36232d1` | 156,450 |
| `input_render_warped/ank_6_38.tif` | `d4ede48d5a62b54f97d285acc9ff5d46a896d55c0c7a0ac7e6992a1451373265` | 156,450 |
| `input_render_warped/ank_7_36.tif` | `7738dbf0e6c02707a62971124afe4fa260423b5fa356484ad4660bcea8f39f94` | 156,450 |
| `input_render_warped/ank_7_8.tif` | `93d4365997820b79879fc30f1dc1ec6e69ef780ad2b9e00dec158a57cbc6f5e4` | 156,450 |
| `input_render_warped/ank_8_19.tif` | `4387fe426868549436b689aaa429e023f6a81ef44bdff9715c927e25c1f3f079` | 156,450 |
| `input_render_warped/ank_8_22.tif` | `7d4a4f3fc4e35a5c1f27e497c84f120a54080bcd12bc79355493e3fbdd58da07` | 156,450 |
| `input_render_warped/ank_8_31.tif` | `370c305f41ba4cdba0e4901a6591422665e8995c60c6c0606ffd95dd6608aa5d` | 156,450 |
| `input_render_warped/ank_8_41.tif` | `4e93046960739122d1414bf1c7563d961e7e36695f88c2609ab888605319c2e8` | 156,450 |
| `input_render_warped/ank_9_1.tif` | `8d88e2e579b2bc02309a9883d90a476339e587665b6616019dc4ea2085da819c` | 156,450 |
| `input_render_warped/ank_9_24.tif` | `e33dc776e1757b1ca4b4e9eb74d3e992a42711045914b9eb0ed1747fa61ab6fb` | 156,450 |
| `input_render_warped/ank_9_25.tif` | `9a7dbc84f0f2945105964bb779aeb652b653e29179fbfedb5efa4510104794ec` | 156,450 |
| `real_chip_bt601/ank_0_10.tif` | `a6cd59f5e67fa18515312dea2bd90a244c1d175e7a14d605dc07a13ffcc6ca38` | 52,386 |
| `real_chip_bt601/ank_0_16.tif` | `546bbf685f3c932a46daa3ea447eb968d5437bead477a9f6041c60d88d0b201c` | 52,386 |
| `real_chip_bt601/ank_0_30.tif` | `5d4e296e319e6cba2f888b95fcf57c22cf7ca7f1146b4b42ee08cde7ff9f5039` | 52,386 |
| `real_chip_bt601/ank_0_41.tif` | `b813d5e22717c4f8ed8b8ec27044c6c44ca22e91de23e854904d76a6060c1309` | 52,386 |
| `real_chip_bt601/ank_10_1.tif` | `2061c2b8a941d39cc61a9f4523377d213b9fe63b2f13abe58453c9eb0330ef90` | 52,386 |
| `real_chip_bt601/ank_11_14.tif` | `b38c37b37393a5731014a42b6cea6f692e3714515e368fea60c2d373f5c2aa73` | 52,386 |
| `real_chip_bt601/ank_12_21.tif` | `2977f113c15026f231fc77fdd458a57a0ca802b23183d213c108ba3f4bccb207` | 52,386 |
| `real_chip_bt601/ank_12_28.tif` | `26ad932b3c7165ac77da5dabea1527294a1c272e25245dd9e98bf6d348199124` | 52,386 |
| `real_chip_bt601/ank_12_35.tif` | `f3a9d0e6dd2635414a0ae2177ee34cb8fac7d8d27e549de4bf4dfbcb2963aa92` | 52,386 |
| `real_chip_bt601/ank_13_12.tif` | `05266c1d68c4e791d27bb7251d7bb155ce185d413e9e4e2abe5032660035f0e5` | 52,386 |
| `real_chip_bt601/ank_13_17.tif` | `22958cbef2d9d2acde94c463de893ffb48dc353ba9006a61fe06e6179b152907` | 52,386 |
| `real_chip_bt601/ank_13_21.tif` | `39e88cccaa83656046ca4e154f987890b095e5ad1e2533136b859d42c9874fc3` | 52,386 |
| `real_chip_bt601/ank_13_29.tif` | `6073425b2e6ed688c01550085fbcc37d2e1f3ee3b0d458845860168bc7e80c6f` | 52,386 |
| `real_chip_bt601/ank_13_34.tif` | `8d73c5dbd505066f07082c9aed448afd787e5645e0e2e0b19aed3e8475626a96` | 52,386 |
| `real_chip_bt601/ank_13_6.tif` | `f85121a14b7db6dab5bbb2001eb12883220c3fd8db3f479f3d4b39bae3da1a07` | 52,386 |
| `real_chip_bt601/ank_14_33.tif` | `bae6714c906a970637e376bedf91707b286836264debdcbc5e889c040399589b` | 52,386 |
| `real_chip_bt601/ank_14_9.tif` | `7ac2ef584497b204bb00aeaca6487f212165ef33f0ef0fa1849a7e5e4dd51c61` | 52,386 |
| `real_chip_bt601/ank_15_22.tif` | `bc7b0b65c99f9bf6ac0058b09f4394a5f1dd8d61ca2aafed20dfe36706737c8f` | 52,386 |
| `real_chip_bt601/ank_15_41.tif` | `e3ace58bddde4e6fde87c547485c87a5b2f62fdb950f05d8cc31c1db446fef7f` | 52,386 |
| `real_chip_bt601/ank_15_6.tif` | `1ef194fc8c152eca1512e9164e5ca07205e134a60038ba70c8692ebf0b1cc15e` | 52,386 |
| `real_chip_bt601/ank_16_36.tif` | `4ba07f659d87ff99f3e9cc4fd55e4621ce19306f9b65829631883a0abd38551c` | 52,386 |
| `real_chip_bt601/ank_16_9.tif` | `45178163fad307211fd2bb18f7793cc9e71a07037ae450e987c25723fcc98420` | 52,386 |
| `real_chip_bt601/ank_17_17.tif` | `c243c4a011d0965e4f1f21c3d0dacd636f957b5eb9b447deb11fa5f78a1b5558` | 52,386 |
| `real_chip_bt601/ank_17_19.tif` | `ff7409ac805d3229f46b68a0a05ce11553757651fe3c8dcd543271e894570008` | 52,386 |
| `real_chip_bt601/ank_17_22.tif` | `81453a78319c14162968da6917785362468b506fb9d39753333553ed830d35fb` | 52,386 |
| `real_chip_bt601/ank_17_31.tif` | `a527dd1e0389d9d7296f1cec5e2fd47701bf4d3b7d3c9fda46d8edfb39b465cc` | 52,386 |
| `real_chip_bt601/ank_17_32.tif` | `ef5a43264ec48885a123681943f4e3bddd53d2abb5e2c606bae79e20423c20bd` | 52,386 |
| `real_chip_bt601/ank_18_16.tif` | `17b6979e8f820aa33b3cb93328f2c74c031a04dd13497cdda0dbd4476ee5a8e3` | 52,386 |
| `real_chip_bt601/ank_18_27.tif` | `6dc3cd32d9c3ea54a7bb6eef12a6f6e677f4997a9c2798992f366cf244f15e2c` | 52,386 |
| `real_chip_bt601/ank_18_29.tif` | `cefb53b2a3d835c2532f94323394eefedd3d1d78989ce5e56d3bfd584d0f560d` | 52,386 |
| `real_chip_bt601/ank_18_37.tif` | `e1282590c1568a6b13dd7664c18495ebe55d2ed27fe2900adbf2b30e51e7aec8` | 52,386 |
| `real_chip_bt601/ank_18_39.tif` | `00a2158b51b3ef20fc01a391509b0ad818a0cc9c8dd593332c85a1c466453ddc` | 52,386 |
| `real_chip_bt601/ank_18_7.tif` | `314a9af4016febabe5bd419d1a11a22380df26f71ff09c19160692de1d237498` | 52,386 |
| `real_chip_bt601/ank_19_15.tif` | `9f76a5e370fabc068875af5bdff24029d85f7f0d6d9293c98265a60bd8edbccc` | 52,386 |
| `real_chip_bt601/ank_19_33.tif` | `7617a3ee7f32a71a8e566c1f0778d2e07a831c2ea01cd81e1dbe9804cbd8fba7` | 52,386 |
| `real_chip_bt601/ank_19_6.tif` | `c00ec8cfafb415016174161829d0abf810392f45989d3f0702c67461a0604981` | 52,386 |
| `real_chip_bt601/ank_19_9.tif` | `45f02efccd2607ed94976f2b484782ffec26801accc9e735df367d80e5d1bd92` | 52,386 |
| `real_chip_bt601/ank_1_34.tif` | `3d8ccfb05ad585ebae07a48291e64729e304419f596e844d354b651ad37dfe1d` | 52,386 |
| `real_chip_bt601/ank_20_10.tif` | `9022a5bec0916396d8187eff44bdd475cf8af3f30cbfa80151f59017700f572b` | 52,386 |
| `real_chip_bt601/ank_20_19.tif` | `c824b2b14c001b249618e73f2889f38874159f65807a4860862ca83d7ac25b47` | 52,386 |
| `real_chip_bt601/ank_20_37.tif` | `1b84398caf8b1ff0455ddd0e33771e971d41cfc54aca034f8c78a098439878a6` | 52,386 |
| `real_chip_bt601/ank_20_6.tif` | `b7c39e0132b3c34398bf46cbb6b10e0e0500d30fc2698f506cec2f826d2e9e87` | 52,386 |
| `real_chip_bt601/ank_22_10.tif` | `392713b2f3945b3ffbe7fd25847bb05467dcaafde7804a9d71421209818744a5` | 52,386 |
| `real_chip_bt601/ank_22_16.tif` | `1836bc28f02085f540bf0dd8e45be11e071b4d11039dfd6caf602f6452b01e85` | 52,386 |
| `real_chip_bt601/ank_22_37.tif` | `5cde6e8f03cfb2364823d0c7db246a5040a5df4705b84ca6c6bb23b6ed5b8197` | 52,386 |
| `real_chip_bt601/ank_23_14.tif` | `4a902a48479b98a508c659e3888fbe3dccc5afd893be0b48b724c44a2281c397` | 52,386 |
| `real_chip_bt601/ank_23_28.tif` | `ee93cf807af33d2e37e0b9fc6a0036e274a76d2705ecd1a4f46e4eaafd0d340d` | 52,386 |
| `real_chip_bt601/ank_24_0.tif` | `ef5e054127aa5ba8f6a9221ae02cb80b740146ce77b02992818b3cc506fd558d` | 52,386 |
| `real_chip_bt601/ank_24_12.tif` | `5a0817a54a020e022cb9f9a87544768ca40005cd8329c6ccfe212c564a9d3e78` | 52,386 |
| `real_chip_bt601/ank_24_14.tif` | `48ddf217d30bb0502134d4e2250ebfd3d52b0b5fac66b1bf5646beb1cc69dcc4` | 52,386 |
| `real_chip_bt601/ank_24_3.tif` | `34e9ba9cf89a3bec4f802f021054aa8408d51e33f0fc64cfc114d28813a1a446` | 52,386 |
| `real_chip_bt601/ank_25_1.tif` | `fef3bef96a129295f95be8ac8c90b35e51a1863a3aa2ea0c4dab14ad570efa9d` | 52,386 |
| `real_chip_bt601/ank_25_14.tif` | `658d002d5bd1d0fbdf973e0c5f1186a53f096fd1c14d55579822e17a00d95192` | 52,386 |
| `real_chip_bt601/ank_25_16.tif` | `ab402cef34433efcca9b0068846b89ab7daaf04a3cf1aff534e67f4ca0e7a975` | 52,386 |
| `real_chip_bt601/ank_25_37.tif` | `b4324d31d8cac5e30e0c4e37ff7c454b64cbdad651e7c1e9c2b4c6dcd234d1b9` | 52,386 |
| `real_chip_bt601/ank_26_21.tif` | `31ff58b26539dbf0f783c8bda22723b462c9cfdb3e1245229ac7d1f96c0cada6` | 52,386 |
| `real_chip_bt601/ank_26_22.tif` | `d6d3f269d75012630075459ba71b19b90b984da5a147a8c2615fa263387ed3d6` | 52,386 |
| `real_chip_bt601/ank_26_29.tif` | `18e308759680e83d04e625fceab65395ae0919d37185ec7e391bb049f2fc4f32` | 52,386 |
| `real_chip_bt601/ank_26_3.tif` | `0d1e72953d8ef4f05f0fe728b47dd0874d302547af1aa074ea7b6c148fd48f70` | 52,386 |
| `real_chip_bt601/ank_26_35.tif` | `e2b0a50003b966d72f9f0dfa9ef1d4dcf28633e45f73edf78b976ff5b149c8c1` | 52,386 |
| `real_chip_bt601/ank_26_5.tif` | `f24fde88e19c95e84a73b26b234f15fdf90b9d7c8f98d05c12b99589ff0ec438` | 52,386 |
| `real_chip_bt601/ank_27_14.tif` | `9b82c47e349e2d8fb93b83226313ff275224cbde024ba707e7036b8c7d3344c9` | 52,386 |
| `real_chip_bt601/ank_27_40.tif` | `7fd9d51eae39b0cdb71e3e5231e093f882c4545e898a63e21c5edb51213b0a06` | 52,386 |
| `real_chip_bt601/ank_28_27.tif` | `d446805ab894c60a4279062347cb9af50a408511f5606b936ea0a9851ab3d9df` | 52,386 |
| `real_chip_bt601/ank_28_37.tif` | `6ad04aad81af37c67cf0e2a7e6759133ff4834c854fb8976f5d6e1de9e74f83d` | 52,386 |
| `real_chip_bt601/ank_28_38.tif` | `d4ddb6f222e2000568378c596b10c789eae64d49983a014dc6f5a094fb86b6f1` | 52,386 |
| `real_chip_bt601/ank_28_9.tif` | `f2607cfd94359d5ed00b47fc6165948bf7c9300a487c127fd7fc6255847af0df` | 52,386 |
| `real_chip_bt601/ank_29_0.tif` | `93a0382aec9fa0202fbdc7ef27836f21687ce8b5472fb7a4dbe46d84d7878297` | 52,386 |
| `real_chip_bt601/ank_29_11.tif` | `e5dc0a789740a6a36c73386428138a02f8b9afb9ea889dd0ccaa4184fc3c52a7` | 52,386 |
| `real_chip_bt601/ank_29_21.tif` | `0f23d9cef356821984d151d0dcfc5569dead62fc004a234d97a2faf22c630339` | 52,386 |
| `real_chip_bt601/ank_29_24.tif` | `cc79185d7a0d44e4038cb4ffb1e91cb77cd0c4d6663009d0c884d568523b95f9` | 52,386 |
| `real_chip_bt601/ank_29_26.tif` | `07db248bba925e5fb79ad7d28bff27b79650c8e1ad07ed03940c6b11d1d1783c` | 52,386 |
| `real_chip_bt601/ank_2_12.tif` | `9f094b9a451033d5f6eff61694e58f0162f2f21900231e3a0737ddc9a1a33ac0` | 52,386 |
| `real_chip_bt601/ank_2_23.tif` | `b18690f1771f4dec282ae06a021ca6959ca790b9a54b5df485d8ff9ee001bd81` | 52,386 |
| `real_chip_bt601/ank_30_30.tif` | `7d6b98d8cfd7b1f2788f580c712ad5c5824730d2a38b06be1169d7aef62d64e8` | 52,386 |
| `real_chip_bt601/ank_30_7.tif` | `5fb29c0e7c730b6cf8ff1a4a6e5c8147295c8cbc206a70cf102731c2472f94bc` | 52,386 |
| `real_chip_bt601/ank_31_32.tif` | `a12883a225dae656653f44626e4470d0c3963efe280ce10c47c1660664cd0ed9` | 52,386 |
| `real_chip_bt601/ank_31_7.tif` | `8d0333923181806bcccc23be8a790c3d72776638336b33aff5a00a33094f248a` | 52,386 |
| `real_chip_bt601/ank_32_12.tif` | `15aa7e9982ba517d6f2f5a9c09d1be6b9c4b06209f9f9414b0679c1019b817df` | 52,386 |
| `real_chip_bt601/ank_32_21.tif` | `9d7cba7242540cb478a8d595d9e2b446b48480c25d6f8969d9d2cb5cbd1d3e73` | 52,386 |
| `real_chip_bt601/ank_32_37.tif` | `d4ec20339cf6b1053115d82028b409f42873fc299cacdfcef50999484571877c` | 52,386 |
| `real_chip_bt601/ank_33_25.tif` | `c3ff4d13921c058e95cc85f625d919f907cc6d21381538db5db2546c98227888` | 52,386 |
| `real_chip_bt601/ank_33_3.tif` | `10478aa4c930bb613c7f319c878cc3923bd002ec100309b3de3dd2825366aeec` | 52,386 |
| `real_chip_bt601/ank_33_34.tif` | `9d77150b1e4423a24ce89962a9e7e5e4ce3db80f22949f55b8ccd1fa69e4836c` | 52,386 |
| `real_chip_bt601/ank_33_36.tif` | `0a0f9db98c52f0c779d567cf3f45c9d3f48772f423b9b782178e59ec7b53f56e` | 52,386 |
| `real_chip_bt601/ank_34_11.tif` | `02f9cf55e9cdc39c1f934cb3744aba625df08902794d940845c45d1d277bd099` | 52,386 |
| `real_chip_bt601/ank_34_15.tif` | `4ab07c917420f352c4977d52dc2104810145286adacafec2a36f01e6c8199cf5` | 52,386 |
| `real_chip_bt601/ank_34_21.tif` | `e5cc1d90adc1804ef8af5cd01e70c18c549b656e193023eb382bea830a2d2e20` | 52,386 |
| `real_chip_bt601/ank_34_30.tif` | `04d469dc992ca804c39cbdaa7b2b1a9a3e819db36784d9c1a85073ec790394ac` | 52,386 |
| `real_chip_bt601/ank_35_11.tif` | `978d6694814b6f5a2b0e58e3e920466c444d477e4c33ee67909eae59aede04e4` | 52,386 |
| `real_chip_bt601/ank_35_28.tif` | `d47a53cb8a8f98101014fdc0460766e10afaa553f438b3ae88d29dc81a6c3f1c` | 52,386 |
| `real_chip_bt601/ank_35_39.tif` | `86c00f904de4256b94db7384a967e78547eb68417cb0b93558112fd84dbfe443` | 52,386 |
| `real_chip_bt601/ank_35_7.tif` | `d66c9f78253110bd9e5e3dfde01f7f0660ad18ce7f6aa1ede32c3be20c784737` | 52,386 |
| `real_chip_bt601/ank_36_40.tif` | `42dc529c1d0ee938f901b1b98182a2d4d122936aa4bbb28cc8575a85a77b5063` | 52,386 |
| `real_chip_bt601/ank_38_19.tif` | `e8c84d79984d01bae5abb0ce77b0216c6fbed4a9a06de48f710ce086a99e3191` | 52,386 |
| `real_chip_bt601/ank_38_22.tif` | `a8c6cac9b7989ba9eafe7fc874417b9b46eca3ba97cb684c884a3139f4ae61da` | 52,386 |
| `real_chip_bt601/ank_38_24.tif` | `fec020aa9d44ad836497a691662ae0c19a27a496018aeccaec4300abfa34ee8f` | 52,386 |
| `real_chip_bt601/ank_38_27.tif` | `e4aa4792ca43b93de22d1fb3633da70f594e860c4c8bf9501713ac19a123f75a` | 52,386 |
| `real_chip_bt601/ank_38_40.tif` | `a41ecd45be858a348a57db1e12893ac8ee9e91774e57955860ce2779c88feeba` | 52,386 |
| `real_chip_bt601/ank_38_9.tif` | `95f017345b65b06af3a3ebb1e1e21f2267a954fc2c0bac4523ffe489d5e4f4a0` | 52,386 |
| `real_chip_bt601/ank_39_1.tif` | `8875d1ac9ecef7275d5616c1a5640243b3c2c655414bb5692246f493d45704ae` | 52,386 |
| `real_chip_bt601/ank_3_13.tif` | `a21e6e22be9c2210fe682f505f1c36adb5153ac23114338c201724da8fff0e02` | 52,386 |
| `real_chip_bt601/ank_3_25.tif` | `175a0ec833772707ecbb329c2355386d739f8c4a63f11e7533213e0e0a5afb29` | 52,386 |
| `real_chip_bt601/ank_3_29.tif` | `b2bd0b20e084e906d7667cdd360bf3ad89228fe03f758bc5bea1a144afd1a848` | 52,386 |
| `real_chip_bt601/ank_3_34.tif` | `c771fe1cad787a6d6fa6d7f0d6eb3964c14d3da3d92d7060adb2f977820b8c11` | 52,386 |
| `real_chip_bt601/ank_3_39.tif` | `5c4591b2111771a0b2b021c5c94687c254fbf6b2fd22f4b91c696c65fe2fd6b8` | 52,386 |
| `real_chip_bt601/ank_3_9.tif` | `62dbeb492cb59892c8b8b1891c53aa3cbc8e8c8b417d34551a964bcbcfd8dc24` | 52,386 |
| `real_chip_bt601/ank_40_19.tif` | `89c9ea49493d2851818db5389a72c03835fbc67245dee79e921beda4d26182bc` | 52,386 |
| `real_chip_bt601/ank_40_2.tif` | `f8ac9380b1af933d92b556718b163e090c86bbc49971f28be730088656152ca5` | 52,386 |
| `real_chip_bt601/ank_40_40.tif` | `4c6ec0321edc0ea9647f4245f678a9530607df6c9e0f7039ac0c095373b76b11` | 52,386 |
| `real_chip_bt601/ank_41_0.tif` | `1a1de07d15a820b0c915ee96f4315214094add764b62467be8ad68dd9bec744a` | 52,386 |
| `real_chip_bt601/ank_41_1.tif` | `19a92c6bd98bd2a6f7c78608e3914868d58e25c86b287cb8347303b2ba9b5324` | 52,386 |
| `real_chip_bt601/ank_41_19.tif` | `25be2172ca7702def636dbe8e13945c1a274a8219b5873ca838eca1fdcee194e` | 52,386 |
| `real_chip_bt601/ank_41_40.tif` | `ba4eb2cefe9d156645048dd3c06bd205f94ec213997c5698ceac2fb7973f7a43` | 52,386 |
| `real_chip_bt601/ank_4_23.tif` | `3cf32f506d2d08e1ef720ff5b3d8162475e55dd5a4f25872de08aeb44b792f5a` | 52,386 |
| `real_chip_bt601/ank_4_41.tif` | `b8e6957b7a2dceb63c97901197727c9967ea589f578c63f8b3b960501232e460` | 52,386 |
| `real_chip_bt601/ank_5_12.tif` | `0f291b212567a7d016ecec155db1875607c0edf03b3d4ee7eaddfffbc8e7fb1a` | 52,386 |
| `real_chip_bt601/ank_5_40.tif` | `5b447a0a70f846e5a5aa5d1e1424a5e627c5b40cd6c643a204c5167d55fe3226` | 52,386 |
| `real_chip_bt601/ank_5_5.tif` | `856fff83e582b1b2b56f95767a538dee0d54d443671f6d09bc6533d1151953ce` | 52,386 |
| `real_chip_bt601/ank_6_10.tif` | `85a5b250fa27991dedcaa08ca218a0e12578b20a2c562e7dc31de6e075d057ba` | 52,386 |
| `real_chip_bt601/ank_6_38.tif` | `92213e31ca90e48a34729115c4593ff527357ef7ec778ac04d70eb39b0436ae0` | 52,386 |
| `real_chip_bt601/ank_7_36.tif` | `ccab8367fc3ec51f6c96fca07e30c1e3f13040a67876769f01bc99f93ddf70be` | 52,386 |
| `real_chip_bt601/ank_7_8.tif` | `8cb6a092a24e518cb8765fcd0da0ce9002c27c0b65cd058db472618edeb72bcb` | 52,386 |
| `real_chip_bt601/ank_8_19.tif` | `3a35096b2962354cc78249e699eed7c818b4a7c5de5466d9b2dc94e16cfbc093` | 52,386 |
| `real_chip_bt601/ank_8_22.tif` | `09e6c0fcc5b437a2c0391d9f4590c4e32daba34271a424d326499605ee00f2e0` | 52,386 |
| `real_chip_bt601/ank_8_31.tif` | `4d8ae10160d882a351b0ba34fcddc1aa18a73394777e1c5b0d198b32ef6cb278` | 52,386 |
| `real_chip_bt601/ank_8_41.tif` | `1a07705396e06e10b561ae8bdbb9fd33e4682abe4625d497d1454cbc922894b0` | 52,386 |
| `real_chip_bt601/ank_9_1.tif` | `896f97380f7e970818ca9e5eabf9f3a5d3d24061fd0b77e7d7a7093191bddb9a` | 52,386 |
| `real_chip_bt601/ank_9_24.tif` | `31562112ef45f0638bb27aede7f9c3d580576acff7ee0a92b1314237b80a02ca` | 52,386 |
| `real_chip_bt601/ank_9_25.tif` | `6f0521305924c7de6be741a6c1c9d6cf766bdd0cda602cd0801287f7c27842ba` | 52,386 |

**343 files, 27.8 MB.** (260 rasters added 2026-08-26 as insurance for the informative-mask test.) (2 added by the LR-confound probe, 1 by the common-support re-scoring, 2026-08-26.) (2 added 2026-08-26 by the LR-confound probe.) Regenerate this table with `shasum -a 256` over the directory.
