"""
Çok dilli destek modülü
Linux sistemlerinde standart gettext kullanır
"""
import gettext
import locale
import os
from pathlib import Path

class I18n:
    """Uluslararasılaştırma yöneticisi"""
    
    def __init__(self):
        self.domain = 'orkesta'
        self.locale_dir = self._get_locale_dir()
        self.current_locale = None
        self._translator = None
        
    def _get_locale_dir(self):
        """Locale dizinini bul"""
        # Geliştirme ortamı
        dev_locale = Path(__file__).parent.parent.parent / 'locale'
        if dev_locale.exists():
            return str(dev_locale)
        
        # Sistem kurulumu
        system_locale = Path('/usr/share/locale')
        if system_locale.exists():
            return str(system_locale)
        
        # Flatpak kurulumu
        flatpak_locale = Path('/app/share/locale')
        if flatpak_locale.exists():
            return str(flatpak_locale)
        
        return str(dev_locale)
    
    def setup(self, lang=None):
        """
        Dil ayarlarını yapılandır
        
        Args:
            lang: Dil kodu (örn: 'en', 'tr', 'de'). None ise sistem dilini kullan
        """
        try:
            if lang is None:
                # Sistem dilini al
                system_locale = locale.getdefaultlocale()[0]
                if system_locale:
                    lang = system_locale.split('_')[0]
                else:
                    lang = 'en'
            
            self.current_locale = lang
            
            # gettext'i yapılandır
            try:
                self._translator = gettext.translation(
                    self.domain,
                    localedir=self.locale_dir,
                    languages=[lang],
                    fallback=True
                )
            except Exception:
                # Fallback: İngilizce varsayılan
                self._translator = gettext.translation(
                    self.domain,
                    localedir=self.locale_dir,
                    languages=['en'],
                    fallback=True
                )
            
            self._translator.install()
            
        except Exception as e:
            print(f"i18n kurulum hatası: {e}")
            # En basit fallback
            import builtins
            builtins.__dict__['_'] = lambda s: s
    
    def get_translator(self):
        """Translator fonksiyonunu döndür"""
        if self._translator:
            return self._translator.gettext
        return lambda s: s
    
    def get_available_languages(self):
        """Mevcut dilleri listele"""
        languages = [('en', 'English')]  # Varsayılan
        
        locale_path = Path(self.locale_dir)
        if locale_path.exists():
            for item in locale_path.iterdir():
                if item.is_dir() and (item / 'LC_MESSAGES' / f'{self.domain}.mo').exists():
                    lang_code = item.name
                    languages.append((lang_code, self._get_language_name(lang_code)))
        
        return languages
    
    def _get_language_name(self, code: str) -> str:
        """Dil kodundan dil ismini al"""
        names = {
            'en': 'English',
            'tr': 'Türkçe',
            'de': 'Deutsch',
            'fr': 'Français',
            'es': 'Español',
            'it': 'Italiano',
            'pt': 'Português',
            'ru': 'Русский',
            'zh': '中文',
            'ja': '日本語',
            'ar': 'العربية'
        }
        return names.get(code, code.upper())


# Global instance
_i18n = I18n()

def setup_i18n(lang=None):
    """Çok dilli desteği başlat"""
    _i18n.setup(lang)
    return _i18n.get_translator()

def get_i18n():
    """I18n instance'ını döndür"""
    return _i18n

# Kolay kullanım için
_ = _i18n.get_translator()
