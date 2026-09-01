# WP16 Part A — the checkpoint, which failed in two directions

**Repository** `mvy0502/GenCP`, branch `tubitak-tr`. **Date** 1 September 2026.
**Code changed** `tubitak/sr/sr_train/train.py`, `evaluate.py`, `export_onnx.py`. `sr_train`
only; the plugin was not touched.
**Machine** Apple M4 Max, macOS 26.5.1, arm64. **Environment** `gencp`: python 3.11.15,
torch 2.13.0, numpy 2.4.6.

Two symptoms were suspected of being one defect. **They are not.** Measured, they are
independent, and each is fixed by a different change.

| symptom | cause | fix |
|---|---|---|
| `torch.save` hangs at the final checkpoint, `last.pt` truncated at 8192 bytes, 4 runs of 4 | an **outstanding `.to(device, non_blocking=True)` host-to-device copy** that was never consumed; `torch.save` then blocks copying an MPS storage back to the host | synchronise the device before serialising |
| `torch.load` refuses our own checkpoints | `versions()` stored `torch.__version__`, a **`TorchVersion`**, a `str` subclass that `weights_only=True` will not unpickle | store versions as plain `str` |

The evidence that they are separate is direct: a payload carrying `TorchVersion` objects
**saves without hanging** (case `versions_obj` below), and the smallest payload that hangs
contains no version record at all.

---

## 1. The stack, captured rather than inferred

The reproduction registers `faulthandler.dump_traceback_later(60, exit=True)` before the save.
On the failing case it fires:

```
Timeout (0:01:00)!
Thread 0x000000016fa6b000 (most recent call first):
  <no Python frame>

Thread 0x000000016fb83000 (most recent call first):
  <no Python frame>

Thread 0x00000001ed69de80 (most recent call first):
  File ".../torch/storage.py", line 264 in cpu
  File ".../torch/serialization.py", line 1310 in _save
  File ".../torch/serialization.py", line 1003 in save
  File ".../wp16_repro.py", line 87 in main
```

`torch.save` → `_save` → `storage.cpu()`. It is blocked copying a device storage to the host,
inside the serialiser. The two threads with no Python frame are the MPS backend's. The output
file at that moment is **8192 bytes** — the production signature exactly.

---

## 2. Bisecting the dictionary

Each case runs 12 real optimiser steps of the real `SRNet` on MPS, then saves. `stray=1` leaves
one unconsumed `.to(device, non_blocking=True)` pair alive, which is what the training loop
does; `stray=0` leaves none; `stray=2` leaves a live MPS tensor transferred **blocking**.

| case | payload | stray | result |
|---|---|---|---|
| `full` | model + opt + step + best | 1 | **HUNG**, 8192 bytes |
| `full` | same | 0 | saved, 5 900 871 bytes, 0.4 s |
| `model_only` | model state dict | 1 | **HUNG**, 0 bytes |
| `opt_only` | Adam state | 1 | **HUNG**, 4096 bytes |
| `tiny` | `{"t": torch.zeros(4, device="mps")}` | 1 | **HUNG**, 0 bytes |
| `tiny` | same | 0 | saved, 1612 bytes |
| `tiny` | same | 2 (blocking) | saved, 1612 bytes |
| `tiny_cpu` | `{"t": torch.zeros(4)}` | 1 | saved, 1633 bytes |
| `scalars` | `{"step": 1, "best": 0.1}` | 1 | saved, 1303 bytes |
| `cpu_state` | state dicts moved to host first | 1 | saved, 5 900 541 bytes |
| `versions_obj` | `{"step": 1, "versions": {...TorchVersion...}}` | 1 | **saved**, 1461 bytes |
| `versions_str` | same with plain strings | 1 | saved, 1461 bytes |
| `full` on **CPU** device | model + opt | 1 | saved, 5 900 743 bytes |

### The smallest thing that hangs

> **`torch.save({"t": torch.zeros(4, device="mps")})` — a four-element tensor — while an
> unconsumed `.to(device, non_blocking=True)` host-to-device copy is still outstanding.**

Four elements. The dictionary's contents are almost irrelevant: any MPS-resident storage in
the payload is enough. What matters is the outstanding asynchronous copy.

Three facts pin it down:

- **It must be the non-blocking transfer.** A live MPS tensor transferred *blocking*
  (`stray=2`) saves fine. Merely holding device memory is not the trigger.
- **Dropping the Python reference does not help.** `drop_stray=1` deletes the name before
  saving; it still hangs at 8192 bytes. The pending copy is queued in the device, not held by
  the variable.
- **`torch.mps.synchronize()` fixes it.** Same failing case, one line added: saved, 5 900 997
  bytes.

### Why the periodic saves survived and only the last one hung

`CHECKPOINT_EVERY = 500` over 20 000 steps means `last.pt` was written 40 times successfully
before the write that hung. The asymmetry is in the loop, not the data. Inside the loop each
batch is consumed by forward and backward, which synchronises the device before the next save.
At the end, `while step < total` exits only after the inner `for lo, hi in batches(...)`
yields **one more pair** — two non-blocking transfers — and the loop then breaks at
`if step >= total` without using them. That abandoned pair is alive, and unsynchronised, for
the final `torch.save`. Four runs out of four, always the same place.

---

## 3. The fix

`train.py` gains one place where checkpoints are written:

```python
def save_checkpoint(payload, path, dev):
    _sync(dev)                      # torch.mps.synchronize() / torch.cuda.synchronize()
    torch.save(_to_cpu(payload), path)
```

Both halves are deliberate:

- **`_sync`** addresses the cause. Without it the hang is one abandoned batch away from
  returning, whatever else changes.
- **`_to_cpu`** moves tensors to the host and coerces `str` subclasses to `str`. It keeps
  `torch.save` off the internal device-to-host path entirely, and it fixes the second defect:
  a checkpoint that stores MPS-resident storages and `TorchVersion` objects can only be read
  back on a Mac, with the safety check disabled. That is the opposite of what standing
  practice 9's version record is for.

`versions()` now calls `str()` on every value it records. The `_to_cpu` coercion is
belt-and-braces: a payload assembled anywhere else cannot reintroduce the defect.

The three loaders (`train.py --resume`, `evaluate.py`, `export_onnx.py`) now try
`weights_only=True` first and fall back **with a printed note**, so the existing pre-WP16
checkpoints still load and a silent `weights_only=False` everywhere does not become permanent:

```
note: best.pt is a pre-WP16 checkpoint (weights_only=True refused it: UnpicklingError);
      re-reading with weights_only=False
```

---

## 4. Evidence

**E1 — the hang is gone.** The reproduction's exact failing state (12 real steps on MPS, one
abandoned non-blocking pair alive), saved through the shipped `save_checkpoint`:

```
save_checkpoint returned in 0.07s, 5,899,533 bytes
```

**E2 — a checkpoint saved the new way loads back.** With torch's **default**
`weights_only=True`, no override:

```
torch.load(weights_only=True) succeeded; keys ['best','model','opt','step','train_device','versions']
versions = {'torch': '2.13.0', 'numpy': '2.4.6', 'python': '3.11.15',
            'onnxruntime': '1.29.0', 'mps': True}
types    = ['str', 'str', 'str', 'str', 'bool']
tensor device as stored: cpu
```

**E3 — no weight changes.** The real shipped checkpoint
(`sr_train_runs_tci_v2/run1/best.pt`, the TCI v2 model) was re-saved through the new path and
compared:

- the old file is refused by `weights_only=True` (`UnpicklingError`, `TorchVersion` not an
  allowed global); the re-saved one is accepted;
- version **text** preserved: `2.13.0` → `2.13.0`;
- **all 30 weight tensors bit-equal**, `torch.equal` on every one.

**E4 — the exported model is bit-identical.** ONNX exported from each checkpoint, same
filename so the `checkpoint` metadata field matches, everything else unchanged:

| exported from | sha256 |
|---|---|
| old-format checkpoint | `01496736913ac257f8f57ccb26e1c4220e903b6c309712ebcc48e0b834485920` |
| new-format checkpoint | `01496736913ac257f8f57ccb26e1c4220e903b6c309712ebcc48e0b834485920` |

**Bit-identical** — and that hash is the published `gencp_sr_tci_x4_b3_v2.onnx` in
`sr-plugin-v0.1.0`. The new checkpoint format reproduces the shipped model byte for byte.

**E5 — a real training run.** 120 steps, `--val-every=60`, on the corrected TCI corpus,
through the patched code end to end: exit 0, `last.pt` **6 142 485 bytes** (not 8192),
`best.pt` 6 142 933 bytes, both loading under `weights_only=True`. The run directory was
removed afterwards; it was a smoke test, not a model.

---

## 5. What was not done, and why the fix is still the right one

The controlled A/B is the reproduction harness, not a full 20 000-step run: the harness fails
deterministically in seconds with the production signature, and a full run costs half an hour
per arm. **The claim "the fix prevents the hang" therefore rests on the harness, and the claim
"the fix does not break training" rests on E5.** Neither is a 20 000-step run under the fix,
and the next real training run is the first one of those.

`torch.mps.synchronize()` alone would fix the hang without changing the file at all. Both were
taken because a checkpoint readable only on the machine that wrote it is a poor record, and
E3/E4 show the format change costs nothing: same weights, same exported bytes.

---

## 6. Open items

1. No 20 000-step run has yet completed under the fix. The harness reproduces and the smoke
   run passes; the real confirmation is the next training run.
2. `_sync` handles `mps` and `cuda`. Any other accelerator falls through silently and would
   need its own branch.
3. The pre-WP16 checkpoints on disk — including the ones the three shipped models were
   exported from — remain in the old format. They load through the announced fallback. They
   are not rewritten, because rewriting them would change files that existing evidence
   documents refer to by hash.
4. Whether this is a torch 2.13 / MPS bug worth reporting upstream was not investigated. The
   reproduction is four lines and would make a clean report.
