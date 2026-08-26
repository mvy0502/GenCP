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
    "osm_sparse_warning": (
        "<b>Bu karoda çok az OSM verisi var</b> ({pct:.3f}% piksel; yollar {roads}, "
        "binalar {buildings}, su {water}, arazi kullanımı {landuse}). Çıktı büyük ölçüde "
        "arazi örtüsünden türetilecek: model, girdinin sessiz kaldığı yerde detay "
        "uyduruyor. Aşağıdaki onay kutusunu işaretlemeden önce bunu göz önünde "
        "bulundurun."),
    "osm_zero_warning": (
        "<b>Bu karoda hiç OSM nesnesi yok.</b> Seçtiğiniz kaynak bu alanı kapsamıyor "
        "olabilir. Sonuç yine de üretilir ve makul bir kırsal alan gibi görünür - hata "
        "gibi görünmez."),

    # ---------------------------------------------------------------- 4 model ---
    "sec4": "4 · Model",
    "model_none": "Model seçilmedi.",
    "model_desc": "<b>{name}</b><br>değiştirilme {mtime} · {mb:.1f} MB",
    "model_pick": "ONNX üretici model",

    # ---------------------------------------------------------------- 5 run -----
    "sec5": "5 · Çalıştırma",
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
    "sec6": "6 · Çıktı",
    "add_layer": "Sonucu haritaya katman olarak ekle",
    "write_tif": "Diske GeoTIFF yaz",
    "save_as": "Farklı kaydet…",
    "out_pick": "GeoTIFF yaz",
    "make_confidence": "Güven katmanı da üret (piksel başına güvenilirlik)",
    "confidence_cost": "16 ek çıkarım geçişi; karo başına yaklaşık 0,3 saniye.",
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
    "verdict_scope": (
        "Bantlar 150 ayrık Avrupa karosunda C2 kolu için ölçüldü (Spearman rho -0,75; "
        "eşleşen nokta sayısı sabit tutulduğunda -0,38). Görüntü belirlenimci yoldan, "
        "güven haritası ise dropout açık 16 geçişten gelir - teslim edilen görüntü "
        "rastgele yoldan gelmez."),
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
    "err_out_missing": ("Çıktı dosyası için bir yol seçin (6. bölüm, “Farklı kaydet”), "
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
