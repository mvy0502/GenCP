# GenCP Sentetik Referans eklentisi - hızlı başlangıç

QGIS kullanmış, ancak bu eklentiyi hiç görmemiş biri için. Yalnızca tıklamalar.
Mimari ve gerekçe için `README.md` dosyasına bakın.

Doğrulandığı sürüm: **QGIS 4.2.1 (macOS)**. QGIS 3.28 için kod uyumlu yazıldı ama
denenmedi.

---

## Önce indirilecek iki dosya

| Dosya | Nereden | Ne işe yarar |
|---|---|---|
| `gencp_plugin.zip` (47 KB) | https://github.com/mvy0502/gencp-validation/releases/download/plugin-v0.2.0/gencp_plugin.zip | Eklentinin kendisi |
| `gencp_C3_fp32.onnx` (208 MB) | Doğrudan proje sahibinden isteyin - herkese açık olarak yayımlanmıyor | Üretici model ağırlıkları |

Sürüm sayfası: https://github.com/mvy0502/gencp-validation/releases/tag/plugin-v0.2.0

Model dosyası neden bağlantıyla verilmiyor: ağırlıklar GenCP'nin CC-BY 4.0 ağırlıklarından
türedi, ancak ince ayar girdileri ODbL lisanslı OpenStreetMap verisinden üretildi. ODbL'nin
share-alike yükümlülüğünün bu ağırlıklara uzanıp uzanmadığı belirsiz olduğu için dosya
kurum içi doğrudan aktarımla veriliyor. Ayrıntı: `tubitak/docs/evidence/BACKUP.md`.

Ayrıca elinizde bulunması gerekenler:

- **CLC+ Backbone 2021 rasterı** (`CLMS_CLCplus_RASTER_2021_010m_eu_03035_V1_1.tif`,
  8.2 GB) - Copernicus Land Monitoring Service'ten indirilir.
- **Bir `.osm.pbf` dosyası** (örneğin Geofabrik'ten `turkey-latest.osm.pbf`) - çalışacağınız
  alanı kapsamalı. Alternatif olarak eklentideki **Online (Overpass)** seçeneği kullanılabilir.
- **Bir referans katmanı** - üretilecek görüntünün kapsamını ve CRS'ini bu katman belirler.

---

## Kurulum

1. QGIS'i açın.
2. Menüden **Eklentiler > Eklentileri Yönet ve Kur...** seçin.
3. Soldaki listeden **Ayarlar** sekmesine geçin.
4. **Deneysel eklentileri de göster** kutusunu işaretleyin.
   Bu adım atlanamaz: eklenti `experimental=True` olarak işaretli olduğu için bu kutu
   işaretli değilse kurulduktan sonra listede görünmez.
5. Soldaki listeden **ZIP'ten Kur** sekmesine geçin.
6. **...** düğmesiyle indirdiğiniz `gencp_plugin.zip` dosyasını seçin.
7. **Eklentiyi Kur** düğmesine basın.
8. **Kurulu** sekmesine geçin, listede **GenCP Synthetic Reference** satırının yanındaki
   kutunun işaretli olduğunu doğrulayın.
9. Pencereyi kapatın. Eklenti artık **Raster > GenCP > GenCP Synthetic Reference...**
   menüsünde ve araç çubuğunda bir simge olarak duruyor.

---

## Bir çıktı üretmek

10. Referans katmanınızı QGIS'e ekleyin (**Katman > Katman Ekle > Raster Katman Ekle...**).
    Üretilecek alan ve CRS bu katmandan okunur.
11. **Raster > GenCP > GenCP Synthetic Reference...** ile eklentiyi açın.

### 1 - Girdi

12. **Reference layer** açılır listesinden 10. adımdaki katmanı seçin.
13. **Extent**, **CRS** ve **Tiles / estimate** satırlarının dolduğunu görün.
    - **CRS metrik olmalıdır.** Katmanınız EPSG:3857 (Web Mercator) ise burada kırmızı bir
      uyarı çıkar ve düğmeler kapalı kalır. Bu durumda katmanı önce kendi UTM diliminize
      dönüştürün: katmana sağ tıklayın, **Dışa Aktar > Nesneleri Farklı Kaydet...**, CRS
      alanından UTM seçin. Coğrafi CRS'ler (EPSG:4326, EPSG:4258) otomatik olarak UTM'ye
      dönüştürülür, elle bir şey yapmanız gerekmez.
14. **Tile overlap** varsayılan olarak 640 m gelir. İlk denemeniz için **0 m** seçin -
    tek karo üretir ve saniyeler sürer.

### 2 - Veri kaynağı

15. **Local vector file (.osm.pbf)** seçeneğini işaretleyin.
16. **Browse...** ile `.osm.pbf` dosyanızı seçin.
17. **CLC+ Backbone raster** alanına **Browse...** ile CLC+ rasterını seçin.
18. Bu bölümde kırmızı yazı kalmamalı. Kalıyorsa yazıda hangi dosyanın bulunamadığı yazar.

### 3 - Önizleme (bu adımı atlamayın)

19. **Render preview tile** düğmesine basın. Birkaç saniye sürer.
20. Çıkan görüntüye **bakın**. Modelin gireceği rasterleştirilmiş girdi budur.
    Yollar, su ve arazi örtüsü burada yanlışsa üretilen görüntü de aynı şekilde ve
    kendinden emin biçimde yanlış olur.
21. Görüntünün altında sarı bir uyarı kutusu çıkarsa okuyun. En sık çıkanı: seçtiğiniz
    `.osm.pbf` bu alanı kapsamıyor, yani karoda **hiç OSM nesnesi yok**. Sonuç yine de
    üretilir ve boş bir kırsal alan gibi görünür - hata gibi görünmez. Bu durumda alanı
    kapsayan bir `.osm.pbf` seçin.
22. Çok karolu bir alanda **Next tile** ile başka karolara da bakabilirsiniz.
23. Görüntü doğruysa **I have looked at tile ... and the render is correct** kutusunu
    işaretleyin. Bu kutu işaretlenmeden **Generate** düğmesi açılmaz.

### 4 - Model

24. **Browse...** ile `gencp_C3_fp32.onnx` dosyasını seçin.
25. Altında dosya adının, değiştirilme tarihinin ve boyutunun göründüğünü doğrulayın.

### 6 - Çıktı

26. **Write a GeoTIFF to disk** kutusunu işaretli bırakın.
27. **Save as...** ile çıktı dosyasının yolunu ve adını belirleyin (örneğin
    `gencp_reference.tif`).
28. **Add the result to the map as a layer** işaretliyse sonuç bitince otomatik olarak
    haritaya eklenir.

### 5 - Çalıştırma

29. **Generate** düğmesine basın.
30. İlerleme çubuğunu izleyin. Üretim arka planda bir **QgsTask** üzerinde çalışır;
    QGIS bu sırada donmaz, harita gezinilebilir kalır.
31. Vazgeçmek isterseniz **Cancel** düğmesine basın. İş durur ve **yarım bir dosya diske
    yazılmaz**.
32. Bittiğinde alt satırda yazılan dosyanın yolu görünür ve katman haritaya eklenir.

Üretilen GeoTIFF, referans katmanın kuzeybatı köşesine tam oturur, piksel boyu tam
10.0 m'dir ve içinde hangi model ve hangi ayarlarla üretildiğini anlatan bir
`GENCP_PROVENANCE` etiketi taşır.

---

## Süre hakkında

Bölüm 1'de gösterilen süre tahmini karo başına yaklaşık 6 saniyedir ve **toplam** süreyi
kabaca doğru verir. Ancak bu sürenin neredeyse tamamı **Render preview tile** adımında ve
**Generate** sırasındaki rasterleştirmede geçer; modelin kendisi karo başına yarım saniyenin
altındadır. Yani 19. adım beklediğinizden uzun, 29. adım beklediğinizden kısa sürer.

Aynı alanı ikinci kez ürettiğinizde rasterleştirme önbellekten gelir ve iş saniyeler sürer.

---

## `onnxruntime` yoksa ne yapmalı

Model çalıştırılamıyorsa **Generate** sırasında `No module named 'onnxruntime'` benzeri bir
hata görürsünüz. Kütüphaneyi **QGIS'in kendi Python'una** kurmanız gerekir; bilgisayarınızdaki
başka bir Python'a kurmak işe yaramaz.

1. QGIS'te **Eklentiler > Python Konsolu** açın.
2. Şunu yazıp çalıştırın:

   ```python
   import sys; print(sys.executable)
   ```

3. Bir terminal açın ve çıkan yolu kullanarak kurun:

   ```bash
   "<2. adımda yazan yol>" -m pip install onnxruntime
   ```

   macOS'ta bu genellikle şudur:

   ```bash
   /Applications/QGIS.app/Contents/MacOS/bin/python3 -m pip install onnxruntime
   ```

4. **QGIS'i tamamen kapatıp yeniden açın.** Yeniden başlatmadan kütüphane görünmez.
5. Python Konsolu'nda doğrulayın:

   ```python
   import onnxruntime; print(onnxruntime.__version__)
   ```

Yerel `.osm.pbf` dosyası kullanacaksanız `osmium` da aynı şekilde gerekir:

```bash
"<QGIS'in python yolu>" -m pip install osmium
```

**macOS'a özel not.** onnxruntime QGIS uygulamasının içinde çalışır ama paketle gelen
`python3.12` çalıştırılabiliriyle test ederseniz "different Team IDs" hatası alırsınız.
Bu bir kurulum hatası değildir; eklenti QGIS uygulaması içinde sorunsuz çalışır. Test
edecekseniz uygulama ikilisini kullanın.

---

## Bir şey ters giderse

| Belirti | Sebep |
|---|---|
| Eklenti kurulduktan sonra listede yok | 4. adımdaki **Deneysel eklentileri de göster** işaretlenmemiş |
| **Render preview tile** düğmesi kapalı | Bölüm 2'de kırmızı yazı var; CLC+ veya `.osm.pbf` yolu boş ya da dosya yok |
| Bölüm 1'de kırmızı CRS uyarısı | Referans katman metrik olmayan bir CRS'te; 13. adıma bakın |
| **Generate** düğmesi kapalı | 23. adımdaki onay kutusu işaretli değil, ya da model yolu boş, ya da çıktı yolu seçilmemiş |
| Önizlemede sarı uyarı kutusu | `.osm.pbf` bu alanı kapsamıyor; 21. adıma bakın |
| Çıktı boş bir kırsal alan gibi | Aynı sebep - 21. adım |
