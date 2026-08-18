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
├── scripts/
│   ├── fix_openmp.sh            # OpenMP çakışması düzeltmesi (kurulumdan sonra şart)
│   ├── verify_georeferencing.py # coğrafi referanslama doğrulaması
│   └── visualize.py             # görsel karşılaştırma / doğrulama ızgarası
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

### Ortamı sıfırdan kurma (İKİ adım — ikincisi zorunlu)

```bash
conda env create -f tubitak/environment.yml
conda activate gencp
bash tubitak/scripts/fix_openmp.sh
```

İkinci adım **atlanamaz**. `environment.yml` tek başına çalışan bir ortam üretmez:
kurulum biter, ancak `import torch` OpenMP çakışması nedeniyle çöker
(bkz. [Bilinen sorunlar](#bilinen-sorunlar--ortam-tuzakları)). `fix_openmp.sh`
idempotenttir; zaten düzeltilmiş bir ortamda hiçbir şey yapmadan çıkar.

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

## Bilinen sorunlar / ortam tuzakları

Bu bölüm, kurulum sırasında karşılaşılan ve **tekrar karşılaşılacak** sorunları
belgeler. Her ikisi de referans ortamda görülmemişti; bu makineye özgüdür.

### 1. OpenMP çakışması — `OMP: Error #15`

**Belirti.** Bir şey yapmadan, yalnızca:

```
OMP: Error #15: Initializing libomp.dylib, but found libomp.dylib already initialized.
```

Süreç `abort` ile ölür (exit 134). `import torch` **tek başına** yeterlidir;
`test.py` dahil torch kullanan her şey çalışmaz.

**Kök neden.** İki ayrı OpenMP runtime aynı sürece yükleniyor:

| Kaynak | Getirdiği runtime |
|---|---|
| conda-forge (`numpy`, `rasterio`, `libopenblas`) | `$CONDA_PREFIX/lib/libomp.dylib` (`llvm-openmp`) |
| pip `torch` wheel | `.../site-packages/torch/lib/libomp.dylib` (paket içinde gömülü) |

conda-forge numpy önce conda'nın libomp'unu yüklüyor; ardından torch kendi
kopyasını başlatmaya çalışıyor ve OpenMP guard süreci durduruyor. Tek bir kaynaktan
gelen paketlerle bu olmaz — sorun conda ve pip'i karıştırmaktan doğuyor.

**Çözüm.** Torch'un gömülü kopyası yedeklenip conda'nınkine sembolik bağ yapılır,
böylece süreçte **tek** OpenMP runtime kalır:

```bash
conda activate gencp
bash tubitak/scripts/fix_openmp.sh
```

**Neden `KMP_DUPLICATE_LIB_OK=TRUE` KULLANILMADI.** Bu değişken bir çözüm değil,
guard'ı susturmadır: iki runtime'ın yan yana yaşamasına izin verir. OpenMP'nin kendi
uyarısının dediği gibi bu "crash" veya **sessizce hatalı sonuç** üretebilir. Bir GAN
çıkarım hattında sessizce yanlış sayı, gürültülü çökmeden çok daha kötüdür — çıktı
makul görünür ama yanlış olur. Sembolik bağ ise tek runtime bırakarak sorunu ortadan
kaldırır. Doğrulandı: bağ sonrası torch↔numpy matmul farkı `0.0`.

**⚠️ Kalıcı değildir.** Sembolik bağ `site-packages` içinde yaşar; ne
`environment.yml` ne de git bunu yakalar. Torch'u yeniden kuran/yükselten **her**
işlem (`pip install -U torch`, `pip install --force-reinstall`, ortamı silip yeniden
kurma) gömülü kopyayı geri getirir ve çökme geri döner. Bu durumda betiği tekrar
çalıştırın — idempotenttir, gereksiz yere çalıştırmak zararsızdır.

### 2. `visdom` pip ile kurulamıyor — `pkg_resources`

**Belirti.**

```
ModuleNotFoundError: No module named 'pkg_resources'
ERROR: Failed to build 'visdom' when getting requirements to build wheel
```

**Kök neden.** `visdom`'un `setup.py` dosyası `pkg_resources` import ediyor;
setuptools 82 bu modülü kaldırdı. pip'in build isolation ortamı güncel setuptools
kurduğu için build daha başlamadan patlıyor.

**Dikkat — sessiz yan etki.** pip önce tüm bağımlılıkları çözdüğü için bu hata
komutun **tamamını** iptal eder. Yani

```bash
pip install torch torchvision dominate visdom wandb   # ← visdom yüzünden hiçbiri kurulmaz
```

çalıştırıldığında torch da kurulmaz. Hata mesajı yalnızca visdom'dan söz ettiği için
bu kolayca gözden kaçar.

**Çözüm.** visdom'u conda-forge'dan, kalanını pip'ten kurun:

```bash
conda install -c conda-forge visdom      # 0.2.4
pip install torch torchvision dominate wandb
```

### 3. VHR demo kurulmadı

`GenCP_VHR_demo/requirements_VHR.txt` `tensorflow==2.10.1` ve `gdal==3.6.4` pinliyor.
TensorFlow 2.10.1'in macOS arm64 wheel'i yok. Kapsam dışı bırakıldı.
GDAL ayrıca kurulmadı — `rasterio` kendi GDAL'ını getiriyor.

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

> **Bu kontrol tek başına yeterli DEĞİLDİR.** `gencp_georeferencing.py`, `crs` ve
> `transform` alanlarını referans rasterdan **olduğu gibi** kopyalar. Dolayısıyla
> yanlış PNG yazılmış olsa bile bu üç alan doğru görünür. Gerçek doğrulama için
> [Doğrulama betikleri](#doğrulama-betikleri) bölümüne bakın.

## Doğrulama betikleri

### `verify_georeferencing.py`

CRS/boyut/çözünürlük kontrolünün kapatamadığı boşluğu kapatır. `data/GenCP_DB/`
içindeki her dosya için üç kontrol yapar:

1. **Kimlik** — GeoTIFF piksel dizisi `_fake.png` ile mi yoksa `_real.png` ile mi
   birebir eşleşiyor? Doğru cevap `_fake`. `_real` eşleşmesi ağır hatadır
   (üretilen görüntü yerine girdi görüntüsü yazılmış demektir).
2. **Transform** — çıktının affine dönüşümü, aynı adlı girdi rasterınınkiyle
   eleman eleman aynı mı?
3. **Eşleşme** — dosya adı eşlemesi 1:1 mi; hiçbir çıktı farklı adlı bir girdiden
   türetilmiş mi?

```bash
python tubitak/scripts/verify_georeferencing.py
```

Salt-okunur; hiçbir şey yazmaz. Başarısızlıkta sıfırdan farklı kod döner.
Son çalıştırma: **50/50 PASS** (üç kontrolün üçünde de).

### `visualize.py --verify`

Yukarıdaki kimlik kontrolünün görsel karşılığı. Üç satırlı ızgara üretir:
satır 1 OSM girdisi, satır 2 üretilen `_fake.png`, satır 3 `GenCP_DB/` içinden
geri okunan GeoTIFF. **Satır 2 ile satır 3 piksel piksel aynı olmalıdır**; betik
bunu dizi karşılaştırmasıyla da doğrular ve farklıysa hata verir.

```bash
python tubitak/scripts/visualize.py --verify -n 6 --seed 7
```

Çıktı: `tubitak/outputs/verification_grid.png`. Son çalıştırma: 6/6 birebir aynı.

## Görselleştirme

```bash
python tubitak/scripts/visualize.py --seed 42 -n 4
```

Rastgele 4 karo seçip üst satırda OSM girdisini, alt satırda üretilen görüntüyü
`tubitak/outputs/sample_output.png` dosyasına yazar.

> `tubitak/outputs/` ve `tubitak/data/` `.gitignore` kapsamındadır; üretilen
> figürler depoya girmez, yalnızca betikler izlenir.

## VS Code

Yorumlayıcı olarak `gencp` conda ortamını seçin:

```
/opt/homebrew/Caskroom/miniforge/base/envs/gencp/bin/python
```
