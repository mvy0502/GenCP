# Gösteri tıklama sırası — GenCP Süper Çözünürlük eklentisi

Bu belge, QGIS'i daha önce hiç kullanmamış birinin gösteriyi baştan sona yapabilmesi için
yazıldı. Her adım tek bir iştir. Hiçbir adım "zaten bellidir" diye atlanmadı.

**Soğuk başlangıç varsayılır:** QGIS kapalı, eklenti kurulu değil, hiçbir katman açık değil.

> ### Önemli: QGIS menüleri İNGİLİZCE, eklenti penceresi TÜRKÇE
>
> Bu makinedeki QGIS arayüzü İngilizcedir (`locale/userLocale = en_GB`, ölçüldü). Eklentinin
> kendi penceresi ise Türkçedir. Bu belgede:
>
> * **QGIS'in kendi menüleri İngilizce yazılmıştır**, parantez içinde Türkçe karşılığıyla:
>   **Layer** (Katman) > **Add Layer** (Katman Ekle).
> * **Eklenti penceresindeki yazılar Türkçedir** ve ekranda göreceğiniz gibi yazılmıştır:
>   Girdi, Ayarlar, Yöntem, Çalıştır.
>
> Ekranda Türkçe menü arıyorsanız bulamazsınız; İngilizce olanı arayın.

**Bu belge üç kez sınandı**, en son üç yöntemin tamamı ve karşılaştırma adımı için, sıfırdan
bir QGIS profilinde. Bulunan hatalar düzeltildi (ayrıntı: `06-wsx4-eklentide.md`).

**Tamamı ne kadar sürer:** kurulum yaklaşık 3 dakika, üç üretim toplam yaklaşık 1,5 dakika.

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

---

## Bölüm 0 — Gösteriden önce, bir kez

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

---

## Bölüm 1 — QGIS'i açın

1. `Command + Boşluk` ile Spotlight'ı açın.
2. `QGIS` yazın.
3. **QGIS-final-4_2_1** olanı seçip `Enter`'a basın.
4. Açılırken birkaç saniye bekleyin. Ortada tanıtım penceresi çıkarsa sağ üstteki çarpıyla
   kapatın.

Sol tarafta **Layers** (Katmanlar) paneli boştur.

---

## Bölüm 2 — Eklentiyi kurun

Bir kere yapılır; QGIS'i kapatıp açsanız da kurulu kalır.

1. Üst menüden **Plugins** (Eklentiler) > **Manage and Install Plugins…**
2. Açılan pencerenin **sol** tarafından **Install from ZIP** (ZIP'ten Kur).
3. **ZIP file** kutusunun sağındaki **…** düğmesine tıklayın.
4. `Command + Shift + G` tuşlarına basın; çıkan kutuya yapıştırıp `Enter`:

   ```
   /Users/vedat/Documents/GenCP-Generative-Goruntu-Uretimi-OpenStreetMap/tubitak/data/sr_dist
   ```

5. **gencp_super_resolution.zip** dosyasına **çift tıklayın**.
6. **Install Plugin** (Eklentiyi Kur) düğmesine tıklayın.
7. Çıkan bilgi kutusunda **OK** (Tamam).
8. **Bu bir denetleme adımıdır, bir iş değil.** Sol taraftan **Installed** (Kurulu) listesine
   geçin, **GenCP Super-Resolution** satırını bulun, onay kutusunun **işaretli olduğunu
   görün**. QGIS zip'ten kurulan eklentiyi kendiliğinden etkinleştirir; ölçüldü, kutu zaten
   işaretli gelir. İşaretsizse (beklenmez) işaretleyin.
9. Pencereyi **Close** (Kapat) ile kapatın.

**Doğrulama.** Üst menüden **Raster**'a tıklayın; **GenCP SR** başlığını görmelisiniz.

---

## Bölüm 3 — GÖSTERİNİN ANA KISMI: referans model wsx4 (4×)

Danışmanın hedeflediği model. Yaklaşık **26 saniye** sürer ve 10 m girdiyi **2,5 m**'ye
çıkarır.

### 3.1 Girdiyi ÖNCE haritaya katman olarak yükleyin

**Bu adımı atlamayın ve dosyayı eklenti penceresinden seçmeyin.** Nedeni 3.5'te
kullanılacak: **girdiyi katman olarak yüklerseniz kaynak Layers panelinde kalır, QGIS sonucu
onun üstüne yerleştirir, ve böylece üstteki katmanın onay kutusunu açıp kapatmak
öncesi/sonrası karşılaştırmasıdır.** Dosyayı doğrudan eklentiden seçerseniz kaynak panelde
olmaz ve karşılaştıracak bir şey kalmaz.

1. Üst menüden **Layer** (Katman) > **Add Layer** (Katman Ekle) > **Add Raster Layer…**
2. **Raster dataset(s)** kutusunun sağındaki **…** düğmesi.
3. `Command + Shift + G`, sonra yapıştırıp `Enter`:

   ```
   /Users/vedat/Documents/GenCP-Generative-Goruntu-Uretimi-OpenStreetMap/tubitak/data/sr_model_input
   ```

4. **DEMO_INPUT_WSX4_36SXJ_1024px_B2-B3-B4-B8_uint16DN_10m.tif** dosyasına çift tıklayın.
   **Adında WSX4 geçen dosya budur; diğerini seçmeyin.**
5. **Add** (Ekle), sonra **Close** (Kapat).

**Ne görmelisiniz:** haritada bir görüntü ve **Layers panelinde tek bir satır**:
`DEMO_INPUT_WSX4_36SXJ_1024px_...`. Panelde bu satır yoksa dosya katman olarak
yüklenmemiştir; 2. adıma dönün.

**Görüntü karanlık ya da tuhaf renkli görünebilir — bu normaldir.** Bu görsel bir dosya
değil, 16 bitlik yansıtma verisidir. Görünmüyorsa: katmana sağ tıklayıp **Zoom to Layer**
(Katmana Yakınlaştır).

### 3.2 Eklentiyi açın, yöntemi ve modeli seçin

6. **Raster** > **GenCP SR** > **GenCP Super-Resolution…**
7. **Girdi** bölümünde **Yüklü katmandan** seçilidir — **öyle bırakın**. **Raster katman**
   kutusundan **DEMO_INPUT_WSX4_…** katmanını seçin.
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
17. Yaklaşık **26 saniye** sonra:

    ```
    Bitti · 36 karo · 25,7 sn · 107 MB Katman eklendi ve girdiyle hizalı.
    ```

18. **Layers panelinde artık İKİ satır vardır ve yeni olan ÜSTTEDİR:**

    ```
    DEMO_INPUT_WSX4_..._sr_x4      <- sonuç (2,5 m), ÜSTTE
    DEMO_INPUT_WSX4_...            <- kaynak (10 m), ALTTA
    ```

    Sıra böyle değilse yeni katmanı fareyle tutup en üste sürükleyin.

### 3.4 Renk ölçeğini eşitleyin — karşılaştırmayı dürüst yapan adım

**Bu adım neden var.** QGIS her katmana **kendi** en küçük/en büyük değerlerine göre **ayrı
bir renk gerdirmesi** uygular (varsayılan: **Cumulative count cut**, yani %2–%98). İki katman
aynı sahneyi gösterse bile bu yüzden farklı görünür.

Bu gösterinin kendi verisinde ölçüldü — kaynak ile çıktının QGIS'e sorulan gerdirme
değerleri:

| Bant | Kaynak Min–Max | Çıktı Min–Max (eşitlemeden önce) |
|---|---|---|
| Red | 116 – 1422 | 107 – 1371 |
| Green | 363 – 1943 | 406 – 1961 |
| Blue | 155 – 2365 | 109 – 2408 |

Yalnızca bu değerleri eşitlemek, ekrandaki **piksellerin %95,7'sinin rengini değiştirdi** —
model çıktısı hiç değişmeden. **Bu adımı atlarsanız gördüğünüz farkın büyük bölümü süper
çözünürlük değil, renk ölçeğidir.**

**Önce kaynak katmanın değerlerini okuyun:**

19. Layers panelinde **alttaki** (kaynak) katmana **çift tıklayın**. Layer Properties
    penceresi açılır.
20. Sol sütundan **Symbology** (Sembol Sistemi) sekmesini seçin.
21. **Band Rendering** başlığı altında üç satır vardır: **Red band**, **Green band**,
    **Blue band**. Her satırın sağında **Min** ve **Max** kutuları vardır.
22. **Altı sayıyı da bir kağıda yazın** — üç bandın Min ve Max değerleri. Şuna benzer
    görünürler:

    ```
    Red band    Min 116     Max 1422
    Green band  Min 363     Max 1943
    Blue band   Min 155     Max 2365
    ```

    (Sizin sayılarınız farklı olabilir; önemli olan **kaynağınkileri** yazmanız.)
23. **Cancel** (İptal) ile kapatın — kaynakta hiçbir şey değiştirmiyoruz.

**Sonra aynı değerleri çıktı katmanına yazın:**

24. Layers panelinde **üstteki** (çıktı) katmana **çift tıklayın**.
25. Yine **Symbology** sekmesi, yine **Band Rendering**.
26. **Red band** satırındaki **Min** kutusuna kağıttaki kırmızı Min değerini, **Max** kutusuna
    kırmızı Max değerini yazın. Aynısını **Green band** ve **Blue band** için yapın.
    **Altı kutunun altısını da** doldurun.
27. Hemen altındaki **Min / Max Value Settings** başlığında seçili düğmenin
    **Cumulative count cut**'tan **User defined**'a kendiliğinden geçtiğini göreceksiniz.
    Geçmediyse **User defined**'ı elle seçin.
28. **OK** (Tamam) ile kapatın.

Artık iki katman **aynı renk ölçeğini** kullanıyor ve aradaki her fark modelden geliyor.

### 3.5 Öncesi/sonrası: üstteki katmanın onay kutusu

29. Haritada bir yere iyice **yakınlaşın** (fare tekerleği ileri). Vadi kenarları, tarla
    sınırları ve yol izleri en iyi görünen yerlerdir.
30. Layers panelinde **üstteki** katmanın **solundaki onay kutusunu kapatıp açın.**

    * **Kutu işaretliyken:** model çıktısı, 2,5 m.
    * **Kutu boşken:** altındaki kaynak, 10 m.

    **Öncesi/sonrası karşılaştırması budur.** Başka bir araca gerek yoktur.

31. Birkaç kez açıp kapatın. Kenarlar keskinleşir ve yumuşar; çerçeve, konum ve renk ölçeği
    değişmez.

**Biri "bu karşılaştırma dürüst mü?" diye sorarsa:** *"Evet — iki katman da aynı gerdirme
değerlerini kullanıyor ve o değerler kaynaktan alındı."*

**Ne söylenmeli:** bu, danışmanın adını verdiği modeldir ve Türkiye görüntüsü üzerinde
çalışmaktadır. Referans aracın kendisi bu veriyi **okuyamaz** — yalnızca THEIA/MAJA ya da
L1C SAFE biçimini kabul eder — bu yüzden modelin Türkiye verisiyle kullanılabildiği tek yol
bu eklentidir.

---

## Bölüm 4 — Karşılaştırma: GenCP modeli (2×)

Yaklaşık **22–35 saniye** — makine meşgulse uzun ucuna yaklaşır, ölçüldü. Aynı düzen:
**önce katman olarak yükleyin**, sonra eklentiden katmanı seçin.

1. **Layer** > **Add Layer** > **Add Raster Layer…**, **…**, `Command + Shift + G`:

   ```
   /Users/vedat/Documents/GenCP-Generative-Goruntu-Uretimi-OpenStreetMap/tubitak/data/sr_model_input
   ```

2. **DEMO_INPUT_36SXJ_4096px_B02-B03-B04_uint16DN_10m.tif** (adında **WSX4 geçmeyen**)
   dosyasına çift tıklayın, **Add**, **Close**.
3. Eklenti penceresinde **Raster katman** kutusundan bu katmanı seçin.
4. **Girdi** satırında **`3 bant`** yazmalıdır.
5. **Yöntem** kutusundan **Eğitilmiş model — GenCP (2×)** seçin.
6. **Model dosyası**: **…** > `Command + Shift + G` >

   ```
   /Users/vedat/Documents/GenCP-Generative-Goruntu-Uretimi-OpenStreetMap/tubitak/data/sr_models
   ```

   ve **gencp_sr_x2_v1.onnx** dosyasına çift tıklayın.
7. **Model künyesi** satırı:

   ```
   gencp_sr_x2_v1.onnx · DN/5000 · 2× · 3 bant B02,B03,B04 · yumuşak geçişli birleştirme · adım 16306/20000
   ```

8. **Çalıştır**. `Bitti · 81 karo · … sn · 323 MB …` yazısı çıkar. **Karo sayısı 81
   olmalıdır**; süre 22 ile 35 saniye arasında değişir. (**529 karo** değil — 529, Bölüm
   5'teki bikübik işidir; o çok daha büyük bir dosyadır.)
9. Karşılaştırmak için **3.4 ve 3.5 adımlarını bu katman çifti için tekrarlayın**: kaynağın
   Min/Max değerlerini okuyun, çıktıya yazın, sonra üstteki katmanın onay kutusunu açıp
   kapatın.

---

## Bölüm 5 — Karşılaştırma: bikübik

Taban çizgisi. Yaklaşık **39 saniye** (bu dosya çok daha büyüktür).

1. **Layer** > **Add Layer** > **Add Raster Layer…**, `Command + Shift + G`:

   ```
   /Users/vedat/Documents/GenCP-Generative-Goruntu-Uretimi-OpenStreetMap/tubitak/data/tiles36SVJ
   ```

   **TCI.tif**, **Add**, **Close**.
2. **Raster katman** kutusundan **TCI**'yi seçin.
3. **Yöntem** kutusundan **Bikübik** seçin.
4. **Çalıştır**.

TCI 8 bitlik görsel bir dosyadır; renk ölçeği zaten 0–255'tir, bu yüzden 3.4 adımına
genellikle gerek kalmaz. Yine de iki katmanın Min/Max değerlerine bakmak iyi olur.

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
| Menülerde Türkçe yazı arıyorum, bulamıyorum | QGIS'in kendi arayüzü İngilizcedir. Türkçe olan yalnızca eklenti penceresidir |
| **Raster** menüsünde **GenCP SR** yok | Bölüm 2 adım 8: **Installed** listesinde onay kutusu |
| **Model künyesi** boş kalıyor, model seçtiğim halde | wsx4 için: `wsx4_spatrad.yaml` dosyası `.onnx` yanında değil |
| **Model künyesi**nde **onnxruntime** uyarısı | Model yolları çalışmaz. **Bikübik ile devam edin**; o `onnxruntime` istemez |
| Eklenti açılırken **rasterio** uyarısı | Bu QGIS kurulumunda `rasterio` yok; gösteri bu makinede yapılamaz |
| Durum satırında "4 bant bekler" ya da "16 bit … bekler" | Yöntem ile dosya eşleşmiyor. Bölüm 6'daki tabloya bakın |
| **Çalıştır** soluk, neden belirsiz | Fareyi düğmenin üzerinde bekletin; eksik olanı yazar |
| Layers panelinde tek satır var | Girdi katman olarak yüklenmemiş. Bölüm 3.1'e dönün |
| Sonuç katmanı kaynağın altında kaldı | Layers panelinde fareyle tutup en üste sürükleyin |
| İki katman aynı sahne olduğu halde çok farklı renkte | Bölüm 3.4 yapılmamış: renk ölçeği eşitlenmemiş |
| İş çok uzun sürüyor | **Durdur**. Diske eksik dosya yazılmaz |
| "Başarısız:" ile başlayan yazı | **View** (Görünüm) > **Panels** > **Log Messages** > **GenCP SR** |
| wsx4 hiç çalışmıyor ve zaman yok | **GenCP modeli**, o da olmazsa **Bikübik** ile gösterin |

**Bir şey çökerse:** eklenti penceresini kapatıp **Raster > GenCP SR**'den yeniden açmak,
QGIS'i kapatmadan durumu sıfırlar.

---

## Gösteriden sonra temizlik

Çıktılar büyüktür. Önce katmanları QGIS'ten kaldırın (Layers panelinde sağ tıklayıp
**Remove Layer** — Katmanı Kaldır), sonra:

```bash
rm -f /Users/vedat/Documents/GenCP-Generative-Goruntu-Uretimi-OpenStreetMap/tubitak/data/sr_model_input/*_sr_x2.tif /Users/vedat/Documents/GenCP-Generative-Goruntu-Uretimi-OpenStreetMap/tubitak/data/sr_model_input/*_sr_x4.tif /Users/vedat/Documents/GenCP-Generative-Goruntu-Uretimi-OpenStreetMap/tubitak/data/tiles36SVJ/TCI_sr_x2.tif
```
