# Oturum devri — 25 Ağustos 2026, ~21:40 +03

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
