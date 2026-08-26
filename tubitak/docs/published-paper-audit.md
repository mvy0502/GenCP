# Yayınlanmış GenCP makalesinin denetimi — 10 maddelik kontrol

**Kaynak:** Guasch, E.; Yalçın, İ.; Kocaman, S.; Saunier, S.; de Laurentiis, L.
*GENCP: GAN-Based Ground Control Point Generation for Satellite Image Georeferencing.*
**Remote Sensing 2026, 18(14), 2356**, yayın tarihi 2026-07-15, DOI **10.3390/rs18142356**
(gold OA, 39 sayfa). PDF yerel kopya: `tubitak/data/paper/gencp.pdf` (36,7 MB), metin
katmanı `gencp_text.txt`, şekiller `figs/`.

Zenodo 15044428 makale değil **poster**tir (VH-RODA 2024). Aynı DOI ağırlıkların da
kaynağı. Aşağıdaki her madde, makalenin metin katmanından veya yayınlanmış veri
setinden doğrudan doğrulandı.

---

## 1. KARIOS artık şekilleri — **makaleden belirlenemiyor**

Makale Şekil 22–25'te KARIOS çıktısını veriyor, ancak yalnızca **dağılım** panellerini:
histogramlar, dairesel hata saçılımı (easting-northing düzleminde) ve radyal hata
yüzdelik eğrisi. **Konuma bağlı bir artık haritası / kayma alanı (shift field)
yayınlanmamış.** Dolayısıyla "çip içinde konuma göre doğrusal rampa var mı" sorusu
yayından cevaplanamıyor; KARIOS bu çıktıyı üretebiliyor (bizim koşularımızda `02_dx.png`
vb.), makale dahil etmemiş.

Dairesel saçılım görsel olarak izotropik ve tek merkezli — saf bir ölçek hatasının
üreteceği yönlü/kama biçimli yapı görünmüyor. Bu, madde 2'deki nicel sonuçla tutarlı.

## 2. Ortalama–saçılım tutarsızlığı — **imza mevcut, ve makale bunu kendisi yazıyor**

Makalenin kendi cümlesi: *"the RMSE is mainly driven by residual dispersion"* ve
*"the HR model does not introduce a strong systematic displacement"*.

| | 31TFJ (eğitim sahası) B04 | 31TFJ TCI | 30TXT (bağımsız) B04 | 30TXT TCI |
|---|---|---|---|---|
| Ortalama hata | 5,7 m | 6,4 m | 5,6 m | 7,2 m |
| Std | 20,5 m | 21 m | 23,7 m | 23,2 m |
| RMSE | 21,3 m | 21,9 m | 24,4 m | 24,3 m |

Eksen bazında: 31TFJ TCI easting ortalama **−3,39 m** (σ 14,53), northing **+5,49 m**
(σ 15,10); 30TXT B04 easting **−1,58 m** (σ 17,29), northing **+5,42 m** (σ 16,26).

**Bizim ölçek hatamızla nicel karşılaştırma — dikkatli okunmalı:**

Bir 256 px çipte gerçek GSD 10,0390625 m, beyan 10,0 m ⇒ piksel başına 0,0390625 m hata;
çip kenarında eksen başına **10,0 m**, köşede **14,14 m**. Anahtar noktalar çip üzerinde
düzgün dağılıysa eksen başına **ortalama 5,0 m, std 2,89 m**.

- **Ortalamalar çarpıcı biçimde uyuyor.** Kuzey-yukarı bir rasterde GSD eksik beyan
  edilirse northing hatası pozitif, easting hatası negatif olur ve her ikisi de 0→10 m
  büyür, ortalaması ±5 m. Makalenin dört HR ölçümünde de northing ortalaması **+5,0…+6,9 m**,
  easting ortalaması **−1,6…−3,4 m**: *işaretler ve büyüklük mertebesi öngörüyle uyumlu.*
- **Saçılım uymuyor.** Öngörülen std 2,89 m, gözlenen σ ≈ 14,5–17,3 m. Ölçek hatası
  varyansın en fazla **%3,9**'unu açıklar.

**Dürüst sonuç:** yayınlanmış sistematik ortalama kaymalar (~5 m) bizim bulduğumuz ölçek
hatasının imzasıyla tutarlı; **saçılım ise değil** ve makalenin kendi açıklaması (içerik,
maske bilgi yoğunluğu, yerel eşleşme hataları) orada geçerli kalıyor. Bunu bir *hipotez*
olarak sunmalıyız — onların işleme zincirinin bu betiği kullanıp kullanmadığını ve
KARIOS'un işaret konvansiyonunu doğrulayamıyoruz.

## 3. 257 nereden geliyor? — **premis tersine döndü: veri hazırlığından**

- Makale **"5500 image patches with a size of 256 × 256 pixels ... from the 23 sites"**
  diyor; Tablo 5'te her iki model için `Image size 256 × 256`.
- **"257" makale metninde hiç geçmiyor** (0 kez). "10.0390625" de geçmiyor.
- **Ama yayınlanan veri seti 257 piksel.** `GenCP_HR_DB/image_pairs/train` içindeki 400
  örneklem rasterin tamamı **514 × 257** (yani iki adet 257 × 257 yarım), beyan edilen
  piksel boyutu 1,0 (coğrafi dönüşüm yok).
- Upstream `GenCP_HR_demo/gencp_georeferencing.py` (telespazio-tim, `e218f29`,
  2025-03-20, *"add GenCP demo notebooks"*) boyutları **üretilen** görüntüden,
  dönüşümü **referans** rasterden alıyor:
  `height=test_img.shape[1], width=test_img.shape[2], transform=src.transform`.
  Kodda "257" sabiti yok; uyumsuzluk örtük.

**Cevap:** 257 **eğitim/korpus verisi hazırlığından** geliyor; ağın gördüğü boyut 256
(makaleyle tutarlı); hata ise 257 tabanlı dönüşümün 256 px çıktıya yazıldığı
**demo/çıkarım betiğinde** oluşuyor. Yani sizin kuralınızın ikinci şartı ("çıkarma adımı
hiç 257 üretmiyorsa") **sağlanmıyor** — dolayısıyla "yalnızca çıkarım yolunda" demek
eksik olur. Doğru ifade: *kök neden, veri hazırlığındaki 257 ile belgelenen/ağın kullandığı
256 arasındaki belgelenmemiş indirgemedir; hata çıkarım yolunda maddileşir.*

## 4. HR için yeniden örnekleme adımı — **tarif edilmiyor**

VHR için açık: *"All images were resampled to a spatial resolution of 50 cm."*
HR bölümünde (§3.1) vektör indirme, rasterleştirme ve yama çıkarma anlatılıyor;
**herhangi bir yeniden örnekleme adımı yok.** Makaledeki 8 "GSD" geçişinin tamamı VHR
bağlamında. 257→256 indirgemesi fiilen gerçekleşiyor (pix2pix `load_size`/`crop_size`
yolu) ama makalede belgelenmiyor.

## 5. Üretilen çipin GSD'si 10.0 m yazılmış mı? — **evet, yayınlanmış şekilde**

Şekil 22 (31TFJ TCI) ve Şekil 25 (30TXT B04) KARIOS panellerinde, **monitored dosya
üretilen ürün** iken (`31TFJ_gen_TCI.tif`, `30TXT_gen_B04_clip.tif`) panel açıkça
**`Pixel size : 10.0 m`** yazıyor (sırasıyla EPSG:32631 ve EPSG:32630).

**Belgelenmiş çelişki mevcut:** yayınlanmış figürde üretilen ürün 10,0 m olarak
raporlanıyor; aynı depodaki georeferans betiği ise 257 px'lik referans dönüşümünü 256 px
çıktıya kopyaladığı için gerçek örnekleme aralığı 10,0390625 m.

## 6. Raporladıkları KARIOS sayıları (atıf için)

**HR modeli, iki S2 L2A ürünü** — 31TFJ (eğitim sahası,
`S2B_MSIL2A_20240915T102559_N0511_R108_T31TFJ_20240915T131207`) ve 30TXT (bağımsız saha,
`S2A_MSIL2A_20240919T105731_N0511_R094_T30TXT_20240919T171547`):

| Ölçüt | 31TFJ TCI | 31TFJ B04 | 30TXT TCI | 30TXT B04 |
|---|---|---|---|---|
| Eşleşen anahtar nokta | **2912** | **2798** | **957** | **978** |
| Global RMSE | 21,93 m | 21,29 m | ~24,4 m | ~24,4 m |
| CE90 | 35,70 m | 35,23 m | 39,69 m | 39,46 m |
| CE95 | 42,14 m | 41,90 m | 45,16 m | 46,12 m |
| Easting ort. / σ | −3,39 / 14,53 m | −2,72 / — | −2,10 / — | −1,58 / 17,29 m |
| Northing ort. / σ | +5,49 / 15,10 m | +5,01 / — | +6,89 / — | +5,42 / 16,26 m |

Görsel/radyometrik (Tablo 7): Mix Sites–TCI MS-SSIM 0,414 / PSNR 28,586 / LPIPS 0,520;
Mix–B04 0,453 / 29,160 / 0,468; 30TXT–TCI 0,312 / 28,431 / 0,542; 30TXT–B04 0,336 /
28,625 / 0,494.

Makalenin kendi nitelemesi, alıntılanmaya değer: sonuçlar *"coarse geometric consistency
rather than precise GCP-level control"* olarak yorumlanmalı.

## 7. Anahtar nokta sayısı raporlanmış mı? — **evet, ve boşluk iddiamızı destekliyor**

Yukarıdaki tablo. Kritik olan, makalenin kendi gözlemi: eğitim sahasında 2912/2798 olan
sayı bağımsız sahada **957/978'e düşüyor** ve makale bunu *"weaker matching robustness ...
the generated chips generalize less effectively to the independent site"* diye yorumluyor.

Bizim ölçtüğümüz eşleşme noktası açığı (sentetik 388, gerçek görüntüler 1164–1738) ile
aynı yöndedir; makale bu düşüşü kendi bağımsız sahasında zaten belgelemiş durumda.

## 8. Kayıp formülasyonları — **HR'da LPIPS teyit edildi**

Tablo 5:

| | HR modeli | VHR modeli |
|---|---|---|
| GAN Loss | **Adversarial + λ·LPIPS** | **Adversarial + λ·L1** |
| λ | 100 | 100 |
| Discriminator loss | BCE | BCE |
| Öğrenme oranı / epok | 0,0002 / 120 | 0,0002 / 100–150 |
| Batch | [1, 4, 16] | 32–64 |
| Görüntü boyutu | 256 × 256 | 256 × 256 |
| Dropout | True | True |

Metin açık: *"the L1 reconstruction loss used in the classical Pix2Pix formulation was
replaced by a Learned Perceptual Image Patch Similarity (LPIPS) loss"* — **HR'da L1
yerine LPIPS**. LPIPS TorchMetrics 0.11.0 ile hesaplanıyor.

Bu, depodaki `models/pix2pix_model.py`'nin torchmetrics'i koşulsuz import edip LPIPS'i
`.cuda()` ile kurmasının **sebebini açıklıyor**: HR modeli gerçekten LPIPS ile eğitilmiş.

> **Bizim C1/C2 karşılaştırmamız için önemli sonuç:** yayınlanmış HR ağırlıkları
> *adversarial + LPIPS* ile eğitilmiş; bizim C1 kolumuz ise stok pix2pix *adversarial + L1*
> ile ince ayar yapıldı. Yani C1, yayınlanmış modelin kayıp yapısını yeniden üretmiyor.
> "Adversarial terim bir yüktür" bulgumuz C1–C2 karşıtlığından geliyor ve geçerli kalıyor,
> ancak yayınlanmış modelle ilişkilendirirken bu fark belirtilmeli.

## 9. 23 Avrupa eğitim sahası ve 30TXT — **bizim sahalarımız temiz**

- 23 saha ve MGRS kodları **Şekil 3'te görsel olarak** veriliyor; metin katmanında liste
  yok (yalnızca 30TXT ve 31TFJ metinde geçiyor).
- 30TXT: *"an unseen European site"*, bağımsız test tile'ı. 31TFJ: eğitim sahası.
- **Doğrudan kanıt yayınlanmış korpustan alındı.** `GenCP_HR_DB` içindeki farklı MGRS
  tile'ları: eğitim 76, test 57, birleşim **77 tile**, tamamı **UTM 30–34** kuşağında
  (Batı/Orta Avrupa).

| Bizim sahamız | Korpusta var mı? |
|---|---|
| 36TVK (Ankara — Faz B/C değerlendirmesi) | **YOK** |
| 36SXJ (Kapadokya — temiz kıyas sahası) | **YOK** |
| 36SWJ (Tuz Gölü) | **YOK** |
| 35TPF (İstanbul — E2 güncellik sahası) | **YOK** |

Türkiye kuşağındaki (35T/36/37/38) **hiçbir tile korpusta yok**. Ön-eğitimli modelin
eğitim setiyle değerlendirme sahalarımız arasında **örtüşme yok**; ODTÜ kontaminasyonu
yalnızca *bizim kendi ince ayar setimize* özgüydü ve orada zaten kayıt altına alındı.

*Küçük tutarsızlık, not edilsin:* makale "23 saha / 5500 yama" diyor; yayınlanan korpus
77 MGRS tile ve 5131 + 577 = **5708** çift içeriyor (ayrıca daha önce tespit ettiğimiz
9 sızıntı chip'i). "Saha" ile "tile" aynı şey değil; sayılar birebir örtüşmüyor.

## 10. Veri erişilebilirlik beyanı — **commit yok**

> *"The code and the associated datasets are publicly available at
> https://github.com/telespazio-tim/GenCP (accessed on 6 July 2026) and
> https://doi.org/10.5281/zenodo.15044428 (accessed on 6 July 2026)."*

- **Sürüm veya commit belirtilmemiş** — yalnızca çıplak depo adresi ve erişim tarihi.
- Zenodo kaydındaki "Repository URL" alanı ise **farklı** bir adres gösteriyor:
  `github.com/telespazio-tim/pytorch-CycleGAN-and-pix2pix-for-genCP`.
- Bizim çatalımızın temel aldığı upstream commit'ler: `c99ce7c` (first commit) …
  `e218f29` (demo notebooks, georeferans betiğinin eklendiği commit) … `8dc9f2a`.

Yani yayının işaret ettiği kod durumu **tek bir noktaya sabitlenmemiş**; bizim bulgumuzu
atıflarken hangi commit'i incelediğimizi kendimiz belirtmeliyiz.
