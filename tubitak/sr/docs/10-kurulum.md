# Kurulum kılavuzu — iki QGIS eklentisi

Bu belge, eklentileri **bu makine olmayan** bir bilgisayara kuracak kişi için yazılmıştır.
İçindeki her adım, 31 Ağustos 2026'da yayımlanmış zip dosyaları indirilerek, hiçbir şeyin
kurulu olmadığı yeni bir profilde denenmiştir. Denenmemiş olan her şey, denenmediği
belirtilerek yazılmıştır.

İki eklenti vardır ve birbirinden bağımsızdır:

| Eklenti | Ne yapar | Sürüm |
|---|---|---|
| **GenCP Synthetic Reference** (Proje 1) | OpenStreetMap ve arazi örtüsünden sentetik uydu görüntüsü üretir | 0.2.0 |
| **GenCP Super-Resolution** (Proje 2) | Sentinel-2 görüntüsünün çözünürlüğünü artırır | 0.1.0 |

---

## 1. Ön koşullar

### 1.1 QGIS ve işletim sistemi

| | Sınanan | Durum |
|---|---|---|
| QGIS | **4.2.1 (Belém do Pará)** | Sınanmıştır |
| İşletim sistemi | **macOS** | Sınanmıştır |
| QGIS 3.28 – 3.x | — | **Sınanmamıştır.** Eklentilerin `metadata.txt` dosyaları en düşük sürüm olarak 3.28 belirtir, ancak bu sürümlerde hiç çalıştırılmamıştır |
| Windows, Linux | — | **Sınanmamıştır** |

Sınanmamış bir yapılandırmanın çalışacağı taahhüt edilmez. Desteklenmediği anlamına da
gelmez; yalnızca denenmemiştir.

### 1.2 Python paketleri

Eklentiler QGIS'in **kendi** Python yorumlayıcısını kullanır. Bilgisayarda ayrıca kurulu olan
bir Python'un içindeki paketler işe yaramaz; paketlerin QGIS'in içinden içe aktarılabiliyor
(import) olması gerekir.

**Python konsolu**, QGIS'in içinde komut yazılan penceredir. Şu şekilde açılır:
**Eklentiler > Python Konsolu** (İngilizce arayüzde **Plugins > Python Console**).

Aşağıdaki satırlar bu konsola tek tek yapıştırılıp Enter'a basılarak denenmelidir.

| Paket | Hangi eklenti / hangi yöntem için | Kontrol satırı |
|---|---|---|
| `rasterio` | **Her ikisi de, her yöntem için zorunludur** | `import rasterio; print(rasterio.__version__)` |
| `onnxruntime` | Proje 1'in tamamı; Proje 2'de yalnızca model yöntemleri | `import onnxruntime; print(onnxruntime.__version__)` |
| `PyYAML` | Yalnızca Proje 2'de wsx4 modeli için | `import yaml; print(yaml.__version__)` |

Bir sürüm numarası yazdırılıyorsa paket vardır. `ModuleNotFoundError` alınıyorsa paket yoktur.

**Ölçülmüş davranış — paket eksikken ne olur.** Bu tablo, paketler sınama sırasında
yorumlayıcıdan kaldırılarak elde edilmiştir; kaynak kodun okunmasıyla değil.

| Eksik paket | Eklenti | Gözlenen sonuç |
|---|---|---|
| `rasterio` | Proje 2 | Eklenti açılırken uyarı verir ve çalışmaz |
| `rasterio` | Proje 1 | Üretim başlarken **ham Python hatası**: `ImportError`, `gencp_core/extent.py` satır 65 |
| `onnxruntime` | Proje 2 | **Eklenti sorunsuz yüklenir. Bikübik yöntemi çalışır.** Yalnızca model yöntemleri kullanılamaz |
| `onnxruntime` | Proje 1 | Üretim çıkarım aşamasında **ham Python hatası**: `ImportError`, `gencp_core/infer.py` satır 54 |

**Proje 1, eksik pakete Türkçe bir ileti üretmez.** Kullanıcı ham bir Python hatası görür.
Bu bir bulgudur, kusur olarak düzeltilmemiştir; eklenti kodu dondurulmuştur.

**Proje 2'nin ilettiği Türkçe metinler**, eklentiden birebir alınmıştır:

`rasterio` eksikken — *bu ileti sınama sırasında gerçekten üretilmiştir*:

> **rasterio** paketi bu QGIS kurulumunda yok. Eklenti raster okuyup yazmak için onu kullanır ve onsuz çalışamaz.
>
> QGIS'in Python ortamına `rasterio` kurulmalıdır.

`onnxruntime` eksikken — *metin eklentiden alınmıştır; bu iletinin ekranda belirdiği
sınanmamıştır*:

> **onnxruntime** paketi bu QGIS kurulumunda yok. Eğitilmiş model bu paketle çalışır.
>
> **Bikübik** yöntemi onsuz da çalışır; model yolu için QGIS'in Python ortamına `onnxruntime` kurulmalıdır.

`PyYAML` eksikken — *metin eklentiden alınmıştır; bu iletinin ekranda belirdiği
sınanmamıştır*:

> **PyYAML** paketi bu QGIS kurulumunda yok. Eklenti, künye taşımayan modellerin (wsx4 gibi) yapılandırmasını yanındaki .yaml dosyasından okur ve onsuz okuyamaz.
>
> QGIS'in Python ortamına `PyYAML` kurulmalıdır.

---

## 2. Kurulum adımları

**Profil**, QGIS'in ayarlarını ve kurulu eklentilerini sakladığı klasördür. Aşağıdaki adımlar
kullanılan profili değiştirmez; eklenti o an açık olan profile kurulur.

### 2.1 Her iki eklenti için ortak ve atlanamaz adım

**Her iki eklenti de "deneysel" (experimental) olarak işaretlidir.** Bu kutu işaretlenmeden
eklenti kurulur fakat listede görünmez; kullanıcı kurulumun başarısız olduğunu sanır.

1. **Eklentiler > Eklentileri Yönet ve Kur** açılmalıdır.
   (İngilizce arayüzde: **Plugins > Manage and Install Plugins**.)
2. Soldaki **Ayarlar** (**Settings**) sekmesine geçilmelidir.
3. **Deneysel eklentileri de göster** (**Show also experimental plugins**) kutusu
   işaretlenmelidir.

### 2.2 Proje 2 — GenCP Super-Resolution

1. Zip dosyası indirilmelidir:
   `https://github.com/mvy0502/gencp-validation/releases/download/sr-plugin-v0.1.0/gencp_super_resolution.zip`
   (49.379 bayt)
2. **Eklentiler > Eklentileri Yönet ve Kur** penceresinde **ZIP'ten Kur**
   (**Install from ZIP**) sekmesine geçilmelidir.
3. **…** düğmesiyle indirilen `gencp_super_resolution.zip` seçilmelidir.
4. **Eklentiyi Kur** (**Install Plugin**) düğmesine basılmalıdır.
5. Eklenti **Raster** menüsünde **GenCP Super-Resolution** başlığıyla görünmelidir.

### 2.3 Proje 1 — GenCP Synthetic Reference

1. Zip dosyası indirilmelidir:
   `https://github.com/mvy0502/gencp-validation/releases/download/plugin-v0.2.0/gencp_plugin.zip`
   (94.987 bayt)
2. Aynı **ZIP'ten Kur** sekmesinden bu dosya seçilip kurulmalıdır.
3. Eklenti **Raster > GenCP > GenCP Synthetic Reference** altında ve araç çubuğunda
   görünmelidir.

> Eklentinin kendi `QUICKSTART.md` dosyasında zip boyutu 73 KB olarak yazılıdır. Yayımlanmış
> dosya **94.987 bayttır**. Bu belgedeki sayı ölçülmüştür.

---

## 3. Dosyalar tablosu

> **İndirme adreslerinin tek doğru kaynağı deponun kök `README.md` dosyasındaki tablodur.**
> Aşağıdaki satırlar oradan alınmıştır; bir çelişki olursa `README.md` geçerlidir.

Eklentiler kurulduktan sonra, kullanılacak yönteme göre ek dosyalar gerekir. Hiçbiri zip'in
içinde gelmez.

| Yöntem | Gereken dosya | Nereden indirilir | Nereye konulur |
|---|---|---|---|
| **P2 — Bikübik** | *(ek dosya gerekmez)* | — | — |
| **P2 — GenCP SR, 2x** | `gencp_sr_x2_v1.onnx` (1.964.122 bayt) | `https://github.com/mvy0502/gencp-validation/releases/download/sr-plugin-v0.1.0/gencp_sr_x2_v1.onnx` | Herhangi bir klasöre; yol eklentinin **Model** alanından seçilir |
| **P2 — GenCP SR, 4x** | `gencp_sr_x4_b4.onnx` (2.086.466 bayt) | `https://github.com/mvy0502/gencp-validation/releases/download/sr-plugin-v0.1.0/gencp_sr_x4_b4.onnx` | Aynı şekilde |
| **P2 — wsx4** | `wsx4_spatrad.onnx` **ve** `wsx4_spatrad.yaml` | `https://github.com/Evoland-Land-Monitoring-Evolution/sentinel2_superresolution` — bu projenin ürünü değildir, sürüm sayfasına eklenmemiştir | **İkisi aynı klasörde, yan yana durmalıdır.** Eklenti `.yaml` dosyasını modelin yanında arar; ölçek, normalleştirme ve kırpma kenarı oradan okunur |
| **P2 — girdi** | Sentinel-2 rasteri, uint16 DN, 10 m | Kullanıcının kendi verisi | Herhangi bir klasör |
| **P1 — model** | `gencp_C2_fp32.onnx` (217.678.087 bayt) | `https://github.com/mvy0502/gencp-validation/releases/download/plugin-v0.2.0/gencp_C2_fp32.onnx` | Herhangi bir klasöre; yol eklentinin model alanından seçilir |
| **P1 — arazi örtüsü** | `clcplus_2021_turkey_10m.tif` (916.422.550 bayt) | `https://github.com/mvy0502/gencp-validation/releases/download/veri-turkiye-2026-08-31/clcplus_2021_turkey_10m.tif` | Yolu `GENCP_CLC_PATH` ortam değişkeniyle veya eklentinin alanıyla verilir |
| **P1 — OSM** | `turkey-2026-08-19.osm.pbf` (642.343.710 bayt) | `https://github.com/mvy0502/gencp-validation/releases/download/veri-turkiye-2026-08-31/turkey-2026-08-19.osm.pbf` — ya da eklentinin kendi indirme düğmesi | Herhangi bir klasör |

---

## 4. Doğrulama

### 4.1 Eklentiler göründü mü

**Eklentiler > Eklentileri Yönet ve Kur > Kurulu** listesinde şu iki satır bulunmalıdır:

- `GenCP Super-Resolution`
- `GenCP Synthetic Reference`

Görünmüyorlarsa §2.1'deki deneysel kutusu işaretlenmemiştir.

### 4.2 Proje 2 — kısa koşu

Ek dosya gerektirmediği için doğrulama **bikübik** yöntemiyle yapılmalıdır.

1. Bir Sentinel-2 rasteri QGIS'e eklenmelidir.
2. **Raster > GenCP Super-Resolution** açılmalıdır.
3. Yöntem **Bikübik**, ölçek **2x** seçilmelidir.
4. Çıktı yolu verilip çalıştırılmalıdır.

**Beklenen sonuç — sınamada ölçülmüştür.** 256 × 256 piksel, 3 bantlı, EPSG:32636, 10 m'lik
bir girdi ile:

| | Girdi | Çıktı |
|---|---|---|
| Boyut | 256 × 256 | **512 × 512** |
| KRS | EPSG:32636 | **EPSG:32636 (değişmez)** |
| Piksel boyu | 10 m | **5 m** |
| Başlangıç noktası | — | **değişmez** |

Kırpılan değer sayısı **0**, kapsanmayan piksel sayısı **0** olmalıdır.

### 4.3 Proje 1 — kısa koşu

Model, arazi örtüsü ve OSM dosyaları hazırsa küçük bir alan için üretim çalıştırılmalıdır.

**Sınamada ölçülen:** İstanbul'da yaklaşık 2,6 km × 2,3 km'lik bir alan, tek çekirdek,
**21,7 saniye**; çıktı 258 × 228 piksel, 3 bant, uint8, EPSG:32635; geçerli veri oranı
0,9999; uyarı üretilmemiştir.

---

## 5. Sorun giderme

| Belirti | Olası sebep | Yapılacak işlem |
|---|---|---|
| Eklenti kurulduğu hâlde listede görünmüyor | Her iki eklenti de deneysel işaretlidir | **Ayarlar** sekmesinde **Deneysel eklentileri de göster** kutusu işaretlenmelidir (§2.1) |
| Eklenti listede görünüyor fakat açılmıyor | `rasterio` eksiktir (Proje 2), ya da zip bozuk inmiştir | Python konsolunda `import rasterio` denenmelidir. Ayrıca indirilen dosyanın boyutu §2'deki bayt sayısıyla karşılaştırılmalıdır |
| `rasterio` bulunamadı | Paket QGIS'in Python ortamında yok | QGIS'in kendi Python ortamına `rasterio` kurulmalıdır. **Sistemdeki başka bir Python'a kurmak sonucu değiştirmez** |
| `onnxruntime` bulunamadı | Paket yok | **Proje 2'de bikübik yöntemi çalışmaya devam eder**; model yöntemleri için paket kurulmalıdır. Proje 1'in tamamı bu pakete bağımlıdır ve onsuz üretim yapamaz |
| `PyYAML` bulunamadı | Paket yok | Yalnızca wsx4 için gereklidir. Kendi modellerimiz künyelerini kendi içlerinde taşır ve `PyYAML` olmadan çalışır |
| Model dosyası seçilmemiş | Yöntem model gerektiriyor, alan boş | Model alanından `.onnx` dosyası seçilmelidir. Kurulu eklentide bu alan boş gelir; bu beklenen davranıştır |
| Yanlış dosya yanlış yöntemle verilmiş | Örneğin 3 bantlı 2x model, 4 bant bekleyen wsx4 yerine seçilmiş | Yöntem ile model eşleştirilmelidir: 2x model 3 bant (B02,B03,B04), 4x model ve wsx4 4 bant (B02,B03,B04,B08) ister |
| wsx4 seçildi fakat çalışmıyor | `.yaml` dosyası modelin yanında değil | `wsx4_spatrad.yaml`, `wsx4_spatrad.onnx` ile **aynı klasöre** konulmalıdır |
| Çıktı yazılamıyor | Hedef klasör yok, yazma izni yok, ya da disk dolu | Yazma izni olan bir klasör seçilmelidir. Ağ sürücüleri yerine yerel disk tercih edilmelidir |

---

## 6. Sınanmış ve sınanmamış olanlar

**Sınanmıştır** — 31 Ağustos 2026, QGIS 4.2.1 (Belém do Pará), macOS:

- Her iki eklenti de **yayımlanmış zip dosyalarından** indirilmiş, çalışma ağacına erişimi
  olmayan, yeni oluşturulmuş bir profile kurulmuştur.
- QGIS her ikisini de **görmüş, yüklemiş ve başlatmıştır**.
- Proje 2'nin bikübik yöntemi uçtan uca çalışmış, ızgara sözleşmesi tam olarak korunmuştur.
- Proje 1 uçtan uca çalışmış, 21,7 saniyede çıktı üretmiştir.
- `rasterio` ve `onnxruntime` yorumlayıcıdan kaldırılarak her iki eklentinin davranışı
  ölçülmüştür.

**Sınanmamıştır:**

- QGIS 3.28 ve diğer 3.x sürümleri.
- Windows ve Linux.
- Proje 2'nin **model** ve **wsx4** yöntemlerinin bu yeni profilde uçtan uca koşusu; yalnızca
  bikübik koşulmuştur.
- `PyYAML` ve `onnxruntime` eksikliğinde Türkçe iletilerin ekranda belirmesi; metinler
  eklentiden birebir alınmıştır, ancak ekrana geldikleri gözlenmemiştir.
- Bu belgedeki hiçbir adım Türkçe arayüzlü bir QGIS'te denenmemiştir; sınama İngilizce
  arayüzde yapılmıştır. Menü adlarının Türkçe karşılıkları parantez içinde verilmiştir.
