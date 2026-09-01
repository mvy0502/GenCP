# Devir rehberi — GenCP TÜBİTAK çalışması

> ## DEPO AYRIMI — 26 Ağustos 2026
>
> **Araştırma işi bu depoda yapılmaz.** 26 Ağustos 2026 tarihinden itibaren:
>
> | Ne | Nerede |
> |---|---|
> | Ön kayıtlar, sonuçlar, denetimler, kanıt artefaktları, düzeltme kaydı | **gencp-validation** — https://github.com/mvy0502/gencp-validation (dal: `main`) |
> | Makale (GRSL letter ve arXiv uzun sürümü) | **gencp-letter** — depo özeldir, bağlantı verilmedi: erişimi olmayan herkese 404 döner |
> | pix2pix fork'u, QGIS eklenti iş paketi, OSM rasterizer ve korpus zinciri | **bu depo** (GenCP), dal `tubitak-tr` |
>
> Bu rehberdeki `docs/...` bağlantılarının çoğu artık bu depoda çözülmez; hedefleri
> gencp-validation'a taşındı. Aynı yollar orada geçerlidir.
>
> **Bir araştırma kaydını (registration) bu depoya işlemeyin.** Tek istisna bir dosya
> değil, bir **sınıftır**: **eklenti iş paketinin kendi kayıtları ve sonuçları burada
> kalır.** Bir gate'i kaydeden ya da raporlayan her belge, yönettiği kodun yanında
> durur. Bugün bunlar `docs/plugin-gate-registrations.md` (çünkü `tests/gate_r.py` ve
> `gate_o.py` kayıt belgesi olarak onu gösterir) ve `docs/plugin-results.md`. Sonraki
> kapıların belgeleri de bu satır değiştirilmeden aynı sınıfa girer.
>
> ### Kayda geçen ramak kala — 26 Ağustos 2026
>
> **Sınır ilk yazıldığında bu istisna sınıf olarak değil, o an var olan tek dosya
> olarak yazıldı.** Sonuç: silme commit'i `b815b46`, paralel çalışan oturumun tam o
> sırada yazmakta olduğu `tubitak/docs/plugin-results.md` dosyasını sildi. Dosya
> **kayboldu ve yeniden yazılarak kurtarıldı** (`21054d7`); yayımlanmış hiçbir sayı
> etkilenmedi, kayıtlı hiçbir iddia yer değiştirmedi. Bu yüzden burada duruyor:
> **depo hijyeni**, araştırma kaydına yapılmış bir düzeltme değil —
> `corrections-log.md`'ye girmez.
>
> Kayda geçmesi gereken üç ayrıntı:
>
> - **Sınır, yazıldığı biçimiyle denetleyen oturum tarafından onaylandı.** Hata
>   onaysız bir adım değildi; onaylanan metnin kendisi dardı.
> - **Uçuştaki iş yok edildi.** Kurtarıldı, ama silme, aynı ağaçta aktif olarak
>   yazılmakta olan bir dosyayı yakaladı.
> - **`b815b46`'nın commit mesajı hâlâ dar hâli söylüyor** ("`tubitak/docs/**` except
>   `plugin-gate-registrations.md`"). Commit mesajı değiştirilemez — tarih yeniden
>   yazılmıyor — bu yüzden tutarsızlık keşfedilmeyi beklemek yerine buraya yazıldı:
>   **geçerli olan bu paragraftır, o commit mesajı değil.**
>
> Tarih yeniden yazılmadı ve yazılmayacak. İki depo 96503b7 birleşme tabanından
> itibaren aynı tarihi paylaşır; araştırma kaydında anılan 49 commit SHA'sının hepsi
> her iki depoda da çözülür. `filter-repo` hiç kullanılmadı.
>
> ### KURAL: İKİ DEPO KALICI OLARAK AYRILDI — HİÇBİR YÖNDE MERGE YOK, HİÇBİR ZAMAN
>
> Bu bir uyarı değil, **kuraldır**. Uyarı unutulur; kapalı kapı unutulmaz.
>
> - **`b815b46` 263 dosyayı siler.** `tubitak-tr` dalı gencp-validation'a
>   birleştirilirse bu silme oraya yayılır ve **araştırma kaydını yok eder**.
> - **Ters yön de kapalıdır.** gencp-validation `main` bu depoya birleştirilmez.
> - **Bekleyen tek tamamlayıcı aktarım `cherry-pick` ile yapılır**, merge ile değil.
>   Senkron noktası `844dbec`; oraya kadar her şey gencp-validation'da (birleştirme
>   `f9e0de6`, ardından kanıt rasterları `284571b`). Sonrasında bu dalda oluşanlar:
>   `f95ad61`, `d393152`, `814f06c` (eklenti iş paketi — sınıra göre GenCP'de kalır)
>   ve `b815b46` (silme commit'i).
> - **O aktarımdan sonra senkron KAPANIR.** GenCP fork ve QGIS eklenti iş paketi
>   olarak devam eder; gencp-validation araştırma kaydı ve makale çalışması olarak
>   devam eder. Bir daha birleşmezler.


Bu dosya, projeyi devralacak kişinin (yeni stajyer veya proje sahibi) "ne nerede
yapıldı, nasıl çalıştırılır, ne açık" sorularına tek yerden cevap bulması için
yazıldı. Son güncelleme: 26 Ağustos 2026 (depo ayrımı — yukarıdaki kutuya bakın).

## 1. Beş dakikada proje

Upstream GenCP (`telespazio-tim/GenCP`), OSM rasterlarından pix2pix ile sentetik
uydu görüntüsü (GCP referansı) üretir. Bu çalışma o pipeline'ın bağımsız ölçüm ve
doğrulamasıdır: yayınlanmış modelde doğrulanmış bir georeferanslama ölçek hatası
(+1/256), üç kollu KARIOS validasyonu, halüsinasyon ölçümü, kayıp fonksiyonu
faktöriyeli (2×2, GAN × L1/LPIPS) ve Türkiye'ye genelleme hattı içerir.
Özet: [`tubitak/README.md`](README.md) → "Findings summary" ve
"Where things moved since" bölümleri.

## 2. Ne nerede?

| Ne | Nerede |
|---|---|
| Bulgular ve güncel durum özeti | [README.md](README.md) |
| Tüm deney kayıtları (registration) ve sonuç raporları | [docs/](docs/) — her deney `*-registration.md` + `*-results.md` çifti |
| Düzeltme geçmişi (hangi iddia neden geri çekildi/değişti) | [docs/corrections-log.md](docs/corrections-log.md) |
| Açık işler — her paket sonunda baştan okunur | [docs/open-items.md](docs/open-items.md) |
| Kurumsal teslimat aracı (deterministik referans üretici, Option-A düzeltmesi gömülü) | [tool/gencp_ref.py](tool/gencp_ref.py) + [docs/tool-results.md](docs/tool-results.md) |
| Faz C eğitimleri (Kaggle, 2×T4) | [kaggle/](kaggle/) — `build_kernels.py` + `train_c1_c2.py` |
| Seed replikasyonu (Modal, A10G) | [modal/gencp_modal.py](modal/gencp_modal.py) + [docs/seed-replication-registration.md](docs/seed-replication-registration.md) |
| Ölçüm/analiz scriptleri | [scripts/](scripts/) — açıklamalı liste README'deki dizin ağacında |
| Türkçe ilerleme + sonuç raporları | [rapor2/](rapor2/), [rapor3/](rapor3/) (PDF'ler `rapor3/build_pdf.py` ile üretilir, git'te tutulmaz) |
| Makale planı (GRSL letter) | [docs/paper-roadmap.md](docs/paper-roadmap.md) |

Kök dizindeki geri kalan her şey upstream pix2pix/GenCP kodudur; bu çalışma onu
değiştirmez (tek istisna: eğitim kollarının uyguladığı, kayıtlı yamalar — bkz.
`kaggle/train_c1_c2.py` ve `modal/` içindeki patch).

## 3. Nasıl çalıştırılır?

1. **Ortam:** [README.md](README.md) → "Environment setup" (Miniforge, `gencp` env)
   ve "Known issues" (OpenMP ve visdom tuzakları — ikisine de düşeceksiniz).
2. **Referans üretimi:** `tool/gencp_ref.py` — deterministik; aynı girdiyle
   byte-exact aynı çıktı. Kullanım README'deki "Running the pipeline" bölümünde.
3. **Ölçümler:** her scriptin başında ne ölçtüğü ve hangi doc'a rapor verdiği
   yazar; `shift_estimator.py` gibi paylaşılan modüller self-test içerir —
   ölçüme güvenmeden önce self-test çalıştırın.
4. **GPU işleri:** Kaggle kernelleri `kaggle/build_kernels.py` ile üretilir;
   Modal uygulaması `modal/gencp_modal.py` (staging, enumeration-order yaması ve
   dosya sayısı guard'ı dahil — bunlara dokunmadan önce
   [docs/corrections-log.md](docs/corrections-log.md) entry 29'u okuyun).

## 4. Çalışma disiplini (devralan kişi için önemli)

- Her deney **önce kayıt** (registration: tahminler, falsifikasyon bantları),
  **sonra koşu**, sonra kayda karşı skorlanmış sonuç dosyası.
- Hatalar silinmez; [docs/corrections-log.md](docs/corrections-log.md)'a
  numaralı girdi olarak işlenir. Git geçmişi (662+ commit) kayıtların zaman
  damgasıdır — **history rewrite yapmayın.**
- Paket kapanışında [docs/open-items.md](docs/open-items.md) baştan okunur
  (standing practice 8).

## 5. Açık işler ve karar bekleyenler (25 Ağustos itibarıyla)

1. **Seed replikasyonu** Modal/A10G üzerinde koşuyor (SEED-b kapısı) — sonuç
   docs'a işlenecek.
2. **Piksel bazlı confidence score (iyi/kötü)** — danışman direktifi (25 Ağustos
   görüşmesi); kayıt (registration) yazılmadan uygulanmamalı. Mevcut reliability
   skoru chip seviyesinde; piksel seviyesi için aday girdiler zaten ölçülü: OSM
   kenar yoğunluğu (rho = −0.61 bulgusu), halüsinasyon oranı, palet-dışı pikseller.
3. **Türk rasterizer'ı** KARIOS kabul kapısını geçemedi; tanımlı çözüm land-cover
   taban katmanı (ör. ESA WorldCover) — karar bekliyor
   ([docs/renderer-tolerance.md](docs/renderer-tolerance.md) §4).
4. **Offline/uydu-üstü kullanım bağlamı** E1–E3 konumlandırmasına işlenecek:
   hedef ortam uyduda offline kullanım (gerçek referans görüntüye erişim yok) —
   E1–E3'ün çürüttüğü "gerçek görüntü zaten erişilebilir" öncülünün geçerli
   olmadığı, sentetik referans gerekçesinin ayakta kaldığı senaryo. E1–E3'ü
   geçersiz kılmaz, kapsamını netleştirir; rapora/makaleye caveat'larıyla işlenmeli.
5. **GRSL letter** — [docs/paper-roadmap.md](docs/paper-roadmap.md).
6. Uzun kuyruk: [docs/open-items.md](docs/open-items.md).

---

# Devralan için: ne yapıldı, ne bulundu, nerede duruyor

*Bu bölüm 30 Ağustos 2026'da, stajın bitiminde yazıldı. Teknik belgeler İngilizcedir;
bu rehber Türkçedir çünkü onu okuyacak kişi Türk olacak.*

## 1. Bu nedir

OpenStreetMap vektörleri ile CLC+ arazi örtüsünden, **10 m çözünürlükte, georeferanslı
sentetik uydu görüntüsü** üreten bir zincir ve onu QGIS içinden çalıştıran bir eklenti.
Üretici, pix2pix koşullu GAN'ının GenCP (Telespazio) HR sürümünden türetildi ve Türkiye
verisiyle ince ayara tabi tutuldu.

Amaç, görüntü eşleştirmede **referans** olarak kullanılmaktı: elinizde georeferansı
şüpheli bir görüntü varsa, aynı alanın sentetik referansına karşı eşleştirip düzeltirsiniz.

## 2. Ne bulundu — olumsuz sonuçlar dâhil

**Bunları okumadan devam etmeyin.** Üçü de ölçüldü, üçü de ürünün aleyhine, ve üçü de
kayda geçirilmiş tahminlere karşı puanlandı. Yeniden keşfetmeyin; daha kötüsü, tersini
varsaymayın.

**2.1 Erişilebilirlik boşluğu yok.** Tez şuydu: "gerçek görüntü her zaman bulunmaz, bizimki
bulunur." Ölçüldü: **24 uzamın 24'ünde** kullanılabilir, bulutsuz Sentinel-2 sahnesi vardı;
ortanca uzamda **2 gün** öncesine ait, en kötüsünde 17 gün. Boşluk yok.
→ `docs/positioning-results.md` (E1)

**2.2 Güncellik boşluğu da yok.** Tez şuydu: "OSM bugünkü yolu bilir, 2021 görüntüsü
bilmez." Ölçüldü: **yüksek değişimli karolarda bile** 2021 tarihli gerçek görüntü,
güncel OSM'den üretilmiş sentetik referansı yendi.
→ `docs/positioning-results.md` (E2, E3)

**2.3 Gerçek görüntü, 10 m'de sentetiği yener — açık farkla.** Ayrık kıyas kümesinde
ortanca eşleştirme hatası: gerçek Sentinel-2 (başka tarih) **0,033 piksel**, GenCP C2
**0,541 piksel**. On altı kat.
→ `docs/T1-benchmark-results.md`

**Peki neden devam edildi?** Çünkü kayıtlı karar kuralı "koşullu" verdi ve koşulu
adlandırmayı şart koştu. Koşul şudur: **sentetik referans, gerçek seçeneklerin gerçekten
bulunmadığı yerde doğru seçimdir.** Uygulamada bu, **çevrimdışı ve uçuş sırasında (on-board)**
kullanımdır: arşiv sorgulayamayan, indiremeyen, yalnızca yanında taşıdığı veriyle çalışması
gereken bir sistem. Orada 0,541 piksel, "referans yok"un alternatifidir — 0,033 pikselin
değil.

Bu ayrımı sunumda ve makalede koruyun. Ürünü "gerçek görüntüden iyi" diye sunmak, elimizdeki
ölçümlerin söylemediği bir şeydir.

## 3. Her şey nerede

| Ne | Nerede |
|---|---|
| Kod, eklenti, korpus zinciri | `mvy0502/GenCP`, dal `tubitak-tr` — **çalışılan depo** |
| Kayıtlar, sonuçlar, kanıt | `mvy0502/gencp-validation` — **devir kopyası, asla kaynak değil** |
| Makale | `mvy0502/gencp-letter` (özel) |
| Veri | `tubitak/data/` — tamamı `.gitignore`'da, hiçbiri depoda değil |
| Yayımlanmış varlıklar | gencp-validation sürüm sayfaları: eklenti zip'i, model, Türkiye OSM, Türkiye CLC+ |
| Kanıt yedeği | Kaggle, dört önekli arşiv — `docs/evidence/BACKUP.md` |

**Kaggle'a bilerek yedeklenmeyenler:** kurumsal (TÜBİTAK) görüntüler ve Google Earth
görselleri. Bunlar depoya da, veri kümesine de, yayımlanan hiçbir artefakta da girmez.
Bu bir tercih değil, kuraldır — `CLAUDE.md`.

## 4. Nasıl çalıştırılır

`tubitak/qgis_plugin/QUICKSTART.md`. Burada tekrar etmiyorum; orası günceldir ve temiz bir
profilde baştan sona izlenerek doğrulandı. Özet: eklenti zip'i + model + Türkiye CLC+
indirilir, OSM verisini eklentinin kendi düğmesi indirir. Hesap açmak, veri kırpmak
gerekmez. Toplam 1,78 GB.

## 5. Sayılar ne anlama geliyor

**Güven bantları.** Her piksel için kırmızı/turuncu/yeşil. Bantlar 150 karoluk **ayrık
Avrupa** kümesinde, C2 kolunda ölçüldü; ortanca eşleştirme hataları kırmızı 3,31 px,
turuncu 2,63 px, yeşil 1,33 px. Spearman rho −0,76; eşleşen nokta sayısı sabit tutulduğunda
−0,38.

**Kırmızı ne iddia eder:** "bu bölge girdiye az dayanıyor, eşleştirmede kullanmayın."
Bir hata payı vermez, bir olasılık vermez. Sıralama iddiasıdır.

**Türkiye'ye taşınırken:** aynı sınırlar 130 karoluk Ankara kümesine değiştirilmeden
uygulandığında sıralama korunur, ayrışma artar (5,2 kat / 2,5 kat), kırmızı bandın mutlak
değeri %7 içinde kalır; turuncu ve yeşil Türkiye'de daha düşük çıkar.
→ `docs/confidence-transfer-results.md`

**İstanbul sonucu (30 Ağustos 2026).** 567 karo, 640 m bindirme, C2, ülke OSM dosyası.
Güven payları: tüm çıktı dikdörtgeninde yeşil %55,4 / turuncu %5,8 / kırmızı %38,8;
geçerli veri ayak izinde %59,0 / %5,9 / %35,1; **ayak izi içindeki karada %85,7 / %8,2 /
%6,0**. Kırsal Ankara karosunda %29,6 / %29,0 / %41,4.

Üç sayının farkı önemlidir: dikdörtgen, sahnenin döndürülmüş ayak izinin dışındaki siyah
dolguyu ve Marmara'yı içerir. **Karadaki pay, aracın yoğun kentte ne yaptığını gösteren
sayıdır.**

## 6. Bilinen sınırlar — ve neden öyle bırakıldılar

**6.1 `class_map`'te bina sınıfı yok.** Güven modülü, 22 renkli üst-akış paletine karşı
sınıflandırır; rasterizer bina rengini (165,42,42) paletin üstüne ekler. Bir bina pikseli
en yakın komşusuna, yani **`red_road`**'a (104,8 DN uzakta) atanır. Sonuç: `conf_D` yoğun
yapılaşmayı yol-yoğunluğundan ayıramaz.

*Bantlar yine de geçerlidir*, çünkü kalibrasyon **aynı eşlemeden** geçti; skor uçtan uca
tutarlıdır. Değiştirmek, yeniden kalibrasyon demektir — 150 karoluk Avrupa kümesinde,
baştan. Bu yüzden bırakıldı. Kullanıcıya gösterilen bina sayacı ayrı düzeltildi
(`confidence.building_mask`), o `class_map`'ten geçmez.

**6.2 Gate R'nin kanıtlamadığı şey.** Gate R, eklentinin rasterizer'ının **bu projenin
kendi** araştırma zinciriyle bayt-bayt aynı olduğunu kanıtlar. Üst-akış GenCP ile
karşılaştırma kapsamında hiç olmadı — ve fark tam oradan girdi: **üst-akışın HR paleti bina
sınıfı içermez**, bizimki ekler. Ön-eğitimli taban bu rengi hiç görmedi; ince ayarlanmış
kollar gördü, çünkü eğitim girdileri aynı `make_chip`'ten geçiyor.
→ `docs/plugin-gate-registrations.md`

**6.3 Paralel üretim QGIS içinde çalışmaz.** Dışarıda çalışır (2,80 dk / 4,67 dk). İçeride
iki sebeple çalışmaz: `spawn`, `sys.executable`'ı yeniden çalıştırır ve QGIS içinde bu QGIS
uygulamasının kendisidir; ve `osmium`, macOS'ta QGIS'in paket python'undan içe aktarılamaz
(onnxruntime'da belgelenen imza ayrımının aynısı). Eklenti bunu 200 ms'de sınar ve seri
moda düşer. Düzeltmek isteyen: QGIS'in python'una osmium'u kurmak ilk denenecek şeydir.

**6.4 Denenmemiş ortamlar.** QGIS 3.x için kod uyumlu yazıldı ama **hiç çalıştırılmadı**.
Windows hiç denenmedi. Doğrulanan tek ortam QGIS 4.2.1 / macOS'tur.

## 7. Tasarlandı ama çalıştırılmadı

Her biri, yeniden tasarlamaya gerek kalmadan devralınabilecek kadar yazıldı.

**7.1 Arazi gölgesi girdi kanalları.** DEM + güneş açısından hesaplanan gölge maskesini
modele ek kanal olarak vermek. Tasarım hazır. **Bina gölgesi elde edilemez** — OSM'de
Türkiye için bina yüksekliği kapsaması seyrek; bu bir uygulama eksiği değil, veri
sınırıdır ve tasarımda böyle kayıtlıdır.

**7.2 OSM tavanı ölçümü.** "Model ne kadar iyi olursa olsun, OSM'in kendisi ne kadar
bilgi taşıyor?" sorusunun ölçümü. Üst sınırı verir; modeli iyileştirmenin ne zaman
anlamsızlaştığını söyler.

**7.3 Maskelenmiş çekişmeli kayıp (masked adversarial loss).** C4/C5 kollarında çekişmeli
terim bütün karoya uygulandı. Yalnızca OSM'in bilgi taşıdığı bölgelere maskelemek,
kayıtlı ama çalıştırılmamış bir varyanttır.

**7.4 Avrupa kol karşılaştırmasının eşit-sayılı yeniden puanlanması.** Ortak destek
denetimi Ankara'da yapıldı; **Avrupa korpusuna uygulanmadı**. C2'nin C1'e üstünlüğü
(1,9802 px / 2,5329 px) eşit olmayan nokta sayıları üzerinden hesaplandı (74 / 52).
Bu sayı bu yüzden bir üst sınır gibi okunmalıdır. Denetim yapılana kadar kesin değildir.

## 8. Bu proje nasıl çalıştı, ve neden

`CLAUDE.md`'deki duran uygulamalar. Her biri bir sessiz hatanın kalıntısıdır — yaklaşık on
iki tanesi yakalandı. Kodu bu uygulamalar olmadan devralan biri aynı sınıftan hataları
yeniden üretir.

| # | Uygulama | Doğuran hata |
|---|---|---|
| 1 | Her kayıt bir değişmezlik bölümü içerir | Neyin sabit kaldığı yazılmadığı için bir sonuç yorumlanamadı |
| 2 | Her sayının çıkarım yolu belirtilir | Farklı yollardan iki sayı karşılaştırıldı |
| 3 | Tek işaret uzlaşımı, yazılı | Rapor ortasında işaret döndü |
| 4 | Tahminler sonuçtan önce kaydedilir | Sonucu görüp ölçüt seçmek |
| 5 | Kayıt metni korpusu ve dizini adıyla anar | Yanlış dizin adı bir gate'i düşürdü |
| 6 | Düşen gate raporlanır, ayarlanmaz | Parametre oynatarak geçirme isteği |
| 7 | Uzun koşular kontrol noktalıdır | Canlılık varsayıldı, ölçülmedi |
| 8 | Paket sonunda açık maddeler gözden geçirilir | Unutulan iş |
| 9 | Tohum ve kütüphane sürümleri kaydedilir | Kayıt A'nın stokastik kolu birebir yeniden üretilemiyor |
| 10 | Her doğrulayıcı bozuk girdilere karşı da denenir | 23 doğrulayıcının 18'i hiçbir şeye bakmadan "geçti" dedi |
| 11 | **Bir denetim, düşen bir vakayla doğar** | Son dört denetimin üçü hiçbir şey yakalayamazdı |
| 12 | **Birim varsayan kod, birimi varsaydığı yerde sınar** | Dört hata, tek cümle: metre varsayan kod coğrafi KRS ile karşılaştı |

En pahalı ikisi, 10 ve 11'dir. Bir denetimin kendisinin bozuk olması, denetimsiz olmaktan
kötüdür: yanlış bir güven verir.

## 9. İlk gün ne yapmalı

1. `QUICKSTART.md`'yi temiz bir profilde uçtan uca izleyin. Çalışmıyorsa belge yanlıştır,
   siz değil — düzeltin.
2. `tubitak/tests/` altındaki gate'leri çalıştırın. Hepsi geçmeli. Geçmiyorsa önce onu
   çözün; hiçbir sayı o noktadan sonra güvenilir değildir.
3. Bölüm 2'yi bir kez daha okuyun. Projenin en pahalı bilgisi oradadır ve olumsuzdur.


---

# Proje 2 — Sentinel-2 süper çözünürlük (`tubitak/sr/`)

*Bu bölüm 31 Ağustos 2026'da eklenmiştir. Yukarıdaki bölümler Proje 1'i (sentetik referans)
anlatır; burası ayrı bir iş koludur ve `tubitak/sr/` altında durur.*

## P2.1 Bu iş kolu nedir

Sentinel-2 görüntüsünü **süper çözünürlüklendiren (super-resolution)** bir QGIS eklentisi ve
onun ölçüm zinciri geliştirilmiştir. Eklenti üç yöntem sunar: **bikübik (bicubic)** kontrol,
bu çalışmada eğitilen **GenCP SR** modeli ve referans olarak alınan **wsx4** modeli
(Evoland/CESBIO).

İş kolunun asıl sorusu piksel benzerliği değildir. Süper çözünürlüğün **görüntü eşleştirmeyi
(image matching)** gerçekten iyileştirip iyileştirmediği ölçülmüştür; bir geometrik referansın
varlık nedeni budur.

## P2.2 `tubitak/sr/` içinde ne var — modül modül

| Dizin | İçerik | Not |
|---|---|---|
| `sr_core/` | Kiremitleme (tiling), birleştirme (mosaic), ızgara sözleşmesi (grid contract), bikübik büyütücü | **Dondurulmuştur.** QGIS'ten bağımsızdır; `test_no_qgis_imports.py` bunu sınar |
| `sr_plugin/` | QGIS eklentisi: diyalog, `QgsTask`, Türkçe metinler, ONNX büyütücü | **Dondurulmuştur.** Zip'e paketlenirken `sr_core` içine gömülür (vendoring) |
| `sr_data/` | Korpus üretimi, Wald bozundurması (degradation), bulut maskesi, bölünmeler (splits), metrikler | `degrade.py` tek gerçek bozundurma uygulamasıdır; kopyalanmaz, içe aktarılır |
| `sr_train/` | Eğitim, değerlendirme, ONNX dışa aktarımı, kontrol kolu, varyant yapılandırması | `config.py` `GENCP_SR_VARIANT` ile x2/x4 arasında geçiş yapar |
| `sr_match/` | WP8 eşleştirme deneyi: dört kol, KLT ölçümü, kırpma kenarlı wsx4 koşusu | `karios` ortamında çalıştırılır (tek `cv2` bulunan ortam) |
| `tests/` | Gate S, kiremit eşdeğerliği, eklenti koruyucuları (guards), QGIS-içe-aktarma sınaması | Her biri bilinen-doğru ve bilinen-yanlış vakayla koşar |
| `docs/` | On altı rapor: `00-recon`'dan `09-devir`'e | Her paket önce kayıt (registration), sonra ölçüm |

## P2.3 Depoda bilerek bulunmayanlar ve nasıl elde edilecekleri

Hiçbir veri deposunda tutulmaz; tamamı `.gitignore` kapsamındaki `tubitak/data/` altındadır.
Aşağıdaki her satır, ilgili varlığın **tam olarak nasıl yeniden üretileceğini** verir.

**1. Yansıtma (reflectance) bantları — B02, B03, B04, beş granül.**
Kamuya açık `sentinel-cogs` S3 kovasından indirilir; kayıt gerekmez:
| | |
|---|---|
| S3 kovası | `sentinel-cogs`, bölge `us-west-2` |
| Nesne anahtarı (key) | `sentinel-s2-l2a-cogs/36/<band>/<square>/<year>/<month>/<item-id>/<BAND>.tif` |

Köşeli parantezli alanlar doldurulmalıdır; tam adres bu ikisinin birleşimidir.
Kalıp bilerek tek parça bir adres olarak yazılmamıştır: bağlantı denetleyicisi
(`tubitak/tests/check_links.py`) bir kalıbı gerçek bir bağlantıdan ayıramaz ve
her koşuda yanlış bir ölü bağlantı bildirirdi.
Beş ürünün kimlikleri (`item-id`) `docs/02a-reflectance-corpus.md` §1'de tam olarak
yazılıdır ve indirilen dosyalar ETag ile doğrulanmıştır. `tubitak/data/s2_reflectance_l2a/`
altına yerleştirilmelidir.

**2. B08 (NIR) bandı.** Aynı kova, aynı desen, `B08` bandı ile. `tubitak/data/s2_b08/`
altına yerleştirilmelidir.

**3. Wald korpusu (x2, üç bant).** Şu şekilde üretilir:
```
python -m sr_data.build_corpus
```
`tubitak/sr/` dizininden çalıştırılmalıdır. Sonuç: `tubitak/data/sr_wald_corpus/`.

**4. Düzeltilmiş bölünme (v2).** Granüller arası sızıntı (leak) giderilmiş bölünme:
```
python tubitak/sr/sr_train/split_fix.py
```
Sonuç: `tubitak/data/sr_wald_split_v2/`.

**5. Dört bantlı korpus (x4).** B08, mevcut çiplere eklenir:
```
python tubitak/sr/sr_train/join_b08.py
```
Sonuç: `tubitak/data/sr_wald_corpus_x4/` (5.531 çip, 2,9 GB).

**6. Model ağırlıkları.** Depoda tutulmaz, sürüm sayfasına eklenir. Yeniden eğitim:
```
GENCP_SR_VARIANT=x4 python tubitak/sr/sr_train/train.py --steps 20000 --batch 32 \
    --budget-min 60 --run tubitak/data/sr_train_runs_x4/run1
GENCP_SR_VARIANT=x4 python tubitak/sr/sr_train/export_onnx.py \
    --ckpt tubitak/data/sr_train_runs_x4/run1/best.pt \
    --out tubitak/data/plugin_models/gencp_sr_x4_b4.onnx --schedule 20000
```
x2 modeli için `GENCP_SR_VARIANT` değişkeni verilmez; öntanımlı değer WP3B'nin
yapılandırmasıdır.

**7. wsx4 ağırlıkları.** Bu çalışmanın ürünü değildir ve **hiçbir sürüme eklenmez.**
Üst kaynaktan alınmalıdır: `https://github.com/Evoland-Land-Monitoring-Evolution/sentinel2_superresolution`.
`wsx4_spatrad.onnx` ve yanındaki `wsx4_spatrad.yaml` birlikte indirilmeli ve aynı dizine
konulmalıdır; eklenti `.yaml` dosyasını modelin yanında arar ve ölçek, normalleştirme ile
kırpma kenarını oradan okur.

**8. Gösterim (demo) girdileri.** Şu şekilde üretilir:
```
python tubitak/sr/sr_train/make_model_input.py
```
Sonuç: `tubitak/data/sr_model_input/`.

## P2.4 Dondurulmuş dizin uzlaşımı ve gerekçesi

**`tubitak/sr/sr_plugin/`, `tubitak/sr/sr_core/`, `tubitak/qgis_plugin/` ve
`tubitak/gencp_core/` dondurulmuştur.**

Gerekçe, kod kalitesi değildir: **4 Eylül 2026 gösterimi, öntanımlı (default) QGIS profiline
kurulu eklenti üzerinden yapılacaktır.** Bu dört dizindeki bir değişiklik, gösterimin
dayandığı davranışı sınanmamış biçimde değiştirir. Paketleme kusuru veya mutlak yol (absolute
path) bulunsa dahi düzeltilmez; **bulgu olarak raporlanır.** Zip'in kurulmaması gösterimi
etkilemez, çünkü gösterim zip'ten değil kurulu eklentiden çalışır.

Bir dosyanın silinmesi veya taşınması söz konusu olduğunda `CLAUDE.md`'deki kural geçerlidir:
**bu depoda o dosyayı okuyan bir şey var mı?** Varsa kalır.

## P2.5 Bu projenin tekrar ürettiği iki hata biçimi

Devralan kişi bu ikisiyle karşılaşacaktır. İkisi de tavsiye değil, ölçülmüş vakadır.

### P2.5.1 Öntanımlı değeri bir modül sabitine bağlı parametre

Bir fonksiyon `scale=SCALE` biçiminde bir öntanımlı değer alır; `SCALE` modül düzeyinde
`params.SCALE`'dir ve değeri 2'dir. Ölçek 4 ile çalışan bir çağrı parametreyi geçmezse,
**hata vermeden 2 ile çalışır.**

Bu tek cümle bu projede **yedi kez** gerçekleşmiştir. Belgelenmiş örnekler:

| Nerede | Ne yaptı | Nasıl yakalandı |
|---|---|---|
| `train.py`, `evaluate.py` | `degrade_chip` ölçeksiz çağrıldı; ölçek 4 modeline 128 piksel girdi verildi | kayıp fonksiyonunda boyut çakışması |
| `corpus_checks.c4` | `mtf_at` ölçeksiz çağrıldı; ölçek 2 süzgeci ölçek 4 Nyquist frekansında değerlendirildi, kayıtlı 0,3 yerine 0,7401 çıktı | C4 denetimi düştü |
| `gaussian_decimation_kernel` | Aday pencere blok merkezi yerine sıfır etrafında kuruldu; ölçek 4'te her bozundurulmuş girdiye **−0,0011 piksel** kayma gömüldü | X3 denetimi düştü |
| `evaluate.CAVEAT`, ONNX `caveat`, `output_layout` | Ölçek 4 modelinin içinde "ikiye bölme", "5 m" ve "2x spatial" metinleri taşındı | çıktı okunarak |
| `gencp_core/extent.py:65` | `from rasterio.crs import CRS` **modül düzeyinde**; rasterio'su olmayan bir QGIS'te diyalog hiç açılmadı, kullanıcı yığın izi gördü | kurumun QGIS 3.40 makinesinde, `12-qt5-uyumluluk.md` |
| `build_corpus`'un nodata kuralı | "herhangi bir bant 0 ise reddet" uint16 için yazılmıştı; 8 bit TCI'de karanlık **araziyi** reddetti, 36SXJ'de 1008 çipin 954'ünü gereksiz yere | `13-tci-model-v2.md` |
| `mtf_at`, `degrade_chip` ölçeksiz çağrıldı | ölçek 2 varsayılanıyla ölçek 4 işi yapıldı | `07-x4-registration.md` §11.1 |

Sonuncusu en pahalısıdır: kapsam uyarısının sayıyla birlikte taşınması **kural olarak
konulmuştu**, uyarı da taşındı — ancak sabit yazılmış (hard-coded) biçimde. O metin
`metadata_props` içinde, yani **eklentinin kullanıcıya gösterdiği yerde** durur.
**Yalan söyleyen künye (provenance), künyesizlikten kötüdür.**

Korunma yolu: birim veya ölçek varsayan kod, varsaydığı yeri sınamalıdır. `vectors.require_metric`
ve `sr_train/data.assert_band_order` bu amaçla yazılmıştır.

### P2.5.2 Düşemeyen doğrulayıcı

Hiçbir şeye bakmadan "geçti" diyen bir denetim, denetimsizlikten kötüdür: yanlış güven verir.

| Vaka | Ölçüm |
|---|---|
| Proje 1 doğrulayıcı denetimi | 23 doğrulayıcının **18'i** bozuk çağrılarda 0 ile çıktı |
| X5 bant sırası denetimi | `assert_band_order` **tanımlanmış ama hiçbir yerden çağrılmamıştı** |
| WP9 mutlak yol denetimi | `zsh` değişken bölmesi (word splitting) nedeniyle `grep` tek bir dosya adı aldı; denetim **hiçbir dosyaya bakmadan** "temiz" dedi |
| `leakage.py`'nin KF2 vakası | Beklenen değer **47**, yansıma korpusunda ölçülmüş bir sabitti. Korpus değişince "bana ait değil" demek yerine **FAILED** dedi ve temiz bir bölünme için karar vermeyi reddetti | `13-tci-model-v2.md` §3.1 |
| `check_links.py` | Adres **kalıbını** gerçek bağlantıdan ayıramaz; her koşuda yanlış bir ölü bağlantı bildirir | `09-devir.md` |

**Genel biçim, WP13'te kaydedilmiştir: çıplak bir sabit olarak yazılmış beklenen değer,
korpus değiştiği anda sessizce sınanamaz hâle gelir.** Uygulanmadığını duyurmaz; başarısızlık
bildirir - bu daha kötüdür, çünkü boş yere uyaran bir denetim, insanların atlamayı öğrendiği
denetimdir. Çözüm: beklenen değer, ölçüldüğü korpusun kimliğiyle birlikte taşınır
(`leakage.py`, `KF2_EXPECTED`).

Sondan bir önceki vaka bu belgeyi yazan oturumda olmuştur ve yalnızca **bilinen-doğru vakasının da
başarısız olması** sayesinde fark edilmiştir. Kural bu yüzden şudur: **bir denetim, düşen bir
vakayla birlikte doğar.** Önce bulunması gereken bir şey aranmalı, denetimin onu bulduğu
görülmeli, ancak ondan sonra "bulamadı" sonucuna güvenilmelidir.

## P2.6 Açık maddeler — her biri kaynağı olan raporla

| # | Madde | Kaynak |
|---|---|---|
| 1 | ~~Eğitim süreci son `last.pt` yazımında dört koşunun dördünde de kilitlendi~~ **KAPANDI (WP16).** Sebep: döngü kırılırken tüketilmeden kalan bir `.to(device, non_blocking=True)` kopyası askıda bırakılıyor; `torch.save` sonra MPS deposunu ana belleğe kopyalarken bloke oluyor. Çözüm: kaydetmeden önce `torch.mps.synchronize()`. Askıda kopya varken **dört elemanlı** bir MPS tensörünü kaydetmek bile kilitleniyor | `16-checkpoint.md` §2 |
| 2 | Sonda (probe) sürdürülebilir hızı **dört koşuda da** olduğundan yüksek gösterdi (0,51 / 0,60 / 0,71 / 0,63). Marj kuralı işe yarıyor; sebep ölçülmedi | `11-zamanlama.md` §5 |
| 3 | ~~wsx4 çıktısının çeyrek piksel kayması atfedilmemiştir~~ **KAPANDI — ATFEDİLDİ (WP16).** Kayma **modelin kendisine aittir.** Kendi araçları (`--l1c`), kendi ürünleri, kendi bicubic çıktıları üzerinde ölçüldü; bizim ızgaramız ile onlarınki **0,0015 piksel** içinde uyuşuyor. Ölçüm bizim 36SXJ granülümüzle **aynı datatake** (A009000) üzerinde yapıldı. Bizim dikişimiz aklandı | `17-wsx4-hizalama.md` §4 |
| 3a | **Yeni açık soru — WP8'in "yalnızca y ekseni" okumasının yerine geçer.** Kendi doğal ölçeğinde kayma **her iki eksende** ve yaklaşık eşit (dx −0,2022, dy −0,2299); WP8 ise 40 m → 10 m denemesinde dx +0,032 ölçmüştü. İki deney **aynı anda birçok bakımdan** farklıdır (40 m → 10 m ile doğal 10 m → 2,5 m; L2A BOA ile L1C TOA; bizim dikişimiz ile onların döşemesi), bu yüzden **çelişkinin kendisi de atfedilebilir değildir** | `17-wsx4-hizalama.md` §5 |
| 3b | **Kayıt: WP16 brifingindeki "iki arıza muhtemelen aynıdır" varsayımı ölçümle çürütülmüştür.** `TorchVersion` nesneleri taşıyan bir yük **kilitlenmeden kaydedilir**, ve kilitlenen dosya `last.pt`'nin içinde `versions` anahtarı hiç yoktur. İki bağımsız arızadır ve iki ayrı düzeltme gerektirmiştir. Bir sonraki okuyucu aynı varsayımı tekrarlamasın | `16-checkpoint.md` §giriş |
| 4 | Eşleştirme tek bant (B04), tek dedektör (KLT), tek granül (36SXJ) ile ölçülmüştür | `08-eslestirme.md` §14 |
| 5 | SSIM yalnızca kendi uç değerlerine karşı doğrulanmıştır | `03b-training.md` §7 |
| 6 | **QGIS 3.40 hiç çalıştırılamadı** — qgis.org'dan indirilemiyor. Sınanan: 4.2.1 ve 3.44.13, yalnızca macOS. **Windows ve Linux sınanmamıştır** | `12-qt5-uyumluluk.md` §5 |
| 7 | Gömülü `onnxruntime`'ın Windows'ta yerel DLL'lerini yükleyip yükleyemediği **sınanmamıştır**; Katman 2'nin tamamı buna bağlıdır | `13-cevrimdisi-kurulum.md` §9 |
| 8 | `coverage_block.py` çalıştırılamıyor: gerektirdiği üç OSM çıkarımı hiçbir belgede adlandırılmamış | `tubitak/docs/open-items.md` madde 27 |
| 9 | Qt5'te karanlık tema yakalama hatası teşhis edilmedi; açık hipotez ölçülüp **çürütüldü** | `12-qt5-uyumluluk.md` §2.2 |
| 10 | EOX'un ton eğrisi sorusu **çözülmemiştir**; aynı tarihli bir Exploitation karosu gerekir | `11-eox.md` §14 |
| 11 | Düzeltilmiş nodata kuralı hâlâ tek tek siyah pikselleri nodata sayıyor (36SXJ'de 54 çip) | `13-tci-model-v2.md` §10.4 |
| 12 | Ölçek-4 çekirdeğinin ayrık MTF'si **ölçülmüştür (0,299975794)** ama hiçbir denetim bunu doğrulamaz. C4 yalnızca `C.SCALE`'deki çekirdeği sınar, denetimler de x4 varyantında corpus uyuşmazlığı nedeniyle çalışmayı reddeder | `15-kontroller.md` §10 madde 1 |
| 13 | **C2 ve C3 ölçek-4 corpus'unda hiç çalıştırılmamıştır**: `sr_wald_corpus_x4` içinde `manifest.csv` yoktur. Bu corpus'un ayrım (split) yalıtımı tek başına **D18**'e dayanır — bulut/gölge taraması ve tampon mesafesi bağımsız olarak doğrulanmamıştır. **16 bitlik ürün geldiğinde ve `gencp_sr_x4_b4.onnx` gerçek kullanıma girdiğinde ilk yapılacak iş budur** | `15-kontroller.md` §10 madde 2 |

## P2.7 Elde tutulan üç model, ve sayıların kapsamı

**Kurum bugün 8 bit RGB görüntü tutmaktadır; 16 bit dört bantlı ürün sonra alınacaktır.**
Her iki katman için birer model vardır.

| Model | Ölçek | Bant | Normalleştirme | Hangi katmana uyar |
|---|---|---|---|---|
| **`gencp_sr_tci_x4_b3_v2.onnx`** | ×4 | 3, `B02,B03,B04` | `DN/255` | **kurumun bugün tuttuğu 8 bit RGB** |
| **`gencp_sr_x4_b4.onnx`** | ×4 | 4, `+B08` | `DN/10000` | **16 bit yansıma katmanı, geldiğinde** |
| `gencp_sr_x2_v1.onnx` | ×2 | 3 | `DN/5000` | daha eski üç bantlı yansıma çalışması |

**Kapsamı belirtilmemiş bir sayı bu belgeye girmez.** Projenin varlık nedeni olan sonuç:

> Ayrık tutulan **36SXJ** granülünde, **1628 çipte**, **40 m → 10 m** dönüşümünde, gerçek
> Sentinel-2'ye karşı ölçülmüş: 8 bit model, bikübiğin **3,94 katı** kullanılabilir kontrol
> noktası üretir (çip başına 491,3 / 124,6 RANSAC iç noktası) ve eşleştirme hatasını
> **%40** azaltır (0,592 / 0,984 piksel). **1628 çipin hepsinde** bikübikten iyidir.

Piksel benzelirliği, aynı granül, kayıtlı bikübik kontrole karşı eşli fark: 8 bit model
**+3,520 dB** (0/1628 çipte kötü), dört bantlı model **+2,971 dB** (1/1332).

**Bu iki sayı birbiriyle karşılaştırılamaz**: farklı ürün, farklı bölen, farklı korpus.

**Bu sayıların hiçbiri eklentinin normal kullanımdaki 10 m → 2,5 m dönüşümüne ait değildir**;
orada karşılaştırılacak bir gerçek referans yoktur. Kendi uyguladığımız bir bulanıklığı geri
çevirmekte bikübiği yenmek, gerçek görüntüyü süper çözünürlüklendirmekle aynı iddia değildir.

### Kurulum

Gereken her şey, kurulumun kurumun kendi verisi olmadan doğrulanabilmesi için iki örnek raster
dâhil, tek sayfadadır — toplam **8,1 MB**, aktarım sonrası doğrulama için `SHA256SUMS.txt` ile:
<https://github.com/mvy0502/gencp-validation/releases/tag/sr-plugin-v0.1.0>

İnternetsiz makineler için adım adım: [`sr/docs/10-kurulum.md`](sr/docs/10-kurulum.md) §7.

## P2.8 İndirme adresleri — hangi belge yetkilidir

**Deponun kök `README.md` dosyasındaki indirme tablosu tek doğru kaynaktır.** Başka hiçbir
belge bu tabloyu kopyalamamalıdır; kopyalanan tablo güncelliğini yitirir ve hangisinin doğru
olduğu belirsizleşir. Bu, ölçülmüş bir sorundur: `QUICKSTART.md` tablonun ikinci bir kopyasını
taşıyordu ve iki satırı (zip boyutu 89 KB, gerçekte 94.987 bayt; silinmiş bir sürüm etiketine
bağlantı) yanlıştı.

Diğer belgeler yalnızca **işaret eder**:

| Belge | Ne içerir |
|---|---|
| kök `README.md` | **Tablo.** Dosya adı, bayt cinsinden boyut, ne işe yaradığı, sabitlenmiş (pinned) indirme adresi |
| `tubitak/qgis_plugin/QUICKSTART.md` | Yalnızca iki sürüm etiketi adresi — zip'in içinden okunduğunda depoya erişimi olmayan biri dosyalara ulaşabilsin diye. Tabloyu kopyalamaz |
| `tubitak/sr/docs/10-kurulum.md` | Kurulum adımları; dosya satırları README'den alınmıştır ve çelişki hâlinde README geçerlidir |

### Sürüm etiketleri ve neden üç tanedir

| Etiket | İçerik | Ne sıklıkla değişir |
|---|---|---|
| `plugin-v0.2.0` | Proje 1 eklentisi ve model ağırlıkları. **`latest` olarak işaretlidir** | Sık |
| `sr-plugin-v0.1.0` | Proje 2 eklentisi ve iki modeli | Sık, Proje 1'den bağımsız |
| `veri-turkiye-2026-08-31` | CLC+ Türkiye kırpması ve Türkiye OSM çıkarımı | Seyrek |

İki eklenti bağımsız sürüm alır ve **birleştirilmemelidir**: birleştirilirse birinin her
düzeltmesinde diğerinin dosyaları da yeniden yüklenir. Veri ayrı bir etikettedir çünkü her
iki eklenti de onu kullanır ve bir diyalog düzeltmesi için 1,5 GB'ın yeniden yüklenmesi
gerekmemelidir.

Veri etiketi ve Proje 2 etiketi **bilerek `latest` değildir**; `releases/latest/download/...`
adresleri Proje 1'in dosyalarına çözümlenmelidir.

### `osm-turkey-2026-08-19` etiketi neden hâlâ duruyor

Bu etiket bir uyumluluk kopyasıdır ve insanlar için değildir.
`tubitak/gencp_core/geofabrik.py` içindeki `MIRRORS["turkey"]` tam olarak o adresi ve o
dosyanın MD5'ini sabit olarak taşır; Geofabrik yanıt vermediğinde eklentinin indirme düğmesi
oraya düşer. `gencp_core` dondurulmuş bir dizindir, bu yüzden adres koddan değiştirilmemiş,
etiket yerinde bırakılmıştır. **Aynı dosya ayrıca `veri-turkiye-2026-08-31` etiketinde de
bulunur ve ikisi birebir aynıdır.**
