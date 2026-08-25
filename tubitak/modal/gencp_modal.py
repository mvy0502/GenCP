"""Modal entry point for the seed-replication training runs.

Registration: tubitak/docs/seed-replication-registration.md, AMENDMENT SEED-b.

WHAT THIS CHANGES vs Kaggle, and nothing else:
  * GPU: Modal A10G (Ampere, sm_86) instead of Kaggle T4 (Turing, sm_75). sm_86 IS in the
    pinned torch build's arch list, so no binary-compatibility argument is needed. An L4
    (Ada, sm_89) was the first choice and was superseded before any run: sm_89 is NOT in that
    list. See AMENDMENT SEED-b.
  * TF32 EXPLICITLY DISABLED. The T4 has no TF32 at all, so leaving Ada's TF32 on would move
    convolution and matmul precision as well as hardware, and two factors would vary where we
    intend one. This costs speed and the cost is accepted.
  * Data comes from a Modal Volume instead of /kaggle/input.

WHAT IS HELD IDENTICAL: the image is pinned to the exact versions recovered from the Kaggle
GPU image (AMENDMENT SEED-b), the training script is tubitak/kaggle/train_c1_c2.py unchanged,
the data is byte-identical (same pretrained sha256, same 5,577 pairs), and the sharp-half stop
rule runs exactly as it does on Kaggle because it lives inside that script.

    modal run --detach tubitak/modal/gencp_modal.py::gate_seed43
"""
import os
import subprocess
import sys
import time

import modal

# ---------------------------------------------------------------------------------------
# Image pinned to the RECOVERED Kaggle GPU environment (AMENDMENT SEED-b).
# gcr.io/kaggle-gpu-images/python@sha256:37c64f7d... , BUILD_DATE 20260629-122508
#   Ubuntu 22.04.5 / glibc 2.35 / Python 3.12.13
#   torch 2.10.0+cu128 (cuda 12.8, cudnn 91002) / torchvision 0.25.0+cu128
#   torchmetrics 1.9.0 / numpy 2.0.2 / Pillow 11.3.0 / scipy 1.16.3
# Every version here is a recovered observation, not a capture of the image the Kaggle runs
# used; the amendment says so in those words.
# Python is pinned to the EXACT patch release, 3.12.13, not just the minor. The first build
# used modal.Image.debian_slim(python_version="3.12"), which resolved to 3.12.10 - a near
# version, and the registration forbids substituting one. debian_slim cannot pin a patch
# release, so the base image is the official python:3.12.13-slim instead.
image = (
    modal.Image.from_registry("python:3.12.13-slim", add_python=None)
    .apt_install("git")
    .pip_install(
        "torch==2.10.0+cu128",
        "torchvision==0.25.0+cu128",
        extra_index_url="https://download.pytorch.org/whl/cu128",
    )
    .pip_install(
        "torchmetrics==1.9.0",
        "numpy==2.0.2",
        "pillow==11.3.0",
        "scipy==1.16.3",
        # setuptools/wheel at the versions the Kaggle GPU image carried. They matter: the
        # training script runs `pip install -q dominate visdom` itself, and visdom's legacy
        # setup.py needs pkg_resources (setuptools), which Modal's slim image omits.
        "setuptools==81.0.0",
        "wheel==0.47.0",
    )
)
# NOTE on visdom/dominate, recorded because it looks like a missing pin and is not one.
# The Kaggle GPU image contained NEITHER (verified in the recovery probe's pip freeze).
# train_c1_c2.py installs them itself with check=False, so a failure there is non-fatal on
# Kaggle, and util/visualizer.py imports visdom only under `display_id > 0` while every run
# here passes --display_id -1. Pre-installing visdom in the image would therefore make the
# Modal environment DIFFER from Kaggle's and would turn a tolerated failure into a hard image
# build failure - which is exactly what happened on the first build attempt. It is left to the
# script, as on Kaggle.

app = modal.App("gencp-seed-replication")
vol = modal.Volume.from_name("gencp-data")
out_vol = modal.Volume.from_name("gencp-out", create_if_missing=True)

DATA = "/data/gencp-tr"
OUT = "/out"

# Expected wall time per arm on A10G, from the Kaggle T4 times divided by ~3.5, with the
# timeout set to roughly TWICE that. A hung job left to Modal's 24-hour maximum would burn
# most of the monthly credit for nothing.
TIMEOUTS = {"C1": 2 * 60 * 60, "C2": 2 * 60 * 60, "C4": 4 * 60 * 60, "C5": 4 * 60 * 60}


def _cuda_smoke_test():
    """Prove the GPU computes CORRECTLY, not merely that it computes.

    corrections-log entry 9 recorded a P100 (sm_60) that torch could not emit code for while
    `cuda_available` was True, and its "what would have caught it sooner" was a real CUDA
    smoke test rather than a capability-string comparison. That remedy is kept.

    It is strengthened here because `finite` is not the dangerous failure mode -
    finite-but-wrong is. A silently mis-executing kernel returns perfectly finite garbage.
    So the device result is compared against a CPU reference of the SAME computation at fp32
    tolerance, and the max absolute difference is REPORTED as a number rather than collapsed
    into a boolean. On an A10 (sm_86, natively in the pinned build's arch list) this should be
    trivially clean; if it is not, we learn it in seconds instead of inside a training run.
    """
    import torch
    cap = torch.cuda.get_device_capability(0)
    sm = f"sm_{cap[0]}{cap[1]}"
    arches = torch.cuda.get_arch_list()
    print(f"[smoke] device={torch.cuda.get_device_name(0)} capability={cap} -> {sm}")
    print(f"[smoke] torch arch list={arches}")
    listed = sm in arches
    print(f"[smoke] {sm} natively in arch list: {listed}")
    if not listed:
        print(f"[smoke] WARNING: {sm} is NOT in the pinned build's arch list - this run would "
              f"depend on CUDA minor-version binary compatibility, which AMENDMENT SEED-b "
              f"chose A10G specifically to avoid.")

    torch.manual_seed(0)
    a = torch.randn(512, 512)
    b = torch.randn(512, 512)
    conv = torch.nn.Conv2d(3, 8, 3, padding=1)
    x = torch.randn(2, 3, 64, 64)

    mm_cpu = a @ b
    y_cpu = conv(x)
    with torch.no_grad():
        mm_gpu = (a.cuda() @ b.cuda()).cpu()
        y_gpu = conv.cuda()(x.cuda()).cpu()
    torch.cuda.synchronize()

    d_mm = (mm_cpu - mm_gpu).abs().max().item()
    d_cv = (y_cpu - y_gpu).abs().max().item()
    rel_mm = d_mm / mm_cpu.abs().max().item()
    print(f"[smoke] matmul  max|GPU-CPU| = {d_mm:.3e}  (relative {rel_mm:.3e})")
    print(f"[smoke] conv2d  max|GPU-CPU| = {d_cv:.3e}")
    assert torch.isfinite(mm_gpu).all() and torch.isfinite(y_gpu).all(), \
        "CUDA smoke test produced non-finite output"
    # fp32 accumulation over a 512-length dot product; anything beyond this is not rounding.
    TOL = 1e-3
    assert d_mm < TOL and d_cv < TOL, \
        f"GPU disagrees with CPU beyond fp32 tolerance: matmul {d_mm:.3e}, conv {d_cv:.3e}"
    print(f"[smoke] GPU agrees with CPU within {TOL:.0e} - proceeding")
    return {"sm": sm, "listed": bool(listed), "matmul_maxdiff": float(d_mm),
            "conv_maxdiff": float(d_cv)}


def _disable_tf32():
    """AMENDMENT SEED-b: TF32 off, so precision does not move with the hardware."""
    import torch
    torch.backends.cudnn.allow_tf32 = False
    torch.backends.cuda.matmul.allow_tf32 = False
    print(f"[tf32] cudnn.allow_tf32={torch.backends.cudnn.allow_tf32}  "
          f"cuda.matmul.allow_tf32={torch.backends.cuda.matmul.allow_tf32}  (both must be False)")


def _run_arm(arm: str, seed: int):
    """Run one arm by invoking the UNCHANGED tubitak/kaggle/train_c1_c2.py.

    The script is used verbatim, including its sharp-half stop rule (run_train / _spike_hits),
    which therefore behaves on Modal exactly as it does on Kaggle. Only the two environment
    variables it already reads are set here.
    """
    t0 = time.time()
    _cuda_smoke_test()
    _disable_tf32()

    repo = "/work/GenCP"
    subprocess.run(["git", "clone", "--depth", "1", "-b", "tubitak-tr",
                    "https://github.com/mvy0502/GenCP.git", repo], check=True)

    # The training script expects the Kaggle mount layout; the Volume provides the same tree.
    os.makedirs("/kaggle/input", exist_ok=True)
    if not os.path.exists("/kaggle/input/gencp-tr"):
        os.symlink(DATA, "/kaggle/input/gencp-tr")
    os.makedirs("/kaggle/working", exist_ok=True)

    env = dict(os.environ, ARM=arm, SEED=str(seed),
               PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True")
    # TF32 off must survive into the training subprocess as well as this one.
    env["NVIDIA_TF32_OVERRIDE"] = "0"

    p = subprocess.run([sys.executable, f"{repo}/tubitak/kaggle/train_c1_c2.py"],
                       cwd=repo, env=env)
    elapsed = time.time() - t0

    dst = f"{OUT}/seed{seed}/{arm}"
    os.makedirs(dst, exist_ok=True)
    subprocess.run(["cp", "-r", f"/kaggle/working/checkpoints/{arm}", dst], check=False)
    out_vol.commit()

    gpu_seconds = elapsed
    print(f"[cost] arm={arm} seed={seed} rc={p.returncode} "
          f"wall={elapsed/3600:.3f} h  GPU-seconds={gpu_seconds:.0f}")
    if p.returncode != 0:
        raise RuntimeError(f"{arm} seed {seed} exited {p.returncode}")
    return {"arm": arm, "seed": seed, "gpu_seconds": gpu_seconds}


@app.function(image=image, gpu="A10G", volumes={"/data": vol, OUT: out_vol},
              timeout=TIMEOUTS["C1"])
def train_c1(seed: int):
    return _run_arm("C1", seed)


@app.function(image=image, gpu="A10G", volumes={"/data": vol, OUT: out_vol},
              timeout=TIMEOUTS["C2"])
def train_c2(seed: int):
    return _run_arm("C2", seed)


@app.function(image=image, gpu="A10G", volumes={"/data": vol, OUT: out_vol},
              timeout=TIMEOUTS["C4"])
def train_c4(seed: int):
    return _run_arm("C4", seed)


@app.function(image=image, gpu="A10G", volumes={"/data": vol, OUT: out_vol},
              timeout=TIMEOUTS["C5"])
def train_c5(seed: int):
    return _run_arm("C5", seed)


@app.function(image=image, gpu="A10G", volumes={"/data": vol}, timeout=15 * 60)
def smoke():
    """Standalone pre-gate check: environment, Ada compatibility, TF32 off, data present."""
    import torch
    print("=" * 78)
    print(f"python {sys.version.split()[0]}")
    for m in ("torch", "torchvision", "torchmetrics", "numpy", "PIL", "scipy"):
        try:
            mod = __import__(m)
            print(f"{m:12} {getattr(mod, '__version__', '?')}")
        except Exception as e:
            print(f"{m:12} FAILED {e}")
    print(f"torch.version.cuda {torch.version.cuda}  cudnn {torch.backends.cudnn.version()}")
    print("=" * 78)
    _cuda_smoke_test()
    _disable_tf32()
    import hashlib
    h = hashlib.sha256()
    with open(f"{DATA}/latest_net_G.pth", "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    n_pairs = len(os.listdir(f"{DATA}/pairs/train"))
    print(f"[data] pretrained sha256 {h.hexdigest()}")
    print(f"[data] training pairs {n_pairs}")
    # str() casts: torch.__version__ is a TorchVersion (str subclass) whose unpickling
    # needs torch installed locally, which the driver does not have.
    return {"pretrained_sha256": h.hexdigest(), "pairs": n_pairs,
            "torch": str(torch.__version__), "cuda": str(torch.version.cuda)}


@app.local_entrypoint()
def gate_seed43():
    """AMENDMENT SEED-b hardware gate: seed 43, all four arms, on A10G."""
    seed = 43
    t0 = time.time()
    results = []
    for fn in (train_c1, train_c2, train_c4, train_c5):
        results.append(fn.remote(seed))
    total = sum(r["gpu_seconds"] for r in results)
    print("\n" + "=" * 78)
    for r in results:
        print(f"  {r['arm']} seed {r['seed']}: {r['gpu_seconds']:.0f} GPU-seconds "
              f"({r['gpu_seconds']/3600:.2f} h)")
    # A10G on-demand list price at the time of writing; used only for a credit estimate.
    A10G_USD_PER_HOUR = 1.10
    print(f"  TOTAL {total:.0f} GPU-seconds = {total/3600:.2f} A10G-hours "
          f"~ ${total/3600*A10G_USD_PER_HOUR:.2f} of the $30 monthly credit")
    print(f"  wall clock {(time.time()-t0)/3600:.2f} h")
    print("=" * 78)
