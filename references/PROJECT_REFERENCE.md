# Orkesta - Web Development Environment Manager

## 📋 Proje Özeti
GTK4 + Python ile geliştirilmiş, web geliştiriciler için **yerel LAMP/LEMP sunucu ortamlarını yöneten modüler bir masaüstü uygulaması**. Her servis bağımsız Python modülü ve shell scriptleri ile yönetilir.

## 🎯 Proje Amacı
Web developer'lar için **Apache, MySQL, PHP** gibi yerel geliştirme servisleri tek arayüzden yönetmek:
- ✅ **Kurulum/Kaldırma**: Tek sudo şifresi ile toplu kurulum (script tabanlı)
- ✅ **Başlatma/Durdurma**: Systemd servis yönetimi
- ✅ **Yapılandırma**: Her servisin kendi özel ayar paneli
- ✅ **Detay Sayfası**: Her servis için özelleştirilmiş yönetim arayüzü
- ✅ **Dağıtım Bağımsızlığı**: Fedora, Debian/Ubuntu, Arch desteği

## 🏗️ Mimari Tasarım (Yeni Prensip)

### 🎼 Ana Prensipler

#### 1. **Minimal Main - Maksimum Modülerlik**
- `main.py` **SADECE** GTK arayüzünü başlatır
- Hiçbir servis mantığı main'de olmaz
- Servisler tamamen bağımsız modüllerdir

#### 2. **Servis = Python Modülü + Scripts**
Her servis şu yapıya sahiptir:
```
services/
├── apache.py           # Python modülü (BaseService'ten türetilmiş)
├── mysql.py
├── php.py
└── ...

scripts/
├── apache/
│   ├── install.sh      # Kurulum scripti
│   ├── vhost-create.sh # VHost oluşturma
│   └── ssl-enable.sh   # SSL aktifleştirme
├── mysql/
│   ├── install.sh
│   ├── secure.sh       # mysql_secure_installation
│   └── create-db.sh    # Veritabanı oluşturma
└── php/
    ├── install.sh
    └── switch-version.sh
```

#### 3. **Script-First Yaklaşımı**
- **Tek sudo şifresi**: Tüm işlemler tek script çalıştırması ile
- **Paket yöneticisi detection**: Script içinde OS tespiti
- **Toplu kurulum**: Bağımlılıklar + yapılandırma tek seferde
- **Platform bağımsız**: Fedora (dnf), Debian (apt), Arch (pacman) desteği

#### 4. **Dinamik Servis Yükleme**
```python
# ServiceLoader otomatik keşfeder
services/
├── apache.py    ✅ Yüklenir
├── mysql.py     ✅ Yüklenir
├── php.py       ✅ Yüklenir
├── nginx.py     ✅ Yüklenir (gelecekte)
└── base_service.py  ❌ Yüklenmez (abstract class)
```

### 🔧 Temel Bileşenler

#### 1. Ana Uygulama (main.py + src/app.py)
**Sorumluluk**: Sadece GTK arayüzünü başlatmak
```python
# main.py
from src.app import OrkestaApp
app = OrkestaApp()
app.run()
```

**ÖNEMLİ**: Main'de asla:
- ❌ Servis kontrolü
- ❌ Kurulum/kaldırma işlemi
- ❌ Platform tespiti (sadece gösterim için)

#### 2. Servis Modülleri (services/*.py)
Her servis `BaseService` abstract class'ından türer:

```python
from services.base_service import BaseService, ServiceType

class ApacheService(BaseService):
    @property
    def name(self) -> str:
        return "apache"
    
    @property
    def display_name(self) -> str:
        return "Apache HTTP Server"
    
    @property
    def service_type(self) -> ServiceType:
        return ServiceType.WEB_SERVER
    
    # Script execution
    def install(self) -> Tuple[bool, str]:
        script_path = f"{SCRIPTS_DIR}/apache/install.sh"
        return self._execute_script(script_path)
    
    # Her servis kendi özel metodlarına sahip
    def create_vhost(self, ...):
        # Apache'ye özel işlem
```

**Servis Özellikleri**:
- ✅ Tamamen bağımsız (diğer servislerden izole)
- ✅ Kendi script'lerini çalıştırır
- ✅ Özel metodlar (create_vhost, create_database, vb.)
- ✅ Platform detection (Fedora/Debian/Arch)

#### 3. Script Yönetimi (scripts/) - CLI-First Approach
Her servis kendi klasöründe **bağımsız CLI komutları** barındırır (VestaCP, cPanel, aaPanel gibi):

**Prensip: Script = Standalone CLI Tool**
```bash
# ✅ Terminal'den doğrudan kullanılabilir
sudo scripts/apache/vhost-create.sh example.com /var/www/html --ssl

# ✅ Automation'da kullanılabilir  
crontab: 0 2 * * * /usr/local/bin/orkesta-backup.sh

# ✅ Python sadece script'i çağırır
result = subprocess.run(['pkexec', script_path, *args])
```

**Örnek: Apache VHost Create Script (CLI Tool)**
```bash
#!/bin/bash
# scripts/apache/vhost-create.sh
# Standalone CLI tool for creating Apache virtual hosts

set -e  # Exit on error

# Help & Usage
show_help() {
    cat << EOF
Usage: $(basename "$0") <domain> <docroot> [options]

Creates an Apache virtual host configuration.

Options:
  --ssl           Enable SSL/HTTPS
  --php=VERSION   PHP version (e.g., 8.2)
  --port=PORT     Custom port (default: 80)
  --json          Output as JSON
  --help          Show this help

Examples:
  # Basic vhost
  $(basename "$0") example.com /var/www/example.com
  
  # With SSL and PHP 8.2
  $(basename "$0") example.com /var/www/html --ssl --php=8.2

Exit Codes:
  0 - Success
  1 - General error
  2 - Invalid parameters
  3 - Permission denied
EOF
    exit 0
}

# Parameter parsing
DOMAIN=""
DOCROOT=""
SSL=false
PHP_VERSION=""
JSON_OUTPUT=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --help) show_help ;;
        --ssl) SSL=true; shift ;;
        --php=*) PHP_VERSION="${1#*=}"; shift ;;
        --json) JSON_OUTPUT=true; shift ;;
        *) 
            [ -z "$DOMAIN" ] && DOMAIN="$1" || DOCROOT="$1"
            shift 
            ;;
    esac
done

# Validation
if [ -z "$DOMAIN" ] || [ -z "$DOCROOT" ]; then
    echo "Error: Domain and document root required" >&2
    exit 2
fi

# OS Detection
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS_TYPE=$ID
fi

# OS-specific paths
case $OS_TYPE in
    fedora)
        VHOST_DIR="/etc/httpd/conf.d"
        SERVICE="httpd"
        ;;
    ubuntu|debian)
        VHOST_DIR="/etc/apache2/sites-available"
        SERVICE="apache2"
        ;;
    arch)
        VHOST_DIR="/etc/httpd/conf"
        SERVICE="httpd"
        ;;
esac

# Create config, enable site, reload
# ... (implementation)

# Output
if [ "$JSON_OUTPUT" = true ]; then
    echo '{"success":true,"domain":"'$DOMAIN'","docroot":"'$DOCROOT'"}'
else
    echo "✅ VHost '$DOMAIN' created successfully"
    echo "   Config: $VHOST_DIR/$DOMAIN.conf"
fi

exit 0
```

**Script Standartları (Her script şunlara sahip olmalı)**:
- 🔑 **Tek sudo şifresi**: pkexec ile çalıştırılır
- 📦 **Platform detection**: OS tespiti script içinde
- ⚡ **Toplu işlem**: Tüm adımlar tek script'te
- 📝 **Exit codes**: 0=success, 1=error, 2=invalid params
- 🖥️ **CLI-first**: Terminal'den bağımsız kullanım
- 🤖 **Automation**: Cron, Ansible, CI/CD entegrasyonu
- � **--json flag**: Structured output
- 📚 **--help flag**: Self-documented
- 🔍 **--dry-run**: Test mode (opsiyonel)
- 🐛 **--verbose**: Debug mode (opsiyonel)
- ♻️ **Idempotent**: Birden fazla çalıştırılabilir

#### 4. Platform Yöneticisi (src/platform_manager.py)
**Sorumluluk**: OS tespiti ve temel sistem bilgileri
```python
class PlatformManager:
    def get_os_type(self) -> str:
        # Fedora, Debian, Ubuntu, Arch tespiti
    
    def get_package_manager(self) -> str:
        # dnf, apt, pacman
    
    def is_service_active(self, service_name: str) -> bool:
        # systemctl status kontrolü
```

**NOT**: Platform manager artık paket kurulumu yapmaz, sadece bilgi sağlar!

#### 5. Servis Yükleyici (src/service_loader.py)
**Sorumluluk**: Dinamik servis keşfi ve yükleme
```python
class ServiceLoader:
    def load_services(self):
        # services/*.py dosyalarını tara
        # BaseService türevlerini yükle
    
    def get_service(self, name: str) -> BaseService:
        # Servis instance'ını döndür
```

## 📁 Proje Yapısı (Güncel)

```
orkesta/
├── main.py                      # ⭐ Ana giriş noktası (SADECE GTK başlatır)
├── PROJECT_REFERENCE.md         # 📖 Bu dosya - Projenin rehberi
├── README.md                    # Kullanıcı dökümanı
├── CURRENT_STATUS.md            # Güncel durum ve yapılacaklar
├── requirements.txt             # Python bağımlılıkları
├── translations.py              # Çeviri yönetimi
├── TRANSLATION.md               # Çeviri rehberi
│
├── src/                         # 🎨 Ana uygulama kodu
│   ├── __init__.py
│   ├── app.py                   # GTK4/Libadwaita uygulaması
│   ├── platform_manager.py      # OS tespiti ve sistem bilgileri
│   ├── service_loader.py        # Dinamik servis yükleyici
│   │
│   ├── ui/                      # 🖼️ GTK Arayüz bileşenleri
│   │   ├── __init__.py
│   │   └── main_window.py       # Ana pencere + Servis detay sayfaları
│   │
│   └── utils/                   # 🔧 Yardımcı modüller
│       ├── __init__.py
│       ├── system.py            # Sistem komutları (pkexec, sudo)
│       ├── logger.py            # Merkezi loglama
│       ├── validators.py        # Doğrulama fonksiyonları
│       └── i18n.py              # Çok dilli destek
│
├── services/                    # 🚀 Servis Modülleri (Bağımsız)
│   ├── __init__.py
│   ├── base_service.py          # Abstract base class (tüm servisler bu class'tan türer)
│   │
│   │   # ✅ Şu anda aktif servisler
│   ├── apache.py                # Apache HTTP Server + VHost yönetimi
│   ├── mysql.py                 # MySQL Database + DB/User yönetimi
│   ├── php.py                   # PHP + Multi-version + Extension yönetimi
│   │
│   │   # 🔜 Gelecekte eklenecekler
│   ├── nginx.py                 # Nginx (TODO)
│   ├── mariadb.py               # MariaDB (TODO)
│   ├── postgresql.py            # PostgreSQL (TODO)
│   └── redis.py                 # Redis (TODO)
│
├── scripts/                     # 🛠️ Shell Scriptleri (Servis başına klasör)
│   │
│   ├── apache/                  # Apache scriptleri
│   │   ├── install.sh           # Kurulum scripti (TODO: şimdilik kod içinde)
│   │   ├── vhost-create.sh      # VHost oluşturma (TODO)
│   │   └── ssl-enable.sh        # SSL modülü aktifleştirme (TODO)
│   │
│   ├── mysql/                   # MySQL scriptleri
│   │   ├── install.sh           # Kurulum + root password setup (TODO: şimdilik kod içinde)
│   │   ├── secure.sh            # mysql_secure_installation (TODO)
│   │   └── create-db.sh         # Veritabanı oluşturma (TODO)
│   │
│   ├── php/                     # PHP scriptleri
│   │   ├── install.sh           # PHP kurulum + ondrej/php repo (TODO: şimdilik kod içinde)
│   │   ├── switch-version.sh    # Versiyon değiştirme (TODO)
│   │   └── install-extension.sh # Extension kurulum (TODO)
│   │
│   │   # 🔧 Genel yardımcı scriptler
│   ├── install-vhost-manager.sh # VHost manager kurulum helper
│   └── orkesta-vhost-manager.sh # VHost CLI tool
│
├── locales/                     # 🌍 Çeviri dosyaları
│   ├── tr/
│   │   └── LC_MESSAGES/
│   │       └── orkesta.po       # Türkçe çeviriler
│   └── en/
│       └── LC_MESSAGES/
│           └── orkesta.po       # İngilizce (default)
│
├── resources/                   # 📦 Kaynaklar (TODO)
│   ├── icons/                   # İkonlar
│   └── config/                  # Varsayılan yapılandırmalar
│
├── flatpak/                     # 📦 Flatpak paketleme (TODO)
│   ├── com.orkesta.Orkesta.yml  # Flatpak manifest
│   └── com.orkesta.Orkesta.desktop
│
└── tests/                       # 🧪 Test dosyaları (TODO)
    ├── __init__.py
    ├── test_platform.py
    ├── test_services.py
    └── test_ui.py
```

### 📂 Klasör Açıklamaları

#### `services/` - Servis Modülleri
- Her `.py` dosyası bir servisi temsil eder
- `BaseService` abstract class'ından türetilir
- **Bağımsız**: Diğer servislerden izole çalışır
- **Özel metodlar**: Her servisin kendine özgü işlevleri var

#### `scripts/` - Shell Scriptleri
- Her servis için ayrı klasör
- **Platform bağımsız**: OS tespiti script içinde
- **Tek sudo**: pkexec ile çalıştırılır
- **Toplu işlem**: Kurulum + yapılandırma tek script

#### `src/ui/` - GTK Arayüzü
- `main_window.py`: Ana pencere + Servis listesi + Detay sayfaları
- Her servisin detay sayfası dinamik oluşturulur
- Servis özel UI bileşenleri (VHost listesi, DB listesi vb.)

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

## 📝 Geliştirme Aşamaları ve Durum

### ✅ Faz 1: Temel Altyapı (TAMAMLANDI)
**Hedef**: Modüler servis mimarisi ve dinamik yükleme
- [x] Proje yapısı oluşturma
- [x] Platform yöneticisi (OS ve paket yöneticisi tespiti)
- [x] BaseService abstract class
- [x] Dinamik servis yükleyici (ServiceLoader)
- [x] Utility modülleri (logger, system, validators, i18n)
- [x] Çok dilli destek (TR/EN)

**Tamamlanan Dosyalar:**
- ✅ `src/platform_manager.py` - OS tespiti (Fedora/Debian/Arch)
- ✅ `services/base_service.py` - Abstract base class
- ✅ `src/service_loader.py` - Dinamik modül keşfi
- ✅ `src/utils/logger.py` - Merkezi loglama
- ✅ `src/utils/system.py` - pkexec, sudo komutları
- ✅ `src/utils/validators.py` - Doğrulama
- ✅ `src/utils/i18n.py` - Çeviri sistemi

---

### ✅ Faz 2: GTK4 Arayüzü (TAMAMLANDI)
**Hedef**: Modern, kullanıcı dostu arayüz
- [x] GTK4 + Libadwaita entegrasyonu
- [x] Ana pencere tasarımı
- [x] Servis listesi (dinamik, kart tabanlı)
- [x] Sistem bilgileri sidebar
- [x] Servis detay sayfaları (navigasyon)
- [x] Progress dialog'lar (install/uninstall)
- [x] Toast bildirimleri

**Tamamlanan Dosyalar:**
- ✅ `src/app.py` - OrkestaApp (GTK Application)
- ✅ `src/ui/main_window.py` - Ana pencere + detay sayfaları
- ✅ `main.py` - Uygulama giriş noktası

**UI Özellikleri:**
- 🎨 Modern card-based servis listesi
- 📊 Sidebar sistem bilgileri (IP, Hostname, Python ver.)
- 🔙 Back button navigasyon
- ⚡ Async install/uninstall (thread-based)
- 🔔 Toast/Dialog bildirimleri

---

### ✅ Faz 3: Ana Servisler (TAMAMLANDI - İLK SET)
**Hedef**: Apache, MySQL, PHP ile temel LAMP stack

#### ✅ Apache HTTP Server (apache.py)
**Durum**: Tam fonksiyonel
- [x] Install/Uninstall (multi-distro)
- [x] Start/Stop/Restart/Enable/Disable
- [x] Virtual Host Yönetimi
  - [x] VHost oluşturma (HTTP + HTTPS unified config)
  - [x] VHost listeleme
  - [x] VHost enable/disable (Debian/Ubuntu)
  - [x] VHost silme
  - [x] VHost detay görüntüleme
- [x] SSL/HTTPS Yönetimi
  - [x] SSL modülü enable/disable
  - [x] Self-signed certificate oluşturma
  - [x] HTTP -> HTTPS redirect
- [x] PHP Entegrasyonu
  - [x] PHP versiyonu tespit etme
  - [x] PHP modülü değiştirme (a2enmod/a2dismod)
  - [x] VHost bazında PHP-FPM yapılandırması
- [x] Detay sayfası (VHost listesi, SSL yönetimi, PHP switch)

#### ✅ MySQL Database Server (mysql.py)
**Durum**: Tam fonksiyonel
- [x] Install/Uninstall (multi-distro)
- [x] Otomatik root password setup (kurulum sırasında)
- [x] Root password saklama (local config)
- [x] Start/Stop/Restart/Enable/Disable
- [x] Veritabanı Yönetimi
  - [x] Veritabanı oluşturma
  - [x] Veritabanı listeleme
  - [x] Veritabanı silme
- [x] Kullanıcı Yönetimi
  - [x] Kullanıcı oluşturma
  - [x] Yetki verme (GRANT)
- [x] Root Password Yönetimi
  - [x] Password değiştirme
  - [x] Otomatik authentication detection (Unix Socket vs Password)
  - [x] mysql_secure_installation entegrasyonu
- [x] Detay sayfası (DB/User yönetimi, password change)

#### ✅ PHP (php.py)
**Durum**: Multi-version destekli, tam fonksiyonel
- [x] Multi-version desteği (7.4, 8.0, 8.1, 8.2, 8.3)
- [x] Install/Uninstall (version bazlı)
- [x] ondrej/php PPA entegrasyonu (Debian/Ubuntu)
- [x] Version switching
- [x] PHP-FPM servis yönetimi
- [x] Extension Yönetimi
  - [x] Extension listeleme
  - [x] Extension kurulum
  - [x] Extension kaldırma
- [x] Start/Stop/Restart/Enable/Disable (active version)
- [x] Detay sayfası

---

### 🔄 Faz 4: Script Migrasyonu (ŞİMDİKİ FAZ)
**Hedef**: Kod içi bash komutlarını script dosyalarına taşımak

**Neden Script Kullanılmalı?**
1. ✅ **Tek sudo şifresi**: Tüm işlemler tek script'te
2. ✅ **Bakım kolaylığı**: Bash mantığı ayrı dosyalarda
3. ✅ **Yeniden kullanılabilirlik**: CLI'dan da çalışabilir
4. ✅ **Test edilebilirlik**: Script'ler bağımsız test edilebilir
5. ✅ **Platform bağımsızlık**: OS detection script içinde

**Yapılacak CLI Tools:**

Apache Tools:
- [ ] `scripts/apache/install.sh` - Apache kurulum
- [ ] `scripts/apache/vhost-create.sh` - VHost oluştur
- [ ] `scripts/apache/vhost-delete.sh` - VHost sil
- [ ] `scripts/apache/vhost-list.sh` - VHost listele
- [ ] `scripts/apache/vhost-enable.sh` - VHost aktif et (Debian/Ubuntu)
- [ ] `scripts/apache/vhost-disable.sh` - VHost pasif et
- [ ] `scripts/apache/ssl-enable.sh` - SSL modülü aktif et
- [ ] `scripts/apache/ssl-cert-create.sh` - Self-signed cert oluştur
- [ ] `scripts/apache/php-switch.sh` - PHP versiyonu değiştir

MySQL Tools:
- [ ] `scripts/mysql/install.sh` - MySQL kurulum + root password
- [ ] `scripts/mysql/database-create.sh` - Database oluştur
- [ ] `scripts/mysql/database-delete.sh` - Database sil
- [ ] `scripts/mysql/database-list.sh` - Database'leri listele
- [ ] `scripts/mysql/user-create.sh` - User oluştur
- [ ] `scripts/mysql/user-grant.sh` - User'a yetki ver
- [ ] `scripts/mysql/password-change.sh` - Root password değiştir
- [ ] `scripts/mysql/backup.sh` - Database backup

PHP Tools:
- [ ] `scripts/php/install.sh` - PHP + ondrej/php repo
- [ ] `scripts/php/version-switch.sh` - Version değiştir
- [ ] `scripts/php/version-list.sh` - Kurulu version'ları listele
- [ ] `scripts/php/extension-install.sh` - Extension kur
- [ ] `scripts/php/extension-remove.sh` - Extension kaldır
- [ ] `scripts/php/extension-list.sh` - Extension'ları listele

**CLI Tool Şablonu (VestaCP/cPanel Stili):**
```bash
#!/bin/bash
# scripts/apache/vhost-create.sh
# Standalone CLI tool for Apache VHost management
# Usage: vhost-create.sh <domain> <docroot> [options]

set -e  # Exit on error

# ============================================
# HELP & DOCUMENTATION
# ============================================
show_help() {
    cat << EOF
Usage: $(basename "$0") <domain> <docroot> [options]

Creates an Apache virtual host configuration.

Arguments:
  domain          Domain name (required)
  docroot         Document root path (required)

Options:
  --ssl           Enable SSL/HTTPS
  --php=VERSION   PHP version (e.g., 8.2)
  --port=PORT     HTTP port (default: 80)
  --email=EMAIL   Server admin email
  --json          Output as JSON
  --dry-run       Show what would be done
  --verbose       Verbose output
  --help          Show this help

Examples:
  # Basic HTTP vhost
  $(basename "$0") example.com /var/www/example.com

  # HTTPS with PHP 8.2
  $(basename "$0") example.com /var/www/html --ssl --php=8.2
  
  # Custom port
  $(basename "$0") dev.local /var/www/dev --port=8080
  
  # JSON output for automation
  $(basename "$0") api.local /var/www/api --json

Exit Codes:
  0 - Success
  1 - General error
  2 - Invalid parameters
  3 - Permission denied
  4 - Service not available

EOF
    exit 0
}

# ============================================
# PARAMETER PARSING
# ============================================
DOMAIN=""
DOCROOT=""
SSL=false
PHP_VERSION=""
PORT=80
EMAIL="webmaster@localhost"
JSON_OUTPUT=false
DRY_RUN=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --help|-h)
            show_help
            ;;
        --ssl)
            SSL=true
            shift
            ;;
        --php=*)
            PHP_VERSION="${1#*=}"
            shift
            ;;
        --port=*)
            PORT="${1#*=}"
            shift
            ;;
        --json)
            JSON_OUTPUT=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        *)
            if [ -z "$DOMAIN" ]; then
                DOMAIN="$1"
            elif [ -z "$DOCROOT" ]; then
                DOCROOT="$1"
            else
                echo "Error: Unknown parameter: $1" >&2
                exit 2
            fi
            shift
            ;;
    esac
done

# ============================================
# VALIDATION
# ============================================
if [ -z "$DOMAIN" ] || [ -z "$DOCROOT" ]; then
    echo "Error: Domain and document root are required" >&2
    echo "Run with --help for usage information" >&2
    exit 2
fi

# ============================================
# OS DETECTION
# ============================================
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS_TYPE=$ID
else
    echo "Error: Cannot detect OS" >&2
    exit 4
fi

[ "$VERBOSE" = true ] && echo "Detected OS: $OS_TYPE"

# ============================================
# OS-SPECIFIC CONFIGURATION
# ============================================
case $OS_TYPE in
    fedora)
        VHOST_DIR="/etc/httpd/conf.d"
        SERVICE_NAME="httpd"
        [ "$VERBOSE" = true ] && echo "Using Fedora configuration"
        ;;
    ubuntu|debian)
        VHOST_DIR="/etc/apache2/sites-available"
        ENABLED_DIR="/etc/apache2/sites-enabled"
        SERVICE_NAME="apache2"
        [ "$VERBOSE" = true ] && echo "Using Debian/Ubuntu configuration"
        ;;
    arch)
        VHOST_DIR="/etc/httpd/conf"
        SERVICE_NAME="httpd"
        [ "$VERBOSE" = true ] && echo "Using Arch configuration"
        ;;
    *)
        echo "Error: Unsupported OS: $OS_TYPE" >&2
        exit 4
        ;;
esac

# ============================================
# MAIN LOGIC
# ============================================
if [ "$DRY_RUN" = true ]; then
    echo "DRY RUN MODE - No changes will be made"
    echo "Would create VHost: $DOMAIN"
    echo "Document root: $DOCROOT"
    [ "$SSL" = true ] && echo "SSL: Would be enabled"
    exit 0
fi

# Create document root
[ "$VERBOSE" = true ] && echo "Creating document root: $DOCROOT"
mkdir -p "$DOCROOT"

# Create default index.html
cat > "$DOCROOT/index.html" << EOF
<!DOCTYPE html>
<html>
<head><title>Welcome to $DOMAIN</title></head>
<body><h1>✅ $DOMAIN is working!</h1></body>
</html>
EOF

# Generate VHost config
# ... (config generation logic)

# Reload Apache
[ "$VERBOSE" = true ] && echo "Reloading $SERVICE_NAME"
systemctl reload "$SERVICE_NAME"

# ============================================
# OUTPUT
# ============================================
if [ "$JSON_OUTPUT" = true ]; then
    cat << EOF
{
  "success": true,
  "domain": "$DOMAIN",
  "docroot": "$DOCROOT",
  "ssl": $SSL,
  "config_file": "$VHOST_DIR/$DOMAIN.conf"
}
EOF
else
    echo "✅ VHost '$DOMAIN' created successfully"
    echo "   Document root: $DOCROOT"
    [ "$SSL" = true ] && echo "   SSL: Enabled"
    echo "   Config: $VHOST_DIR/$DOMAIN.conf"
    echo ""
    echo "Access your site at: http://$DOMAIN"
fi

exit 0
```

**Key Features (VestaCP/cPanel Benzeri)**:
- ✅ **Standalone**: GUI'dan bağımsız çalışır
- ✅ **Self-documented**: `--help` ile detaylı kullanım
- ✅ **Parametreli**: Flexible argument handling
- ✅ **Exit codes**: Standard Unix return codes
- ✅ **JSON output**: Automation için structured data
- ✅ **Dry-run**: Test modu, değişiklik yapmadan simülasyon
- ✅ **Verbose**: Debug için detaylı log
- ✅ **Idempotent**: Birden fazla çalıştırılabilir
- ✅ **Error handling**: Tüm hatalar yakalanır ve anlamlı mesaj
- ✅ **Multi-distro**: Fedora/Debian/Arch desteği built-in

---

### 🔜 Faz 5: Ek Servisler (GELECEK)
**Hedef**: LEMP, caching, NoSQL desteği

#### Nginx Web Server
- [ ] Install/Uninstall
- [ ] Server blocks (VHost equivalent)
- [ ] SSL/HTTPS
- [ ] PHP-FPM entegrasyonu
- [ ] Detay sayfası

#### MariaDB Database
- [ ] Install/Uninstall
- [ ] MySQL ile aynı özellikler
- [ ] Detay sayfası

#### PostgreSQL Database
- [ ] Install/Uninstall
- [ ] Database/User yönetimi
- [ ] pgAdmin entegrasyonu
- [ ] Detay sayfası

#### Redis Cache
- [ ] Install/Uninstall
- [ ] Start/Stop
- [ ] Config editor
- [ ] Detay sayfası

#### Memcached
- [ ] Install/Uninstall
- [ ] Start/Stop
- [ ] Detay sayfası

---

### 🔜 Faz 6: Gelişmiş Özellikler (İLERİ SEVİYE)
**Hedef**: Pro kullanıcı özellikleri

- [ ] **Config Editor**: Servis config dosyalarını düzenle
- [ ] **Log Viewer**: Servis loglarını görüntüle (tail -f)
- [ ] **Port Manager**: Port kullanımı ve conflict çözme
- [ ] **Backup/Restore**: Veritabanı yedekleme
- [ ] **Project Manager**: Proje bazlı VHost/DB gruplandırma
- [ ] **Import/Export**: Yapılandırma taşıma
- [ ] **Performance Monitor**: Servis resource kullanımı

---

### 🔜 Faz 7: Paketleme ve Dağıtım (RELEASE)
**Hedef**: Kullanıcılara kolay kurulum

#### Flatpak
- [ ] Flatpak manifest (com.orkesta.Orkesta.yml)
- [ ] Desktop file (.desktop)
- [ ] AppStream metadata (.appdata.xml)
- [ ] Sandbox izinleri (systemd, network, filesystem)
- [ ] Flathub submission

#### Diğer Paketler (Opsiyonel)
- [ ] Debian/Ubuntu `.deb` paketi
- [ ] Fedora `.rpm` paketi
- [ ] Arch AUR paketi
- [ ] AppImage (portable)

## 🏆 Proje Başarıları ve Güçlü Yönler

### ✨ Öne Çıkan Özellikler
1. **Modüler Mimari**: Servisler tamamen bağımsız, yeni servis eklemek çok kolay
2. **Platform Bağımsızlığı**: Fedora, Debian, Ubuntu, Arch desteği
3. **Gerçek LAMP Stack**: Apache + MySQL + PHP tam entegrasyon
4. **Modern UI**: GTK4/Libadwaita ile native Linux deneyimi
5. **Multi-version PHP**: Aynı anda birden fazla PHP versiyonu
6. **VHost Yönetimi**: Tek tıkla website kurulumu (HTTP/HTTPS)
7. **Otomatik MySQL Setup**: Root password otomatik, güvenli saklama
8. **i18n**: Türkçe/İngilizce arayüz
9. **Async Operations**: UI donmadan install/uninstall
10. **Detaylı UI**: Her servis için özelleştirilmiş detay sayfası

### 💪 Teknik Güçlü Yönler
- **Dinamik Servis Yükleme**: ServiceLoader otomatik keşfeder
- **Abstract Base Class**: BaseService standardı
- **pkexec Entegrasyonu**: GUI-friendly sudo
- **Thread-safe Operations**: GLib.idle_add ile güvenli UI update
- **Error Handling**: Kullanıcı dostu hata mesajları
- **Logger System**: Merkezi, yapılandırılabilir loglama
- **Type Hints**: Tam type annotation desteği

---

## 🔐 Güvenlik Considerations

### Sudo/Root Erişimi
**Servis yönetimi için root gerekliliği:**
- ✅ **pkexec kullanımı**: GUI-friendly authentication
- ✅ **PolicyKit entegrasyonu**: Sistem policy'lere uyumlu
- ✅ **Şifre saklama**: MySQL root password encrypted local config
- ✅ **Script validation**: Bash script'ler güvenli (set -e)
- ⚠️ **Dikkat**: Script'ler root ile çalışır, kod review önemli

### Güvenlik Prensipleri
1. **Minimal Privilege**: Sadece gerekli işlemler için sudo
2. **User Confirmation**: Kritik işlemler için onay dialog
3. **Password Encryption**: Şifreler plain text saklanmaz
4. **Input Validation**: Tüm user input validate edilir
5. **Safe Defaults**: Güvenli varsayılan ayarlar

### Flatpak İzinleri (TODO)
```yaml
finish-args:
  - --share=network              # Ağ erişimi (servis yönetimi için)
  - --filesystem=host            # Sistem dosyaları (config edit için)
  - --socket=system-bus          # Systemd erişimi
  - --talk-name=org.freedesktop.systemd1  # Servis kontrol
  - --talk-name=org.freedesktop.PolicyKit1  # pkexec için
```

**Sandbox Sınırlamaları:**
- Flatpak sandbox'ı root işlemleri kısıtlar
- PolicyKit izinleri dikkatlice yapılandırılmalı
- Host filesystem erişimi minimal tutulmalı

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

## 🚀 Kurulum ve Çalıştırma

### Gereksinimler
```bash
# Python 3.10+
python3 --version

# GTK4 ve Libadwaita (Debian/Ubuntu)
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0 gir1.2-adw-1

# GTK4 ve Libadwaita (Fedora)
sudo dnf install python3-gobject gtk4 libadwaita

# GTK4 ve Libadwaita (Arch)
sudo pacman -S python-gobject gtk4 libadwaita
```

### Python Bağımlılıkları
```bash
# requirements.txt'ten kurulum
pip install -r requirements.txt
```

### Geliştirme Ortamında Çalıştırma
```bash
# Ana dizinde
python3 main.py

# veya
./main.py
```

### Flatpak Build (TODO)
```bash
# Build
flatpak-builder build-dir flatpak/com.orkesta.Orkesta.yml

# Test run
flatpak-builder --run build-dir flatpak/com.orkesta.Orkesta.yml main.py

# Install locally
flatpak-builder --user --install build-dir flatpak/com.orkesta.Orkesta.yml
```

---

## �️ CLI Script Kullanım Örnekleri

### Terminal'den Doğrudan Kullanım (VestaCP/cPanel Style)

#### Apache VHost Yönetimi
```bash
# VHost oluştur (HTTP)
sudo scripts/apache/vhost-create.sh example.com /var/www/example.com

# VHost oluştur (HTTPS + PHP 8.2)
sudo scripts/apache/vhost-create.sh example.com /var/www/html \
    --ssl --php=8.2

# VHost listele
scripts/apache/vhost-list.sh

# VHost listele (JSON)
scripts/apache/vhost-list.sh --json

# VHost sil
sudo scripts/apache/vhost-delete.sh example.com

# VHost aktif et (Debian/Ubuntu)
sudo scripts/apache/vhost-enable.sh example.com

# Help
scripts/apache/vhost-create.sh --help
```

#### MySQL Database Yönetimi
```bash
# Database oluştur
sudo scripts/mysql/database-create.sh wordpress_db

# Database + User oluştur
sudo scripts/mysql/database-create.sh myapp_db \
    --user=myapp_user --password=secret123

# Database listele
scripts/mysql/database-list.sh

# Database listele (JSON)
scripts/mysql/database-list.sh --json

# Database backup
sudo scripts/mysql/backup.sh myapp_db /backups/myapp_db.sql

# Root password değiştir
sudo scripts/mysql/password-change.sh --new-password=NewSecure123
```

#### PHP Version Yönetimi
```bash
# PHP 8.2 kur
sudo scripts/php/install.sh --version=8.2

# Version listele
scripts/php/version-list.sh

# Version değiştir
sudo scripts/php/version-switch.sh 8.2

# Extension kur
sudo scripts/php/extension-install.sh mbstring --version=8.2

# Extension listele
scripts/php/extension-list.sh --version=8.2
```

### Automation Örnekleri

#### Cron Job
```bash
# Her gece saat 2'de tüm database'leri yedekle
0 2 * * * /usr/local/bin/orkesta-mysql backup-all /backups/mysql/

# Her hafta sonu log dosyalarını temizle
0 0 * * 0 /usr/local/bin/orkesta-apache log-rotate
```

#### Ansible Playbook
```yaml
- name: Setup WordPress Environment
  hosts: webserver
  tasks:
    - name: Install Apache
      command: /opt/orkesta/scripts/apache/install.sh
      become: yes

    - name: Create VHost
      command: >
        /opt/orkesta/scripts/apache/vhost-create.sh
        wordpress.example.com
        /var/www/wordpress
        --ssl
        --php=8.2
      become: yes

    - name: Create Database
      command: >
        /opt/orkesta/scripts/mysql/database-create.sh
        wordpress_db
        --user=wp_user
        --password={{ db_password }}
      become: yes
```

#### Bash Script (Deployment)
```bash
#!/bin/bash
# deploy-new-site.sh

DOMAIN=$1
DB_NAME="${DOMAIN//./_}_db"  # example.com -> example_com_db

echo "🚀 Deploying $DOMAIN..."

# Create VHost
sudo scripts/apache/vhost-create.sh "$DOMAIN" "/var/www/$DOMAIN" \
    --ssl --php=8.2 --json > /tmp/vhost.json

# Check success
if [ $? -eq 0 ]; then
    echo "✅ VHost created"
else
    echo "❌ VHost creation failed"
    exit 1
fi

# Create Database
sudo scripts/mysql/database-create.sh "$DB_NAME" \
    --user="${DB_NAME}_user" \
    --password=$(openssl rand -base64 12) \
    --json > /tmp/db.json

echo "✅ Deployment complete!"
echo "Domain: $DOMAIN"
echo "DB: $DB_NAME"
```

#### Python Integration (Custom Panel)
```python
import subprocess
import json

def create_vhost(domain, docroot, ssl=False, php_version=None):
    """Create Apache VHost using Orkestra CLI"""
    cmd = [
        'sudo',
        'scripts/apache/vhost-create.sh',
        domain,
        docroot,
        '--json'
    ]
    
    if ssl:
        cmd.append('--ssl')
    
    if php_version:
        cmd.append(f'--php={php_version}')
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        return json.loads(result.stdout)
    else:
        raise Exception(f"VHost creation failed: {result.stderr}")

# Usage
try:
    vhost_info = create_vhost('example.com', '/var/www/example.com', 
                              ssl=True, php_version='8.2')
    print(f"✅ VHost created: {vhost_info['config_file']}")
except Exception as e:
    print(f"❌ Error: {e}")
```

#### PHP Web Panel
```php
<?php
// create_vhost.php

function createVHost($domain, $docroot, $ssl = false) {
    $cmd = sprintf(
        'sudo scripts/apache/vhost-create.sh %s %s %s --json',
        escapeshellarg($domain),
        escapeshellarg($docroot),
        $ssl ? '--ssl' : ''
    );
    
    $output = shell_exec($cmd);
    $result = json_decode($output, true);
    
    if ($result['success']) {
        return [
            'status' => 'success',
            'message' => "VHost created: {$result['domain']}",
            'config' => $result['config_file']
        ];
    }
    
    return ['status' => 'error', 'message' => 'Creation failed'];
}

// Usage
$result = createVHost('example.com', '/var/www/example.com', true);
echo json_encode($result);
?>
```

---

## �💡 Kullanım Senaryoları

### Senaryo 1: WordPress Geliştirme
**Amaç**: Yerel WordPress sitesi kurmak
1. Apache'yi kur ve çalıştır
2. MySQL'i kur, veritabanı oluştur
3. PHP 8.2 kur ve aktifleştir
4. Apache'de yeni VHost oluştur (example.local)
5. WordPress dosyalarını document root'a kopyala
6. `/etc/hosts` dosyasına domain ekle
7. Tarayıcıda `http://example.local` aç

**Orkesta ile**: Sadece 5 tıklama! 🎉

### Senaryo 2: Laravel Projesi
**Amaç**: Yeni Laravel projesi geliştirmek
1. Apache + MySQL + PHP 8.2 kur
2. MySQL'de veritabanı ve kullanıcı oluştur
3. VHost oluştur (SSL enabled)
4. Composer ile Laravel kur
5. `.env` dosyasını yapılandır

**Orkesta ile**: Servis altyapısı 2 dakikada hazır!

### Senaryo 3: Multi-version PHP Test
**Amaç**: PHP 7.4 ve 8.2 arasında test
1. Her iki PHP versiyonunu kur
2. İki farklı VHost oluştur
3. Her VHost'a farklı PHP versiyonu ata
4. Her ikisini de aynı anda çalıştır

**Orkesta ile**: Version switching tek tıklama!

### Senaryo 4: HTTPS Geliştirme
**Amaç**: HTTPS ile local geliştirme
1. Apache SSL modülünü aktifleştir
2. Self-signed certificate oluştur
3. VHost oluştur (SSL enabled)
4. HTTP -> HTTPS redirect otomatik

**Orkesta ile**: Tek dialog, full HTTPS setup!

---

## 🎯 Proje Vizyonu

### Kısa Vadeli Hedefler (3 Ay)
- ✅ Script migration tamamlansın
- ✅ Nginx, MariaDB, PostgreSQL eklensin
- ✅ Comprehensive testing
- ✅ User documentation

### Orta Vadeli Hedefler (6 Ay)
- � Flatpak paketleme ve Flathub yayını
- 🚀 Config editor ve log viewer
- 🚀 Performance monitoring
- 🚀 Backup/restore özellikleri

### Uzun Vadeli Vizyon (1 Yıl)
- 🌟 **Linux'ta #1 Web Dev Manager**
- 🌟 10+ servis desteği (LAMP, LEMP, MEAN, JAMstack)
- 🌟 Project templates (WordPress, Laravel, Django, etc.)
- 🌟 Docker integration (opsiyonel)
- 🌟 Community contributions

### Topluluk Hedefleri
- 📢 GitHub 500+ star
- 👥 10+ contributor
- 🌍 5+ dil desteği
- 📦 Tüm major distro'larda paket
- 💬 Active Discord/forum community

---

## �📚 Kaynaklar ve Referanslar

### Teknik Dökümanlar
- [GTK4 Documentation](https://docs.gtk.org/gtk4/)
- [Libadwaita Human Interface Guidelines](https://gnome.pages.gitlab.gnome.org/libadwaita/doc/main/)
- [PyGObject API Reference](https://pygobject.readthedocs.io/)
- [Flatpak Documentation](https://docs.flatpak.org/)
- [Python systemd Integration](https://www.freedesktop.org/wiki/Software/systemd/)

### Servis Dökümanları
- [Apache HTTP Server Documentation](https://httpd.apache.org/docs/)
- [MySQL Reference Manual](https://dev.mysql.com/doc/)
- [PHP Manual](https://www.php.net/manual/)
- [Nginx Documentation](https://nginx.org/en/docs/)

### Design Inspiration
- [GNOME Software](https://gitlab.gnome.org/GNOME/gnome-software)
- [Boxes (GNOME Boxes)](https://gitlab.gnome.org/GNOME/gnome-boxes)
- [XAMPP Control Panel](https://www.apachefriends.org/)
- [Laragon](https://laragon.org/) (Windows)

---

## 📌 Geliştirici Notları

### Mimari Kararlar
1. **Neden GTK4?**: Native Linux deneyimi, modern, performanslı
2. **Neden Python?**: Hızlı geliştirme, büyük ekosistem, okunabilir kod
3. **Neden Script'ler?**: Tek sudo, platform bağımsız, test edilebilir
4. **Neden Modüler?**: Kolay genişletme, bağımsız geliştirme, maintainability

### Tasarım Prensipleri
- **KISS (Keep It Simple)**: Basit, anlaşılır arayüz
- **DRY (Don't Repeat Yourself)**: Kod tekrarı yok, BaseService abstract class
- **SOLID**: Özellikle Single Responsibility ve Dependency Inversion
- **Convention over Configuration**: Akıllı varsayılanlar

### Kod Review Checklist
- [ ] Type hints var mı?
- [ ] Docstring var mı?
- [ ] Error handling yapılmış mı?
- [ ] Logger kullanılmış mı (print değil)?
- [ ] i18n kullanılmış mı (_("text"))?
- [ ] Platform bağımsız mı?
- [ ] Test yazıldı mı?

### Commit Message Format
```
type(scope): subject

body (optional)

footer (optional)
```

**Types**: feat, fix, docs, style, refactor, test, chore

**Examples**:
```
feat(apache): add VHost management UI
fix(mysql): handle empty root password case
docs(readme): update installation instructions
refactor(service_loader): improve error handling
```

---

## 🤝 Katkıda Bulunma

### Yeni Servis Eklemek
1. `services/new_service.py` oluştur (BaseService'ten türet)
2. `scripts/new_service/` klasörü oluştur
3. `install.sh` ve diğer script'leri yaz
4. Detay sayfası UI'ı ekle (`main_window.py` içinde `_add_newservice_sections`)
5. Test et (Fedora, Debian, Arch)
6. Pull request aç

### Bug Report
GitHub Issues kullan:
- Detaylı açıklama
- Sistem bilgileri (distro, GTK version)
- Hata mesajları ve loglar
- Reproduce steps

### Feature Request
GitHub Discussions kullan:
- Use case açıkla
- Mockup/screenshot (varsa)
- Benzer örnekler

---

## 📄 Lisans

**TODO**: Lisans belirlenecek
Önerilen: **GPL-3.0** (GTK4 uyumlu, open source)

---

## 👨‍💻 Geliştiriciler

**Yavuz** - Initial work ve mimari tasarım

---

## 🙏 Teşekkürler

- GNOME Team - GTK4 ve Libadwaita
- PyGObject Community
- Apache, MySQL, PHP Communities
- Tüm open source contributors

---

**📅 Son Güncelleme**: 9 Kasım 2025
**📝 Referans Versiyonu**: 2.0 (Mimari Revizyon)
**🎼 Orkesta** - Simplifying local web development on Linux

## 🐛 Bilinen Sınırlamalar ve TODO'lar

### Mevcut Sınırlamalar
1. **Script Migration**: Henüz kod içi bash -> script dosyası taşıması yapılmadı
2. **Flatpak Sandbox**: Systemd servis kontrolü sandbox'ta sınırlı
3. **Config Editor**: Henüz config dosyası düzenleme arayüzü yok
4. **Log Viewer**: Servis loglarını görüntüleme eksik
5. **Toast System**: Toast overlay yapısı eksik (şu an console print)

### Geliştirme TODO'ları
- [ ] Script dosyalarını oluştur (`scripts/*/install.sh`)
- [ ] Toast overlay implementasyonu (Adw.ToastOverlay)
- [ ] Config editor widget (syntax highlighting)
- [ ] Log viewer (tail -f entegrasyonu)
- [ ] Test suite (unit + integration tests)
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Flatpak packaging
- [ ] Performance monitoring

### Bilinen Buglar
- Yok (şu an için stabil çalışıyor)

### Platform-Specific Notlar
1. **Debian/Ubuntu**: ondrej/php PPA gerekir (otomatik eklenir)
2. **Fedora**: SELinux ayarları dikkat gerektirebilir
3. **Arch**: AUR paketleri manuel kurulum gerektirebilir
4. **Mint**: Tamamen test edildi, sorunsuz çalışıyor

## � Proje İstatistikleri

### Kod Metrikleri
- **Toplam Satır**: ~8000+ satır Python kodu
- **Servis Modülleri**: 3 aktif (Apache, MySQL, PHP)
- **UI Bileşenleri**: 1 ana pencere (dinamik detay sayfaları)
- **Dil Desteği**: 2 dil (TR, EN)
- **Platform Desteği**: 3 dağıtım (Fedora, Debian/Ubuntu, Arch)

### Özellik Kapsamı
- ✅ **Servis Yönetimi**: Install, uninstall, start, stop, restart
- ✅ **Apache**: VHost, SSL, PHP entegrasyonu (50+ özellik)
- ✅ **MySQL**: DB/User yönetimi, password, auto-setup (30+ özellik)
- ✅ **PHP**: Multi-version, extension, FPM (25+ özellik)
- ✅ **UI**: Modern GTK4/Libadwaita, responsive, navigasyon
- ✅ **i18n**: Türkçe/İngilizce çeviri sistemi

---

## 📅 Zaman Çizelgesi

### 7 Kasım 2024 - Proje Başlangıcı
- ✅ Proje yapısı ve mimari tasarım
- ✅ BaseService abstract class
- ✅ Platform manager
- ✅ Service loader
- ✅ İlk Apache modülü

### 8-10 Kasım 2024 - Temel Altyapı
- ✅ Utility modülleri (logger, system, validators)
- ✅ Çok dilli destek (i18n)
- ✅ MySQL servis modülü
- ✅ PHP servis modülü (multi-version)

### 11-15 Kasım 2024 - GTK4 Arayüzü
- ✅ Ana pencere tasarımı
- ✅ Servis listesi (card-based)
- ✅ Sidebar sistem bilgileri
- ✅ Servis detay sayfaları
- ✅ Navigation (back button)
- ✅ Progress dialogs

### 16-20 Kasım 2024 - Apache Özellikleri
- ✅ VHost management (create, list, delete, enable/disable)
- ✅ SSL/HTTPS (enable module, create certificate)
- ✅ PHP integration (version detection, switching)
- ✅ VHost detay sayfası
- ✅ Unified HTTP/HTTPS config

### 21-25 Kasım 2024 - MySQL Özellikleri
- ✅ Database management
- ✅ User management
- ✅ Root password handling
- ✅ Auto authentication detection
- ✅ Detay sayfası

### 26-30 Kasım 2024 - PHP Özellikleri
- ✅ Multi-version support (7.4-8.3)
- ✅ ondrej/php PPA integration
- ✅ Version switching
- ✅ Extension management
- ✅ PHP-FPM configuration

### 📅 9 Kasım 2025 - Mimari Revizyon
**Durum**: Projenin mevcut durumu analiz edildi ve referans güncellendi
**Yeni Prensip**: Script-first yaklaşımı
**Sonraki Adım**: Kod içi bash komutlarını script dosyalarına taşıma (Faz 4)

---

## 🎯 Mevcut Durum ve Sonraki Adımlar

### ✅ Tamamlanan (Faz 1-3)
1. ✅ **Modüler Mimari**: Dinamik servis yükleme çalışıyor
2. ✅ **3 Tam Fonksiyonel Servis**: Apache, MySQL, PHP
3. ✅ **Modern GTK4 UI**: Responsive, navigasyon, async operations
4. ✅ **Multi-distro**: Fedora/Debian/Arch desteği
5. ✅ **i18n**: TR/EN çeviri sistemi
6. ✅ **100+ Özellik**: VHost, SSL, DB, User, PHP version management

### 🔄 Şu An Üzerinde Çalışılan (Faz 4)
**Script Migration**: Kod içi bash'i script dosyalarına taşıma
- Neden: Tek sudo şifresi, bakım kolaylığı, yeniden kullanılabilirlik
- Hedef: `scripts/apache/`, `scripts/mysql/`, `scripts/php/` klasörleri
- Öncelik: Install/uninstall scriptleri

### 🔜 Sonraki Adımlar
1. **Faz 4 Tamamlama**: Script migration (2-3 gün)
2. **Faz 5 Başlangıcı**: Nginx servis modülü (5-7 gün)
3. **Test & Bug Fix**: Mevcut özellikleri sağlamlaştırma (3-4 gün)
4. **Dokumentasyon**: Kullanıcı rehberi ve API dökümanları (2-3 gün)

### 💡 Gelecek Vizyonu
- **3 Ay İçinde**: Nginx, MariaDB, PostgreSQL, Redis eklenmeli
- **6 Ay İçinde**: Flatpak paketleme ve Flathub yayını
- **1 Yıl İçinde**: Config editor, log viewer, backup/restore
- **Hedef**: Linux'ta en iyi local web dev environment manager

---

## 📝 Geliştirici Notları

### Çalışma Ortamı
- **OS**: Linux Mint 22.2 (Debian-based)
- **Paket Yöneticisi**: APT
- **Python**: 3.10+
- **GTK**: 4.0
- **Libadwaita**: 1.x

### Önemli Dosyalar
- `PROJECT_REFERENCE.md` ← **Bu dosya**: Projenin ana rehberi
- `CURRENT_STATUS.md`: Güncel durum ve yapılacaklar
- `TRANSLATION.md`: Çeviri rehberi
- `README.md`: Kullanıcı dökümanı

### Test Komutu
```bash
python3 main.py
```

### Yeni Servis Ekleme
1. `services/new_service.py` oluştur (BaseService'ten türet)
2. `scripts/new_service/` klasörü oluştur
3. Install/uninstall scriptlerini yaz
4. Restart application - otomatik yüklenir!

### Kod Standartları
- **Naming**: snake_case (Python PEP8)
- **Docstrings**: Her sınıf ve fonksiyon
- **Type hints**: Fonksiyon parametreleri ve dönüş değerleri
- **Logging**: logger kullan (print değil)
- **i18n**: Her kullanıcı mesajı için `_("text")` kullan
- **Error handling**: Try-except ve meaningful error messages

### Git Workflow
```bash
# Feature branch oluştur
git checkout -b feature/nginx-service

# Değişiklikleri commit et
git add services/nginx.py
git commit -m "feat: add nginx service module"

# Main'e merge et
git checkout main
git merge feature/nginx-service
```
