# Nginx Service Package

**Tamamen bağımsız, kendi kendine yeten servis paketi.**

## İçerik

```
nginx/
├── __init__.py          # Service class (NginxService)
├── nginx.sh             # Bash script (tüm sistem işlemleri)
├── metadata.json        # Servis metadata
├── icon.svg             # Servis ikonu
├── i18n.py              # Bağımsız çeviri sistemi
└── locale/              # Çeviri dosyaları
    ├── tr/LC_MESSAGES/
    └── en/LC_MESSAGES/
```

## Özellikler

- ✅ Nginx web sunucusu yönetimi
- ✅ Bağımsız çeviri sistemi
- ✅ Otomatik servis keşfi
- ✅ Tamamen modüler

## Bağımsızlık

Bu paket hiçbir ana utils/ veya ui/ bileşenine bağımlı değildir.
