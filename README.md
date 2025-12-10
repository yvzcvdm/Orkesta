# Orkesta

Orkesta, geliştiriciler için Apache / MySQL / PHP gibi yerel servisleri yönetmeyi kolaylaştıran modern bir GTK4 + Libadwaita masaüstü uygulamasıdır. Basit bir GUI ile servisleri kurma, başlatma/durdurma, yeniden başlatma ve yapılandırma işlemlerini script tabanlı bir yaklaşımla gerçekleştirir.

**Kısa Özeti:** Orkesta, geliştirici makinelerinde web geliştirme ortamlarını hızlıca yönetmek için tasarlanmış, lehine kolaylık ve açıklık sağlayan bir araçtır.

**Özellikler**
- Basit, modern GTK4 / Libadwaita arayüzü
- Apache, MySQL, PHP için hazır script'ler ile yönetim
- Script-First mimari: tüm platform mantığı `scripts/` içinde, Python kodu yalnızca UI / orchestration yapar
- Çoklu dil desteği (locale/ dizininde çeviriler)
- Kolay paketleme: `packaging/build_deb.sh` ile .deb üretimi

**Gereksinimler**
- Python 3
- GTK4, libadwaita ve ilgili Python GObject paketleri (`python3-gi`, `gir1.2-gtk-4.0`, `gir1.2-adw-1`)
- `dpkg-deb` (paket oluşturmak için)

**Hızlı Başlangıç**

1) Depoyu klonlayın veya zaten buradaysanız kök dizine geçin:

```bash
cd /path/to/Orkesta
```

2) Gereksinimleri yükleyin (Ubuntu/Debian örneği):

```bash
sudo apt update
sudo apt install python3 python3-gi gir1.2-gtk-4.0 gir1.2-adw-1 python3-psutil python3-yaml
```

3) Uygulamayı çalıştırmak için (paket kurulu değilken):

```bash
python3 main.py
# veya packaging içinde oluşturduğunuz wrapper ile
./packaging/usr/bin/orkesta
```

4) Paket oluşturma (opsiyonel, proje kökünde):

```bash
./packaging/build_deb.sh 0.1.0
```

5) Oluşan `.deb` paketini yükleyin:

```bash
sudo dpkg -i orkesta_0.1.0.deb
```

**Servis Yönetimi ve İzinler**

Orkesta servislerle etkileşim için `scripts/` içindeki shell script'leri çağırır. Bu script'lerin çoğu sistem seviyesinde değişiklikler (başlatma/durdurma, enable/disable) yaptığı için kök yetkisine ihtiyaç duyar.

Hızlı çözüm olarak paket `postinst` script'i kurulum sırasında `/etc/sudoers.d/orkesta` dosyasını ekler ve aşağıdaki satırı içerir:

```
%sudo ALL=(ALL) NOPASSWD: /opt/orkesta/scripts/*
```

Bu sayede `sudo` parola istemeden `scripts/` altındaki komutları çalıştırır. Ancak bu, geniş yetki verdiği için güvenlik açısından bazı riskler taşır.

Güvenlik önerileri:
- Daha sınırlı izin için özel bir grup oluşturun (ör. `orkesta`) ve sadece o gruba izin verin.
- Uzun vadede `polkit`/`pkexec` tabanlı bir yetkilendirme akışı uygulayın; GUI ile uygun şekilde yetkilendirme penceresi gösterir.
- Script'lerin argüman doğrulamasını güçlendirin ve tehlikeli kabuk komutlarından kaçının.

**Nasıl Kullanılır (Kısa)**
- Uygulamayı başlatın: `orkesta` (paket kurulduysa) veya `python3 main.py`.
- UI üzerinden servis seçin ve `Start` / `Stop` / `Restart` düğmelerini kullanın.
- Eğer bir işlem başarısız olursa, `~/.cache/orkesta` veya uygulama içi log'ları kontrol edin (ayrıntılı log path için `utils/logger.py` dosyasına bakın).

**Geliştirme**
- Kod yapısı:
  - `src/` : uygulama kaynağı (UI, platform manager, service loader)
  - `services/` : servis adapter'ları
  - `scripts/` : gerçek operasyonları yapan shell script'leri
  - `packaging/` : .deb oluşturma yardımcıları
- Bir değişiklik yaptıktan sonra uygulamayı doğrudan çalıştırarak test edin:

```bash
python3 main.py
```

**Paketleme Notları**
- `packaging/build_deb.sh` otomatik olarak `DEBIAN/postinst` ve `DEBIAN/postrm` script'lerini ekler. Bu scriptler sudoers girdisini yönetir.

**Hata Giderme**
- Paket kurulumunda `dpkg-deb` izin hatası alırsanız: `packaging/build_deb.sh` dosyası içerisinde `DEBIAN` script izinlerinin (`postinst`, `postrm`) doğru (`0755`) olduğundan emin olun.
- Servisler başlatılmıyorsa: uygulama log'larını ve `/etc/sudoers.d/orkesta` dosyasını kontrol edin.

**Katkıda Bulunma**
- Katkılar memnuniyetle kabul edilir. Yeni özellik, hata düzeltme veya tercüme için PR açın.

**Lisans**
- Bu proje için lisans dosyası eklenmemişse lütfen proje sahibine danışın. (Örnek lisans olarak `MIT` eklemek yaygındır.)

---

Eğer isterseniz README'yi projenize özel ekran görüntüleri, sürüm rozetleri veya daha ayrıntılı paketleme yönergeleriyle genişletebilirim. Hangi bölümü önceliklendirmek istersiniz? (örn. polkit örneği, güvenli sudoers grup akışı, ek CLI komutları)