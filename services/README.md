# Orkesta Services - Modüler Plugin Yapısı

## 🎯 Mimari Prensibi

Orkesta, **WordPress plugin sistemi** gibi çalışan tam modüler bir yapıya sahiptir. Her servis kendi klasöründe bağımsız bir modül olarak yaşar ve sonradan eklenip/çıkarılabilir.

## 📦 Servis Yapısı

Her servis şu dosyalardan oluşur:

```
services/
  service_name/
    __init__.py       # Service sınıfı (ServiceClass)
    service.sh        # Bash script (sistem operasyonları)
    ui.py            # GTK UI view (opsiyonel)
    metadata.json    # Servis bilgileri
```

### Örnek: Apache Servisi

```
services/apache/
  ├── __init__.py       # ApacheService class
  ├── apache.sh         # Apache yönetim scripti
  ├── ui.py            # ApacheView (özel UI)
  ├── metadata.json    # Servis metadata
```

## 🔌 Plugin Olarak Kullanım

### Yeni Servis Ekleme

1. **Klasör oluştur**: `services/myservice/`
2. **Metadata ekle**: `metadata.json`
```json
{
  "name": "myservice",
  "display_name": "My Service",
  "version": "1.0.0",
  "author": "Your Name",
  "description": "Service description",
  "icon": "icon-name-symbolic",
  "category": "web_server|database|cache|other",
  "requires": [],
  "enabled": true
}
```

3. **Service sınıfı**: `__init__.py`
```python
from services.base_service import BaseService, ServiceType
from typing import Tuple

class MyService(BaseService):
    SCRIPT_NAME = 'myservice.sh'
    
    @property
    def name(self) -> str:
        return "myservice"
    
    # BaseService metodlarını implement et
    def is_installed(self) -> bool:
        success, _ = self._execute_script(self.SCRIPT_NAME, 'is-installed')
        return success
    
    # ... diğer metodlar
```

4. **Bash script**: `myservice.sh`
```bash
#!/bin/bash
# Sistem operasyonları
case "$1" in
    is-installed)
        # Check installation
        ;;
    install)
        # Installation logic
        ;;
esac
```

5. **UI (opsiyonel)**: `ui.py`
```python
from src.ui.services.base_view import BaseServiceView

class MyServiceView(BaseServiceView):
    def _add_custom_sections(self):
        # Özel UI bölümleri ekle
        pass
```

### Servis Kaldırma

Servisi devre dışı bırakmak için:
- **Geçici**: `metadata.json`'da `"enabled": false`
- **Kalıcı**: Klasörü sil

## 🔄 Otomatik Yükleme

`ServiceLoader` otomatik olarak:
1. `services/` klasöründeki tüm alt klasörleri tarar
2. `__init__.py` olan klasörleri servis olarak algılar
3. BaseService'ten türeyen sınıfları yükler
4. UI varsa entegre eder

**Kod değişikliği gerekmez** - sadece dosyaları ekle/çıkar!

## 📋 Mevcut Servisler

| Servis | Klasör | Script | UI |
|--------|--------|--------|-----|
| Apache | `apache/` | `apache.sh` | ❌ |
| MySQL | `mysql/` | `mysql.sh` | ❌ |
| PHP | `php/` | `php.sh` | ❌ |
| Hosts | `system_hosts/` | `hosts.sh` | ✅ |

## 🎨 UI Customization

Her servis kendi UI'ını sağlayabilir:

```python
# services/myservice/__init__.py

def get_detail_view(self, main_window):
    from services.myservice.ui import MyServiceView
    view = MyServiceView(self, main_window)
    return view.create_view()
```

Eğer `get_detail_view()` `None` dönerse, default `BaseServiceView` kullanılır.

## 🚀 Marketplace Hazırlık

Bu yapı sayesinde:
- ✅ Servisler `.zip` olarak paketlenebilir
- ✅ İndirilen servisler `services/` klasörüne çıkarılır
- ✅ Uygulama yeniden başlatılınca otomatik yüklenir
- ✅ Bağımlılıklar `metadata.json`'da tanımlıdır

## 📝 Best Practices

### 1. Script-First Yaklaşım
**Tüm sistem operasyonları bash scriptlerde!**
```python
# ✅ DOĞRU
def install(self):
    return self._execute_script('myservice.sh', 'install')

# ❌ YANLIŞ  
def install(self):
    subprocess.run(['apt', 'install', 'myservice'])
```

### 2. Bağımsızlık
- Servisler birbirlerini import etmemeli
- Ortak kodlar `base_service.py`'de
- Script self-contained olmalı

### 3. Metadata Doğruluğu
- Version semantic versioning (1.0.0)
- Bağımlılıkları belirt
- İkon GTK icon theme'den

## 🔧 Geliştirme

### Yeni Servis Test Etme

```bash
# 1. Servisi oluştur
mkdir -p services/myservice
cd services/myservice

# 2. Dosyaları ekle
touch __init__.py myservice.sh ui.py metadata.json

# 3. Uygulamayı çalıştır
python3 main.py

# Servis otomatik yüklenir!
```

### Debug

Loglar servislerin yüklendiğini gösterir:
```
INFO - Servisler yükleniyor: /path/to/services
INFO - Bulunan servis modülleri: ['apache', 'mysql', 'php', 'system_hosts']
INFO - Servis yüklendi: My Service (myservice)
```

## 📚 Örnekler

### Minimal Servis

En basit servis yapısı:
```python
# services/minimal/__init__.py
from services.base_service import BaseService, ServiceType
from typing import Tuple

class MinimalService(BaseService):
    SCRIPT_NAME = 'minimal.sh'
    
    @property
    def name(self) -> str:
        return "minimal"
    
    def is_installed(self) -> bool:
        return True
    
    def install(self) -> Tuple[bool, str]:
        return True, "Already available"
    
    # ... diğer required metodlar (stub olabilir)
```

### Özel UI ile Servis

SystemHosts örneğine bakın: [services/system_hosts/](system_hosts/)

---

**Not**: Bu yapı WordPress Plugin API'sinden esinlenmiştir ve maksimum modülerlik için tasarlanmıştır.
