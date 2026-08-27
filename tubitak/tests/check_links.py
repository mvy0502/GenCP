#!/usr/bin/env python
"""Check every link in a set of Markdown files, and PROVE the check can fail first.

Three checks in this project could only ever report "found nothing": an enumeration that
missed two files, a BSD-grep PCRE lookahead that matched zero lines, and a poll loop
reading an attribute that did not exist. A clean result from a check that cannot fail is
indistinguishable from a clean result from a check that can, and is worth nothing.

So this script runs a SELF-TEST before it runs the real check: it builds a temporary file
containing one link that is known dead and one known live, and refuses to proceed unless it
reports exactly the dead one. `--self-test-only` runs just that part.

    python tubitak/tests/check_links.py FILE [FILE ...]
    python tubitak/tests/check_links.py --self-test-only

Relative links are resolved against the file's own directory. External links are checked
with a HEAD request unless --no-net is passed. Fragments (#anchor) are stripped: GitHub
rewrites heading ids, so a fragment cannot be verified from the filesystem and pretending
otherwise would be another check that cannot fail.
"""
from __future__ import annotations

import re
import sys

# Unknown arguments are refused, not ignored: a verifier that runs its default
# and prints PASS when you asked for something else is reporting on the wrong run.
import os.path as _op  # noqa: E402
sys.path.insert(0, _op.join(_op.dirname(_op.abspath(__file__)),
                            *(['..', 'tests'] if _op.basename(
                                _op.dirname(_op.abspath(__file__))) != 'tests'
                              else [])))
from _guard import strict_argv  # noqa: E402
strict_argv(known=('--no-net', '--self-test-only'), positional=999)
import tempfile
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

LINK_RE = re.compile(r'\[[^\]]*\]\(([^)\s]+)(?:\s+"[^"]*")?\)')
IMG_RE = re.compile(r'<img[^>]+src="([^"]+)"')
# A bare URL in Markdown is auto-linked by GitHub, so to a reader it IS a link. The first
# version of this checker missed them entirely and reported "1 link" for a file with five -
# a clean result that meant nothing, which is the exact failure this script exists to
# avoid. Excludes anything already captured as a ](...) target or an src="...".
BARE_URL_RE = re.compile(r'(?<![(\"<])\bhttps?://[^\s<>)\]"\'`]+')
SKIP_SCHEMES = ("mailto:", "tel:", "data:")


def _trim_bare(u):
    """Strip what markdown put after a bare URL: emphasis markers, then punctuation."""
    prev = None
    while prev != u:
        prev = u
        for suffix in ("**", "__", "*", "_", "~~", "`"):
            if u.endswith(suffix):
                u = u[: -len(suffix)]
        u = u.rstrip(".,;:")
    return u


def _tracked(path):
    """Is this path committed? Cached per repository root.

    A link to a gitignored file passes .exists() on the machine that wrote it and 404s for
    everyone else. Eleven report figures under a gitignored directory passed this checker
    while being broken on GitHub for every visitor - exactly the class of silent pass the
    self-test exists to rule out.
    """
    import subprocess
    path = Path(path).resolve()
    root = path.parent
    while root != root.parent and not (root / ".git").exists():
        root = root.parent
    if not (root / ".git").exists():
        return None                              # not a git tree; nothing to say
    if root not in _TRACKED_CACHE:
        try:
            out = subprocess.run(["git", "-C", str(root), "ls-files", "-z"],
                                 capture_output=True, timeout=60)
            _TRACKED_CACHE[root] = {
                (root / f).resolve() for f in out.stdout.decode().split("\0") if f
            }
        except Exception:                        # noqa: BLE001
            _TRACKED_CACHE[root] = None
    known = _TRACKED_CACHE[root]
    return None if known is None else path in known


_TRACKED_CACHE = {}


def extract(text):
    md = LINK_RE.findall(text)
    img = IMG_RE.findall(text)
    # Trailing punctuation and markdown emphasis are not part of the URL. A bare URL
    # written inside **bold** came back as ".../gencp-validation**" and was reported dead,
    # which is a false alarm - and a checker that cries wolf gets ignored, which is the
    # same end state as a checker that cannot fail.
    bare = [_trim_bare(u) for u in BARE_URL_RE.findall(text)]
    seen = set(md) | set(img)
    return md + img + [u for u in bare if u not in seen]


def check_file(path, check_net=True, timeout=15):
    """Return (n_links, [(target, reason)]) for one Markdown file."""
    path = Path(path)
    base = path.parent
    bad = []
    targets = extract(path.read_text(encoding="utf-8"))
    for raw in targets:
        t = raw.strip()
        if t.startswith(SKIP_SCHEMES) or t.startswith("#"):
            continue
        if t.startswith(("http://", "https://")):
            if not check_net:
                continue
            try:
                req = Request(t, method="HEAD",
                              headers={"User-Agent": "gencp-link-check"})
                with urlopen(req, timeout=timeout) as r:
                    if r.status >= 400:
                        bad.append((t, f"HTTP {r.status}"))
            except HTTPError as e:
                # GitHub answers HEAD on some asset paths with 403 but serves GET fine.
                if e.code in (403, 405):
                    try:
                        with urlopen(Request(t, headers={"User-Agent": "gencp-link-check"}),
                                     timeout=timeout) as r2:
                            if r2.status >= 400:
                                bad.append((t, f"HTTP {r2.status}"))
                    except Exception as e2:          # noqa: BLE001
                        bad.append((t, f"{type(e2).__name__}"))
                else:
                    bad.append((t, f"HTTP {e.code}"))
            except URLError as e:
                bad.append((t, f"unreachable ({e.reason})"))
            continue
        rel = t.split("#", 1)[0]
        if not rel:
            continue
        target = base / rel
        if not target.exists():
            bad.append((t, "no such file"))
        elif target.is_file() and _tracked(target) is False:
            bad.append((t, "exists locally but is NOT tracked by git - 404 for visitors"))
    return len(targets), bad


def self_test():
    """Refuse to be trusted until the checker has demonstrably reported a dead link."""
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        (d / "live.md").write_text("i am here\n")
        probe = d / "probe.md"
        probe.write_text(
            "[live relative](live.md)\n"
            "[DEAD relative](definitely_not_here.md)\n"
            "<img src=\"also_missing.png\">\n"
            "bare url https://example.invalid/x and [md](https://example.invalid/y)\n")
        n, bad = check_file(probe, check_net=False)
        found = {t for t, _ in bad}
        # Dead-detection is proven on the FILESYSTEM side (offline, deterministic); the
        # bare-URL path is proven by the count - 5 targets, not 4, which is what caught the
        # extractor missing them.
        ok = (found == {"definitely_not_here.md", "also_missing.png"} and n == 5)
        print(f"  self-test: {n} links seen (expected 5, incl. one bare URL), "
              f"reported dead = {sorted(found)}")
        if not ok:
            print("  SELF-TEST FAILED: the checker did not report exactly the links that "
                  "were planted dead. A clean run from it would mean nothing.")
            return False
        # A bare URL inside **bold** must come back without the emphasis markers.
        got = _trim_bare("https://example.invalid/repo**")
        if got != "https://example.invalid/repo":
            print(f"  SELF-TEST FAILED: bare-URL trimming returned {got!r}")
            return False
        print("  self-test: bare URL inside **bold** trims to the URL itself")

    # A file that exists but is not committed 404s for every visitor. Prove that fires.
    import subprocess
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        try:
            subprocess.run(["git", "init", "-q", str(d)], check=True, timeout=60)
            (d / ".gitignore").write_text("ignored.png\n")
            (d / "ignored.png").write_bytes(b"x")
            (d / "committed.png").write_bytes(b"x")
            doc = d / "doc.md"
            doc.write_text("![a](ignored.png)\n![b](committed.png)\n")
            subprocess.run(["git", "-C", str(d), "add", "-A"], check=True, timeout=60)
            subprocess.run(["git", "-C", str(d), "-c", "user.email=t@t", "-c", "user.name=t",
                            "commit", "-qm", "x"], check=True, timeout=60)
        except Exception as e:                   # noqa: BLE001
            print(f"  self-test: SKIPPED the untracked-file check ({type(e).__name__}); "
                  "results below cannot distinguish committed from gitignored targets")
            return True
        _TRACKED_CACHE.clear()
        n, bad = check_file(doc, check_net=False)
        found = {t for t, _ in bad}
        if found != {"ignored.png"}:
            print(f"  SELF-TEST FAILED: untracked detection reported {sorted(found)}, "
                  "expected exactly ['ignored.png']")
            return False
        print("  self-test: a gitignored target is reported; a committed one is not")

    print("  self-test PASSED - the checker demonstrably reports dead links, so a "
          "clean result below is worth something")
    return True


def main(argv):
    args = [a for a in argv[1:] if not a.startswith("--")]
    no_net = "--no-net" in argv
    print("=" * 74)
    print("LINK CHECK")
    print("=" * 74)
    if not self_test():
        return 2
    if "--self-test-only" in argv:
        return 0
    # With no file arguments, walk the tree. An earlier invocation passed no files and got
    # "0 links checked across 0 files; 0 dead" with exit 0 - a clean bill of health for
    # having looked at nothing. Discovering the files makes the zero-argument case do real
    # work, and an empty discovery is now an error rather than a pass.
    if not args:
        skip = {".git", "data", "outputs", "__pycache__", "node_modules"}
        args = sorted(
            str(f) for f in Path(".").rglob("*.md")
            if not (skip & set(f.parts))
        )
        print(f"  no files given; discovered {len(args)} markdown files under {Path('.').resolve()}")
        if not args:
            print("  NOTHING TO CHECK: no markdown files found. Refusing to report a pass.")
            return 2

    print()
    total = 0
    all_bad = []
    for f in args:
        n, bad = check_file(f, check_net=not no_net)
        total += n
        status = "OK" if not bad else f"{len(bad)} DEAD"
        print(f"  {status:>8}  {n:>3} links  {f}")
        for t, why in bad:
            print(f"            DEAD: {t}   ({why})")
            all_bad.append((f, t, why))
    print()
    print(f"  {total} links checked across {len(args)} files; {len(all_bad)} dead")
    if total == 0:
        # Files were found and none of them contained a link. Either the corpus is the
        # wrong one or the extractor is broken - both have happened here. "0 dead out of
        # 0" is not a clean bill of health, it is the absence of an examination.
        print("  NOTHING TO CHECK: files were read but not one link was found. That is a "
              "broken extractor or the wrong corpus, not a pass.")
        return 2
    return 1 if all_bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
