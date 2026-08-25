# Devir rehberi — GenCP TÜBİTAK çalışması

Bu dosya, projeyi devralacak kişinin (yeni stajyer veya proje sahibi) "ne nerede
yapıldı, nasıl çalıştırılır, ne açık" sorularına tek yerden cevap bulması için
yazıldı. Son güncelleme: 25 Ağustos 2026.

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
