"""
PHP Service - UI Module

PHP version ve extension yönetimi için özel arayüz
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw
import logging
from ui.services.base_view import BaseServiceView
from utils.i18n import get_i18n

logger = logging.getLogger(__name__)
_ = get_i18n().get_translator()


class PHPView(BaseServiceView):
    """
    PHP Service UI
    
    PHP version ve extension yönetimi
    """
    
    def _add_custom_sections(self):
        """PHP'ye özel bölümler"""
        self._add_version_management_section()
        self._add_version_actions_section()
        self._add_extensions_section()
    
    def _add_version_management_section(self):
        """PHP version bilgileri"""
        try:
            # Get PHP information
            php_info = self.service.get_php_info()
            
            # PHP Version Management
            version_group = Adw.PreferencesGroup()
            version_group.set_title(_("PHP Version Management"))
            
            # Active version
            active_version_row = Adw.ActionRow()
            active_version_row.set_title(_("Active Version"))
            active_version = php_info.get('active_version', 'Unknown')
            version_label = Gtk.Label(label=f"PHP {active_version}")
            version_label.add_css_class("monospace")
            active_version_row.add_suffix(version_label)
            version_group.add(active_version_row)
            
            # Installed versions
            installed_versions = php_info.get('installed_versions', [])
            if len(installed_versions) > 1:
                installed_row = Adw.ActionRow()
                installed_row.set_title(_("Installed Versions"))
                installed_row.set_subtitle(", ".join(installed_versions))
                version_group.add(installed_row)
            
            # Available versions
            available_versions = php_info.get('available_versions', [])
            available_row = Adw.ActionRow()
            available_row.set_title(_("Available Versions"))
            available_row.set_subtitle(", ".join(available_versions))
            version_group.add(available_row)
            
            self.main_box.append(version_group)
            
            # Store for later use
            self.installed_versions = installed_versions
            self.available_versions = available_versions
            
        except Exception as e:
            logger.error(f"Error getting PHP info: {e}")
            error_group = Adw.PreferencesGroup()
            error_group.set_title(_("PHP Information"))
            error_row = Adw.ActionRow()
            error_row.set_title(_("Error"))
            error_row.set_subtitle(str(e))
            error_group.add(error_row)
            self.main_box.append(error_group)
            
            self.installed_versions = []
            self.available_versions = []
    
    def _add_version_actions_section(self):
        """Version yönetim işlemleri"""
        version_actions_group = Adw.PreferencesGroup()
        version_actions_group.set_title(_("Version Actions"))
        
        # Install new version
        install_version_row = Adw.ActionRow()
        install_version_row.set_title(_("Install New Version"))
        install_version_row.set_subtitle(_("Install additional PHP version"))
        install_version_row.set_activatable(True)
        install_version_row.connect("activated", lambda r: self._on_php_install_version())
        install_icon = Gtk.Image.new_from_icon_name("list-add-symbolic")
        install_version_row.add_prefix(install_icon)
        version_actions_group.add(install_version_row)
        
        # Switch version (if multiple versions available)
        if len(self.installed_versions) > 1:
            switch_version_row = Adw.ActionRow()
            switch_version_row.set_title(_("Switch Version"))
            switch_version_row.set_subtitle(_("Change active PHP version"))
            switch_version_row.set_activatable(True)
            switch_version_row.connect("activated", lambda r: self._on_php_switch_version())
            switch_icon = Gtk.Image.new_from_icon_name("emblem-synchronizing-symbolic")
            switch_version_row.add_prefix(switch_icon)
            version_actions_group.add(switch_version_row)
        
        # Uninstall version (if multiple versions available)
        if len(self.installed_versions) > 1:
            uninstall_version_row = Adw.ActionRow()
            uninstall_version_row.set_title(_("Uninstall Version"))
            uninstall_version_row.set_subtitle(_("Remove a PHP version"))
            uninstall_version_row.set_activatable(True)
            uninstall_version_row.connect("activated", lambda r: self._on_php_uninstall_version())
            uninstall_icon = Gtk.Image.new_from_icon_name("edit-delete-symbolic")
            uninstall_version_row.add_prefix(uninstall_icon)
            version_actions_group.add(uninstall_version_row)
        
        self.main_box.append(version_actions_group)
    
    def _add_extensions_section(self):
        """Extension yönetimi"""
        try:
            extensions_group = Adw.PreferencesGroup()
            extensions_group.set_title(_("Extensions"))
            
            # Get installed extensions
            installed_extensions = self.service.get_installed_extensions()
            popular_extensions = self.service.get_popular_extensions()
            
            # Extension count
            ext_count_row = Adw.ActionRow()
            ext_count_row.set_title(_("Installed Extensions"))
            ext_count_label = Gtk.Label(label=str(len(installed_extensions)))
            ext_count_label.add_css_class("monospace")
            ext_count_row.add_suffix(ext_count_label)
            extensions_group.add(ext_count_row)
            
            # Install extension
            install_ext_row = Adw.ActionRow()
            install_ext_row.set_title(_("Install Extension"))
            install_ext_row.set_subtitle(_("Install a PHP extension"))
            install_ext_row.set_activatable(True)
            install_ext_row.connect("activated", lambda r: self._on_php_install_extension(popular_extensions, installed_extensions))
            install_ext_icon = Gtk.Image.new_from_icon_name("list-add-symbolic")
            install_ext_row.add_prefix(install_ext_icon)
            extensions_group.add(install_ext_row)
            
            # Manage extensions
            manage_ext_row = Adw.ActionRow()
            manage_ext_row.set_title(_("Manage Extensions"))
            manage_ext_row.set_subtitle(_("View and uninstall extensions"))
            manage_ext_row.set_activatable(True)
            manage_ext_row.connect("activated", lambda r: self._on_php_manage_extensions(installed_extensions))
            manage_ext_icon = Gtk.Image.new_from_icon_name("preferences-system-symbolic")
            manage_ext_row.add_prefix(manage_ext_icon)
            extensions_group.add(manage_ext_row)
            
            self.main_box.append(extensions_group)
            
        except Exception as e:
            logger.error(f"Error adding extensions section: {e}")
    
    # ============================================
    # EVENT HANDLERS (MainWindow'a delege et)
    # ============================================
    
    def _on_php_install_version(self):
        """Yeni PHP version kur"""
        self.main_window._on_php_install_version(self.service, self.available_versions)
    
    def _on_php_switch_version(self):
        """PHP version değiştir"""
        self.main_window._on_php_switch_version(self.service, self.installed_versions)
    
    def _on_php_uninstall_version(self):
        """PHP version kaldır"""
        self.main_window._on_php_uninstall_version(self.service, self.installed_versions)
    
    def _on_php_install_extension(self, popular_extensions, installed_extensions):
        """Extension kur"""
        self.main_window._on_php_install_extension(self.service, popular_extensions, installed_extensions)
    
    def _on_php_manage_extensions(self, installed_extensions):
        """Extension'ları yönet"""
        self.main_window._on_php_manage_extensions(self.service, installed_extensions)
