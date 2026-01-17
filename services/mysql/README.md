# MySQL Service Package

**Tamamen bağımsız, kendi kendine yeten servis paketi.**

## İçerik

```
mysql/
├── __init__.py          # Service class (MySQLService)
├── mysql.sh             # Bash script (tüm sistem işlemleri)
├── ui.py                # GTK UI (BaseView'dan türer)
├── metadata.json        # Servis metadata
├── icon.svg             # Servis ikonu
├── i18n.py              # Bağımsız çeviri sistemi
└── locale/              # Çeviri dosyaları
    ├── tr/LC_MESSAGES/
    └── en/LC_MESSAGES/
```

## Özellikler

- ✅ Veritabanı yönetimi
- ✅ Kullanıcı yönetimi
- ✅ Root şifre yönetimi
- ✅ Bağımsız çeviri sistemi
- ✅ Otomatik servis keşfi

## Bağımsızlık

Bu paket hiçbir ana utils/ veya ui/ bileşenine bağımlı değildir.
