# Orkesta - Web Development Environment Manager

## 📋 Proje Özeti
GTK + Python ile geliştirilmiş, web geliştiriciler için yerel sunucu ortamlarını yöneten modüler bir masaüstü uygulaması.

## 🎯 Proje Amacı
Web developer'lar için Apache, Nginx, MySQL, MariaDB, PostgreSQL, MongoDB, Memcached, Redis gibi servisleri:
- Kurabilme / Kaldırabilme
- Başlatma / Durdurma
- Yapılandırma dosyalarını düzenleme
- Veritabanı oluşturma ve yönetme

## 🏗️ Mimari Tasarım

### Modüler Yapı
- **Master Uygulama**: Ana GTK arayüzü ve koordinasyon
- **Servis Modülleri**: Her servis için ayrı Python modülü
- **Dinamik Yükleme**: `services/` klasöründen otomatik modül keşfi

### Temel Bileşenler

#### 1. Ana Uygulama (main.py)
- GTK4 arayüzü
- Servis listesi görünümü
- İşletim sistemi bilgileri paneli
- Servis modüllerini dinamik yükleme

#### 2. Servis Modülleri (services/)
Her modül şu özelliklere sahip olmalı:
```python
class ServiceModule:
    name: str              # Servis adı (Apache, Nginx, etc.)
    description: str       # Kısa açıklama
    icon: str             # İkon dosyası/adı
    
    def is_installed()    # Kurulu mu kontrolü
    def install()         # Kurulum
    def uninstall()       # Kaldırma
    def start()           # Başlat
    def stop()            # Durdur
    def restart()         # Yeniden başlat
    def status()          # Durum kontrolü
    def configure()       # Ayarlar paneli
    def get_info()        # Servis bilgileri
```

#### 3. Platform Yöneticisi (platform_manager.py)
- İşletim sistemi tespiti (Fedora/Debian/Arch)
- Paket yöneticisi seçimi (dnf/apt/pacman)
- Platform özelinde komutlar

#### 4. Yapılandırma Yöneticisi (config_manager.py)
- Servis ayarları
- Uygulama ayarları
- Kullanıcı tercihleri

## 📁 Proje Yapısı

```
orkesta/
├── main.py                      # Ana giriş noktası
├── PROJECT_REFERENCE.md         # Bu dosya
├── README.md                    # Proje açıklaması
├── requirements.txt             # Python bağımlılıkları
├── setup.py                     # Kurulum scripti
│
├── src/
│   ├── __init__.py
│   ├── app.py                   # Ana GTK uygulaması
│   ├── platform_manager.py      # OS tespiti ve paket yönetimi
│   ├── config_manager.py        # Yapılandırma yönetimi
│   ├── service_loader.py        # Dinamik modül yükleyici
│   │
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── main_window.py       # Ana pencere
│   │   ├── service_list.py      # Servis listesi widget
│   │   ├── service_panel.py     # Servis detay paneli
│   │   └── system_info.py       # Sistem bilgileri widget
│   │
│   └── utils/
│       ├── __init__.py
│       ├── system.py            # Sistem komutları
│       ├── logger.py            # Loglama
│       └── validators.py        # Doğrulama fonksiyonları
│
├── services/                    # Servis modülleri
│   ├── __init__.py
│   ├── base_service.py          # Temel servis sınıfı
│   ├── apache.py                # Apache modülü
│   ├── nginx.py                 # Nginx modülü
│   ├── mysql.py                 # MySQL modülü
│   ├── mariadb.py               # MariaDB modülü
│   ├── postgresql.py            # PostgreSQL modülü
│   ├── mongodb.py               # MongoDB modülü
│   ├── redis.py                 # Redis modülü
│   └── memcached.py             # Memcached modülü
│
├── resources/                   # Kaynaklar
│   ├── icons/                   # İkonlar
│   ├── ui/                      # GTK UI tanımları (.ui dosyaları)
│   └── config/                  # Varsayılan yapılandırmalar
│
├── flatpak/                     # Flatpak paketleme
│   ├── com.orkesta.Orkesta.yml  # Flatpak manifest
│   └── com.orkesta.Orkesta.desktop
│
└── tests/                       # Test dosyaları
    ├── __init__.py
    ├── test_platform.py
    ├── test_services.py
    └── test_ui.py
```

## 🔧 Teknoloji Stack

### Ana Teknolojiler
- **Python 3.10+**: Ana programlama dili
- **GTK4**: Kullanıcı arayüzü
- **PyGObject**: GTK Python bağlayıcıları

### İşletim Sistemi Desteği
- **Fedora**: DNF paket yöneticisi
- **Debian/Ubuntu**: APT paket yöneticisi
- **Arch Linux**: Pacman paket yöneticisi

### Flatpak
- Platform bağımsız dağıtım
- Sandbox güvenliği
- org.freedesktop.Platform runtime

## 📝 Geliştirme Aşamaları

### Faz 1: Temel Altyapı ✅ (TAMAMLANDI)
- [x] Proje yapısı oluşturma
- [x] Platform yöneticisi (OS ve paket yöneticisi tespiti)
- [x] Temel servis sınıfı (BaseService abstract class)
- [x] Servis yükleyici (Dinamik modül keşfi)
- [x] Utility modülleri (logger, system, validators)
- [x] İlk servis modülü (Apache)
- [x] Test main.py dosyası

**Tamamlanan Dosyalar:**
- ✅ `src/platform_manager.py` - OS tespiti ve paket yönetimi
- ✅ `services/base_service.py` - Temel servis abstract class
- ✅ `src/service_loader.py` - Dinamik servis yükleyici
- ✅ `src/utils/logger.py` - Merkezi loglama
- ✅ `src/utils/system.py` - Sistem utilities
- ✅ `src/utils/validators.py` - Doğrulama fonksiyonları
- ✅ `services/apache.py` - Apache servis modülü
- ✅ `main.py` - Test uygulaması

**Test Sonucu:**
```
✅ Platform tespiti çalışıyor (Linux Mint 22.2 - Debian based)
✅ APT paket yöneticisi tespit edildi
✅ Apache servis modülü başarıyla yüklendi
✅ Servis durumu kontrolü çalışıyor
```

### Faz 2: GTK Arayüzü (ŞİMDİKİ AŞAMA)
- [ ] Ana pencere tasarımı
- [ ] Servis listesi widget
- [ ] Sistem bilgileri paneli
- [ ] Servis detay paneli

### Faz 3: Servis Modülleri
- [x] Apache modülü (Temel - tamamlandı)
- [ ] Nginx modülü
- [ ] MySQL modülü
- [ ] PostgreSQL modülü
- [ ] Redis modülü
- [ ] MongoDB modülü
- [ ] Memcached modülü

### Faz 4: Gelişmiş Özellikler
- [ ] Yapılandırma editörü
- [ ] Veritabanı yönetimi
- [ ] Log görüntüleyici
- [ ] Port yönetimi

### Faz 5: Flatpak Paketleme
- [ ] Flatpak manifest oluşturma
- [ ] İzinleri yapılandırma
- [ ] Test ve paketleme
- [ ] Flathub yayınlama

## 🔐 Güvenlik Considerations

### Flatpak İzinleri
```yaml
finish-args:
  - --share=network              # Ağ erişimi
  - --filesystem=host            # Sistem dosyalarına erişim (dikkatli!)
  - --socket=system-bus          # Systemd erişimi için
  - --talk-name=org.freedesktop.systemd1
```

### Sudo/Root Erişimi
Servis yönetimi için sudo gerekliliği:
- pkexec kullanımı
- PolicyKit entegrasyonu
- Güvenli şifre yönetimi

## 📦 Bağımlılıklar

### Python Paketleri (requirements.txt)
```
PyGObject>=3.42.0
pycairo>=1.20.0
psutil>=5.9.0
pyyaml>=6.0
```

### Sistem Gereksinimleri
- GTK4
- systemd (servis yönetimi için)
- sudo/pkexec

## 🎨 UI/UX Tasarım Prensipleri

1. **Basitlik**: Kolay kullanım, minimal tıklama
2. **Görünürlük**: Servis durumları açıkça gösterilmeli
3. **Hızlı Erişim**: Sık kullanılan işlemler bir tıkla erişilebilir
4. **Güvenlik**: Kritik işlemler için onay dialogs
5. **Bilgilendirme**: Detaylı hata mesajları ve loglar

## 🚀 Çalıştırma

### Geliştirme Ortamında
```bash
python main.py
```

### Flatpak Build
```bash
flatpak-builder build-dir flatpak/com.orkesta.Orkesta.yml
flatpak-builder --run build-dir flatpak/com.orkesta.Orkesta.yml main.py
```

## 📚 Kaynaklar ve Referanslar

- [GTK4 Documentation](https://docs.gtk.org/gtk4/)
- [PyGObject API Reference](https://pygobject.readthedocs.io/)
- [Flatpak Documentation](https://docs.flatpak.org/)
- [Python systemd Integration](https://www.freedesktop.org/wiki/Software/systemd/)

## 📌 Notlar

- Her servis modülü bağımsız çalışabilmeli
- Platform tespiti öncelikle /etc/os-release dosyasını kullanmalı
- Flatpak sandbox'ında systemd erişimi için özel izinler gerekli
- Kullanıcı izinleri ve sudo gereksinimleri iyi yönetilmeli

## 🐛 Bilinen Sınırlamalar

1. Flatpak içinde systemd servisleri yönetmek karmaşık olabilir
2. Root erişimi gerektiren işlemler kullanıcı onayı gerektirir
3. Her dağıtımda paket isimleri farklı olabilir

## 📅 Son Güncelleme
**Tarih**: 7 Kasım 2025
**Durum**: Faz 1 Tamamlandı ✅ - Temel altyapı hazır
**Sonraki Adım**: GTK4 arayüzü geliştirme başlayacak

### Son Yapılanlar (7 Kasım 2025)
1. ✅ Platform yöneticisi implementasyonu
   - OS tespiti (/etc/os-release)
   - Paket yöneticisi tespiti (dnf/apt/pacman)
   - Systemd servis yönetimi
   
2. ✅ BaseService abstract class
   - Tüm servisler için temel metodlar
   - install/uninstall/start/stop/restart
   - Durum kontrolü ve bilgi toplama
   
3. ✅ ServiceLoader dinamik modül yükleyici
   - services/ klasöründen otomatik keşif
   - Servis filtreleme ve sorgulama
   
4. ✅ Utility modülleri
   - Logger: Merkezi loglama
   - System: Sistem komutları ve dosya işlemleri
   - Validators: Veri doğrulama
   
5. ✅ İlk servis modülü (Apache)
   - Multi-distro desteği (Fedora/Debian/Arch)
   - Yapılandırma seçenekleri tanımlandı
   
6. ✅ Test uygulaması
   - Sistem bilgilerini gösterir
   - Yüklü servisleri listeler
   - Servis durumlarını kontrol eder

### Mevcut Durum
- **Çalışan İşletim Sistemi**: Linux Mint 22.2 (Debian-based)
- **Tespit Edilen Paket Yöneticisi**: APT
- **Yüklü Servis Modülleri**: 1 (Apache)
- **Kod Satırı**: ~1500+ satır
