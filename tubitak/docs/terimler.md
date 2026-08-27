# Terim listesi

Kullanıcıya görünen bütün Türkçe metinde bu karşılıklar geçerlidir: eklenti arayüzü,
`QUICKSTART.md`, `DEMO.md`, `gencp-validation` README'si ve sürüm notları.

Ölçüt şudur: **QGIS'in resmî Türkçe yerelleştirmesi neyi kullanıyorsa o.** Kullanıcı
menüde "Katman" görüyorsa belgede de "katman" okumalıdır. QGIS'te karşılığı olmayan
terimler için aşağıdaki ikinci tablo geçerlidir.

## QGIS'ten gelenler

| İngilizce | Türkçe | Not |
|---|---|---|
| layer | katman | |
| raster layer | raster katman | "raster" çevrilmez |
| vector layer | vektör katman | |
| coordinate reference system (CRS) | koordinat referans sistemi (KRS) | Kısaltma QGIS'te KRS |
| extent | kapsam | |
| plugin | eklenti | |
| Plugins > Manage and Install Plugins | Eklentiler > Eklentileri Yönet ve Kur | Menü adı birebir |
| Install from ZIP | ZIP'ten Kur | Menü adı birebir |
| Layer > Add Layer > Add Raster Layer | Katman > Katman Ekle > Raster Katman Ekle | Menü adı birebir |
| Python Console | Python Konsolu | |
| project | proje | |
| Save As | Farklı Kaydet | |
| resolution | çözünürlük | |
| band | bant | |
| symbology | sembol sistemi | QGIS'in kullandığı karşılık |
| legend | gösterim | Katman panelindeki renk açıklaması |
| toolbar | araç çubuğu | |
| progress bar | ilerleme çubuğu | |
| tooltip | ipucu | Arayüzde görünmez; belgede geçerse bu |

## Projeye özgü terimler

| İngilizce | Türkçe | Neden |
|---|---|---|
| tile | karo | Görüntünün bölündüğü kare parça |
| tile overlap | karo bindirmesi | |
| ground sample distance (GSD) | yer örnekleme aralığı | 10 m |
| synthetic reference | sentetik referans | Ürünün adı |
| rasterised OSM input | rasterleştirilmiş OSM girdisi | Modelin gördüğü şey |
| land cover | arazi örtüsü | CLC+ ürünü |
| OSM extract (.osm.pbf) | OSM çıkarımı | Geofabrik dosyası |
| confidence | güven | |
| confidence band | güven bandı | kırmızı / turuncu / yeşil |
| alpha channel | alfa kanalı | |
| matching error | eşleştirme hatası | KARIOS'un ölçtüğü |
| held-out (corpus) | ayrık | "ayrık küme": eğitimde kullanılmamış |
| pre-registered | önceden kayda geçirilmiş | Ölçümden önce yazılıp commit'lenmiş |
| model weights | model ağırlıkları | |
| provenance | künye | Dosyanın içine gömülen üretim kaydı |
| resampled | yeniden örneklenmiş | |
| deterministic | belirlenimci | |
| generator | üretici | pix2pix üreticisi |

## Yazım kuralları

- Kısa cümle. Bir cümlede bir iş.
- Okuyucu meslektaştır: ne "lütfen" ne de öğretmen tonu.
- Sayı ondalığı virgülle: **1,98 piksel**. Dosya adları ve kod içindeki sayılar hariç.
- Yüzde işareti sayının önünde ve bitişik: **%34**.
- Sayıya ek getirmek gerekiyorsa cümleyi değiştir. "%22'si" gibi ekler okunuşa göre
  değişir ve biçimlendirmeyle üretilemez.
- Menü adları QGIS'te göründüğü gibi, **kalın**.
- Dosya adları ve komutlar `tek tırnaklı kod` biçiminde.
- Emoji yok.
