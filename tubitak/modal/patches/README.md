# Patches applied to the cloned upstream repo on Modal

Committed, not applied ad hoc at container start. A `sed` against a fresh clone would be an
unrecorded code path — the class corrections-log entries 22 and 25 record — so the change
lives here as a file, is applied with `git apply` (which verifies the pre-state and fails
loudly if upstream ever differs), and the sha256 of the resulting file is logged at preflight.
"Which code did this run use" therefore has an answer six months from now.

## image_folder_sorted.patch

`data/image_folder.py:make_dataset()` does `for root, _, fnames in sorted(os.walk(dir))`,
which sorts the walk tuples but **not** `fnames`, so per-directory file order is whatever the
filesystem enumeration returns.

Measured (AMENDMENT SEED-b): the Modal **Volume enumerates in sorted order**, the extracted
local copy does **not** —

    volume order sha256  4b5f232034261ed1a2b051db6e17d1dd6a1424ba9225bb49c5e3433e8493cad9
    local  order sha256  a4171d8815059227fc8d61afd956ead164eea695e186c7913625f9faa8006099

so staging to local disk would have silently changed which files the seeded shuffle maps to.

**This patch restores the order the Volume was already giving, on local disk.** It is not a new
arbitrary ordering imposed on Modal; it preserves the network layer's behaviour after the data
moves to local disk. Kaggle's enumeration order was never recorded and cannot be recovered, so
this makes Modal runs internally consistent and reproducible — it does not make them provably
match Kaggle. The gate measures that residual directly by running C2 twice, sorted and
unsorted, at fixed hardware and fixed seed.
