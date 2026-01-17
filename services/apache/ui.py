"""
Apache Service - UI Module

Apache Web Server yönetimi için özel arayüz
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


class ApacheView(BaseServiceView):
    """
    Apache Service UI
    
    VirtualHost, PHP modül, SSL sertifika ve Apache modül yönetimi
    """
    
    def _add_custom_sections(self):
        """Apache'ye özel bölümler"""
        self._add_port_management_section()
        self._add_apache_modules_section()
        self._add_php_modules_section()
        self._add_ssl_section()
        self._add_vhosts_section()
    
    def _add_port_management_section(self):
        """Port yönetimi bölümü"""
        ports_group = Adw.PreferencesGroup()
        ports_group.set_title(_("Port Management"))
        ports_group.set_description(_("Manage Apache listening ports"))
        
        try:
            # Get current ports
            ports = self.service.list_ports()
            
            # Show current ports
            for port_info in ports:
                port = port_info.get('port')
                is_ssl = port_info.get('ssl', False)
                
                port_row = Adw.ActionRow()
                port_row.set_title(f"Port {port}")
                
                if is_ssl:
                    port_row.set_subtitle(_("SSL/HTTPS"))
                    ssl_icon = Gtk.Image.new_from_icon_name("security-high-symbolic")
                    port_row.add_prefix(ssl_icon)
                else:
                    port_row.set_subtitle(_("HTTP"))
                    http_icon = Gtk.Image.new_from_icon_name("network-server-symbolic")
                    port_row.add_prefix(http_icon)
                
                # Remove button (don't allow removing 80 and 443 easily)
                if port not in [80, 443]:
                    remove_btn = Gtk.Button()
                    remove_btn.set_icon_name("user-trash-symbolic")
                    remove_btn.set_valign(Gtk.Align.CENTER)
                    remove_btn.add_css_class("flat")
                    remove_btn.connect("clicked", lambda b, p=port: self._on_port_remove(p))
                    port_row.add_suffix(remove_btn)
                
                ports_group.add(port_row)
            
            # Add port button
            add_port_row = Adw.ActionRow()
            add_port_row.set_title(_("Add Port"))
            add_port_row.set_subtitle(_("Add a new listening port"))
            add_port_row.set_activatable(True)
            add_port_row.connect("activated", lambda r: self._on_port_add())
            add_icon = Gtk.Image.new_from_icon_name("list-add-symbolic")
            add_port_row.add_prefix(add_icon)
            ports_group.add(add_port_row)
            
            # Change port button
            change_port_row = Adw.ActionRow()
            change_port_row.set_title(_("Change Port"))
            change_port_row.set_subtitle(_("Change an existing port number"))
            change_port_row.set_activatable(True)
            change_port_row.connect("activated", lambda r: self._on_port_change())
            change_icon = Gtk.Image.new_from_icon_name("emblem-synchronizing-symbolic")
            change_port_row.add_prefix(change_icon)
            ports_group.add(change_port_row)
        
        except Exception as e:
            logger.error(f"Error loading ports: {e}")
            error_row = Adw.ActionRow()
            error_row.set_title(_("Error"))
            error_row.set_subtitle(str(e))
            error_row.set_sensitive(False)
            ports_group.add(error_row)
        
        self.main_box.append(ports_group)
    
    def _add_apache_modules_section(self):
        """Apache modülleri yönetimi"""
        modules_group = Adw.PreferencesGroup()
        modules_group.set_title(_("Apache Modules"))
        modules_group.set_description(_("Manage Apache modules (enable/disable)"))
        
        try:
            # Manage Modules button
            manage_modules_row = Adw.ActionRow()
            manage_modules_row.set_title(_("Manage Modules"))
            manage_modules_row.set_subtitle(_("Enable or disable Apache modules"))
            manage_modules_row.set_activatable(True)
            manage_modules_row.connect("activated", lambda r: self._on_apache_manage_modules())
            manage_icon = Gtk.Image.new_from_icon_name("preferences-system-symbolic")
            manage_modules_row.add_prefix(manage_icon)
            modules_group.add(manage_modules_row)
            
            # Show some key modules status
            modules = self.service.list_modules()
            
            # Show SSL module
            ssl_modules = [m for m in modules if m['name'] == 'ssl']
            if ssl_modules:
                ssl_mod = ssl_modules[0]
                ssl_row = Adw.ActionRow()
                ssl_row.set_title("SSL Module")
                if ssl_mod['enabled']:
                    status_label = Gtk.Label(label="✅ " + _("Enabled"))
                    status_label.add_css_class("success")
                else:
                    status_label = Gtk.Label(label="❌ " + _("Disabled"))
                    status_label.add_css_class("error")
                ssl_row.add_suffix(status_label)
                modules_group.add(ssl_row)
            
            # Show Rewrite module
            rewrite_modules = [m for m in modules if m['name'] == 'rewrite']
            if rewrite_modules:
                rewrite_mod = rewrite_modules[0]
                rewrite_row = Adw.ActionRow()
                rewrite_row.set_title("Rewrite Module")
                if rewrite_mod['enabled']:
                    status_label = Gtk.Label(label="✅ " + _("Enabled"))
                    status_label.add_css_class("success")
                else:
                    status_label = Gtk.Label(label="❌ " + _("Disabled"))
                    status_label.add_css_class("error")
                rewrite_row.add_suffix(status_label)
                modules_group.add(rewrite_row)
            
            # Show module count
            enabled_count = sum(1 for m in modules if m['enabled'])
            total_count = len(modules)
            count_row = Adw.ActionRow()
            count_row.set_title(_("Total Modules"))
            count_label = Gtk.Label(label=f"{enabled_count}/{total_count} " + _("enabled"))
            count_label.add_css_class("monospace")
            count_row.add_suffix(count_label)
            modules_group.add(count_row)
        
        except Exception as e:
            logger.error(f"Error loading modules: {e}")
            error_row = Adw.ActionRow()
            error_row.set_title(_("Error"))
            error_row.set_subtitle(str(e))
            error_row.set_sensitive(False)
            modules_group.add(error_row)
        
        self.main_box.append(modules_group)
    
    def _add_php_modules_section(self):
        """PHP modülleri (Apache-specific)"""
        php_modules_group = Adw.PreferencesGroup()
        php_modules_group.set_title(_("PHP Modules"))
        php_modules_group.set_description(_("Manage PHP Apache modules (install/switch/remove)"))
        
        try:
            php_module_installed = self.service.is_php_module_installed()
            
            if php_module_installed:
                # Get PHP module list
                php_modules = self.service.get_installed_php_modules()
                active_php_module = self.service.get_active_php_module()
                
                # Active PHP Apache module
                active_module_row = Adw.ActionRow()
                active_module_row.set_title(_("Active PHP Apache Module"))
                if active_php_module:
                    module_label = Gtk.Label(label=f"PHP {active_php_module}")
                    module_label.add_css_class("monospace")
                    module_label.add_css_class("success")
                    active_module_row.add_suffix(module_label)
                else:
                    module_label = Gtk.Label(label=_("None"))
                    module_label.add_css_class("dim-label")
                    active_module_row.add_suffix(module_label)
                php_modules_group.add(active_module_row)
                
                # List installed PHP modules
                if php_modules and len(php_modules) > 0:
                    modules_row = Adw.ActionRow()
                    modules_row.set_title(_("Installed PHP Modules"))
                    modules_info = []
                    for mod in php_modules:
                        status = "✅" if mod['enabled'] else "⚪"
                        modules_info.append(f"{status} PHP {mod['version']}")
                    modules_row.set_subtitle(" • ".join(modules_info))
                    php_modules_group.add(modules_row)
                
                # Switch PHP module (if multiple available)
                if php_modules and len(php_modules) > 1:
                    switch_module_row = Adw.ActionRow()
                    switch_module_row.set_title(_("Switch PHP Module"))
                    switch_module_row.set_subtitle(_("Change active PHP Apache module"))
                    switch_module_row.set_activatable(True)
                    switch_module_row.connect("activated", lambda r: self._on_apache_switch_php_module(php_modules))
                    switch_module_icon = Gtk.Image.new_from_icon_name("emblem-synchronizing-symbolic")
                    switch_module_row.add_prefix(switch_module_icon)
                    php_modules_group.add(switch_module_row)
                
                # Install PHP module
                install_php_module_row = Adw.ActionRow()
                install_php_module_row.set_title(_("Install PHP Module"))
                install_php_module_row.set_subtitle(_("Install PHP Apache module for a specific version"))
                install_php_module_row.set_activatable(True)
                install_php_module_row.connect("activated", lambda r: self._on_apache_install_php_module_dialog())
                install_php_module_icon = Gtk.Image.new_from_icon_name("list-add-symbolic")
                install_php_module_row.add_prefix(install_php_module_icon)
                php_modules_group.add(install_php_module_row)
                
                # Uninstall PHP module
                if php_modules and len(php_modules) > 0:
                    uninstall_php_module_row = Adw.ActionRow()
                    uninstall_php_module_row.set_title(_("Uninstall PHP Module"))
                    uninstall_php_module_row.set_subtitle(_("Remove a PHP Apache module"))
                    uninstall_php_module_row.set_activatable(True)
                    uninstall_php_module_row.connect("activated", lambda r: self._on_apache_uninstall_php_module_dialog(php_modules))
                    uninstall_php_module_icon = Gtk.Image.new_from_icon_name("edit-delete-symbolic")
                    uninstall_php_module_row.add_prefix(uninstall_php_module_icon)
                    php_modules_group.add(uninstall_php_module_row)
            else:
                # Install PHP module button
                install_php_module_row = Adw.ActionRow()
                install_php_module_row.set_title(_("Install PHP Module"))
                install_php_module_row.set_subtitle(_("Install PHP Apache module"))
                install_php_module_row.set_activatable(True)
                install_php_module_row.connect("activated", lambda r: self._on_apache_install_php_module_dialog())
                install_php_module_icon = Gtk.Image.new_from_icon_name("list-add-symbolic")
                install_php_module_row.add_prefix(install_php_module_icon)
                php_modules_group.add(install_php_module_row)
        
        except Exception as e:
            logger.error(f"Error loading PHP modules: {e}")
            error_row = Adw.ActionRow()
            error_row.set_title(_("Error"))
            error_row.set_subtitle(str(e))
            error_row.set_sensitive(False)
            php_modules_group.add(error_row)
        
        self.main_box.append(php_modules_group)
    
    def _add_ssl_section(self):
        """SSL sertifika yönetimi"""
        ssl_cert_group = Adw.PreferencesGroup()
        ssl_cert_group.set_title(_("SSL Certificates"))
        
        try:
            # Create self-signed certificate button
            create_cert_row = Adw.ActionRow()
            create_cert_row.set_title(_("Create Self-Signed Certificate"))
            create_cert_row.set_subtitle(_("Generate SSL certificate for a domain"))
            create_cert_row.set_activatable(True)
            create_cert_row.connect("activated", lambda r: self._on_apache_create_certificate())
            create_cert_icon = Gtk.Image.new_from_icon_name("document-new-symbolic")
            create_cert_row.add_prefix(create_cert_icon)
            ssl_cert_group.add(create_cert_row)
        
        except Exception as e:
            logger.error(f"Error with SSL certificates: {e}")
        
        self.main_box.append(ssl_cert_group)
    
    def _add_vhosts_section(self):
        """VirtualHost yönetimi"""
        vhosts_group = Adw.PreferencesGroup()
        vhosts_group.set_title(_("Virtual Hosts"))
        
        try:
            vhosts = self.service.list_vhosts()
            
            # Create vhost button
            create_vhost_row = Adw.ActionRow()
            create_vhost_row.set_title(_("Create Virtual Host"))
            create_vhost_row.set_subtitle(_("Add a new website configuration"))
            create_vhost_row.set_activatable(True)
            create_vhost_row.connect("activated", lambda r: self._on_apache_create_vhost())
            create_vhost_icon = Gtk.Image.new_from_icon_name("list-add-symbolic")
            create_vhost_row.add_prefix(create_vhost_icon)
            vhosts_group.add(create_vhost_row)
            
            # List existing vhosts
            if vhosts:
                # Add separator
                separator_row = Adw.ActionRow()
                separator_row.set_title(_("Existing Virtual Hosts"))
                separator_row.set_sensitive(False)
                vhosts_group.add(separator_row)
                
                for vhost in vhosts:
                    vhost_row = Adw.ActionRow()
                    
                    # Use server_name as title, fallback to filename
                    title = vhost.get('server_name', vhost.get('filename', 'Unknown'))
                    if not title or title == '':
                        title = vhost.get('filename', 'Unknown')
                    if title.endswith('.conf'):
                        title = title[:-5]  # Remove .conf extension
                    
                    vhost_row.set_title(title)
                    
                    # Subtitle with status info
                    subtitle_parts = []
                    
                    # Enabled status
                    if vhost.get('enabled'):
                        subtitle_parts.append("✅ Enabled")
                    else:
                        subtitle_parts.append("❌ Disabled")
                    
                    # SSL status
                    if vhost.get('ssl'):
                        subtitle_parts.append("🔒 SSL")
                    
                    # PHP version
                    php_version = vhost.get('php_version', '')
                    if php_version:
                        subtitle_parts.append(f"🐘 PHP {php_version}")
                    
                    # Filename if different from title
                    if vhost.get('filename') and vhost.get('filename') != title and not title.endswith('.conf'):
                        subtitle_parts.append(vhost['filename'])
                    
                    vhost_row.set_subtitle(' • '.join(subtitle_parts))
                    vhost_row.set_activatable(True)
                    vhost_row.connect("activated", lambda r, v=vhost: self._show_vhost_detail(v))
                    
                    # Arrow icon to indicate clickable
                    arrow = Gtk.Image.new_from_icon_name("go-next-symbolic")
                    arrow.set_valign(Gtk.Align.CENTER)
                    vhost_row.add_suffix(arrow)
                    
                    vhosts_group.add(vhost_row)
        
        except Exception as e:
            logger.error(f"Error listing vhosts: {e}")
        
        self.main_box.append(vhosts_group)
    
    # ============================================
    # EVENT HANDLERS (MainWindow'a delege et)
    # ============================================
    
    def _on_apache_manage_modules(self):
        """Apache modüllerini yönet"""
        self.main_window._on_apache_manage_modules(self.service)
    
    def _on_apache_switch_php_module(self, php_modules):
        """PHP modülünü değiştir"""
        self.main_window._on_apache_switch_php_module(self.service, php_modules)
    
    def _on_apache_install_php_module_dialog(self):
        """PHP modülü kur"""
        self.main_window._on_apache_install_php_module_dialog(self.service)
    
    def _on_apache_uninstall_php_module_dialog(self, php_modules):
        """PHP modülünü kaldır"""
        self.main_window._on_apache_uninstall_php_module_dialog(self.service, php_modules)
    
    def _on_apache_create_certificate(self):
        """SSL sertifikası oluştur"""
        self.main_window._on_apache_create_certificate(self.service)
    
    def _on_apache_create_vhost(self):
        """VirtualHost oluştur"""
        self.main_window._on_apache_create_vhost(self.service)
    
    def _show_vhost_detail(self, vhost):
        """VirtualHost detayını göster"""
        self.main_window._show_vhost_detail(self.service, vhost)
    
    def _on_port_add(self):
        """Yeni port ekle"""
        dialog = Adw.MessageDialog.new(self.main_window)
        dialog.set_heading(_("Add Port"))
        dialog.set_body(_("Enter the port number Apache should listen on"))
        
        # Create content box
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content_box.set_margin_start(12)
        content_box.set_margin_end(12)
        content_box.set_margin_top(12)
        content_box.set_margin_bottom(12)
        
        # Port entry
        port_entry = Gtk.Entry()
        port_entry.set_placeholder_text(_("Port number (1-65535)"))
        port_entry.set_input_purpose(Gtk.InputPurpose.DIGITS)
        content_box.append(port_entry)
        
        # SSL checkbox
        ssl_check = Gtk.CheckButton()
        ssl_check.set_label(_("SSL/HTTPS port"))
        content_box.append(ssl_check)
        
        dialog.set_extra_child(content_box)
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("add", _("Add"))
        dialog.set_response_appearance("add", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_default_response("add")
        
        def on_response(dialog, response):
            if response == "add":
                try:
                    port = int(port_entry.get_text().strip())
                    if port < 1 or port > 65535:
                        self.main_window._show_toast(_("Invalid port number. Must be between 1-65535"))
                        return
                    
                    is_ssl = ssl_check.get_active()
                    success, message = self.service.add_port(port, is_ssl)
                    self.main_window._show_toast(message)
                    
                    if success:
                        dialog.close()
                        # Refresh view
                        self.main_window._refresh_detail_page()
                except ValueError:
                    self.main_window._show_toast(_("Please enter a valid port number"))
        
        dialog.connect("response", on_response)
        dialog.present()
    
    def _on_port_remove(self, port):
        """Port kaldır"""
        dialog = Adw.MessageDialog.new(self.main_window)
        dialog.set_heading(_("Remove Port {port}?").format(port=port))
        
        if port in [80, 443]:
            dialog.set_body(_("Warning: Removing default port {port} may break virtual hosts.\n\nAre you sure you want to continue?").format(port=port))
        else:
            dialog.set_body(_("Are you sure you want to remove port {port}?").format(port=port))
        
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("remove", _("Remove"))
        dialog.set_response_appearance("remove", Adw.ResponseAppearance.DESTRUCTIVE)
        
        def on_response(dialog, response):
            if response == "remove":
                success, message = self.service.remove_port(port)
                self.main_window._show_toast(message)
                
                if success:
                    dialog.close()
                    # Refresh view
                    self.main_window._refresh_detail_page()
        
        dialog.connect("response", on_response)
        dialog.present()
    
    def _on_port_change(self):
        """Port değiştir"""
        # Get current ports
        ports = self.service.list_ports()
        
        if not ports:
            self.main_window._show_toast(_("No ports configured"))
            return
        
        dialog = Adw.MessageDialog.new(self.main_window)
        dialog.set_heading(_("Change Port"))
        dialog.set_body(_("Select the port to change and enter the new port number"))
        
        # Create content box
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content_box.set_margin_start(12)
        content_box.set_margin_end(12)
        content_box.set_margin_top(12)
        content_box.set_margin_bottom(12)
        
        # Old port dropdown
        old_port_label = Gtk.Label(label=_("Current Port:"))
        old_port_label.set_halign(Gtk.Align.START)
        content_box.append(old_port_label)
        
        old_port_dropdown = Gtk.DropDown()
        port_strings = [str(p['port']) for p in ports]
        old_port_dropdown.set_model(Gtk.StringList.new(port_strings))
        content_box.append(old_port_dropdown)
        
        # New port entry
        new_port_label = Gtk.Label(label=_("New Port:"))
        new_port_label.set_halign(Gtk.Align.START)
        content_box.append(new_port_label)
        
        new_port_entry = Gtk.Entry()
        new_port_entry.set_placeholder_text(_("Port number (1-65535)"))
        new_port_entry.set_input_purpose(Gtk.InputPurpose.DIGITS)
        content_box.append(new_port_entry)
        
        dialog.set_extra_child(content_box)
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("change", _("Change"))
        dialog.set_response_appearance("change", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_default_response("change")
        
        def on_response(dialog, response):
            if response == "change":
                try:
                    selected_idx = old_port_dropdown.get_selected()
                    old_port = int(port_strings[selected_idx])
                    new_port = int(new_port_entry.get_text().strip())
                    
                    if new_port < 1 or new_port > 65535:
                        self.main_window._show_toast(_("Invalid port number. Must be between 1-65535"))
                        return
                    
                    if old_port == new_port:
                        self.main_window._show_toast(_("Old and new port are the same"))
                        return
                    
                    success, message = self.service.set_port(old_port, new_port)
                    self.main_window._show_toast(message)
                    
                    if success:
                        dialog.close()
                        # Refresh view
                        self.main_window._refresh_detail_page()
                except ValueError:
                    self.main_window._show_toast(_("Please enter a valid port number"))
                except IndexError:
                    self.main_window._show_toast(_("Please select a port"))
        
        dialog.connect("response", on_response)
        dialog.present()
