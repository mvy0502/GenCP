#!/usr/bin/env python
"""Verify a Kaggle backup dataset actually contains every archive we sent.

Written because `kaggle datasets create` once uploaded two of four archives and exited
with status 0, printing no error and not even a "Starting upload" line for the two it
skipped. A zero exit code from that tool does not mean the upload was complete, and a
single page of `kaggle datasets files` does not either - one large archive's entries can
fill the whole page and hide the absence of the others.

So: poll until the dataset reports a non-zero size (Kaggle extracts tars server-side and
reports 0 until it has finished), then page through the ENTIRE file list and count
entries per expected archive prefix.
"""
from __future__ import annotations
import sys, time

DATASET = "vedatyildirim/gencp-evidence-backup-2"
EXPECTED = ["checkpoints_C4", "checkpoints_C5", "checkpoints_C4_s43_modal",
            "generated_fakes"]
POLL_SECONDS = 30
MAX_WAIT = 90 * 60


def api():
    from kaggle.api.kaggle_api_extended import KaggleApi
    a = KaggleApi()
    a.authenticate()
    return a


def dataset_size(a):
    for d in a.dataset_list(mine=True, search="gencp-evidence-backup-2"):
        if str(d.ref) == DATASET:
            return int(getattr(d, "totalBytes", 0) or 0)
    return -1


def all_files(a):
    """Page through the complete file list."""
    names, token, pages = [], None, 0
    while True:
        r = a.dataset_list_files(DATASET, page_token=token, page_size=200)
        batch = getattr(r, "files", None) or []
        names += [str(f.name) for f in batch]
        pages += 1
        token = getattr(r, "nextPageToken", None) or getattr(r, "next_page_token", None)
        if not token or not batch:
            break
        if pages > 400:
            print("  stopped paging at 400 pages")
            break
    return names, pages


def main():
    a = api()
    t0 = time.time()
    size = dataset_size(a)
    while size <= 0 and time.time() - t0 < MAX_WAIT:
        print(f"  size still 0 after {int(time.time()-t0)}s — Kaggle still extracting",
              flush=True)
        time.sleep(POLL_SECONDS)
        size = dataset_size(a)
    print(f"\ndataset size reported: {size:,} bytes after {int(time.time()-t0)}s")
    if size <= 0:
        print("TIMED OUT waiting for a non-zero size — NOT VERIFIED")
        return 2

    names, pages = all_files(a)
    print(f"enumerated {len(names):,} file entries over {pages} pages\n")
    ok = True
    for pfx in EXPECTED:
        # exact prefix: 'checkpoints_C4/' must not be satisfied by 'checkpoints_C4_s43_modal/'
        n = sum(1 for x in names if x.startswith(pfx + "/"))
        state = "PRESENT" if n > 0 else "*** MISSING ***"
        if n == 0:
            ok = False
        print(f"  {pfx:<28s} {n:>7,} entries   {state}")
    print()
    print("=" * 64)
    print("BACKUP 2: " + ("UPLOADED AND VERIFIED — all four archives present"
                          if ok else "INCOMPLETE — see MISSING above"))
    print("=" * 64)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
