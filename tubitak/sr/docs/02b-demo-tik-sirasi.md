# Gösteri tıklama sırası — GenCP Süper Çözünürlük eklentisi

Bu belge, QGIS'i daha önce hiç kullanmamış birinin gösteriyi baştan sona yapabilmesi için
yazıldı. Her adım tek bir iştir. Hiçbir adım "zaten bellidir" diye atlanmadı.

**Soğuk başlangıç varsayılır:** QGIS kapalı, eklenti kurulu değil, hiçbir katman açık değil.

**Bu belge iki kez sınandı.** Önce bikübik yolu için yazıldı ve sıfırdan bir QGIS profilinde
uygulandı; 20 adımdan 2'si yanlış çıktı ve düzeltildi. Sonra eğitilmiş model yolu eklendi ve
belge yeniden baştan sona uygulandı (ayrıntı: `04-model-in-plugin.md`). Aşağıdaki metin
düzeltilmiş olanıdır.

**Tamamı ne kadar sürer:** kurulum yaklaşık 3 dakika, iki üretim toplam yaklaşık 1 dakika.

---

## Eklenti ne yapar — üç yöntem, üç ayrı dosya

Eklenti bir rasterı alır, piksel boyunu küçültür ve sonucu yeni bir GeoTIFF olarak yazar.
**Üç yöntem vardır ve her biri farklı bir girdi dosyası ister.** Yanlış eşleştirme yaparsanız
eklenti çalışmayı reddeder ve nedenini söyler; yanlış sonuç üretmez.

| Yöntem | Ne yapar | Ölçek | Hangi dosyayı ister |
|---|---|---|---|
| **Referans model — wsx4** | Danışmanın hedeflediği model (Evoland/CESBIO, ESRGAN, WorldStrat). 10 m → 2,5 m. | **4×** | Adı **DEMO_INPUT_WSX4_** ile başlayan **4 bantlı** dosya (B2,B3,B4,B8) |
| **Eğitilmiş model — GenCP** | Bu projenin eğittiği model. 10 m → 5 m. | **2×** | Adı **DEMO_INPUT_** ile başlayan **3 bantlı** dosya (B02,B03,B04) |
| **Bikübik** | Taban çizgisi. Yeni bilgi üretmez. | 2× | **TCI** dosyası (8 bit, görsel) |

**Model ağırlıkları eklentiyle birlikte gelmez.** Model dosyasını (`.onnx`) her iki model
yolunda da siz seçersiniz. Eklenti ölçeği, bant sayısını, bant sırasını, normalleştirmeyi ve
karo birleştirme yöntemini **modelin kendisinden** okur; hiçbirini kendi içinde saklamaz.

**wsx4 için kritik ayrıntı:** `wsx4_spatrad.onnx` dosyasının **yanında**
`wsx4_spatrad.yaml` dosyası da bulunmalıdır. wsx4 grafiği künye taşımaz; parametreleri bu
yaml dosyasından okunur. Yaml yoksa eklenti modeli reddeder.

**Gösteride söylenmesi gereken cümle:** çıktı ızgarası denetlenmiştir (Gate S, 5/5), ama
**çıktının doğruluğu doğrulanmamıştır**. "2,5 m çözünürlüklü görüntü ürettik" denmemelidir;
"2,5 m ızgaraya, danışmanın hedeflediği modelin takılı olduğu bir hat kurduk" denmelidir.

## Bölüm 0 — Gösteriden önce, bir kez

Gösteri sırasında değil, gösteriden **önce** yapılır.

### 0.1 Eklenti dosyasını (zip) üret

Terminal'i açın (`Command + Boşluk`, `Terminal` yazın, `Enter`). İki satırı sırayla
yapıştırın:

```bash
cd /Users/vedat/Documents/GenCP-Generative-Goruntu-Uretimi-OpenStreetMap
```

```bash
/opt/homebrew/Caskroom/miniforge/base/envs/gencp/bin/python tubitak/sr/build_sr_plugin_zip.py
```

Son satırda `checked:` sözcüğünü görmelisiniz. Görmüyorsanız devam etmeyin.

### 0.2 Dosyaların yerinde olduğunu doğrulayın

```bash
ls -l /Users/vedat/Documents/GenCP-Generative-Goruntu-Uretimi-OpenStreetMap/tubitak/data/sr_dist/gencp_super_resolution.zip /Users/vedat/Documents/GenCP-Generative-Goruntu-Uretimi-OpenStreetMap/tubitak/data/wp5_reference/models/wsx4_spatrad.onnx /Users/vedat/Documents/GenCP-Generative-Goruntu-Uretimi-OpenStreetMap/tubitak/data/wp5_reference/models/wsx4_spatrad.yaml /Users/vedat/Documents/GenCP-Generative-Goruntu-Uretimi-OpenStreetMap/tubitak/data/sr_model_input/DEMO_INPUT_WSX4_36SXJ_1024px_B2-B3-B4-B8_uint16DN_10m.tif /Users/vedat/Documents/GenCP-Generative-Goruntu-Uretimi-OpenStreetMap/tubitak/data/sr_models/gencp_sr_x2_v1.onnx /Users/vedat/Documents/GenCP-Generative-Goruntu-Uretimi-OpenStreetMap/tubitak/data/sr_model_input/DEMO_INPUT_36SXJ_4096px_B02-B03-B04_uint16DN_10m.tif /Users/vedat/Documents/GenCP-Generative-Goruntu-Uretimi-OpenStreetMap/tubitak/data/tiles36SVJ/TCI.tif
```

**Yedi satır** görmelisiniz. `No such file` yazan varsa o yol gösteride çalışmaz.

| Ne | Tam yol (`…` = depo kökü) |
|---|---|
| Eklenti (zip) | `…/tubitak/data/sr_dist/gencp_super_resolution.zip` |
| **wsx4 ağırlıkları** | `…/tubitak/data/wp5_reference/models/wsx4_spatrad.onnx` |
| **wsx4 yapılandırması** (yanında olmalı) | `…/tubitak/data/wp5_reference/models/wsx4_spatrad.yaml` |
| **wsx4 girdisi** (4 bant) | `…/tubitak/data/sr_model_input/DEMO_INPUT_WSX4_36SXJ_1024px_B2-B3-B4-B8_uint16DN_10m.tif` |
| GenCP modeli | `…/tubitak/data/sr_models/gencp_sr_x2_v1.onnx` |
| GenCP girdisi (3 bant) | `…/tubitak/data/sr_model_input/DEMO_INPUT_36SXJ_4096px_B02-B03-B04_uint16DN_10m.tif` |
| Bikübik girdisi | `…/tubitak/data/tiles36SVJ/TCI.tif` |

`…` = `/Users/vedat/Documents/GenCP-Generative-Goruntu-Uretimi-OpenStreetMap`

## Bölüm 1 — QGIS'i açın

1. `Command + Boşluk` ile Spotlight'ı açın.
2. `QGIS` yazın.
3. **QGIS-final-4_2_1** olanı seçip `Enter`'a basın.
4. Açılırken birkaç saniye bekleyin. Ortada tanıtım penceresi çıkarsa sağ üstteki çarpıyla
   kapatın.

Sol tarafta **Katmanlar** paneli boştur.

---

## Bölüm 2 — Eklentiyi kurun

Bir kere yapılır; QGIS'i kapatıp açsanız da kurulu kalır.

1. Üst menüden **Eklentiler** > **Eklentileri Yönet ve Kur…**
2. Açılan pencerenin **sol** tarafından **ZIP'ten Kur**.
3. **ZIP dosyası** kutusunun sağındaki **…** düğmesine tıklayın.
4. `Command + Shift + G` tuşlarına basın; çıkan kutuya yapıştırıp `Enter`:

   ```
   /Users/vedat/Documents/GenCP-Generative-Goruntu-Uretimi-OpenStreetMap/tubitak/data/sr_dist
   ```

5. **gencp_super_resolution.zip** dosyasına **çift tıklayın**.
6. **Eklentiyi Kur** düğmesine tıklayın.
7. "Eklenti kuruldu" kutusunda **Tamam**'a basın.
8. **Bu bir denetleme adımıdır, bir iş değil.** Sol taraftan **Kurulu** listesine geçin,
   **GenCP Super-Resolution** satırını bulun, onay kutusunun **işaretli olduğunu görün**.
   QGIS zip'ten kurulan eklentiyi kendiliğinden etkinleştirir; ölçüldü, kutu zaten işaretli
   gelir. İşaretsizse (beklenmez) işaretleyin.
9. Pencereyi **Kapat** ile kapatın.

**Doğrulama.** Üst menüden **Raster**'a tıklayın; **GenCP SR** başlığını görmelisiniz.

---

## Bölüm 3 — GÖSTERİNİN ANA KISMI: referans model wsx4 (4×)

Danışmanın hedeflediği model. Yaklaşık **27 saniye** sürer ve 10 m girdiyi **2,5 m**'ye
çıkarır.

### 3.1 Girdi katmanını ekleyin

1. **Katman** > **Katman Ekle** > **Raster Katman Ekle…**
2. **Raster veri kümesi(leri)** kutusunun sağındaki **…** düğmesi.
3. `Command + Shift + G`, sonra yapıştırıp `Enter`:

   ```
   /Users/vedat/Documents/GenCP-Generative-Goruntu-Uretimi-OpenStreetMap/tubitak/data/sr_model_input
   ```

4. **DEMO_INPUT_WSX4_36SXJ_1024px_B2-B3-B4-B8_uint16DN_10m.tif** dosyasına çift tıklayın.
   **Adında WSX4 geçen dosya budur; diğerini seçmeyin.**
5. **Ekle**, sonra **Kapat**.

**Görüntü karanlık ya da tuhaf renkli görünebilir — bu normaldir.** Bu görsel bir dosya
değil, 16 bitlik yansıtma verisidir. Görünmüyorsa: katmana sağ tıklayıp **Katmana
Yakınlaştır**.

### 3.2 Eklentiyi açın, yöntemi ve modeli seçin

6. **Raster** > **GenCP SR** > **GenCP Super-Resolution…**
7. **Girdi** bölümünde **Yüklü katmandan** seçilidir; **Raster katman** kutusundan
   **DEMO_INPUT_WSX4_…** katmanını seçin.
8. **Girdi** satırında şunu görmelisiniz:

   ```
   1024 × 1024 piksel · 4 bant, uint16 · EPSG:32636 · 10 m çözünürlük
   ```

   **`4 bant` ve `uint16` yazması önemlidir.** `3 bant` yazıyorsa yanlış dosyayı seçtiniz.

9. **Ayarlar** > **Yöntem** kutusundan **Referans model — wsx4 (4×)** seçin.
10. **Model dosyası** kutusunun sağındaki **…** düğmesine basın, `Command + Shift + G`,
    sonra:

    ```
    /Users/vedat/Documents/GenCP-Generative-Goruntu-Uretimi-OpenStreetMap/tubitak/data/wp5_reference/models
    ```

11. **wsx4_spatrad.onnx** dosyasına çift tıklayın.
12. **Model künyesi** satırında şu belirmelidir:

    ```
    wsx4_spatrad.onnx · normalleştirme modelin içinde · 4× · 4 bant B2,B3,B4,B8 · kırpmalı birleştirme (kenar 130 px)
    ```

    Bu satırın tamamı **modelin kendi yapılandırmasından** okunur. Çıkmıyorsa
    `wsx4_spatrad.yaml` dosyası `.onnx` dosyasının yanında değildir.

13. **Tahmin** satırında şu yazmalıdır:

    ```
    36 karo · çıktı 4096 × 4096 piksel · 2,5 m çözünürlük · yaklaşık 134 MB
    ```

14. **Çıktı dosyası** kendiliğinden dolar; olduğu gibi bırakın. **İş bitince haritaya ekle**
    işaretli olsun.

### 3.3 Çalıştırın

15. **Çalıştır**. Çıktı zaten varsa **Evet**.
16. **Karo 4 / 36** gibi bir yazı hızla artar.
17. Yaklaşık **27 saniye** sonra:

    ```
    Bitti · 36 karo · 27,0 sn · 107 MB Katman eklendi ve girdiyle hizalı.
    ```

18. Yeni katmanı **Katmanlar** panelinde en üste sürükleyin ve bir yere iyice yakınlaşın.

**Ne söylenmeli:** bu, danışmanın adını verdiği modeldir ve Türkiye görüntüsü üzerinde
çalışmaktadır. Referans aracın kendisi bu veriyi **okuyamaz** — yalnızca THEIA/MAJA ya da
L1C SAFE biçimini kabul eder — bu yüzden modelin Türkiye verisiyle kullanılabildiği tek yol
bu eklentidir.

---

## Bölüm 4 — Karşılaştırma: GenCP modeli (2×)

Yaklaşık **23 saniye**.

1. **Katman** > **Katman Ekle** > **Raster Katman Ekle…**, `Command + Shift + G`:

   ```
   /Users/vedat/Documents/GenCP-Generative-Goruntu-Uretimi-OpenStreetMap/tubitak/data/sr_model_input
   ```

2. **DEMO_INPUT_36SXJ_4096px_B02-B03-B04_uint16DN_10m.tif** (WSX4 **geçmeyen**) dosyasına
   çift tıklayın, **Ekle**, **Kapat**.
3. Eklenti penceresinde **Raster katman** kutusundan bu katmanı seçin.
4. **Yöntem** kutusundan **Eğitilmiş model — GenCP (2×)** seçin.
5. **Model dosyası**: **…** > `Command + Shift + G` >

   ```
   /Users/vedat/Documents/GenCP-Generative-Goruntu-Uretimi-OpenStreetMap/tubitak/data/sr_models
   ```

   ve **gencp_sr_x2_v1.onnx** dosyasına çift tıklayın.
6. **Model künyesi** satırı:

   ```
   gencp_sr_x2_v1.onnx · DN/5000 · 2× · 3 bant B02,B03,B04 · yumuşak geçişli birleştirme · adım 16306/20000
   ```

7. **Çalıştır**. Yaklaşık 23 saniye sonra `Bitti · 529 karo · …` yazısı çıkar.

---

## Bölüm 5 — Karşılaştırma: bikübik

Taban çizgisi. Yaklaşık **39 saniye** (bu dosya çok daha büyüktür).

1. **Katman Ekle** > `Command + Shift + G` >

   ```
   /Users/vedat/Documents/GenCP-Generative-Goruntu-Uretimi-OpenStreetMap/tubitak/data/tiles36SVJ
   ```

   **TCI.tif**, **Ekle**, **Kapat**.
2. **Raster katman** kutusundan **TCI**'yi seçin.
3. **Yöntem** kutusundan **Bikübik** seçin.
4. **Çalıştır**.

---

## Bölüm 6 — Yanlış dosyayı vermek (isteğe bağlı, ama etkili)

Eklentinin yanlış girdiyi **reddettiğini** göstermek, çalıştığını göstermek kadar
değerlidir. Üç yöntem ve üç dosya olduğu için karıştırmak kolaydır; eklenti karıştırmaya
izin vermez. Hepsi ölçülmüştür:

| Yöntem | Verilen dosya | Sonuç |
|---|---|---|
| wsx4 | TCI (8 bit, 3 bant) | **Reddedilir** |
| wsx4 | GenCP girdisi (3 bant) | **Reddedilir** |
| GenCP | wsx4 girdisi (4 bant) | **Reddedilir** |
| GenCP | GenCP girdisi (3 bant) | Kabul edilir |
| Bikübik | TCI | Kabul edilir |

Denemek için: **Yöntem** = **Referans model — wsx4 (4×)**, **Raster katman** = GenCP
girdisi. **Çalıştır** soluklaşır ve durum satırında şu çıkar:

> Model **4 bant** bekler (B2,B3,B4,B8); seçilen dosyada **3 bant** var.
>
> Adı **MODEL_INPUT_** ile başlayan yansıtma dosyasını seçin.

Diske **hiçbir dosya yazılmaz**. Yöntemi geri değiştirdiğinizde uyarı kaybolur.

---

## Sorun çıkarsa — gösteri sırasında

| Belirti | Ne yapılmalı |
|---|---|
| **Raster** menüsünde **GenCP SR** yok | Bölüm 2 adım 8: **Kurulu** listesinde onay kutusu |
| **Model künyesi** boş kalıyor, model seçtiğiniz halde | wsx4 için: `wsx4_spatrad.yaml` dosyası `.onnx` yanında değil |
| **Model künyesi**nde **onnxruntime** uyarısı | Model yolları çalışmaz. **Bikübik ile devam edin**; o `onnxruntime` istemez |
| Eklenti açılırken **rasterio** uyarısı | Bu QGIS kurulumunda `rasterio` yok; gösteri bu makinede yapılamaz |
| Durum satırında "4 bant bekler" ya da "16 bit … bekler" | Yöntem ile dosya eşleşmiyor. Yukarıdaki tabloya bakın |
| **Çalıştır** soluk, neden belirsiz | Fareyi düğmenin üzerinde bekletin; eksik olanı yazar |
| İş çok uzun sürüyor | **Durdur**. Diske eksik dosya yazılmaz |
| "Başarısız:" ile başlayan yazı | **Görünüm** > **Paneller** > **Günlük Mesajları** > **GenCP SR** |
| Çıktı katmanı görünmüyor | **Katmanlar** panelinde en üste sürükleyin |
| wsx4 hiç çalışmıyor ve zaman yok | **GenCP modeli**, o da olmazsa **Bikübik** ile gösterin |

**Bir şey çökerse:** eklenti penceresini kapatıp **Raster > GenCP SR**'den yeniden açmak,
QGIS'i kapatmadan durumu sıfırlar.

---

## Gösteriden sonra temizlik

Çıktılar büyüktür. Önce katmanları QGIS'ten kaldırın (**Katmanlar** panelinde sağ tıklayıp
**Katmanı Kaldır**), sonra:

```bash
rm -f /Users/vedat/Documents/GenCP-Generative-Goruntu-Uretimi-OpenStreetMap/tubitak/data/sr_model_input/*_sr_x2.tif /Users/vedat/Documents/GenCP-Generative-Goruntu-Uretimi-OpenStreetMap/tubitak/data/sr_model_input/*_sr_x4.tif /Users/vedat/Documents/GenCP-Generative-Goruntu-Uretimi-OpenStreetMap/tubitak/data/tiles36SVJ/TCI_sr_x2.tif
```
