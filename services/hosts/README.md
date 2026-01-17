# Hosts File Manager Service Package

**Tamamen bağımsız, kendi kendine yeten servis paketi.**

## İçerik

```
hosts/
├── __init__.py          # Service class (SystemHostsService)
├── hosts.sh             # Bash script (tüm sistem işlemleri)
├── ui.py                # GTK UI (BaseView'dan türer)
├── metadata.json        # Servis metadata
├── icon.svg             # Servis ikonu
├── i18n.py              # Bağımsız çeviri sistemi
└── locale/              # Çeviri dosyaları
    ├── tr/LC_MESSAGES/
    └── en/LC_MESSAGES/
```

## Özellikler

- ✅ /etc/hosts dosya yönetimi
- ✅ Host ekleme/silme
- ✅ Yedekleme/geri yükleme
- ✅ Bağımsız çeviri sistemi
- ✅ Otomatik servis keşfi

## Bağımsızlık

Bu paket hiçbir ana utils/ veya ui/ bileşenine bağımlı değildir.
