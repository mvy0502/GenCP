"""Every user-visible string in the SR plugin, in one place.

The interface is Turkish. Code, comments, commit messages and documentation stay English.
Nothing in dialog.py may contain a Turkish literal; a missing string here is the bug, and
`t()` says so loudly rather than falling back to the key.

`S` holds LABELS - what a widget is called, a couple of words. `TIP` holds TOOLTIPS - the
explanation that would otherwise sit in the dialog as prose. Same split as Project 1's
plugin, for the same reason.

Terminology follows `tubitak/docs/terimler.md`, which takes QGIS's own Turkish
localisation as the authority so the words match the menus the user is already looking at:
katman, raster katman, KRS, kapsam, karo, karo bindirmesi, çözünürlük, ilerleme çubuğu.

Four terms this work package needs are NOT in that file, because Project 1 had no scale
factor and no resampler. They are recorded here and in `docs/02b-plugin.md` rather than by
editing Project 1's terminology file, which belongs to another work package:

    super-resolution  -> süper çözünürlük
    scale factor      -> ölçek katsayısı
    bicubic           -> bikübik            (a proper name; not translated)
    upsampler/method  -> yöntem

Turkish conventions from terimler.md that bite in code: decimal comma, and a suffix
attached to a numeral cannot be produced by string formatting because Turkish suffixes
follow how a number is READ. Numbers are therefore never given a glued suffix here.
"""
from __future__ import annotations

LANG = "tr"

S = {
    # ------------------------------------------------------------------ pencere ----
    "window_title": "GenCP Süper Çözünürlük",
    "close": "Kapat",

    # ------------------------------------------------------------------- girdi ----
    "sec_input": "Girdi",
    "src_from_layer": "Yüklü katmandan",
    "src_from_file": "Dosyadan",
    "input_layer": "Raster katman",
    "input_file": "Raster dosyası",
    "src_info": "Girdi",
    "src_unset": "<span style='color:gray'>girdi seçilmedi</span>",
    "src_bad": "<span style='color:#a00'>Bu raster okunamadı.</span>",
    # Reads: "10980 x 10980 piksel - 3 bant, uint8 - EPSG:32636 - 10 m"
    "src_value": ("{w} × {h} piksel · {bands} bant, {dtype} · {crs} · "
                  "{gsd} m çözünürlük"),
    "src_rotated": ("<span style='color:#a00'>Bu raster kuzeye dönük değil "
                    "(döndürülmüş ya da eğilmiş). Süper çözünürlük bunu işlemez.</span>"),

    # ------------------------------------------------------------------ ayarlar ----
    "sec_settings": "Ayarlar",
    "scale": "Ölçek katsayısı",
    "scale_fixed": "2 ×  (çözünürlük iki katına çıkar)",
    "method": "Yöntem",
    "method_bicubic": "Bikübik",
    "model_file": "Model dosyası",
    "model_disabled": "<span style='color:gray'>Bikübik yönteminde kullanılmaz.</span>",

    # ------------------------------------------------------------------ gelişmiş ---
    "sec_advanced": "Gelişmiş",
    "tile_px": "Karo boyutu (piksel)",
    "overlap_px": "Karo bindirmesi (piksel)",
    "advanced_note": ("<span style='color:gray'>Gösteri için değiştirmeyin. "
                      "Varsayılan 512 / 32 ölçülmüş değerdir.</span>"),

    # ------------------------------------------------------------------- çıktı ----
    "sec_output": "Çıktı",
    "out_file": "Çıktı dosyası",
    "add_layer": "İş bitince haritaya ekle",
    "out_estimate": "Tahmin",
    "out_estimate_value": ("<b>{n} karo</b> · çıktı {w} × {h} piksel · "
                           "{gsd} m çözünürlük · yaklaşık {mb:.0f} MB"),
    "out_estimate_unset": "<span style='color:gray'>—</span>",

    # ------------------------------------------------------------------ çalışma ----
    "run": "Çalıştır",
    "cancel": "Durdur",
    "idle": " ",
    "starting": "Başlatılıyor…",
    "stage_tiles": "Karo {done} / {total}",
    "cancelling": "Durduruluyor…",
    "cancelled": "Durduruldu. Diske eksik dosya yazılmadı.",
    "done": "Bitti · {n} karo · {secs} sn · {mb} MB",
    "done_aligned": "Katman eklendi ve girdiyle hizalı.",
    "done_misaligned": ("<b>Çıktı katmanı girdiyle hizalı değil.</b> "
                        "Ayrıntı için Günlük Mesajları panelinde GenCP SR bölümüne bakın."),
    "failed": "Başarısız: {msg}",
    "layer_add_failed": "Çıktı yazıldı ama katman olarak açılamadı: {path}",

    # --------------------------------------------------------------- engelleyici ---
    # Shown in place of the run button's tooltip when the run button is disabled, so the
    # user is told WHY rather than left clicking a dead button.
    "blocked_no_input": "Önce bir girdi rasterı seçin.",
    "blocked_bad_input": "Seçilen raster okunamıyor.",
    "blocked_no_output": "Çıktı dosyası yolunu yazın.",
    "blocked_output_is_input": "Çıktı yolu girdiyle aynı olamaz.",
    "blocked_running": "İş sürüyor.",

    # ------------------------------------------------------------------ hatalar ----
    "err_open": "Raster açılamadı: {msg}",
    "err_overwrite_title": "Dosya var",
    "err_overwrite": "{name} zaten var. Üzerine yazılsın mı?",
    "yes": "Evet",
    "no": "Hayır",

    # ------------------------------------------------------------------ WP4 model ---
    "method_model": "Eğitilmiş model (ONNX)",
    "model_info": "Model künyesi",
    "model_unset": "<span style='color:gray'>model dosyası seçilmedi</span>",
    # Reads: "gencp_sr_x2_v1.onnx - DN/5000 - 2x - 3 bant B02,B03,B04 - adım 16306/20000"
    "model_desc": ("{name} · DN/{norm:.0f} · {scale}× · {ch} bant {order} · "
                   "adım {done}/{sched}"),
    "model_bad": "<span style='color:#a00'>Bu ONNX dosyası okunamadı: {msg}</span>",
    "model_caveat": ("<span style='color:gray'>Model, 20 m→10 m üzerinde eğitildi ve "
                     "10 m→5 m uygulanıyor. 5 m çıktı doğrulanmamıştır.</span>"),
    "tile_model_note": ("<span style='color:gray'>Model yolunda karo boyutu modelin "
                        "künyesinden okunur.</span>"),

    # --- girdi reddi: modele uygun olmayan dosya. Çalışıp saçma üretmek yerine reddeder ---
    "err_input_title": "Girdi modele uygun değil",
    "err_dtype": ("Model <b>16 bit tam sayı (uint16)</b> yansıtma değerleri bekler; "
                  "seçilen dosyanın veri tipi <b>{got}</b>.<br><br>"
                  "TCI dosyası 8 bitlik <i>görsel</i> bir birleşimdir; modelin eğitildiği "
                  "veri bu değildir ve model bu dosyayla anlamsız sonuç üretir.<br><br>"
                  "Model yolu için adı <b>MODEL_INPUT_</b> ile başlayan, {order} bantlarını "
                  "içeren yansıtma dosyasını seçin. TCI dosyasını <b>Bikübik</b> yöntemiyle "
                  "kullanabilirsiniz."),
    "err_bands": ("Model <b>{want} bant</b> bekler ({order}); seçilen dosyada "
                  "<b>{got} bant</b> var.<br><br>Adı <b>MODEL_INPUT_</b> ile başlayan "
                  "yansıtma dosyasını seçin."),
    "err_range": ("Dosya 16 bit ama değerleri 8 bitlik bir görüntününki gibi "
                  "(%99,9 dilimi <b>{p999:.0f}</b>). Yansıtma verisinde bu değer birkaç "
                  "bindir. Bu dosya büyük olasılıkla dönüştürülmüş bir TCI.<br><br>"
                  "Adı <b>MODEL_INPUT_</b> ile başlayan dosyayı seçin."),
    "err_model_meta": ("<b>{name}</b> künye bilgisi taşımıyor: {missing}. Eklenti "
                       "normalleştirme sabitini modelden okur; künyesiz bir modeli "
                       "tahminle çalıştırmaz."),

    # --- eksik paketler: okunur bir mesaj, ModuleNotFoundError değil ---
    "err_no_rasterio": ("<b>rasterio</b> paketi bu QGIS kurulumunda yok. Eklenti raster "
                        "okuyup yazmak için onu kullanır ve onsuz çalışamaz.<br><br>"
                        "QGIS'in Python ortamına <code>rasterio</code> kurulmalıdır."),
    "err_no_onnxruntime": ("<b>onnxruntime</b> paketi bu QGIS kurulumunda yok. "
                           "Eğitilmiş model bu paketle çalışır.<br><br>"
                           "<b>Bikübik</b> yöntemi onsuz da çalışır; model yolu için "
                           "QGIS'in Python ortamına <code>onnxruntime</code> kurulmalıdır."),
    "blocked_no_model": "Model dosyasını seçin.",
    "blocked_bad_model": "Model dosyası okunamıyor.",
    "blocked_input_not_model": "Bu girdi model yolunda kullanılamaz (ipucu için bakın).",

    # ------------------------------------------------------------ dosya süzgeci ---
    # File-dialog filters are user-facing text and therefore live here, not in dialog.py.
    # They were literals in dialog.py until plugin_guards G1 reported them.
    "filter_raster": "GeoTIFF (*.tif *.tiff *.TIF *.TIFF);;Tüm dosyalar (*)",
    "filter_model": "ONNX (*.onnx);;Tüm dosyalar (*)",
}

TIP = {
    "src_from_layer": ("QGIS'te açık olan raster katmanlar. Katman yoksa "
                       "\"Dosyadan\" seçeneğini kullanın."),
    "src_from_file": ("Diskteki bir GeoTIFF. Katman olarak açmanız gerekmez."),
    "input_layer": ("İşlenecek raster katman. Kuzeye dönük ve döndürülmemiş olmalıdır; "
                    "değilse iş başlamadan reddedilir."),
    "input_file": ("İşlenecek GeoTIFF. Kuzeye dönük ve döndürülmemiş olmalıdır."),
    "src_info": ("Girdinin okunan gerçek özellikleri: boyut, bant sayısı, veri tipi, "
                 "KRS ve piksel boyu. Bunlar dosyadan okunur, tahmin edilmez."),
    "scale": ("Çıktının girdiye göre kaç kat ince olacağı. Şimdilik 2'ye sabitlenmiştir: "
              "10 m girdi 5 m çıktı verir. Kaynak ızgarasının tam katı olması gerekir."),
    "method": ("Ara değer yöntemi. Bikübik bir taban çizgisidir, eğitilmiş model değildir; "
               "yeni bilgi üretmez, var olanı yeniden örnekler."),
    "model_file": ("Eğitilmiş model dosyası. Bikübik yönteminde kullanılmaz ve bu yüzden "
                   "kapalıdır; eğitilmiş model hazır olduğunda burası açılacaktır."),
    "tile_px": ("Görüntünün işlendiği kare parçanın kaynak piksel cinsinden boyu. "
                "Küçültmek belleği azaltır, süreyi biraz uzatır."),
    "overlap_px": ("Komşu karoların üst üste binme miktarı. 8 pikselin altında karo "
                   "sınırları çıktıda görünür hale gelir; bu ölçülmüş bir değerdir."),
    "out_file": ("Yazılacak GeoTIFF. Yazma atomiktir: iş yarıda kesilirse bu yolda "
                 "yarım dosya oluşmaz."),
    "add_layer": ("Çıktı dosyasını iş bitince haritaya raster katman olarak ekler ve "
                  "girdiyle hizalı olup olmadığını denetler."),
    "out_estimate": ("Karo sayısı ve çıktı boyutu. Boyut sıkıştırmadan önceki kaba bir "
                     "tahmindir; gerçek dosya genellikle daha küçüktür."),
    "method": ("Ara değer yöntemi. <b>Bikübik</b> bir taban çizgisidir, yeni bilgi "
               "üretmez. <b>Eğitilmiş model</b> ayrıntı üretir ve yalnızca yansıtma "
               "(uint16) girdisiyle çalışır; TCI dosyasıyla çalışmaz."),
    "model_file": ("Eğitilmiş modelin ONNX dosyası. Normalleştirme sabiti, ölçek ve bant "
                   "sırası bu dosyanın içinden okunur; eklenti bunları kendi içinde "
                   "saklamaz."),
    "model_info": ("Modelin kendi künyesi: normalleştirme böleni, ölçek, bant sayısı ve "
                   "sırası, ve eğitimin kaçıncı adımda durduğu."),
    "run": "İşi arka planda başlatır. QGIS bu sırada donmaz.",
    "cancel": ("Çalışan işi durdurur. Yarıda kesilen iş diske dosya bırakmaz, "
               "bu yüzden sonraki bir çalıştırma yarım dosyayı hazır sanmaz."),
}


def t(key, **kw):
    """Look up a label. A missing key is a bug, and says so loudly."""
    try:
        s = S[key]
    except KeyError:
        raise KeyError(f"strings.S has no key {key!r} - add it, do not inline the text")
    return s.format(**kw) if kw else s


def tip(key, **kw):
    """Look up a tooltip. Missing tooltips are silent - a widget may legitimately lack one."""
    s = TIP.get(key)
    if s is None:
        return ""
    return s.format(**kw) if kw else s
