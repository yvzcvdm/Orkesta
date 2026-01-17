"""
PHP Service - Standalone i18n System

Tamamen bağımsız çeviri sistemi - ana utils/i18n.py'ye bağımlı değil.
"""

import os
import locale as system_locale
import gettext
from typing import Callable

class PHPI18n:
    """PHP servisi için bağımsız i18n yöneticisi"""
    
    def __init__(self):
        self.domain = 'php'
        self.locale_dir = os.path.join(os.path.dirname(__file__), 'locale')
        self._translator = None
        self._setup_translation()
    
    def _setup_translation(self):
        """Çeviri sistemini kur"""
        # Sistem dilini al
        lang = os.environ.get('LANGUAGE') or os.environ.get('LANG', 'en_US').split('.')[0]
        
        try:
            # gettext translator'ı kur
            translation = gettext.translation(
                self.domain,
                localedir=self.locale_dir,
                languages=[lang],
                fallback=True
            )
            self._translator = translation.gettext
        except Exception:
            # Fallback: Direkt string döndür
            self._translator = lambda s: s
    
    def get_translator(self) -> Callable[[str], str]:
        """Translator fonksiyonunu döndür"""
        return self._translator


# Global instance
_i18n_instance = None

def get_i18n() -> PHPI18n:
    """Singleton i18n instance'ı döndür"""
    global _i18n_instance
    if _i18n_instance is None:
        _i18n_instance = PHPI18n()
    return _i18n_instance
