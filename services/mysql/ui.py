"""
MySQL Service - UI Module

MySQL/MariaDB database yönetimi için özel arayüz
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw
import logging
from src.ui.services.base_view import BaseServiceView
from src.utils.i18n import get_i18n

logger = logging.getLogger(__name__)
_ = get_i18n().get_translator()


class MySQLView(BaseServiceView):
    """
    MySQL Service UI
    
    Database, kullanıcı ve root password yönetimi
    """
    
    def _add_custom_sections(self):
        """MySQL'e özel bölümler"""
        self._add_mysql_status_section()
        self._add_mysql_management_section()
    
    def _add_mysql_status_section(self):
        """MySQL status bilgileri"""
        mysql_info_group = Adw.PreferencesGroup()
        mysql_info_group.set_title(_("MySQL Status"))
        
        try:
            # Get MySQL info
            mysql_info = self.service.get_mysql_status_info()
            
            # Root access status
            root_access_row = Adw.ActionRow()
            root_access_row.set_title(_("Root Access"))
            if mysql_info.get('root_access', False):
                if mysql_info.get('auth_method') == 'Unix Socket (sudo mysql)':
                    root_status_label = Gtk.Label(label="🔓 Unix Socket (sudo)")
                    root_status_label.add_css_class("success")
                else:
                    root_status_label = Gtk.Label(label="🔐 Password Auth")
                    root_status_label.add_css_class("success")
            else:
                root_status_label = Gtk.Label(label="🔒 Access Denied")
                root_status_label.add_css_class("error")
            
            root_access_row.add_suffix(root_status_label)
            mysql_info_group.add(root_access_row)
            
            # Root password/method display
            auth_row = Adw.ActionRow()
            auth_row.set_title(_("Authentication Method"))
            auth_method = mysql_info.get('auth_method', 'Unknown')
            auth_label = Gtk.Label(label=auth_method)
            auth_label.add_css_class("monospace")
            auth_row.add_suffix(auth_label)
            mysql_info_group.add(auth_row)
            
            # Version row
            version_row = Adw.ActionRow()
            version_row.set_title(_("MySQL Version"))
            version_label = Gtk.Label(label=mysql_info.get('version', 'Unknown'))
            version_label.add_css_class("monospace")
            version_row.add_suffix(version_label)
            mysql_info_group.add(version_row)
            
            # Database count (clickable to show list)
            db_count_row = Adw.ActionRow()
            db_count_row.set_title(_("Databases"))
            db_count_row.set_subtitle(_("Click to view database list"))
            db_count_label = Gtk.Label(label=str(mysql_info.get('databases_count', 0)))
            db_count_label.add_css_class("monospace")
            db_count_row.add_suffix(db_count_label)
            db_count_row.set_activatable(True)
            db_count_row.connect("activated", lambda r: self._show_mysql_databases(mysql_info.get('databases', [])))
            mysql_info_group.add(db_count_row)
            
            # Users count (clickable to show list)  
            users_count_row = Adw.ActionRow()
            users_count_row.set_title(_("Users"))
            users_count_row.set_subtitle(_("Click to view user list"))
            users_count_label = Gtk.Label(label=str(mysql_info.get('users_count', 0)))
            users_count_label.add_css_class("monospace")
            users_count_row.add_suffix(users_count_label)
            users_count_row.set_activatable(True)
            users_count_row.connect("activated", lambda r: self._show_mysql_users(mysql_info.get('users', [])))
            mysql_info_group.add(users_count_row)
            
        except Exception as e:
            logger.error(f"Error getting MySQL info: {e}")
            error_row = Adw.ActionRow()
            error_row.set_title(_("Status"))
            error_label = Gtk.Label(label="❌ Error loading info")
            error_label.add_css_class("error")
            error_row.add_suffix(error_label)
            mysql_info_group.add(error_row)
        
        self.main_box.append(mysql_info_group)
    
    def _add_mysql_management_section(self):
        """MySQL yönetim işlemleri"""
        mysql_management_group = Adw.PreferencesGroup()
        mysql_management_group.set_title(_("MySQL Management"))
        
        # Change Root Password
        password_row = Adw.ActionRow()
        password_row.set_title(_("Change Root Password"))
        password_row.set_subtitle(_("Set or change MySQL root password"))
        password_row.set_activatable(True)
        password_row.connect("activated", lambda r: self._on_mysql_change_password())
        password_icon = Gtk.Image.new_from_icon_name("dialog-password-symbolic")
        password_row.add_prefix(password_icon)
        mysql_management_group.add(password_row)
        
        self.main_box.append(mysql_management_group)
    
    # ============================================
    # EVENT HANDLERS (MainWindow'a delege et)
    # ============================================
    
    def _show_mysql_databases(self, databases):
        """Database listesini göster"""
        self.main_window._show_mysql_databases(self.service, databases)
    
    def _show_mysql_users(self, users):
        """Kullanıcı listesini göster"""
        self.main_window._show_mysql_users(self.service, users)
    
    def _on_mysql_change_password(self):
        """Root password değiştir"""
        self.main_window._on_mysql_change_password(self.service)
