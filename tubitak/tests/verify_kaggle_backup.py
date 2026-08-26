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

Two modes:

    (default)  presence  - stop as soon as every prefix has been seen once. Fast, and
                           enough to catch a wholly missing archive. It does NOT catch a
                           half-uploaded one: a truncated tar extracts to a prefix that
                           reads PRESENT exactly like a complete one.
    --full     completeness - page the entire listing with no early exit, count entries
                           per prefix, and diff each against the local tar in
                           `tubitak/data/evidence_backup_2/`. Slow (~190 pages) and the
                           only mode that can say "complete".
"""
from __future__ import annotations
import os, sys, time

DATASET = "vedatyildirim/gencp-evidence-backup-2"
EXPECTED = ["checkpoints_C4", "checkpoints_C5", "checkpoints_C4_s43_modal",
            "generated_fakes"]
POLL_SECONDS = 30
MAX_WAIT = 90 * 60
_REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STAGING_DIR = os.path.join(_REPO, "tubitak", "data", "evidence_backup_2")
FULL_PAGE_PAUSE = 2.5


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


def count_all_prefixes(a, expected):
    """Page the ENTIRE listing, counting every entry, with no early exit.

    Presence is not completeness: a half-uploaded tar extracts to a prefix that reads as
    PRESENT exactly like a whole one. The only way to tell them apart is to count what is
    actually on the server and compare it against the local tar. That means enumerating
    all ~37k entries - the thing `find_prefixes` deliberately avoids - so this mode pauses
    longer between pages and backs off harder on 429. It takes minutes, and that is the
    price of the stronger claim.

    Returns (counts, other, pages, seen_total, complete). `complete` is False if the walk
    was cut short by rate limiting, in which case the counts are lower bounds and prove
    nothing.
    """
    import requests
    counts = {p: 0 for p in expected}
    other = 0
    seen_names = set()
    token, pages, seen_total = None, 0, 0
    while True:
        r = None
        for attempt in range(10):
            try:
                r = a.dataset_list_files(DATASET, page_token=token, page_size=200)
                break
            except requests.exceptions.HTTPError as e:
                if e.response is not None and e.response.status_code == 429:
                    wait = 15 * (attempt + 1)
                    print(f"  429 rate-limited; backing off {wait}s", flush=True)
                    time.sleep(wait)
                    continue
                raise
            except requests.exceptions.RequestException as e:
                # A ~190-page walk is long enough that the transport itself fails: the
                # first attempt at this mode died on ConnectionResetError(54) partway
                # through, which the 429-only handler did not catch, and the traceback
                # cost the whole walk. Kaggle also drops long-lived connections without
                # sending a 429. Retrying the SAME page_token is safe - paging is a pure
                # read, so a repeat costs a request and nothing else.
                wait = 15 * (attempt + 1)
                print(f"  transport error ({type(e).__name__}); retry in {wait}s",
                      flush=True)
                time.sleep(wait)
                continue
        if r is None:
            print("  giving up after repeated errors - enumeration INCOMPLETE", flush=True)
            return counts, other, pages, seen_total, False
        batch = getattr(r, "files", None) or []
        fresh = 0
        for f in batch:
            name = str(f.name)
            if name in seen_names:
                continue          # a repeated page must not inflate a count
            seen_names.add(name)
            fresh += 1
            seen_total += 1
            for pfx in expected:
                if name.startswith(pfx + "/"):
                    counts[pfx] += 1
                    break
            else:
                other += 1
        pages += 1
        if batch and fresh == 0:
            # Every name on this page was already counted. Either the page token stopped
            # advancing or the listing wrapped; either way the walk is no longer making
            # progress and continuing would only spin. Stop and say so.
            print(f"  page {pages} was entirely duplicate - listing is not advancing",
                  flush=True)
            return counts, other, pages, seen_total, False
        if pages % 10 == 0:
            print(f"  ...{pages} pages, {seen_total:,} entries", flush=True)
        token = getattr(r, "nextPageToken", None) or getattr(r, "next_page_token", None)
        if not token or not batch:
            return counts, other, pages, seen_total, True
        time.sleep(FULL_PAGE_PAUSE)


def local_counts(staging=STAGING_DIR):
    """Entry counts read from the local tars, keyed by the prefix Kaggle will use.

    Kaggle names the extracted directory after the archive file, so `checkpoints_C4.tar`
    becomes the prefix `checkpoints_C4/` regardless of what the tar's own root directory
    is called (it is `c4_checkpoints/`). Returns {prefix: (files, dirs, appledouble)}.
    `files` is what the server listing is compared against - Kaggle lists files, not the
    directories that contain them - and it INCLUDES the macOS `._*` AppleDouble members,
    because Kaggle stores those as ordinary files. `appledouble` reports how many of the
    `files` count they are, so the real payload is always visible next to the raw number.

    Read with Python's `tarfile`, NOT with the `tar` CLI, and that distinction is the
    whole reason this function exists. macOS ships libarchive, whose reader transparently
    merges an AppleDouble `._x` member back into `x` as extended attributes, so `tar -tf`
    on this machine does not print the `._` entries at all. Kaggle extracts on Linux,
    which has no such reader, so every one of them lands as a real file in the dataset.
    The first attempt at this comparison used `tar -tf`, undercounted every archive by
    almost exactly half, and made the server listing look like it was paging forever.
    `tarfile` lists raw members and merges nothing.
    """
    import tarfile
    out = {}
    if not os.path.isdir(staging):
        return out
    for fn in sorted(os.listdir(staging)):
        if fn.endswith(".tar"):
            prefix = fn[:-4]
        elif fn.endswith(".tar.gz"):
            prefix = fn[:-7]
        else:
            continue
        dirs = files = ad = 0
        with tarfile.open(os.path.join(staging, fn), "r|*") as t:
            for m in t:
                if m.isdir():
                    dirs += 1
                else:
                    files += 1
                    if os.path.basename(m.name).startswith("._"):
                        ad += 1
        out[prefix] = (files, dirs, ad)
    return out


def run_full(a):
    """--full: count every server-side entry per prefix and diff against the local tars."""
    loc = local_counts()
    expected = sorted(set(EXPECTED) | set(loc))
    print(f"comparing {len(expected)} prefixes; full enumeration, no early exit\n",
          flush=True)
    counts, other, pages, seen_total, complete = count_all_prefixes(a, expected)
    print(f"\npaged {pages} pages, {seen_total:,} entries total "
          f"({other:,} matched no expected prefix)\n")
    print(f"  {'prefix':<28s} {'local':>9s} {'server':>9s}  match   "
          f"{'real':>8s} {'AppleDbl':>9s} {'dirs':>6s}")
    ok = complete
    for pfx in expected:
        srv = counts[pfx]
        if pfx in loc:
            lf, ld, lad = loc[pfx]
            match = "YES" if srv == lf else "*** NO ***"
            if srv != lf:
                ok = False
            print(f"  {pfx:<28s} {lf:>9,} {srv:>9,}  {match:<8s}"
                  f"{lf - lad:>8,} {lad:>9,} {ld:>6,}")
        else:
            print(f"  {pfx:<28s} {'n/a':>9s} {srv:>9,}  (no local tar to compare)")
    print("\n  local/server counts are ALL non-directory members, AppleDouble included -")
    print("  that is what Kaggle stores. 'real' is the payload once `._*` is removed.")
    if not complete:
        print("\n  ENUMERATION WAS CUT SHORT - server counts are lower bounds, not totals")
    print()
    print("=" * 72)
    print("BACKUP 2 COMPLETENESS: " + ("every archive matches its local tar" if ok
                                       else "MISMATCH or incomplete walk - see above"))
    print("=" * 72)
    return 0 if ok else 1


def main():
    full = "--full" in sys.argv or "--counts" in sys.argv
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

    if full:
        return run_full(a)

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
