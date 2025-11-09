# Orkesta 🎼

**Web Development Environment Manager**

Orkesta, web geliştiriciler için yerel sunucu ortamlarını yönetmeyi kolaylaştıran, GTK tabanlı modern bir masaüstü uygulamasıdır.

## ✨ Özellikler

- 🚀 **Modüler Servis Yönetimi**: Apache, Nginx, MySQL, PostgreSQL, MongoDB, Redis ve daha fazlası
- 🔧 **Kolay Kurulum**: Tek tıkla servis kurulumu ve kaldırma
- ⚙️ **Yapılandırma Editörü**: Servis ayarlarını GUI üzerinden düzenleme
- 💾 **Veritabanı Yönetimi**: Yeni veritabanları oluşturma ve yönetme
- 🖥️ **Platform Desteği**: Fedora, Debian/Ubuntu ve Arch Linux desteği
- 📦 **Flatpak**: Platform bağımsız dağıtım

## 🎯 Kullanım Senaryoları

- Yerel geliştirme ortamı kurulumu
- Birden fazla web sunucusu yönetimi
- Veritabanı sunucularını hızlıca başlatma/durdurma
- Farklı PHP/Node.js projeler için ortam yapılandırması

## 🛠️ Teknolojiler

- **Python 3.10+**
- **GTK4** - Modern kullanıcı arayüzü
- **systemd** - Servis yönetimi
- **Flatpak** - Platform bağımsız paketleme

## 📋 Gereksinimler

- Python 3.10 veya üzeri
- GTK4
- systemd
- Linux (Fedora, Debian/Ubuntu veya Arch)

## 🚀 Kurulum

### Geliştirici Kurulumu

```bash
# Repository'yi klonlayın
git clone https://github.com/yourusername/orkestra.git
cd orkestra

# Sanal ortam oluşturun
python -m venv venv
source venv/bin/activate

# Bağımlılıkları yükleyin
pip install -r requirements.txt

# Uygulamayı çalıştırın
python main.py
```

### Flatpak Kurulumu (Yakında)

```bash
flatpak install flathub com.orkesta.Orkesta
flatpak run com.orkesta.Orkesta
```

## 📖 Dokümantasyon

Detaylı proje dokümantasyonu ve mimari bilgiler için [PROJECT_REFERENCE.md](PROJECT_REFERENCE.md) dosyasına bakın.

## 🤝 Katkıda Bulunma

Katkılarınızı bekliyoruz! Lütfen CONTRIBUTING.md dosyasını okuyun.

## 📄 Lisans

Bu proje [MIT Lisansı](LICENSE) altında lisanslanmıştır.

## 🙏 Teşekkürler

GTK, Python ve açık kaynak topluluğuna teşekkürler.

## 📞 İletişim

- Issue Tracker: GitHub Issues
- Tartışmalar: GitHub Discussions

---

**Not**: Bu proje aktif geliştirme aşamasındadır. Önerileriniz ve katkılarınız için GitHub üzerinden iletişime geçebilirsiniz.

## Hedef Kullanıcılar
- Web geliştiriciler
- Backend mühendisleri
- DevOps ve sistem yöneticileri
- Laravel, Django, Flask, Node.js, PHP geliştiricileri

## Platformlar
- Linux (Debian, Ubuntu, Arch, Fedora vb.)

## Lisans
MIT / GPL / (karar sizde)
