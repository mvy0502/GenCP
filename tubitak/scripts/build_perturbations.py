#!/usr/bin/env python
"""Build renderer-perturbation variants of the OSM input rasters.

Perturbations are applied to the **256 px image the network actually sees**, not to
the 257 px source. That matters: `test.py` resizes 257->256 with BICUBIC, which
re-introduces anti-aliasing and would silently undo perturbation A. Resizing to 256
first (verified to be a no-op when `test.py` resizes again) keeps every perturbation
intact through to the network.

Axes (see docs/renderer-tolerance.md §1 for what each simulates and its caveats):
  A     anti-aliasing removed      quantise every pixel to its nearest palette colour
  B     anti-aliasing increased    Gaussian blur, sigma 1.0
  Cp/Cm road width +1 / -1 px      dilate / erode road-classified pixels
  Dg*   global colour shift        +delta on all channels, all pixels
  Ds*   single-class colour shift  +delta on light_green pixels only
  E     draw order inverted        remove roads, letting landuse win (proxy)
  F     missing class              black/snow replaced by local dominant colour
  G     building rendering         building blobs dilated 1 px (proxy)
"""
from __future__ import annotations
import argparse, glob, sys, warnings
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "GenCP_HR_demo"))
from genCP_HR_osm_colors import color_dict  # noqa: E402

def hex2rgb(h):
    if h == "white": return (255, 255, 255)
    if h == "black": return (0, 0, 0)
    h = h.lstrip("#"); return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

AREA = ["light_green","forest_green","water","light_purple","gray","no_vegetation",
        "sand","rock","light_gray"]
ROAD = ["residential_road","tertiary_road","unclassified_road","track","foot_path",
        "light_orange_road","medium_orange_road"]
SPECIAL = ["black","snow"]
NAMES = AREA + ROAD + SPECIAL + ["building"]
PAL = np.array([hex2rgb(color_dict[n]) for n in AREA+ROAD+SPECIAL] + [[165,42,42]], float)
IDX = {n: i for i, n in enumerate(NAMES)}
ROAD_I = [IDX[n] for n in ROAD]
SPEC_I = [IDX[n] for n in SPECIAL]

def classify(img):
    d = np.linalg.norm(img[:, :, None, :] - PAL[None, None, :, :], axis=3)
    return d.argmin(axis=2)

def local_dominant(img, mask):
    """Replace masked pixels with the most common non-masked colour in the image."""
    out = img.copy()
    if not mask.any(): return out
    keep = img[~mask].astype(np.int32)
    k = (keep[:,0]<<16)|(keep[:,1]<<8)|keep[:,2]
    u, c = np.unique(k, return_counts=True)
    dom = int(u[c.argmax()])
    out[mask] = [(dom>>16)&255, (dom>>8)&255, dom&255]
    return out

def main() -> int:
    from PIL import Image
    from torchvision import transforms
    from scipy import ndimage
    import rasterio
    from rasterio.errors import NotGeoreferencedWarning
    warnings.filterwarnings("ignore", category=NotGeoreferencedWarning)

    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--osm", default=str(ROOT/"tubitak/data/karios/reference/osm"))
    ap.add_argument("--out", default=str(ROOT/"tubitak/data/sensitivity/inputs"))
    ap.add_argument("--chips", type=int, default=30)
    a = ap.parse_args()

    r256 = transforms.Resize([256,256], transforms.InterpolationMode.BICUBIC)
    files = sorted(glob.glob(f"{a.osm}/*.tif"))

    # stratify by OSM information content so P3 is testable
    from scipy.ndimage import sobel
    scored = []
    for f in files[::max(1, len(files)//220)]:
        with rasterio.open(f) as s: img = np.transpose(s.read(),(1,2,0)).astype(float)
        g = img.mean(axis=2)
        scored.append((float((np.hypot(sobel(g,0),sobel(g,1))>20).mean()), f))
    scored.sort()
    step = max(1, len(scored)//a.chips)
    sel = [f for _, f in scored[::step]][:a.chips]
    print(f"selected {len(sel)} chips, OSM edge density "
          f"{scored[0][0]:.3f} .. {scored[-1][0]:.3f} (stratified)")

    variants = ["base","A","B","Cp","Cm","E","F","G"] + \
               [f"Dg{d}" for d in (2,5,10,20,40)] + [f"Ds{d}" for d in (2,5,10,20,40)]
    for v in variants: (Path(a.out)/v).mkdir(parents=True, exist_ok=True)

    for f in sel:
        stem = Path(f).stem
        with rasterio.open(f) as s: src = np.transpose(s.read(),(1,2,0)).astype(np.uint8)
        base = np.array(r256(Image.fromarray(src)))          # what the network sees
        cls = classify(base.astype(float))
        roads = np.isin(cls, ROAD_I)
        spec  = np.isin(cls, SPEC_I)
        bld   = (cls == IDX["building"])

        out = {"base": base}
        out["A"] = PAL[cls].astype(np.uint8)                          # hard edges
        out["B"] = np.stack([ndimage.gaussian_filter(base[:,:,k].astype(float),1.0)
                             for k in range(3)],axis=-1).clip(0,255).astype(np.uint8)
        for tag, m in (("Cp", ndimage.binary_dilation(roads)),
                       ("Cm", ndimage.binary_erosion(roads))):
            im = base.copy()
            if tag == "Cp":
                new = m & ~roads
                im[new] = PAL[cls[roads]].mean(axis=0) if roads.any() else im[new]
            else:
                gone = roads & ~m
                im = local_dominant(im, gone) if gone.any() else im
            out[tag] = im.astype(np.uint8)
        out["E"] = local_dominant(base, roads).astype(np.uint8)       # roads not drawn
        out["F"] = local_dominant(base, spec).astype(np.uint8)        # class removed
        gd = ndimage.binary_dilation(bld) & ~bld
        imG = base.copy(); imG[gd] = PAL[IDX["building"]]
        out["G"] = imG.astype(np.uint8)
        for d in (2,5,10,20,40):
            out[f"Dg{d}"] = np.clip(base.astype(int)+d,0,255).astype(np.uint8)
            im = base.astype(int)
            im[cls == IDX["light_green"]] += d
            out[f"Ds{d}"] = np.clip(im,0,255).astype(np.uint8)

        for v, im in out.items():
            Image.fromarray(im).save(Path(a.out)/v/f"{stem}.png")

    print(f"wrote {len(sel)} chips x {len(variants)} variants = {len(sel)*len(variants)} inputs")
    print("variants:", ", ".join(variants))
    return 0

if __name__ == "__main__":
    sys.exit(main())
