# Orkesta - Architecture Summary

**Date**: 9 Kasım 2025  
**Version**: 2.0 (Revised Architecture)

Bu dosya, projenin mimari prensiplerini ve karar süreçlerini özetler.

---

## 🎯 Core Principles

### 1. **Script-First Approach - CLI as First-Class Citizens**
**Problem**: Kod içinde bash komutları bakımı zorlaştırıyor
**Solution**: Her servis için **bağımsız CLI komutları** (VestaCP, cPanel, aaPanel gibi)

**Prensip: Script = Standalone CLI Tool**
```bash
# ✅ DOĞRU: Script tek başına çalışır
/usr/local/bin/orkesta-vhost create example.com /var/www/example.com --ssl

# ✅ DOĞRU: Script parametrelerle yönetilir
scripts/apache/vhost-create.sh example.com /var/www/html --php=8.2 --ssl

# ❌ YANLIŞ: Script arayüze bağımlı değil
# Script içinde GTK/Python kodu olmamalı!
```

**Avantajlar**:
- ✅ **Tek sudo şifresi**: Tüm işlemler tek script'te
- ✅ **Platform bağımsız**: OS detection script içinde
- ✅ **CLI kullanımı**: Terminal'den doğrudan çalışabilir
- ✅ **Test edilebilir**: Script'ler bağımsız test edilir
- ✅ **Bakım kolay**: Bash mantığı ayrı dosyalarda
- ✅ **3rd-party entegrasyon**: Başka araçlar çağırabilir
- ✅ **Automation friendly**: CI/CD, cron jobs kullanabilir

**VestaCP/cPanel Benzeri Yaklaşım**:
```bash
# VestaCP stilinde
v-add-web-domain user example.com
v-add-database user database_name

# Orkesta stilinde
orkesta-apache vhost-create example.com
orkesta-mysql database-create mydb
```

### 2. **Minimal Main, Maksimum Modülerlik**
**Principle**: Main sadece GTK başlatır, servis mantığı yok

```python
# ✅ DOĞRU: main.py
from src.app import OrkestaApp
app = OrkestaApp()
app.run()

# ❌ YANLIŞ: main.py
if service.is_installed():
    service.start()  # Bu main'de olmamalı!
```

### 3. **Servis = Modül + Script**
Her servis iki parçadan oluşur:

```
services/apache.py       # Python modülü (UI logic)
scripts/apache/install.sh  # Shell script (system operations)
```

### 4. **Detay Sayfası = Servis Özel UI**
Her servisin kendine özgü detay sayfası var:
- Apache: VHost listesi, SSL yönetimi, PHP switch
- MySQL: Database listesi, User listesi, Password management
- PHP: Version listesi, Extension listesi

**Implementation**: `main_window.py` içinde `_create_service_detail_page()`

---

## 📦 Component Breakdown

### Layer 1: Core (Platform & Loading)
```
src/platform_manager.py    # OS detection, package manager
src/service_loader.py      # Dynamic service discovery
```

**Responsibility**: System information, service discovery
**No business logic**: Sadece bilgi toplar, işlem yapmaz

### Layer 2: Services (Business Logic)
```
services/base_service.py   # Abstract base class
services/apache.py         # Apache implementation
services/mysql.py          # MySQL implementation
services/php.py            # PHP implementation
```

**Responsibility**: Service-specific operations
**Independence**: Her servis tamamen bağımsız

### Layer 3: Scripts (Standalone CLI Tools)
```
scripts/apache/
├── install.sh              # Apache kurulum
├── vhost-create.sh         # VHost oluştur
├── vhost-delete.sh         # VHost sil
├── vhost-list.sh           # VHost listele
├── ssl-enable.sh           # SSL aktif et
└── ssl-create-cert.sh      # Self-signed cert

scripts/mysql/
├── install.sh              # MySQL kurulum
├── database-create.sh      # Database oluştur
├── database-delete.sh      # Database sil
├── database-list.sh        # Database listele
├── user-create.sh          # User oluştur
└── password-change.sh      # Root password değiştir

scripts/php/
├── install.sh              # PHP kurulum
├── version-switch.sh       # Version değiştir
├── version-list.sh         # Kurulu version'ları listele
├── extension-install.sh    # Extension kur
└── extension-list.sh       # Extension'ları listele
```

**Responsibility**: System-level operations (install, config)
**Platform-aware**: OS detection içinde
**Standalone**: Her script tek başına çalışabilir (VestaCP/cPanel gibi)

**Script Özellikleri**:
1. **Parametreli çalışma**: `./vhost-create.sh example.com /var/www/html`
2. **Exit codes**: 0=success, 1=error, 2=invalid params
3. **JSON output** (opsiyonel): `--json` flag ile structured output
4. **Help built-in**: `--help` parametresi
5. **Dry-run mode**: `--dry-run` ile test
6. **Verbose mode**: `--verbose` ile detaylı log

### Layer 4: UI (Presentation)
```
src/app.py                 # GTK Application
src/ui/main_window.py      # Main window + detail pages
```

**Responsibility**: User interface only
**No business logic**: Servisleri çağırır, kendisi işlem yapmaz

---

## 🔄 Data Flow

### Install Flow Example (GUI Mode)
```
[User clicks Install]
    ↓
[main_window.py - _on_service_install()]
    ↓
[service.install() in thread]
    ↓
[Execute: pkexec scripts/apache/install.sh]
    ↓
[Script runs completely independent]
    ↓
  Script içinde:
  - OS detection
  - Package installation
  - systemctl enable/start
  - Config file setup
  - Return exit code + output
    ↓
[Python reads exit code + output]
    ↓
[GLib.idle_add() - UI update]
    ↓
[Toast message + service list refresh]
```

### CLI Flow Example (Terminal Mode)
```bash
# Kullanıcı terminalden çalıştırır
$ sudo scripts/apache/vhost-create.sh example.com /var/www/example.com --ssl

# Script tek başına çalışır
  - Parametre validation
  - Config generation
  - File creation
  - Apache reload
  - Exit with status

# Output
✅ VHost 'example.com' created successfully
   Document root: /var/www/example.com
   SSL: Enabled
   Config: /etc/apache2/sites-available/example.com.conf

# veya
$ scripts/apache/vhost-create.sh --help
Usage: vhost-create.sh <domain> <document_root> [options]

Options:
  --ssl              Enable SSL/HTTPS
  --php=VERSION      Specify PHP version (e.g., 8.2)
  --port=PORT        Custom port (default: 80)
  --help             Show this help
  --json             Output as JSON
```

### VHost Creation Flow
```
[User fills VHost dialog]
    ↓
[main_window.py - _on_apache_create_vhost()]
    ↓
[apache.create_vhost(...)]
    ↓
[Generate config from template]
    ↓
[Write to temp file]
    ↓
[pkexec cp temp_file /etc/apache2/sites-available/]
    ↓
[a2ensite via pkexec]
    ↓
[systemctl reload apache2]
    ↓
[Toast message + refresh detail page]
```

---

## 🎨 UI Architecture

### Navigation Pattern
```
[Service List]  →  [Service Detail]  →  [VHost Detail]
     ↑                     ↓                   ↓
     └──── Back Button ────┴───────────────────┘
```

**Implementation**:
- `main_stack` with "list" and "detail" children
- Back button visibility toggled
- Detail page recreated on each navigation

### Dynamic Detail Pages
Detail pages are created dynamically per service:

```python
def _create_service_detail_page(self, service):
    # Base sections (all services)
    - Status
    - Actions (install/start/stop)
    
    # Service-specific sections
    if service.name == "apache":
        self._add_apache_sections()  # VHost, SSL, PHP
    elif service.name == "mysql":
        self._add_mysql_sections()   # DB, Users, Password
```

**Benefit**: Each service can have unlimited custom UI

---

## 🔐 Security Architecture

### pkexec Usage
All sudo operations use pkexec:
```bash
pkexec bash /path/to/script.sh
```

**Why pkexec?**
- ✅ GUI-friendly (PolicyKit dialog)
- ✅ System policy integration
- ✅ Session-based authentication
- ❌ Not: `sudo` (terminal only)
- ❌ Not: `gksu` (deprecated)

### Password Storage
MySQL root password:
```
~/.config/orkesta/mysql_config.json
permissions: 0600 (owner only)
```

**Security**:
- File permissions restricted
- Not in git (gitignore'd)
- Only for automated operations

---

## 🧩 Extension Points

### Adding New Service
```python
# 1. Create services/nginx.py
from services.base_service import BaseService

class NginxService(BaseService):
    @property
    def name(self) -> str:
        return "nginx"
    
    # ... implement abstract methods

# 2. Create scripts/nginx/install.sh
# 3. Restart app - auto-loaded!
```

### Adding Service-Specific UI
```python
# In main_window.py
def _add_nginx_sections(self, main_box, service):
    # Custom UI for Nginx
    nginx_group = Adw.PreferencesGroup()
    nginx_group.set_title("Nginx Configuration")
    # ... add custom widgets
    main_box.append(nginx_group)

# In _create_service_detail_page()
if service.name == "nginx":
    self._add_nginx_sections(main_box, service)
```

---

## 📊 Performance Considerations

### Async Operations
Heavy operations run in threads:
```python
def install_thread():
    success, message = service.install()
    GLib.idle_add(self._on_complete, success, message)

thread = threading.Thread(target=install_thread, daemon=True)
thread.start()
```

**Why threads?**
- UI remains responsive
- User can cancel
- Progress indication possible

### Lazy Loading
Services loaded only once:
```python
# ServiceLoader caches service instances
self.services = {}  # Loaded once, reused
```

### Status Caching
Service status checked on demand:
```python
def get_status(self):
    # No caching - always fresh
    # Alternative: Could cache with TTL
```

---

## 🎯 Script Design Principles (VestaCP/cPanel Style)

### CLI-First Mentality
**Her script = Bağımsız komut satırı aracı**

#### Örnek: VHost Oluşturma Script
```bash
#!/bin/bash
# scripts/apache/vhost-create.sh
# Standalone CLI tool for creating Apache virtual hosts

set -e  # Exit on error

# ============================================
# USAGE & HELP
# ============================================
show_help() {
    cat << EOF
Usage: $(basename "$0") <domain> <docroot> [options]

Creates an Apache virtual host configuration.

Arguments:
  domain          Domain name (e.g., example.com)
  docroot         Document root path (e.g., /var/www/example.com)

Options:
  --ssl           Enable SSL/HTTPS with self-signed certificate
  --php=VERSION   PHP version (e.g., 8.2)
  --port=PORT     HTTP port (default: 80)
  --email=EMAIL   Server admin email
  --json          Output result as JSON
  --dry-run       Show what would be done without executing
  --verbose       Verbose output
  --help          Show this help message

Examples:
  # Basic HTTP vhost
  $(basename "$0") example.com /var/www/example.com

  # HTTPS with PHP 8.2
  $(basename "$0") example.com /var/www/example.com --ssl --php=8.2

  # Custom port
  $(basename "$0") dev.local /var/www/dev --port=8080

Exit Codes:
  0 - Success
  1 - General error
  2 - Invalid parameters
  3 - Permission denied
  4 - Service not available

Author: Orkesta Team
Version: 1.0
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

# Parse arguments
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

# Validate required parameters
if [ -z "$DOMAIN" ] || [ -z "$DOCROOT" ]; then
    echo "Error: Domain and document root are required" >&2
    echo "Run with --help for usage information" >&2
    exit 2
fi

# ============================================
# OS DETECTION
# ============================================
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        echo "$ID"
    else
        echo "unknown"
    fi
}

OS_TYPE=$(detect_os)

# ============================================
# MAIN LOGIC
# ============================================
[ "$VERBOSE" = true ] && echo "Creating VHost for $DOMAIN..."

# OS-specific paths
case $OS_TYPE in
    ubuntu|debian)
        VHOST_DIR="/etc/apache2/sites-available"
        ENABLED_DIR="/etc/apache2/sites-enabled"
        SERVICE_NAME="apache2"
        ;;
    fedora)
        VHOST_DIR="/etc/httpd/conf.d"
        SERVICE_NAME="httpd"
        ;;
    *)
        echo "Error: Unsupported OS: $OS_TYPE" >&2
        exit 4
        ;;
esac

# Create document root
if [ "$DRY_RUN" = false ]; then
    mkdir -p "$DOCROOT"
    echo "<h1>Welcome to $DOMAIN</h1>" > "$DOCROOT/index.html"
fi

# Generate config
# ... (config generation logic)

# Output result
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
fi

exit 0
```

### Key Design Points

#### 1. **Self-Contained**
```bash
# ✅ Her şey script içinde
- Parametre parsing
- OS detection
- Error handling
- Output formatting

# ❌ Dışarıya bağımlı değil
- Python'a bağımlı değil
- GTK'ya bağımlı değil
- Config dosyasına bağımlı değil (her şey parametre)
```

#### 2. **Standard Input/Output**
```bash
# Exit codes
0 = Success
1 = General error
2 = Invalid parameters
3 = Permission denied
4 = Service not available

# Output formats
- Human-readable (default)
- JSON (--json flag)
- Quiet (--quiet flag)
```

#### 3. **Automation-Friendly**
```bash
# Cron job
0 2 * * * /usr/local/bin/orkesta-backup.sh

# Ansible playbook
- name: Create VHost
  command: /usr/local/bin/orkestra-apache vhost-create example.com /var/www

# CI/CD pipeline
script:
  - scripts/apache/install.sh
  - scripts/mysql/database-create.sh testdb
```

#### 4. **Control Panel Integration**
```bash
# Webmin/Virtualmin gibi paneller
system("orkestra-apache vhost-create domain.com /var/www");

# Custom web panel
exec("orkestra-mysql database-create mydb --json");
$result = json_decode($output);
```

### Script Standards

**Her script şunlara sahip olmalı:**
1. ✅ `--help` parametresi (detaylı kullanım)
2. ✅ Exit code standardı (0=success, >0=error)
3. ✅ Parameter validation
4. ✅ OS detection (multi-distro)
5. ✅ Error messages (stderr'a)
6. ✅ Success messages (stdout'a)
7. ✅ `--json` flag (opsiyonel, structured output)
8. ✅ `--dry-run` flag (opsiyonel, test mode)
9. ✅ `--verbose` flag (opsiyonel, debug)
10. ✅ Idempotent (birden fazla çalıştırılabilir)

---

## 🔮 Future Architecture

### Phase 4: Script Migration
Move all bash code to scripts:
```
Current:  service.install() has inline bash
Future:   service.install() calls install.sh
```

### Phase 5+: Plugin System
```python
# Third-party services as plugins
~/.local/share/orkesta/plugins/
    nginx/
        __init__.py
        service.py
```

### Phase 6: API Layer
```python
# REST API for external tools
/api/services
/api/services/apache/vhosts
/api/services/mysql/databases
```

---

## 📝 Design Decisions Log

### Why GTK4 over Qt?
- Native GNOME integration
- Modern Libadwaita widgets
- Better Linux ecosystem fit
- Smaller binary size

### Why Python over C++?
- Faster development
- Easier maintenance
- Great GTK bindings (PyGObject)
- Scripting capabilities

### Why BaseService abstract class?
- Enforces consistent API
- Type safety with type hints
- Easy to extend
- Self-documenting

### Why scripts over subprocess calls?
- Reduces Python complexity
- Platform-independent
- Single sudo password
- Reusable from CLI

---

## 🎓 Learning Resources

**For Contributors:**
1. Read PROJECT_REFERENCE.md (comprehensive guide)
2. Study BaseService implementation
3. Look at Apache service (best example)
4. Check main_window.py for UI patterns

**Key Patterns:**
- Service isolation (each service independent)
- Script execution (pkexec + bash)
- Dynamic UI (detail pages per service)
- Thread-safe UI updates (GLib.idle_add)

---

**Document Version**: 1.0  
**Last Updated**: 9 Kasım 2025  
**Maintainer**: Project Team
