"""
Hosts Editor Dialog

GTK4 dialog for managing /etc/hosts file entries.
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib
import logging

logger = logging.getLogger(__name__)

# Import i18n
try:
    from src.utils.i18n import get_i18n
    _ = get_i18n().get_translator()
except:
    _ = lambda s: s


class HostsEditorDialog(Adw.Window):
    """Dialog for managing hosts file entries"""
    
    def __init__(self, parent, hosts_service):
        super().__init__()
        
        self.parent_window = parent
        self.hosts_service = hosts_service
        
        # Window settings
        self.set_title(_("Hosts File Manager"))
        self.set_default_size(700, 500)
        self.set_modal(True)
        self.set_transient_for(parent)
        
        # Build UI
        self._build_ui()
        
        # Load entries
        self._load_entries()
    
    def _build_ui(self):
        """Build the dialog UI"""
        # Main box
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        # Header bar
        header = Adw.HeaderBar()
        header.set_show_end_title_buttons(True)
        
        # Add button in header
        add_button = Gtk.Button()
        add_button.set_icon_name("list-add-symbolic")
        add_button.set_tooltip_text(_("Add Entry"))
        add_button.connect("clicked", self._on_add_clicked)
        header.pack_start(add_button)
        
        # Backup button
        backup_button = Gtk.Button()
        backup_button.set_icon_name("document-save-symbolic")
        backup_button.set_tooltip_text(_("Backup Hosts File"))
        backup_button.connect("clicked", self._on_backup_clicked)
        header.pack_end(backup_button)
        
        # Restore button
        restore_button = Gtk.Button()
        restore_button.set_icon_name("document-revert-symbolic")
        restore_button.set_tooltip_text(_("Restore Hosts File"))
        restore_button.connect("clicked", self._on_restore_clicked)
        header.pack_end(restore_button)
        
        main_box.append(header)
        
        # Toolbar box with info
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        toolbar.set_margin_top(12)
        toolbar.set_margin_bottom(12)
        toolbar.set_margin_start(12)
        toolbar.set_margin_end(12)
        toolbar.set_spacing(12)
        
        # Info label
        info_label = Gtk.Label()
        info_label.set_markup(
            f"<span size='small'>{_('Manage local domain mappings in /etc/hosts file')}</span>"
        )
        info_label.set_halign(Gtk.Align.START)
        info_label.set_hexpand(True)
        toolbar.append(info_label)
        
        # Entry count
        self.count_label = Gtk.Label()
        self.count_label.set_halign(Gtk.Align.END)
        toolbar.append(self.count_label)
        
        main_box.append(toolbar)
        
        # Scrolled window for list
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_hexpand(True)
        
        # List box
        self.list_box = Gtk.ListBox()
        self.list_box.set_selection_mode(Gtk.SelectionMode.NONE)
        self.list_box.add_css_class("boxed-list")
        self.list_box.set_margin_start(12)
        self.list_box.set_margin_end(12)
        self.list_box.set_margin_bottom(12)
        
        scrolled.set_child(self.list_box)
        main_box.append(scrolled)
        
        # Set content
        self.set_content(main_box)
    
    def _load_entries(self):
        """Load hosts entries from service"""
        # Clear existing entries
        while True:
            child = self.list_box.get_first_child()
            if child is None:
                break
            self.list_box.remove(child)
        
        # Get entries
        entries = self.hosts_service.list_entries()
        
        if not entries:
            # Show empty state
            status_page = Adw.StatusPage()
            status_page.set_title(_("No Entries"))
            status_page.set_description(_("Add your first hosts entry to get started"))
            status_page.set_icon_name("network-server-symbolic")
            self.list_box.append(status_page)
            self.count_label.set_text(_("0 entries"))
            return
        
        # Create row for each entry
        for entry in entries:
            row = self._create_entry_row(entry)
            self.list_box.append(row)
        
        # Update count
        self.count_label.set_text(
            _("{count} entries").format(count=len(entries))
        )
    
    def _create_entry_row(self, entry):
        """Create a row for a hosts entry"""
        row = Gtk.ListBoxRow()
        row.set_activatable(False)
        
        # Box for row content
        row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        row_box.set_spacing(12)
        row_box.set_margin_top(12)
        row_box.set_margin_bottom(12)
        row_box.set_margin_start(12)
        row_box.set_margin_end(12)
        
        # Left side: IP and domain info
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        info_box.set_spacing(4)
        info_box.set_hexpand(True)
        
        # Domain (main text)
        domain_label = Gtk.Label()
        domain_label.set_markup(
            f"<span size='11000' weight='bold'>{entry['domain']}</span>"
        )
        domain_label.set_halign(Gtk.Align.START)
        domain_label.set_ellipsize(3)  # END
        info_box.append(domain_label)
        
        # IP address (subtitle)
        ip_label = Gtk.Label()
        ip_label.set_markup(
            f"<span size='9000' foreground='#666666'>{entry['ip']}</span>"
        )
        ip_label.set_halign(Gtk.Align.START)
        info_box.append(ip_label)
        
        row_box.append(info_box)
        
        # Right side: Delete button
        delete_button = Gtk.Button()
        delete_button.set_icon_name("user-trash-symbolic")
        delete_button.set_tooltip_text(_("Remove Entry"))
        delete_button.add_css_class("destructive-action")
        delete_button.set_valign(Gtk.Align.CENTER)
        delete_button.connect("clicked", self._on_delete_clicked, entry)
        row_box.append(delete_button)
        
        row.set_child(row_box)
        return row
    
    def _on_add_clicked(self, button):
        """Show add entry dialog"""
        dialog = AddHostsEntryDialog(self, self.hosts_service, self._on_entry_modified)
        dialog.present()
    
    def _on_delete_clicked(self, button, entry):
        """Delete hosts entry"""
        # Confirmation dialog
        dialog = Adw.MessageDialog.new(self)
        dialog.set_heading(_("Remove Hosts Entry?"))
        dialog.set_body(
            _("Remove '{domain}' → {ip} from hosts file?").format(
                domain=entry['domain'],
                ip=entry['ip']
            )
        )
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("remove", _("Remove"))
        dialog.set_response_appearance("remove", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_default_response("cancel")
        dialog.set_close_response("cancel")
        
        dialog.connect("response", self._on_delete_response, entry)
        dialog.present()
    
    def _on_delete_response(self, dialog, response, entry):
        """Handle delete confirmation response"""
        if response == "remove":
            # Remove entry
            success, message = self.hosts_service.remove_entry(entry['domain'])
            
            if success:
                self._show_toast(_("Entry removed successfully"))
                self._load_entries()
            else:
                self._show_error_dialog(_("Failed to Remove Entry"), message)
    
    def _on_backup_clicked(self, button):
        """Backup hosts file"""
        success, message = self.hosts_service.backup()
        
        if success:
            self._show_toast(_("Hosts file backed up successfully"))
        else:
            self._show_error_dialog(_("Backup Failed"), message)
    
    def _on_restore_clicked(self, button):
        """Restore hosts file"""
        # Confirmation dialog
        dialog = Adw.MessageDialog.new(self)
        dialog.set_heading(_("Restore Hosts File?"))
        dialog.set_body(_("This will replace the current hosts file with the backup. Continue?"))
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("restore", _("Restore"))
        dialog.set_response_appearance("restore", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_default_response("cancel")
        dialog.set_close_response("cancel")
        
        dialog.connect("response", self._on_restore_response)
        dialog.present()
    
    def _on_restore_response(self, dialog, response):
        """Handle restore confirmation response"""
        if response == "restore":
            success, message = self.hosts_service.restore()
            
            if success:
                self._show_toast(_("Hosts file restored successfully"))
                self._load_entries()
            else:
                self._show_error_dialog(_("Restore Failed"), message)
    
    def _on_entry_modified(self, dialog):
        """Reload entries when modified"""
        self._load_entries()
    
    def _show_toast(self, message):
        """Show toast notification"""
        # Use parent window's toast if available
        if hasattr(self.parent_window, '_show_toast'):
            self.parent_window._show_toast(message)
        else:
            print(f"Toast: {message}")
    
    def _show_error_dialog(self, title, message):
        """Show error dialog"""
        dialog = Adw.MessageDialog.new(self)
        dialog.set_heading(title)
        dialog.set_body(message)
        dialog.add_response("ok", _("OK"))
        dialog.set_default_response("ok")
        dialog.present()


class AddHostsEntryDialog(Adw.Window):
    """Dialog for adding new hosts entry"""
    
    def __init__(self, parent, hosts_service, on_added_callback=None):
        super().__init__()
        
        self.parent_window = parent
        self.hosts_service = hosts_service
        self.on_added_callback = on_added_callback
        
        # Window settings
        self.set_title(_("Add Hosts Entry"))
        self.set_default_size(500, 300)
        self.set_modal(True)
        self.set_transient_for(parent)
        
        # Build UI
        self._build_ui()
    
    def _build_ui(self):
        """Build the dialog UI"""
        # Main box
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        # Header
        header = Adw.HeaderBar()
        main_box.append(header)
        
        # Content
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        content_box.set_margin_top(24)
        content_box.set_margin_bottom(24)
        content_box.set_margin_start(24)
        content_box.set_margin_end(24)
        content_box.set_spacing(18)
        
        # Domain entry
        domain_group = Adw.PreferencesGroup()
        domain_group.set_title(_("Domain Name"))
        domain_group.set_description(_("e.g., example.local or myapp.test"))
        
        domain_row = Adw.EntryRow()
        domain_row.set_title(_("Domain"))
        self.domain_entry = domain_row
        domain_group.add(domain_row)
        
        content_box.append(domain_group)
        
        # IP entry
        ip_group = Adw.PreferencesGroup()
        ip_group.set_title(_("IP Address"))
        ip_group.set_description(_("Usually 127.0.0.1 for local development"))
        
        ip_row = Adw.EntryRow()
        ip_row.set_title(_("IP"))
        ip_row.set_text("127.0.0.1")  # Default
        self.ip_entry = ip_row
        ip_group.add(ip_row)
        
        content_box.append(ip_group)
        
        # Button box
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        button_box.set_spacing(12)
        button_box.set_halign(Gtk.Align.END)
        button_box.set_margin_top(12)
        
        # Cancel button
        cancel_button = Gtk.Button(label=_("Cancel"))
        cancel_button.connect("clicked", lambda b: self.close())
        button_box.append(cancel_button)
        
        # Add button
        add_button = Gtk.Button(label=_("Add"))
        add_button.add_css_class("suggested-action")
        add_button.connect("clicked", self._on_add_clicked)
        button_box.append(add_button)
        
        content_box.append(button_box)
        
        main_box.append(content_box)
        self.set_content(main_box)
    
    def _on_add_clicked(self, button):
        """Add the hosts entry"""
        domain = self.domain_entry.get_text().strip()
        ip = self.ip_entry.get_text().strip()
        
        # Validate
        if not domain:
            self._show_error(_("Domain is required"))
            return
        
        if not ip:
            self._show_error(_("IP is required"))
            return
        
        # Validate IP
        if not self.hosts_service.validate_ip(ip):
            self._show_error(_("Invalid IP address format"))
            return
        
        # Add entry
        success, message = self.hosts_service.add_entry(ip, domain)
        
        if success:
            if self.on_added_callback:
                self.on_added_callback(self)
            self.close()
        else:
            self._show_error(message)
    
    def _show_error(self, message):
        """Show error dialog"""
        dialog = Adw.MessageDialog.new(self)
        dialog.set_heading(_("Error"))
        dialog.set_body(message)
        dialog.add_response("ok", _("OK"))
        dialog.set_default_response("ok")
        dialog.present()
