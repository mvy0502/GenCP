# Gösterim

`gencp_demo.qgz` gösterim için hazırlandı. Açıldığında referans katman yüklü gelir,
eklentinin bütün dosya yolları projenin içinden dolar. Klavyeye dokunmadan çıktı alınır.

Ölçülen süre: proje açılışından çıktı katmanına **1,2 saniye**, önbellek boşken, QGIS
4.2.1 / macOS. İki tıklama: eklentiyi aç, **Üret**.

Seçilen alan Ankara `ank_4_23`. Bilerek seçildi: güven katmanında her üç bant da
görünür — yaklaşık %30 yeşil, %29 turuncu, %41 kırmızı. Tek renk çıkan bir örnek hiçbir
şey göstermez.

## Akış

**1. Projeyi açın.** `tubitak/demo/gencp_demo.qgz`.

Katman panelinde **referans (ank_4_23)** görünür. Bu gerçek bir Sentinel-2 görüntüsüdür;
üretilecek alan ve koordinat sistemi ondan okunur.

**2. Eklentiyi açın.** **Raster > GenCP > GenCP Synthetic Reference**.

Girdi bölümündeki kapsam, KRS ve karo sayısı kendiliğinden dolmuştur. Gelişmiş bölümü
kapalıdır: dosya yolları hatırlandığı için gösterim sırasında dosya aranmaz.

**3. Üret.** Düğme pencerenin altındadır.

İlerleme çubuğunun yanındaki satır adımı yazar: rasterleştirme, üretim, güven, birleştirme.
İş arka planda çalışır, QGIS donmaz.

**4. Sonuç.** Haritaya iki katman eklenir: üretilen görüntü ve `gencp_reference_osm`,
yani modelin gördüğü rasterleştirilmiş girdi.

Gösterilecek üç şey:

- **Girdi ile çıktıyı karşılaştırın.** `gencp_reference_osm` katmanını açıp kapatın.
  Biri modelin gördüğü harita, öteki onun ürettiği görüntü. Nereyi tutturduğu, nereyi
  uydurduğu görünür.

  Karşılaştırma yaparken üretilen katmanın **en üstte** olmasına dikkat edin. Katman
  panelinde referans görüntü üstte kalırsa karşılaştırdığınız şey üretim değil, referansın
  kendisidir. Üretilen katman artık tam opak çizilir; alttaki katmanla karışmaz.
- **Güveni gösterin.** Çıktının 4. bandı alfa kanalıdır ve sürekli güven değerini taşır.
  Katman özelliklerinden 4. bandı tek bant gri olarak açarsanız güven haritası ortaya
  çıkar: açık bölgeler girdiye dayanır, koyu bölgeler uydurmadır.

  Eklenti katmanı haritaya eklerken 4. bandı **çizimde yok sayar**; görüntü tam opak
  görünür. Bu bilerek yapılıyor. Alfa bandı burada saydamlık değil güven taşır, ama QGIS
  bunu bilemez ve varsayılan olarak alttaki katmanla karıştırır. Karıştırdığında
  karşılaştırma bozulur: üretilen görüntü, altındaki gerçek görüntüyle harmanlanıp
  olduğundan çok daha isabetli görünür.
- **Özeti okuyun.** Çalıştırma bölümündeki tek satır her bandın yüzdesini verir.

Renkli üç bantlı katmanı da göstermek isterseniz, üretimden önce Gelişmiş bölümünden
**Renkli güven katmanı da üret** kutusunu işaretleyin.

## Gösterimden önce

Otuz saniyelik denetim:

```bash
cd <depo kökü>
QT_QPA_PLATFORM=offscreen GENCP_REPO_ROOT="$PWD" \
  /Applications/QGIS-final-4_2_1.app/Contents/MacOS/QGIS-final-4_2_1 \
  --nologo --code tubitak/tests/demo_dry_run.py
cat /tmp/demo_dry_run.txt
```

`18/18 checks passed` çıkıyorsa gösterim hazırdır. Betik projeyi sıfırdan açar, hatırlanan
ayarları siler ki yolları yalnızca proje sağlasın, sonra klavyeye dokunmadan çıktıya
kadar gider.

## İki olası aksaklık

**`onnxruntime` kurulu değil.** Üretim sırasında `No module named 'onnxruntime'` çıkar.
Gösterim sırasında kurmaya kalkışmayın: kurulumdan sonra QGIS'i yeniden başlatmak gerekir.
Önceden **Eklentiler > Python Konsolu** içinde denetleyin:

```python
import onnxruntime; print(onnxruntime.__version__)
```

Hata verirse, gösterimden önce kurun ve QGIS'i kapatıp açın. Komut QUICKSTART.md'de.

**Bir dosya yolu değişmiş.** Projede yollar mutlak yazılıdır. Depo başka bir makinede farklı bir
klasördeyse eklenti hangi dosyayı bulamadığını yazar. Düzeltmesi yirmi saniye sürer:
Gelişmiş bölümünü açın, **Gözat** ile eksik dosyayı gösterin. Model için de aynısı. Yeni
yol hatırlanır.

Bu makinedeki yerler:

| Ne | Yol |
|---|---|
| Referans raster | `tubitak/data/ankara/run/ref/ank_4_23.tif` |
| OSM çıkarımı | `tubitak/data/geofabrik/ankara_chips/ank_4_23.osm.pbf` |
| CLC+ Backbone | `tubitak/data/clcplus/CLMS_CLCplus_RASTER_2021_010m_eu_03035_V1_1.tif` |
| Model | `tubitak/data/plugin_models/gencp_C2_fp32.onnx` |
| Çıktı klasörü | `tubitak/data/demo_out/` |

Eklenti menüde görünmüyorsa: **Eklentiler > Eklentileri Yönet ve Kur > Ayarlar** altında
**Deneysel eklentileri de göster** işaretli olmalıdır.

## İkinci kez çalıştırmak

Aynı alan yeniden üretilirse rasterleştirme önbellekten gelir, iş bir saniyenin altına
iner. Başka bir alan göstermek için Girdi bölümünden başka bir referans katman seçin.
Önbellek alana göre ayrılır, eski karo yeniden kullanılmaz.
