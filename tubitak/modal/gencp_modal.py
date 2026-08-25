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
    # LPIPS backbone weights baked in at BUILD time, not downloaded at run time.
    # These weights ARE PART OF C4/C5's objective function: torchmetrics' LPIPS uses this
    # VGG-16 as its feature extractor, so if the file differed between platforms those two
    # arms would be training against a different loss and nothing would report it.
    # Kaggle fetched the same URL on every LPIPS run (verified in all six c4/c5 logs).
    # torchvision verifies only the 8-hex (32-bit) prefix in the filename; the FULL sha256 is
    # pinned here and asserted at preflight. See AMENDMENT SEED-b.
    .run_commands(
        "mkdir -p /root/.cache/torch/hub/checkpoints",
        "python -c \"import urllib.request; urllib.request.urlretrieve("
        "'https://download.pytorch.org/models/vgg16-397923af.pth',"
        "'/root/.cache/torch/hub/checkpoints/vgg16-397923af.pth')\"",
        "python -c \"import hashlib,sys; "
        "h=hashlib.sha256(open('/root/.cache/torch/hub/checkpoints/vgg16-397923af.pth','rb')"
        ".read()).hexdigest(); "
        "assert h=='" + "397923af8e79cdbb6a7127f12361acd7a2f83e06b05044ddf496e83de57a5bf0" + "', h; "
        "print('[image] vgg16 sha256 verified', h)\"",
    )
)

VGG_PATH = "/root/.cache/torch/hub/checkpoints/vgg16-397923af.pth"
EXPECTED_VGG_SHA256 = "397923af8e79cdbb6a7127f12361acd7a2f83e06b05044ddf496e83de57a5bf0"
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

# The repository commit every container checks out. PINNED, not `-b tubitak-tr`, because a
# bare branch clone takes whatever HEAD happens to be at container start: on 2026-08-25 three
# commits landed at 19:16:15 WHILE the gate was running, one of which modified
# tubitak/kaggle/train_c1_c2.py - the training script itself. C1/C2/C4/C5 had already cloned
# the older code, so the next arm would have run a different code version inside the same
# gate. That diff turned out to be behaviour-preserving (open() -> with open()), but the
# hazard is structural and this closes it.
#
# f2dc962 carries the train_c1_c2.py that ALL FOUR completed seed-43 arms ran:
#     sha256(train_c1_c2.py) 839e1aadd8b88a7be6b7...  at 4817b90 (C1,C2) and f2dc962 (C4,C5)
#     sha256(train_c1_c2.py) 878fa2009683277e28f1...  at 96503b7 (the mid-run commit)
GIT_COMMIT = "f2dc962"

# The ordered file-list hash the SORTED code path must produce - the Modal Volume's own
# enumeration, which the committed patch restores on local disk (AMENDMENT SEED-b). Asserting
# this covers BOTH failure classes at once: a count change (the AppleDouble doubling) and a
# same-count change to contents or order, which a count check cannot see.
EXPECTED_ORDER_SHA256 = "4b5f232034261ed1a2b051db6e17d1dd6a1424ba9225bb49c5e3433e8493cad9"
EXPECTED_N_FILES = 5577
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
    subprocess.run(["git", "clone", "https://github.com/mvy0502/GenCP.git", repo], check=True)
    subprocess.run(["git", "checkout", "--detach", GIT_COMMIT], cwd=repo, check=True)
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo,
                          capture_output=True, text=True, check=True).stdout.strip()
    print(f"[repo] pinned checkout {GIT_COMMIT} -> HEAD {head}", flush=True)
    tsha = _sha256_file(f"{repo}/tubitak/kaggle/train_c1_c2.py")
    print(f"[repo] train_c1_c2.py sha256: {tsha}", flush=True)

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

    # LPIPS backbone: part of C4/C5's objective, so it is pinned and checked like any other
    # input, not left to a runtime download.
    vggsha = _sha256_file(VGG_PATH) if os.path.exists(VGG_PATH) else None
    print(f"[weights] vgg16-397923af.pth sha256: {vggsha}", flush=True)
    assert vggsha == EXPECTED_VGG_SHA256, (
        f"LPIPS VGG weights differ from the pinned value - refusing to train.\n"
        f"  expected {EXPECTED_VGG_SHA256}\n  got      {vggsha}")

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
    # Hard gate on the file count. The first tar was built on macOS and libarchive stored an
    # xattr header per entry; GNU tar on Linux materialised each as an AppleDouble "._name"
    # file, which is_image_file() then accepted because it still ends in .tif. The staged set
    # came to n=11154 - exactly double - half of it 4 KB metadata junk, and training would
    # have run on it. Content hashes all still matched, so only a count/order check could see
    # it. The tar is now built with --no-xattrs; this assertion is the standing guard.
    # Count first: when it IS the count that broke, this gives the clearer message.
    assert n == EXPECTED_N_FILES, (
        f"staged training set has {n} files, expected {EXPECTED_N_FILES} - refusing to train. "
        f"first three: {first}")
    # Then the ordered-list hash, which is the real guard: it also catches a corruption that
    # preserves the count while changing contents or order, which the count cannot.
    if sort_files:
        assert oh == EXPECTED_ORDER_SHA256, (
            f"staged file list does not match the expected ordered hash - refusing to train.\n"
            f"  expected {EXPECTED_ORDER_SHA256}\n  got      {oh}\n  first three: {first}")
        print("[stage] ordered-list hash matches the expected value", flush=True)
    else:
        # The unsorted control cannot be asserted against a fixed value: raw ext4 enumeration
        # depends on the per-directory hash seed, so it is not stable across containers. That
        # is a property of the control, not a gap - it measures "an unsorted order", not one
        # specific alternative ordering. Recorded so the asymmetry is not read as an oversight.
        print(f"[stage] unsorted control - order hash {oh} NOT asserted "
              f"(raw ext4 order is not stable across containers)", flush=True)

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


@app.function(image=image, timeout=24 * 60 * 60, retries=0,
              volumes={OUT: out_vol})
def gate_driver(seed: int, arms=None):
    """Sequence the gate arms from inside Modal, with three fixes from the C4 failure.

    1. retries=0. Retrying a SEQUENCER is never correct: it re-executes completed work, which
       is exactly what happened - C4 failed, the driver was retried, and it began re-running
       C1 and C2 that had already succeeded. Retries belong on individual arms if anywhere,
       never on the thing that orders them.
    2. Per-arm failure isolation. One arm failing no longer kills the chain or discards
       completed work; the failure is recorded and the remaining arms still run.
    3. Skip-completed. An arm already present in the output Volume is not re-run, which also
       makes the whole gate resumable after any interruption.
    """
    t0 = time.time()
    fns = {"C1": train_c1, "C2": train_c2, "C4": train_c4, "C5": train_c5,
           "C2_unsorted": train_c2_unsorted}
    order = arms or ["C1", "C2", "C4", "C5", "C2_unsorted"]
    results, failures = [], []
    for name in order:
        out_vol.reload()
        if os.path.isdir(f"{OUT}/seed{seed}/{name}"):
            print(f"[driver] SKIP {name} - already present in the output Volume", flush=True)
            continue
        try:
            r = fns[name].remote(seed)
            results.append(r)
            print(f"[driver] OK {r['arm']} in {r['gpu_seconds']/3600:.2f} h", flush=True)
        except Exception as exc:
            failures.append({"arm": name, "error": repr(exc)[:2000]})
            print(f"[driver] FAILED {name}: {exc!r}", flush=True)
            print(f"[driver] continuing with the remaining arms", flush=True)
    total = sum(r["gpu_seconds"] for r in results)
    A10G_USD_PER_HOUR = 1.10
    print("\n" + "=" * 78, flush=True)
    for r in results:
        print(f"  {r['arm']:12} sorted={r['sorted']}  {r['gpu_seconds']:.0f} s "
              f"({r['gpu_seconds']/3600:.2f} h)", flush=True)
    for f in failures:
        print(f"  {f['arm']:12} FAILED  {f['error'][:200]}", flush=True)
    print(f"  TOTAL {total:.0f} GPU-seconds = {total/3600:.2f} A10G-hours "
          f"~ ${total/3600*A10G_USD_PER_HOUR:.2f}", flush=True)
    print(f"  driver wall clock {(time.time()-t0)/3600:.2f} h", flush=True)
    print("=" * 78, flush=True)
    return {"results": results, "failures": failures,
            "total_gpu_seconds": float(total),
            "usd": float(total / 3600 * A10G_USD_PER_HOUR)}


@app.local_entrypoint()
def gate_seed43():
    """Spawn the Modal-side driver and exit. Nothing after this depends on this machine."""
    call = gate_driver.spawn(43, ["C4", "C5", "C2_unsorted"])
    print(f"[launch] gate driver spawned on Modal, call id {call.object_id}")
    print("[launch] the laptop can be closed - sequencing runs inside Modal, not here.")
    print("[launch] progress: modal app logs, or check the gencp-out Volume.")


@app.function(image=image, volumes={OUT: out_vol}, timeout=30 * 60)
def verify_latest(seed: int):
    """Per arm on the output Volume: latest_net_G.pth tensor-equal to 20_net_G.pth, plus the
    sha256 of latest.

    The local evaluation downloads latest_net_G.pth ONLY, so the equality check that
    seed_eval_run.py::step_infer performs when both files are present is performed HERE,
    where both files live. The printed sha256 is what the local run asserts its downloaded
    file against - transfer integrity and identity in one line.
    """
    import hashlib
    import torch
    res = {}
    base = f"{OUT}/seed{seed}"
    for tag in sorted(os.listdir(base)):
        arm = "C2" if tag.startswith("C2") else tag        # C2_unsorted stores under .../C2
        d = f"{base}/{tag}/{arm}"
        a = torch.load(f"{d}/latest_net_G.pth", map_location="cpu")
        b = torch.load(f"{d}/20_net_G.pth", map_location="cpu")
        eq = set(a) == set(b) and all(torch.equal(a[k], b[k]) for k in a)
        h = hashlib.sha256(open(f"{d}/latest_net_G.pth", "rb").read()).hexdigest()
        res[tag] = {"tensor_equal_latest_20": bool(eq), "latest_sha256": h}
        print(f"[verify] {tag}: latest==20 tensor-equal {eq}   latest sha256 {h}", flush=True)
    assert all(r["tensor_equal_latest_20"] for r in res.values()), \
        f"latest_net_G.pth is not epoch 20 for some arm: {res}"
    return res


@app.function(image=image, volumes={"/data": vol}, timeout=60 * 60)
def order_check():
    """Four hashes, so the framing claim in AMENDMENT SEED-b is verified and not asserted.

    The claim is that sorting RESTORES the order the Volume was already giving, rather than
    imposing a new one on Modal. That is only true if (a) the Volume's own enumeration is
    already sorted and (b) the sorted local enumeration equals it. Both are checked here.
    """
    v_raw, v_n, v_first = _ordered_list_hash(f"{DATA}/pairs/train", sort_files=False)
    v_srt, _, _ = _ordered_list_hash(f"{DATA}/pairs/train", sort_files=True)
    _stage_local()
    l_raw, l_n, l_first = _ordered_list_hash(f"{LOCAL_DATA}/pairs/train", sort_files=False)
    l_srt, _, l_sfirst = _ordered_list_hash(f"{LOCAL_DATA}/pairs/train", sort_files=True)
    sha_vol = _sha256_file(f"{DATA}/latest_net_G.pth")
    sha_loc = _sha256_file(f"{LOCAL_DATA}/latest_net_G.pth")
    return {"volume_raw": v_raw, "volume_sorted": v_srt, "volume_n": int(v_n),
            "local_raw": l_raw, "local_sorted": l_srt, "local_n": int(l_n),
            "volume_already_sorted": bool(v_raw == v_srt),
            "sort_restores_volume_order": bool(l_srt == v_raw),
            "local_raw_differs_from_volume": bool(l_raw != v_raw),
            "pretrained_volume": sha_vol, "pretrained_local": sha_loc,
            "volume_first": v_first, "local_raw_first": l_first, "local_sorted_first": l_sfirst}


@app.local_entrypoint()
def check_order():
    r = order_check.remote()
    print("\n" + "=" * 78)
    print("ENUMERATION ORDER - does sorting RESTORE the Volume's order, or impose a new one?")
    print("=" * 78)
    print(f"  file count   volume {r['volume_n']}   local {r['local_n']}   (must both be 5577)")
    print(f"  volume, raw enumeration   : {r['volume_raw']}")
    print(f"  volume, sorted            : {r['volume_sorted']}")
    print(f"  local,  raw enumeration   : {r['local_raw']}")
    print(f"  local,  sorted            : {r['local_sorted']}")
    print()
    print(f"  Volume was ALREADY sorted            : {r['volume_already_sorted']}")
    print(f"  local raw DIFFERS from volume        : {r['local_raw_differs_from_volume']}")
    print(f"  sorting RESTORES the volume order    : {r['sort_restores_volume_order']}")
    print()
    print(f"  volume first three     : {r['volume_first']}")
    print(f"  local raw first three  : {r['local_raw_first']}")
    print(f"  local sorted first     : {r['local_sorted_first']}")
    print(f"  pretrained match       : {r['pretrained_volume'] == r['pretrained_local']}")
    print("=" * 78)
