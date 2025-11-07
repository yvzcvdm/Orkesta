# Translation Guide / Çeviri Rehberi

Orkesta uses GNU gettext for internationalization. The default language is English, with support for multiple languages.

Orkesta uluslararasılaştırma için GNU gettext kullanır. Varsayılan dil İngilizce'dir ve birçok dili destekler.

## Supported Languages / Desteklenen Diller

- 🇬🇧 English (default)
- 🇹🇷 Türkçe
- 🇩🇪 Deutsch
- 🇫🇷 Français
- 🇪🇸 Español

## For Developers / Geliştiriciler İçin

### Adding translatable strings / Çevrilebilir metinler ekleme

Wrap text in the `_()` function:

```python
from src.utils.i18n import _

label = Gtk.Label(label=_("Hello World"))
message = _("Service installed successfully")
```

### Extracting and compiling translations / Çevirileri çıkarma ve derleme

```bash
# Extract all translatable strings
# Tüm çevrilebilir metinleri çıkar
python extract_translations.py

# This will:
# Bu script:
# 1. Create/update locale/orkesta.pot (template file)
# 2. Create/update PO files for each language
# 3. Compile PO files to MO format
```

### Directory structure / Dizin yapısı

```
locale/
  ├── orkesta.pot          # Translation template
  ├── tr/
  │   └── LC_MESSAGES/
  │       ├── orkesta.po   # Turkish translations
  │       └── orkesta.mo   # Compiled Turkish
  ├── de/
  │   └── LC_MESSAGES/
  │       ├── orkesta.po   # German translations
  │       └── orkesta.mo   # Compiled German
  └── ...
```

## For Translators / Çevirmenler İçin

### How to translate / Nasıl çeviri yapılır

1. **Get the PO file / PO dosyasını al**
   - Download `locale/<lang>/LC_MESSAGES/orkesta.po`
   - Example: `locale/tr/LC_MESSAGES/orkesta.po`

2. **Edit with a PO editor / PO editörü ile düzenle**
   - Use Poedit, Lokalize, or any text editor
   - Poedit, Lokalize veya herhangi bir metin editörü kullan

3. **Translate strings / Metinleri çevir**
   ```po
   #: src/ui/main_window.py:89
   msgid "SYSTEM INFORMATION"
   msgstr "SİSTEM BİLGİLERİ"
   
   #: src/ui/main_window.py:98
   msgid "💻 Operating System"
   msgstr "💻 İşletim Sistemi"
   ```

4. **Compile and test / Derle ve test et**
   ```bash
   python extract_translations.py
   python main.py
   ```

### Testing translations / Çevirileri test etme

Set the language environment variable:
```bash
# Turkish / Türkçe
LANG=tr_TR.UTF-8 python main.py

# German / Almanca
LANG=de_DE.UTF-8 python main.py

# French / Fransızca
LANG=fr_FR.UTF-8 python main.py
```

## Language Detection / Dil Algılama

Orkesta automatically detects the system language and uses it. You can also force a specific language:

Orkesta sistem dilini otomatik algılar. Belirli bir dil de zorlayabilirsiniz:

```python
from src.utils.i18n import setup_i18n

# Force Turkish / Türkçe zorla
_ = setup_i18n('tr')

# Force German / Almanca zorla
_ = setup_i18n('de')

# Use system default / Sistem varsayılanı
_ = setup_i18n()
```

## Requirements / Gereksinimler

Translation tools must be installed:
Çeviri araçları kurulu olmalı:

```bash
# Debian/Ubuntu
sudo apt install gettext

# Fedora
sudo dnf install gettext

# Arch Linux
sudo pacman -S gettext
```

## Contributing Translations / Çeviri Katkısı

1. Fork the repository
2. Add/update your language PO file
3. Test the translation
4. Submit a pull request

Contributions are welcome! / Katkılar bekliyoruz!

## Translation Best Practices / En İyi Uygulamalar

- Keep the same formatting (emoji, punctuation)
- Maintain placeholder positions: `{service_name}`
- Test translations in the UI
- Check text length fits in buttons/labels
- Be consistent with terminology

---

For questions: [GitHub Issues](https://github.com/yourusername/orkestra/issues)
