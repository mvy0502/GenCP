# GenCP — İlerleme Raporu 2

**OpenStreetMap verisinden sentetik uydu görüntüsü üretimi · 20 Ağustos 2026**

Rapor 1'de hazır olduğunu bildirdiğim üretim ve doğrulama altyapısını Türkiye sahasında uçtan
uca çalıştırdım. Ankara üzerinde 130 chip üretip ölçtüm; ardından modeli Türkiye verisiyle iki
ayrı reçeteyle ince ayara tabi tuttum ve sonucu üç bağımsız genelleme testinden geçirdim. Bu
raporun tamamı, Rapor 1'de tanıttığım disiplinin sonucudur: her sayı, ölçümden **önce** kod
deposuna işlenmiş yazılı tahminlere karşı puanlandı. Tutan tahminler kadar tutmayanlar da bu
raporda; güvenilirliğin kaynağı tam olarak bu.

> **Öne çıkan bulgu.** Ön-eğitimli model, girdi zenginliği eşitlendiğinde Ankara'nın yoğun
> katmanlarında Avrupa'dan ayırt edilemiyor; sahanın genelindeki ceza ılımlı (+0.226 px) ve
> kayıtlı "coğrafya önemli" eşiğinin çok altında. Türkiye verisiyle yalnız-L1 ince ayar (C2),
> medyan konum hatasını **2.588 → 0.929 piksele** düşürdü (%64 iyileşme). Bu kazanımın
> **~%95'i** sahne değişimine dayanıklı (Kapadokya taşınma oranı R = 0.945) ve Avrupa
> performansında hiçbir kayıp yok — aksine orada da −0.364 px iyileşme ölçüldü. Rapor 1'in
> "girdide olmayan yapı üretme" bulgusunun pratik çözümü, mimari değişiklik değil, kayıp
> fonksiyonu değişikliği çıktı.

| Alan | Durum | Not |
|---|---|---|
| Kendi rasterleştiricimiz | Tamam | Held-out kalite kapısı +0.012 px ile geçti; Geofabrik şeffaflık kapısı %99.91 |
| Türkiye ilk üretim (Ankara) | Tamam | 130 chip; beş kayıtlı tahmine (T1–T5) karşı puanlandı |
| İnce ayar deneyi (Faz C) | Tamam | Üç kol; kazanan C2: 2.588 → 0.929 px |
| Genelleme testleri (Avrupa + Faz D) | Tamam | Kazanımın ~%95'i gerçek adaptasyon; Avrupa'da unutma yok |
| C3 (AB karışımlı ince ayar) | Hazır, beklemede | GPU kotası 22 Ağustos 00:00 UTC'de yenilenince koşacak |

## 1. Kendi rasterleştiricimiz ve kalite kapıları

Rapor 1'in birinci sonraki adımı, OSM rasterlerini kendi hattımızla üretip referans veriyle
karşılaştırmaktı. Bunu tamamladım: OSM vektör verisini ve CLC+ Backbone 2021 arazi örtüsü taban
katmanını birleştiren bir rasterleştirici kurdum ve her aşamasını sayısal kapılardan geçirdim.

Taban katmanı seçimi kendi başına bir bulgu oldu. İlk denediğim ESA WorldCover 10 m ürünü,
referans rasterlerin su sınıfını sistematik olarak kaçırıyordu; sınıf paletini birebir
eşleştirince özgün korpusun taban ürününün **CLC+ Backbone 2021** olduğunu tespit ettim. CLC+
katmanı geldiğinde iki ürünü aynı chip'ler üzerinde yarıştırdım: CLC+ tabanı WorldCover'a göre
−0.205 ± 0.052 px daha iyi (t = −3.96) ve su geri çağırması %25.1'den %82.0'ye çıktı. Nihai
kabul, hiçbir ayarın dokunmadığı **25 chip'lik held-out kapıda** ölçüldü:

> Kendi render'ımız − referans raster = **+0.0120 ± 0.1319 px (t = 0.09)** — istatistiksel sıfır.
> Kendi hattımız, korpusun kendi rasterleriyle ölçülebilir fark üretmiyor. **KAPI GEÇİLDİ.**

Veri kaynağını Overpass API'den yerel Geofabrik arşivlerine taşırken de aynı disiplini
uyguladım: geçiş, "aynı sonucu veriyor" varsayımıyla değil, bayt düzeyinde bir **şeffaflık
kapısıyla** kabul edildi. Bu kapı gerçek bir hata yakaladı: osmium aracının varsayılan `simple`
çıkarma stratejisi, chip sınırını aşan multipolygon'ları sessizce düşürüyor (en kötü chip'te
piksellerin %84'ü yanlış sınıfa, baskın akış 3:1 oranında orman→arkaplan). `-s smart`
stratejisine geçip kapıyı yeniden koştum: **geometri 28/28 özdeş, piksellerin %99.79'u
bayt-özdeş, sınıf uyumu %99.91** (en kötü chip %99.23). Kapı olmasaydı bu hata eğitim verisine
sessizce taşınacaktı.

## 2. Türkiye ilk üretimi — Ankara, kayıtlı tahminlere karşı

Rapor 1'de "hedef saha kararı bekleniyor" durumundaydık; saha **Ankara** (Sentinel-2 tile'ı
36TVK, 2026-04-30 sahnesi, %2.04 bulut) olarak belirlendi. 1564 geçerli chip adayından, CLC+
bilgi yoğunluğuna göre beş katmandan (Q1 en seyrek … Q5 en yoğun) 26'şar chip seçip 130 chip
ürettim ve KARIOS ile ölçtüm — 130/130 chip puan aldı.

Ölçümden önce iki tahmin kaydı işledim (v1 08:43 UTC, girdi ölçüsü düzeltilmiş v2 09:05 UTC —
her ikisi de ilk Türk chip'i üretilmeden önce). Beş kayıtlı kalemin sonucu:

| Kalem | Önceden kayıt | Ölçüm | Hüküm |
|---|---|---|---|
| T1 Ankara medyanı | 2.85 ± 1.08 px | 2.588 px | **TUTTU** |
| T2 katman bazında | 3.24 / 3.04 / 2.85 / 2.57 / 2.02 | 3.48 / 3.11 / 2.49 / 2.08 / 1.24 | **TUTTU** (aralıklar içinde; yoğun uçta Türkiye tahminden iyi) |
| T3 yalnız-yoğunluk farkı | +0.80 px | ≈ +0.78 px | **TUTTU**, neredeyse birebir |
| T4 coğrafya önemli ⇔ eşleşmiş fark > +0.5 px | — | eski 44-chip tabanda **−0.247 px**; 568-chip tabanda **+0.226 px** (Q4 +0.174, Q5 +0.038) | **Tetiklenmedi** — yoğun katmanlarda ceza yok; başlık düzeltmesi için bkz. §7 kayıt 11 |
| T5 yoğunluk açıklaması yanlışlanır ⇔ eşleşmiş ≈ ham veya \|ρ\| < 0.3 | — | Türkiye ρ = **−0.727** (Avrupa −0.675) | **Yanlışlanmadı — mekanizma aynı güçte** |

Naif bir karşılaştırma "Türkiye Avrupa'dan +0.536 px (%26) kötü" derdi. Ayrıştırma bu farkın
büyük bölümünün **girdi yoğunluğu** olduğunu gösteriyor. Eşleşmiş farkın kendisi ise taban
çizgisine duyarlı çıktı ve bunu açıkça raporluyorum: ilk analizin 44 chip'lik eski Avrupa taban
çizgisine karşı verdiği değer −0.247 px idi ("Türkiye hafifçe daha iyi"); tüm sahaları **tek ve
çok daha iyi desteklenen 568 chip'lik taban çizgisine** karşı yeniden puanlayan doğrulama,
Ankara'yı **+0.226 px'e** koyuyor (katman bazında Q1 +0.260 / Q2 +0.285 / Q3 +0.375 /
Q4 +0.174 / Q5 +0.038) — ölçülebilir ama ılımlı bir ceza. Kayıtlı T4 ölçütü (yoğun katmanlarda
> +0.5 px) her iki taban çizgisinde de tetiklenmiyor: yoğun uçta ceza fiilen sıfır, ceza
seyrek/orta katmanlarda toplanıyor. Rapor 1'in ana bulgusu Türkiye'de aynen geçerli:
yoğunluk-hata ilişkisi Avrupa'da ρ = −0.675, Türkiye'de ρ = −0.727.

![Ankara ilk üretim panelleri](gorseller/ankara-ilk-uretim.png)

*Her katmanın en seyrek chip'i ve en yoğun chip: solda girdi (OSM+CLC+ render), ortada üretilen
görüntü, sağda gerçek Sentinel-2. Q1'de model, neredeyse boş girdiden gerçekte var olmayan bir
parsel mozaiği uyduruyor — Rapor 1'de Avrupa'da ölçtüğüm davranış Türkiye'ye aynen taşınmış.
Q2 örneğindeki beyaz erozyon arazisi (badlands), Avrupa korpusunda bulunmayan bir yer şekli
olarak görünür biçimde başarısız. En altta yoğun kentsel Ankara: yol ağı ve blok dokusu gerçek
şehri yakından izliyor (1.11 px, 163 nokta) — modelin en iyi hali.*

Üç dürüst sınırlama: (i) eşleşmiş karşılaştırma 130 chip'in 104'ünü kapsıyor — Q1'in o
seyreklikte Avrupa karşılığı yok, ham sayısı (3.480 px) ayrıştırılamadan raporlanıyor;
(ii) Ankara sahnesi kalite gözetilerek seçildi, Avrupa referans görüntüleri ise heterojen —
iddia "en az yoğunluk-eşleşmiş Avrupa kadar iyi" biçiminde okunmalı; (iii) Q2'nin eşleşmiş taban
çizgisi yalnızca 6 Avrupa chip'ine dayanıyor, kırılgan.

## 3. Faz C — Türkiye verisiyle ince ayar (Kaggle)

Rapor 1'deki tespit — girdide karşılığı olmayan her kenar hatalı bir yer kontrol noktasıdır —
bir müdahale hipotezi doğurdu: uydurulan yüksek frekanslı yapı, çekişmeli (adversarial) kaybın
ürünüyse, o kaybı kaldırmak uydurmayı da kaldırmalı. Bunu, hiçbir eğitim koşusu başlamadan önce
kaydettiğim bir deney tasarımıyla sınadım (09:29 UTC): **C1** = GAN+L1 (özgün reçete), **C2** =
yalnız L1, ikisi de yalnız Türkiye çiftleriyle; **C3** = kazanan kol + AB karışımı, sıralı olarak
sonra. Kayıtlı tahmin R1: *"C2 artıkta 0.15–0.40 px farkla kazanır; C1 nokta sayısında ve
görünümde kazanır."*

Eğitim Kaggle'ın ücretsiz 2×T4 GPU'sunda koştu: kol başına 20 epoch (~75 dk), 5577 Türkiye
çifti, seed 42, yayınlanmış üreteç ağırlıklarından başlatma. C1'in gerektirdiği ayrıştırıcı
hiç yayınlanmadığı için soğuk başlangıçlı bir D kurdum (2.770.500 parametre; sha256 ve üretim
kaydı provenance dosyasında). Değerlendirme disiplini sonuç görülmeden sabitlendi: **yalnız
epoch 20** (`latest` ile `20_net_G` tensör tensör özdeşliği iki kolda da doğrulandı; 54.414 M
parametre), diğer 19 checkpoint yalnızca betimleyici.

![Eğitim seyri](gorseller/egitim-kaybi.png)

*İki kolun G_L1 kaybının epoch ortalaması. Soğuk başlangıçlı ayrıştırıcının bilinen riski olan
erken üreteç bozulması gerçekleşmedi: C1 32.8–34.3 bandında düz, sıçrama yok; C2 düzenli iniyor.
Kayıtlı durdurma kuralı hiçbir koşuda tetiklenmedi.*

Sonuçlar, 130 chip'lik aynı Ankara değerlendirme setinde:

| Katman | Ön-eğitimli | C1 (GAN+L1) | C2 (yalnız L1) |
|---|---|---|---|
| Q1 | 3.480 px / 37 nokta | 3.532 / 38 | **2.649 / 43** |
| Q2 | 3.106 / 38 | 2.720 / 47 | **1.452 / 56** |
| Q3 | 2.492 / 52 | 2.019 / 62 | **0.983 / 76** |
| Q4 | 2.084 / 56 | 1.483 / 73 | **0.711 / 108** |
| Q5 | 1.240 / 91 | 0.712 / 120 | **0.552 / 194** |
| **TÜMÜ** | **2.588 / 51** | **1.869 / 61** | **0.929 / 75** |

Eşleştirilmiş (chip bazında) farklar: C1 − ön-eğitimli **−0.530 ± 0.070 px** (t = −7.6, 130
chip'in 32'si kötüleşti); C2 − ön-eğitimli **−1.167 ± 0.074 px** (t = −15.9, 8/130 kötüleşti);
C2 − C1 **−0.638 ± 0.054 px** (t = −11.9, 9/130), medyan −0.524 px.

![Üç kol katman grafiği](gorseller/uc-kol-katman.png)

*Üç kolun katman bazında medyan artığı. C2 her katmanda hem ön-eğitimliyi hem C1'i geçiyor;
en büyük mutlak kazanç orta katmanlarda.*

![Nokta sayısı grafiği](gorseller/nokta-sayisi.png)

*Chip başına hayatta kalan eşleştirme noktası. Kayıtlı beklenti "C2 nokta kaybeder, kalanlar
dürüst olur" idi; tersi çıktı — C2 her katmanda en çok noktayı üretiyor (Q5'te 194'e karşı 91).*

Kayıtlı tahminlerin puanlaması, olduğu gibi:

| Kalem | Önceden kayıt | Ölçüm | Hüküm |
|---|---|---|---|
| R1 kazanan | C2, 0.15–0.40 px farkla | C2, eşleştirilmiş medyan 0.524 px | Kazanan **DOĞRU**; marj bandı **AŞILDI** (~1.5×); "C1 nokta sayısında kazanır" yarısı **YANLIŞLANDI** — C2 noktada da kazandı (13.334'e karşı 9.813) |
| R2 iyileşme nerede | İyileşme yoğunlukla pozitif korelasyonlu (ρ ≥ +0.3); Q1 iyileşmez | C1: ρ = +0.232 [%95 GA +0.065, +0.385], Q1 −0.078 ± 0.171 (sıfır). C2: ρ = +0.032 [−0.161, +0.224], Q1 **−0.843 ± 0.220** | **İki kayıtlı iddianın tutarsızlığı** olarak puanlandı — aşağıda |
| R3 L1 hipotezi yanlışlanır | C1 ≥ 0.15 px önde, veya C2 noktaları C1'in %50 altına düşer | C2 −0.638 px önde; noktaları C1'in %29 **üstünde** | Tetiklenmedi; ikinci koşulun işareti ters çıktı |
| R4 ince ayar değmez | Hiçbir kol +0.15 px'i geçemez, veya Q5 bozulur | İki kol da geniş farkla geçti; Q5 iki kolda da iyileşti | Tetiklenmedi — **ince ayar bu kanıtla değer** |

R2'nin hikâyesi bu raporun metodolojik dersi. R1, C2'nin kazanacağını *uydurma çekişmeli kaybın
ürünüdür* diye öngörmüştü; R2 ise ince ayarın *uydurmayı değil, Anadolu-görünümlü uydurmayı*
öğreteceğini söylüyordu. İkisi aynı kol için aynı anda doğru olamaz — ve bu tutarsızlık, veri onu
açığa çıkarana kadar fark edilmedi. Veri, ayrımı kayıp fonksiyonu üzerinden temiz biçimde
çözüyor: çekişmeli terimin **bulunduğu** C1'de R2'nin mekanizması işliyor (ρ = +0.232, Q1'de
iyileşme sıfır — boş girdide uydurma sürüyor); terimin **bulunmadığı** C2'de mekanizma işleyemez
ve işlemiyor (ρ = +0.032 — iyileşme katmandan bağımsız, R2'nin "iyileşmez" dediği Q1'de −0.843
px). Düzeltilmiş kapsam cümlesi, gelecek kayıtların devralması için dokümana işlendi: *uydurma
mekanizması çekişmeli terime koşulludur; saf yeniden-oluşturma kaybı altında ince ayar, girdinin
belirsiz bıraktığı her yerde kaçınmayı öğretir.*

![Üç kol görsel karşılaştırma](gorseller/uc-kol-gorsel.png)

*Aynı chip'lerde dört panel: girdi, ön-eğitimli, C1, C2. Kayıtlı "kötü görünür, iyi ölçülür"
profili doğrulandı: C2 gözle görülür biçimde daha bulanık — en seyrek girdide neredeyse dümdüz,
orta yoğunlukta keskin yollarla yumuşatılmış bitki örtüsü — ama yapısal olarak sadık. C1 daha
fotogerçekçi ve arada puan alıyor. Q3'ün en seyrek chip'inde her iki ince ayarlı kol
ön-eğitimliden kötü: kazanç chip bazında evrensel değil (C2'de 8/130 kötüleşme).*

![Yoğunluk-artık saçılımı](gorseller/yogunluk-sacilim.png)

*Girdi bilgi yoğunluğu ile chip medyan hatası, iki kol. C2 bulutu yalnız aşağı inmekle kalmıyor,
seyrek uçtaki en kötü chip'leri de topluyor — yoğunluğa bağımlılık zayıflıyor.*

Bir üretim-yolu doğrulaması sonuca güven veriyor: Faz B'nin yayınlanmış çıktıları yerel ortamda
bayt düzeyinde yeniden üretilemediğinden (üretim-ortamı sayısalları), ön-eğitimli kol aynı
ortamda yeniden üretilip kapı olarak puanlandı: yeniden-üretim − yayınlanmış = **+0.034 ± 0.045
px**, istatistiksel sıfır. Geometri ve girdi hattı bayt-özdeş, skor formülü son basamağa kadar
aynı.

## 4. Kazanım gerçek mi? — sahne adaptasyonu sınırı

Tablodaki %64'ün kritik bir zaafı var ve bunu sonuç dokümanına ben yazdım: ince ayar verisi ile
değerlendirme görüntüleri **aynı tile'ı (36TVK) ve aynı 2026-04-30 çekimini** paylaşıyor.
Chip düzeyinde sızıntı piksel piksel dışlandı, ama atmosfer, güneş açısı ve fenoloji ortak.
"Bu nisan sahnesini öğrendi" ile "Anadolu'yu öğrendi" aynı tabloyu üretir. Ayrım için iki test
kaydettim — ikisi de sınırları ve okuma bantları sayı görülmeden commit edilerek.

**Test 1 — Avrupa held-out: unutma var mı?** 568 chip (577 test chip'i − 9 kayıtlı
eğitim/test çakışması), C2 ve ön-eğitimli aynı ortamda üretildi. Kayıtlı bantlar: > +0.5 px
felaket düzeyinde unutma; +0.15…+0.5 ılımlı; ±0.15 eşit; **< −0.15 genel iyileşme**. Kayıtlı
dürüst beklenti, tek bölgeye 20 epoch ince ayarın varsayılan sonucu olarak "bir miktar unutma"
idi. Ölçüm: C2 − ön-eğitimli = **−0.364 ± 0.024 px** (t = −15.1, medyan −0.343, 124/568 chip
kötüleşti), nokta sayısı 68 → 90 (1.36×), **beş katmanın beşi de iyileşti** (Q1 −0.221 ± 0.133
… Q5 −0.373 ± 0.029). Hüküm: **genel iyileşme bandı — unutma yok.** Bu sonucun kayıtlı aday
açıklaması da ölçümden önce yazılmıştı: ince ayar çiftleri bizim **düzeltilmiş
koordinatlarımızı** taşıyor, özgün eğitim ise Rapor 1'de belgelediğim 1/256 ölçek hatalı
geometriyle yapılmıştı — ince ayar, üretecin örtük geometrik önselini kısmen yeniden eğitmiş
olabilir.

![Fark histogramları](gorseller/fark-histogram.png)

*Chip başına C2 − ön-eğitimli farkın dağılımı; negatif = iyileşme. Solda Ankara (ortalama
−1.167 px), sağda Avrupa held-out (−0.364 px). Avrupa'daki kayma küçük ama 568 chip üzerinde
sistematik — ince ayar Avrupa'da hiçbir şey unutturmamış, bir miktar da kazandırmış.*

**Test 2 — Kapadokya: kazanım sahneyle mi taşınıyor?** 36SXJ (2026-05-27), envanterdeki tile'ı
**ve** tarihi ince ayarda bulunmayan tek saha. Kayıtlı büyüklük: sabit Ankara yoğunluk kesim
noktalarıyla eşlenen katmanlarda kazanım oranı R = Kapadokya kazanımı / Ankara kazanımı; okuma
bantları **≥ 0.7 çoğunlukla gerçek adaptasyon**, 0.3–0.7 karışık, ≤ 0.3 çoğunlukla sahne. Ölçüm:
ön-eğitimli 3.391 → C2 2.861 px, eşleştirilmiş −0.780 ± 0.093 px (34/130 kötüleşme); katman
kazanımları Q1 +0.43, Q2 +1.66, Q3 +1.26, Q4 +1.41 px (Q5'te n = 2, dışarıda);
**R = 1.188 / 1.258 = 0.945**. Hüküm: **≥ 0.7 bandı — Ankara kazanımının ~%95'i sahne ve tarih
değişimini aşarak taşınıyor.**

Kayıtlı confound'u saklamıyorum: Kapadokya aynı zamanda daha zor bir yer şekli, ve fenolojisi
dört hafta kaymış. Düşük bir R iki türlü okunabilirdi (sahneye özgülük *veya* arazi zorluğu) ve
kayıt bunu açıkça söylüyordu; yüksek R ise tek türlü okunur — confound ancak sonucu
*zayıflatabilirdi*, güçlendiremezdi. Bu yüzden 0.945, bandın tasarımı gereği güçlü bir sonuç.

![Kapadokya-Ankara kazanım oranı](gorseller/kapadokya-oran.png)

*Katman bazında C2 kazanımı, iki saha, aynı sabit yoğunluk kesim noktaları. Q2–Q4'te Kapadokya
kazanımı Ankara'yla neredeyse örtüşüyor; yalnız en seyrek katman geride. Eşit ağırlıklı oran
R = 0.945.*

![Kapadokya görsel karşılaştırma](gorseller/kapadokya-gorsel.png)

*Kapadokya chip panelleri: girdi, ön-eğitimli, C2, gerçek görüntü. Ankara'da öğrenilen kaçınma
davranışı burada da görünür; peribacası/erozyon dokusunda ise her iki kol da gerçek morfolojiyi
üretemiyor — bir sonraki bölümün konusu.*

Üçüncü saha **Tuz Gölü** (36SWJ) aynı tabloda ama kayıtlı uyarısıyla: bu tile ince ayarın
eğitim tile'larından biri ve aynı 2026-04-30 tarihli. C2 için genelleme testi **değildir**;
oradaki güçlü C2 sonucu (ön-eğitimli 3.506 → 2.856... bkz. §5) sahne adaptasyonuyla tam
açıklanabilir. Ön-eğitimli ağırlıklar için ise geçerli bir bileşimsel test olmayı sürdürüyor.

## 5. Faz D — mekanizma ayrımı: bileşim mi, morfoloji mi?

Ankara'daki tek badlands chip'inin görünür başarısızlığı bir hipotez doğurmuştu: model,
Avrupa'nın **yer şekli sözlüğünün** içinde genelleşiyor, dışında bozuluyor. Bunu ayrıştırmak
için iki uç saha, sonuç tablosu önceden kaydedilerek seçildi: **Tuz Gölü** (bileşimsel uçdeğer —
%60 çıplak / %36 su tuz düzlüğü, en yakın Avrupa tile'ına JSD 0.467, ikinci adayın 2.8 katı) ve
**Kapadokya** (morfolojik uçdeğer — sıradan sınıflar, yabancı doku; JSD ölçüsü kabartmaya kör
olduğu için metrik bilinçli olarak geçersiz kılınarak eklendi, gerekçesi kayıtta). Kayıtlı
dört-sonuç tablosu: tuz chip'leri başarısız (> +0.8 px) + badlands tutar → sınır bileşim; ikisi
de başarısız → güçlü yer-şekli hipotezi; **ikisi de tutar → yer-şekli açıklaması desteklenmedi**;
tuz tutar + badlands başarısız → sözlük yalnız doku uzayında.

Ölçümler (ön-eğitimli ağırlıklar, yoğunluk-eşleşmiş Avrupa'ya karşı):

- **Tuz Gölü tuz chip'leri (n = 51):** eşleşmiş ceza **+0.513 ± 0.140 px** — kayıtlı başarısızlık
  eşiği +0.8 px **aşılmadı**, ama "tutar" eşiği ≤ +0.3 px de sağlanmadı: ara sonuç.
- **Kapadokya badlands chip'leri (n = 5, bitkisiz oran ≥ %25):** ceza **+0.084 ± 0.265 px**;
  aynı sahanın düz-tarım chip'leri (n = 113): **+0.446 ± 0.063 px**. Badlands ≈ düz — morfolojik
  bir imza **yok**.

Dört-sonuç tablosunda en yakın satır **tutar/tutar**: güçlü biçimiyle yer-şekli-sözlüğü hipotezi
**desteklenmedi**. Onun yerine veride görünen şey, yer şeklini izlemeyen saha-düzeyi cezalar ve
aynı 568 chip'lik taban çizgisinde üç sahanın oluşturduğu bir **gradyan**: Ankara +0.23 <
Kapadokya +0.45 < Tuz Gölü +0.46–0.51 px. Kalite gözetilerek seçilmiş sahne (Ankara) en düşük
cezayı gösteriyor. Tek badlands chip'inden kurulan
hipotez, 130'ar chip'lik ölçümde büyük ölçüde o chip'in anekdotu çıktı — ve bunu söyleyebilmemin
tek nedeni, sonuç tablosunun sonuçtan önce yazılmış olması.

![Tuz Gölü görsel karşılaştırma](gorseller/tuzgolu-gorsel.png)

*Tuz Gölü chip panelleri. Tuz kabuğunun dokusu her iki kolda da yarı gerçekçi; asıl bulgu
sayısal: ince ayarın kazanımı tuz chip'lerinde yalnız +0.185 px iken tuz-dışı chip'lerde
+0.860 px. Eğitim verisinde neredeyse hiç bulunmayan sınıf, ince ayardan neredeyse hiçbir şey
alamıyor.*

Tuz Gölü'nün C2 tarafı (eşleştirilmiş −0.587 ± 0.103 px, 36/126; 4 chip iki kolda 0 nokta
verdiği için dışlandı, dışlama kuralı simetrik) yukarıdaki sahne-adaptasyonu uyarısıyla
okunmalı. Ama içindeki kontrast uyarıdan bağımsız bilgi taşıyor: **C2 kazanımı tuz
chip'lerinde +0.185, tuz-dışında +0.860 px.** İnce ayar, eğitim örneklemesinde nadir olan
sınıfa (tuz yüzeyi; benzer biçimde su, Ankara sahnesinin %0.34'ü) işlemiyor. Bu, C3'ün
AB-karışım gerekçesinin ta kendisi ve kayıtlı per-sınıf raporlama planının nedeni.

## 6. Checkerboard izleme kalemi

C2 çıktılarının bir kısmında transpoz-evrişim kaynaklı zayıf bir dama tahtası deseni görünüyor.
KLT periyodik desene kilitlenebildiği için bunun nokta sayısını şişirme riski var; metrik
(FFT'de periyot-2/4 tepe gücü) her üretimde kaydedilmek üzere **üretimden önce** tanımlandı.
Sonuç, üç sahada tutarlı: artefakt gücü nokta sayısıyla **negatif** korelasyonda (C2: Avrupa
ρ = −0.281, p ≈ 10⁻¹¹; Kapadokya −0.392; Tuz −0.380) ve artıkla **pozitif** (sırasıyla +0.251 /
+0.420 / +0.451). Yani desen metrikleri şişirmiyor; güçlü olduğu chip'ler zaten kötü eşleşen
chip'ler. Artefakt C2'de ön-eğitimliden güçlü (medyan güç 0.0018–0.0024'e karşı 0.0012–0.0019;
gürültü tabanı 0.0009) ve girdisi seyrek chip'lerde yoğunlaştığı için **seyreklikle karışıktır**
(confound) — izleme kalemi açık kalıyor, kapanmış bir bulgu değil.

## 7. Düzeltmeler disiplini — kayıt ile gerçek ayrıştığında

Bu dönem, kayıtlı/iddia edilen ile fiilen doğru olanın ayrıştığı her durumu tek bir günlükte
topladım. Uygulanan test: *bu tutarsızlığı bilen bir okur herhangi bir sonucu farklı yorumlar
mıydı?* Hayırsa kayıt düzeltilir (görünür biçimde); evetse **veya sapma kendi tahminimiz
yönündeyse** koşu düzeltilir. On bir kayıt:

| # | İddia/varsayım | Gerçek | Çözüm |
|---|---|---|---|
| 1 | "KARIOS'ta üst projeden 3× kötüyüz" | İki farklı büyüklük karşılaştırılmış; üst projenin kendi istatistiğinde 4.5× daha iyiyiz | İddia geri çekildi |
| 2 | "11 kapı chip'i sıfır noktayla kalıyor; nedeni su kaybı" | Harness hatası: referans dosyaları eksikti, hata çıktısı susturulmuştu — chip'ler hiç ölçülmemişti | Atıf geri çekildi; harness düzeltildi; erratum yazıldı |
| 3 | Isınma gerekçesi: "bu hızda D, G'yi bozduğundan kat kat hızlı öğrenir" | pix2pix tek `--lr` kullanır; G/D oran hiç değişmez | Gerekçe değiştirildi, yapılandırma aynı |
| 4 | Faz C/D sahne tarihleri birbirinin yerine geçer varsayımı | Kapadokya'nın kullanılabilir 04-30 sahnesi yok; dört haftalık fenoloji sapması | Veri hazırlanmadan confound olarak kaydedildi |
| 5 | "Isınma = 2 epoch 2e-5"; ardından "kayıp simetrik, o yüzden nötr" | Isınma epoch 2'si **lr = 0** koşmuş (zamanlayıcı off-by-one); simetri iddiası yanlıştı — anomali yalnız C1'e düşüyor ve **kendi R1 tahminimiz yönünde** | **Koşu düzeltildi:** C1, hiçbir sonuç görülmeden iptal edilip `--lr_policy step` ile yeniden başlatıldı |
| 6 | Geofabrik çıkarımları Overpass'a denk varsayımı (ilk "düzeltme" bir config anahtarıydı) | osmium `simple` stratejisi sınır-aşan multipolygonları düşürüyor; config anahtarı sessizce yok sayılıyor — düzeltme boşmuş | Komut satırında `-s smart`; şeffaflık kapısı yeniden: %99.91 |
| 7 | Kaggle mount sorunu "`dataset_sources` ile çözüldü" | Bağlama bozuk değildi; sabit kodlanmış yol yanlıştı (özel veri setleri farklı yollara bağlanabiliyor) | Betikte mount keşfi; iki yerleşim de gözlendi |
| 8 | Kernel kimliği = metadata `id` varsayımı | `kernels push` slug'ı **başlıktan** türetir ve yalnız uyarır | Kimlikler başlıktan türetilir hale getirildi |
| 9 | `torch.cuda.is_available()` GPU kanıtı sayıldı | P100'de (sm_60) True döner ama torch 2.10+cu128 kod üretemez | Preflight'a mimari-listesi doğrulaması; T4 sabitlendi |
| 10 | Faz B `test_opt.txt` kaydı çıkarım replikasyonunda güvende varsayıldı | `test.py` opsiyon dosyasını checkpoint klasörüne yazar; replikasyon orijinali ezdi | Açıklandı; orijinal koşunun opsiyonları dokümanda metin olarak korunuyor |
| 11 | Faz B başlığı: "ölçülebilir coğrafi ceza yok" | Sonuç taban çizgisine bağımlıydı: 44 chip'lik eski tabanda −0.247 px, daha iyi desteklenen 568 chip'lik tabanda **+0.226 px**; kayıtlı yoğun-katman ölçütü yine tetiklenmiyor (Q4 +0.174, Q5 +0.038) | Başlık düzeltildi ("yoğun katmanlarda ceza yok, genelde ılımlı"); Faz D dokümanı yazılmadan önce tüm sahalar tek taban çizgisine karşı yeniden puanlandı — düzeltmeyi yakalayan da bu oldu |

5 numaralı kayıt ilkesel olarak en önemlisi: yeniden başlatmayı zorlayan şey sapmanın büyüklüğü
değil (C1 adım bütçesinin %1.49'u), **yönüydü**. Kendi tahminimize doğru işleyen bir sapma,
muhtemelen önemsiz olsa bile, şüpheci bir okurun reddetme hakkına sahip olduğu tam
konfigürasyondur — o yüzden sonuç doğmadan yok edildi.

**Rapor 1'e göre güncellenen ifadeler** (hiçbir sayı yanlış çıkmadı; şunlar daha iyi kontrollü
ölçümlerle güncellendi):

- Rapor 1'in **ρ = −0.79** değeri, erken ve kontrolsüz yerel metrikti. Güncel değerler: nokta
  sayısı kontrol edilince kısmi **ρ = −0.61** (GenCP'ye özgü etki; gerçek görüntülerdeki tavan
  kontrolü ρ ≈ +0.06, null) ve yoğunluk-artık ilişkisi Avrupa **ρ = −0.655/−0.675**, Türkiye
  **ρ = −0.727**.
- "Türkiye sahası: beklemede" → Ankara seçildi, üretildi, ölçüldü; Faz C ve D tamamlandı.
- Üst projenin "sapmalar çoğunlukla kırsal alanlarda" gözlemi Rapor 1'de mekanizmasızdı; artık
  mekanizma biliniyor **ve kapsamı ölçüldü**: uydurma, çekişmeli kayba koşullu (R2'nin
  düzeltilmiş kapsamı).
- "Uydurma cezalandırılamıyor, eşiği yok" tespiti hâlâ doğru — ama pratik çözümü bulundu:
  sorunu üreten kayıp terimini kaldırmak (C2), uydurmanın kendisini büyük ölçüde kaldırıyor.

## 8. Sonraki adımlar

![Dört sahada kazanım özeti](gorseller/dort-saha-kazanim.png)

*C2'nin dört sahadaki eşleştirilmiş kazanımı (hata çubukları ± standart hata). Ankara kısmen
sahne avantajı içerir; Kapadokya taşınmayı, Avrupa unutmamayı ölçer; Tuz Gölü eğitim tile'ı
olduğu için uyarıyla raporlanır.*

| # | İş | Ön koşul |
|---|---|---|
| 1 | **C3 koşusu** — C2 reçetesi + 1200 AB çifti (karışımın %17.7'si), aynı 20-epoch protokol, aynı 130-chip değerlendirme. Paket hazır ve doğrulanmış. | GPU kotası: 22 Ağustos 00:00 UTC |
| 2 | **C3 puanlaması** — kayıtlı beklenti ve karar kuralına karşı (aşağıda). | Madde 1 |
| 3 | **Per-sınıf raporlama** — su / kentsel / tuz sınıflarında ayrı doğruluk tablosu; C3'ün nadir-sınıf iddiasının doğrudan testi. Kayıtlı. | Madde 1 |
| 4 | **Checkerboard izlemesinin sürdürülmesi** — C3 dahil her üretimde aynı metrik. | Yok |

C3'ün anlamı, Avrupa sonucuyla değişti ve bunu açıkça kaydediyorum: karışım, "unutmayı onarmak"
için tasarlanmıştı; Avrupa'da unutma çıkmadığına göre onaracak bir şey yok. C3 artık şu soruyu
test ediyor: *karışım, Türkiye-yalnız ince ayarın üzerine ölçülebilir bir şey ekliyor mu —
özellikle nadir sınıflarda (tuz, su, yoğun kent)?* **Null sonuç beklenen sonuçtur** ve öyle
raporlanacaktır; C2'nin mevcut kazanımını koruyup korumadığı ve tuz-chip'i kazanımını
+0.185 px'in üzerine taşıyıp taşımadığı, sayılar görülmeden yazılmış karar kuralıyla
puanlanacak.

## Üretilen çıktılar

| Çıktı | İçerik |
|---|---|
| Kod deposu | Rasterleştirici, kalite kapıları, Kaggle eğitim paketi, analiz betikleri — github.com/mvy0502/GenCP (tubitak-tr dalı, tubitak/ klasörü) |
| Teknik dokümanlar | 11 doküman: tahmin kayıtları, sonuç puanlamaları, yapılandırma, düzeltme günlüğü — her sonuç için yöntem, sayı, sınırlama |
| Eğitilmiş modeller | C1 ve C2 üreteç checkpoint'leri (epoch bazında, bütünlük doğrulamalı) + ayrıştırıcı provenance kaydı |
| Üretim ve ölçüm | 4 sahada (Ankara, Avrupa held-out, Kapadokya, Tuz Gölü) toplam ~1.500 chip'lik üretim-ölçüm çifti, chip bazında CSV'lerle |

Kullandığım tüm bileşenler açık lisanslı: kod BSD 3-Clause, GenCP model ağırlıkları CC-BY 4.0,
Sentinel-2 verisi Copernicus açık lisansı, OSM verisi ODbL, CLC+ Backbone Copernicus Land
Monitoring Service koşullarında. Kaggle'a yüklenen eğitim veri seti özel (private) tutuluyor;
kamuya açılması gerekirse ODbL'nin paylaş-benzer hükümleri için ayrı bir lisans kararı gerekir ve
bu, dokümana not edilmiştir. Rapordaki tüm ölçümler tekrarlanabilir: tahmin kayıtları, betikler
ve chip bazında ham sonuçlar kod deposunda; ayrıntılı teknik dokümantasyon talep hâlinde
iletilebilir.
