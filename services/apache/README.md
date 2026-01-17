# Apache Service Package

**Tamamen bağımsız, kendi kendine yeten servis paketi.**

## İçerik

```
apache/
├── __init__.py          # Service class (ApacheService)
├── apache.sh            # Bash script (tüm sistem işlemleri)
├── ui.py                # GTK UI (BaseView'dan türer)
├── metadata.json        # Servis metadata
├── icon.svg             # Servis ikonu
├── i18n.py              # Bağımsız çeviri sistemi
└── locale/              # Çeviri dosyaları
    ├── tr/
    │   └── LC_MESSAGES/
    │       ├── apache.po
    │       └── apache.mo
    └── en/
        └── LC_MESSAGES/
            ├── apache.po
            └── apache.mo
```

## Özellikler

- ✅ **Tamamen bağımsız**: Ana utils/ veya ui/ klasörlerine bağımlı değil
- ✅ **Kendi i18n sistemi**: Kendi çevirilerini yönetir
- ✅ **Kendi ikonu**: icon.svg kendi klasöründe
- ✅ **Script-first**: Tüm sistem işlemleri apache.sh'de
- ✅ **Zero-config**: metadata.json ile otomatik yüklenir

## Kullanım

Servis otomatik olarak `ServiceLoader` tarafından yüklenir. Manuel import:

```python
from services.apache import ApacheService
```

## Çeviri Güncelleme

```bash
# .po düzenle
nano locale/tr/LC_MESSAGES/apache.po

# .mo derle
msgfmt locale/tr/LC_MESSAGES/apache.po -o locale/tr/LC_MESSAGES/apache.mo
```
