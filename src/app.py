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
                # İlk önce sudo şifresi iste
                self._request_sudo_password()
                
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
    
    def _request_sudo_password(self):
        """Uygulama başlangıcında sudo şifresi iste"""
        import subprocess
        import os
        from gi.repository import Gtk, Adw, GLib
        
        # Sudo gerekip gerekmediğini kontrol et
        try:
            # Test sudo access
            result = subprocess.run(['sudo', '-n', 'true'], capture_output=True, timeout=1)
            if result.returncode == 0:
                # Sudo cache'de var, şifre istemeye gerek yok
                return
        except:
            pass
        
        # Sudo şifresi dialog'u
        dialog = Adw.MessageDialog.new(None)
        dialog.set_heading(_("Administrator Access Required"))
        dialog.set_body(_("Orkesta needs administrator privileges for system operations. Please enter your password."))
        
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("ok", _("OK"))
        dialog.set_response_appearance("ok", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_default_response("ok")
        
        # Password entry
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        content_box.set_spacing(12)
        content_box.set_margin_top(12)
        content_box.set_margin_bottom(12)
        content_box.set_margin_start(12)
        content_box.set_margin_end(12)
        
        password_entry = Adw.PasswordEntryRow()
        password_entry.set_title(_("Password"))
        password_entry.set_show_apply_button(False)
        
        content_box.append(password_entry)
        dialog.set_extra_child(content_box)
        
        password_accepted = False
        
        def on_response(dialog, response):
            nonlocal password_accepted
            if response == "ok":
                password = password_entry.get_text()
                if password:
                    # Test password
                    try:
                        result = subprocess.run(
                            ['sudo', '-S', 'true'], 
                            input=password + '\n', 
                            text=True,
                            capture_output=True,
                            timeout=5
                        )
                        if result.returncode == 0:
                            password_accepted = True
                            dialog.close()
                            return
                        else:
                            # Wrong password
                            password_entry.set_text("")
                            password_entry.add_css_class("error")
                            GLib.timeout_add(2000, lambda: password_entry.remove_css_class("error"))
                            return
                    except Exception as e:
                        print(f"Sudo test error: {e}")
                        
                # Empty or wrong password
                if not password:
                    password_entry.add_css_class("error")
                    GLib.timeout_add(1000, lambda: password_entry.remove_css_class("error"))
            else:
                # Cancel
                dialog.close()
                sys.exit(0)
        
        dialog.connect("response", on_response)
        
        # Enter key activation
        def on_entry_activate(entry):
            dialog.response("ok")
        
        password_entry.connect("entry-activated", on_entry_activate)
        
        dialog.present()
        password_entry.grab_focus()
        
        # Wait for dialog to close
        from gi.repository import GLib
        main_context = GLib.MainContext.default()
        while not password_accepted and dialog.get_visible():
            main_context.iteration(False)
    
    def do_shutdown(self):
        """Uygulama kapanırken çağrılır"""
        Adw.Application.do_shutdown(self)


def main():
    """GTK uygulamasını başlat"""
    app = OrkestaApp()
    return app.run(sys.argv)


if __name__ == '__main__':
    sys.exit(main())
