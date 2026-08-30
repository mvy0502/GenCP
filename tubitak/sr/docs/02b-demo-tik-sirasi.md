# Gösteri tıklama sırası — GenCP Süper Çözünürlük eklentisi

Bu belge, QGIS'i daha önce hiç kullanmamış birinin gösteriyi baştan sona yapabilmesi için
yazıldı. Her adım tek bir iştir. Hiçbir adım "zaten bellidir" diye atlanmadı.

**Soğuk başlangıç varsayılır:** QGIS kapalı, eklenti kurulu değil, hiçbir katman açık değil.

**Bu belge bir kez sınandı.** Yazıldıktan sonra sıfırdan bir QGIS profilinde baştan sona
uygulandı; 20 adımdan 2'si yanlış çıktı ve düzeltildi (ayrıntı: `02b-plugin.md`, §9).
Aşağıdaki metin düzeltilmiş olanıdır.

**Tamamı ne kadar sürer:** kurulum yaklaşık 3 dakika, üretim yaklaşık 40 saniye.

**Bu eklenti ne yapar:** bir raster dosyasını alır, piksel boyunu ikiye böler ve sonucu
yeni bir GeoTIFF olarak yazar. 10 m girdi 5 m çıktı verir. Şu anki yöntem **bikübik**tir:
bu bir taban çizgisidir, eğitilmiş model değildir. Yeni bilgi üretmez, var olanı yeniden
örnekler.

---

## Bölüm 0 — Gösteriden önce, bir kez

Bu bölüm gösteri sırasında değil, gösteriden **önce** yapılır. Sonucu bir dosyadır ve o
dosya durduğu sürece bu bölüm bir daha yapılmaz.

### 0.1 Eklenti dosyasını (zip) üret

Terminal'i açın. (Bulamıyorsanız: Spotlight'ı `Command + Boşluk` ile açın, `Terminal`
yazın, `Enter`.)

Aşağıdaki iki satırı sırayla yapıştırıp her birinden sonra `Enter`'a basın:

```bash
cd /Users/vedat/Documents/GenCP-Generative-Goruntu-Uretimi-OpenStreetMap
```

```bash
/opt/homebrew/Caskroom/miniforge/base/envs/gencp/bin/python tubitak/sr/build_sr_plugin_zip.py
```

Ekranda şuna benzer bir satır görmelisiniz:

```
/Users/vedat/Documents/GenCP-Generative-Goruntu-Uretimi-OpenStreetMap/tubitak/data/sr_dist/gencp_super_resolution.zip  13 files  34613 bytes  sha256 ...
  checked: metadata, classFactory module, vendored sr_core, no .pyc
```

Son satırdaki `checked:` sözcüğünü görmüyorsanız devam etmeyin; zip eksiktir.

Üretilen dosyanın tam yolu — bir sonraki bölümde gerekecek, not edin:

```
/Users/vedat/Documents/GenCP-Generative-Goruntu-Uretimi-OpenStreetMap/tubitak/data/sr_dist/gencp_super_resolution.zip
```

### 0.2 Girdi dosyasının yerinde olduğunu doğrulayın

```bash
ls -l /Users/vedat/Documents/GenCP-Generative-Goruntu-Uretimi-OpenStreetMap/tubitak/data/tiles36SVJ/TCI.tif
```

Bir satır ve yaklaşık `358841596` gibi bir sayı görmelisiniz. `No such file` yazıyorsa
gösteri bu dosya olmadan yapılamaz.

---

## Bölüm 1 — QGIS'i açın

1. Spotlight'ı açın: `Command + Boşluk`.
2. `QGIS` yazın.
3. Çıkan sonuçlar arasından **QGIS-final-4_2_1** olanı seçin ve `Enter`'a basın.
4. Program açılırken birkaç saniye beklersiniz. Ortada bir tanıtım penceresi çıkarsa
   sağ üstteki çarpıya basıp kapatın.

Artık boş bir QGIS penceresi karşınızda. Sol tarafta **Katmanlar** paneli boş.

---

## Bölüm 2 — Eklentiyi kurun

Bu bölüm bir kere yapılır. Eklenti bir kez kurulduktan sonra QGIS'i kapatıp açsanız da
kurulu kalır.

1. Üst menüden **Eklentiler**'e tıklayın.
2. Açılan listeden **Eklentileri Yönet ve Kur…** seçeneğine tıklayın.
3. Açılan pencerenin **sol** tarafında bir liste var. Oradan **ZIP'ten Kur**'a tıklayın.
4. Ortada **ZIP dosyası** yazan bir kutu ve sağında **…** düğmesi göreceksiniz.
   **…** düğmesine tıklayın.
5. Bir dosya seçme penceresi açılır. Klavyeden `Command + Shift + G` tuşlarına basın.
   Küçük bir yol yazma kutusu çıkar.
6. Bu kutuya aşağıdaki yolu yapıştırın ve `Enter`'a basın:

   ```
   /Users/vedat/Documents/GenCP-Generative-Goruntu-Uretimi-OpenStreetMap/tubitak/data/sr_dist
   ```

7. Listede **gencp_super_resolution.zip** dosyasını göreceksiniz. Üzerine **çift
   tıklayın**.
8. Dosya seçme penceresi kapanır, yol kutusuna dosyanın yolu yazılmıştır.
9. **Eklentiyi Kur** düğmesine tıklayın.
10. Birkaç saniye sonra "Eklenti kuruldu" anlamında bir bilgi kutusu çıkar. **Tamam**'a
    basın.
11. **Bu bir denetleme adımıdır, bir iş değil.** Aynı pencerenin sol tarafından
    **Kurulu** listesine tıklayın. Listede **GenCP Super-Resolution** satırını bulun ve
    solundaki **onay kutusunun işaretli olduğunu görün**.

    QGIS, ZIP'ten kurulan bir eklentiyi kendiliğinden etkinleştirir; ölçüldü, kutu zaten
    işaretli gelir. Yani burada yapacağınız bir şey yoktur — sadece bakın. Kutu
    işaretsizse (beklenmez) işaretleyin, çünkü işaretsizken eklenti menüde görünmez.
12. Pencereyi **Kapat** düğmesiyle kapatın.

**Kurulumun doğrulanması.** Üst menüden **Raster**'a tıklayın. Açılan listede
**GenCP SR** başlığını görmelisiniz. Görmüyorsanız 11. adımdaki onay kutusu işaretli
değildir; geri dönüp işaretleyin.

---

## Bölüm 3 — Girdi katmanını haritaya ekleyin

Bu adım zorunlu değildir — eklenti dosyayı doğrudan diskten de okuyabilir — ama gösteride
öncesi ve sonrası yan yana görüneceği için yapılması iyi olur.

1. Üst menüden **Katman** > **Katman Ekle** > **Raster Katman Ekle…** yolunu izleyin.
2. Açılan pencerede **Raster veri kümesi(leri)** kutusunun sağındaki **…** düğmesine
   tıklayın.
3. `Command + Shift + G` tuşlarına basın ve çıkan kutuya şunu yapıştırıp `Enter`'a basın:

   ```
   /Users/vedat/Documents/GenCP-Generative-Goruntu-Uretimi-OpenStreetMap/tubitak/data/tiles36SVJ
   ```

4. **TCI.tif** dosyasına çift tıklayın.
5. **Ekle** düğmesine, sonra **Kapat** düğmesine tıklayın.
6. Haritada bir uydu görüntüsü belirir. Sol taraftaki **Katmanlar** panelinde **TCI**
   yazan bir satır oluşur.

Görüntü çok küçük ya da hiç görünmüyorsa: **Katmanlar** panelinde **TCI** satırına
**sağ tıklayın** ve **Katmana Yakınlaştır** seçeneğine tıklayın.

---

## Bölüm 4 — Eklentiyi açın ve ayarları yapın

1. Üst menüden **Raster** > **GenCP SR** > **GenCP Super-Resolution…** yolunu izleyin.
2. **GenCP Süper Çözünürlük** başlıklı pencere açılır.

Pencerede yukarıdan aşağıya dört bölüm var: **Girdi**, **Ayarlar**, **Gelişmiş**,
**Çıktı**.

### 4.1 Girdi

3. En üstte iki seçenek var: **Yüklü katmandan** ve **Dosyadan**. **Yüklü katmandan**
   zaten seçilidir; öyle bırakın.
4. Altındaki **Raster katman** kutusuna tıklayın ve listeden **TCI**'yi seçin.
5. Hemen altındaki **Girdi** satırında şu yazının belirmesini bekleyin:

   ```
   10980 × 10980 piksel · 3 bant, uint8 · EPSG:32636 · 10 m çözünürlük
   ```

   Bu satır dosyadan okunur. Çıkmıyorsa yanlış katman seçilmiştir.

### 4.2 Ayarlar

6. **Ölçek katsayısı** satırında `2 ×  (çözünürlük iki katına çıkar)` yazar. Bu bir
   yazıdır, değiştirilemez ve gösteride değiştirilmesi gerekmez.
7. **Yöntem** kutusunda **Bikübik** seçilidir. Başka seçenek yoktur.
8. **Model dosyası** kutusu **soluk ve tıklanamaz** durumdadır. Bu doğrudur: bikübik
   yönteminde model kullanılmaz. Bu kutu, eğitilmiş model hazır olduğunda kullanılacak
   yerdir.

### 4.3 Gelişmiş

9. **Gelişmiş** bölümünün başındaki onay kutusu **işaretsiz** olmalıdır. Gösteride bu
   bölüme dokunmayın.

### 4.4 Çıktı

10. **Çıktı dosyası** kutusu kendiliğinden dolmuştur. İçinde şuna benzer bir yol vardır:

    ```
    /Users/vedat/Documents/GenCP-Generative-Goruntu-Uretimi-OpenStreetMap/tubitak/data/tiles36SVJ/TCI_sr_x2.tif
    ```

    Bu yolu olduğu gibi bırakabilirsiniz. Başka bir yere yazmak isterseniz kutunun
    sağındaki **…** düğmesiyle seçin.

11. **İş bitince haritaya ekle** onay kutusu **işaretli** olmalıdır. İşaretli değilse
    işaretleyin.

12. **Tahmin** satırında şu yazmalıdır:

    ```
    529 karo · çıktı 21960 × 21960 piksel · 5 m çözünürlük · yaklaşık 1447 MB
    ```

    Buradaki MB değeri sıkıştırmadan önceki kaba bir tahmindir; diskteki gerçek dosya
    yaklaşık 1255 MB olacaktır.

---

## Bölüm 5 — Çalıştırın

1. Pencerenin altındaki **Çalıştır** düğmesine tıklayın.
2. Çıktı dosyası zaten varsa **"… zaten var. Üzerine yazılsın mı?"** diye sorar.
   Gösteride **Evet**'e basın.
3. **İlerleme çubuğu** dolmaya başlar. Hemen altında **Karo 12 / 529** gibi bir yazı
   belirir ve sayı hızla büyür. Karolar saniyede on beş kadar işlendiği için ilk
   birkaç sayıyı yakalayamazsınız; bu normaldir. Önemli olan sayının **durmadan
   artması**: durursa iş takılmıştır.
4. Bu sırada QGIS **donmaz**. İsterseniz haritayı sürükleyin ya da yakınlaştırın:
   çalıştığını görmek gösterinin bir parçasıdır.
5. Yaklaşık **40 saniye** sonra ilerleme çubuğu %100'e gelir ve altında şuna benzer bir
   yazı belirir:

   ```
   Bitti · 529 karo · 37,7 sn · 1255 MB Katman eklendi ve girdiyle hizalı.
   ```

   Cümlenin sonundaki **"Katman eklendi ve girdiyle hizalı"** kısmı önemlidir: çıktının
   girdiyle aynı yerde durduğunu söyler.

6. Sol taraftaki **Katmanlar** panelinde **TCI_sr_x2** adlı yeni bir satır belirir.

---

## Bölüm 6 — Sonucu gösterin

1. **Katmanlar** panelinde **TCI_sr_x2** satırının en üstte olduğundan emin olun. Değilse
   fareyle tutup en üste sürükleyin.
2. Haritada bir yere epeyce **yakınlaşın**. Fare tekerleğini ileri çevirin ya da
   `Command + Shift + =` tuşlarına basın. Bir yerleşim yerine ya da yol kavşağına
   yakınlaşmak en iyisidir.
3. Farkı göstermek için: **Katmanlar** panelinde **TCI_sr_x2** satırının solundaki onay
   kutusunu **kapatıp açın**. Altındaki 10 m katman görünüp kaybolur; iki görüntü
   arasındaki fark budur.

**Ne söylenmeli, ne söylenmemeli.** Çıktı 5 m ızgaradadır ve ızgara doğruluğu
denetlenmiştir (Gate S). Ama bu **bikübik** bir yeniden örneklemedir: görüntü daha
yumuşaktır, yeni ayrıntı **içermez**. Gösteride "5 m çözünürlüklü görüntü ürettik"
denmemelidir; "5 m ızgaraya, eğitilmiş model takılmaya hazır bir hat kurduk" denmelidir.

---

## Bölüm 7 — İşi yarıda durdurmak (isteğe bağlı)

Gösteride durdurmanın çalıştığını göstermek isterseniz:

1. **Çalıştır**'a basın.
2. **Karo 50 / 529** civarını beklemeden, herhangi bir anda **Durdur** düğmesine
   tıklayın.
3. Birkaç saniye içinde şu yazı çıkar:

   ```
   Durduruldu. Diske eksik dosya yazılmadı.
   ```

4. Bu cümle ölçülmüştür: yarıda kesilen iş çıktı yolunda hiçbir dosya bırakmaz, var olan
   bir dosyayı da bozmaz.

---

## Sorun çıkarsa

| Belirti | Sebep | Ne yapılmalı |
|---|---|---|
| **Raster** menüsünde **GenCP SR** yok | Eklenti kurulu ama etkin değil | Bölüm 2, adım 11'e dönün: **Kurulu** listesinde onay kutusunu işaretleyin. QGIS normalde bunu kendisi yapar, o yüzden bu satıra düşmeniz beklenmez |
| **Eklentileri Yönet ve Kur** penceresinde kurulum hata verdi | Zip eksik ya da bozuk | Bölüm 0.1'i tekrar çalıştırın, `checked:` satırını görün |
| **Raster katman** kutusu boş | Haritada hiç raster katman yok | Bölüm 3'ü yapın, ya da **Dosyadan** seçeneğine geçip dosyayı doğrudan seçin |
| **Girdi** satırında "Bu raster okunamadı" yazıyor | Dosya bozuk ya da desteklenmeyen bir biçimde | Başka bir dosya deneyin |
| **Girdi** satırında "kuzeye dönük değil" yazıyor | Raster döndürülmüş | Bu eklenti döndürülmüş rasterları işlemez; önce QGIS ile yeniden projelendirin |
| **Çalıştır** düğmesi soluk | Bir eksik var | Fareyi düğmenin üzerinde bekletin: eksik olan şeyi yazar |
| Yazı "Başarısız:" diye başlıyor | İş hata verdi | **Görünüm** > **Paneller** > **Günlük Mesajları**'nı açın, **GenCP SR** sekmesine bakın |
| Çıktı katmanı haritada görünmüyor | Katman listede en altta | **Katmanlar** panelinde en üste sürükleyin |

---

## Gösteriden sonra temizlik

Çıktı dosyası yaklaşık 1,2 GB'dır. Gösteri bittiğinde silmek isterseniz:

```bash
rm /Users/vedat/Documents/GenCP-Generative-Goruntu-Uretimi-OpenStreetMap/tubitak/data/tiles36SVJ/TCI_sr_x2.tif
```

Silmeden önce QGIS'te o katmanı kaldırın: **Katmanlar** panelinde **TCI_sr_x2** satırına
sağ tıklayıp **Katmanı Kaldır** deyin. Aksi halde QGIS dosyayı açık tutar.
