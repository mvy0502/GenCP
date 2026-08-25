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
DATA_TAR = "/data/gencp-tr.tar"
OUT = "/out"

# Expected wall time per arm on A10G, from the Kaggle T4 times divided by ~3.5, with the
# timeout set to roughly TWICE that. A hung job left to Modal's 24-hour maximum would burn
# most of the monthly credit for nothing.
TIMEOUTS = {"C1": 2 * 60 * 60, "C2": 2 * 60 * 60, "C4": 4 * 60 * 60, "C5": 4 * 60 * 60}


LOCAL_DATA = "/scratch/gencp-tr"


def _ordered_list_hash(root, sort_files=False):
    """Hash the ORDERED dataset file list exactly as pix2pix's make_dataset() builds it.

    data/image_folder.py:make_dataset does `for root, _, fnames in sorted(os.walk(dir))` -
    which sorts the WALK TUPLES but NOT `fnames`, so the per-directory file order is whatever
    the filesystem enumeration returns. A network-backed Modal Volume and a local ext4 can
    enumerate the same directory differently. If they do, the seeded shuffle maps to different
    files, batch composition changes, and the run is not the same run.

    So the hash is over the ordered sequence of names, not over file contents: contents being
    identical is already established by the pretrained sha256 and does not answer this.
    Names are made relative to `root` so the differing path prefixes cannot cause a spurious
    mismatch.
    """
    IMG = (".jpg", ".jpeg", ".png", ".ppm", ".bmp", ".pgm", ".tif", ".tiff", ".webp")
    names = []
    for r, _, fnames in sorted(os.walk(root)):
        for fname in (sorted(fnames) if sort_files else fnames):  # mirrors the patched/unpatched code path
            if fname.lower().endswith(IMG):
                names.append(os.path.relpath(os.path.join(r, fname), root))
    import hashlib
    h = hashlib.sha256("\n".join(names).encode()).hexdigest()
    return h, len(names), names[:3]


def _sha256_file(path):
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _stage_local():
    """Stage the dataset onto container-local disk from a SINGLE tar on the Volume.

    Measured cause (AMENDMENT SEED-b): the Volume is network-backed and pix2pix reads 5,577
    individual small files per epoch. Training on it stalled the dataloader at 0.120-0.491 s
    per image against Kaggle's steady 0.003 s - a 4.9x faster GPU produced a 2x slower run.

    The first fix attempted `cp -r` from the Volume, which is the SAME small-file network cost
    and blew a 30-minute timeout without finishing. So the dataset is staged as one 2.06 GB
    tar: a single sequential read, extracted locally. One large read replaces 5,577 small ones.
    """
    if os.path.exists(LOCAL_DATA):
        return
    os.makedirs("/scratch", exist_ok=True)
    t = time.time()
    # --warning=no-unknown-keyword: the tar was created on macOS and carries
    # com.apple.provenance xattrs, which GNU tar warns about once per file - 1,884 lines
    # that swamped the run output on the first attempt.
    subprocess.run(["tar", "--warning=no-unknown-keyword", "-xf", DATA_TAR, "-C", "/scratch"],
                   check=True, stderr=subprocess.DEVNULL)
    os.rename("/scratch/kaggle_stage", LOCAL_DATA)
    print(f"[stage] extracted tar -> local disk in {time.time()-t:.1f}s", flush=True)


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


def _run_arm(arm: str, seed: int, sort_files: bool = True, label: str = None):
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

    # Enumeration-order patch: COMMITTED as a file, applied with `git apply`, never sed'd in.
    # `git apply` verifies the pre-state and fails loudly if upstream ever differs, so this is
    # a recorded code path rather than an ad hoc one (corrections-log entries 22 and 25).
    # It RESTORES the order the Modal Volume was already giving, on local disk - it is not a
    # new ordering imposed on Modal. See tubitak/modal/patches/README.md.
    patch = f"{repo}/tubitak/modal/patches/image_folder_sorted.patch"
    if sort_files:
        subprocess.run(["git", "apply", "--check", patch], cwd=repo, check=True)
        subprocess.run(["git", "apply", patch], cwd=repo, check=True)
        print("[patch] image_folder_sorted.patch APPLIED (sorted enumeration)", flush=True)
    else:
        print("[patch] image_folder_sorted.patch NOT applied (unsorted control arm)", flush=True)
    ifsha = _sha256_file(f"{repo}/data/image_folder.py")
    print(f"[patch] data/image_folder.py sha256: {ifsha}", flush=True)

    # The training script expects the Kaggle mount layout; the Volume provides the same tree.
    _stage_local()
    # Post-copy verification, not only on the Volume: the initialisation for every arm and
    # every seed must be the same file after staging as before it.
    sha = _sha256_file(f"{LOCAL_DATA}/latest_net_G.pth")
    print(f"[stage] pretrained sha256 after copy: {sha}", flush=True)
    assert sha == "5938576369544301bb5241daf0581330042286dab215abe1d55defeea297a022", \
        f"pretrained generator changed during staging: {sha}"
    oh, n, first = _ordered_list_hash(f"{LOCAL_DATA}/pairs/train", sort_files=sort_files)
    print(f"[stage] ordered file-list sha256 (as this run will read it): {oh}  n={n}", flush=True)
    print(f"[stage] first three: {first}", flush=True)

    os.makedirs("/kaggle/input", exist_ok=True)
    if not os.path.exists("/kaggle/input/gencp-tr"):
        os.symlink(LOCAL_DATA, "/kaggle/input/gencp-tr")
    os.makedirs("/kaggle/working", exist_ok=True)

    env = dict(os.environ, ARM=arm, SEED=str(seed),
               PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True")
    # TF32 off must survive into the training subprocess as well as this one.
    env["NVIDIA_TF32_OVERRIDE"] = "0"

    p = subprocess.run([sys.executable, f"{repo}/tubitak/kaggle/train_c1_c2.py"],
                       cwd=repo, env=env)
    elapsed = time.time() - t0

    tag = label or arm
    dst = f"{OUT}/seed{seed}/{tag}"
    os.makedirs(dst, exist_ok=True)
    subprocess.run(["cp", "-r", f"/kaggle/working/checkpoints/{arm}", dst], check=False)
    out_vol.commit()

    gpu_seconds = elapsed
    print(f"[cost] arm={tag} seed={seed} sorted={sort_files} rc={p.returncode} "
          f"wall={elapsed/3600:.3f} h  GPU-seconds={gpu_seconds:.0f}")
    if p.returncode != 0:
        raise RuntimeError(f"{arm} seed {seed} exited {p.returncode}")
    return {"arm": tag, "seed": seed, "sorted": bool(sort_files),
            "gpu_seconds": float(gpu_seconds), "image_folder_sha256": ifsha,
            "order_hash": oh}


@app.function(image=image, gpu="A10G", volumes={"/data": vol, OUT: out_vol},
              timeout=TIMEOUTS["C1"])
def train_c1(seed: int):
    return _run_arm("C1", seed)


@app.function(image=image, gpu="A10G", volumes={"/data": vol, OUT: out_vol},
              timeout=TIMEOUTS["C2"])
def train_c2(seed: int):
    return _run_arm("C2", seed)


@app.function(image=image, gpu="A10G", volumes={"/data": vol, OUT: out_vol},
              timeout=TIMEOUTS["C2"])
def train_c2_unsorted(seed: int):
    """C2 with the enumeration patch NOT applied - the order-effect control.

    Registered reading (AMENDMENT SEED-b): the difference between this and the sorted C2, at
    fixed hardware and fixed seed, IS the order effect. It is reported beside the s43-to-s44
    seed spread and the larger of the two is stated. This converts "we cannot know what order
    Kaggle used" from an unresolved ambiguity into a measured bound.
    """
    return _run_arm("C2", seed, sort_files=False, label="C2_unsorted")


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
    for fn in (train_c1, train_c2, train_c4, train_c5, train_c2_unsorted):
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


@app.function(image=image, volumes={"/data": vol}, timeout=60 * 60)
def order_check():
    """Compare the ORDERED dataset file list on the Volume against the local copy.

    This is the precondition for calling the local-copy fix scientifically neutral. Content
    identity is not enough: if enumeration order differs, the seeded shuffle maps to different
    files and the run changes.
    """
    vol_h, vol_n, vol_first = _ordered_list_hash(f"{DATA}/pairs/train")
    print(f"[order] VOLUME  sha256={vol_h}  n={vol_n}")
    print(f"[order]   first three: {vol_first}")
    _stage_local()
    loc_h, loc_n, loc_first = _ordered_list_hash(f"{LOCAL_DATA}/pairs/train")
    print(f"[order] LOCAL   sha256={loc_h}  n={loc_n}")
    print(f"[order]   first three: {loc_first}")
    match = vol_h == loc_h
    print(f"[order] ORDER IDENTICAL: {match}")
    if not match:
        vs = set(vol_first) ^ set(loc_first)
        print(f"[order] the fix is NOT order-neutral; an explicit sort must be applied "
              f"and recorded. head symmetric difference: {vs}")
    sha_vol = _sha256_file(f"{DATA}/latest_net_G.pth")
    sha_loc = _sha256_file(f"{LOCAL_DATA}/latest_net_G.pth")
    print(f"[order] pretrained on Volume: {sha_vol}")
    print(f"[order] pretrained local    : {sha_loc}   match={sha_vol == sha_loc}")
    return {"volume_order_sha256": vol_h, "local_order_sha256": loc_h,
            "order_identical": bool(match), "n_files": int(vol_n),
            "pretrained_volume": sha_vol, "pretrained_local": sha_loc}


@app.local_entrypoint()
def check_order():
    """Print the order-check result from the returned dict, so it cannot be lost in stdout."""
    r = order_check.remote()
    print("\n" + "=" * 78)
    print("ORDERED DATASET FILE-LIST HASH - Volume vs container-local copy")
    print("=" * 78)
    print(f"  n files                : {r['n_files']}")
    print(f"  VOLUME order sha256    : {r['volume_order_sha256']}")
    print(f"  LOCAL  order sha256    : {r['local_order_sha256']}")
    print(f"  ORDER IDENTICAL        : {r['order_identical']}")
    print(f"  pretrained on Volume   : {r['pretrained_volume']}")
    print(f"  pretrained after copy  : {r['pretrained_local']}")
    print(f"  pretrained match       : {r['pretrained_volume'] == r['pretrained_local']}")
    print("=" * 78)
