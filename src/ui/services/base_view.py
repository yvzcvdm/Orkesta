"""
Base Service View

Her servis için ortak UI yapısı.
Her servis bu sınıfı extend ederek kendi özel bölümlerini ekler.
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw
import logging
from src.utils.i18n import get_i18n

logger = logging.getLogger(__name__)
_ = get_i18n().get_translator()


class BaseServiceView:
    """
    Base Service View Class
    
    Her servis bu sınıfı extend ederek:
    - Standart header/status/actions bölümünü alır
    - _add_custom_sections() metodunu override ederek özel bölümler ekler
    """
    
    def __init__(self, service, main_window):
        """
        Args:
            service: BaseService instance
            main_window: MainWindow instance (callbacks için)
        """
        self.service = service
        self.main_window = main_window
    
    def create_view(self) -> Gtk.Widget:
        """Ana view'ı oluştur"""
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_hexpand(True)
        
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.main_box.set_spacing(24)
        self.main_box.set_margin_top(24)
        self.main_box.set_margin_bottom(24)
        self.main_box.set_margin_start(24)
        self.main_box.set_margin_end(24)
        
        # Standart bölümler
        self._add_header_section()
        self._add_actions_section()
        
        # Servise özel bölümler (alt sınıflar override edebilir)
        if self.service.is_installed():
            self._add_custom_sections()
        
        scrolled.set_child(self.main_box)
        return scrolled
    
    def _add_header_section(self):
        """Header section - Status, Port, Type"""
        header_group = Adw.PreferencesGroup()
        header_group.set_title(self.service.display_name)
        header_group.set_description(self.service.description)
        
        # Status row
        status = self.service.get_status().value
        status_row = Adw.ActionRow()
        status_row.set_title(_("Status"))
        
        if status == "running":
            status_label = Gtk.Label(label="🟢 Running")
            status_label.add_css_class("success")
        elif status == "stopped":
            status_label = Gtk.Label(label="🔴 Stopped")
            status_label.add_css_class("warning")
        elif status == "not_installed":
            status_label = Gtk.Label(label="❌ Not Installed")
            status_label.add_css_class("error")
        else:
            status_label = Gtk.Label(label="⚪ Unknown")
        
        status_row.add_suffix(status_label)
        header_group.add(status_row)
        
        # Port row (opsiyonel)
        if self.service.default_port:
            port_row = Adw.ActionRow()
            port_row.set_title(_("Port"))
            port_label = Gtk.Label(label=str(self.service.default_port))
            port_label.add_css_class("monospace")
            port_row.add_suffix(port_label)
            header_group.add(port_row)
        
        # Type row
        type_row = Adw.ActionRow()
        type_row.set_title(_("Type"))
        type_label = Gtk.Label(label=self.service.service_type.value.replace('_', ' ').title())
        type_row.add_suffix(type_label)
        header_group.add(type_row)
        
        self.main_box.append(header_group)
    
    def _add_actions_section(self):
        """Actions section - Start/Stop/Install/Uninstall"""
        actions_group = Adw.PreferencesGroup()
        actions_group.set_title(_("Actions"))
        
        # Sadece gerçek servisler için start/stop göster
        is_service = getattr(self.service, 'is_service', True)
        
        if self.service.is_installed():
            # Service control buttons (sadece gerçek servisler için)
            if is_service and self.service.is_running():
                # Stop button
                stop_row = Adw.ActionRow()
                stop_row.set_title(_("Stop Service"))
                stop_row.set_subtitle(_("Stop the running service"))
                stop_row.set_activatable(True)
                stop_row.connect("activated", lambda r: self._on_service_stop())
                stop_icon = Gtk.Image.new_from_icon_name("media-playback-stop-symbolic")
                stop_row.add_prefix(stop_icon)
                actions_group.add(stop_row)
                
                # Restart button
                restart_row = Adw.ActionRow()
                restart_row.set_title(_("Restart Service"))
                restart_row.set_subtitle(_("Restart the service"))
                restart_row.set_activatable(True)
                restart_row.connect("activated", lambda r: self._on_service_restart())
                restart_icon = Gtk.Image.new_from_icon_name("view-refresh-symbolic")
                restart_row.add_prefix(restart_icon)
                actions_group.add(restart_row)
            elif is_service and not self.service.is_running():
                # Start button
                start_row = Adw.ActionRow()
                start_row.set_title(_("Start Service"))
                start_row.set_subtitle(_("Start the service"))
                start_row.set_activatable(True)
                start_row.connect("activated", lambda r: self._on_service_start())
                start_icon = Gtk.Image.new_from_icon_name("media-playback-start-symbolic")
                start_row.add_prefix(start_icon)
                actions_group.add(start_row)
            
            # Uninstall button (sadece uninstall edilebilen servisler için)
            if self.service.can_uninstall:
                uninstall_row = Adw.ActionRow()
                uninstall_row.set_title(_("Uninstall"))
                uninstall_row.set_subtitle(_("Remove this service from your system"))
                uninstall_row.set_activatable(True)
                uninstall_row.connect("activated", lambda r: self._on_service_uninstall())
                uninstall_icon = Gtk.Image.new_from_icon_name("user-trash-symbolic")
                uninstall_row.add_prefix(uninstall_icon)
                actions_group.add(uninstall_row)
        else:
            # Install button
            install_row = Adw.ActionRow()
            install_row.set_title(_("Install"))
            install_row.set_subtitle(_("Install this service and its dependencies"))
            install_row.set_activatable(True)
            install_row.connect("activated", lambda r: self._on_service_install())
            install_icon = Gtk.Image.new_from_icon_name("document-save-symbolic")
            install_row.add_prefix(install_icon)
            actions_group.add(install_row)
        
        self.main_box.append(actions_group)
    
    def _add_custom_sections(self):
        """
        Servise özel bölümler (override edilebilir)
        Alt sınıflar bu metodu override ederek kendi UI'larını ekler
        """
        pass
    
    # ============================================
    # CALLBACK METHODS (MainWindow delegasyonu)
    # ============================================
    
    def _on_service_install(self):
        """Install action"""
        self.main_window._on_service_install(self.service)
    
    def _on_service_uninstall(self):
        """Uninstall action"""
        self.main_window._on_service_uninstall(self.service)
    
    def _on_service_start(self):
        """Start action"""
        self.main_window._on_service_start(self.service)
    
    def _on_service_stop(self):
        """Stop action"""
        self.main_window._on_service_stop(self.service)
    
    def _on_service_restart(self):
        """Restart action"""
        self.main_window._on_service_restart(self.service)
    
    # ============================================
    # UTILITY METHODS
    # ============================================
    
    def refresh_view(self):
        """View'ı yenile (servis değiştikten sonra)"""
        # Ana pencereye detay sayfasını yeniden oluşturmasını söyle
        self.main_window._refresh_detail_page()
