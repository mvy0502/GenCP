# WP12 — the plugin on QGIS 3.x (Qt5), not only 4.2 (Qt6)

## 0. What could not be done, and what was done instead

**QGIS 3.40 is no longer downloadable.** Every 3.40.x macOS build returns 403 from
`download.qgis.org`, while `ltr/qgis_ltr_final-3_44_13.dmg` and `pr/qgis_pr_final-4_2_1.dmg`
both return 200 — so 403 means absent, not denied. Homebrew pins the same pair
(`qgis@ltr` = 3.44.13, `qgis` = 4.2.1). There is no legitimate source for 3.40 on this
machine.

**QGIS 3.44.13 was installed instead**, alongside 4.2.1. It is the current LTR, it is **Qt5**
(5.15.18 / PyQt5 5.15.10), and it uses the separate `QGIS3` profile root — so it exercises
both hypotheses the brief names. What it cannot do is prove anything about 3.40 specifically;
see §5.

---

## 1. Which of the two causes it is: **A, a missing library**

**Reproduced exactly**, and the traceback matches the institution's line for line:

```
dialog.py line 375, in _build_ui
    from gencp_core import extent as _ext
  ...
gencp_core/extent.py line 65, in <module>
    from rasterio.crs import CRS as _CRS
ImportError: No module named 'rasterio'
```

**It is not Qt5 versus Qt6.** With rasterio present, the dialog builds and the whole suite
runs on Qt 5.15.18. The plugin was loaded, started and its dialog constructed under PyQt5
without a single enum or moved-class failure.

**The single line responsible** is `gencp_core/extent.py:65`. It was the only module-level
heavy import in the entire package: rasterio's other two uses in that same file
(`rasterio.warp`, `rasterio.transform`) were already deferred inside functions, and
`onnxruntime` and `osmium` were already lazy everywhere. One import out of the set was
eager, and it happened to sit on the path `_build_ui` takes.

### 1.1 The numbers the institution's machine could not give

| | |
|---|---|
| QGIS | 3.44.13-Solothurn |
| **Python** | **3.12.11** (`Clang 17.0.0`) — wheel tag **cp312** |
| **`sys.executable`** | `/Applications/QGIS-LTR.app/Contents/MacOS/QGIS` — **the app binary, not a python** |
| `sys.prefix` | `/Applications/QGIS-LTR.app/Contents/Frameworks/` |
| Qt / PyQt | 5.15.18 / 5.15.10; PyQt5 present, PyQt6 absent |
| bundled site-packages | `/Applications/QGIS-LTR.app/Contents/Frameworks/lib/python3.12/site-packages` |
| user site-packages | `/Users/<user>/.local/lib/python3.12/site-packages` |

**`sys.executable` is the QGIS application binary**, so `sys.executable -m pip` is not a
usable instruction. That is why the message in §3 tells the user to run pip from inside
QGIS's own Python Console instead.

**A second finding, from where the libraries actually resolve on this machine:** `rasterio`,
`numpy` and `shapely` come from QGIS-LTR's **own bundle**, while `onnxruntime` and `osmium`
come from **`~/.local/lib/python3.12/site-packages`** — a user-level directory shared by
*any* Python 3.12 on the machine, including both QGIS installations. So part of why "it works
on 4.2 here" is that user-site packages leak into both, which will not be true on a machine
where nobody installed them. **The two QGIS installations do not have as separate an
environment as assumed.**

## 2. The fix, and both versions afterwards

`gencp_core/extent.py`: the module-level `from rasterio.crs import CRS` becomes a `_crs()`
accessor that imports on first use. Its two call sites are updated. Nothing else changes —
no arithmetic, no behaviour.

### 2.1 Suite, both versions side by side

Core gates, which do not involve QGIS and exercise the changed module:

| gate | result |
|---|---|
| Gate R | **PASS 3/3** tiles byte-identical to stored originals |
| Gate G | **PASS 12/12** assertions |
| Gate ALPHA | **PASS 19/19** |

QGIS-side, run the documented way (`--code`, `QT_QPA_PLATFORM=offscreen`, output to
`GENCP_TEST_OUT`), plugin enabled in each throwaway profile:

| test | QGIS 3.44.13 (Qt5) | QGIS 4.2.1 (Qt6) |
|---|---|---|
| `test_plugin_headless` | **23/23** | **23/23** |
| `overlap_constraints` | **20/20** | **20/20** |
| `qml_sidecar` | **6/6** | **6/6** |
| `plugin_e2e_run` | **80/82** | **82/82** |
| `demo_dry_run` | see §2.2 | see §2.2 |
| `coverage_block` | not run — see §2.3 | not run |

Additionally, the **super-resolution plugin** (Project 2) was installed from its published zip
into the Qt5 profile and exercised: discovered, loaded, started, dialog constructed, and
bicubic run end to end with the Gate S contract exact (256 → 512, CRS and origin unchanged,
**0 clipped, 0 uncovered**). Its dialog also builds on both Qt versions.

### 2.2 Two results that are NOT clean, reported as they are

**`plugin_e2e_run`, 80/82 on Qt5.** Both failures are the same check —
*"the dark capture really is dark — window background lightness 239"*. This is the test
harness failing to force a dark palette under Qt5, not the plugin: the check exists precisely
to refuse to assert anything about dark-mode styling when the capture is not actually dark,
and it did its job. **The obvious explanation is disproved**: I hypothesised that
`QPalette.ColorRole.Window` would not resolve under PyQt5, leaving the palette empty, and
measured it — all eight roles resolve on Qt5 exactly as on Qt6. The real cause is
undiagnosed and is an open item. **No cause is asserted.**

**`demo_dry_run` — the cross-version comparison is not sound and is withdrawn.** It appeared
to be 18/18 on Qt6 against 7 failures on Qt5, and that comparison is worthless: the four
"pre-filled from the project" checks passed on Qt6 because my Qt6 throwaway profile had been
**contaminated by earlier runs in this work package**, which wrote paths into `QgsSettings`
via the dialog's own `_remember`. The demo project itself carries **no `<GenCP>` properties at
all** — verified by unzipping `gencp_demo.qgz` — so on a genuinely empty profile neither
version can pre-fill from it. Attempts to re-run on genuinely fresh profiles hung QGIS 3.44 at
startup and did not produce a result. **The honest statement is that this test's cross-version
behaviour is unresolved**, and that a test which passes only because of profile residue was
not testing what it claimed.

### 2.3 `coverage_block` was not run

It requires `--wrong=`, `--right=` and `--partial=` OSM extracts. No invocation is documented
anywhere in the repository, and no fixture extract exists that fails to cover the Istanbul
test extent while being small enough to index in reasonable time — the smallest available is
660 MB, and a country-sized extract costs about 16 minutes to index (`11-zamanlama.md` §5).
Constructing the three fixtures is a separate task. **It is also CLI and version-independent,
so it is not part of the 3.44-versus-4.2 question.** Separately: given no arguments it raises
`KeyError: 'wrong'` rather than refusing cleanly, which is a small defect in the test against
standing practice 10.

## 3. A missing library now explains itself

`plugin.py` gains `REQUIRED_MODULES`, `missing_requirements()` and a guard in `run()` that
fires **before the dialog is constructed** — constructing it would re-enter the same failing
import and put the traceback back on screen.

The message names the library, names **that QGIS's own site-packages directory** (computed at
runtime, so it differs correctly between the two installations), and gives the one line to run
in QGIS's Python Console. The guard uses the **static** `QMessageBox.warning`, which takes no
enum argument at all — so the fix for a Qt-independent problem does not itself introduce a
Qt5/Qt6 difference.

**Verified known-false first, as practice 11 requires**, by removing the library from a live
interpreter:

| case | QGIS 3.44.13 (Qt5) | QGIS 4.2.1 (Qt6) |
|---|---|---|
| rasterio removed | message shown, names `.../QGIS-LTR.app/.../site-packages` | message shown, names `.../QGIS-final-4_2_1.app/.../site-packages` |
| onnxruntime removed | message shown | message shown |
| everything present | **dialog builds** | **dialog builds** |

The two messages name different directories on the two installations, which is the whole point:
installing into the wrong QGIS's Python changes nothing.

## 4. Metadata made honest

`qgisMinimumVersion` was **3.28**, reasoned about and never run. It is now **3.44** in both
plugins' `metadata.txt` — the oldest version actually verified.

## 5. What remains unverified — stated plainly

- **QGIS 3.40 was never run.** It is not obtainable. A 3.44 pass says Qt5 works and says the
  rasterio fix works; it does **not** say 3.40 works.
- **Any QGIS below 3.44 is untested.** The declared minimum now says so.
- **Windows is untested.** A Mac Qt5 pass tells us Qt5 works; it tells us nothing about
  Windows. Paths, the hardened-runtime signing behaviour that governs which interpreter can
  load onnxruntime, and pip-into-QGIS all differ there.
- **Linux is untested.**
- The `demo_dry_run` cross-version result (§2.2) and the Qt5 dark-capture cause (§2.2) are
  open.

## 6. The finding worth keeping

> **One eager import out of a package that had carefully deferred all the others was enough
> to make the plugin look broken on an entire QGIS generation.**

The deferral discipline was already there — `onnxruntime`, `osmium` and rasterio's two other
uses were all lazy. The failure was a single line that had never been checked against the
condition it assumed, on a machine nobody had tested. The guard in §3 is the part that
generalises: **a heavy dependency must be allowed to be absent, and must say so in a
sentence.**
