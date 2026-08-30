# WP9 — making the repository say what exists

Someone opening this repository yesterday could not tell that Project 2 existed: `README.md`
and `tubitak/DEVIR.md` did not mention `tubitak/sr/`, and there was no release, so there was
nothing anyone could install. The work was committed and invisible.

**No behaviour was changed.** This work package writes documents and builds a package. The
frozen directories were not touched; §4 gives the evidence.

---

## 1. What was written

| file | what changed |
|---|---|
| `README.md` | a Project 2 section: the plugin, its three methods, what has been measured **with its scope**, what has not, the requirements, and where the reports are |
| `tubitak/DEVIR.md` | a Turkish handover section (§P2.1–P2.7): `tubitak/sr/` module by module, what is deliberately absent and the exact command that regenerates or fetches each, the frozen-directory convention with its reason, the two failure modes this project keeps producing, and the open items with their source report |
| `tubitak/sr/docs/09-release-notes-draft.md` | the draft release, **not published** |
| this file | what was refreshed, what the install test found, what cannot be reproduced from the repository alone |

Two numbers appear in the README, and neither can be quoted without its scope, by construction:
the matching result names its granule (**36SXJ**), its corpus (**1332 chips**) and its
transformation (**40 m → 10 m against real Sentinel-2**) in the same sentence; and the wsx4
comparison states in the same paragraph that the model is run outside its trained domain and
why that is unavoidable — **the only ground truth in this repository is real Sentinel-2 at
10 m.**

## 2. The release that was drafted, not published

Tag **`sr-plugin-v0.1.0`** on `mvy0502/gencp-validation`, following the convention the existing
`plugin-v0.2.0` and `clcplus-turkey-2026-08-30` releases already set.

| attachment | size | sha256 |
|---|---|---|
| `gencp_super_resolution.zip` | 49,379 B | `59b72bb9d600…c17bf962` |
| `gencp_sr_x2_v1.onnx` | 1,964,122 B | `3fcb34a2ff5e…5b0375ef7` |
| `gencp_sr_x4_b4.onnx` | 2,086,466 B | `f3f2ffbde52c…89f0ad4ba` |

**wsx4's weights are not attached.** They are not this project's work. The draft links
`https://github.com/IGNF/sentinel2_superresolution` and states that **both** `wsx4_spatrad.onnx`
and `wsx4_spatrad.yaml` must be downloaded **into the same directory**, because the plugin
reads the sidecar beside the model for the scale, normalisation and crop margin — the wsx4
graph carries no embedded provenance.

Both of our models carry their provenance inside the graph, including the registered schedule
beside what actually ran: the x2 model stopped at **16,306 of a registered 20,000 steps**
(`stop_reason = budget`), the x4 model completed **20,000 of 20,000** (`stop_reason = steps`).

## 3. The install test

**The zip installed and ran.** Built with `tubitak/sr/build_sr_plugin_zip.py`: 14 files,
49,379 bytes.

The test was deliberately not shortcut. QGIS was launched with `--profiles-path` pointing
**into the scratchpad**, so the throwaway profile lived outside the normal profiles root
entirely and the default profile was not merely untouched but unreachable. The plugin was
installed by unpacking the zip into that profile — what QGIS's "Install from ZIP" does — and
the run went through **QGIS's own loader**, not a hand-rolled import:

| check | result |
|---|---|
| QGIS discovered the plugin (`available_plugins`) | **yes** |
| `loadPlugin` / `startPlugin` | **both true** |
| active in `qgis.utils.plugins`, instance class | **yes**, `GenCPSRPlugin` |
| `sr_core` resolved to the **vendored** copy inside the plugin | **yes** |
| **working-tree paths on `sys.path`** | **none** |
| bicubic end to end, 256 px → 512 px | **ran** |
| Gate S: CRS equal / origin equal / pixel halved / size doubled | **all four hold** |
| clipped values, uncovered output pixels | **0, 0** |

**Nothing was found missing.** The zip is self-contained: vendoring `sr_core` is what makes it
so, and the test confirms the vendored copy is the one that loads.

### 3.1 Two false starts, both worth recording

**The first run wrote nothing and put an error dialog on Vedat's screen.** QGIS's `--code`
execs the file **without setting `__file__`**, so the script died with `NameError` on its first
line — before it could write even its own start marker. Fixed by writing the path in literally
and sending any traceback to a file instead of a dialog. A test harness that reports failure
only through a modal dialog is a harness that reports nothing when nobody is watching.

**The second run passed while testing less than it appeared to.** `--profiles-path X` makes
QGIS use `X/profiles`, so the plugin I had unpacked into `X/wp9` was never on QGIS's own search
path; my script had appended the directory by hand. That version proved the zip's *contents*
work. It did not prove **QGIS installs and loads it**, which is the actual question. The table
above is from the corrected run.

## 4. The default profile was not touched

Recorded before anything else was done, and again at the end:

| | files | digest of the hash list |
|---|---|---|
| baseline | 38 | `fcd92be044d9da20dd3a086b72c07257c09d6e51a03513d78866fc96d7eae112` |
| after | 38 | `fcd92be044d9da20dd3a086b72c07257c09d6e51a03513d78866fc96d7eae112` |

**Identical.** `diff` reports no difference. No new profile appeared in the normal profiles
root; the throwaway lived entirely under the scratchpad. The plugin the 4 September
demonstration runs on is untouched, and so are `tubitak/sr/sr_plugin/`, `tubitak/sr/sr_core/`,
`tubitak/qgis_plugin/` and `tubitak/gencp_core/`.

## 5. Audit: absolute paths, data references, machine assumptions

Listing is the deliverable; nothing was changed.

**Absolute paths in the shipped zip: none.** No `/Users/`, `/Applications/`, `/opt/homebrew`,
`/private/tmp` or Windows drive letters in any of the 14 files.

**Environment assumptions: none.** No `os.environ`, `getenv` or `expanduser` anywhere in the
package.

**Repository-layout references: 13, and all but two are documentation.** Docstrings and
comments cite `tubitak/sr/tests/gate_s.py`, `tubitak/docs/terimler.md` and similar as the
authority for a convention. They are prose; they resolve for a reader with the repository and
mislead nobody without it.

**The two that are code** — `dialog.py:381–382`:

```python
cands = {"wsx4": ["tubitak/data/wp5_reference/models/wsx4_spatrad.onnx"],
         "model": ["tubitak/data/sr_models/gencp_sr_x2_v1.onnx"]}.get(kind, [])
```

These are **repository-relative** and are reached only after `self._repo_root()` returns a
directory, which it cannot do in a deployed profile. The code comment three lines above says
exactly this and calls the empty result the correct outcome. **So this is a checkout
convenience that degrades to "the user picks the file", not a broken absolute path** — but it
is listed because it is the only place in the package that names a path inside `tubitak/data/`.

One observation from reading it, listed and not fixed: the model candidate names only
`gencp_sr_x2_v1.onnx`. In a checkout, the model method never pre-fills the **x4** model WP7
produced.

## 6. What remains impossible to reproduce from the repository alone

`tubitak/DEVIR.md` §P2.3 gives the exact command for each. What no command in this repository
can produce:

1. **The five Sentinel-2 L2A products.** They are downloaded, not generated. The route is
   public and needs no registration (`sentinel-cogs` S3 via Element84 Earth Search) and the
   five product IDs are recorded in `02a-reflectance-corpus.md` §1 with ETag verification — so
   the *inputs* are reproducible, but only while that bucket serves them.
2. **wsx4's weights**, which are third-party and deliberately never shipped.
3. **Byte-for-byte reproduction of the x2 model.** Its stochastic arm's library versions were
   not recorded at the time — the omission that standing practice 9 exists to prevent. The x4
   model does record them.
4. **The two hangs and the probe/run gap**, which are properties of this machine and are
   recorded as open items rather than as reproducible procedures.

## 7. The handover copy

Procedure followed: **`CLAUDE.md` rule 2** — *"refreshed at milestones by copying the curated
`tubitak/` tree"*. That is where it is documented; no procedure was invented. The remote's URL
was printed and confirmed before anything touched it: **`devir` →
`https://github.com/mvy0502/gencp-validation.git`**. The remote name was spelled out in every
command and no bare `git push devir` was run.

**The refresh is an overlay, never a delete-sync.** The handover copy holds 662 files under
`tubitak/`, including directories this repository no longer has. `rsync --delete` would
propagate this repository's deletions and destroy the research record — the same failure
`CLAUDE.md` records as having nearly happened once through a merge. Files present only in the
handover copy are left alone.

### 7.1 Three near-misses during the refresh, none of which reached the remote

**Nothing was committed or pushed to `devir` until the copy was correct**, so none of these
escaped the scratchpad. All three are the same shape and it is this project's own recurring
one.

1. **A blind audit.** The first absolute-path audit reported "none" for every category. It was
   piping an unquoted `$FILES` into `grep`, and **zsh does not word-split unquoted variables**,
   so grep received one impossible filename and read nothing. Caught only because the
   known-true case — searching for a string that is certainly present — also returned zero.
   **The empty result was going into the report as a clean bill of health.**
2. **A truncated copy.** The first overlay piped `rsync --itemize-changes` into `head -30`,
   which closed the pipe and killed rsync with SIGPIPE partway through. `tubitak/sr/` arrived
   as empty directories. Piping a long operation into `head` truncates the *work*, not just
   the output.
3. **30 GB toward a repository that must never hold data.** The second overlay excluded
   `data/` — and the working tree also gitignores `tubitak/outputs/`, 68 GB of it, which the
   exclude list did not name. Nothing was staged and nothing was pushed, and the clone was
   deleted and re-made from scratch.

The third is exactly the lesson `CLAUDE.md` already records twice: **an enumeration of what to
exclude fails, because the thing you did not think of is not on the list.** The fix is not a
longer exclude list. **The curated tree is defined as the set of files git tracks** —
`git ls-files tubitak` — so anything gitignored cannot enter by construction, whether or not
anyone thought of it.
