#!/usr/bin/env python3
"""D19 — training. Charbonnier only, no adversarial or perceptual term.

Model selection uses the `val` split ONLY. The two test sets are not opened by this file at
all: `data.load_split` is called for 'train' and 'val' and for nothing else, which is the
mechanical form of the promise that the test sets are read once, at the end of Part C.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
import torch

SR = Path(__file__).resolve().parents[1]
if str(SR) not in sys.path:
    sys.path.insert(0, str(SR))

from sr_data import params as P                                         # noqa: E402
from sr_data.degrade import degrade_chip                                # noqa: E402
from sr_train import config as C, data as D                             # noqa: E402
from sr_train.model import SRNet, charbonnier                           # noqa: E402


def versions():
    import numpy, torch as _t
    # str() on every one of these. torch.__version__ is a TorchVersion, not a str, and a
    # checkpoint containing one cannot be read back under torch's default
    # weights_only=True - standing practice 9's version record was what made the record
    # unreadable. WP16: this is a SEPARATE defect from the save hang; measured, a payload
    # carrying TorchVersion objects saves without hanging.
    v = dict(torch=str(_t.__version__), numpy=str(numpy.__version__),
             python=sys.version.split()[0])
    try:
        import onnxruntime; v["onnxruntime"] = str(onnxruntime.__version__)
    except Exception:
        v["onnxruntime"] = "absent"
    if _t.cuda.is_available():
        v["cuda"] = str(_t.version.cuda)
        v["gpu"] = str(_t.cuda.get_device_name(0))
    v["mps"] = bool(getattr(_t.backends, "mps", None) and _t.backends.mps.is_available())
    return v



def _sync(dev):
    """Drain outstanding asynchronous work on `dev` before anything reads its memory.

    WP16: `torch.save` hung on four training runs out of four, always at the final
    checkpoint, always leaving `last.pt` truncated at 8192 bytes. The stack, captured with
    faulthandler rather than inferred, was blocked in `torch/storage.py:264 in cpu` -
    `torch.save` copying an MPS storage to the host from inside `_save`.

    The trigger is not the dictionary's contents. It is an OUTSTANDING
    `.to(device, non_blocking=True)` host-to-device copy that was never consumed. The
    training loop leaves exactly one: after the last optimiser step, `batches()` yields one
    more pair - two non-blocking transfers - and the loop then breaks without using them.
    The periodic saves inside the loop never hit this because their batch had been consumed
    by forward and backward, which synchronises.

    Measured: with such a transfer outstanding, `torch.save({"t": torch.zeros(4,
    device="mps")})` - four elements - hangs. With it consumed, or transferred blocking, or
    after this synchronise, the full 5.9 MB checkpoint saves in 0.4 s. Dropping the Python
    reference to the stray tensor does NOT help; the copy is queued in the device, not held
    by the name.
    """
    if dev.type == "mps" and getattr(torch, "mps", None):
        torch.mps.synchronize()
    elif dev.type == "cuda":
        torch.cuda.synchronize()


def _to_cpu(obj):
    """Recursively detach tensors onto the host, structure preserved.

    A checkpoint holding MPS-resident storages can only be read back on a machine with
    MPS. That makes the training record hostage to the hardware that produced it, which is
    the opposite of what standing practice 9 is for. Saving from the host also keeps
    `torch.save` off the internal device-to-host path entirely.
    """
    if torch.is_tensor(obj):
        return obj.detach().to("cpu")
    if isinstance(obj, str) and type(obj) is not str:
        # A str SUBCLASS - torch.__version__ is a TorchVersion - pickles as its class, and
        # weights_only=True refuses classes it does not know. The text is identical; only
        # the type makes the record unreadable. Coerced here as well as in versions(), so a
        # payload assembled anywhere else cannot reintroduce the defect.
        return str(obj)
    if isinstance(obj, dict):
        return {k: _to_cpu(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return type(obj)(_to_cpu(v) for v in obj)
    return obj


def load_checkpoint(path, map_location="cpu"):
    """Load a checkpoint, preferring torch's safe reader.

    Pre-WP16 checkpoints store `TorchVersion` objects, which `weights_only=True` refuses.
    Those files are our own, written by this script, so falling back is safe - but the
    fallback is announced, because a silent `weights_only=False` everywhere is how the safe
    default stops meaning anything.
    """
    try:
        return torch.load(path, map_location=map_location, weights_only=True)
    except Exception as e:
        print(f"  note: {Path(path).name} is a pre-WP16 checkpoint (weights_only=True "
              f"refused it: {type(e).__name__}); re-reading with weights_only=False",
              flush=True)
        return torch.load(path, map_location=map_location, weights_only=False)


def save_checkpoint(payload, path, dev):
    """The one place a checkpoint is written. Synchronise, move to host, then save.

    `versions()` already returns plain strings (see its own note), so the result loads
    under torch's default `weights_only=True`.
    """
    _sync(dev)
    torch.save(_to_cpu(payload), path)


def pick_device(want=None):
    if want and want != "auto":
        return torch.device(want)
    if torch.cuda.is_available():
        return torch.device("cuda")
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def dihedral(x, k):
    """One of the 8 dihedral transforms of the last two axes. k in [0, 8)."""
    if k & 4:
        x = np.flip(x, axis=-1)
    return np.rot90(x, k & 3, axes=(-2, -1))


class Pairs:
    """Degraded input / target pairs for one split, degraded ONCE up front.

    `degrade_chip` is imported from sr_data, never reimplemented, and the divisor is asserted
    against the registration rather than written again.

    Degrading once and augmenting afterwards is only valid because the degradation COMMUTES
    with the 8 dihedral transforms: the low-pass kernel is separable, symmetric, and its
    decimation phase is symmetric about the 2x2 block centre. That is not assumed - it is
    checked by `check_commutes()` and the training run refuses to start if it fails.
    """

    def __init__(self, split, limit=None):
        chips, recs = D.load_split(split)
        if limit:
            chips, recs = chips[:limit], recs[:limit]
        div = D.assert_norm_divisor(C.NORM_DIVISOR_DN)
        lo, hi = [], []
        for i in range(chips.shape[0]):
            # scale MUST be passed: degrade_chip's default comes from params.SCALE (2),
            # so a variant that does not pass it silently degrades at the wrong factor.
            a, b = degrade_chip(chips[i], div, scale=C.SCALE)
            lo.append(a); hi.append(b)
        self.lo = np.stack(lo).astype(np.float32)
        self.hi = np.stack(hi).astype(np.float32)
        self.recs = recs

    def __len__(self):
        return self.lo.shape[0]


def check_commutes(n=8, seed=C.TRAIN_SEED):
    """Known-true/known-false for the commutation the Pairs cache depends on."""
    rng = np.random.default_rng(seed)
    x = (rng.random((C.N_BANDS, C.CHIP_PX, C.CHIP_PX)) * 3000 + 500).astype(np.uint16)
    div = C.NORM_DIVISOR_DN
    worst = 0.0
    for k in range(8):
        a, _ = degrade_chip(np.ascontiguousarray(dihedral(x, k)), div, scale=C.SCALE)
        b, _ = degrade_chip(x, div, scale=C.SCALE)
        worst = max(worst, float(np.abs(a - np.ascontiguousarray(dihedral(b, k))).max()))
    # known-false: an ASYMMETRIC degradation must NOT commute
    def shifted(t, d):
        # D27: phase-0 decimation by the CONFIGURED scale, no filter. It was hard-coded to
        # ::2, which at s=4 still returns a differing array - so the gate reported success
        # while no longer testing the s=4 phase at all. A known-false that has decayed into a
        # no-op is worse than none, because it looks like coverage.
        return t[:, ::C.SCALE, ::C.SCALE].astype(np.float32) / d
    bad = 0.0
    for k in range(8):
        a = shifted(np.ascontiguousarray(dihedral(x, k)), div)
        b = np.ascontiguousarray(dihedral(shifted(x, div), k))
        bad = max(bad, float(np.abs(a - b).max()))
    return worst, bad


def batches(pairs, batch, rng, device, augment=True):
    n = len(pairs)
    order = rng.permutation(n)
    for s in range(0, n - batch + 1, batch):
        idx = order[s:s + batch]
        lo, hi = pairs.lo[idx], pairs.hi[idx]
        if augment:
            k = rng.integers(0, 8)
            lo = np.ascontiguousarray(dihedral(lo, k))
            hi = np.ascontiguousarray(dihedral(hi, k))
        yield (torch.from_numpy(lo).to(device, non_blocking=True),
               torch.from_numpy(hi).to(device, non_blocking=True))


@torch.no_grad()
def validate(model, pairs, device, batch=16):
    model.eval()
    tot, n = 0.0, 0
    for s in range(0, len(pairs), batch):
        lo = torch.from_numpy(pairs.lo[s:s + batch]).to(device)
        hi = torch.from_numpy(pairs.hi[s:s + batch]).to(device)
        tot += float(charbonnier(model(lo), hi)) * lo.shape[0]
        n += lo.shape[0]
    return tot / max(n, 1)


def main():
    ap = argparse.ArgumentParser(prog="train.py")
    ap.add_argument("--steps", type=int, default=20000)
    ap.add_argument("--batch", type=int, default=C.BATCH)
    ap.add_argument("--lr", type=float, default=C.LR)
    ap.add_argument("--device", default="auto")
    ap.add_argument("--run", default=None, help="run directory")
    ap.add_argument("--resume", default=None, help="checkpoint to resume from")
    ap.add_argument("--probe", type=int, default=0, help="timing probe: run N steps and stop")
    ap.add_argument("--budget-min", type=float, default=None, help="wall-clock stop rule")
    ap.add_argument("--val-every", type=int, default=500)
    ap.add_argument("--limit-train", type=int, default=None)
    a = ap.parse_args()

    dev = pick_device(a.device)
    torch.manual_seed(C.TRAIN_SEED)
    rng = np.random.default_rng(C.TRAIN_SEED)
    run = Path(a.run or (C.data_root() / C.RUN_SUBDIR / "run1"))
    run.mkdir(parents=True, exist_ok=True)

    ok, bad = check_commutes()
    print(f"degradation commutes with the 8 dihedral transforms: max |diff| {ok:.3e}")
    print(f"  known-false (phase-0 decimation, no filter): max |diff| {bad:.3e}")
    if ok > 1e-6:
        raise SystemExit("train: degradation does NOT commute with the dihedral group; "
                         "the pre-degraded cache would be wrong. Refusing to train.")
    if bad <= 1e-6:
        raise SystemExit("train: the commutation check cannot fail; it is not a check.")

    t_load = time.perf_counter()
    tr = Pairs("train", limit=a.limit_train)
    va = Pairs("val")
    print(f"train {len(tr)} chips, val {len(va)} chips, loaded+degraded in "
          f"{time.perf_counter()-t_load:.1f} s  (test sets NOT opened)")

    model = SRNet(bands=C.N_BANDS, scale=C.SCALE).to(dev)
    opt = torch.optim.Adam(model.parameters(), lr=a.lr, betas=(0.9, 0.999))
    step0, best = 0, float("inf")
    if a.resume:
        # Safe reader first; pre-WP16 checkpoints store TorchVersion objects and need the
        # announced fallback. See load_checkpoint.
        ck = load_checkpoint(a.resume, map_location=dev)
        model.load_state_dict(ck["model"]); opt.load_state_dict(ck["opt"])
        step0, best = ck["step"], ck.get("best", float("inf"))
        rng = np.random.default_rng(C.TRAIN_SEED + step0)
        print(f"resumed from {a.resume} at step {step0}, best val {best:.6f}")

    total = a.probe or a.steps
    print(f"device {dev}  params {model.n_params():,}  batch {a.batch}  steps {step0}->{total}")
    hist, t0, step = [], time.perf_counter(), step0
    stop_reason = "steps"
    while step < total:
        model.train()
        for lo, hi in batches(tr, a.batch, rng, dev):
            if step >= total:
                break
            frac = step / max(total - 1, 1)
            lr = C.LR_MIN + 0.5 * (a.lr - C.LR_MIN) * (1 + math.cos(math.pi * frac))
            for gp in opt.param_groups:
                gp["lr"] = lr
            loss = charbonnier(model(lo), hi)
            opt.zero_grad(set_to_none=True)
            loss.backward()
            opt.step()
            step += 1
            if step % 50 == 0 or step == total:
                el = time.perf_counter() - t0
                print(f"  step {step:6d}/{total}  loss {float(loss):.6f}  lr {lr:.2e}  "
                      f"{el:7.1f}s  {(step-step0)/max(el,1e-9):.2f} steps/s", flush=True)
            if a.probe and step - step0 >= a.probe:
                break
            if step % a.val_every == 0:
                v = validate(model, va, dev)
                hist.append(dict(step=step, val=v, loss=float(loss)))
                print(f"    val charbonnier {v:.6f}" + ("  * best" if v < best else ""),
                      flush=True)
                if v < best:
                    best = v
                    save_checkpoint(dict(model=model.state_dict(), opt=opt.state_dict(),
                                    step=step, best=best, train_device=str(dev),
                                    versions=versions(), config=dict(
                                        width=C.WIDTH, n_blocks=C.N_BLOCKS, scale=C.SCALE,
                                        norm_divisor_dn=C.NORM_DIVISOR_DN,
                                        bands=list(C.BANDS), variant=C.VARIANT)),
                               run / "best.pt", dev)
            if step % C.CHECKPOINT_EVERY == 0:
                save_checkpoint(dict(model=model.state_dict(), opt=opt.state_dict(),
                                     step=step, best=best), run / "last.pt", dev)
            if a.budget_min and (time.perf_counter() - t0) / 60.0 >= a.budget_min:
                stop_reason = "budget"
                break
        if a.probe and step - step0 >= a.probe:
            stop_reason = "probe"
            break
        if stop_reason == "budget":
            break

    el = time.perf_counter() - t0
    rate = (step - step0) / max(el, 1e-9)
    rec = dict(work_package=C.WORK_PACKAGE, device=str(dev), params=model.n_params(),
               batch=a.batch, steps_done=step - step0, step_from=step0, step_to=step,
               wall_clock_s=el, steps_per_s=rate, best_val=best, stop_reason=stop_reason,
               seed=C.TRAIN_SEED, lr=a.lr, lr_min=C.LR_MIN,
               charbonnier_eps=C.CHARBONNIER_EPS, versions=versions(),
               n_train=len(tr), n_val=len(va), history=hist)
    name = "probe.json" if a.probe else "train_record.json"
    (run / name).write_text(json.dumps(rec, indent=2))
    print(f"\n{step-step0} steps in {el:.1f} s = {rate:.2f} steps/s "
          f"({rate*a.batch:.1f} chips/s), stop: {stop_reason}")
    if a.probe:
        for tgt in (10000, 20000, 40000):
            print(f"  extrapolation: {tgt:6d} steps -> {tgt/rate/60:7.1f} min "
                  f"= {tgt/rate/3600:5.2f} h")
    print(f"  wrote {run/name}")
    if not a.probe:
        save_checkpoint(dict(model=model.state_dict(), opt=opt.state_dict(), step=step,
                             best=best), run / "last.pt", dev)
    return 0


if __name__ == "__main__":
    sys.exit(main())
