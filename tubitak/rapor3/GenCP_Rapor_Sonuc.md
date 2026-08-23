# GenCP — Sonuç Raporu
## OpenStreetMap'ten üretilen sentetik referans görüntülerin Georef'te kullanılabilirliği

**23 Ağustos 2026 · Vedat Yıldırım**
Kod ve tüm ölçüm kayıtları: **github.com/mvy0502/GenCP** (`tubitak-tr` dalı, `tubitak/` klasörü)

---

## 1. Cevap

Soru, TÜBİTAK'ın Georef'te OSM türevli sentetik referans kullanıp kullanamayacağıydı.

**Ölçtüğüm cevap: gerçek 10 m görüntü bulunabilen her yerde gerçek görüntü kullanılmalı. Türkiye'de bu, pratikte her yer anlamına geliyor.** Yedi bölgeye yayılmış, kıyı/iç ve kentsel/kırsal olarak dengelenmiş 24 alan örnekledim. **24 alanın 24'ünde** son 90 gün içinde bulut oranı %10'un altında bir Sentinel-2 sahnesi vardı; son bulutsuz sahneden bu yana geçen sürenin medyanı **2 gün**, en kötü alanda **17 gündü**. EOX bulutsuz mozaik ise 24 alanın tamamını kapsıyordu.

Sentetik referansın iddiası hiçbir zaman "daha doğru" değildi; "her zaman, her yerde, bulutsuz elde edilebilir" idi. Bu iddia Türkiye'de 10 m çözünürlükte bir ayırt edici özellik değil.

![](gorseller/f2-erisilebilirlik.png)

*24 alanın hiçbiri 90 gün eşiğine yaklaşmıyor. Karar: sentetik referansı "erişilebilirlik" gerekçesiyle tercih etmek için ölçülmüş bir dayanak yok.*

---

## 2. Karşılaştırma — iki sayı birlikte

Yer doğruluğunu üretmek için gerçek bir Sentinel-2 sahnesine **bilinen bir kaydırma** uyguladım ve her aday referanstan bu kaydırmayı geri kazanmasını istedim. Doğruluk tanım gereği kesin. Eğitim verisiyle örtüşmeyen temiz bir sahada (Kapadokya, 36SXJ) ölçtüm.

![](gorseller/f1-karsilastirma.png)

**Solda 10 m hedef görüntü:** gerçek kaynaklar 1 piksellik kaydırmayı 0,017–0,034 piksel hatayla geri kazanıyor, bizim referansımız 0,541 piksel hatayla. Aradaki fark yaklaşık **on altı kat**.

**Sağda 0,46 m hedef görüntü** — Georef'in fiilen çalıştığı kip, çünkü 10 m referansı hedef görüntünün çözünürlüğüne yükseltiyor: EOX 2,06 m, gerçek Sentinel-2 2,32 m, GenCP 2,38 m. Buradaki fark yaklaşık **%15**.

İki sayının birlikte verilmesi şart. Yalnızca soldaki verilirse ürünün aleyhine olan tablo abartılmış olur; yalnızca sağdaki verilirse hafifletilmiş olur.

Sağdaki panelin asıl mesajı sıralama değil, büyüklük: **her üç adayın hatası da uygulanan kaydırmayla aynı mertebede.** 0,46 m hedefte 10 m'lik bir referans, kaynağı ne olursa olsun birkaç metrenin altındaki kaymayı geri kazanamıyor. Pratik cümle şu: **metre-altı hedeflerde 10 m referanstan metre mertebesinde artık hata bekleyin — bu bir çözünürlük sorunu, kaynak seçimi sorunu değil.**

Bir sınır: bu ölçümler KLT eşleştiricisiyle yapıldı. Georef'in kendi eşleştirme stratejisini çalıştıramadık; buradaki her sayı o anlamda bir vekil ölçüdür.

---

## 3. Test edilip kapanan iki gerekçe

Sentetik referans için geriye kalan iki argümanı da ölçtüm; ikisi de ayakta kalmadı.

**Erişilebilirlik** — bölüm 1'deki sayılar.

**Güncellik.** Bizim referansımız bugünün OSM'inden üretiliyor; gerçek görüntü ise bir tarihe ait. Değişimin çok olduğu bir alanda (İstanbul kuzey gelişim koridoru, eğitim verisinde bulunmayan bir karo) 2026 hedefine karşı **2021 tarihli** bir Sentinel-2 sahnesini bizim güncel-OSM referansımızla yarıştırdım: ortalama geri kazanım hatası 2021 sahnesinde 0,057 piksel, bizim referansımızda 0,120 piksel. Kritik olan etkileşimdi — avantajın "en çok değişen karolarda" ortaya çıkıp çıkmadığı. **Çıkmadı**: en çok değişen ve en az değişen karolar arasındaki fark 0,008 ± 0,031 piksel, yani sıfırdan ayırt edilemiyor. Beş yıllık eski bir görüntü, en çok değişmiş alanlarda bile bizim güncel referansımızı yeniyor.

Dürüst bir not: **OSM'in kendi gecikmesi de aynı ölçüde geçerli bir açıklama.** Değişimi OSM henüz işlememiş olabilir. Bu ikisini ayırmak OSM düzenleme geçmişi analizi gerektiriyordu, yapmadım.

---

## 4. Sonuçtan bağımsız olarak teslim edilenler

**GenCP hattında sistematik bir geometri hatası bulup düzelttim.** Üretim betiği 257 pikselik girdinin koordinat bilgisini 256 pikselik çıktıya değiştirmeden kopyalıyor. Gerçek piksel boyutu 10,0390625 m iken dosyada 10,0 m yazıyor: tam olarak 1/256, yani **+%0,39**; chip köşesinde **14 m**'ye ulaşıyor. Dört bağımsız yöntemle doğruladım. **Bu hata GenCP'yi çalıştıran herkesi ilgilendiriyor.**

**Çalışan bir araç.** Sınır kutusu girdi → georeferanslı 10 m referans çıktı. Deterministik ve bit düzeyinde tekrarlanabilir; her dosyanın içine tam köken kaydı gömülü (model, checkpoint özeti, OSM anlık görüntüsü, kod sürümü). Yanında bir **güvenilirlik katmanı**: alanları sıralıyor, en iyi %75'i tutulduğunda teslim edilen doğruluk Ankara'da 0,21 piksel, Kapadokya'da 0,42 piksel iyileşiyor — karşılığında kapsamanın %25'inden vazgeçiliyor.

**ODTÜ paketi** teslime hazır: referans GeoTIFF, güvenilirlik katmanı, köken dosyası ve alıcı için yazılmış bir README.

![](gorseller/f4-odtu.png)

*Soldan sağa: OSM+CLC+ girdisi, üretilen referans, gerçek Sentinel-2. Karar: teslim edilen ürünün ne olduğunu gösterir; yol ağı ve kentsel doku takip ediliyor, doku gerçek görüntüden daha yumuşak.*

**Karşılaştırma yönteminin kendisi.** Enstitünün bu karşılaştırmayı yapmayı planladığını söylemiştiniz; bilinen-kaydırma yöntemi ve kodu depoda, doğrudan çalıştırılabilir durumda.

---

## 5. Tek olumlu bulgu ve neden bundan sonrası için önemli

**Referans görüntü üretiminde çekişmeli (adversarial) kayıp ölçülebilir bir yüktür.**

Girdinin bilgi taşımadığı yerlerde model yapı uyduruyor; uydurulmuş bir kenar ise hatalı bir yer kontrol noktası demek. Bunu dolaylı değil doğrudan ölçtüm: girdinin sessiz olduğu bölgelerde üretilen görüntünün kenar yoğunluğunu gerçek görüntününkine oranladım.

![](gorseller/f3-uydurma.png)

*Ön-eğitimli 1,016 ve GAN+L1 1,023 — ikisi de girdide karşılığı olmayan alanları gerçek görüntü yoğunluğunda dokuyla dolduruyor. Yalnız-L1 0,218. Karar: VHR'de bir referans üreteci kurulacaksa çekişmeli terim baştan dışarıda bırakılmalı.*

Çekişmeli terimi kaldırmak medyan konum hatasını **%64 iyileştirdi** (2,588 → 0,929 piksel; Georef'in tüketeceği tek bantlı eşleştirmede kentsel chip'lerde 0,593 piksel). Bulgu dört alternatif açıklamayı (soğuk ayrıştırıcı, bulanıklık, koordinat düzeltmesi, "ölçtüğümüz metriğe göre eğitildi") ve dört farklı eşleştirici ailesini aştı.

**Öneri — sonuç değil, öneri olarak.** GenCP'nin varsayımı referans görüntülerin telifle kısıtlı olmasıdır. 10 m'de böyle bir kısıt yok: Sentinel-2 ve EOX ücretsiz. Yöntemin burada karşılığını vermemesinin sebebi budur. Kısıt **VHR'de** gerçekten var. Enstitü o çözünürlükte bir referans üreteci kurar veya ihale ederse, bu bulgu doğrudan ve **para harcanmadan önce** uygulanır.

---

## 6. Sırada

Sentinel-2 süper-çözünürlük: 10 m → 5 m, hedef 2,5 m. Bu, ayrı bir iş değil bölüm 2'nin doğrudan devamı — ölçüm, bağlayıcı kısıtın referansın çözünürlüğü olduğunu gösterdi; dolayısıyla atılacak adım kaynağı değiştirmek değil, çözünürlüğü yükseltmek.

---

**Rapor 1'deki iki sayının düzeltmesi.** Eski değerlerle çalışmamanız için: yoğunluk–hata korelasyonu için verdiğim **ρ = −0,79**, kontrolsüz erken bir yerel ölçüydü; nokta sayısı kontrol edildiğinde **−0,61**. Ayrıca "model Anadolu'ya genelleniyor, ölçülebilir coğrafi ceza yok" ifadesi taban çizgisine bağımlıydı: daha iyi desteklenen bir taban çizgisine karşı ceza **+0,226 piksel**, en yoğun girdi katmanında ise **+0,038 piksele** düşüyor. Kayıtların tamamı depodaki düzeltme günlüğünde.
