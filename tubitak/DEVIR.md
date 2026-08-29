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

