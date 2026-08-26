#!/usr/bin/env python
"""Verify a Kaggle backup dataset actually contains every archive we sent.

Written because `kaggle datasets create` once uploaded two of four archives and exited
with status 0, printing no error and not even a "Starting upload" line for the two it
skipped. A zero exit code from that tool does not mean the upload was complete, and a
single page of `kaggle datasets files` does not either - one large archive's entries can
fill the whole page and hide the absence of the others.

Run with the interpreter that HAS the kaggle module. On this machine the CLI's shebang
points at the miniforge base python, not the `gencp` env:

    /opt/homebrew/Caskroom/miniforge/base/bin/python tubitak/tests/verify_kaggle_backup.py

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
    """Bytes Kaggle reports for the dataset, or -1 if it is not listed.

    The attribute is `total_bytes` on this client (2.2.4). An earlier version of this
    script read `totalBytes`, which silently returns the default 0 forever and made the
    poll loop unfalsifiable - the same class of bug as the silent partial upload it was
    written to catch. Both spellings are accepted now, and an unknown-attribute case is
    reported rather than defaulted.
    """
    for d in a.dataset_list(mine=True, search="gencp-evidence-backup-2"):
        if str(d.ref) != DATASET:
            continue
        for attr in ("total_bytes", "totalBytes", "size"):
            if hasattr(d, attr):
                return int(getattr(d, attr) or 0)
        print("  WARNING: no size attribute found on the dataset object; "
              f"available: {[x for x in dir(d) if not x.startswith('_')][:12]}")
        return 0
    return -1


def find_prefixes(a, expected):
    """Page the listing until every expected prefix has been seen at least once.

    Kaggle lists alphabetically, so the archives appear in a known order and the last one
    (`generated_fakes`, 35,322 entries) begins after roughly 2,160 entries. Enumerating
    the WHOLE listing is both unnecessary and harmful: 37k entries at 200 per page is ~185
    rapid calls, which earns a 429 Too Many Requests and verifies nothing. So: stop as
    soon as all prefixes are found, pause between pages, and back off on 429.
    """
    import requests
    counts = {p: 0 for p in expected}
    token, pages, seen_total = None, 0, 0
    while True:
        for attempt in range(5):
            try:
                r = a.dataset_list_files(DATASET, page_token=token, page_size=200)
                break
            except requests.exceptions.HTTPError as e:
                if e.response is not None and e.response.status_code == 429:
                    wait = 10 * (attempt + 1)
                    print(f"  429 rate-limited; backing off {wait}s", flush=True)
                    time.sleep(wait)
                    continue
                raise
        else:
            print("  giving up after repeated 429s — NOT VERIFIED")
            return counts, pages, False
        batch = getattr(r, "files", None) or []
        for f in batch:
            name = str(f.name)
            seen_total += 1
            for pfx in expected:
                if name.startswith(pfx + "/"):
                    counts[pfx] += 1
        pages += 1
        if all(v > 0 for v in counts.values()):
            print(f"  all {len(expected)} prefixes seen after {pages} pages "
                  f"({seen_total:,} entries) — stopping early", flush=True)
            return counts, pages, True
        token = getattr(r, "nextPageToken", None) or getattr(r, "next_page_token", None)
        if not token or not batch:
            return counts, pages, True
        time.sleep(1.5)


def main():
    a = api()
    t0 = time.time()
    size = dataset_size(a)
    while size <= 0 and time.time() - t0 < MAX_WAIT:
        print(f"  size still 0 after {int(time.time()-t0)}s - Kaggle still extracting",
              flush=True)
        time.sleep(POLL_SECONDS)
        size = dataset_size(a)
    print(f"\ndataset size reported: {size:,} bytes after {int(time.time()-t0)}s")
    if size <= 0:
        print("TIMED OUT waiting for a non-zero size — NOT VERIFIED")
        return 2

    counts, pages, complete = find_prefixes(a, EXPECTED)
    print(f"paged {pages} pages\n")
    ok = complete
    for pfx in EXPECTED:
        n = counts[pfx]
        state = "PRESENT" if n > 0 else "*** MISSING ***"
        if n == 0:
            ok = False
        print(f"  {pfx:<28s} {n:>7,} entries seen   {state}")
    print("\n  (counts are 'seen before early exit', not totals — presence is the test)")
    print()
    print("=" * 64)
    print("BACKUP 2: " + ("UPLOADED AND VERIFIED — all four archives present"
                          if ok else "INCOMPLETE — see MISSING above"))
    print("=" * 64)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
