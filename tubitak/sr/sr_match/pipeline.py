#!/usr/bin/env python
"""WP8 - the four arms and the KLT/RANSAC measurement. Registered in `08-eslestirme.md`.

Runs in the `karios` conda environment, the only one on this machine with a detector. Nothing
was installed for this work package: cv2, scipy and onnxruntime were already there, and
`sr_data.degrade` / `sr_core.upsample` are pure numpy so they import unchanged.

The degradation is IMPORTED from sr_data, never reimplemented (registration section 3).
"""
from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np

SR = Path(__file__).resolve().parents[1]
for p in (str(SR), "/Users/vedat/tools/karios"):
    if p not in sys.path:
        sys.path.insert(0, p)

from sr_core.upsample import BicubicUpsampler          # noqa: E402
from sr_data.degrade import degrade                    # noqa: E402

SEED = 20260831
SCALE = 4
BAND = 2                       # B04 (red) in B02,B03,B04,B08 - registration section 5.1
NORM_DIVISOR_DN = 10000.0

#: tubitak/configs/karios_gencp.json, unchanged. Chosen in Project 1, before WP8 existed.
KLT = dict(minDistance=1, blocksize=5, maxCorners=20000, matching_winsize=15,
           qualityLevel=0.1, laplacian_kernel_size=7)
BACK_THRESHOLD = 0.1           # KARIOS klt.py forward-backward consistency
RANSAC_THRESH_PX = 3.0
RANSAC_ITERS = 5000
RANSAC_CONF = 0.99


# --------------------------------------------------------------------------- the four arms
def degrade_to_40m(chip_dn):
    """(4,256,256) uint16 DN -> (4,64,64) float32 DN, by the REGISTERED degradation."""
    return degrade(np.asarray(chip_dn, np.float32), scale=SCALE).astype(np.float32)


def arm_bicubic(lo_dn):
    up = BicubicUpsampler(scale=SCALE)
    return np.moveaxis(up.upsample(np.moveaxis(lo_dn, 0, -1)), -1, 0).astype(np.float32)


def arm_onnx_ours(sess, lo_dn):
    x = (lo_dn / np.float32(NORM_DIVISOR_DN))[None]
    y = sess.run(None, {sess.get_inputs()[0].name: x.astype(np.float32)})[0][0]
    return (y * np.float32(NORM_DIVISOR_DN)).astype(np.float32)


def arm_onnx_wsx4(sess, lo_dn):
    """wsx4 divides by 10000 on the way in and multiplies on the way out: it takes DN."""
    y = sess.run(None, {sess.get_inputs()[0].name: lo_dn[None].astype(np.float32)})[0][0]
    return y.astype(np.float32)


# ------------------------------------------------------------- radiometry, registration 5.2a
def to_uint8_fixed(arr, lo, hi):
    """One window for every arm, taken from the REFERENCE chip. KARIOS's own _to_uint8 uses
    each image's own min/max, which across arms is a confound: a different dynamic range
    becomes a different stretch, so the detector sees a different image."""
    if hi <= lo:
        return np.zeros(arr.shape, np.uint8)
    return np.clip((np.asarray(arr, np.float64) - lo) / (hi - lo) * 255.0,
                   0, 255).astype(np.uint8)


# ------------------------------------------------------------------ the KLT/RANSAC measurement
def match(arm_plane_u8, ref_plane_u8):
    """Detect on the ARM, track into the REFERENCE (registration 5.2b). Returns a dict."""
    k = KLT["laplacian_kernel_size"]
    lap_arm = cv2.Laplacian(arm_plane_u8, cv2.CV_8U, ksize=k)
    lap_ref = cv2.Laplacian(ref_plane_u8, cv2.CV_8U, ksize=k)

    p0 = cv2.goodFeaturesToTrack(lap_arm, mask=None, maxCorners=KLT["maxCorners"],
                                 qualityLevel=KLT["qualityLevel"],
                                 minDistance=KLT["minDistance"], blockSize=KLT["blocksize"])
    if p0 is None or len(p0) == 0:
        return dict(n_keypoints=0, n_tracked=0, n_inliers=0, inlier_ratio=float("nan"),
                    inlier_ratio_tracked=float("nan"), rmse_model=float("nan"),
                    rmse_truth=float("nan"), dx=float("nan"), dy=float("nan"))

    w = KLT["matching_winsize"]
    lk = dict(winSize=(w, w), maxLevel=1,
              criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 0.03))
    p1, _, _ = cv2.calcOpticalFlowPyrLK(lap_arm, lap_ref, p0, None, **lk)
    p0r, _, _ = cv2.calcOpticalFlowPyrLK(lap_ref, lap_arm, p1, None, **lk)
    good = np.abs(p0 - p0r).reshape(-1, 2).max(-1) < BACK_THRESHOLD

    a = p0.reshape(-1, 2)[good]
    b = p1.reshape(-1, 2)[good]
    n_kp, n_tr = int(len(p0)), int(len(a))
    if n_tr < 3:
        return dict(n_keypoints=n_kp, n_tracked=n_tr, n_inliers=0,
                    inlier_ratio=0.0, inlier_ratio_tracked=float("nan"),
                    rmse_model=float("nan"), rmse_truth=float("nan"),
                    dx=float("nan"), dy=float("nan"))

    cv2.setRNGSeed(SEED)
    M, inl = cv2.estimateAffinePartial2D(a, b, method=cv2.RANSAC,
                                         ransacReprojThreshold=RANSAC_THRESH_PX,
                                         maxIters=RANSAC_ITERS, confidence=RANSAC_CONF,
                                         refineIters=10)
    if M is None or inl is None:
        return dict(n_keypoints=n_kp, n_tracked=n_tr, n_inliers=0, inlier_ratio=0.0,
                    inlier_ratio_tracked=0.0, rmse_model=float("nan"),
                    rmse_truth=float("nan"), dx=float("nan"), dy=float("nan"))

    m = inl.ravel().astype(bool)
    ai, bi = a[m], b[m]
    n_in = int(m.sum())
    proj = (M[:, :2] @ ai.T).T + M[:, 2]
    rmse_model = float(np.sqrt(((proj - bi) ** 2).sum(1).mean())) if n_in else float("nan")
    d = bi - ai
    rmse_truth = float(np.sqrt((d ** 2).sum(1).mean())) if n_in else float("nan")
    return dict(n_keypoints=n_kp, n_tracked=n_tr, n_inliers=n_in,
                inlier_ratio=n_in / n_kp, inlier_ratio_tracked=n_in / n_tr,
                rmse_model=rmse_model, rmse_truth=rmse_truth,
                dx=float(d[:, 0].mean()), dy=float(d[:, 1].mean()))
