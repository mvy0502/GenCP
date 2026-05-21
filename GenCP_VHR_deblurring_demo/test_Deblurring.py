'''
This source code is licensed under the license found in the LICENSE file.
This is the implementation of the "LaKDNet: Revisiting Image Deblurring with an Efficient ConvNet". 
Project GitHub repository: https://github.com/lingyanruan/LaKDNet
Email: lyruanruan@gmail.com
Copyright (c) 2024-present, Lingyan Ruan

Modifications:

- Improved error handling for file operations.
- Added: GeoTIFF output with georeferencing metadata support.
- Adjusted: Argument parser and YAML configuration handling.
- Added: PSNR, MS-SSIM, and LPIPS evaluation pipeline updates.
- Added: Custom 8-bit-compatible PSNR calculation.
- Preserved original pixel values during georeferencing operations.
- Other minor refactoring and testing-related improvements.
'''

import os
import numpy as np
import torch
import torchvision.utils as vutils
from util.util import *
from pathlib import Path
from glob import glob
from natsort import natsorted
from math import log10, sqrt
from scipy import ndimage
from scipy.signal import fftconvolve
from torchmetrics.image.lpip import LearnedPerceptualImagePatchSimilarity
from models.LaKDNet import *
import argparse
import yaml
from osgeo import gdal

# Argument Parser
parser = argparse.ArgumentParser(description='Image Deblurring Testing')
parser.add_argument('--model_path', type=str, required=True, 
                    help='Path to the model weight file (e.g., "./model.pth")')
parser.add_argument('--input_files', type=str, required=True,
                    help='Glob pattern for input files (e.g., "./input/*.tif")')
parser.add_argument('--target_files', type=str, default=None,
                    help='Glob pattern for target/GT files (e.g., "./target/*.tif"). Optional for evaluation.')
parser.add_argument('--output_folder', type=str, required=True,
                    help='Output folder path (e.g., "./output/")')
parser.add_argument('--config_yaml', type=str, default='./options/fine_tuning_config_test.yaml',
                    help='Path to YAML config file for network configuration')
parser.add_argument('--type', type=str, default='Motion', choices=['Motion', 'Defocus'],
                    help='Type of blur: Motion or Defocus')

args = parser.parse_args()

# Load YAML config
with open(args.config_yaml, 'r') as file:
    config = yaml.safe_load(file)[args.type]

net_configs = config.get('net_configs', [])
if len(net_configs) == 0:
    raise ValueError("No net_configs found in YAML.")

net_config_name = net_configs[0]
net_config = config[net_config_name]

print("Loaded net_config:", net_config_name)
print(net_config)


# =========================
# LPIPS
# =========================
compute_lpips = LearnedPerceptualImagePatchSimilarity(
    net_type='vgg',
    reduction='mean'
).cuda()
compute_lpips.eval()


# =========================
# Metrics Functions
# =========================
def compute_psnr_custom(img1, img2):
    """
    PSNR calculation compatible with image_quality_iy.ipynb style.
    img1, img2 can be either [0,1] float or [0,255] float/uint8.
    """

    img1 = img1.astype(np.float64)
    img2 = img2.astype(np.float64)

    # Eğer görüntüler [0,1] aralığındaysa [0,255]'e çevir
    if img1.max() <= 1.0 and img2.max() <= 1.0:
        img1 = img1 * 255.0
        img2 = img2 * 255.0

    # Notebook mantığına yakın olması için uint8 görüntü gibi davran
    img1 = np.clip(img1, 0, 255).round().astype(np.uint8)
    img2 = np.clip(img2, 0, 255).round().astype(np.uint8)

    mse = np.mean((img1 - img2) ** 2)

    if mse == 0:
        return 100.0

    max_pixel = 255.0
    return 20 * log10(max_pixel / sqrt(mse))


def fspecial_gauss(size, sigma):
    x, y = np.mgrid[
        -size // 2 + 1:size // 2 + 1,
        -size // 2 + 1:size // 2 + 1
    ]

    g = np.exp(-((x ** 2 + y ** 2) / (2.0 * sigma ** 2)))
    return g / g.sum()


def ssim_custom(img1, img2, cs_map=False):
    """
    img1, img2: numpy arrays in 0-255 range, HxWxC
    """

    img1 = img1.astype(np.float64)
    img2 = img2.astype(np.float64)

    size = 11
    sigma = 1.5

    window = fspecial_gauss(size, sigma)
    window = np.reshape(window, (size, size, 1))

    K1 = 0.01
    K2 = 0.03
    L = 255

    C1 = (K1 * L) ** 2
    C2 = (K2 * L) ** 2

    mu1 = fftconvolve(img1, window, mode='valid')
    mu2 = fftconvolve(img2, window, mode='valid')

    mu1_sq = mu1 * mu1
    mu2_sq = mu2 * mu2
    mu1_mu2 = mu1 * mu2

    sigma1_sq = fftconvolve(img1 * img1, window, mode='valid') - mu1_sq
    sigma2_sq = fftconvolve(img2 * img2, window, mode='valid') - mu2_sq
    sigma12 = fftconvolve(img1 * img2, window, mode='valid') - mu1_mu2

    ssim_map = (
        ((2 * mu1_mu2 + C1) * (2 * sigma12 + C2)) /
        ((mu1_sq + mu2_sq + C1) * (sigma1_sq + sigma2_sq + C2))
    )

    cs_map_val = (
        (2.0 * sigma12 + C2) /
        (sigma1_sq + sigma2_sq + C2)
    )

    if cs_map:
        return ssim_map, cs_map_val, np.mean(ssim_map)

    return ssim_map, np.mean(ssim_map)


def msssim(img1, img2):
    """
    MS-SSIM calculation.
    img1, img2: numpy arrays in 0-255 range, HxWxC
    """

    level = 5
    weight = np.array([0.0448, 0.2856, 0.3001, 0.2363, 0.1333])
    downsample_filter = np.ones((2, 2, 1)) / 4.0

    im1 = img1.astype(np.float64)
    im2 = img2.astype(np.float64)

    mssim = np.array([])
    mcs = np.array([])

    for _ in range(level):
        ssim_map, cs_map, _ = ssim_custom(im1, im2, cs_map=True)

        mssim = np.append(mssim, ssim_map.mean())
        mcs = np.append(mcs, cs_map.mean())

        filtered_im1 = ndimage.convolve(im1, downsample_filter, mode='reflect')
        filtered_im2 = ndimage.convolve(im2, downsample_filter, mode='reflect')

        im1 = filtered_im1[::2, ::2]
        im2 = filtered_im2[::2, ::2]

    return np.prod(mcs[0:level - 1] ** weight[0:level - 1]) * \
           (mssim[level - 1] ** weight[level - 1])


def add_georef(pred_path, ref_path):
    """
    Adds projection and geotransform from ref_path to pred_path.
    Pixel values are not modified.
    """
    src_ds = gdal.Open(ref_path, gdal.GA_ReadOnly)
    out_ds = gdal.Open(pred_path, gdal.GA_Update)

    if src_ds is None:
        print(f"Warning: reference image could not be opened: {ref_path}")
        return

    if out_ds is None:
        print(f"Warning: output image could not be opened for update: {pred_path}")
        src_ds = None
        return

    out_ds.SetGeoTransform(src_ds.GetGeoTransform())
    out_ds.SetProjection(src_ds.GetProjection())
    out_ds.FlushCache()

    src_ds = None
    out_ds = None

# =========================
# Test Function
# =========================
def test(
    input_c_file_path_list,
    gt_file_path_list,
    net_config=None,
    net_weight=None,
    result_dir=None,
    blur_type='Motion'
):

    PSNR_total = 0.0
    MSSSIM_total = 0.0
    LPIPS_total = 0.0
    eval_count = 0

    Path(result_dir).mkdir(parents=True, exist_ok=True)

    total_files = len(input_c_file_path_list)
    print(f'Processing {total_files} images...')

    network = LaKDNet(**net_config).cuda()
    network.load_state_dict(torch.load(net_weight))
    network.eval()

    for i, filepath in enumerate(input_c_file_path_list):
        filename = os.path.basename(filepath)
        base, ext = os.path.splitext(filename)

        GT = None

        C = read_image(filepath, 255.0)
        C = torch.FloatTensor(C.transpose(0, 3, 1, 2).copy()).cuda()
        C, h, w = crop_image(C, 8, True)

        if gt_file_path_list is not None:
            GT = read_image(gt_file_path_list[i], 255.0)
            GT = crop_image(torch.FloatTensor(GT.transpose(0, 3, 1, 2).copy()).cuda())

        with torch.no_grad():
            output = network(C)

        output = output[:, :, :h, :w]

        if GT is not None:
            GT = GT[:, :, :h, :w]

        print(
            f"DEBUG [{filename}]: "
            f"Output Min: {output.min().item():.5f}, "
            f"Output Max: {output.max().item():.5f}"
        )

        # Save normal image
        out_path = os.path.join(result_dir, base + "_deblurred" + ext)

        try:
            vutils.save_image(
                output,
                out_path,
                nrow=1,
                padding=0,
                normalize=False
            )
        except Exception:
            out_path = os.path.join(result_dir, base + "_deblurred.png")
            vutils.save_image(
                output,
                out_path,
                nrow=1,
                padding=0,
                normalize=False
            )

        # Save GeoTIFF
        try:
            add_georef(out_path, filepath)
            print(f"Georeference added without modifying pixels: {out_path}")
        except Exception as e:
            print(f"Error adding georeference for {filename}: {e}")

        # Evaluation
        if GT is not None:
            output_cpu = output.detach().cpu().numpy()[0].transpose(1, 2, 0).astype(np.float32)
            GT_cpu = GT.detach().cpu().numpy()[0].transpose(1, 2, 0).astype(np.float32)

            if i == 0:
                print("DEBUG shapes:", output_cpu.shape, GT_cpu.shape)
                print("DEBUG output min/max:", output_cpu.min(), output_cpu.max())
                print("DEBUG GT min/max:", GT_cpu.min(), GT_cpu.max())

            output_255 = np.clip(output_cpu * 255.0, 0, 255).astype(np.float32)
            GT_255 = np.clip(GT_cpu * 255.0, 0, 255).astype(np.float32)

            psnr = compute_psnr_custom(output_cpu, GT_cpu)
            ms_ssim = msssim(output_255, GT_255)

            lp = compute_lpips(
                output * 2.0 - 1.0,
                GT * 2.0 - 1.0
            ).item()

            print(
                f'[EVAL][{i + 1:02}/{total_files}] {filename} '
                f'PSNR: {psnr:.5f}, MS-SSIM: {ms_ssim:.5f}, LPIPS: {lp:.5f}'
            )

            with open(os.path.join(result_dir, 'score.txt'), 'w' if eval_count == 0 else 'a') as f:
                f.write(
                    f'[EVAL][{i + 1:02}/{total_files}] {filename} '
                    f'PSNR: {psnr:.5f}, MS-SSIM: {ms_ssim:.5f}, LPIPS: {lp:.5f}\n'
                )

            PSNR_total += psnr
            MSSSIM_total += ms_ssim
            LPIPS_total += lp
            eval_count += 1

        else:
            print(f'[PROCESS][{i + 1:02}/{total_files}] {filename}')

    if eval_count > 0:
        PSNR_mean = PSNR_total / eval_count
        MSSSIM_mean = MSSSIM_total / eval_count
        LPIPS_mean = LPIPS_total / eval_count

        with open(os.path.join(result_dir, 'score.txt'), 'a') as f:
            f.write(
                f'[EVAL MEAN][{eval_count}] '
                f'PSNR: {PSNR_mean:.5f}, '
                f'MS-SSIM: {MSSSIM_mean:.5f}, '
                f'LPIPS: {LPIPS_mean:.5f}\n'
            )

        print('\n' + '=' * 70)
        print(
            f'[EVAL MEAN] '
            f'PSNR: {PSNR_mean:.5f}, '
            f'MS-SSIM: {MSSSIM_mean:.5f}, '
            f'LPIPS: {LPIPS_mean:.5f}'
        )
        print('=' * 70 + '\n')


# =========================
# Main
# =========================
if __name__ == '__main__':

    input_c_file_path_list = natsorted(glob(args.input_files))
    gt_file_path_list = natsorted(glob(args.target_files)) if args.target_files else None


    if len(input_c_file_path_list) == 0:
        raise ValueError(f"No input files found matching pattern: {args.input_files}")

    if gt_file_path_list is not None:
        if len(gt_file_path_list) != len(input_c_file_path_list):
            print(
                f"Warning: Number of input files ({len(input_c_file_path_list)}) "
                f"and target files ({len(gt_file_path_list)}) do not match."
            )
            print("Proceeding without evaluation.")
            gt_file_path_list = None

    if not os.path.exists(args.model_path):
        raise FileNotFoundError(f"Model weight file not found: {args.model_path}")

    results_dir = args.output_folder
    os.makedirs(results_dir, exist_ok=True)

    print('=' * 70)
    print(f'Model: {args.model_path}')
    print(f'Input files: {len(input_c_file_path_list)} files')
    print(f'Output folder: {results_dir}')
    print(f'Blur type: {args.type}')

    if gt_file_path_list:
        print(f'Evaluation: Enabled ({len(gt_file_path_list)} target files)')
    else:
        print('Evaluation: Disabled')

    print('=' * 70 + '\n')

    test(
        input_c_file_path_list=input_c_file_path_list,
        gt_file_path_list=gt_file_path_list,
        net_config=net_config,
        net_weight=args.model_path,
        result_dir=results_dir,
        blur_type=args.type
    )

    print(f'\nResults saved to: {results_dir}')
