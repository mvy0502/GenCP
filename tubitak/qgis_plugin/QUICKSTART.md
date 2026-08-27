# GenCP Sentetik Referans eklentisi - hızlı başlangıç

QGIS kullanmış, ancak bu eklentiyi hiç görmemiş biri için. Yalnızca tıklamalar.
Mimari ve gerekçe için `README.md`, ölçüm kayıtları için
`tubitak/docs/confidence-results.md` ve `tubitak/docs/plugin-field-test.md`.

Doğrulandığı sürüm: **QGIS 4.2.1 (macOS)**. QGIS 3.28 için kod uyumlu yazıldı ama
denenmedi. Arayüz Türkçedir.

---

## Önce indirilecek dosyalar

| Dosya | Nereden | Ne işe yarar |
|---|---|---|
| `gencp_plugin.zip` (48 KB) | https://github.com/mvy0502/gencp-validation/releases/download/plugin-v0.2.0/gencp_plugin.zip | Eklentinin kendisi |
| `gencp_C2_fp32.onnx` (208 MB) | Doğrudan proje sahibinden isteyin | Üretici model ağırlıkları |


Sürüm sayfası: https://github.com/mvy0502/gencp-validation/releases/tag/plugin-v0.2.0

Model dosyası neden bağlantıyla verilmiyor: ağırlıklar GenCP'nin CC-BY 4.0
ağırlıklarından türedi, ancak ince ayar girdileri ODbL lisanslı OpenStreetMap verisinden
üretildi. ODbL'nin share-alike yükümlülüğünün bu ağırlıklara uzanıp uzanmadığı belirsiz
olduğu için dosyalar kurum içi doğrudan aktarımla veriliyor.
Ayrıntı: `tubitak/docs/evidence/BACKUP.md`.

Ayrıca elinizde bulunması gerekenler:

- **CLC+ Backbone 2021 rasterı** (`CLMS_CLCplus_RASTER_2021_010m_eu_03035_V1_1.tif`,
  8.2 GB) - Copernicus Land Monitoring Service'ten indirilir.
- **Bir `.osm.pbf` dosyası** (örneğin Geofabrik'ten `turkey-latest.osm.pbf`) - çalışacağınız
  alanı kapsamalı. Alternatif olarak **Çevrimiçi (Overpass)** seçeneği kullanılabilir.
- **Bir referans katman** - üretilecek görüntünün kapsamını ve KRS'sini bu katman belirler.

---

## Kurulum

1. QGIS'i açın.
2. **Eklentiler > Eklentileri Yönet ve Kur...** seçin.
3. Soldaki listeden **Ayarlar** sekmesine geçin.
4. **Deneysel eklentileri de göster** kutusunu işaretleyin.
   Bu adım atlanamaz: eklenti `experimental=True` olarak işaretli olduğu için bu kutu
   işaretli değilse kurulduktan sonra listede görünmez.
5. Soldaki listeden **ZIP'ten Kur** sekmesine geçin.
6. **...** düğmesiyle `gencp_plugin.zip` dosyasını seçin.
7. **Eklentiyi Kur** düğmesine basın.
8. **Kurulu** sekmesinde **GenCP Synthetic Reference** satırının işaretli olduğunu
   doğrulayın.
9. Pencereyi kapatın. Eklenti artık **Raster > GenCP > GenCP Synthetic Reference...**
   menüsünde ve araç çubuğunda.

---

## Bir çıktı üretmek

10. Referans katmanınızı QGIS'e ekleyin (**Katman > Katman Ekle > Raster Katman Ekle...**).
11. **Raster > GenCP > GenCP Synthetic Reference...** ile eklentiyi açın.

### 1 · Girdi

12. **Referans katman** listesinden 10. adımdaki katmanı seçin.
13. **Kapsam**, **KRS** ve **Karo / süre tahmini** satırlarının dolduğunu görün.
    - **KRS metrik olmalıdır.** Katmanınız EPSG:3857 (Web Mercator) ise burada kırmızı bir
      uyarı çıkar ve düğmeler kapalı kalır; uyarı ne yapmanız gerektiğini yazar. Katmanı
      kendi UTM diliminize dönüştürün: katmana sağ tıklayın, **Dışa Aktar > Nesneleri
      Farklı Kaydet...**, KRS alanından UTM seçin. Coğrafi KRS'ler (EPSG:4326, EPSG:4258)
      otomatik olarak UTM'ye dönüştürülür.
14. **Karo bindirmesi** varsayılan 640 m'dir. İlk denemeniz için **0 m** seçin - tek karo
    üretir ve saniyeler sürer.

### 2 · Veri kaynağı

15. **Yerel vektör dosyası (.osm.pbf)** seçeneğini işaretleyin.
16. **Gelişmiş - dosya yolları** başlığına tıklayarak açın.
17. **OSM çıkarımı** ve **CLC+ Backbone rasterı** alanlarını **Gözat…** ile doldurun.
18. Kırmızı yazı kalmamalı; kalıyorsa hangi dosyanın bulunamadığını ve ne yapmanız
    gerektiğini yazar.

**Bir sonraki açılışta bu yolları yeniden seçmeniz gerekmez.** Eklenti son kullandığınız
CLC+, model ve çıktı klasörü yollarını hatırlar ve **Gelişmiş** bölümünü kapalı açar.

### 3 · Önizleme (bu adımı atlamayın)

19. **Önizleme karosunu oluştur** düğmesine basın. Birkaç saniye sürer.
20. Çıkan görüntüye **bakın**. Modelin gireceği rasterleştirilmiş girdi budur. Yollar, su
    ve arazi örtüsü burada yanlışsa üretilen görüntü de aynı şekilde ve kendinden emin
    biçimde yanlış olur.
21. Görüntünün sağındaki **Bu karodaki OSM içeriği** tablosuna bakın: yollar, binalar, su
    ve arazi kullanımı için kaç piksel olduğunu ve toplam yüzdeyi verir. Sayılar çok
    düşükse çıktı büyük ölçüde arazi örtüsünden türetilecektir.
22. Onay kutusunun üstündeki kutuyu okuyun. Bu karonun hangi güven bandında olduğunu
    yazar - kırmızı, turuncu ya da yeşil - ve bu, üretilecek güven katmanının kullandığı
    ölçünün aynısıdır; ikisi çelişemez. Ayrıca seçtiğiniz `.osm.pbf` bu alanı kapsamıyorsa
    "hiç OSM nesnesi yok" uyarısı çıkar: sonuç yine üretilir ve boş bir kırsal alan gibi
    görünür, hata gibi görünmez. Uyarı, onay kutusuyla aynı çerçevenin içindedir.
23. Çok karolu bir alanda **Sonraki karo** ile başka karolara da bakabilirsiniz.
24. Görüntü doğruysa **... numaralı karoya baktım ..., görüntü doğru** kutusunu
    işaretleyin. Bu kutu işaretlenmeden **Üret** düğmesi açılmaz.

### 4 · Model

25. **Gözat…** ile `gencp_C2_fp32.onnx` dosyasını seçin.
26. Altında dosya adının, değiştirilme tarihinin ve boyutunun göründüğünü doğrulayın.

### 5 · Çıktı

27. **Diske GeoTIFF yaz** kutusunu işaretli bırakın.
28. **Farklı kaydet…** ile çıktı yolunu belirleyin (örneğin `gencp_reference.tif`).
29. **Sonucu haritaya katman olarak ekle** işaretliyse sonuç bitince haritaya eklenir.
30. **Güven katmanı da üret** kutusu varsayılan olarak işaretlidir. Bkz. aşağıdaki bölüm.
    Bu katman girdiden hesaplanır; ek bir model çalıştırmaz ve kayda değer bir süre eklemez.

### 6 · Çalıştırma

31. **Üret** düğmesine basın. Bu düğme her zaman pencerenin altında görünür; kaydırmanız
    gerekmez.
32. İlerleme çubuğunun altındaki satır hangi adımda olduğunuzu yazar:
    *Rasterleştiriliyor*, *Üretiliyor*, *Güven haritası hesaplanıyor*, *Birleştiriliyor*.
    Üretim arka planda bir **QgsTask** üzerinde çalışır; QGIS donmaz.
33. Vazgeçmek isterseniz **Vazgeç** düğmesine basın. İş durur ve **yarım bir dosya diske
    yazılmaz**.
34. Bittiğinde yazılan dosyanın adı görünür ve katmanlar haritaya eklenir.

Üretilen GeoTIFF, referans katmanın kuzeybatı köşesine tam oturur, piksel boyu tam
10.0 m'dir ve içinde hangi model ve hangi ayarlarla üretildiğini anlatan bir
`GENCP_PROVENANCE` etiketi taşır.

---

## Güven katmanı

İkinci bir katman üretilir: `<çıktı adı>_confidence.tif`. Her piksel için tek bir soruyu
yanıtlar: **çıktı burada girdi bilgisine mi dayanıyor, yoksa uydurma mı?**

Üç bant, otomatik olarak renklendirilir - sembolojiyi elle ayarlamanız gerekmez:

| Bant | Anlamı | Ayrık ölçümde o bandın hata ortancası |
|---|---|---|
| **Kırmızı - kullanmayın** | Çıktı burada büyük ölçüde uydurma | 3,31 piksel |
| **Turuncu - dikkatli kullanın** | Girdi zayıf; başka bir kaynakla karşılaştırın | 2,63 piksel |
| **Yeşil - kullanılabilir** | Çıktı burada girdi bilgisine dayanıyor | 1,33 piksel |

5. bölümde ayrıca bütün çalışma için tek satırlık bir değerlendirme çıkar: her bandın
yüzdesi ve çalışmanın ortalama bandı. Kırmızı %20'yi aşarsa ayrıca uyarı verir.

**Bilmeniz gereken dört sınır:**

1. **Bantlar yalnızca `gencp_C2_fp32.onnx` için ölçüldü.** Başka bir model seçerseniz
   4. bölümde uyarı çıkar ve eklenti güven katmanını **üretmez**. Doğrulanmamış bir model
   için bant göstermek, olmayan bir ölçümü uydurmak olurdu. Model dosyası adına göre
   değil, SHA-256 özetine göre denetlenir.
2. **Skor girdiden hesaplanır.** Model çalıştırılmaz; katman, rasterleştirilmiş girdinin
   yerel sınıf çeşitliliğinden gelir. Bu yüzden 3. bölümdeki önizleme uyarısı ile üretilen
   katman aynı sayıyı kullanır ve birbiriyle çelişemez.
3. **Ölçünün gücü.** 150 ayrık Avrupa karosunda Spearman rho **-0,76**, 130 Ankara
   karosunda **-0,77**; KARIOS'un eşleştirdiği nokta sayısı sabit tutulduğunda sırasıyla
   **-0,38** ve **-0,29**. Yani ilişkinin bir bölümü nokta sayısı üzerinden gidiyor.
   En düşük güvenli %50 atıldığında Avrupa'da hata ortancası 1,98 pikselden 1,30 piksele
   iner.
4. **Bir karoda hiç OSM nesnesi olmasa bile bant yeşil çıkabilir**, çünkü skor arazi
   örtüsü çeşitliliğini de sayar. Bu yüzden "hiç OSM nesnesi yok" uyarısı bandan bağımsız
   olarak ayrıca gösterilir.

---

## Süre hakkında

1. bölümdeki tahmin karo başına yaklaşık 6 saniyedir ve **toplam** süreyi kabaca doğru
verir. Ancak bu sürenin neredeyse tamamı rasterleştirmede geçer; modelin kendisi karo
başına yarım saniyenin altındadır. Yani 19. adım beklediğinizden uzun, 31. adım
beklediğinizden kısa sürer. Aynı alanı ikinci kez ürettiğinizde rasterleştirme
önbellekten gelir ve iş saniyeler sürer.

---

## `onnxruntime` yoksa ne yapmalı

**Üret** sırasında `No module named 'onnxruntime'` benzeri bir hata görürsünüz. Kütüphaneyi
**QGIS'in kendi Python'una** kurmanız gerekir; başka bir Python'a kurmak işe yaramaz.

1. QGIS'te **Eklentiler > Python Konsolu** açın.
2. Şunu çalıştırın:

   ```python
   import sys; print(sys.executable)
   ```

3. Bir terminal açın ve çıkan yolu kullanarak kurun:

   ```bash
   "<2. adımda yazan yol>" -m pip install onnxruntime
   ```

   macOS'ta genellikle:

   ```bash
   /Applications/QGIS.app/Contents/MacOS/bin/python3 -m pip install onnxruntime
   ```

4. **QGIS'i tamamen kapatıp yeniden açın.** Yeniden başlatmadan kütüphane görünmez.
5. Python Konsolu'nda doğrulayın:

   ```python
   import onnxruntime; print(onnxruntime.__version__)
   ```

Yerel `.osm.pbf` kullanacaksanız `osmium` da aynı şekilde gerekir:

```bash
"<QGIS'in python yolu>" -m pip install osmium
```

**macOS'a özel not.** onnxruntime QGIS uygulamasının içinde çalışır ama paketle gelen
`python3.12` çalıştırılabiliriyle test ederseniz "different Team IDs" hatası alırsınız.
Bu bir kurulum hatası değildir; eklenti QGIS uygulaması içinde sorunsuz çalışır.

---

## Bir şey ters giderse

| Belirti | Sebep |
|---|---|
| Eklenti kurulduktan sonra listede yok | 4. adımdaki **Deneysel eklentileri de göster** işaretlenmemiş |
| **Önizleme karosunu oluştur** kapalı | 2. bölümde kırmızı yazı var; CLC+ veya `.osm.pbf` yolu boş ya da dosya yok |
| 1. bölümde kırmızı KRS uyarısı | Referans katman metrik olmayan bir KRS'te; 13. adıma bakın |
| **Üret** düğmesi kapalı | 6. bölümün alt satırı sıradaki tek eksiği yazar: katman, kaynak, model, çıktı yolu ya da 24. adımdaki onay |
| Önizlemede sarı uyarı | `.osm.pbf` bu alanı kapsamıyor; 22. adıma bakın |
| Çıktı boş bir kırsal alan gibi | Aynı sebep - 22. adım |
| Güven katmanı üretilmedi | 4. bölümdeki uyarı sebebini yazar: seçtiğiniz model bantların ölçüldüğü model değil |
