"""
Ana GTK Uygulaması

GTK4 tabanlı ana uygulama.
Prensip: Sadece arayüzü yönetir, servis mantığı içermez.
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Adw
import sys

from src.platform_manager import PlatformManager
from src.service_loader import ServiceLoader
from src.utils.i18n import setup_i18n

# Çok dilli desteği başlat
_ = setup_i18n()


class OrkestaApp(Adw.Application):
    """Ana Orkesta uygulaması"""
    
    def __init__(self):
        from gi.repository import Gio
        super().__init__(
            application_id='com.orkesta.Orkesta',
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS
        )
        self.platform_manager = None
        self.service_loader = None
        self.main_window = None
        
    def do_activate(self):
        """Uygulama aktive edildiğinde çağrılır"""
        try:
            if not self.main_window:
                # Platform yöneticisini başlat
                self.platform_manager = PlatformManager()
                
                # Servis yükleyiciyi başlat
                self.service_loader = ServiceLoader(self.platform_manager)
                
                # Ana pencereyi oluştur
                from src.ui.main_window import MainWindow
                self.main_window = MainWindow(
                    application=self,
                    platform_manager=self.platform_manager,
                    service_loader=self.service_loader
                )
            
            self.main_window.present()
        except Exception as e:
            print(f"❌ Hata: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    
    def do_shutdown(self):
        """Uygulama kapanırken çağrılır"""
        Adw.Application.do_shutdown(self)


def main():
    """GTK uygulamasını başlat"""
    app = OrkestaApp()
    return app.run(sys.argv)


if __name__ == '__main__':
    sys.exit(main())
