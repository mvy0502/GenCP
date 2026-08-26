# Devir rehberi — GenCP TÜBİTAK çalışması

> ## DEPO AYRIMI — 26 Ağustos 2026
>
> **Araştırma işi bu depoda yapılmaz.** 26 Ağustos 2026 tarihinden itibaren:
>
> | Ne | Nerede |
> |---|---|
> | Ön kayıtlar, sonuçlar, denetimler, kanıt artefaktları, düzeltme kaydı | **gencp-validation** — https://github.com/mvy0502/gencp-validation (dal: `main`) |
> | Makale (GRSL letter ve arXiv uzun sürümü) | **gencp-letter** — https://github.com/mvy0502/gencp-letter |
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
