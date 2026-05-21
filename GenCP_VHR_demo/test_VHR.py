import numpy as np
import glob
import tifffile
import os
import argparse
import re

# Keras 3 / tf.keras compatible load_model (tf_keras installed in Colab)
try:
    from tf_keras.models import load_model      # Recommended path (Colab: tf_keras==2.19.0)
except Exception:
    try:
        from keras.models import load_model     # Keras 3
    except Exception:
        from tensorflow.keras.models import load_model  # Old fallback (if needed)

from osgeo import gdal



# Parse command-line arguments
parser = argparse.ArgumentParser(description="Process VHR images and generate predictions.")
parser.add_argument("--model_path", type=str, required=True, help="Path to the trained model.")
parser.add_argument("--img_files", type=str, required=True, help="Glob pattern for input images.")
parser.add_argument("--masks_files", type=str, required=True, help="Glob pattern for mask images.")
parser.add_argument("--output_folder", type=str, required=True, help="Folder to save output predictions.")
args = parser.parse_args()


def tile_key(p):
    """
    Builds a unique key from filename:
      <prefix>_rs_patch_<id>.tif  or  <prefix>_rs_mask_<id>.tif
    Key = (prefix, id)
    Example prefix includes R3C2 / R4C2 etc., so patch_20 won't collide across tiles.
    """
    b = os.path.basename(p)
    m = re.match(r"^(.*)_(?:patch|mask)_(\d+)\.tif$", b, flags=re.IGNORECASE)
    if not m:
        return None
    prefix = m.group(1)
    idx = int(m.group(2))
    return (prefix, idx)

imgs = sorted(glob.glob(args.img_files))
msks = sorted(glob.glob(args.masks_files))

img_map = {tile_key(p): p for p in imgs if tile_key(p) is not None}
msk_map = {tile_key(p): p for p in msks if tile_key(p) is not None}

common_keys = sorted(set(img_map.keys()) & set(msk_map.keys()))

# Aligned lists according to tile IDs
img_files = [img_map[k] for k in common_keys]
masks_files = [msk_map[k] for k in common_keys]

# Initialize arrays for images and masks
test_images = np.zeros((len(img_files), 256, 256, 3))
test_masks = np.zeros((len(masks_files), 256, 256, 3))

# Load images
for indx, img_path in enumerate(img_files):
    img = tifffile.imread(img_path)
    img[img == -32768] = 0  # Replace invalid values with 0
    test_images[indx] = img[:, :, :3]

# Load masks
for indx, mask_path in enumerate(masks_files):
    mask = tifffile.imread(mask_path)
    mask[mask == -32768] = 0  # Replace invalid values with 0
    test_masks[indx] = mask[:, :, :3]

X_val = test_images
y_val = test_masks

# Load the trained model
model = load_model(args.model_path)

# Print model summary
print("\n=== Model Summary ===")
model.summary()

# Print training parameters if available
if model.optimizer is not None:
    if "epochs" in model.optimizer.get_config():
        print(f"Number of training epochs: {model.optimizer.get_config()['epochs']}")

# Normalize images to [0, 1] range and # Make predictions
y_val_norm = (y_val - 127.5) / 127.5

preds = model.predict(y_val_norm)
preds = (preds + 1) / 2.0
preds_8bit = (preds * 255).astype(np.uint8)

y_val_norm = (y_val_norm + 1) / 2.0

X_val_norm = (X_val - 127.5) / 127.5
X_val_norm = (X_val_norm + 1) / 2.0

# Define output folder
os.makedirs(args.output_folder, exist_ok=True)

# Save predictions as GeoTIFF
for idx, img_path in enumerate(img_files):
    src_ds = gdal.Open(img_path)
    geotransform = src_ds.GetGeoTransform()
    projection = src_ds.GetProjection()
    src_ds = None  # Close source dataset
    
    pred = preds_8bit[idx]
    base_name = os.path.basename(img_path).split('.')[0]
    output_file = os.path.join(args.output_folder, f"{base_name}_preds.tif")
    
    driver = gdal.GetDriverByName("GTiff")
    rows, cols = pred.shape[:2]
    out_ds = driver.Create(output_file, cols, rows, 3, gdal.GDT_Byte)
    out_ds.SetGeoTransform(geotransform)
    out_ds.SetProjection(projection)
    
    for band in range(3):  # Save each channel
        out_band = out_ds.GetRasterBand(band + 1)
        out_band.WriteArray(pred[:, :, band])
        out_band.FlushCache()
    
    out_ds = None  # Close output dataset

print("Prediction files have been saved as RGB GeoTIFFs!")
