"""Every user-visible string in the plugin, in one place.

The interface is Turkish. Code, comments, commit messages and documentation stay English.
Nothing in dialog.py may contain a Turkish literal; a missing string here is the bug.

`S` holds LABELS - what a widget is called, a couple of words. `TIP` holds TOOLTIPS - the
explanation that used to sit in the dialog as prose. The convention follows Deepness
(PUTvision/qgis-plugin-deepness), whose UI documentation states it plainly: "Almost every
element in UI has its own 'tooltip'". Long-form explanation lives in QUICKSTART.md.

The Turkish here is WRITTEN in Turkish, not translated from English drafts. Terminology is
fixed by tubitak/docs/terimler.md, which takes QGIS's own Turkish localisation as the
authority so the words match the menus the user is already looking at. Conventions from
that file that bite in code: decimal comma, "%34" with the sign in front and no suffix
attached to a numeral (Turkish suffixes follow how a number is READ and cannot be produced
by string formatting).
"""
from __future__ import annotations

LANG = "tr"

S = {
    # ------------------------------------------------------------------ window ----
    "window_title": "GenCP Sentetik Referans",
    "close": "Kapat",

    # ------------------------------------------------------------------- girdi ----
    "sec_input": "Girdi",
    "reference_layer": "Referans katman",
    "extent": "Kapsam",
    "crs": "KRS",
    "tiles_estimate": "Karo / süre",
    "unset": "—",
    "waiting": "<span style='color:gray'>katman seçilmedi</span>",
    "extent_value": "{xmin:.0f}, {ymin:.0f} → {xmax:.0f}, {ymax:.0f}  ({w:.0f} × {h:.0f} m)",
    "tiles_value": "<b>{n} karo</b> · {w} × {h} piksel · yaklaşık {mins:.1f} dk",

    # ------------------------------------------------------------------- model ----
    "sec_model": "Model",
    "model_file": "Model dosyası",
    "model_none": "—",
    "model_desc": "{name} · {mb:.0f} MB · {mtime}",
    "model_calibrated_ok": "<span style='color:gray'>Güven bantları bu dosyada ölçüldü.</span>",
    "model_not_calibrated": ("<b>Güven bantları bu modelde ölçülmedi</b> — ölçüm yalnızca "
                            "{calib} dosyasında yapıldı. Güven katmanı üretilmeyecek."),

    # --------------------------------------------------------------- önizleme ----
    "sec_preview": "Önizleme",
    "preview_button": "Önizlemeyi göster",
    "preview_prev": "◀",
    "preview_next": "▶",
    "preview_rendering": "Önizleme hazırlanıyor…",
    "preview_failed_title": "Önizleme alınamadı",
    "preview_failed": "Önizleme alınamadı: {err}",
    "osm_counts": "Karodaki OSM: {roads} yol · {buildings} bina · {water} su · {landuse} arazi (piksel)",

    "band_red": "Kırmızı — kullanmayın",
    "band_amber": "Turuncu — dikkatli kullanın",
    "band_green": "Yeşil — kullanılabilir",
    "warn_zero_osm": "Bu karoda OSM nesnesi yok. Çıktı yalnızca arazi örtüsünden gelir.",
    "warn_zero_osm_tiles": "{total} karonun {n} tanesinde OSM nesnesi yok. Kaynak: {source}",
    "warn_count_unavailable": "{total} karonun {n} tanesinde nesne sayısı okunamadı.",

    # -------------------------------------------------------------------- çıktı ---
    "sec_output": "Çıktı",
    "out_file": "Çıktı dosyası",
    "out_crs": "Çıktı KRS",
    "out_crs_same": "Referans katmanla aynı",
    "add_layers": "Katmanları haritaya ekle",
    "out_crs_geographic": ("Coğrafi KRS seçtiniz. Üretim yine metrik KRS'de, 10 m'de "
                           "yapılır; yanına yeniden örneklenmiş bir kopya yazılır."),

    # ---------------------------------------------------------------- gelişmiş ---
    "sec_advanced": "Gelişmiş",
    "source_online": "Overpass",
    "source_local": "Yerel .osm.pbf",
    "source": "Veri kaynağı",
    "pbf_file": "OSM çıkarımı",
    "clc_file": "CLC+ rasterı",
    "tile_overlap": "Karo bindirmesi",
    "overlap_suffix": " m",
    "overlap_too_large": ("Karo bindirmesi bir karodan küçük olmalı. Bir karo {limit:.0f} m, "
                          "en büyük geçerli değer {max} m. Girilen: {m} m."),
    "overlap_snapped": ("Karo bindirmesi {m} m'ye çekildi. Değer {step} m'lik piksel "
                        "ızgarasının tam katı olmak zorunda; {typed} m değil."),
    "confidence_alpha": "Güveni alfa kanalına yaz",
    "confidence_band_layer": "Renkli güven katmanı da üret",
    "add_osm_layer": "OSM girdisini katman olarak ekle",

    # ------------------------------------------------------------- çalıştırma ----
    "sec_run": "Çalıştırma",
    "idle": "Hazır",
    "generate": "Üret",
    "cancel": "Vazgeç",
    "running": "Çalışıyor…",
    "cancelling": "Durduruluyor…",
    "cancelled": "Durduruldu. Diske eksik dosya yazılmadı.",
    "stage_render": "Rasterleştiriliyor ({done}/{total})",
    "stage_infer": "Üretiliyor ({done}/{total})",
    "stage_confidence": "Güven hesaplanıyor ({done}/{total})",
    "stage_mosaic": "Birleştiriliyor",
    "stage_unknown": "Çalışıyor ({done}/{total})",
    "failed_title": "Üretim tamamlanamadı",
    "failed": "Üretim tamamlanamadı: {err}",
    "done_wrote": "{name} yazıldı",
    "verdict_line": "Güven — yeşil %{green:.0f}, turuncu %{amber:.0f}, kırmızı %{red:.0f}",
    "verdict_red_warning": ("Çıktının %{red:.0f} kadarı kırmızı bantta. O bölgeleri "
                            "eşleştirmede kullanmayın."),

    # ------------------------------------------------------------------ hatalar ---
    # Her biri ne yapılacağını söyler, neyin bozuk olduğunu değil.
    "err_no_layer": "Referans katman seçin.",
    "err_pbf_empty": "Gelişmiş bölümünden .osm.pbf dosyası seçin ya da Overpass'a geçin.",
    "err_pbf_missing": "OSM çıkarımı yerinde değil: {path}",
    "err_clc_empty": "Gelişmiş bölümünden CLC+ rasterını seçin.",
    "err_clc_missing": "CLC+ rasterı yerinde değil: {path}",
    "err_model_missing": "Gözat düğmesiyle bir .onnx model dosyası seçin.",
    "err_out_missing": "Çıktı dosyası için yol belirtin.",
}

# Arayüzde yer kaplamayan açıklamalar. Uzun anlatım QUICKSTART.md'de.
TIP = {
    "reference_layer": ("Üretilecek alan ve koordinat referans sistemi bu katmandan "
                        "okunur. Katman metrik bir KRS'de olmalıdır; coğrafi KRS'ler "
                        "kendiliğinden UTM'ye çevrilir."),
    "extent": "Referans katmandan okunur, elle girilmez.",
    "crs": ("Üretimin yapıldığı koordinat sistemi. Model 10 m yer örnekleme aralığında "
            "eğitildi, bu yüzden üretim her zaman metrik bir KRS'de yapılır."),
    "tiles_estimate": ("Karo sayısı, çıktı boyutu ve kaba süre. Sürenin çoğu "
                       "rasterleştirmede geçer; model karo başına yarım saniyenin "
                       "altında çalışır."),
    "model_file": ("pix2pix üreticisinin ONNX dosyası. Güven bantları yalnızca "
                   "gencp_C2_fp32.onnx dosyasında ölçüldü. Başka bir dosya seçerseniz "
                   "görüntü yine üretilir, güven katmanı üretilmez. Denetim dosya adına "
                   "değil, SHA-256 özetine bakar."),
    "preview_button": ("Modelin göreceği rasterleştirilmiş girdiyi hazırlar. Bu bir uydu "
                       "görüntüsü değildir: OSM yolları ile CLC+ arazi örtüsünden "
                       "çizilmiş bir haritadır. Üretim için gerekli değildir."),
    "preview_image": ("Modelin göreceği girdi. Buradaki arazi örtüsü, su ya da yollar "
                      "yanlışsa üretilen görüntü de aynı biçimde yanlış olur."),
    "verdict": ("Güven skoru rasterleştirilmiş girdiden hesaplanır, model çalıştırılmaz. "
                "Bant sınırları 150 karoluk ayrık Avrupa kümesinde, C2 kolunda ölçüldü: "
                "Spearman rho -0,76, eşleşen nokta sayısı sabit tutulduğunda -0,38. Aynı "
                "sınırlar 130 karoluk Ankara kümesine uygulandığında sıralama korunur, "
                "ayrışma artar, kırmızı bandın mutlak değeri %7 içinde kalır; turuncu ve "
                "yeşil bantlar Türkiye'de daha düşük çıkar. Ayrıntı QUICKSTART.md'de."),
    "out_file": ("Yazılacak GeoTIFF. Yanına rasterleştirilmiş girdi <ad>_osm.tif olarak, "
                 "istenirse renkli güven katmanı <ad>_confidence.tif olarak yazılır."),
    "out_crs": ("Çıktının teslim edileceği koordinat sistemi. Üretim her koşulda metrik "
                "KRS'de, 10 m'de yapılır. Burada başka bir KRS seçerseniz özgün dosya "
                "yerinde kalır, yanına yeniden örneklenmiş bir kopya yazılır. Kopyanın "
                "pikselleri 10 m ızgarasında değildir; bu, kopyanın künyesine yazılır."),
    "add_layers": "Üretilen dosyaları iş bitince haritaya ekler.",
    "source": ("OSM verisinin okunacağı yer. Yerel .osm.pbf çevrimdışı çalışır ve "
               "hızlıdır. Overpass çevrimiçidir, dosya gerektirmez."),
    "pbf_file": ("Geofabrik'ten indirilen .osm.pbf. Bir kez seçilir, sonraki açılışlarda "
                 "hatırlanır. Çalışılan alanı kapsamalıdır: kapsamazsa çıktı boş kırsal "
                 "alan gibi görünür, hata gibi görünmez."),
    "clc_file": ("CLC+ Backbone 2021 rasterı (Copernicus). Arazi örtüsü tabanı. Bir kez "
                 "seçilir, sonraki açılışlarda hatırlanır."),
    "tile_overlap": ("Komşu karoların üst üste binme miktarı. Serbestçe yazılabilir, iki "
                     "kısıtla: değer 10 m'lik piksel ızgarasının tam katı olmalı ve bir "
                     "karodan (2570 m) küçük kalmalı. Ara değerler karoları kesirli piksele "
                     "oturtur ve mozaikte alt piksel kayması yaratır; bu yüzden kabul "
                     "edilmez. 640 m ölçülmüş varsayılandır: dikiş enerjisi oranı bu değerde "
                     "1,008 çıktı. Başka bir değer seçmek serbesttir ama o değeri biz "
                     "ölçmedik, sorumluluk kullanıcıdadır."),
    "confidence_alpha": ("Güven, çıktı GeoTIFF'inin 4. bandına sürekli değer olarak "
                         "yazılır: alfa = clip((z+4)/8, 0, 1) × 255, 255 en güvenli. RGB "
                         "bantları değişmez, alfayı yok sayan bir uygulama eskisiyle "
                         "birebir aynı görüntüyü okur."),
    "confidence_band_layer": ("Göz için üç renkli ayrı bir katman üretir. Sürekli değer "
                              "zaten alfa kanalında; bu katman yalnızca okumayı "
                              "kolaylaştırır."),
    "add_osm_layer": ("Modelin gördüğü rasterleştirilmiş girdiyi <çıktı>_osm.tif olarak "
                      "yazıp haritaya ekler. Böylece girdi iş bittikten sonra da "
                      "incelenebilir."),
    "generate": "Üretimi arka planda başlatır. QGIS bu sırada donmaz.",
    "cancel": "Çalışan işi durdurur. Diske eksik dosya yazılmaz.",
}


def t(key, **kw):
    """Look up a label. A missing key is a bug, and says so loudly."""
    try:
        s = S[key]
    except KeyError:
        return f"!!MISSING STRING: {key}!!"
    return s.format(**kw) if kw else s


def tip(key):
    """Look up a tooltip. Missing tooltips are silent - a widget may legitimately lack one."""
    return TIP.get(key, "")
