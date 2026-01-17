"""
System Hosts Service - UI Module

Hosts file (/etc/hosts) yönetimi için UI
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


class SystemHostsView(BaseServiceView):
    """
    System Hosts Service UI
    
    /etc/hosts dosyasındaki domain → IP mapping'leri yönetir
    """
    
    def create_view(self) -> Gtk.Widget:
        """
        Hosts Manager için özel view - Status ve Actions olmadan
        Sadece dosya editörü
        """
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_hexpand(True)
        
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.main_box.set_spacing(24)
        self.main_box.set_margin_top(24)
        self.main_box.set_margin_bottom(24)
        self.main_box.set_margin_start(24)
        self.main_box.set_margin_end(24)
        
        # Sadece başlık
        header_group = Adw.PreferencesGroup()
        header_group.set_title(self.service.display_name)
        header_group.set_description(self.service.description)
        self.main_box.append(header_group)
        
        # Hosts'a özel bölümler
        self._add_custom_sections()
        
        scrolled.set_child(self.main_box)
        return scrolled
    
    def _add_custom_sections(self):
        """Hosts'a özel bölümler"""
        self._add_hosts_entries_section()
        self._add_backup_section()
    
    def _add_hosts_entries_section(self):
        """Hosts entry listesi ve ekleme"""
        # Hosts entries list
        entries_group = Adw.PreferencesGroup()
        entries_group.set_title(_("Hosts Entries"))
        entries_group.set_description(_("Manage local domain mappings in /etc/hosts file"))
        
        # Add entry button
        add_row = Adw.ActionRow()
        add_row.set_title(_("Add New Entry"))
        add_row.set_subtitle(_("Add a new domain → IP mapping"))
        add_row.set_activatable(True)
        add_button = Gtk.Button()
        add_button.set_icon_name("list-add-symbolic")
        add_button.set_valign(Gtk.Align.CENTER)
        add_button.add_css_class("flat")
        add_row.add_suffix(add_button)
        add_row.connect("activated", lambda r: self._on_hosts_add_entry())
        entries_group.add(add_row)
        
        self.main_box.append(entries_group)
        
        # Current entries
        entries = self.service.list_entries()
        
        if entries:
            current_group = Adw.PreferencesGroup()
            current_group.set_title(_("Current Entries ({count})").format(count=len(entries)))
            
            for entry in entries:
                entry_row = Adw.ActionRow()
                entry_row.set_title(entry['domain'])
                
                # IP adresi + yönetim durumu
                subtitle_parts = [entry['ip']]
                if entry.get('managed', False):
                    subtitle_parts.append("🔧 Managed by Orkesta")
                else:
                    subtitle_parts.append("ℹ️ System/Other")
                entry_row.set_subtitle(" • ".join(subtitle_parts))
                
                # Sadece Orkesta'nın eklediğini silebiliriz
                if entry.get('managed', False):
                    delete_button = Gtk.Button()
                    delete_button.set_icon_name("user-trash-symbolic")
                    delete_button.set_valign(Gtk.Align.CENTER)
                    delete_button.add_css_class("destructive-action")
                    delete_button.connect("clicked", lambda b, e=entry: self._on_hosts_delete_entry(e))
                    entry_row.add_suffix(delete_button)
                else:
                    # Sistem entry'leri için info ikonu
                    info_icon = Gtk.Image.new_from_icon_name("dialog-information-symbolic")
                    info_icon.set_valign(Gtk.Align.CENTER)
                    info_icon.set_tooltip_text(_("System entry - cannot be deleted"))
                    entry_row.add_suffix(info_icon)
                
                current_group.add(entry_row)
            
            self.main_box.append(current_group)
        else:
            # Empty state
            empty_group = Adw.PreferencesGroup()
            empty_label = Gtk.Label()
            empty_label.set_markup(f"<span foreground='#666666'>{_('No hosts entries yet. Add your first entry to get started.')}</span>")
            empty_label.set_margin_top(12)
            empty_label.set_margin_bottom(12)
            empty_group.add(empty_label)
            self.main_box.append(empty_group)
    
    def _add_backup_section(self):
        """Backup/Restore bölümü"""
        backup_group = Adw.PreferencesGroup()
        backup_group.set_title(_("Backup and Restore"))
        
        # Backup button
        backup_row = Adw.ActionRow()
        backup_row.set_title(_("Backup Hosts File"))
        backup_row.set_subtitle(_("Create a backup of /etc/hosts"))
        backup_row.set_activatable(True)
        backup_row.connect("activated", lambda r: self._on_hosts_backup())
        backup_group.add(backup_row)
        
        # Restore button
        restore_row = Adw.ActionRow()
        restore_row.set_title(_("Restore Hosts File"))
        restore_row.set_subtitle(_("Restore from backup"))
        restore_row.set_activatable(True)
        restore_row.connect("activated", lambda r: self._on_hosts_restore())
        backup_group.add(restore_row)
        
        self.main_box.append(backup_group)
    
    # ============================================
    # EVENT HANDLERS
    # ============================================
    
    def _on_hosts_add_entry(self):
        """Show add hosts entry dialog"""
        self.main_window._on_hosts_add_entry(self.service)
    
    def _on_hosts_delete_entry(self, entry):
        """Delete hosts entry"""
        self.main_window._on_hosts_delete_entry(self.service, entry)
    
    def _on_hosts_backup(self):
        """Backup hosts file"""
        self.main_window._on_hosts_backup(self.service)
    
    def _on_hosts_restore(self):
        """Restore hosts file"""
        self.main_window._on_hosts_restore(self.service)
