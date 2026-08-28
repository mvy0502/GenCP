# Paper handoff context

What an agent working on the manuscript needs to know before it writes a number down.

## Where things live

Three repositories exist for this project. They are not copies of each other.

| Repository | Role | Who writes |
|---|---|---|
| `mvy0502/GenCP`, branch `tubitak-tr` | **Working repository.** Research record, gate registrations, results, code, QGIS plugin | All agent work happens here |
| `mvy0502/gencp-validation` | **Handover copy** for whoever takes the project over | Destination only — never a source, never merged into |
| `mvy0502/gencp-letter` | Paper (TeX) | Paper work only |

The manuscript is written in `gencp-letter`. Every number in it comes from `tubitak/` in
the **working repository** — not from `gencp-validation`, which is a snapshot and may lag.
Never re-derive a number in the paper repository. Every number must cite the gate or
registration it came from, and must state its inference path.

## Rules that bind the manuscript

1. State the inference path for every number. Two numbers from different paths are not
   comparable.
2. One sign convention, stated: **Δ = candidate − baseline; negative = candidate better.**
   Never flip it mid-report.
3. A number whose registration was revised after the outcome was seen is not quotable.
4. Institutional (TÜBİTAK) imagery must never enter the repository or the manuscript's
   source tree. Google Earth imagery is for internal visual verification only.

## Method-section facts that must be stated

These are properties of the published GenCP pipeline that the manuscript cannot omit
without misdescribing what was measured.

### Normalisation at inference — must appear in the method section

The published GenCP pipeline trains with `--norm batch`, and its `test.py` **never calls
`.eval()`** (the `--eval` flag exists but defaults to false, and nothing in the evaluated
path passes it). Its inference therefore runs on **batch statistics**, which at batch
size 1 is **equivalent to instance normalisation** — verified exactly, max abs
difference 0.0.

**Every number this project has measured was produced in that regime.** The manuscript's
method section must say so. Two reasons it cannot be left implicit:

1. A reader who assumes the conventional `model.eval()` at test time would reproduce
   different images. Measured on the C3 checkpoint, switching to running statistics changes
   **100% of pixels, mean 32 DN, max 94 DN**.
2. The distinction is what makes the delivered ONNX model equivalent to the measured
   pipeline: the export replaces each `BatchNorm2d` with the exactly-equivalent
   `InstanceNorm2d` rather than accepting `torch.onnx.export`'s default `eval()` behaviour.

Source: [plugin-results.md](docs/plugin-results.md), Gate O and Item B.

### Dropout at inference — the second half of the same sentence

pix2pix keeps dropout **active at test time** by design, as the generator's noise source in
place of a `z` vector. The published pipeline does this, and every measured number in this
project carries it. The delivered plugin removes dropout, because a tool must return the
same image for the same input; that change was measured against the stochastic baseline and
found indistinguishable within the project's 0.05 px band (Registration A).

If the manuscript quotes a number, it must state which of these two regimes produced it.

## Rendering difference from upstream, for the manuscript

Our HR rendering adds a **building** class (`#a52a2a`) that upstream GenCP's HR palette does
not contain — 22 colours, no building entry, and no mention of buildings in the upstream HR
demo. The VHR palette has one; the HR one does not.

The pretrained base therefore never saw buildings; the fine-tuned arms did, because training
inputs go through the same `make_chip`. Gate R proves our renderer matches our own research
pipeline byte for byte and was never scoped to compare against upstream, which is the gap
this entered through. On a dense İstanbul tile the building class covers about half the
area, so this is not a marginal difference in built-up scenes.
