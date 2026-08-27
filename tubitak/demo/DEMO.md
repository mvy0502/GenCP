# Canlı gösterim - adım adım

Bu klasördeki `gencp_demo.qgz` dosyası gösterim için hazırlandı. Açtığınızda referans
katman yüklü gelir ve eklentinin bütün dosya yolları **projenin içinden** doldurulur:
klavyeye hiç dokunmadan çıktı üretebilirsiniz.

Ölçülen süre: proje açılışından çıktı katmanına kadar **2,2 saniye** (önbellek boşken,
QGIS 4.2.1 / macOS). Doğrulaması: `tubitak/tests/demo_dry_run.py`, 17/17.

Seçilen alan **Ankara `ank_4_23`**. Bilerek seçildi: üretilen güven katmanında üç bandın
üçü de görünür — yaklaşık **%30 yeşil, %29 turuncu, %41 kırmızı**. Tek renk çıkan bir
gösterim hiçbir şey öğretmez.

---

## Gösterim akışı - üç tık

### 0. Projeyi açın

**Proje > Aç…** ile `tubitak/demo/gencp_demo.qgz` dosyasını seçin.

> *Ekranda gösterin:* katman panelinde **referans (ank_4_23)** var. Bu, gerçek bir
> Sentinel-2 görüntüsü; üreteceğimiz sentetik görüntünün kapsamını ve koordinat sistemini
> bu katman belirliyor.

### 1. Eklentiyi açın

**Raster ▸ GenCP ▸ GenCP Synthetic Reference…**

> *Ekranda gösterin:* 1. bölümdeki **Kapsam**, **KRS** ve **Karo / süre tahmini**
> satırları kendiliğinden doldu. Hiçbir şey yazmadık; alan katmandan okundu.

> *Ekranda gösterin:* 2. bölümdeki **Gelişmiş** kapalı duruyor ve üstünde
> "Kaynak hazır: ank_4_23.osm.pbf + CLC+ …" yazıyor. Yollar hatırlandı; gösterim sırasında
> dosya aramıyoruz.

**Karo bindirmesi**ni **0 m** yapın — tek karo üretir, saniyeler sürer.

### 2. Önizleme karosunu oluşturun

3. bölümde **Önizleme karosunu oluştur** düğmesine basın. Yaklaşık **1 saniye**.

> *Ekranda gösterin:* soldaki görüntü modelin göreceği **girdi**. Uydu görüntüsü değil;
> OpenStreetMap yolları ve CLC+ arazi örtüsünden çizilmiş bir harita.

> *Ekranda gösterin:* sağdaki **Bu karodaki OSM içeriği** tablosu. Kaç piksel yol, bina,
> su, arazi kullanımı olduğunu sayıyor — "az veri var" demiyoruz, ölçüyoruz.

> *Ekranda gösterin:* onay kutusunun üstündeki kutu. Bu karonun **turuncu bantta**
> olduğunu ve o bandın Avrupa ayrık ölçümündeki hata ortancasını yazıyor. Aynı ölçü
> birazdan üretilecek güven katmanını da belirleyecek; ikisi çelişemez.

### 3. Onaylayın

**"(4,23) numaralı karoya baktım …, görüntü doğru"** kutusunu işaretleyin.

> *Söyleyin:* bu kutu işaretlenmeden **Üret** düğmesi açılmaz. Kullanıcının modele
> gidecek girdiye bakmadan çıktı üretmesini kasten engelliyoruz.

### 4. Üretin

**Üret** düğmesine basın. Yaklaşık **1 saniye**.

> *Ekranda gösterin:* düğmenin üstündeki satır hangi adımda olduğumuzu yazıyor —
> *Rasterleştiriliyor*, *Üretiliyor*, *Güven haritası hesaplanıyor*, *Birleştiriliyor*.
> İş arka planda bir QgsTask üzerinde koşuyor; QGIS donmuyor.

> *Ekranda gösterin:* haritaya **iki** katman eklendi. `gencp_reference` üretilen
> görüntü, `gencp_reference_confidence` güven katmanı.

### 5. Sonucu gösterin

Katman panelinden `gencp_reference_confidence` katmanını en üste alın.

> *Ekranda gösterin:* üç renk. **Kırmızı** — çıktı burada büyük ölçüde uydurma, kullanmayın.
> **Turuncu** — girdi zayıf. **Yeşil** — çıktı girdi bilgisine dayanıyor. Gösterge
> kendiliğinden geldi; sembolojiyi elle ayarlamadık.

> *Ekranda gösterin:* eklentinin 5. bölümündeki değerlendirme satırı: her bandın yüzdesi
> ve bütün çalışmanın ortalama bandı. **Detaylar**'ı açarsanız ölçünün gücü ve kapsamı
> yazılı — hangi korpusta ölçüldüğü dahil.

Karşılaştırma için `gencp_reference` ile referans katmanı sırayla açıp kapatın: üretilen
görüntünün yapıyı nerede tutturduğu, nerede uydurduğu görünür.

---

## Ters giderse

### `onnxruntime` yok

**Üret**'e basınca `No module named 'onnxruntime'` çıkarsa kütüphane QGIS'in kendi
Python'unda değil demektir. **Gösterim sırasında kurmaya çalışmayın** — QGIS'i yeniden
başlatmak gerekir. Önceden denetleyin:

**Eklentiler ▸ Python Konsolu**:

```python
import onnxruntime; print(onnxruntime.__version__)
```

Hata verirse, gösterimden **önce**:

```bash
# aynı konsolda:  import sys; print(sys.executable)
# sonra terminalde, çıkan yolu kullanarak:
/Applications/QGIS.app/Contents/MacOS/bin/python3 -m pip install onnxruntime
```

ve **QGIS'i tamamen kapatıp açın**.

### Bir dosya yolu taşınmış

Proje, yolları mutlak olarak taşır. Depo başka bir makinede farklı bir klasördeyse
eklenti 2. veya 4. bölümde kırmızı yazıyla **hangi dosyayı bulamadığını** söyler.

Düzeltme, gösterim sırasında bile 20 saniye sürer:

1. 2. bölümde **Gelişmiş - dosya yolları**'nı açın.
2. **Gözat…** ile eksik dosyayı gösterin.
3. Aynısını 4. bölümdeki model için yapın.

Eklenti yeni yolu hatırlar; ikinci kez sormaz.

Dosyaların bu makinedeki yerleri:

| Ne | Yol |
|---|---|
| Referans raster | `tubitak/data/ankara/run/ref/ank_4_23.tif` |
| OSM çıkarımı (40 KB) | `tubitak/data/geofabrik/ankara_chips/ank_4_23.osm.pbf` |
| CLC+ Backbone (8,2 GB) | `tubitak/data/clcplus/CLMS_CLCplus_RASTER_2021_010m_eu_03035_V1_1.tif` |
| Model | `tubitak/data/plugin_models/gencp_C2_fp32.onnx` |
| Çıktı klasörü | `tubitak/data/demo_out/` |

### Eklenti menüde yok

**Eklentiler ▸ Eklentileri Yönet ve Kur ▸ Ayarlar** → **Deneysel eklentileri de göster**
işaretli mi? Eklenti deneysel olarak işaretli; bu kutu boşsa kurulu olsa bile listede
görünmez.

### İkinci kez çalıştırmak

Aynı alanı tekrar üretirseniz rasterleştirme önbellekten gelir ve iş bir saniyenin altına
iner. Farklı bir alan göstermek isterseniz: 1. bölümden başka bir referans katman seçin —
önbellek alana göre anahtarlanır, eski karo yeniden kullanılmaz.

---

## Gösterim öncesi 30 saniyelik denetim

```bash
cd <depo kökü>
QT_QPA_PLATFORM=offscreen GENCP_REPO_ROOT="$PWD" \
  /Applications/QGIS-final-4_2_1.app/Contents/MacOS/QGIS-final-4_2_1 \
  --nologo --code tubitak/tests/demo_dry_run.py
cat /tmp/demo_dry_run.txt
```

`17/17 checks passed` görüyorsanız gösterim hazırdır. Bu betik projeyi sıfırdan açar,
hatırlanan ayarları **siler** (yolları yalnızca proje sağlasın diye), ve klavyeye
dokunmadan çıktıya kadar gider.
