# PHP Module Management - Apache

## 📋 Genel Bakış

Apache servisi için PHP modül yönetimi **hibrit yaklaşım** ile yapılmaktadır:

1. **Otomatik Kurulum**: Apache kurulumu sırasında sistem PHP tespiti yapılır ve varsa Apache modülü otomatik yüklenir
2. **Manuel Yönetim**: UI üzerinden PHP modülleri eklenip çıkarılabilir, versiyon değiştirilebilir

## 🎯 Tasarım Kararları

### Neden Hibrit Yaklaşım?

**Otomatik Kurulum Avantajları:**
- ✅ Kullanıcı müdahalesi gerektirmez
- ✅ "Tek tıkla çalışır" deneyimi
- ✅ Yeni kullanıcılar için kolay

**Manuel Yönetim Avantajları:**
- ✅ Kullanıcıya tam kontrol
- ✅ PHP-FPM vs Apache Module seçimi
- ✅ Modüler ve temiz mimari
- ✅ İleri düzey kullanıcılar için esneklik

### PHP Ayrı Servis mi, Apache İçinde mi?

**Karar: PHP Ayrı Servis + Apache Modül Yönetimi**

PHP ve Apache ayrı servisler olarak kalmalı çünkü:
- PHP-FPM farklı web sunucularıyla çalışabilir (Nginx, LiteSpeed)
- Kullanıcı PHP-FPM veya Apache Module seçebilmeli
- Modüler mimari bakımı kolaylaştırır

## 🛠️ Apache Script'inde Otomatik PHP Yükleme

### Kurulum Sırasında

```bash
action_install() {
    # ... Apache kurulumu ...
    
    # Auto-detect and install PHP module if PHP is available
    if [ "$OS_TYPE" = "debian" ]; then
        echo "Checking for installed PHP versions..."
        local php_found=false
        
        # Check for common PHP versions
        for version in 8.4 8.3 8.2 8.1 8.0 7.4 7.3 7.2; do
            if command -v "php$version" >/dev/null 2>&1 || [ -d "/etc/php/$version" ]; then
                echo "Found PHP $version - Installing Apache module..."
                if apt-get install -y "libapache2-mod-php$version" 2>&1; then
                    echo "PHP $version Apache module installed successfully"
                    systemctl restart "$service_name" 2>&1
                    php_found=true
                    break
                fi
            fi
        done
        
        if [ "$php_found" = false ]; then
            echo "No PHP installation detected. You can install PHP modules later."
        fi
    fi
}
```

### Davranış

1. Apache kurulumu tamamlanır
2. Sistemde yüklü PHP versiyonları taranır (8.4'ten 7.2'ye kadar)
3. İlk bulunan PHP için Apache modülü otomatik yüklenir
4. Apache yeniden başlatılır
5. PHP bulunamazsa uyarı verilir, kurulum devam eder

## 📡 Python API - Apache Service

### Yeni Metodlar

```python
class ApacheService(BaseService):
    
    # PHP Module Listing
    def get_installed_php_modules(self) -> List[Dict[str, Any]]:
        """
        Get list of installed PHP Apache modules with their status
        
        Returns:
            [
                {"version": "7.4", "enabled": false},
                {"version": "8.2", "enabled": true}
            ]
        """
    
    # Active Module
    def get_active_php_module(self) -> Optional[str]:
        """
        Get currently active PHP Apache module version
        
        Returns:
            "8.2" or None if no module is active
        """
    
    # Module Installation
    def install_php_module(self, version: Optional[str] = None) -> Tuple[bool, str]:
        """
        Install PHP module for Apache
        
        Args:
            version: PHP version (e.g., "8.2"). If None, auto-detect.
        
        Returns:
            (success: bool, message: str)
        """
    
    # Module Removal
    def uninstall_php_module(self, version: Optional[str] = None) -> Tuple[bool, str]:
        """
        Uninstall PHP module from Apache
        
        Args:
            version: PHP version (e.g., "8.2"). If None, remove all.
        
        Returns:
            (success: bool, message: str)
        """
    
    # Module Switching
    def switch_php_module(self, version: str) -> Tuple[bool, str]:
        """
        Switch active PHP Apache module to specified version
        
        Args:
            version: Target PHP version (e.g., "8.2")
        
        Returns:
            (success: bool, message: str)
        """
    
    # Check Installation
    def is_php_module_installed(self) -> bool:
        """
        Check if PHP module is installed for Apache
        
        Returns:
            True if any PHP module is installed
        """
```

## 🔧 Bash Script Komutları

### PHP Apache Module Management

```bash
# List installed PHP Apache modules
sudo ./scripts/apache.sh php-module-list [--json]

# Get active PHP Apache module
sudo ./scripts/apache.sh php-module-get-active

# Switch PHP Apache module
sudo ./scripts/apache.sh php-module-switch 8.2

# Install PHP Apache module
sudo ./scripts/apache.sh php-module-install [version]

# Uninstall PHP Apache module
sudo ./scripts/apache.sh php-module-uninstall [version]

# Check if any PHP module is installed
sudo ./scripts/apache.sh php-module-installed
```

### Örnekler

```bash
# Yüklü modülleri listele
$ sudo ./apache.sh php-module-list
PHP 7.4 [DISABLED]
PHP 8.2 [ENABLED]

# JSON formatında
$ sudo ./apache.sh php-module-list --json
[{"version":"7.4","enabled":false},{"version":"8.2","enabled":true}]

# Aktif modülü göster
$ sudo ./apache.sh php-module-get-active
8.2

# PHP 7.4'e geç
$ sudo ./apache.sh php-module-switch 7.4
Module php8.2 disabled.
Enabling module php7.4.
Switched to PHP 7.4 Apache module

# PHP 8.3 modülü yükle
$ sudo ./apache.sh php-module-install 8.3
Installing PHP 8.3 Apache module...
PHP 8.3 Apache module installed successfully
```

## 🎨 UI Entegrasyonu

### Apache Detay Sayfasında PHP Modül Yönetimi

UI'da Apache detay sayfasında bir "PHP Modules" bölümü olmalı:

```
┌─────────────────────────────────────────────┐
│ Apache HTTP Server - Details               │
├─────────────────────────────────────────────┤
│ Status: Running ✅                          │
│ Port: 80, 443                              │
│ Version: Apache/2.4.58                     │
├─────────────────────────────────────────────┤
│ PHP Modules                                │
├─────────────────────────────────────────────┤
│ ○ PHP 7.4    [Switch] [Remove]            │
│ ● PHP 8.2    [Active] [Remove]            │
│                                            │
│ [+ Install New PHP Module]                 │
└─────────────────────────────────────────────┘
```

### Özellikler

1. **List View**: Yüklü PHP modüllerini göster (aktif olanı vurgula)
2. **Switch Button**: Farklı PHP versiyonuna geç
3. **Remove Button**: Modülü kaldır
4. **Install Button**: Yeni PHP modülü yükle
5. **Auto-detect**: Kullanıcı hangi PHP versiyonlarının mevcut olduğunu görebilmeli

## 🔄 Kullanım Senaryoları

### Senaryo 1: İlk Kurulum

```
User: Apache'yi yükle
System: ✅ Apache yüklendi
        ⏳ PHP kontrol ediliyor...
        ✅ PHP 8.2 bulundu
        ✅ Apache PHP modülü yüklendi
        ✅ Apache yeniden başlatıldı
```

### Senaryo 2: Manuel Modül Yükleme

```
User: UI'dan "Install PHP 7.4 Module"
System: ✅ libapache2-mod-php7.4 yüklendi
        ✅ Apache yeniden başlatıldı
        ℹ️ PHP 8.2 hala aktif (switch yapabilirsiniz)
```

### Senaryo 3: Versiyon Değiştirme

```
User: UI'dan "Switch to PHP 7.4"
System: ⏳ PHP 8.2 devre dışı bırakılıyor...
        ⏳ PHP 7.4 aktif ediliyor...
        ✅ Apache yeniden başlatıldı
        ✅ Şimdi PHP 7.4 aktif
```

### Senaryo 4: Modül Kaldırma

```
User: UI'dan "Remove PHP 7.4"
System: ⚠️ PHP 7.4 şu anda aktif, önce başka versiyona geçin
User: "Switch to PHP 8.2" sonra "Remove PHP 7.4"
System: ✅ PHP 8.2 aktif edildi
        ✅ libapache2-mod-php7.4 kaldırıldı
```

## ⚠️ Önemli Notlar

### PHP CLI vs Apache Module

- **PHP CLI**: `php -v` komutuyla görülen versiyon (Terminal/script için)
- **Apache Module**: Web sunucusunda çalışan versiyon (Web için)
- **Bu iki versiyon farklı olabilir!**

### Örnek

```bash
# CLI PHP
$ php -v
PHP 7.4.33

# Apache PHP (Web)
$ curl http://localhost/info.php | grep "PHP Version"
PHP Version 8.2.29
```

### PHP-FPM vs Apache Module

- **PHP-FPM**: Ayrı bir servis, proxy üzerinden çalışır (önerilen)
- **Apache Module**: Apache içine entegre, daha basit
- **İkisi birlikte çalışabilir** (vhost bazında farklı olabilir)

## 🧪 Test Komutları

```python
from services.apache import ApacheService
from src.platform_manager import PlatformManager

pm = PlatformManager()
apache = ApacheService(pm)

# Yüklü modüller
modules = apache.get_installed_php_modules()
print(modules)  # [{"version": "7.4", "enabled": false}, ...]

# Aktif modül
active = apache.get_active_php_module()
print(active)  # "8.2"

# Modül değiştir
success, msg = apache.switch_php_module('7.4')
print(msg)

# Modül yükle
success, msg = apache.install_php_module('8.3')
print(msg)

# Modül kaldır
success, msg = apache.uninstall_php_module('7.4')
print(msg)
```

## 🎯 Sonuç

Bu hibrit yaklaşım:
- ✅ Yeni kullanıcılar için kolay (otomatik)
- ✅ İleri düzey kullanıcılar için esnek (manuel)
- ✅ PHP servisinden bağımsız
- ✅ Modüler ve bakımı kolay
- ✅ PHP-FPM'e geçişe açık

Apache içinde PHP modül yönetimi, kullanıcıya web sunucusu ve PHP entegrasyonu konusunda tam kontrol sağlar.
