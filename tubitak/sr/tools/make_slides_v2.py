#!/usr/bin/env python3
"""Build the six EOX comparison figures used in the presentation slides.

WHAT THIS PRODUCES
    One PNG per site. Each is three panels side by side, 1024 x 1024 each, over a
    2.56 x 2.56 km footprint: the 10 m input replicated 4x by nearest neighbour, the
    same input upsampled 4x by bicubic, and the same input through the GenCP scale-4
    three-band model. Header, footer, attribution and the caveat line are drawn on.

HOW TO RUN IT
    Working directory must be the repository root - the script does
    sys.path.insert(0, "tubitak/sr") to import sr_core.upsample, and the model path
    below is repository-relative.

        python tubitak/sr/tools/make_slides_v2.py <output-directory>

    The output directory must already exist. With no argument the script prints usage
    and exits 1 rather than raising IndexError. Extra arguments and unrecognised
    flags are refused the same way, rather than silently ignored.

WHAT IT NEEDS, AND WHERE EACH INPUT COMES FROM

    1. EOX tiles - fetched over the network at run time, nothing is stored in the
       repository. The source is the EOxCloudless s2cloudless-2024 WMTS layer, zoom 14,
       GoogleMapsCompatible, JPEG:

           https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless-2024_3857/default/
           GoogleMapsCompatible/{z}/{row}/{col}.jpg

       For each site the script computes the local UTM zone from the site longitude,
       lays out a 256 x 256 grid at 10 m centred on the site, converts that footprint to
       EPSG:3857 to decide which z14 tiles cover it (with a one-tile margin), fetches
       each tile with urllib, mosaics them, and reprojects the mosaic into UTM at 10 m
       with bilinear resampling. Between 16 and 25 tiles per site. The mosaic is a fixed
       annual product, so a later run fetches the same pixels - this was confirmed by
       regenerating all six figures and finding every panel bit-identical by sha256 to
       the ones produced on 2026-09-01.

       LICENCE: EOxCloudless is CC BY-NC-SA 4.0, non-commercial only. The attribution
       string drawn on every figure is required and must not be removed.

    2. The model - gencp_sr_tci_x4_b3_v2.onnx, expected at

           tubitak/data/plugin_models/gencp_sr_tci_x4_b3_v2.onnx

       THIS PATH IS NOT IN THE REPOSITORY. Everything under tubitak/data/ is gitignored,
       so on a fresh clone this file is absent and the script exits with a message saying
       where to get it. Download it from the release and place it at that path, or edit
       MODEL to point wherever you keep it:

           https://github.com/mvy0502/gencp-validation/releases/download/
           sr-plugin-v0.1.0/gencp_sr_tci_x4_b3_v2.onnx
           sha256 01496736913ac257f8f57ccb26e1c4220e903b6c309712ebcc48e0b834485920

       Band order is B02,B03,B04 and the normalisation divisor is 255. The script feeds
       rgb[::-1] / 255.0 for exactly that reason: the EOX tiles arrive as R,G,B and the
       model was trained on B02,B03,B04, which is the reverse.

    3. Fonts - Helvetica or Arial from the macOS system font directories, with a
       fallback to PIL's built-in bitmap font. ON A NON-MAC MACHINE the fallback will be
       used and the header text will look different and may overrun; point font() at a
       TrueType file that exists on that machine.

    4. Python - numpy, onnxruntime, rasterio, Pillow, and sr_core.upsample from this
       repository. Written and run under the project's gencp conda environment.

NO STRETCH IS APPLIED - THIS IS THE POINT OF THE FIGURE
    All three panels show the product's own 8-bit DN one to one, R 0-255 G 0-255
    B 0-255, with no percentile stretch, no min-max normalisation, and no per-panel
    rescaling of any kind. Every panel is therefore on one identical display scale, so
    the visible difference between panels is the upsampler and nothing else. The header
    line drawn on each figure says so, and the script prints each panel's per-band DN
    range at the end of every site so a reader can confirm it: independently stretched
    panels would be pinned to 0-255 in all three bands, and the input and bicubic panels
    are not.

    This differs deliberately from the wsx4 figure, which DOES stretch - a per-band
    2nd-98th percentile taken from its input panel only and applied identically to all
    four of its panels. Both are one shared scale; they are simply different scales,
    and each figure states which it used.

PROVENANCE
    Until 2026-09-01 this script existed only as a heredoc in a session transcript. The
    version here reproduces those figures byte for byte in the panel area; the only
    difference is the added display-scale header line and TOP growing 92 -> 120 to fit it.
"""
import io, math, os, sys, urllib.request, warnings
import numpy as np, onnxruntime as ort
from PIL import Image, ImageDraw, ImageFont
from rasterio.transform import from_origin
from rasterio.warp import reproject, Resampling
sys.path.insert(0, "tubitak/sr"); warnings.filterwarnings("ignore")
from sr_core.upsample import BicubicUpsampler

E = 20037508.342789244
Z = 14
RES = 2 * E / (256 * 2**Z)
BASE = ("https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless-2024_3857/default/"
        "GoogleMapsCompatible/%d/%d/%d.jpg")
MODEL = "tubitak/data/plugin_models/gencp_sr_tci_x4_b3_v2.onnx"
if len(sys.argv) != 2 or sys.argv[1].startswith("-"):
    sys.exit("usage: python tubitak/sr/tools/make_slides_v2.py <output-directory>\n"
             "       run from the repository root; the directory must already exist")
OUT = sys.argv[1]
if not os.path.isdir(OUT):
    sys.exit(f"output directory does not exist: {OUT}")
if not os.path.isfile(MODEL):
    sys.exit(f"model not found: {MODEL}\n"
             "  everything under tubitak/data/ is gitignored, so this file is absent on a\n"
             "  fresh clone. Download gencp_sr_tci_x4_b3_v2.onnx from the release and put it\n"
             "  at that path, or edit MODEL:\n"
             "  https://github.com/mvy0502/gencp-validation/releases/tag/sr-plugin-v0.1.0")
N = 256
ATTR = ("EOxCloudless  https://cloudless.eox.at  by EOX IT Services GmbH "
        "(Contains modified Copernicus Sentinel data 2024)")
SITES = [
    ("01_Kadikoy_Istanbul",   "Kadikoy, Istanbul",        29.030, 40.990),
    ("02_Fatih_Istanbul",     "Fatih, Istanbul",          28.972, 41.008),
    ("03_ODTU_Ankara",        "ODTU campus, Ankara",      32.780, 39.891),
    ("04_Giza_Egypt",         "Pyramids of Giza, Egypt",  31.132, 29.977),
    ("05_AngkorWat_Cambodia", "Angkor Wat, Cambodia",    103.867, 13.412),
    ("06_Konya_fields",       "Centre-pivot fields, Konya", 33.050, 37.850),
]

def utm_epsg(lon, lat):
    z = int((lon + 180) / 6) + 1
    return 32600 + z if lat >= 0 else 32700 + z

def fetch(lon, lat):
    epsg = utm_epsg(lon, lat)
    import rasterio.warp as rw
    ex, ey = rw.transform("EPSG:4326", f"EPSG:{epsg}", [lon], [lat])
    cx, cy = ex[0], ey[0]
    half = N * 10 / 2
    dst_tr = from_origin(cx - half, cy + half, 10.0, 10.0)
    corners = rw.transform_bounds(f"EPSG:{epsg}", "EPSG:3857",
                                  cx - half, cy - half, cx + half, cy + half)
    x0, y0, x1, y1 = corners
    c0, c1 = int((x0 + E) / (RES*256)) - 1, int((x1 + E) / (RES*256)) + 1
    r0, r1 = int((E - y1) / (RES*256)) - 1, int((E - y0) / (RES*256)) + 1
    nx, ny = c1 - c0 + 1, r1 - r0 + 1
    mos = np.zeros((3, ny*256, nx*256), np.uint8)
    for r in range(r0, r1+1):
        for c in range(c0, c1+1):
            with urllib.request.urlopen(BASE % (Z, r, c), timeout=60) as f:
                img = np.array(Image.open(io.BytesIO(f.read())).convert("RGB"))
            mos[:, (r-r0)*256:(r-r0+1)*256, (c-c0)*256:(c-c0+1)*256] = np.moveaxis(img, -1, 0)
    src_tr = from_origin(-E + c0*256*RES, E - r0*256*RES, RES, RES)
    out = np.zeros((3, N, N), np.uint8)
    for i in range(3):
        reproject(mos[i], out[i], src_transform=src_tr, src_crs="EPSG:3857",
                  dst_transform=dst_tr, dst_crs=f"EPSG:{epsg}", resampling=Resampling.bilinear)
    return out, epsg, (nx*ny)

def font(sz):
    for p in ("/System/Library/Fonts/Helvetica.ttc",
              "/System/Library/Fonts/Supplemental/Arial.ttf"):
        if os.path.isfile(p):
            try: return ImageFont.truetype(p, sz)
            except Exception: pass
    return ImageFont.load_default()

sess = ort.InferenceSession(MODEL, providers=["CPUExecutionProvider"])
up = BicubicUpsampler(scale=4)
F_T, F_L, F_S, F_M = font(34), font(26), font(18), font(22)

for key, label, lon, lat in SITES:
    rgb, epsg, ntiles = fetch(lon, lat)
    bic = np.moveaxis(up.upsample(np.moveaxis(rgb, 0, -1)), -1, 0)
    x = (rgb[::-1].astype(np.float32) / np.float32(255.0))[None]
    y = sess.run(None, {sess.get_inputs()[0].name: x})[0][0] * 255.0
    mdl = np.clip(y[::-1], 0, 255).astype(np.uint8)
    nn = np.kron(rgb, np.ones((1, 4, 4), np.uint8)).astype(np.uint8)
    panels = [np.moveaxis(a, 0, -1) for a in (nn, bic.astype(np.uint8), mdl)]
    W, H, GAP, TOP, BOT = 1024, 1024, 14, 120, 74
    canvas = Image.new("RGB", (W*3 + GAP*2, H + TOP + BOT), (255, 255, 255))
    for i, p in enumerate(panels):
        canvas.paste(Image.fromarray(p), (i*(W+GAP), TOP))
    d = ImageDraw.Draw(canvas)
    d.text((4, 8), f"{label}   -   2.56 x 2.56 km   -   EPSG:{epsg}", font=F_T, fill=(0,0,0))
    d.text((4, 52), "EOxCloudless s2cloudless-2024 (10 m) super-resolved 4x to 2.5 m",
           font=F_L, fill=(70,70,70))
    d.text((4, 86), "Identical display scale on all three panels, taken from the INPUT: "
                    "no stretch is applied - the product's own 8-bit DN is shown "
                    "one-to-one   R 0-255  G 0-255  B 0-255   (DN)", font=F_M, fill=(70,70,70))
    for i, t in enumerate(("input 10 m (nearest x4)", "bicubic x4", "GenCP SR model x4")):
        d.text((i*(W+GAP) + 8, TOP + H + 6), t, font=F_L, fill=(0,0,0))
    d.text((4, TOP + H + 40), ATTR, font=F_S, fill=(110,110,110))
    d.text((W + GAP + 8, TOP + H + 40),
           "Illustration, not measurement: no ground truth exists for a cloudless mosaic.",
           font=F_S, fill=(150,60,60))
    p = os.path.join(OUT, f"{key}.png")
    canvas.save(p, optimize=True)
    print(f"  {key:24s} {ntiles:2d} tiles  EPSG:{epsg}  {os.path.getsize(p)/1048576:.1f} MB")
    # The claim printed on the figure, made checkable: no panel is rescaled, so the
    # panels do NOT all span 0-255. A panel stretched from its own percentiles would.
    for nm, a in zip(("input ", "bicubic", "model  "), panels):
        rng = "  ".join(f"{c} {int(a[..., i].min()):3d}-{int(a[..., i].max()):3d}"
                        for i, c in enumerate("RGB"))
        print(f"      {nm} DN  {rng}")
