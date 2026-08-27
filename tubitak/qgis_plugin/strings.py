"""Every user-visible string in the plugin, in one place.

The users are Turkish, so the interface is Turkish. Code, comments, commit messages and
documentation stay English - that split is deliberate and is the project's convention.

Everything the user can read lives here so that switching language, or adding real Qt
translations later, is a one-file change rather than a hunt through dialog.py. Nothing in
dialog.py may contain a Turkish literal; if a string is missing from this module, that is
the bug.

Placeholders are `str.format` style and named, so a translator can reorder them.

House rule from the project: no emoji anywhere in user-facing text. Status is carried by
words and colour, not by symbols.
"""
from __future__ import annotations

LANG = "tr"

S = {
    # ---------------------------------------------------------------- window ----
    "window_title": "GenCP - Sentetik Referans Üretimi",
    "close": "Kapat",

    # ---------------------------------------------------------------- 1 input ---
    "sec1": "1 · Girdi",
    "reference_layer": "Referans katman:",
    "extent": "Kapsam:",
    "crs": "KRS:",
    "tiles_estimate": "Karo / süre tahmini:",
    "tile_overlap": "Karo bindirmesi:",
    "overlap_default": "{m} m (varsayılan, ölçülmüş)",
    "overlap_economy": "{m} m (ekonomik)",
    "overlap_plain": "{m} m",
    "unset": "—",
    # A bare dash reads as "failed". These say "waiting for you", which is what they mean.
    "waiting": "<span style='color:gray'>— katman seçilince dolar</span>",
    "no_raster_layer": "<b>Projede uygun katman yok.</b>",
    # Kept to two lines: this sits in the empty state, and an empty form that is taller
    # than a filled one pushes the Generate button off the screen.
    "no_raster_layer_hint": (
        "Önce bir raster katman yükleyin: <b>Katman > Katman Ekle > Raster Katman "
        "Ekle…</b> — bu pencere açıkken de olur, liste kendini günceller."),
    "no_raster_layer_tooltip": (
        "Üretilecek alan ve koordinat referans sistemi seçtiğiniz katmandan okunur. "
        "Katman georeferanslı ve metrik bir KRS'de olmalıdır."),
    "extent_value": "{xmin:.2f}, {ymin:.2f} → {xmax:.2f}, {ymax:.2f}  ({w:.0f} × {h:.0f} harita birimi)",
    "tiles_value": "<b>{n} karo</b> → çıktı {w} × {h} piksel ({mp:.1f} Mpiksel), {crs}",
    "tiles_estimate_note": "kaba tahmin {mins:.1f} dakika (CPU) — garanti değil, tahmindir",

    # ---------------------------------------------------------------- 2 source --
    "sec2": "2 · Veri kaynağı",
    "source_online": "Çevrimiçi (Overpass)",
    "source_local": "Yerel vektör dosyası (.osm.pbf)",
    "advanced": "Gelişmiş - dosya yolları",
    "pbf_label": "OSM çıkarımı (.osm.pbf):",
    "clc_label": "CLC+ Backbone rasterı:",
    "browse": "Gözat…",
    "source_summary_ok": "Kaynak hazır: {pbf} + CLC+ {clc}",
    "source_summary_overpass": "Kaynak hazır: Overpass (çevrimiçi) + CLC+ {clc}",
    "remembered": "En son kullanılan yollar hatırlandı. Değiştirmek için “Gelişmiş” bölümünü açın.",

    # ---------------------------------------------------------------- 3 preview -
    "sec3": "3 · Önizleme - modelin göreceği rasterleştirilmiş girdi",
    "preview_hint": ("Üretmeden önce bu görüntüye bakın. Arazi örtüsü, su veya yollar "
                     "burada yanlışsa üretilen görüntü de aynı şekilde ve kendinden emin "
                     "biçimde yanlış olur."),
    "preview_none": "Henüz önizleme yok.",
    "preview_needs_layer": (
        "Önizleme, 1. bölümde bir referans katman seçildikten sonra burada görünür."),
    "preview_press": (
        "Katman hazır. <b>Önizleme karosunu oluştur</b> düğmesine basın."),
    "osm_placeholder": "<span style='color:gray'>Önizleme oluşturulunca dolar.</span>",
    "preview_button": "Önizleme karosunu oluştur",
    "preview_prev": "◀ Önceki karo",
    "preview_next": "Sonraki karo ▶",
    "preview_rendering": "Önizleme karosu oluşturuluyor…",
    "preview_done": "Önizleme hazır.",
    "preview_done_counts": "Önizleme hazır - bu karoda {total} OSM nesne pikseli.",
    "preview_failed_title": "Önizleme başarısız",
    "preview_failed": "Önizleme başarısız: {err}",
    "confirm_generic": "Yukarıdaki rasterleştirilmiş girdiye baktım, doğru",
    "confirm_tile": "({i},{j}) numaralı karoya baktım ({n} karodan biri), görüntü doğru",

    # OSM content breakdown - "4 OSM nesnesi" is not a number anyone can judge
    "osm_breakdown_title": "Bu karodaki OSM içeriği",
    "osm_roads": "yollar",
    "osm_buildings": "binalar",
    "osm_water": "su",
    "osm_landuse": "arazi kullanımı",
    "osm_px": "{n} piksel",
    "osm_none": "yok",
    # Driven by the SAME registered score and the SAME band boundaries as the output
    # layer, so the two cannot disagree. The old version used a hand-set 0.2% pixel
    # threshold that contradicted the layer on the very first tile it was tested on.
    # Every per-band figure NAMES ITS CORPUS. Registration 3 measured that the European
    # numbers do not transfer to Ankara for amber (-47%) and green (-56%) - only red does
    # (-6.7%). An unqualified "3,3 piksel" was therefore a European number presented as if
    # it were universal. See confidence-transfer-results.md.
    "preview_band_red": (
        "<b>Bu karo kırmızı bantta: üretilen görüntü burada büyük ölçüde uydurma "
        "olacak.</b> Girdi bu alan hakkında neredeyse hiçbir şey söylemiyor, dolayısıyla "
        "modelin ürettiği doku ölçülmüş bir şeye dayanmıyor. Bu bandın eşleştirme hatası "
        "ortancası <b>Avrupa ayrık ölçümünde {px} piksel</b>di. Eşleştirme için "
        "kullanmayın."),
    "preview_band_amber": (
        "<b>Bu karo turuncu bantta: girdi zayıf.</b> Çıktı büyük ölçüde arazi "
        "örtüsünden türetilecek. Bu bandın eşleştirme hatası ortancası <b>Avrupa ayrık "
        "ölçümünde {px} piksel</b>di. Başka bir kaynakla karşılaştırmadan kullanmayın."),
    "preview_band_green": (
        "Bu karo yeşil bantta: çıktı burada girdi bilgisine dayanıyor (bu bandın hata "
        "ortancası Avrupa ayrık ölçümünde {px} piksel)."),
    # Turkish renderings of gencp_core.pipeline.coverage_warnings' STRUCTURED output. That
    # function used to return English sentences, which appeared under a Turkish heading in
    # a half-translated warning box.
    "warn_zero_osm_tiles": (
        "<b>{n} / {total} karoda hiç OSM nesnesi yok</b> ({tiles}{more}). Seçtiğiniz "
        "kaynak ({source}) bu alan için hiçbir şey döndürmedi; o karolar yalnızca CLC+ "
        "arazi örtüsünden oluşuyor: yol, bina ve su sınırı yok. Sonuç makul bir kırsal "
        "alan gibi görünür, hata gibi görünmez. Kaynağın bu kapsamı içerdiğini denetleyin."),
    "warn_zero_osm_source_overpass": "Overpass",
    "warn_more_tiles": " ve {n} karo daha",
    "warn_count_unavailable": "<b>{n} / {total} karo için nesne sayısı okunamadı.</b>",
    "osm_zero_warning": (
        "<b>Bu karoda hiç OSM nesnesi yok.</b> Seçtiğiniz kaynak bu alanı kapsamıyor "
        "olabilir. Sonuç yine de üretilir ve makul bir kırsal alan gibi görünür - hata "
        "gibi görünmez."),

    # ---------------------------------------------------------------- 4 model ---
    "sec4": "4 · Model",
    "model_none": "Model seçilmedi.",
    "model_desc": "<b>{name}</b><br>değiştirilme {mtime} · {mb:.1f} MB",
    "model_pick": "ONNX üretici model",
    # 1.1 - which model SHIPS and which model the bands were CALIBRATED ON are two
    # different decisions, and the dialog now says so out loud instead of letting one
    # imply the other.
    "model_calibrated_ok": (
        "<span style='color:gray'>Güven bantları bu model dosyası için ölçüldü "
        "(SHA-256 doğrulandı).</span>"),
    "model_not_calibrated": (
        "<b>Güven bantları bu model için ölçülmedi</b> — yalnızca <code>{calib}</code> "
        "için. Görüntü üretilir, güven katmanı üretilmez."),
    "model_not_calibrated_tooltip": (
        "Bantlar 150 ayrık Avrupa karosunda C2 kolu için ölçüldü. Başka bir modele "
        "taşındıklarında geçerli olmayabilirler, bu yüzden bu model seçiliyken güven "
        "katmanı üretilmez."),

    # ---------------------------------------------------------------- 5 run -----
    "sec5": "6 · Çalıştırma",
    "idle": "Hazır.",
    "generate": "Üret",
    "cancel": "Vazgeç",
    "running_note": "Arka planda çalışıyor - QGIS donmaz, harita gezinilebilir kalır.",
    "cancelling": "Vazgeçiliyor…",
    "cancelled": "Vazgeçildi. Diske yarım dosya yazılmadı.",
    "stage_render": "Rasterleştiriliyor ({done}/{total})",
    "stage_infer": "Üretiliyor ({done}/{total})",
    "stage_confidence": "Güven haritası hesaplanıyor ({done}/{total})",
    "stage_mosaic": "Birleştiriliyor",
    "stage_unknown": "Çalışıyor ({done}/{total})",
    "failed_title": "Üretim başarısız",
    "failed": "Başarısız: {err}",

    # ---------------------------------------------------------------- 6 output --
    "sec6": "5 · Çıktı",
    "add_layer": "Sonucu haritaya katman olarak ekle",
    "write_tif": "Diske GeoTIFF yaz",
    "save_as": "Farklı kaydet…",
    "out_pick": "GeoTIFF yaz",
    "make_confidence": "Güven katmanı da üret (piksel başına güvenilirlik)",
    "confidence_cost": "Girdiden hesaplanır; ek model çalıştırmaz.",
    "wrote": "yazıldı: {path}",
    "added_layer": "katman olarak eklendi",
    "no_file_to_add": ("diske hiçbir şey yazılmadı, dolayısıyla eklenecek dosya yok; "
                       "sonucu haritaya eklemek için “Diske GeoTIFF yaz” kutusunu "
                       "işaretleyin"),
    "layer_failed": "katman yüklenemedi",
    "seam": "dikiş enerjisi oranı {ratio:.3f}",
    "done": "Bitti.",

    # ---------------------------------------------------------------- bands -----
    "band_red": "Kırmızı - kullanmayın",
    "band_amber": "Turuncu - dikkatli kullanın",
    "band_green": "Yeşil - kullanılabilir",
    "band_red_desc": "Çıktı burada büyük ölçüde uydurma",
    "band_amber_desc": "Girdi zayıf; başka bir kaynakla karşılaştırın",
    "band_green_desc": "Çıktı burada girdi bilgisine dayanıyor",
    "verdict_title": "Güven değerlendirmesi",
    "verdict_line": ("Yeşil %{green:.0f} · Turuncu %{amber:.0f} · Kırmızı %{red:.0f}. "
                     "Bütün çalışmanın ortalama bandı: <b>{band}</b>."),
    "verdict_red_warning": (
        "<b>Uyarı: kırmızı bant çıktının yaklaşık %{red:.0f} kadarını kaplıyor</b> "
        "(eşik %{thr:.0f}). Bu bölgelerde görüntü büyük ölçüde uydurmadır ve "
        "eşleştirme için kullanılmamalıdır."),
    "details": "Detaylar - ölçüm ve kapsam",
    "verdict_scope": (
        "Bant sınırları <b>150 ayrık Avrupa karosunda</b>, C2 kolu için ölçüldü "
        "(Spearman rho -0,76; eşleşen nokta sayısı sabit tutulduğunda -0,38). Aynı "
        "sınırlar 130 Ankara karosuna değiştirilmeden uygulandığında sıralama korunuyor "
        "ve ayrışma artıyor (kırmızı/yeşil 2,5 kat yerine 5,2 kat); kırmızı bandın mutlak "
        "değeri de %7 içinde tutuyor. Turuncu ve yeşil bantların mutlak değerleri ise "
        "Türkiye'de daha düşük çıkıyor - yani gösterilen Avrupa sayıları bu iki bant için "
        "kötümser. Ayrıntı: confidence-transfer-results.md. Skor girdiden hesaplanır; "
        "model çalıştırılmaz."),
    "confidence_not_validated": (
        "<b>Bu model için güven bantları doğrulanmadı.</b> Bantlar yalnızca "
        "<code>gencp_C2_fp32.onnx</code> için ölçüldü; seçtiğiniz model farklı. Güven "
        "katmanı üretilmeyecek. Doğrulanmış modeli seçin veya güven katmanını kapatın."),
    "confidence_no_stochastic": (
        "<b>Güven katmanı için eşleşen rastgele model dosyası bulunamadı.</b> "
        "<code>{name}</code> dosyasının modelin yanında olması gerekir. Güven katmanı "
        "üretilmeyecek."),

    # ---------------------------------------------------------------- errors ----
    # Every one of these names the FIX, not just the fault.
    "err_no_layer": "Önce bir referans katman seçin; üretilecek alan ve KRS ondan okunur.",
    "err_pbf_empty": ("Yerel bir .osm.pbf dosyası seçin (“Gelişmiş” bölümünde “Gözat”), "
                      "ya da yukarıdan Overpass seçeneğine geçin."),
    "err_pbf_missing": ("OSM çıkarımı bulunamadı: {path}. Dosya taşınmış veya silinmiş "
                        "olabilir; “Gelişmiş” bölümünden yeniden seçin."),
    "err_clc_empty": ("CLC+ Backbone raster yolu gerekli. “Gelişmiş” bölümünden "
                      "“Gözat” ile seçin."),
    "err_clc_missing": ("CLC+ rasterı bulunamadı: {path}. “Gelişmiş” bölümünden yeniden "
                        "seçin."),
    "err_model_missing": ("Geçerli bir .onnx model dosyası seçin (4. bölüm, “Gözat”)."),
    "err_out_missing": ("Çıktı dosyası için bir yol seçin (5. bölüm, “Farklı kaydet”), "
                        "ya da “Diske GeoTIFF yaz” kutusunun işaretini kaldırın."),
    "err_not_confirmed": ("Üretmeden önce 3. bölümdeki önizlemeyi oluşturun ve doğru "
                          "olduğunu onaylayın."),
}


def t(key, **kw):
    """Look up a string and format it. A missing key is a bug, and says so loudly."""
    try:
        s = S[key]
    except KeyError:
        return f"!!MISSING STRING: {key}!!"
    return s.format(**kw) if kw else s
