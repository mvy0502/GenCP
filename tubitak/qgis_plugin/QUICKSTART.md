# GenCP Sentetik Referans — kullanım

Eklenti, seçtiğiniz bir alan için OpenStreetMap ve CLC+ arazi örtüsü verisinden
georeferanslı sentetik referans görüntü üretir. Her pikselin ne ölçüde girdiye
dayandığı, çıktının alfa kanalına ölçülmüş bir değer olarak yazılır.

Doğrulandığı ortam: QGIS 4.2.1, macOS. QGIS 3.28 için kod uyumlu yazıldı, denenmedi.
Windows denenmedi.

Terim karşılıkları: [`tubitak/docs/terimler.md`](../docs/terimler.md).

## Gerekenler

Dört dosya. **Hesap açmanız, veri kırpmanız ya da çıkarım aramanız gerekmez.** Toplam
1,78 GB.

| Dosya | Boyut | Nereden |
|---|---|---|
| `gencp_plugin.zip` | 89 KB | [sürüm sayfası](https://github.com/mvy0502/gencp-validation/releases/download/plugin-v0.2.0/gencp_plugin.zip) |
| `gencp_C2_fp32.onnx` | 208 MB | [sürüm sayfası](https://github.com/mvy0502/gencp-validation/releases/download/plugin-v0.2.0/gencp_C2_fp32.onnx) |
| `clcplus_2021_turkey_10m.tif` | 0,92 GB | [CLC+ Türkiye kırpması](https://github.com/mvy0502/gencp-validation/releases/download/clcplus-turkey-2026-08-30/clcplus_2021_turkey_10m.tif) |
| Türkiye OSM verisi | 0,64 GB | **Eklentideki düğme indirir** — elle indirmeyin |

OSM dosyasını eklenti kendisi indirir: Gelişmiş bölümündeki **Türkiye verisini indir**
düğmesi. Önce Geofabrik denenir, yanıt vermezse sabitlenmiş kopya kullanılır.

Ayrıca bir referans katman gerekir. Üretilecek alan ve KRS o katmandan okunur — çalışmak
istediğiniz alanı kapsayan herhangi bir georeferanslı raster olur.

### Neden bu dosyalar

CLC+ arazi örtüsü tabanıdır; OSM yollar, binalar ve su katmanını verir. Model ikisinden
birleşik bir görüntü üretir. Avrupa geneli CLC+ ürünü 8,82 GB'dir ve Copernicus hesabı
gerektirir; yukarıdaki bağlantı Türkiye'ye kırpılmış 0,92 GB'lık kopyadır, lisans ve atıf
bilgisi sürüm notundadır.

## Kurulum

1. **Eklentiler > Eklentileri Yönet ve Kur** penceresini açın.
2. **Ayarlar** sekmesinde **Deneysel eklentileri de göster** kutusunu işaretleyin.
   Eklenti deneysel işaretli; bu kutu boşken kurulur ama listede görünmez.
3. **ZIP'ten Kur** sekmesinden `gencp_plugin.zip` dosyasını seçip kurun.
4. Eklenti **Raster > GenCP > GenCP Synthetic Reference** altında ve araç çubuğunda çıkar.

## Üretim

Referans katmanı projeye ekleyin, eklentiyi açın.

**Girdi.** Listeden referans katmanı seçin. Kapsam, KRS ve karo sayısı kendiliğinden
dolar. KRS metrik olmalıdır. EPSG:3857 seçilirse eklenti uyarır ve düğmeler kapalı kalır;
katmanı **Dışa Aktar > Nesneleri Farklı Kaydet** ile UTM'ye çevirin. EPSG:4326 ve
EPSG:4258 gibi coğrafi sistemler kendiliğinden UTM'ye çevrilir.

**Model.** `gencp_C2_fp32.onnx` dosyasını gösterin. Yol bir kez seçilir, sonra hatırlanır.
Başka bir model seçerseniz görüntü yine üretilir ama güven katmanı üretilmez: bantlar
yalnızca bu dosyada ölçüldü.

**Çıktı.** Yazılacak dosyanın yolunu verin. Çıktı KRS varsayılan olarak referans katmanın
KRS'sidir; başka bir sistem seçerseniz özgün dosya yerinde kalır, yanına yeniden
örneklenmiş bir kopya yazılır.

**Gelişmiş.** İlk kullanımda bir kez açın:

1. **Türkiye verisini indir** düğmesine basın. Ülkenin tamamını kapsayan tek OSM dosyası
   indirilir, MD5 ile doğrulanır ve yolu kendiliğinden ayarlanır. İkinci kez basarsanız
   dosya zaten varsa yeniden indirilmez.
2. **CLC+ rasterı** için indirdiğiniz `clcplus_2021_turkey_10m.tif` dosyasını gösterin.

Her iki yol da hatırlanır; sonraki açılışlarda bu bölüme dokunmanız gerekmez. Karo
bindirmesi ve güven katmanı seçenekleri de buradadır.

**Karo bindirmesi.** Serbestçe yazılır. İki kısıt vardır ve ikisi de yazılıp geçilmiş değil,
uygulanır: değer 10 m'lik piksel ızgarasının tam katı olmalı ve bir karodan (2570 m) küçük
kalmalı. Ara bir değer karoları kesirli piksele oturtur, mozaikte alt piksel kayması yaratır
ve georeferans sözleşmesini sessizce bozar; bu yüzden eklenti böyle bir değeri kabul etmez,
en yakın kata çeker ve çektiğini söyler. En büyük geçerli değer 2560 m'dir.

640 m ölçülmüş varsayılandır: dikiş enerjisi oranı bu değerde 1,008 çıktı. Başka bir değer
seçebilirsiniz, ama o değeri biz ölçmedik. Bindirme büyüdükçe karo sayısı hızla artar —
2560 m'de adım 10 m'ye iner ve süre kullanılamaz hâle gelir. Girdi bölümündeki karo sayısı
ile süre tahmini bunu seçmeden önce gösterir.

**Üret.** Düğme pencerenin altındadır ve her boyutta görünür. İş arka planda çalışır,
QGIS donmaz. İlerleme çubuğunun yanındaki satır hangi adımda olduğunu yazar.
**Vazgeç** işi durdurur; diske eksik dosya yazılmaz.

İş bitince haritaya iki katman eklenir: üretilen görüntü ve `<ad>_osm` adıyla modelin
gördüğü rasterleştirilmiş girdi.

### Önizleme

**Önizlemeyi göster** düğmesi, modelin göreceği rasterleştirilmiş girdiyi ekrana getirir.
Bu bir uydu görüntüsü değil, OSM yolları ile arazi örtüsünden çizilmiş bir haritadır.
Üretim için gerekli değildir; girdinin beklediğiniz gibi olduğunu görmek isterseniz
kullanın. Açıkken karoda kaç piksel yol, bina, su ve arazi kullanımı olduğu da yazılır.

## Güven

Güven, çıktı GeoTIFF'inin **4. bandına (alfa)** sürekli değer olarak yazılır:

    alfa = clip((z + 4) / 8, 0, 1) × 255          z = alfa / 255 × 8 − 4

4. bant güvendir; onu saydamlık sayan yazılım görüntüyü altındaki katmanla harmanlar.
Çıktının yanına yazılan `.qml` dosyası QGIS'te bunu kapatır.

255 en yüksek güven demektir. Bu eşleme dosyanın künyesine de yazılır. **RGB bantları değişmez**:
alfa kanalını yok sayan bir uygulama, alfa eklenmeden önceki görüntüyle birebir aynı
baytları okur.

Göz için üç renkli ayrı bir katman da üretilebilir (Gelişmiş bölümünde). Bantların
ölçülmüş karşılıkları:

| Bant | Ayrık Avrupa kümesinde ortanca eşleştirme hatası |
|---|---|
| Kırmızı — kullanmayın | 3,31 piksel |
| Turuncu — dikkatli kullanın | 2,63 piksel |
| Yeşil — kullanılabilir | 1,33 piksel |

İş bitince Çalıştırma bölümünde tek satırlık bir özet çıkar: her bandın yüzdesi. Kırmızı
%20'yi aşarsa ayrıca uyarı verilir.

### Ölçümün sınırları

Skor rasterleştirilmiş girdiden hesaplanır, model çalıştırılmaz. Bu yüzden üretime
kayda değer bir süre eklemez.

Bant sınırları 150 karoluk ayrık Avrupa kümesinde, C2 kolunda ölçüldü. Spearman rho
**-0,76**; KARIOS'un eşleştirdiği nokta sayısı sabit tutulduğunda **-0,38**. Güveni en düşük yarı
atıldığında ortanca hata 1,98 pikselden 1,30 piksele iner.

Aynı sınırlar 130 karoluk Ankara kümesine değiştirilmeden uygulandığında sıralama korunur
ve ayrışma artar (kırmızı/yeşil oranı 2,5 kat yerine 5,2 kat). Kırmızı bandın mutlak
değeri %7 içinde kalır. Turuncu ve yeşil bantlar Türkiye'de daha düşük çıkar; yukarıdaki
Avrupa sayıları bu iki bant için kötümserdir.

Bantlar yalnızca `gencp_C2_fp32.onnx` dosyasında ölçüldü. Başka bir model seçilirse Model
bölümünde uyarı çıkar ve güven katmanı üretilmez. Denetim dosya adına değil, SHA-256
özetine bakar.

Bir karoda hiç OSM nesnesi olmasa bile bant yeşil çıkabilir: skor arazi örtüsü
çeşitliliğini de sayar. "OSM nesnesi yok" uyarısı bu yüzden banttan bağımsız olarak
ayrıca verilir.

## `onnxruntime` kurulu değilse

Üretim sırasında `No module named 'onnxruntime'` hatası alırsanız kütüphane QGIS'in kendi
Python'unda yok demektir. Başka bir Python'a kurmak işe yaramaz.

**Eklentiler > Python Konsolu** içinde yorumlayıcının yolunu öğrenin:

```python
import sys; print(sys.executable)
```

Terminalde, çıkan yolu kullanarak kurun:

```bash
/Applications/QGIS.app/Contents/MacOS/bin/python3 -m pip install onnxruntime
```

Yerel `.osm.pbf` kullanacaksanız `osmium` da gerekir. Kurulumdan sonra QGIS'i kapatıp
yeniden açın.

macOS'a özgü bir not: onnxruntime QGIS uygulamasının içinde sorunsuz çalışır, ancak
paketle gelen `python3.12` çalıştırılabiliriyle denenirse "different Team IDs" hatası
verir. Bu bir kurulum sorunu değildir.

## Sık karşılaşılanlar

| Belirti | Nedeni |
|---|---|
| Eklenti kurulduğu hâlde listede yok | Kurulumun 2. adımındaki kutu işaretlenmemiş |
| Üret düğmesi kapalı | Çalıştırma bölümündeki satır neyin eksik olduğunu yazar |
| Kırmızı KRS uyarısı | Referans katman metrik olmayan bir KRS'de |
| Önizleme düğmesi kapalı | OSM çıkarımı ya da CLC+ rasterı yerinde değil |
| Çıktı boş kırsal alan gibi | Seçilen `.osm.pbf` bu alanı kapsamıyor |
| Güven katmanı üretilmedi | Seçilen model, bantların ölçüldüğü model değil |

## Lisans

Model ağırlıkları GenCP'nin CC-BY 4.0 lisanslı ağırlıklarından türetilmiştir; atıf
[telespazio-tim/GenCP](https://github.com/telespazio-tim/GenCP) projesinedir. Eklenti
çalışma anında OpenStreetMap verisi okur; OSM verisi ODbL lisanslıdır ve
[OpenStreetMap katkıcılarına](https://www.openstreetmap.org/copyright) atıf gerektirir.
CLC+ Backbone, Copernicus Land Monitoring Service ürünüdür.
