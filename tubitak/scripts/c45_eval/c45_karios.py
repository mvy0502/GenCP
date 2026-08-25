#!/usr/bin/env python
"""C45 step 3: 260 KARIOS runs (C4/C5 x 130 chips), warp/<arm>/<stem>.tif vs
run/ref/<stem>_warp.tif, config tubitak/configs/karios_gencp.json UNCHANGED
(cited per corrections-log lesson 16). Checkpointed: a run whose KLT csv
exists is skipped. Liveness every 20."""
import glob, os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
C45 = ROOT / "tubitak/data/tool_runs/C45"
REF = ROOT / "tubitak/data/ankara/run/ref"
KARIOS = os.environ.get("KARIOS_BIN", "/opt/homebrew/Caskroom/miniforge/base/envs/karios/bin/karios")
CONF = str(ROOT / "tubitak/configs/karios_gencp.json")

stems = sorted(p.name[:-4] for p in (ROOT / "tubitak/data/ankara/run/inputs").glob("*.png"))
assert len(stems) == 130
jobs = [(arm, st) for arm in ("C4", "C5") for st in stems]


def run(job):
    arm, st = job
    res = C45 / "karios" / arm / st
    if glob.glob(str(res / "*" / "KLT_matcher_*.csv")):
        return job, 0, 1, "skipped"
    res.mkdir(parents=True, exist_ok=True)
    p = subprocess.run([KARIOS, "process", str(C45 / f"warp/{arm}/{st}.tif"),
                        str(REF / f"{st}_warp.tif"), "--out", str(res),
                        "--conf", CONF, "--no-log-file"],
                       capture_output=True, text=True)
    csvs = glob.glob(str(res / "*" / "KLT_matcher_*.csv"))
    return job, p.returncode, len(csvs), p.stderr[-300:] if p.returncode else ""


done, bad = 0, []
with ThreadPoolExecutor(max_workers=8) as ex:
    futs = [ex.submit(run, j) for j in jobs]
    for f in as_completed(futs):
        job, rc, ncsv, err = f.result()
        done += 1
        if rc != 0 or ncsv == 0:
            bad.append((job, rc, err))
        if done % 20 == 0:
            print(f"KARIOS {done}/260", flush=True)
print(f"KARIOS complete: {done}/260, failures: {len(bad)}")
for job, rc, err in bad[:20]:
    print("FAIL", job, rc, err)
sys.exit(1 if bad else 0)
