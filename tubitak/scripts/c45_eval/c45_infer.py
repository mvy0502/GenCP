#!/usr/bin/env python
"""C45 step 1: ank130 inference for arms C4 (GAN+LPIPS) and C5 (LPIPS-only),
exactly the B1_infer.py procedure: STOCH (dropout active, no --eval), seed 42
via sitecustomize shim, OVP inputs (run/inputs), CPU, checkpointed.
Registration: tubitak/docs/phase-c-lpips-registration.md.
Checkpoint discipline: asserts latest_net_G.pth tensor-equal to 20_net_G.pth."""
import os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
C45 = ROOT / "tubitak/data/tool_runs/C45"
GP = os.environ.get("GENCP_PYTHON", "/opt/homebrew/Caskroom/miniforge/base/envs/gencp/bin/python")
ARMS = {"C4": ROOT / "tubitak/outputs/c4_checkpoints/checkpoints",
        "C5": ROOT / "tubitak/outputs/c5_checkpoints/checkpoints"}

# seed shim, byte-identical in effect to B1's _shims/s42/sitecustomize.py
shim = C45 / "_shims/s42"
shim.mkdir(parents=True, exist_ok=True)
(shim / "sitecustomize.py").write_text(
    "import random, numpy, torch\n"
    "SEED = 42\n"
    "random.seed(SEED)\n"
    "numpy.random.seed(SEED)\n"
    "torch.manual_seed(SEED)\n"
    "torch.cuda.manual_seed_all(SEED)\n"
    "print('[seed-hook] random/numpy/torch seeded with %d' % SEED, flush=True)\n")
(C45 / "_logs").mkdir(parents=True, exist_ok=True)

import torch  # gencp env
for arm, ck in ARMS.items():
    a = torch.load(ck / arm / "latest_net_G.pth", map_location="cpu")
    b = torch.load(ck / arm / "20_net_G.pth", map_location="cpu")
    assert set(a.keys()) == set(b.keys()) and all(torch.equal(a[k], b[k]) for k in a), \
        f"{arm}: latest_net_G.pth is not tensor-equal to 20_net_G.pth"
    print(f"{arm}: latest_net_G.pth tensor-equal to 20_net_G.pth", flush=True)


def n_fakes(arm):
    d = C45 / f"out/{arm}/{arm}/test_latest/images"
    return len(list(d.glob("*_fake.png"))) if d.is_dir() else 0


def run(arm):
    if n_fakes(arm) >= 130:
        return arm, 0, "skipped"
    env = dict(os.environ)
    env["PYTHONPATH"] = str(shim) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    cmd = [GP, "test.py",
           "--dataroot", "tubitak/data/ankara/run/inputs",
           "--name", arm,
           "--checkpoints_dir", str(ARMS[arm]),
           "--model", "test", "--netG", "unet_256", "--norm", "batch",
           "--dataset_mode", "single", "--load_size", "256", "--crop_size", "256",
           "--num_test", "130", "--gpu_ids", "-1",
           "--results_dir", str(C45 / f"out/{arm}")]
    with open(C45 / f"_logs/infer_{arm}.log", "w") as lf:
        p = subprocess.run(cmd, cwd=ROOT, env=env, stdout=lf, stderr=subprocess.STDOUT)
    return arm, p.returncode, f"{n_fakes(arm)} fakes"


bad = []
with ThreadPoolExecutor(max_workers=2) as ex:
    futs = [ex.submit(run, a) for a in ARMS]
    for f in as_completed(futs):
        arm, rc, note = f.result()
        print(f"infer {arm}: rc={rc} {note}", flush=True)
        if rc != 0 or n_fakes(arm) < 130:
            bad.append((arm, rc))
print(f"inference complete, failures: {len(bad)} {bad}")
sys.exit(1 if bad else 0)
