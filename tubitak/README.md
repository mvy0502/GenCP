# GenCP — TÜBİTAK UZAY çalışma alanı

OpenStreetMap vektör verisinden **pix2pix** (koşullu GAN) ile sentetik uydu
görüntüsü üretimi. Bu klasör (`tubitak/`) staj kapsamındaki çalışmalar içindir ve
upstream (`telespazio-tim/GenCP`) dosyalarıyla çakışmayacak şekilde ayrı tutulur.

- **Kurulum tarihi:** 18 Ağustos 2026
- **Depo kökü:** `~/Documents/GenCP-Generative-Goruntu-Uretimi-OpenStreetMap`
- **Çalışma dalı:** `tubitak-tr` (upstream varsayılan dalı `master`)
- **Donanım:** MacBook Pro, Apple M4 Max (arm64), 36 GB RAM — CUDA yok, CPU ile çalışır

## Depo yapısı

| Uzaktaki | URL |
|---|---|
| `origin` | https://github.com/mvy0502/GenCP.git (fork) |
| `upstream` | https://github.com/telespazio-tim/GenCP.git |

```
tubitak/
├── README.md
├── environment.yml     # conda ortamı (from-history + pip bölümü)
├── scripts/            # visualize.py vb.
├── configs/
├── notebooks/
├── docs/
├── data/               # .gitignore'da
└── outputs/            # .gitignore'da
```

## Ortam kurulumu

Miniforge (conda-forge, Apple Silicon native) kuruldu; Anaconda **değil**.

```bash
brew install --cask miniforge
conda init zsh
conda create -n gencp python=3.11 -y
conda activate gencp
conda install -c conda-forge rasterio osmnx geopandas matplotlib jupyterlab visdom -y
pip install torch torchvision dominate wandb
```

Ortamı yeniden oluşturmak için:

```bash
conda env create -f tubitak/environment.yml
```

### Doğrulanmış sürümler

| Paket | Sürüm |
|---|---|
| Python | 3.11.15 |
| torch | 2.13.0 |
| torchvision | 0.28.0 |
| rasterio | 1.4.4 |
| osmnx | 2.1.1 |
| geopandas | 1.1.4 |
| numpy | 2.4.6 |

`torch.backends.mps.is_available()` → **True**. `torch.cuda.is_available()` → `False` (beklenen).

### Bilinen kurulum notları

1. **`visdom` pip ile kurulmuyor.** `setup.py` içinde `pkg_resources` kullanıyor; setuptools 82
   bunu kaldırdığı için build isolation sırasında `ModuleNotFoundError` alınıyor.
   Çözüm: `conda install -c conda-forge visdom` (0.2.4 kuruldu).
2. **OpenMP çakışması.** conda-forge paketleri ile pip'ten gelen torch ayrı ayrı
   `libomp.dylib` yüklüyor; `import torch` tek başına `OMP: Error #15` ile çöküyordu.
   Çözüm — tek bir OpenMP runtime'a yönlendirme (yedek `.bak` olarak duruyor):

   ```bash
   ENV=$(conda info --base)/envs/gencp
   cd "$ENV/lib/python3.11/site-packages/torch/lib"
   mv libomp.dylib libomp.dylib.bak
   ln -s "$ENV/lib/libomp.dylib" libomp.dylib
   ```

   `KMP_DUPLICATE_LIB_OK=TRUE` tercih **edilmedi**: iki runtime'a birden izin verdiği için
   sessizce hatalı sayısal sonuç riski taşıyor. Sembolik bağ sonrası torch↔numpy matmul
   farkı `0.0` olarak doğrulandı.
3. **VHR demo kurulmadı.** `requirements_VHR.txt` `tensorflow==2.10.1` pinliyor; macOS arm64
   için wheel yok. Kapsam dışı.

## Ağırlıklar

405 MB, Zenodo'dan indirilir; `.gitignore` ile depo dışında tutulur.

```bash
cd GenCP_HR_demo
curl -L -o HR_weights.zip \
  "https://zenodo.org/records/15044428/files/GenCP_HR_Model_Weights.zip?download=1"
unzip -q HR_weights.zip
mkdir -p checkpoints
cp -r HR_Model_Weights/* checkpoints/
rm -rf HR_weights.zip HR_Model_Weights
```

Sonuç: `checkpoints/genCP_HR_RGB_model/latest_net_G.pth` ve
`checkpoints/genCP_HR_B04_model/latest_net_G.pth` (her biri ~218 MB).

## Pipeline çalıştırma

Tüm komutlar `GenCP_HR_demo/` içinden, `gencp` ortamı aktifken çalıştırılır.

### 1. Görüntü üretimi (CPU)

`--gpu_ids -1` CPU modunu açar; kodda değişiklik gerekmez.

```bash
python ../test.py \
  --dataroot "./data/dataset" \
  --name "genCP_HR_RGB_model" \
  --model "test" \
  --results_dir "./data/fake_images" \
  --checkpoints_dir "./checkpoints" \
  --dataset_mode "single" \
  --norm "batch" \
  --netG "unet_256" \
  --gpu_ids -1
```

Beklenen: `[Network G] Total number of parameters : 54.414 M`.
Bu sayı farklıysa yanlış model yüklenmiştir — durdurun.

Çıktı: `data/fake_images/genCP_HR_RGB_model/test_latest/images/` altında 100 dosya
(50 `_real.png` + 50 `_fake.png`).

> Test klasöründe 630 `.tif` var; `test.py`'nin `--num_test` varsayılanı 50 olduğu için
> yalnızca 50 karo işlenir. Daha fazlası için `--num_test` değerini artırın.

### 2. Coğrafi referanslama

```bash
python gencp_georeferencing.py \
  -t "./data/fake_images/genCP_HR_RGB_model/test_latest/images" \
  -i "./data/dataset/test" \
  -o "./data/GenCP_DB"
```

Çıktı: `data/GenCP_DB/` içinde 50 adet coğrafi referanslı GeoTIFF.

`NotGeoreferencedWarning` **normaldir** — üretilen PNG'lerde coğrafi meta veri yoktur;
betik bu bilgiyi girdi rasterlarından alır.

### 3. Doğrulama

```python
import rasterio
with rasterio.open('data/GenCP_DB/31TEJ_0451_00.tif') as s:
    print('CRS:', s.crs, '| size:', s.width, 'x', s.height, '| resolution:', s.res)
```

Beklenen: `CRS: EPSG:32631 | size: 256 x 256 | resolution: (10.0, 10.0)`
(50 dosyanın tamamı bu değerlerde doğrulandı.)

## Görselleştirme

```bash
python tubitak/scripts/visualize.py --seed 42 -n 4
```

Rastgele 4 karo seçip üst satırda OSM girdisini, alt satırda üretilen görüntüyü
`tubitak/outputs/sample_output.png` dosyasına yazar. (`outputs/` git'e dahil değildir.)

## VS Code

Yorumlayıcı olarak `gencp` conda ortamını seçin:

```
/opt/homebrew/Caskroom/miniforge/base/envs/gencp/bin/python
```
