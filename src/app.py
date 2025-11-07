"""
Ana GTK Uygulaması

GTK4 tabanlı ana uygulama window ve manager.
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib
import sys
import logging

from src.platform_manager import PlatformManager
from src.service_loader import ServiceLoader
from src.utils.i18n import setup_i18n

logger = logging.getLogger(__name__)

# Çok dilli desteği başlat
_ = setup_i18n()


class OrkestaApp(Adw.Application):
    """Ana Orkesta uygulaması"""
    
    def __init__(self):
        super().__init__(application_id='com.orkesta.Orkesta')
        
        self.platform_manager = None
        self.service_loader = None
        self.main_window = None
        
    def do_activate(self):
        """Uygulama aktive edildiğinde çağrılır"""
        if not self.main_window:
            # Platform yöneticisini başlat
            logger.info(_("Starting platform manager..."))
            self.platform_manager = PlatformManager()
            
            # Servis yükleyiciyi başlat
            logger.info(_("Loading service modules..."))
            self.service_loader = ServiceLoader(self.platform_manager)
            
            # Ana pencereyi oluştur
            from src.ui.main_window import MainWindow
            self.main_window = MainWindow(
                application=self,
                platform_manager=self.platform_manager,
                service_loader=self.service_loader
            )
        
        self.main_window.present()
    
    def do_shutdown(self):
        """Uygulama kapanırken çağrılır"""
        logger.info("Uygulama kapatılıyor...")
        Adw.Application.do_shutdown(self)


def main():
    """GTK uygulamasını başlat"""
    app = OrkestaApp()
    return app.run(sys.argv)


if __name__ == '__main__':
    sys.exit(main())
