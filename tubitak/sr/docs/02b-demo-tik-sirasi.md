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

## Eklenti ne yapar — iki yöntem, iki ayrı dosya

Eklenti bir rasterı alır, piksel boyunu ikiye böler ve sonucu yeni bir GeoTIFF olarak yazar.
**İki yöntem vardır ve her biri farklı bir girdi dosyası ister.** Yanlış eşleştirme yaparsanız
eklenti çalışmayı reddeder ve nedenini söyler.

| Yöntem | Ne yapar | Hangi dosyayı ister |
|---|---|---|
| **Bikübik** | Taban çizgisi. Yeni bilgi üretmez, var olanı yeniden örnekler. Görüntü yumuşar. | **TCI** dosyası (8 bit, görsel) |
| **Eğitilmiş model (ONNX)** | Ayrıntı üretir. Bu, projenin eğittiği ağdır. | Adı **MODEL_INPUT_** ya da **DEMO_INPUT_** ile başlayan dosya (16 bit, yansıtma) |

**Gösteride söylenmesi gereken cümle:** çıktı 5 m ızgaradadır ve ızgara doğruluğu
denetlenmiştir, ama **5 m çıktı doğrulanmamıştır**. Model 20 m→10 m üzerinde eğitildi ve
10 m→5 m uygulanıyor; bu iki aralığın aynı davrandığı varsayılıyor ve bu varsayım bu projeyle
sınanamaz. "5 m çözünürlüklü görüntü ürettik" **denmemelidir**; "5 m ızgaraya, eğitilmiş
modelin takılı olduğu bir hat kurduk" denmelidir.

---

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

### 0.2 Dört dosyanın yerinde olduğunu doğrulayın

```bash
ls -l /Users/vedat/Documents/GenCP-Generative-Goruntu-Uretimi-OpenStreetMap/tubitak/data/sr_dist/gencp_super_resolution.zip /Users/vedat/Documents/GenCP-Generative-Goruntu-Uretimi-OpenStreetMap/tubitak/data/sr_models/gencp_sr_x2_v1.onnx /Users/vedat/Documents/GenCP-Generative-Goruntu-Uretimi-OpenStreetMap/tubitak/data/sr_model_input/DEMO_INPUT_36SXJ_4096px_B02-B03-B04_uint16DN_10m.tif /Users/vedat/Documents/GenCP-Generative-Goruntu-Uretimi-OpenStreetMap/tubitak/data/tiles36SVJ/TCI.tif
```

**Dört satır** görmelisiniz. `No such file` yazan varsa o dosya eksiktir ve gösteride o yol
çalışmaz.

Yolları not edin; bunlar gösteride tek tek gerekecek:

| Ne | Tam yol |
|---|---|
| Eklenti (zip) | `…/tubitak/data/sr_dist/gencp_super_resolution.zip` |
| **Model** (ONNX) | `…/tubitak/data/sr_models/gencp_sr_x2_v1.onnx` |
| **Model girdisi** (gösteri) | `…/tubitak/data/sr_model_input/DEMO_INPUT_36SXJ_4096px_B02-B03-B04_uint16DN_10m.tif` |
| **Bikübik girdisi** | `…/tubitak/data/tiles36SVJ/TCI.tif` |

(`…` = `/Users/vedat/Documents/GenCP-Generative-Goruntu-Uretimi-OpenStreetMap`)

---

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

## Bölüm 3 — GÖSTERİNİN ANA KISMI: eğitilmiş model

Bu, gösterilecek olan şeydir. Yaklaşık **23 saniye** sürer.

### 3.1 Girdi katmanını ekleyin

1. **Katman** > **Katman Ekle** > **Raster Katman Ekle…**
2. **Raster veri kümesi(leri)** kutusunun sağındaki **…** düğmesi.
3. `Command + Shift + G`, sonra yapıştırıp `Enter`:

   ```
   /Users/vedat/Documents/GenCP-Generative-Goruntu-Uretimi-OpenStreetMap/tubitak/data/sr_model_input
   ```

4. **DEMO_INPUT_36SXJ_4096px_B02-B03-B04_uint16DN_10m.tif** dosyasına çift tıklayın.
5. **Ekle**, sonra **Kapat**.
6. Haritada görüntü belirir. **Katmanlar** panelinde uzun adlı bir satır oluşur.

**Görüntü karanlık ya da tuhaf renkli görünebilir — bu normaldir.** Bu bir görsel dosya
değil, 16 bitlik yansıtma verisidir; QGIS onu otomatik olarak güzel göstermez. Modelin
gördüğü şey budur.

Görüntü hiç görünmüyorsa: **Katmanlar** panelinde satıra sağ tıklayın, **Katmana
Yakınlaştır**.

### 3.2 Eklentiyi açın ve modeli seçin

7. **Raster** > **GenCP SR** > **GenCP Super-Resolution…**
8. **Girdi** bölümünde **Yüklü katmandan** seçili olmalı; **Raster katman** kutusundan
   **DEMO_INPUT_…** katmanını seçin.
9. **Girdi** satırında şunu görmelisiniz:

   ```
   4096 × 4096 piksel · 3 bant, uint16 · EPSG:32636 · 10 m çözünürlük
   ```

   **`uint16` yazması önemlidir.** `uint8` yazıyorsa yanlış dosyayı seçtiniz.

10. **Ayarlar** bölümünde **Yöntem** kutusunu açın ve **Eğitilmiş model (ONNX)** seçin.
11. **Model dosyası** kutusu artık tıklanabilir. Sağındaki **…** düğmesine basın,
    `Command + Shift + G`, sonra:

    ```
    /Users/vedat/Documents/GenCP-Generative-Goruntu-Uretimi-OpenStreetMap/tubitak/data/sr_models
    ```

12. **gencp_sr_x2_v1.onnx** dosyasına çift tıklayın.
13. **Model künyesi** satırında şu belirmelidir:

    ```
    gencp_sr_x2_v1.onnx · DN/5000 · 2× · 3 bant B02,B03,B04 · adım 16306/20000
    ```

    Bu satır **modelin kendi içinden** okunur. Eklenti bu sayıları kendi içinde saklamaz.
    `adım 16306/20000`, eğitimin kayıtlı programın 16306. adımında durduğunu söyler.

14. **Çıktı dosyası** kutusu kendiliğinden dolmuştur. Olduğu gibi bırakın.
15. **İş bitince haritaya ekle** işaretli olmalı.

### 3.3 Çalıştırın

16. **Çalıştır** düğmesine basın. Çıktı zaten varsa **Evet** deyin.
17. İlerleme çubuğu dolar; altında **Karo 12 / 81** gibi bir yazı hızla artar.
18. Yaklaşık **23 saniye** sonra:

    ```
    Bitti · 81 karo · 23,0 sn · 323 MB Katman eklendi ve girdiyle hizalı.
    ```

19. **Katmanlar** panelinde yeni bir katman belirir.

### 3.4 Sonucu gösterin

20. Yeni katmanı **Katmanlar** panelinde en üste sürükleyin.
21. Bir yere iyice **yakınlaşın** (fare tekerleği ileri). Vadi kenarları ve yol izleri en iyi
    görünen yerlerdir.
22. Yeni katmanın onay kutusunu **kapatıp açın**: alttaki 10 m katmanla arasındaki fark budur.

**Ne söylenmeli:** model, kenarların bir kısmını geri getirir; bikübik getirmez. Ölçüldü:
model çıktısının kenar yoğunluğu hedefin altındadır, yani ağ olmayan ayrıntı **uydurmaz**,
eksik bırakır. Bu, bu uygulama için doğru olan taraftır.

---

## Bölüm 4 — Karşılaştırma: bikübik

Aynı işi taban çizgisiyle göstermek için. Yaklaşık **39 saniye** sürer (bu dosya çok daha
büyüktür: 10980 × 10980).

1. **Katman** > **Katman Ekle** > **Raster Katman Ekle…**, `Command + Shift + G`:

   ```
   /Users/vedat/Documents/GenCP-Generative-Goruntu-Uretimi-OpenStreetMap/tubitak/data/tiles36SVJ
   ```

2. **TCI.tif** dosyasına çift tıklayın, **Ekle**, **Kapat**.
3. Eklenti penceresinde **Raster katman** kutusundan **TCI** katmanını seçin.
4. **Yöntem** kutusundan **Bikübik** seçin.
5. **Çıktı dosyası** yolunu olduğu gibi bırakın, **Çalıştır**.
6. Yaklaşık 39 saniye sonra `Bitti · 529 karo · …` yazısı çıkar.

---

## Bölüm 5 — Yanlış dosyayı vermek (isteğe bağlı, ama etkili)

Eklentinin yanlış girdiyi **reddettiğini** göstermek, çalıştığını göstermek kadar
değerlidir. Ölçüldü ve şöyle davranır:

1. **Yöntem** kutusundan **Eğitilmiş model (ONNX)** seçin.
2. **Raster katman** kutusundan **TCI** katmanını seçin (bu 8 bitlik görsel dosyadır).
3. **Çalıştır** düğmesi **soluklaşır** ve durum satırında şu çıkar:

   > Model **16 bit tam sayı (uint16)** yansıtma değerleri bekler; seçilen dosyanın veri tipi
   > **uint8**.
   >
   > TCI dosyası 8 bitlik *görsel* bir birleşimdir; modelin eğitildiği veri bu değildir ve
   > model bu dosyayla anlamsız sonuç üretir.
   >
   > Model yolu için adı **MODEL_INPUT_** ile başlayan, B02,B03,B04 bantlarını içeren
   > yansıtma dosyasını seçin. TCI dosyasını **Bikübik** yöntemiyle kullanabilirsiniz.

4. Diske **hiçbir dosya yazılmaz**. Eklenti çalışıp inandırıcı ama yanlış bir sonuç üretmez.
5. **Yöntem**'i **Bikübik**'e geri alın: uyarı kaybolur, **Çalıştır** yeniden etkinleşir.

---

## Sorun çıkarsa — gösteri sırasında

| Belirti | Ne yapılmalı |
|---|---|
| **Raster** menüsünde **GenCP SR** yok | Bölüm 2 adım 8: **Kurulu** listesinde onay kutusu |
| Eklenti açılırken **rasterio** uyarısı çıkıyor | Bu QGIS kurulumunda `rasterio` yok; gösteri bu makinede yapılamaz |
| **Model künyesi** satırında **onnxruntime** uyarısı | Model yolu çalışmaz. **Bikübik ile devam edin** — o `onnxruntime` istemez ve gösteri sürer |
| Durum satırında "16 bit … bekler" yazıyor | Yanlış dosya. Model için **DEMO_INPUT_…**, bikübik için **TCI.tif** |
| **Çalıştır** soluk ve neden belirsiz | Fareyi düğmenin üzerinde bekletin; eksik olanı yazar |
| İş çok uzun sürüyor | **Durdur**'a basın. Diske eksik dosya yazılmaz. Daha küçük **DEMO_INPUT_** dosyasıyla tekrar deneyin |
| "Başarısız:" ile başlayan bir yazı | **Görünüm** > **Paneller** > **Günlük Mesajları** > **GenCP SR** sekmesi |
| Çıktı katmanı görünmüyor | **Katmanlar** panelinde en üste sürükleyin |
| Model yolu hiç çalışmıyor ve zaman yok | **Bikübik ile gösterin.** Çalıştığı ölçülmüştür ve hiçbir ek pakete bağlı değildir |

**Gösteri sırasında bir şey çökerse:** eklenti penceresini kapatıp **Raster > GenCP SR**'den
yeniden açmak, QGIS'i kapatmadan durumu sıfırlar.

---

## Gösteriden sonra temizlik

Çıktılar büyüktür (bikübik çıktısı ~1,2 GB). Silmeden önce katmanları QGIS'ten kaldırın
(**Katmanlar** panelinde sağ tıklayıp **Katmanı Kaldır**), sonra:

```bash
rm -f /Users/vedat/Documents/GenCP-Generative-Goruntu-Uretimi-OpenStreetMap/tubitak/data/sr_model_input/DEMO_INPUT_36SXJ_4096px_B02-B03-B04_uint16DN_10m_sr_x2.tif /Users/vedat/Documents/GenCP-Generative-Goruntu-Uretimi-OpenStreetMap/tubitak/data/tiles36SVJ/TCI_sr_x2.tif
```
