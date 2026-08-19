#!/bin/bash
# Package the Phase C training dataset for upload as a Kaggle Dataset.
# Run AFTER the tile pipelines finish. Output: tubitak/data/kaggle_gencp_tr.zip
set -euo pipefail
cd "$(dirname "$0")/../.."
OUT=tubitak/data/kaggle_stage
rm -rf "$OUT"; mkdir -p "$OUT/pairs/train"
# Ankara non-eval pairs + the three expansion tiles
cp tubitak/data/ankara/train_pairs/*.tif "$OUT/pairs/train/"
for T in 36SVJ 36TUK 36SWJ; do cp "tubitak/data/tiles$T/pairs/"*.tif "$OUT/pairs/train/"; done
# EU corpus pairs for C3 (packaged now so C3 needs no second upload)
mkdir -p "$OUT/eu_pairs"
ls tubitak/data/GenCP_HR_DB/image_pairs/train/*.tif | python3 -c "
import sys, random
fs=[l.strip() for l in sys.stdin]; random.seed(42)
print('\n'.join(random.sample(fs, 1200)))" | xargs -I{} cp {} "$OUT/eu_pairs/"
cp GenCP_HR_demo/checkpoints/genCP_HR_RGB_model/latest_net_G.pth "$OUT/"
n=$(ls "$OUT/pairs/train" | wc -l | tr -d ' ')
echo "TR pairs: $n   EU pairs (C3 reserve): $(ls "$OUT/eu_pairs" | wc -l | tr -d ' ')"
( cd "$OUT" && zip -qr ../kaggle_gencp_tr.zip . )
du -sh tubitak/data/kaggle_gencp_tr.zip
echo "upload tubitak/data/kaggle_gencp_tr.zip as a private Kaggle Dataset named gencp-tr"
