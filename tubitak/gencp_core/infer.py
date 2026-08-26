"""ONNX inference over rendered tiles — no PyTorch, no Qt, no QGIS.

Why ONNX. The plugin runs inside QGIS's own Python interpreter. Requiring PyTorch there
would mean asking a GIS analyst to install a 2 GB dependency into an application bundle,
which is not a deployment story anybody would accept. `onnxruntime` is a single wheel with
numpy as its only real dependency, and QGIS's Python already ships numpy.

Determinism. pix2pix applies dropout at test time by design — it is the generator's noise
source in place of a z vector — so the evaluated PyTorch path is stochastic. A delivered
tool must hold "same input -> same output" unconditionally, so the exported graph has the
dropout modules removed. See `export.py` for the second determinism question (BatchNorm
mode), which is a measured decision, not a default.

Preprocessing here reproduces `data/base_dataset.get_transform` under the options test.py
uses (`--load_size 256 --crop_size 256`, no flip) in plain PIL + numpy:

    257x257 RGB  ->  PIL bicubic resize to 256x256  ->  float32 /255  ->  (x-0.5)/0.5

torchvision's Resize delegates to PIL for PIL inputs and ToTensor is exactly /255, so this
is the same computation, not an approximation. `tests/gate_o.py` asserts that against the
torchvision pipeline rather than assuming it.
"""
from __future__ import annotations
from pathlib import Path
import numpy as np

INPUT_PX = 256          # what the network consumes
MEAN, STD = 0.5, 0.5


def preprocess(img):
    """PIL image (any size) -> NCHW float32 in [-1, 1], the network's input tensor."""
    from PIL import Image
    if img.mode != "RGB":
        img = img.convert("RGB")
    if img.size != (INPUT_PX, INPUT_PX):
        img = img.resize((INPUT_PX, INPUT_PX), Image.BICUBIC)
    a = np.asarray(img, dtype=np.float32) / 255.0        # HWC in [0,1]
    a = (a - MEAN) / STD                                  # -> [-1,1]
    return np.ascontiguousarray(a.transpose(2, 0, 1)[None], dtype=np.float32)


def postprocess(y):
    """Network output NCHW in [-1,1] -> HWC uint8, matching util.util.tensor2im."""
    a = np.asarray(y)[0]
    a = (a.transpose(1, 2, 0) + 1.0) / 2.0 * 255.0
    return a.astype(np.uint8)


class OnnxGenerator:
    """A loaded ONNX generator. Thread-safe enough for one QgsTask; not shared across."""

    def __init__(self, model_path, num_threads=None):
        import onnxruntime as ort
        self.path = Path(model_path)
        if not self.path.is_file():
            raise FileNotFoundError(f"ONNX model not found: {self.path}")
        so = ort.SessionOptions()
        if num_threads:
            so.intra_op_num_threads = int(num_threads)
        # A single deterministic CPU provider: the plugin must not silently pick up a
        # GPU provider whose kernels would move the numbers off the gated ones.
        self.sess = ort.InferenceSession(str(self.path), so, providers=["CPUExecutionProvider"])
        self.input_name = self.sess.get_inputs()[0].name
        self.output_name = self.sess.get_outputs()[0].name
        self._dtype = self.sess.get_inputs()[0].type

    @property
    def is_fp16(self):
        return "float16" in self._dtype

    def run_tensor(self, x):
        if self.is_fp16:
            x = x.astype(np.float16)
        y = self.sess.run([self.output_name], {self.input_name: x})[0]
        return np.asarray(y, dtype=np.float32)

    def run_image(self, img):
        """PIL image -> generated HWC uint8 RGB."""
        return postprocess(self.run_tensor(preprocess(img)))

    def run_path(self, png_path):
        from PIL import Image
        with Image.open(png_path) as im:
            return self.run_image(im)


def generate_tiles(model, tile_paths, progress=None, cancelled=None):
    """Run every tile through the model.

    progress(done, total) is called after each tile; cancelled() is polled before each
    tile and, if it returns True, generation stops and returns what it has. Both exist so
    the QgsTask wrapper can report and cancel without gencp_core knowing what a QgsTask is.
    """
    out = {}
    total = len(tile_paths)
    for n, (key, path) in enumerate(tile_paths.items(), 1):
        if cancelled is not None and cancelled():
            break
        out[key] = model.run_path(path)
        if progress is not None:
            progress(n, total)
    return out
