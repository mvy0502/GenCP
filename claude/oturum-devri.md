# Oturum devri

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
> **Bir kaydı (registration) bu depoya işlemeyin.** Tek istisna, eklenti iş paketinin
> kendi kapıları: [plugin-gate-registrations.md](docs/plugin-gate-registrations.md)
> burada kalır, çünkü `tests/gate_r.py` ve `gate_o.py` kayıt belgesi olarak onu
> gösterir.
>
> Tarih yeniden yazılmadı ve yazılmayacak. İki depo 96503b7 birleşme tabanından
> itibaren aynı tarihi paylaşır; araştırma kaydında anılan 49 commit SHA'sının hepsi
> her iki depoda da çözülür. `filter-repo` hiç kullanılmadı.
>
> ### Borçlu olunan tamamlayıcı senkron (top-up sync)
>
> Senkron noktası **`844dbec`**. gencp-validation'a bu noktaya kadar her şey aktarıldı
> (birleştirme commit'i `f9e0de6`, ardından kanıt rasterları `284571b`). Ondan sonra bu
> dalda oluşan commit'ler:
>
> - `f95ad61`, `d393152`, `814f06c` — eklenti iş paketi (Gate R, O, D). Sınıra göre
>   GenCP'de kalır; gencp-validation'a taşınması **gerekmez**.
> - `b815b46` — silme commit'i.
>
> **UYARI, ve bu uyarı en önemli satırdır.** Tamamlayıcı senkron `tubitak-tr` dalının
> birleştirilmesiyle **yapılamaz**. `b815b46` 263 dosyayı siler; bu dal olduğu gibi
> birleştirilirse silme gencp-validation'a yayılır ve araştırma kaydını oradan da
> siler. Aktarılması gereken bir şey çıkarsa **yalnız o commit'ler cherry-pick
> edilmelidir**, dal birleştirilmemelidir.

> **Aşağıdaki 25 Ağustos notundaki `../tubitak/docs/...` bağlantıları artık bu depoda
> çözülmez** — hedefleri gencp-validation'a taşındı. Bağlantılar tarihsel kayıt olarak
> bırakıldı; aynı yollar gencp-validation deposunda geçerlidir.

---

## Oturum devri — 25 Ağustos 2026, ~21:40 +03

## Uçuşta olan

Tek dalga, detached, app `ap-FmfGHSbLiIJJG7LotSbiSP` (14 task: 7 CPU driver + 7 GPU):

- **SEED-c bloğu**: seed 45–50, her driver kendi içinde seri `["C5","C4","C2","C1"]`
  (başlık ayağını koruyan sıra), eğitim `f2dc962` pininde. Beklenen bitiş **~03:15 +03
  (26 Ağu)**. Call id'ler: [seed-block-wave-launch.md](../tubitak/docs/gates/seed-block-wave-launch.md).
- **Warm-up de-confound**: seed 43, `C5_warmup` sonra `C2_warmup`, `a782aa5` pininde.
  Beklenen bitiş **~00:35 +03**. Kayıt:
  [warmup-deconfound-registration.md](../tubitak/docs/warmup-deconfound-registration.md)
  (iki dal da önceden yazıldı; n=1 mekanizma sondası, konfirmatuar değil).

## Blok yapısı (AMENDMENT SEED-c, `9ab599e`)

- Kaggle stage 2 İPTAL; Kaggle bloğu n=2 (43, 44), df=1, t*=12.71, artık tutarlılık
  rolünde. Modal konfirmatuar blok: seed 45–50, n=6, df=5, t*=2.571. Modal seed 43
  gate seed'i olarak HARİÇ (görülmüş gözlem), blok yanında raporlanır.
- Okumalar işaret-replikasyonu (6/6), aralıklar RAPORLANIR ama ŞART DEĞİL.
- Havuzlama yok: donanım gate'i NOT POOLED döndü (hardware-gate-results.md).

## Bütçe durumu (lansman anında panodan okundu)

Kullanım $11.77, tahsilat $0.00; kalan kredi $18.23. Tavan: $50 (30 kredi + $20
merdiven; $40'ta $10 otomatik tahsilat). Kalan iş ~$39 → **~bir kol kadar aşım riski
KABUL EDİLDİ**: tavan vurursa son seed'lerin C1'i kalır (yalnız C1−C2'yi besler),
skip-completed ile 1 Eylül sıfırlamasında kaldığı yerden tamamlanır. $20 spend limit
olduğu gibi kalacak; yükseltme/destek talebi YOK.

## Dalga sonrası yapılacaklar

1. Her seed için: latest_net_G indir (verify_latest ile Modal tarafında latest==20 +
   sha eşleşmesi), dondurulmuş kodla yerel değerlendirme (`seed_eval_run.py --seed S
   --variant modal`), **değerlendirme aşamalarını ZAMANLA ve gates log'una yaz**
   (indirme / inference / warp / KARIOS / edge ratio — repoda hiç ölçüm yok).
2. Driver maliyetlerini panoyla mutabakat et ($1.10/h sabittir, Modal fiyatı değildir);
   farkı launch log'a işle. Her driver bitişinde pano bakiyesini kaydet.
3. Warm-up eğrileri: kayıttaki İKİ DALDAN hangisi — okuma kayıt dokümanındaki tanımla
   (ana aşama 1→2 epoch ortalaması), eğriler görüldükten sonra kural OYNAMAZ.
4. seed_analysis.py Modal bloğu için n=6 ile koşulacak (SEED-c okumaları); Kaggle bloğu
   ayrı raporlanır, hiçbir yerde havuzlanmış istatistik olmaz.

## Değerlendirme kod donması

seed_eval + c45_eval `48ced64`'te sha-pinli (registration'daki tablo). Beş Modal kolu
skorlandı; SEED-c değerlendirmesi başlamadan dondurma kuralı aynen sürüyor: değişiklik
gerekirse önce taze seed-42 gate, sonra her şey yeniden.
