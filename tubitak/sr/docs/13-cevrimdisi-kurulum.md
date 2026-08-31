# Çevrimdışı kurulum kiti — internet olmayan Windows makineleri için

Bu belge, internet erişimi olmayan bir Windows makinesinde QGIS eklentilerinin ihtiyaç
duyduğu Python paketlerinin nasıl kurulacağını anlatır. Komut satırı bilgisi
gerektirmez; her adım birebir uygulanabilir biçimde yazılmıştır.

## 1. Kitin içinde ne var

`kit/` klasörü, **16 adet `.whl` dosyası** ve bir `MANIFEST.json` içerir; toplam
**57,6 MB**. Sürümler ve SHA-256 özetleri `MANIFEST.json` içinde kayıtlıdır; kurulan
dosyaların sınanan dosyalarla aynı olduğu bu şekilde gösterilebilir.

| Paket | Sürüm | Boyut |
|---|---|---|
| `rasterio` | 1.5.1 | 29,2 MB |
| `onnxruntime` | 1.29.0 | 13,4 MB |
| `osmium` | 4.3.1 | 1,7 MB |
| bağımlılıklar (numpy, protobuf, requests, …) | 13 dosya | 13,3 MB |

**`rasterio` bilerek dâhil edilmiştir**, Windows QGIS'in onu zaten getiriyor olma
ihtimaline rağmen: `pip` zaten karşılanmış olanı atlar ve 1,78 GB'lık veri yükünün yanında
bu birkaç on megabaytın maliyeti yoktur. Küçültmeye çalışılmamıştır.

Hedef: **Windows 64 bit, Python 3.12 (cp312)**. Başka bir Python sürümü ya da başka bir
işletim sistemi için bu kit **kullanılamaz**.

## 2. Önce: hangi paketlerin eksik olduğu ölçülmelidir

Kurulumdan önce `tubitak/tool/qgis_ortam_raporu.py` dosyasının tamamı QGIS'in Python
konsoluna yapıştırılıp çalıştırılmalıdır (**Eklentiler > Python Konsolu**). Çıktı iki şeyi
verir:

1. **Hangi paketler `YOK`** — yalnızca onlar kurulacaktır.
2. **QGIS'in kendi `site-packages` dizininin tam yolu** — kurulumun hedefi budur.

**Python sürümü `3.12` değilse bu kit kullanılmamalıdır.** Rapordaki `abi tag` satırı
`cp312` yazmalıdır.

## 3. Kurulum

Klasör makineye kopyalanmalıdır; örneğin `C:\gencp_kit\`.

### 3.1 Tercih edilen yol: OSGeo4W Shell

**OSGeo4W Shell**, QGIS ile birlikte gelen ve QGIS'in kendi Python'ını doğru biçimde
ayarlayan komut penceresidir. Başlat menüsünde QGIS klasörünün altında bulunur.

Açıldıktan sonra tek satır:

```
python -m pip install --no-index --find-links=C:\gencp_kit\wheels --target="<HEDEF>" rasterio onnxruntime osmium
```

`<HEDEF>`, §2'deki raporun gösterdiği QGIS `site-packages` dizinidir; tırnak içinde
yazılmalıdır.

> **Hedef dizin neden açıkça yazılıyor?** `pip`'in öntanımlı hedefi, makinedeki **her**
> Python 3.12 tarafından paylaşılan kullanıcı düzeyinde bir dizindir. Geliştirme
> makinesinde ölçülen durum tam olarak budur: `onnxruntime` ve `osmium` oradan
> çözümleniyordu. Temiz bir kurum bilgisayarında o sızıntı olmayacaktır, bu yüzden hedef
> tahmine bırakılmaz.

Yazma izni hatası alınırsa: OSGeo4W Shell **yönetici olarak** açılmalı (sağ tık >
Yönetici olarak çalıştır), ya da `--target` yerine `--user` kullanılmalıdır.

### 3.2 OSGeo4W Shell bulunamazsa: QGIS Python Konsolu

**Eklentiler > Python Konsolu** açılıp tek satır çalıştırılır:

```python
import pip; pip.main(["install", "--no-index", "--find-links", r"C:\gencp_kit\wheels", "--target", r"<HEDEF>", "rasterio", "onnxruntime", "osmium"])
```

### 3.3 `pip` yoksa

Rapor `pip` bulunamadığını gösterirse, OSGeo4W Shell'de şu denenmelidir:

```
python -m ensurepip --default-pip
```

`ensurepip` de yoksa, `get-pip.py` internetli bir makineden indirilip kit klasörüne
konulmalı ve `python get-pip.py --no-index --find-links=C:\gencp_kit\wheels`
çalıştırılmalıdır.

## 4. Kurulumun doğrulanması

**QGIS yeniden başlatılmalıdır.** Ardından §2'deki rapor yeniden çalıştırılır. Başarılı
sayılması için:

- `rasterio`, `onnxruntime`, `osmium` satırlarının hepsi **`VAR`** olmalıdır;
- her birinin yolu, kurulum hedefi olarak verilen dizini göstermelidir.

Eklenti açıldığında eksik paket uyarısı **çıkmamalıdır**. Çıkıyorsa, uyarının gösterdiği
dizin ile kurulum hedefi aynı değildir; kurulum o dizine tekrarlanmalıdır.

## 5. Bu kitin sınanmışlığı

**Sınanmıştır.** Kit iki kez, ağ bağlantısı kapalı biçimde (`--no-index`) kurulmuştur:

1. **Windows paket kümesi**, `--platform win_amd64 --python-version 3.12` ile bir hedef
   dizine kurulmuştur: 16 paketin tamamı çözümlenmiş, bağımlılık kümesi eksiksiz
   çıkmıştır.
2. **Aynı sürümler**, temiz bir Python 3.12.12 sanal ortamında kurulmuş ve
   `rasterio`, `onnxruntime`, `osmium` **içe aktarılabilmiştir**.

**Sınanmamıştır:** Windows'un kendisi. Yukarıdaki iki koşu, paket kümesinin eksiksiz
olduğunu ve komutun doğru olduğunu gösterir; **Windows'ta çalışacağını göstermez.**
Windows QGIS 3.40'ın `rasterio`'yu kendi içinde getirip getirmediği de bilinmemektedir —
§2'deki rapor bunu ölçmek içindir.

---

# Katman 2 — `onnxruntime` ve `osmium` eklentinin içine gömüldü

Amaç: **`rasterio`'su zaten olan** bir makinede kullanıcı yalnızca eklenti zip'ini kurar;
pip yok, internet yok, elle adım yok.

## 6. İki ayrı dağıtım dosyası — bilinçli bir karar

Gömülen tekerlekler `win_amd64` / `cp312` ikilileridir. Tek bir dosyada dağıtılsalardı her
macOS ve Linux kurulumuna 44 MB kullanılamaz Windows ikilisi inecekti. Bu yüzden **iki ayrı
sürüm dosyası** vardır:

| Dosya | Boyut | İçerik | Kime |
|---|---|---|---|
| `gencp_plugin.zip` | **98.410 bayt** | `_vendor/` yok | macOS, Linux, ve Windows'ta paketleri kendi kuranlar |
| `gencp_plugin_win_amd64.zip` | **15.935.709 bayt** | `onnxruntime` + `osmium` gömülü | internetsiz Windows makineleri |

**Çapraz platform dosyası Windows'a özel hâle getirilmemiştir.** Aynı kaynak koddan iki
dosya üretilir; `_vendor/` bulunmayan yapıda gömme kodu hiçbir şey yapmaz.

## 7. Gömülü kopya, kurulu kopyaya karşı KAYBEDER

`__init__.py` içindeki `_extend_path_for_vendored()`:

- `importlib.util.find_spec` ile **önce sistemde var mı diye bakar**; yalnızca bulunamayan
  paketler için `_vendor` dizinini `sys.path`'e **ekler (append)**, başa koymaz.
- `import` yerine `find_spec` kullanılır: burada `onnxruntime`'ı içe aktarmak, WP12'de
  kurulan geciktirme düzenini bozardı.
- Bozuk bir kurulum "yok" sayılır, çünkü `find_spec` hata verirse sonuç `False` olur.

Gerekçe: **çalışan bir kurulumu sessizce ezen gömülü kopya, yeni bir sessiz hata sınıfıdır** —
bu projenin varlık nedeni olan hata sınıfı.

**`rasterio` bilerek gömülmemiştir.** Kendi GDAL'ini taşır; QGIS aynı süreçte başka bir
GDAL'i çoktan yüklemiştir. Tek süreçte iki GDAL bilinen bir çökme sınıfıdır. **Kullanıcının
elle kurduğu bir bağımlılık, çöken bir QGIS'ten iyidir.**

## 8. Üç durum da koşuldu

| Durum | `ADDED_FOR` | İçe aktarma sonucu |
|---|---|---|
| **A** `_vendor` var, sistemde kopya yok | `['onnxruntime', 'osmium']` | ikisi de **`_vendor/`'dan** geldi |
| **B** `_vendor` yok, sistemde kopya yok | `[]` | `ModuleNotFoundError` — mevcut uyarı iletisi devreye girer |
| **C** `_vendor` var, sistemde kopya **var** | `[]` | ikisi de **sistemden** geldi; gömülü kopya kullanılmadı |

B, denetimin düşebildiğini gösterir; C, öncelik kuralının çalıştığını.

## 9. Doğrulanmamış olan — ve bu maddenin önemi büyüktür

**Gömülü `onnxruntime`'ın Windows'ta yerel DLL'lerini yükleyip yükleyemediği
sınanmamıştır.** Python 3.8'den beri Windows, bir uzantının yanındaki DLL'leri `sys.path`
üzerinden değil `os.add_dll_directory` listesi üzerinden çözer. Kod bunu çağırır
(`onnxruntime/capi` ve `osmium.libs` için), **ancak hiçbir Windows makinesinde
çalıştırılmamıştır.** Katman 2'nin tamamı bu tek noktaya bağlıdır.

**Bu yüzden Katman 1 (çevrimdışı tekerlek kiti) vazgeçilmezdir ve önce tamamlanmıştır.**
Katman 2 çalışmazsa Katman 1 hâlâ çalışır.
