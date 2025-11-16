"""
Ana Pencere - Main Window

GTK4/Libadwaita tabanlı ana uygulama penceresi.
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gio
import logging
import os
import subprocess
from src.utils.i18n import get_i18n

logger = logging.getLogger(__name__)

# Çeviri fonksiyonu
_ = get_i18n().get_translator()


class MainWindow(Adw.ApplicationWindow):
    """Ana uygulama penceresi"""
    
    def __init__(self, application, platform_manager, service_loader):
        super().__init__(application=application)
        
        self.platform_manager = platform_manager
        self.service_loader = service_loader
        
        # Progress dialog değişkenleri
        self.progress_dialog = None
        self.progress_bar = None
        self.progress_label = None
        self.progress_timeout_id = None
        
        # Navigation state
        self.current_service = None
        self.main_stack = None
        
        # Pencere ayarları
        self.set_title("Orkesta")
        self.set_default_size(1000, 700)
        
        # CSS yükle
        self._load_css()
        
        # UI oluştur
        self._build_ui()
        
        # Servisleri yükle
        self._load_services()
    
    def _load_css(self):
        """Custom CSS yükle"""
        css_provider = Gtk.CssProvider()
        
        # CSS'i ekle
        Gtk.StyleContext.add_provider_for_display(
            self.get_display(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
    
    def _build_ui(self):
        """Ana UI'ı oluştur"""
        # Ana Box
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        # Header Bar
        self.header = Adw.HeaderBar()
        self.header.set_title_widget(Adw.WindowTitle(title="Orkesta", subtitle="Web Development Manager"))
        
        # Back button (başlangıçta gizli)
        self.back_button = Gtk.Button()
        self.back_button.set_icon_name("go-previous-symbolic")
        self.back_button.set_visible(False)
        self.back_button.connect("clicked", self._on_back_clicked)
        self.header.pack_start(self.back_button)
        
        # Menü butonu
        menu_button = Gtk.MenuButton()
        menu_button.set_icon_name("open-menu-symbolic")
        self.header.pack_end(menu_button)
        
        main_box.append(self.header)
        
        # Stack for navigation (list <-> detail)
        self.main_stack = Gtk.Stack()
        self.main_stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        
        # Split View (Sidebar + Content)
        split_view = Adw.OverlaySplitView()
        split_view.set_sidebar_position(Gtk.PackType.START)
        split_view.set_max_sidebar_width(400)
        split_view.set_min_sidebar_width(320)
        
        # Sidebar
        sidebar = self._create_sidebar()
        split_view.set_sidebar(sidebar)
        
        # Content Area (Service List)
        self.service_list_page = self._create_service_list_page()
        split_view.set_content(self.service_list_page)
        
        self.main_stack.add_named(split_view, "list")
        
        # Detail page will be created when needed
        
        main_box.append(self.main_stack)
        
        # Ana box'ı window'a ekle
        self.set_content(main_box)
    
    def _create_sidebar(self):
        """Sidebar oluştur"""
        sidebar_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        sidebar_box.add_css_class("sidebar")
        sidebar_box.set_margin_top(12)
        sidebar_box.set_margin_bottom(12)
        sidebar_box.set_margin_start(12)
        sidebar_box.set_margin_end(12)
        sidebar_box.set_spacing(20)
        
        system_info = self.platform_manager.get_system_info_dict()
        
        # Sistem bilgileri başlık
        system_title = Gtk.Label()
        system_title.set_markup(f"<span size='10500' weight='bold'>{_('SYSTEM INFORMATION')}</span>")
        system_title.set_halign(Gtk.Align.START)
        system_title.set_margin_bottom(8)
        sidebar_box.append(system_title)
        
        # Sistem bilgileri listesi
        system_list = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        system_list.set_spacing(2)
        
        # OS bilgisi
        os_box = self._create_info_row(_("💻 Operating System"), system_info['os_name'])
        system_list.append(os_box)
        
        # Versiyon
        version_box = self._create_info_row(_("📦 Version"), system_info['os_version'])
        system_list.append(version_box)
        
        # Dağıtım
        distro_box = self._create_info_row(_("🐧 Distribution"), system_info['os_type'].title())
        system_list.append(distro_box)
        
        # Kernel
        kernel_box = self._create_info_row(_("⚙️ Kernel"), system_info['kernel_version'])
        system_list.append(kernel_box)
        
        # Mimari
        arch_box = self._create_info_row(_("🔧 Architecture"), system_info['architecture'])
        system_list.append(arch_box)
        
        # Paket yöneticisi
        pm_box = self._create_info_row(_("📥 Package Manager"), system_info['package_manager'].upper())
        system_list.append(pm_box)
        
        # IP adresi
        ip_address = self._get_local_ip()
        ip_box = self._create_info_row(_("🌐 IP Address"), ip_address)
        system_list.append(ip_box)
        
        # Hostname
        hostname = self._get_hostname()
        hostname_box = self._create_info_row(_("🖥️ Hostname"), hostname)
        system_list.append(hostname_box)
        
        # Python version
        import sys
        python_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        python_box = self._create_info_row(_("🐍 Python"), python_ver)
        system_list.append(python_box)
        
        sidebar_box.append(system_list)
        
        # Separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        separator.set_margin_top(8)
        separator.set_margin_bottom(8)
        sidebar_box.append(separator)
        
        # İstatistikler başlık
        stats_title = Gtk.Label()
        stats_title.set_markup(f"<span size='10500' weight='bold'>{_('STATISTICS')}</span>")
        stats_title.set_halign(Gtk.Align.START)
        stats_title.set_margin_bottom(8)
        sidebar_box.append(stats_title)
        
        # İstatistikler listesi
        stats = self.service_loader.get_service_count()
        stats_list = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        stats_list.set_spacing(2)
        
        # Toplam servis
        total_box = self._create_info_row(_("📊 Total Services"), str(stats['total']))
        stats_list.append(total_box)
        
        # Kurulu servis
        installed_box = self._create_info_row(_("✅ Installed"), str(stats['installed']))
        stats_list.append(installed_box)
        
        # Çalışan servis
        running_box = self._create_info_row(_("🟢 Running"), str(stats['running']))
        stats_list.append(running_box)
        
        sidebar_box.append(stats_list)
        
        return sidebar_box
    
    def _create_info_row(self, label_text, value_text):
        """Bilgi satırı oluştur - tablo görünümü"""
        row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        row_box.set_spacing(12)
        row_box.set_margin_top(4)
        row_box.set_margin_bottom(4)
        
        # Label (sol taraf, sabit genişlik)
        label = Gtk.Label()
        label.set_halign(Gtk.Align.START)
        label.set_hexpand(False)
        label.set_width_chars(18)
        label.set_xalign(0)
        label.set_markup(f"<span size='9000'>{label_text}</span>")
        row_box.append(label)
        
        # Value (sağ taraf, bold)
        value = Gtk.Label()
        value.set_halign(Gtk.Align.START)
        value.set_hexpand(True)
        value.set_xalign(0)
        value.set_ellipsize(3)  # ELLIPSIZE_END
        value.set_selectable(True)  # Kopyalanabilir
        value.set_markup(f"<span size='9000' weight='700'>{value_text}</span>")
        row_box.append(value)
        
        return row_box
    
    def _get_local_ip(self):
        """Yerel IP adresini al"""
        try:
            import socket
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "N/A"
    
    def _get_hostname(self):
        """Hostname al"""
        try:
            import socket
            return socket.gethostname()
        except Exception:
            return "N/A"
    
    def _create_service_list_page(self):
        """Servis listesi sayfası oluştur"""
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        # Toolbar
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        toolbar.add_css_class("toolbar")
        toolbar.set_margin_top(12)
        toolbar.set_margin_bottom(12)
        toolbar.set_margin_start(12)
        toolbar.set_margin_end(12)
        toolbar.set_spacing(12)
        
        # Başlık
        title_label = Gtk.Label()
        title_label.set_markup(f"<span size='large' weight='bold'>{_('Services')}</span>")
        title_label.set_halign(Gtk.Align.START)
        title_label.set_hexpand(True)
        toolbar.append(title_label)
        
        # Yenile butonu
        refresh_button = Gtk.Button()
        refresh_button.set_icon_name("view-refresh-symbolic")
        refresh_button.set_tooltip_text(_("Refresh"))
        refresh_button.connect("clicked", self._on_refresh_clicked)
        toolbar.append(refresh_button)
        
        content_box.append(toolbar)
        
        # Scrolled window
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_hexpand(True)
        
        # Servis listesi (ListBox kullanarak)
        self.service_list_box = Gtk.ListBox()
        self.service_list_box.set_selection_mode(Gtk.SelectionMode.NONE)
        self.service_list_box.add_css_class("boxed-list")
        self.service_list_box.set_margin_start(12)
        self.service_list_box.set_margin_end(12)
        self.service_list_box.set_margin_bottom(12)
        self.service_list_box.connect("row-activated", self._on_service_row_activated)
        
        scrolled.set_child(self.service_list_box)
        content_box.append(scrolled)
        
        return content_box
    
    def _load_services(self):
        """Servisleri yükle ve göster"""
        # Mevcut servisleri temizle
        while True:
            child = self.service_list_box.get_first_child()
            if child is None:
                break
            self.service_list_box.remove(child)
        
        # Servisleri al
        services = self.service_loader.get_all_services()
        
        if not services:
            # Servis yoksa bilgi göster
            status_page = Adw.StatusPage()
            status_page.set_title(_("No Services"))
            status_page.set_description(_("Add service modules to services/ directory"))
            status_page.set_icon_name("folder-symbolic")
            self.service_list_box.append(status_page)
            return
        
        # Her servis için row oluştur
        for service in services:
            service_row = self._create_service_row(service)
            self.service_list_box.append(service_row)
    
    def _create_service_row(self, service):
        """Modern servis kartı oluştur"""
        # Ana container
        row = Gtk.ListBoxRow()
        row.set_activatable(True)
        # Service'i row'a veri olarak ekle
        row.service = service
        
        # Box içeriği
        card_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        card_box.set_spacing(16)
        card_box.set_margin_top(12)
        card_box.set_margin_bottom(12)
        card_box.set_margin_start(16)
        card_box.set_margin_end(16)
        
        # Sol taraf: Icon + Bilgiler
        left_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        left_box.set_spacing(12)
        left_box.set_hexpand(True)
        
        # İkon (büyük)
        icon = Gtk.Image.new_from_icon_name(service.icon_name)
        icon.set_pixel_size(40)
        left_box.append(icon)
        
        # Bilgi box
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        info_box.set_valign(Gtk.Align.CENTER)
        info_box.set_spacing(4)
        
        # Başlık
        title = Gtk.Label(label=service.display_name)
        title.set_halign(Gtk.Align.START)
        title.set_markup(f"<span size='11000' weight='bold'>{service.display_name}</span>")
        info_box.append(title)
        
        # Alt bilgi satırı
        status = service.get_status().value
        subtitle_parts = []
        
        # Status
        if status == "running":
            subtitle_parts.append("<span foreground='#26a269'>● Running</span>")
        elif status == "stopped":
            subtitle_parts.append("<span foreground='#c01c28'>● Stopped</span>")
        elif status == "not_installed":
            subtitle_parts.append("<span foreground='#9a9996'>● Not Installed</span>")
        else:
            subtitle_parts.append("<span foreground='#9a9996'>● Unknown</span>")
        
        # Port
        if service.default_port:
            subtitle_parts.append(f"Port {service.default_port}")
        
        # Type
        type_name = service.service_type.value.replace('_', ' ').title()
        subtitle_parts.append(type_name)
        
        subtitle = Gtk.Label()
        subtitle.set_halign(Gtk.Align.START)
        subtitle.set_markup(f"<span size='9000'>{' • '.join(subtitle_parts)}</span>")
        info_box.append(subtitle)
        
        left_box.append(info_box)
        card_box.append(left_box)
        
        # Sağ taraf: Ok ikonu
        arrow = Gtk.Image.new_from_icon_name("go-next-symbolic")
        arrow.set_valign(Gtk.Align.CENTER)
        card_box.append(arrow)
        
        row.set_child(card_box)
        return row
    
    def _on_service_install(self, service):
        """Install service"""
        # Onay dialog'u göster
        dialog = Adw.MessageDialog.new(self)
        dialog.set_heading(_("Install {service}?").format(service=service.display_name))
        dialog.set_body(_("A terminal window will open. Please enter your password when prompted.").format(service=service.display_name))
        
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("install", _("Install"))
        dialog.set_response_appearance("install", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_default_response("install")
        dialog.set_close_response("cancel")
        
        def on_response(dialog, response):
            if response == "install":
                # Script yolunu bul
                script_path = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                    'scripts',
                    f'{service.name}.sh'
                )
                
                # Terminal komutları
                terminal_commands = [
                    ['gnome-terminal', '--', 'bash', '-c', 
                     f'echo "Installing {service.display_name}..."; echo ""; sudo bash "{script_path}" install; echo ""; echo "Press Enter to close..."; read'],
                    ['xterm', '-e', 
                     f'bash -c "echo \\"Installing {service.display_name}...\\"; echo \\"\\"; sudo bash \\"{script_path}\\" install; echo \\"\\"; echo \\"Press Enter to close...\\"; read"'],
                    ['konsole', '-e', 
                     f'bash -c "echo \\"Installing {service.display_name}...\\"; echo \\"\\"; sudo bash \\"{script_path}\\" install; echo \\"\\"; echo \\"Press Enter to close...\\"; read"'],
                ]
                
                success = False
                for cmd in terminal_commands:
                    try:
                        subprocess.Popen(cmd)
                        success = True
                        self._show_toast(_("Terminal opened. Please complete installation there."))
                        # Servisleri yenile (3 saniye sonra)
                        GLib.timeout_add_seconds(3, self._load_services)
                        break
                    except:
                        continue
                
                if not success:
                    self._show_toast(_("Could not open terminal. Install manually: sudo bash {script} install").format(script=script_path))
        
        dialog.connect("response", on_response)
        dialog.present()
    
    def _on_service_uninstall(self, service):
        """Uninstall service"""
        # Onay dialog'u göster
        dialog = Adw.MessageDialog.new(self)
        dialog.set_heading(_("Uninstall {service}?").format(service=service.display_name))
        dialog.set_body(_("A terminal window will open. Please enter your password when prompted.").format(service=service.display_name))
        
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("uninstall", _("Uninstall"))
        dialog.set_response_appearance("uninstall", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_default_response("cancel")
        dialog.set_close_response("cancel")
        
        def on_response(dialog, response):
            if response == "uninstall":
                # Script yolunu bul
                script_path = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                    'scripts',
                    f'{service.name}.sh'
                )
                
                # Terminal komutları
                terminal_commands = [
                    ['gnome-terminal', '--', 'bash', '-c', 
                     f'echo "Uninstalling {service.display_name}..."; echo ""; sudo bash "{script_path}" uninstall; echo ""; echo "Press Enter to close..."; read'],
                    ['xterm', '-e', 
                     f'bash -c "echo \\"Uninstalling {service.display_name}...\\"; echo \\"\\"; sudo bash \\"{script_path}\\" uninstall; echo \\"\\"; echo \\"Press Enter to close...\\"; read"'],
                    ['konsole', '-e', 
                     f'bash -c "echo \\"Uninstalling {service.display_name}...\\"; echo \\"\\"; sudo bash \\"{script_path}\\" uninstall; echo \\"\\"; echo \\"Press Enter to close...\\"; read"'],
                ]
                
                success = False
                for cmd in terminal_commands:
                    try:
                        subprocess.Popen(cmd)
                        success = True
                        self._show_toast(_("Terminal opened. Please complete uninstallation there."))
                        # Servisleri yenile (3 saniye sonra)
                        GLib.timeout_add_seconds(3, self._load_services)
                        break
                    except:
                        continue
                
                if not success:
                    self._show_toast(_("Could not open terminal. Uninstall manually: sudo bash {script} uninstall").format(script=script_path))
        
        dialog.connect("response", on_response)
        dialog.present()
    
    def _on_service_start(self, service):
        """Start service"""
        success, message = service.start()
        self._show_toast(message)
        self._load_services()
        # Detay sayfasındaysak yenile
        if self.current_service and self.current_service.name == service.name:
            self._refresh_detail_page()
    
    def _on_service_stop(self, service):
        """Stop service"""
        success, message = service.stop()
        self._show_toast(message)
        self._load_services()
        # Detay sayfasındaysak yenile
        if self.current_service and self.current_service.name == service.name:
            self._refresh_detail_page()
    
    def _on_service_restart(self, service):
        """Restart service"""
        success, message = service.restart()
        self._show_toast(message)
        self._load_services()
        # Detay sayfasındaysak yenile
        if self.current_service and self.current_service.name == service.name:
            self._refresh_detail_page()
    
    def _show_loading_dialog(self, message):
        """Show loading dialog with progress"""
        # Dialog oluştur
        self.progress_dialog = Adw.MessageDialog.new(self)
        self.progress_dialog.set_heading(_("Please Wait"))
        self.progress_dialog.set_body(message)
        
        # Cancel butonu ekle
        self.progress_dialog.add_response("cancel", _("Cancel"))
        self.progress_dialog.set_response_appearance("cancel", Adw.ResponseAppearance.DESTRUCTIVE)
        
        # Cancel handler
        def on_cancel(dialog, response):
            if response == "cancel":
                logger.info("User cancelled operation")
                self._on_operation_complete(False, _("Operation cancelled by user"))
        
        self.progress_dialog.connect("response", on_cancel)
        
        # Progress bar ekle
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        content_box.set_spacing(12)
        content_box.set_margin_top(12)
        content_box.set_margin_bottom(12)
        content_box.set_margin_start(12)
        content_box.set_margin_end(12)
        
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_show_text(True)
        self.progress_bar.set_text(_("Working..."))
        self.progress_bar.pulse()
        content_box.append(self.progress_bar)
        
        # Status label
        self.progress_label = Gtk.Label()
        self.progress_label.set_wrap(True)
        self.progress_label.set_xalign(0)
        self.progress_label.add_css_class("dim-label")
        self.progress_label.set_text(_("This may take a few minutes..."))
        content_box.append(self.progress_label)
        
        self.progress_dialog.set_extra_child(content_box)
        
        # Progress animation başlat
        self.progress_timeout_id = None
        def pulse_progress():
            if hasattr(self, 'progress_dialog') and self.progress_dialog and hasattr(self, 'progress_bar') and self.progress_bar:
                self.progress_bar.pulse()
                return True
            return False
        
        self.progress_timeout_id = GLib.timeout_add(100, pulse_progress)
        
        self.progress_dialog.present()
        logger.info(f"Loading: {message}")
    
    def _on_operation_complete(self, success, message):
        """Operation completed"""
        try:
            # Progress animation'ı durdur
            if hasattr(self, 'progress_timeout_id') and self.progress_timeout_id:
                try:
                    GLib.source_remove(self.progress_timeout_id)
                except:
                    pass
                self.progress_timeout_id = None
            
            # Progress bar referansını temizle
            if hasattr(self, 'progress_bar'):
                self.progress_bar = None
            
            # Progress label referansını temizle
            if hasattr(self, 'progress_label'):
                self.progress_label = None
            
            # Dialog'u kapat
            if hasattr(self, 'progress_dialog') and self.progress_dialog:
                try:
                    self.progress_dialog.close()
                except:
                    pass
                self.progress_dialog = None
            
            # Toast göster
            self._show_toast(message)
            
            # Hata mesajı varsa göster
            if not success and message:
                error_dialog = Adw.MessageDialog.new(self)
                error_dialog.set_heading(_("Operation Failed"))
                error_dialog.set_body(message)
                error_dialog.add_response("ok", _("OK"))
                error_dialog.set_default_response("ok")
                error_dialog.present()
            
            # Servisleri yeniden yükle
            try:
                self._load_services()
                # Detay sayfasındaysak yenile
                if self.current_service:
                    self._refresh_detail_page()
            except Exception as e:
                logger.error(f"Error reloading services: {e}")
        
        except Exception as e:
            logger.error(f"Error in _on_operation_complete: {e}")
            import traceback
            traceback.print_exc()
        
        return False
    
    def _show_toast(self, message):
        """Toast mesajı göster"""
        # TODO: Implement toast (Adw.Toast requires overlay)
        logger.info(f"Toast: {message}")
        print(f"📢 {message}")
    
    def _show_sudo_password_dialog(self, callback):
        """Show sudo password dialog"""
        dialog = Adw.MessageDialog.new(self, _("Authentication Required"), None)
        dialog.set_body(_("Please enter your password to continue"))
        
        # Password entry
        password_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        password_box.set_spacing(8)
        password_box.set_margin_top(12)
        
        password_entry = Gtk.PasswordEntry()
        password_entry.set_property("placeholder-text", _("Password"))
        password_entry.set_show_peek_icon(True)
        password_box.append(password_entry)
        
        dialog.set_extra_child(password_box)
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("ok", _("OK"))
        dialog.set_response_appearance("ok", Adw.ResponseAppearance.SUGGESTED)
        
        def on_response(dialog, response):
            if response == "ok":
                password = password_entry.get_text()
                if password:
                    callback(password)
                else:
                    self._show_toast(_("Password cannot be empty"))
        
        dialog.connect("response", on_response)
        dialog.present()
    
    # ==================== NAVIGATION ====================
    
    def _on_service_row_activated(self, listbox, row):
        """Service row activated - show detail"""
        if hasattr(row, 'service'):
            self._show_service_detail(row.service)
    
    def _on_back_clicked(self, button):
        """Back button clicked - return to service list"""
        self.main_stack.set_visible_child_name("list")
        self.back_button.set_visible(False)
        self.current_service = None
        # Servisleri yenile
        self._load_services()
    
    def _show_service_detail(self, service):
        """Show service detail page"""
        self.current_service = service
        
        # MySQL için özel durum - sudo şifresi gerekli olup olmadığını kontrol et
        if service.name == 'mysql' and service.is_installed() and service.is_running():
            try:
                # Saved password var mı kontrol et
                saved_password = service._get_saved_root_password()
                if not saved_password:
                    # Sudo gerekli, şifre iste
                    def on_password_provided(password):
                        # Şifreyi geçici olarak environment'a kaydet
                        import os
                        
                        # SUDO_ASKPASS script oluştur
                        temp_script = f"/tmp/orkesta_sudo_{os.getpid()}.sh"
                        try:
                            with open(temp_script, 'w') as f:
                                f.write(f'#!/bin/bash\necho "{password}"\n')
                            os.chmod(temp_script, 0o700)
                            
                            # Environment'ı geçici olarak değiştir
                            old_askpass = os.environ.get('SUDO_ASKPASS')
                            os.environ['SUDO_ASKPASS'] = temp_script
                            
                            # Normal detay sayfası akışını çağır
                            self._create_and_show_detail_page_normal(service)
                            
                        finally:
                            # Cleanup
                            if old_askpass:
                                os.environ['SUDO_ASKPASS'] = old_askpass
                            elif 'SUDO_ASKPASS' in os.environ:
                                del os.environ['SUDO_ASKPASS']
                            try:
                                os.remove(temp_script)
                            except:
                                pass
                    
                    self._show_sudo_password_dialog(on_password_provided)
                    return
            except Exception as e:
                logger.error(f"Error checking MySQL auth: {e}")
        
        # Normal detay sayfası oluştur
        self._create_and_show_detail_page_normal(service)
    
    def _create_and_show_detail_page_normal(self, service):
        """Normal detail page creation"""
        # Detay sayfası oluştur
        detail_page = self._create_service_detail_page(service)
        
        # Eski detay sayfasını kaldır (varsa) - basit yöntem
        try:
            old_detail = self.main_stack.get_child_by_name("detail")
            if old_detail:
                self.main_stack.remove(old_detail)
        except:
            # GTK API farklılığında sessizce devam et
            pass
        
        # Yeni detay sayfasını ekle
        try:
            self.main_stack.add_named(detail_page, "detail")
            self.main_stack.set_visible_child_name("detail")
        except:
            # Fallback - direkt göster
            self.main_stack.set_visible_child(detail_page)
        
        self.back_button.set_visible(True)
    
    def _refresh_detail_page(self):
        """Refresh the current detail page"""
        if self.current_service:
            # Detay sayfasını yeniden oluştur
            detail_page = self._create_service_detail_page(self.current_service)
            
            # Eski detay sayfasını kaldır
            old_detail = self.main_stack.get_child_by_name("detail")
            if old_detail:
                self.main_stack.remove(old_detail)
            
            # Yeni detay sayfasını ekle
            self.main_stack.add_named(detail_page, "detail")
            
            # Detay sayfasını göster (zaten gösteriliyorsa değişmez)
            self.main_stack.set_visible_child_name("detail")
    
    def _create_service_detail_page(self, service):
        """Create service detail page"""
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_hexpand(True)
        
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        main_box.set_spacing(24)
        main_box.set_margin_top(24)
        main_box.set_margin_bottom(24)
        main_box.set_margin_start(24)
        main_box.set_margin_end(24)
        
        # Header section
        header_group = Adw.PreferencesGroup()
        header_group.set_title(service.display_name)
        header_group.set_description(service.description)
        
        # Status row
        status = service.get_status().value
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
        
        # Port row
        if service.default_port:
            port_row = Adw.ActionRow()
            port_row.set_title(_("Port"))
            port_label = Gtk.Label(label=str(service.default_port))
            port_label.add_css_class("monospace")
            port_row.add_suffix(port_label)
            header_group.add(port_row)
        
        # Type row
        type_row = Adw.ActionRow()
        type_row.set_title(_("Type"))
        type_label = Gtk.Label(label=service.service_type.value.replace('_', ' ').title())
        type_row.add_suffix(type_label)
        header_group.add(type_row)
        
        main_box.append(header_group)
        
        # Actions section
        actions_group = Adw.PreferencesGroup()
        actions_group.set_title(_("Actions"))
        
        if service.is_installed():
            # Service control buttons
            if service.is_running():
                # Stop button
                stop_row = Adw.ActionRow()
                stop_row.set_title(_("Stop Service"))
                stop_row.set_subtitle(_("Stop the running service"))
                stop_row.set_activatable(True)
                stop_row.connect("activated", lambda r: self._on_service_stop(service))
                stop_icon = Gtk.Image.new_from_icon_name("media-playback-stop-symbolic")
                stop_row.add_prefix(stop_icon)
                actions_group.add(stop_row)
                
                # Restart button
                restart_row = Adw.ActionRow()
                restart_row.set_title(_("Restart Service"))
                restart_row.set_subtitle(_("Restart the service"))
                restart_row.set_activatable(True)
                restart_row.connect("activated", lambda r: self._on_service_restart(service))
                restart_icon = Gtk.Image.new_from_icon_name("view-refresh-symbolic")
                restart_row.add_prefix(restart_icon)
                actions_group.add(restart_row)
            else:
                # Start button
                start_row = Adw.ActionRow()
                start_row.set_title(_("Start Service"))
                start_row.set_subtitle(_("Start the service"))
                start_row.set_activatable(True)
                start_row.connect("activated", lambda r: self._on_service_start(service))
                start_icon = Gtk.Image.new_from_icon_name("media-playback-start-symbolic")
                start_row.add_prefix(start_icon)
                actions_group.add(start_row)
            
            # Uninstall button
            uninstall_row = Adw.ActionRow()
            uninstall_row.set_title(_("Uninstall"))
            uninstall_row.set_subtitle(_("Remove this service from your system"))
            uninstall_row.set_activatable(True)
            uninstall_row.connect("activated", lambda r: self._on_service_uninstall(service))
            uninstall_icon = Gtk.Image.new_from_icon_name("user-trash-symbolic")
            uninstall_row.add_prefix(uninstall_icon)
            actions_group.add(uninstall_row)
        else:
            # Install button
            install_row = Adw.ActionRow()
            install_row.set_title(_("Install"))
            install_row.set_subtitle(_("Install this service and its dependencies"))
            install_row.set_activatable(True)
            install_row.connect("activated", lambda r: self._on_service_install(service))
            install_icon = Gtk.Image.new_from_icon_name("document-save-symbolic")
            install_row.add_prefix(install_icon)
            actions_group.add(install_row)
        
        main_box.append(actions_group)
        
        # Apache specific sections
        if service.name == "apache" and service.is_installed():
            self._add_apache_sections(main_box, service)
        
        # MySQL specific sections
        if service.name == "mysql" and service.is_installed():
            self._add_mysql_sections(main_box, service)
        
        # PHP specific sections
        if service.name == "php" and service.is_installed():
            self._add_php_sections(main_box, service)
        
        # Configuration section (placeholder)
        config_group = Adw.PreferencesGroup()
        config_group.set_title(_("Configuration"))
        config_group.set_description(_("Configuration options coming soon"))
        main_box.append(config_group)
        
        # Logs section (placeholder)
        logs_group = Adw.PreferencesGroup()
        logs_group.set_title(_("Logs"))
        logs_group.set_description(_("Log viewer coming soon"))
        main_box.append(logs_group)
        
        scrolled.set_child(main_box)
        return scrolled
    
    def _add_mysql_sections(self, main_box, service):
        """Add MySQL-specific sections to detail page"""
        
        # MySQL Status Information
        mysql_info_group = Adw.PreferencesGroup()
        mysql_info_group.set_title(_("MySQL Status"))
        
        try:
            # Get MySQL info (sudo available from startup)
            mysql_info = service.get_mysql_status_info()
            
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
            db_count_row.connect("activated", lambda r: self._show_mysql_databases(service, mysql_info.get('databases', [])))
            mysql_info_group.add(db_count_row)
            
            # Users count (clickable to show list)  
            users_count_row = Adw.ActionRow()
            users_count_row.set_title(_("Users"))
            users_count_row.set_subtitle(_("Click to view user list"))
            users_count_label = Gtk.Label(label=str(mysql_info.get('users_count', 0)))
            users_count_label.add_css_class("monospace")
            users_count_row.add_suffix(users_count_label)
            users_count_row.set_activatable(True)
            users_count_row.connect("activated", lambda r: self._show_mysql_users(service, mysql_info.get('users', [])))
            mysql_info_group.add(users_count_row)
            
        except Exception as e:
            logger.error(f"Error getting MySQL info: {e}")
            error_row = Adw.ActionRow()
            error_row.set_title(_("Status"))
            error_label = Gtk.Label(label="❌ Error loading info")
            error_label.add_css_class("error")
            error_row.add_suffix(error_label)
            mysql_info_group.add(error_row)
        
        main_box.append(mysql_info_group)
        
        # MySQL Management Actions
        mysql_management_group = Adw.PreferencesGroup()
        mysql_management_group.set_title(_("MySQL Management"))
        
        # Change Root Password
        password_row = Adw.ActionRow()
        password_row.set_title(_("Change Root Password"))
        password_row.set_subtitle(_("Set or change MySQL root password"))
        password_row.set_activatable(True)
        password_row.connect("activated", lambda r: self._on_mysql_change_password(service))
        password_icon = Gtk.Image.new_from_icon_name("dialog-password-symbolic")
        password_row.add_prefix(password_icon)
        mysql_management_group.add(password_row)
        
        main_box.append(mysql_management_group)
    

    
    def _show_mysql_detailed_info(self, mysql_info_group, mysql_info, service):
        """Show detailed MySQL information"""
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
        
        # Database count (clickable to show list)
        db_count_row = Adw.ActionRow()
        db_count_row.set_title(_("Databases"))
        db_count_row.set_subtitle(_("Click to view database list"))
        db_count_label = Gtk.Label(label=str(mysql_info.get('databases_count', 0)))
        db_count_label.add_css_class("monospace")
        db_count_row.add_suffix(db_count_label)
        db_count_row.set_activatable(True)
        db_count_row.connect("activated", lambda r: self._show_mysql_databases(service, mysql_info.get('databases', [])))
        mysql_info_group.add(db_count_row)
        


    
    def _on_mysql_change_password(self, service):
        """MySQL root password change dialog"""
        dialog = Adw.MessageDialog.new(self, _("Set MySQL Root Password"), None)
        dialog.set_body(_("Set a new password for MySQL root user. Current password is not required."))
        
        # Create form
        form_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        form_box.set_spacing(12)
        form_box.set_margin_top(12)
        
        # New password
        new_label = Gtk.Label(label=_("New Password:"))
        new_label.set_halign(Gtk.Align.START)
        new_entry = Gtk.PasswordEntry()
        new_entry.set_property("placeholder-text", "Enter new password")
        
        # Confirm password
        confirm_label = Gtk.Label(label=_("Confirm Password:"))
        confirm_label.set_halign(Gtk.Align.START)
        confirm_entry = Gtk.PasswordEntry()
        confirm_entry.set_property("placeholder-text", "Confirm new password")
        
        form_box.append(new_label)
        form_box.append(new_entry)
        form_box.append(confirm_label)
        form_box.append(confirm_entry)
        
        dialog.set_extra_child(form_box)
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("change", _("Set Password"))
        dialog.set_response_appearance("change", Adw.ResponseAppearance.SUGGESTED)
        
        def on_response(dialog, response):
            if response == "change":
                new_password = new_entry.get_text()
                confirm_password = confirm_entry.get_text()
                
                if not new_password:
                    self._show_toast(_("Password cannot be empty"))
                    return
                
                if new_password != confirm_password:
                    self._show_toast(_("Passwords do not match"))
                    return
                
                # Reset password (no current password needed)
                try:
                    success, message = service.reset_root_password(new_password)
                    if success:
                        self._show_toast(_("MySQL root password set successfully!"))
                        # Refresh detail page to show new auth method
                        if self.current_service and self.current_service.name == service.name:
                            GLib.timeout_add_seconds(1, self._refresh_detail_page)
                    else:
                        self._show_toast(_("Failed to set MySQL root password: {error}").format(error=message))
                except Exception as e:
                    logger.error(f"Error setting MySQL root password: {e}")
                    self._show_toast(_("Error: {error}").format(error=str(e)))
                
                dialog.close()
        
        dialog.connect("response", on_response)
        dialog.present()
    
    def _on_mysql_secure_installation(self, service):
        """MySQL secure installation guide"""
        dialog = Adw.MessageDialog.new(self, _("MySQL Secure Installation"), None)
        
        success, message = service.run_mysql_secure_installation()
        dialog.set_body(message)
        
        if success:
            dialog.set_body(dialog.get_body() + "\n\n" + _("Open a terminal and run the command to secure your MySQL installation."))
            dialog.add_response("terminal", _("Open Terminal"))
            dialog.add_response("ok", _("OK"))
            dialog.set_response_appearance("terminal", Adw.ResponseAppearance.SUGGESTED)
        else:
            dialog.add_response("ok", _("OK"))
        
        def on_response(dialog, response):
            if response == "terminal":
                # Open terminal with the command
                import subprocess
                try:
                    subprocess.Popen(['gnome-terminal', '--', 'mysql_secure_installation'])
                except:
                    try:
                        subprocess.Popen(['xterm', '-e', 'mysql_secure_installation'])
                    except:
                        self._show_toast(_("Could not open terminal. Run 'mysql_secure_installation' manually."))
        
        dialog.connect("response", on_response)
        dialog.present()
    
    def _on_mysql_create_database(self, service):
        """MySQL create database dialog"""
        dialog = Adw.MessageDialog.new(self, _("Create MySQL Database"), None)
        dialog.set_body(_("Enter the name for the new database"))
        
        # Database name entry
        entry_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        entry_box.set_spacing(8)
        entry_box.set_margin_top(12)
        
        entry = Gtk.Entry()
        entry.set_property("placeholder-text", "Database name")
        entry_box.append(entry)
        
        dialog.set_extra_child(entry_box)
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("create", _("Create"))
        dialog.set_response_appearance("create", Adw.ResponseAppearance.SUGGESTED)
        
        def on_response(dialog, response):
            if response == "create":
                db_name = entry.get_text().strip()
                if not db_name:
                    self._show_toast(_("Database name cannot be empty"))
                    return
                
                dialog.close()
                
                # Create database (sudo already available from startup)
                success, message = service.create_database(db_name)
                self._show_toast(message)
                
                if success:
                    # Refresh detail page
                    if self.current_service and self.current_service.name == service.name:
                        self._refresh_detail_page()
        
        dialog.connect("response", on_response)
        dialog.present()
    
    def _on_mysql_create_user(self, service):
        """MySQL create user dialog"""
        dialog = Adw.MessageDialog.new(self, _("Create MySQL User"), None)
        dialog.set_body(_("Enter user details"))
        
        # Create form
        form_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        form_box.set_spacing(12)
        form_box.set_margin_top(12)
        
        # Username
        username_label = Gtk.Label(label=_("Username:"))
        username_label.set_halign(Gtk.Align.START)
        username_entry = Gtk.Entry()
        username_entry.set_property("placeholder-text", "Username")
        
        # Password
        password_label = Gtk.Label(label=_("Password:"))
        password_label.set_halign(Gtk.Align.START)
        password_entry = Gtk.PasswordEntry()
        password_entry.set_property("placeholder-text", "Password")
        
        # Host
        host_label = Gtk.Label(label=_("Host (optional):"))
        host_label.set_halign(Gtk.Align.START)
        host_entry = Gtk.Entry()
        host_entry.set_property("placeholder-text", "localhost")
        host_entry.set_text("localhost")
        
        form_box.append(username_label)
        form_box.append(username_entry)
        form_box.append(password_label)
        form_box.append(password_entry)
        form_box.append(host_label)
        form_box.append(host_entry)
        
        dialog.set_extra_child(form_box)
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("create", _("Create User"))
        dialog.set_response_appearance("create", Adw.ResponseAppearance.SUGGESTED)
        
        def on_response(dialog, response):
            if response == "create":
                username = username_entry.get_text().strip()
                password = password_entry.get_text()
                host = host_entry.get_text().strip() or "localhost"
                
                if not username or not password:
                    self._show_toast(_("Username and password are required"))
                    return
                
                dialog.close()
                
                # Check if we need sudo password
                mysql_info = service.get_mysql_status_info()
                if mysql_info.get('auth_method') == 'Unix Socket (sudo mysql)':
                    # Need sudo password
                    def on_password_provided(sudo_password):
                        success, message = service.create_user(username, password, host, sudo_password=sudo_password)
                        self._show_toast(message)
                        
                        if success:
                            # Refresh detail page
                            if self.current_service and self.current_service.name == service.name:
                                self._refresh_detail_page()
                    
                    self._show_sudo_password_dialog(on_password_provided)
                else:
                    # Use existing password
                    success, message = service.create_user(username, password, host)
                    self._show_toast(message)
                    
                    if success:
                        # Refresh detail page
                        if self.current_service and self.current_service.name == service.name:
                            self._refresh_detail_page()
        
        dialog.connect("response", on_response)
        dialog.present()
    
    def _on_mysql_setup_clients(self, service):
        """Setup MySQL for client applications"""
        dialog = Adw.MessageDialog.new(self, _("Setup MySQL for Client Applications"), None)
        dialog.set_body(_("This will configure MySQL to work with external client applications like Navicat, DBGate, and phpMyAdmin."))
        
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("setup", _("Setup"))
        dialog.set_response_appearance("setup", Adw.ResponseAppearance.SUGGESTED)
        
        def on_response(dialog, response):
            if response == "setup":
                self._run_service_action_with_progress(
                    service, 
                    lambda: service.setup_for_clients(),
                    _("Setting up MySQL for client applications..."),
                    _("MySQL client setup completed successfully!"),
                    _("Failed to setup MySQL for client applications")
                )
        
        dialog.connect("response", on_response)
        dialog.present()
    
    def _on_mysql_connection_info(self, service):
        """Show MySQL connection information"""
        dialog = Adw.MessageDialog.new(self, _("MySQL Connection Information"), None)
        
        try:
            # Get connection info
            connection_info = service.get_connection_info()
            
            info_text = ""
            
            if connection_info.get('running', False):
                # TCP Connection info
                tcp_info = connection_info.get('tcp_connection', {})
                info_text += f"🌐 **TCP Connection (for client apps):**\n"
                info_text += f"   Host: {tcp_info.get('host', 'localhost')}\n"
                info_text += f"   Port: {tcp_info.get('port', 3306)}\n"
                info_text += f"   Username: {tcp_info.get('username', 'root')}\n"
                
                if tcp_info.get('password'):
                    info_text += f"   Password: {tcp_info.get('password')}\n"
                else:
                    info_text += f"   Password: (Set password first)\n"
                
                info_text += f"\n🔌 **Socket Connection:**\n"
                socket_info = connection_info.get('socket_connection', {})
                info_text += f"   Socket: {socket_info.get('socket_path', '/var/run/mysqld/mysqld.sock')}\n"
                info_text += f"   Legacy: {socket_info.get('legacy_socket', '/tmp/mysql.sock')}\n"
                
                info_text += f"\n📱 **Client Applications:**\n"
                client_apps = connection_info.get('client_apps', {})
                
                # Navicat
                navicat = client_apps.get('navicat', {})
                info_text += f"   **Navicat:**\n"
                info_text += f"   • Connection Type: {navicat.get('connection_type', 'MySQL')}\n"
                info_text += f"   • Host: {navicat.get('host', 'localhost')}\n"
                info_text += f"   • Port: {navicat.get('port', 3306)}\n"
                info_text += f"   • Username: {navicat.get('username', 'root')}\n"
                
                # DBGate
                dbgate = client_apps.get('dbgate', {})
                info_text += f"\n   **DBGate:**\n"
                info_text += f"   • Engine: {dbgate.get('engine', 'mysql@dbgate-plugin-mysql')}\n"
                info_text += f"   • Server: {dbgate.get('server', 'localhost')}\n"
                info_text += f"   • Port: {dbgate.get('port', 3306)}\n"
                info_text += f"   • User: {dbgate.get('user', 'root')}\n"
            else:
                info_text = "❌ MySQL service is not running.\nStart the service to view connection information."
            
            dialog.set_body(info_text)
            
        except Exception as e:
            logger.error(f"Error getting connection info: {e}")
            dialog.set_body(_("Error retrieving connection information"))
        
        dialog.add_response("close", _("Close"))
        dialog.set_response_appearance("close", Adw.ResponseAppearance.SUGGESTED)
        dialog.present()
    
    def _add_php_sections(self, main_box, service):
        """Add PHP-specific sections to detail page"""
        
        try:
            # Get PHP information
            php_info = service.get_php_info()
            config_info = service.get_config_info()
            
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
            
            main_box.append(version_group)
            
            # Version Actions
            version_actions_group = Adw.PreferencesGroup()
            version_actions_group.set_title(_("Version Actions"))
            
            # Install new version
            install_version_row = Adw.ActionRow()
            install_version_row.set_title(_("Install New Version"))
            install_version_row.set_subtitle(_("Install additional PHP version"))
            install_version_row.set_activatable(True)
            install_version_row.connect("activated", lambda r: self._on_php_install_version(service, available_versions))
            install_icon = Gtk.Image.new_from_icon_name("list-add-symbolic")
            install_version_row.add_prefix(install_icon)
            version_actions_group.add(install_version_row)
            
            # Switch version (if multiple versions available)
            if len(installed_versions) > 1:
                switch_version_row = Adw.ActionRow()
                switch_version_row.set_title(_("Switch Version"))
                switch_version_row.set_subtitle(_("Change active PHP version"))
                switch_version_row.set_activatable(True)
                switch_version_row.connect("activated", lambda r: self._on_php_switch_version(service, installed_versions))
                switch_icon = Gtk.Image.new_from_icon_name("emblem-synchronizing-symbolic")
                switch_version_row.add_prefix(switch_icon)
                version_actions_group.add(switch_version_row)
            
            # Uninstall version (if multiple versions available)
            if len(installed_versions) > 1:
                uninstall_version_row = Adw.ActionRow()
                uninstall_version_row.set_title(_("Uninstall Version"))
                uninstall_version_row.set_subtitle(_("Remove a PHP version"))
                uninstall_version_row.set_activatable(True)
                uninstall_version_row.connect("activated", lambda r: self._on_php_uninstall_version(service, installed_versions))
                uninstall_icon = Gtk.Image.new_from_icon_name("edit-delete-symbolic")
                uninstall_version_row.add_prefix(uninstall_icon)
                version_actions_group.add(uninstall_version_row)
            
            main_box.append(version_actions_group)
            
            # Extensions Management
            extensions_group = Adw.PreferencesGroup()
            extensions_group.set_title(_("Extensions"))
            
            # Get installed extensions
            installed_extensions = service.get_installed_extensions()
            popular_extensions = service.get_popular_extensions()
            
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
            install_ext_row.connect("activated", lambda r: self._on_php_install_extension(service, popular_extensions, installed_extensions))
            install_ext_icon = Gtk.Image.new_from_icon_name("list-add-symbolic")
            install_ext_row.add_prefix(install_ext_icon)
            extensions_group.add(install_ext_row)
            
            # Manage extensions
            manage_ext_row = Adw.ActionRow()
            manage_ext_row.set_title(_("Manage Extensions"))
            manage_ext_row.set_subtitle(_("View and uninstall extensions"))
            manage_ext_row.set_activatable(True)
            manage_ext_row.connect("activated", lambda r: self._on_php_manage_extensions(service, installed_extensions))
            manage_ext_icon = Gtk.Image.new_from_icon_name("preferences-system-symbolic")
            manage_ext_row.add_prefix(manage_ext_icon)
            extensions_group.add(manage_ext_row)
            
            main_box.append(extensions_group)
            
            # Configuration Information
            config_group = Adw.PreferencesGroup()
            config_group.set_title(_("Configuration"))
            
            # Config file location
            if 'config_file' in config_info:
                config_file_row = Adw.ActionRow()
                config_file_row.set_title(_("Configuration File"))
                config_file_row.set_subtitle(config_info['config_file'])
                config_group.add(config_file_row)
            
            # Memory limit
            if 'memory_limit' in config_info:
                memory_row = Adw.ActionRow()
                memory_row.set_title(_("Memory Limit"))
                memory_label = Gtk.Label(label=config_info['memory_limit'])
                memory_label.add_css_class("monospace")
                memory_row.add_suffix(memory_label)
                config_group.add(memory_row)
            
            # Upload max size
            if 'upload_max_size' in config_info:
                upload_row = Adw.ActionRow()
                upload_row.set_title(_("Upload Max Size"))
                upload_label = Gtk.Label(label=config_info['upload_max_size'])
                upload_label.add_css_class("monospace")
                upload_row.add_suffix(upload_label)
                config_group.add(upload_row)
            
            main_box.append(config_group)
            
        except Exception as e:
            logger.error(f"Error adding PHP sections: {e}")
            error_group = Adw.PreferencesGroup()
            error_group.set_title(_("PHP Information"))
            error_row = Adw.ActionRow()
            error_row.set_title(_("Error"))
            error_row.set_subtitle(str(e))
            error_group.add(error_row)
            main_box.append(error_group)
    
    def _add_apache_sections(self, main_box, service):
        """Add Apache-specific sections to detail page"""
        
        # Apache Modules Management
        modules_group = Adw.PreferencesGroup()
        modules_group.set_title(_("Apache Modules"))
        modules_group.set_description(_("Manage Apache modules (enable/disable)"))
        
        try:
            # Manage Modules button
            manage_modules_row = Adw.ActionRow()
            manage_modules_row.set_title(_("Manage Modules"))
            manage_modules_row.set_subtitle(_("Enable or disable Apache modules"))
            manage_modules_row.set_activatable(True)
            manage_modules_row.connect("activated", lambda r: self._on_apache_manage_modules(service))
            manage_icon = Gtk.Image.new_from_icon_name("preferences-system-symbolic")
            manage_modules_row.add_prefix(manage_icon)
            modules_group.add(manage_modules_row)
            
            # Show some key modules status
            modules = service.list_modules()
            
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
            # Show error in UI
            error_row = Adw.ActionRow()
            error_row.set_title(_("Error"))
            error_row.set_subtitle(str(e))
            error_row.set_sensitive(False)
            modules_group.add(error_row)
        
        main_box.append(modules_group)
        
        # PHP Modules Management (Apache-specific)
        php_modules_group = Adw.PreferencesGroup()
        php_modules_group.set_title(_("PHP Modules"))
        php_modules_group.set_description(_("Manage PHP Apache modules (install/switch/remove)"))
        
        try:
            php_module_installed = service.is_php_module_installed()
            
            if php_module_installed:
                # Get PHP module list
                php_modules = service.get_installed_php_modules()
                active_php_module = service.get_active_php_module()
                
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
                    switch_module_row.connect("activated", lambda r: self._on_apache_switch_php_module(service, php_modules))
                    switch_module_icon = Gtk.Image.new_from_icon_name("emblem-synchronizing-symbolic")
                    switch_module_row.add_prefix(switch_module_icon)
                    php_modules_group.add(switch_module_row)
                
                # Install PHP module
                install_php_module_row = Adw.ActionRow()
                install_php_module_row.set_title(_("Install PHP Module"))
                install_php_module_row.set_subtitle(_("Install PHP Apache module for a specific version"))
                install_php_module_row.set_activatable(True)
                install_php_module_row.connect("activated", lambda r: self._on_apache_install_php_module_dialog(service))
                install_php_module_icon = Gtk.Image.new_from_icon_name("list-add-symbolic")
                install_php_module_row.add_prefix(install_php_module_icon)
                php_modules_group.add(install_php_module_row)
                
                # Uninstall PHP module
                if php_modules and len(php_modules) > 0:
                    uninstall_php_module_row = Adw.ActionRow()
                    uninstall_php_module_row.set_title(_("Uninstall PHP Module"))
                    uninstall_php_module_row.set_subtitle(_("Remove a PHP Apache module"))
                    uninstall_php_module_row.set_activatable(True)
                    uninstall_php_module_row.connect("activated", lambda r: self._on_apache_uninstall_php_module_dialog(service, php_modules))
                    uninstall_php_module_icon = Gtk.Image.new_from_icon_name("edit-delete-symbolic")
                    uninstall_php_module_row.add_prefix(uninstall_php_module_icon)
                    php_modules_group.add(uninstall_php_module_row)
            else:
                # Install PHP module button
                install_php_module_row = Adw.ActionRow()
                install_php_module_row.set_title(_("Install PHP Module"))
                install_php_module_row.set_subtitle(_("Install PHP Apache module"))
                install_php_module_row.set_activatable(True)
                install_php_module_row.connect("activated", lambda r: self._on_apache_install_php_module_dialog(service))
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
        
        main_box.append(php_modules_group)
        
        # SSL Certificate Management
        ssl_cert_group = Adw.PreferencesGroup()
        ssl_cert_group.set_title(_("SSL Certificates"))
        
        try:
            # Create self-signed certificate button
            create_cert_row = Adw.ActionRow()
            create_cert_row.set_title(_("Create Self-Signed Certificate"))
            create_cert_row.set_subtitle(_("Generate SSL certificate for a domain"))
            create_cert_row.set_activatable(True)
            create_cert_row.connect("activated", lambda r: self._on_apache_create_certificate(service))
            create_cert_icon = Gtk.Image.new_from_icon_name("document-new-symbolic")
            create_cert_row.add_prefix(create_cert_icon)
            ssl_cert_group.add(create_cert_row)
        
        except Exception as e:
            logger.error(f"Error with SSL certificates: {e}")
        
        main_box.append(ssl_cert_group)
        
        # Virtual Hosts Management
        vhosts_group = Adw.PreferencesGroup()
        vhosts_group.set_title(_("Virtual Hosts"))
        
        try:
            vhosts = service.list_vhosts()
            
            # Create vhost button
            create_vhost_row = Adw.ActionRow()
            create_vhost_row.set_title(_("Create Virtual Host"))
            create_vhost_row.set_subtitle(_("Add a new website configuration"))
            create_vhost_row.set_activatable(True)
            create_vhost_row.connect("activated", lambda r: self._on_apache_create_vhost(service))
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
                    vhost_row.connect("activated", lambda r, s=service, v=vhost: self._show_vhost_detail(s, v))
                    
                    # Arrow icon to indicate clickable
                    arrow = Gtk.Image.new_from_icon_name("go-next-symbolic")
                    arrow.set_valign(Gtk.Align.CENTER)
                    vhost_row.add_suffix(arrow)
                    
                    vhosts_group.add(vhost_row)
        
        except Exception as e:
            logger.error(f"Error listing vhosts: {e}")
        
        main_box.append(vhosts_group)
    
    # ==================== APACHE HANDLERS ====================
    
    def _on_apache_switch_php_module(self, service, php_modules):
        """Switch PHP Apache module dialog"""
        dialog = Adw.MessageDialog.new(self, _("Switch PHP Module"), None)
        dialog.set_body(_("Select the PHP Apache module to activate"))
        
        # Create module selector
        list_box = Gtk.ListBox()
        list_box.set_selection_mode(Gtk.SelectionMode.SINGLE)
        list_box.add_css_class("boxed-list")
        
        active_module = service.get_active_php_module()
        selected_version = [active_module]  # Use list to allow modification in closure
        
        for mod in php_modules:
            row = Gtk.ListBoxRow()
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            box.set_spacing(12)
            box.set_margin_top(8)
            box.set_margin_bottom(8)
            box.set_margin_start(12)
            box.set_margin_end(12)
            
            label = Gtk.Label(label=f"PHP {mod['version']}")
            label.set_hexpand(True)
            label.set_halign(Gtk.Align.START)
            box.append(label)
            
            if mod['enabled']:
                check = Gtk.Image.new_from_icon_name("emblem-ok-symbolic")
                check.add_css_class("success")
                box.append(check)
            
            row.set_child(box)
            row.version = mod['version']
            list_box.append(row)
        
        def on_row_activated(listbox, row):
            selected_version[0] = row.version
        
        list_box.connect("row-activated", on_row_activated)
        
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_child(list_box)
        scrolled.set_min_content_height(200)
        scrolled.set_margin_top(12)
        
        dialog.set_extra_child(scrolled)
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("switch", _("Switch"))
        dialog.set_response_appearance("switch", Adw.ResponseAppearance.SUGGESTED)
        
        def on_response(dialog, response):
            if response == "switch" and selected_version[0]:
                dialog.close()
                self._show_loading_dialog(_("Switching PHP module..."))
                
                # Run in thread
                import threading
                def switch_task():
                    try:
                        success, message = service.switch_php_module(selected_version[0])
                        GLib.idle_add(self._on_operation_complete, success, message)
                    except Exception as e:
                        logger.error(f"Error switching PHP module: {e}")
                        GLib.idle_add(self._on_operation_complete, False, str(e))
                
                thread = threading.Thread(target=switch_task, daemon=True)
                thread.start()
        
        dialog.connect("response", on_response)
        dialog.present()
    
    def _on_apache_install_php_module_dialog(self, service):
        """Install PHP Apache module dialog"""
        dialog = Adw.MessageDialog.new(self, _("Install PHP Module"), None)
        dialog.set_body(_("Enter the PHP version to install Apache module for (e.g., 8.2, 7.4)"))
        
        # Version entry
        entry_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        entry_box.set_spacing(8)
        entry_box.set_margin_top(12)
        
        entry = Gtk.Entry()
        entry.set_property("placeholder-text", "e.g., 8.2")
        entry_box.append(entry)
        
        # Info label
        info_label = Gtk.Label()
        info_label.set_markup(f"<span size='small'>{_('Leave empty to auto-detect')}</span>")
        info_label.add_css_class("dim-label")
        info_label.set_halign(Gtk.Align.START)
        entry_box.append(info_label)
        
        dialog.set_extra_child(entry_box)
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("install", _("Install"))
        dialog.set_response_appearance("install", Adw.ResponseAppearance.SUGGESTED)
        
        def on_response(dialog, response):
            if response == "install":
                version = entry.get_text().strip() or None
                dialog.close()
                
                self._show_loading_dialog(_("Installing PHP module..."))
                
                # Run in thread
                import threading
                def install_task():
                    try:
                        success, message = service.install_php_module(version)
                        GLib.idle_add(self._on_operation_complete, success, message)
                    except Exception as e:
                        logger.error(f"Error installing PHP module: {e}")
                        GLib.idle_add(self._on_operation_complete, False, str(e))
                
                thread = threading.Thread(target=install_task, daemon=True)
                thread.start()
        
        dialog.connect("response", on_response)
        dialog.present()
    
    def _on_apache_uninstall_php_module_dialog(self, service, php_modules):
        """Uninstall PHP Apache module dialog"""
        dialog = Adw.MessageDialog.new(self, _("Uninstall PHP Module"), None)
        dialog.set_body(_("Select the PHP Apache module to uninstall"))
        
        # Create module selector
        list_box = Gtk.ListBox()
        list_box.set_selection_mode(Gtk.SelectionMode.SINGLE)
        list_box.add_css_class("boxed-list")
        
        selected_version = [None]  # Use list to allow modification in closure
        
        for mod in php_modules:
            row = Gtk.ListBoxRow()
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            box.set_spacing(12)
            box.set_margin_top(8)
            box.set_margin_bottom(8)
            box.set_margin_start(12)
            box.set_margin_end(12)
            
            label = Gtk.Label(label=f"PHP {mod['version']}")
            label.set_hexpand(True)
            label.set_halign(Gtk.Align.START)
            box.append(label)
            
            if mod['enabled']:
                status = Gtk.Label(label="(Active)")
                status.add_css_class("dim-label")
                box.append(status)
            
            row.set_child(box)
            row.version = mod['version']
            list_box.append(row)
        
        def on_row_activated(listbox, row):
            selected_version[0] = row.version
        
        list_box.connect("row-activated", on_row_activated)
        
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_child(list_box)
        scrolled.set_min_content_height(200)
        scrolled.set_margin_top(12)
        
        dialog.set_extra_child(scrolled)
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("uninstall", _("Uninstall"))
        dialog.set_response_appearance("uninstall", Adw.ResponseAppearance.DESTRUCTIVE)
        
        def on_response(dialog, response):
            if response == "uninstall" and selected_version[0]:
                dialog.close()
                self._show_loading_dialog(_("Uninstalling PHP module..."))
                
                # Run in thread
                import threading
                def uninstall_task():
                    try:
                        success, message = service.uninstall_php_module(selected_version[0])
                        GLib.idle_add(self._on_operation_complete, success, message)
                    except Exception as e:
                        logger.error(f"Error uninstalling PHP module: {e}")
                        GLib.idle_add(self._on_operation_complete, False, str(e))
                
                thread = threading.Thread(target=uninstall_task, daemon=True)
                thread.start()
        
        dialog.connect("response", on_response)
        dialog.present()
    
    def _on_apache_install_php_module(self, service):
        """Install PHP module for Apache"""
        dialog = Adw.MessageDialog.new(self)
        dialog.set_heading(_("Install PHP Module?"))
        dialog.set_body(_("This will install PHP support for Apache. The server will be restarted."))
        
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("install", _("Install"))
        dialog.set_response_appearance("install", Adw.ResponseAppearance.SUGGESTED)
        
        def on_response(dialog, response):
            if response == "install":
                dialog.close()
                self._show_loading_dialog(_("Installing PHP module..."))
                
                # Thread'de çalıştır
                import threading
                def install_task():
                    try:
                        success, message = service.install_php_module()
                        GLib.idle_add(self._on_operation_complete, success, message)
                    except Exception as e:
                        logger.error(f"Error installing PHP module: {e}")
                        GLib.idle_add(self._on_operation_complete, False, str(e))
                
                thread = threading.Thread(target=install_task, daemon=True)
                thread.start()
        
        dialog.connect("response", on_response)
        dialog.present()
    
    def _on_apache_uninstall_php_module(self, service):
        """Uninstall PHP module from Apache"""
        dialog = Adw.MessageDialog.new(self)
        dialog.set_heading(_("Uninstall PHP Module?"))
        dialog.set_body(_("This will remove PHP support from Apache. The server will be restarted."))
        
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("uninstall", _("Uninstall"))
        dialog.set_response_appearance("uninstall", Adw.ResponseAppearance.DESTRUCTIVE)
        
        def on_response(dialog, response):
            if response == "uninstall":
                dialog.close()
                self._show_loading_dialog(_("Uninstalling PHP module..."))
                
                # Thread'de çalıştır
                import threading
                def uninstall_task():
                    try:
                        success, message = service.uninstall_php_module()
                        GLib.idle_add(self._on_operation_complete, success, message)
                    except Exception as e:
                        logger.error(f"Error uninstalling PHP module: {e}")
                        GLib.idle_add(self._on_operation_complete, False, str(e))
                
                thread = threading.Thread(target=uninstall_task, daemon=True)
                thread.start()
        
        dialog.connect("response", on_response)
        dialog.present()
    
    def _on_apache_manage_modules(self, service):
        """Show Apache modules management dialog"""
        # Create main dialog
        dialog = Adw.Dialog()
        dialog.set_title(_("Apache Modules"))
        dialog.set_content_width(500)
        dialog.set_content_height(600)
        
        # Main container
        toolbar_view = Adw.ToolbarView()
        
        # Header bar
        header_bar = Adw.HeaderBar()
        toolbar_view.add_top_bar(header_bar)
        
        # Content box with loading state
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        content_box.set_margin_top(12)
        content_box.set_margin_bottom(12)
        content_box.set_margin_start(12)
        content_box.set_margin_end(12)
        
        # Loading spinner initially
        loading_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        loading_box.set_valign(Gtk.Align.CENTER)
        loading_box.set_spacing(12)
        
        spinner = Gtk.Spinner()
        spinner.set_spinning(True)
        spinner.set_size_request(32, 32)
        loading_box.append(spinner)
        
        loading_label = Gtk.Label(label=_("Loading modules..."))
        loading_label.add_css_class("dim-label")
        loading_box.append(loading_label)
        
        content_box.append(loading_box)
        toolbar_view.set_content(content_box)
        dialog.set_child(toolbar_view)
        
        # Load modules in thread
        import threading
        def load_modules_task():
            try:
                modules = service.list_modules()
                GLib.idle_add(self._populate_modules_dialog, content_box, loading_box, modules, service, dialog)
            except Exception as e:
                logger.error(f"Error loading modules: {e}")
                GLib.idle_add(self._populate_modules_dialog, content_box, loading_box, [], service, dialog, str(e))
        
        thread = threading.Thread(target=load_modules_task, daemon=True)
        thread.start()
        
        dialog.present(self)
    
    def _populate_modules_dialog(self, content_box, loading_box, modules, service, dialog, error=None):
        """Populate modules dialog with loaded data"""
        # Remove loading spinner
        content_box.remove(loading_box)
        
        if error:
            error_label = Gtk.Label(label=_("Error loading modules: ") + error)
            error_label.set_wrap(True)
            error_label.add_css_class("error")
            content_box.append(error_label)
            return False
        
        if not modules:
            empty_label = Gtk.Label(label=_("No modules found"))
            empty_label.add_css_class("dim-label")
            empty_label.set_valign(Gtk.Align.CENTER)
            content_box.append(empty_label)
            return False
        
        # Create scrolled window
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        # Create list box with modules
        list_box = Gtk.ListBox()
        list_box.set_selection_mode(Gtk.SelectionMode.NONE)
        list_box.add_css_class("boxed-list")
        
        # Sort modules: enabled first, then alphabetically
        modules.sort(key=lambda m: (not m.get('enabled', False), m.get('name', '')))
        
        for module in modules:
            row = Adw.ActionRow()
            row.set_title(module.get('name', 'Unknown'))
            
            # Add description if available
            description = module.get('description', '')
            if description:
                row.set_subtitle(description)
            
            # Add switch
            switch = Gtk.Switch()
            switch.set_active(module.get('enabled', False))
            switch.set_valign(Gtk.Align.CENTER)
            
            # Store module name in switch
            module_name = module.get('name', '')
            switch.module_name = module_name
            switch.service = service
            switch.parent_dialog = dialog
            
            switch.connect("notify::active", self._on_module_switch_toggled)
            
            row.add_suffix(switch)
            row.set_activatable_widget(switch)
            
            list_box.append(row)
        
        scrolled.set_child(list_box)
        content_box.append(scrolled)
        
        return False
    
    def _on_module_switch_toggled(self, switch, param):
        """Handle module enable/disable toggle"""
        module_name = getattr(switch, 'module_name', '')
        service = getattr(switch, 'service', None)
        parent_dialog = getattr(switch, 'parent_dialog', None)
        
        if not module_name or not service:
            return
        
        enabled = switch.get_active()
        
        # Close parent dialog and show loading
        if parent_dialog:
            parent_dialog.close()
        
        if enabled:
            self._show_loading_dialog(_("Enabling module..."))
        else:
            self._show_loading_dialog(_("Disabling module..."))
        
        # Run in thread
        import threading
        def toggle_task():
            try:
                if enabled:
                    success, message = service.enable_module(module_name)
                else:
                    success, message = service.disable_module(module_name)
                GLib.idle_add(self._on_operation_complete, success, message)
            except Exception as e:
                logger.error(f"Error toggling module {module_name}: {e}")
                GLib.idle_add(self._on_operation_complete, False, str(e))
        
        thread = threading.Thread(target=toggle_task, daemon=True)
        thread.start()
    
    def _on_apache_enable_ssl(self, service):
        """Enable SSL module"""
        dialog = Adw.MessageDialog.new(self)
        dialog.set_heading(_("Enable SSL Module?"))
        dialog.set_body(_("This will enable HTTPS support in Apache. The server will be restarted."))
        
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("enable", _("Enable SSL"))
        dialog.set_response_appearance("enable", Adw.ResponseAppearance.SUGGESTED)
        
        def on_response(dialog, response):
            if response == "enable":
                success, message = service.enable_ssl_module()
                self._show_toast(message)
                if success:
                    dialog.close()
                    if self.current_service and self.current_service.name == service.name:
                        self._refresh_detail_page()
        
        dialog.connect("response", on_response)
        dialog.present()
    
    def _on_apache_create_certificate(self, service):
        """Create self-signed certificate dialog"""
        dialog = Adw.MessageDialog.new(self, _("Create SSL Certificate"), None)
        dialog.set_body(_("Enter the domain name for the certificate"))
        
        # Domain entry
        entry_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        entry_box.set_spacing(8)
        entry_box.set_margin_top(12)
        
        entry = Gtk.Entry()
        entry.set_property("placeholder-text", "example.com")
        entry_box.append(entry)
        
        info_label = Gtk.Label()
        info_label.set_markup(f"<span size='small'>{_('A self-signed certificate will be created for development use.')}</span>")
        info_label.set_wrap(True)
        info_label.add_css_class("dim-label")
        entry_box.append(info_label)
        
        dialog.set_extra_child(entry_box)
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("create", _("Create Certificate"))
        dialog.set_response_appearance("create", Adw.ResponseAppearance.SUGGESTED)
        
        def on_response(dialog, response):
            if response == "create":
                domain = entry.get_text().strip()
                if not domain:
                    self._show_toast(_("Domain name cannot be empty"))
                    return
                
                success, message, cert_info = service.create_self_signed_certificate(domain)
                self._show_toast(message)
                
                if success:
                    dialog.close()
                    # Show certificate info
                    info_dialog = Adw.MessageDialog.new(self)
                    info_dialog.set_heading(_("Certificate Created"))
                    info_dialog.set_body(
                        _("Certificate: {cert}\nKey: {key}").format(
                            cert=cert_info.get('cert_path', ''),
                            key=cert_info.get('key_path', '')
                        )
                    )
                    info_dialog.add_response("ok", _("OK"))
                    info_dialog.present()
        
        dialog.connect("response", on_response)
        dialog.present()
    
    def _on_apache_create_vhost(self, service):
        """Create virtual host dialog with comprehensive settings"""
        # Create a full dialog with better layout
        dialog = Adw.Dialog()
        dialog.set_title(_("Create Virtual Host"))
        
        # Create toolbar view
        toolbar_view = Adw.ToolbarView()
        
        # Header bar with cancel and create buttons
        header = Adw.HeaderBar()
        
        cancel_button = Gtk.Button(label=_("Cancel"))
        cancel_button.connect("clicked", lambda b: dialog.close())
        header.pack_start(cancel_button)
        
        create_button = Gtk.Button(label=_("Create"))
        create_button.add_css_class("suggested-action")
        header.pack_end(create_button)
        
        toolbar_view.add_top_bar(header)
        
        # Main content
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_hexpand(True)
        scrolled.set_min_content_width(500)
        scrolled.set_min_content_height(500)
        
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        content_box.set_spacing(24)
        content_box.set_margin_top(24)
        content_box.set_margin_bottom(24)
        content_box.set_margin_start(24)
        content_box.set_margin_end(24)
        
        # Basic Settings Group
        basic_group = Adw.PreferencesGroup()
        basic_group.set_title(_("Basic Settings"))
        basic_group.set_description(_("Configure domain name and document root"))
        
        # Server name entry row
        servername_row = Adw.EntryRow()
        servername_row.set_title(_("Server Name (Domain)"))
        servername_row.set_text("")
        servername_row.set_show_apply_button(False)
        basic_group.add(servername_row)
        
        # Document root with file chooser
        docroot_row = Adw.ActionRow()
        docroot_row.set_title(_("Document Root"))
        docroot_row.set_subtitle(_("Location of website files"))
        
        docroot_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        docroot_box.set_spacing(6)
        docroot_box.set_valign(Gtk.Align.CENTER)
        
        docroot_entry = Gtk.Entry()
        docroot_entry.set_placeholder_text("/var/www/example.local")
        docroot_entry.set_hexpand(True)
        docroot_box.append(docroot_entry)
        
        browse_button = Gtk.Button()
        browse_button.set_icon_name("document-open-symbolic")
        browse_button.set_tooltip_text(_("Browse"))
        
        def on_browse_clicked(button):
            file_dialog = Gtk.FileDialog()
            file_dialog.set_title(_("Select Document Root"))
            file_dialog.select_folder(None, None, lambda d, res: self._on_folder_selected(d, res, docroot_entry))
        
        browse_button.connect("clicked", on_browse_clicked)
        docroot_box.append(browse_button)
        
        docroot_row.add_suffix(docroot_box)
        basic_group.add(docroot_row)
        
        content_box.append(basic_group)
        
        # PHP Settings Group
        php_group = Adw.PreferencesGroup()
        php_group.set_title(_("PHP Configuration"))
        php_group.set_description(_("Select PHP version for this virtual host"))
        
        # PHP version selector
        php_versions = service.get_installed_php_versions()
        php_row = Adw.ComboRow()
        php_row.set_title(_("PHP Version"))
        php_row.set_subtitle(_("Leave as 'None' if not using PHP"))
        
        php_model = Gtk.StringList()
        php_model.append(_("None"))
        php_versions_list = [None]
        
        for version in php_versions:
            php_model.append(f"PHP {version}")
            php_versions_list.append(version)
        
        php_row.set_model(php_model)
        php_row.set_selected(0)
        php_group.add(php_row)
        
        content_box.append(php_group)
        
        # SSL/HTTPS Settings Group
        ssl_group = Adw.PreferencesGroup()
        ssl_group.set_title(_("SSL/HTTPS Configuration"))
        ssl_group.set_description(_("Enable HTTPS with automatic certificate generation"))
        
        # SSL enable switch
        ssl_row = Adw.SwitchRow()
        ssl_row.set_title(_("Enable SSL/HTTPS"))
        ssl_row.set_subtitle(_("Listen on port 443 with automatic self-signed certificate"))
        ssl_row.set_active(False)
        ssl_group.add(ssl_row)
        
        # SSL info when enabled
        ssl_info_row = Adw.ActionRow()
        ssl_info_row.set_title(_("Certificate Generation"))
        ssl_info_row.set_subtitle(_("A self-signed certificate will be automatically created and configured"))
        ssl_info_icon = Gtk.Image.new_from_icon_name("dialog-information-symbolic")
        ssl_info_row.add_prefix(ssl_info_icon)
        ssl_info_row.set_visible(False)
        ssl_group.add(ssl_info_row)
        
        def on_ssl_toggled(switch, *args):
            ssl_info_row.set_visible(switch.get_active())
        
        ssl_row.connect("notify::active", on_ssl_toggled)
        
        content_box.append(ssl_group)
        
        scrolled.set_child(content_box)
        toolbar_view.set_content(scrolled)
        dialog.set_child(toolbar_view)
        
        # Create button handler
        def on_create_clicked(button):
            server_name = servername_row.get_text().strip()
            document_root = docroot_entry.get_text().strip()
            ssl_enabled = ssl_row.get_active()
            php_selected = php_row.get_selected()
            php_version = php_versions_list[php_selected] if php_selected > 0 else None
            
            # Debug logging
            logger.info(f"Creating vhost - Server name: '{server_name}', Document root: '{document_root}'")
            
            # Validation
            if not server_name:
                self._show_toast(_("Server name cannot be empty"))
                return
            
            # Auto-generate document root if empty
            if not document_root:
                document_root = f"/var/www/{server_name}"
                docroot_entry.set_text(document_root)
            
            logger.info(f"Final values - Server name: '{server_name}', Document root: '{document_root}'")
            
            # Show progress
            self._show_toast(_("Creating virtual host..."))
            
            # Create vhost with all settings
            success, message = service.create_vhost(
                server_name=server_name,
                document_root=document_root,
                ssl=ssl_enabled,
                php_version=php_version
            )
            
            self._show_toast(message)
            
            if success:
                dialog.close()
                if self.current_service and self.current_service.name == service.name:
                    self._refresh_detail_page()
        
        create_button.connect("clicked", on_create_clicked)
        
        # Auto-fill document root when server name changes (with debounce)
        auto_fill_timeout = [None]  # Use list to allow modification in closure
        
        def on_servername_changed(entry):
            # Cancel previous timeout
            if auto_fill_timeout[0]:
                GLib.source_remove(auto_fill_timeout[0])
                auto_fill_timeout[0] = None
            
            # Set new timeout (500ms delay)
            def do_auto_fill():
                server_name = entry.get_text().strip()
                if server_name and not docroot_entry.get_text().strip():
                    new_path = f"/var/www/{server_name}"
                    logger.info(f"Auto-filling document root: '{server_name}' -> '{new_path}'")
                    docroot_entry.set_text(new_path)
                auto_fill_timeout[0] = None
                return False  # Don't repeat
            
            auto_fill_timeout[0] = GLib.timeout_add(500, do_auto_fill)
        
        servername_row.connect("changed", on_servername_changed)
        
        dialog.present(self)
    
    def _on_folder_selected(self, file_dialog, result, entry):
        """Handle folder selection for document root"""
        try:
            folder = file_dialog.select_folder_finish(result)
            if folder:
                path = folder.get_path()
                if path:
                    entry.set_text(path)
        except Exception as e:
            logger.error(f"Error selecting folder: {e}")
    
    def _on_apache_toggle_vhost(self, service, vhost, enabled):
        """Toggle virtual host enabled state"""
        if enabled:
            success, message = service.enable_vhost(vhost['filename'])
        else:
            success, message = service.disable_vhost(vhost['filename'])
        
        self._show_toast(message)
        if not success:
            # Revert switch state if failed
            self._show_service_detail(service)
    
    def _on_apache_delete_vhost(self, service, vhost):
        """Delete virtual host"""
        dialog = Adw.MessageDialog.new(self)
        dialog.set_heading(_("Delete Virtual Host?"))
        dialog.set_body(_("Are you sure you want to delete '{name}'? This action cannot be undone.").format(
            name=vhost['server_name']
        ))
        
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("delete", _("Delete"))
        dialog.set_response_appearance("delete", Adw.ResponseAppearance.DESTRUCTIVE)
        
        def on_response(dialog, response):
            if response == "delete":
                success, message = service.delete_vhost(vhost['filename'])
                self._show_toast(message)
                if success:
                    dialog.close()
                    if self.current_service and self.current_service.name == service.name:
                        self._refresh_detail_page()
        
        dialog.connect("response", on_response)
        dialog.present()
    
    def _show_vhost_detail(self, service, vhost):
        """Show virtual host detail page"""
        # Always get full detailed information from script
        filename = vhost.get('filename', '')
        if not filename:
            self._show_toast(_("Invalid virtual host data"))
            return
        
        details = service.get_vhost_details(filename)
        if not details:
            self._show_toast(_("Could not load virtual host details"))
            return
        
        # Debug: Log details
        logger.info(f"Vhost details for {filename}: {details}")
        logger.info(f"Keys: {list(details.keys()) if isinstance(details, dict) else 'Not a dict'}")
        
        # Create detail dialog
        dialog = Adw.Dialog()
        dialog.set_title(details.get('server_name', filename))
        
        # Main content
        toolbar_view = Adw.ToolbarView()
        
        # Header bar
        header = Adw.HeaderBar()
        header.set_show_title(True)
        toolbar_view.add_top_bar(header)
        
        # Scrolled content
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_hexpand(True)
        scrolled.set_min_content_width(500)
        scrolled.set_min_content_height(600)
        
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        content_box.set_spacing(24)
        content_box.set_margin_top(24)
        content_box.set_margin_bottom(24)
        content_box.set_margin_start(24)
        content_box.set_margin_end(24)
        
        # Site Information
        info_group = Adw.PreferencesGroup()
        info_group.set_title(_("Site Information"))
        
        # Server name
        name_row = Adw.ActionRow()
        name_row.set_title(_("Server Name"))
        server_name = details.get('server_name', 'N/A')
        logger.info(f"Setting server_name: {server_name}")
        name_row.set_subtitle(server_name)
        info_group.add(name_row)
        
        # Document root
        docroot_row = Adw.ActionRow()
        docroot_row.set_title(_("Document Root"))
        doc_root = details.get('document_root', 'N/A')
        logger.info(f"Setting document_root: {doc_root}")
        docroot_row.set_subtitle(doc_root or "N/A")
        info_group.add(docroot_row)
        
        # SSL status
        ssl_row = Adw.ActionRow()
        ssl_row.set_title(_("SSL/HTTPS"))
        if details.get('ssl', False) or details.get('ssl_enabled', False):
            ssl_row.set_subtitle("✅ " + _("Enabled"))
        else:
            ssl_row.set_subtitle("❌ " + _("Disabled"))
        info_group.add(ssl_row)
        
        # PHP version
        php_row = Adw.ActionRow()
        php_row.set_title(_("PHP Version"))
        php_version = details.get('php_version', '')
        if php_version:
            php_row.set_subtitle(f"PHP {php_version}")
        else:
            php_row.set_subtitle(_("Not configured"))
        info_group.add(php_row)
        
        content_box.append(info_group)
        
        # PHP Management
        php_group = Adw.PreferencesGroup()
        php_group.set_title(_("PHP Configuration"))
        
        php_versions = service.get_installed_php_versions()
        if php_versions:
            # Change PHP version
            change_php_row = Adw.ActionRow()
            change_php_row.set_title(_("Change PHP Version"))
            change_php_row.set_subtitle(_("Switch to a different PHP version"))
            change_php_row.set_activatable(True)
            change_php_row.connect("activated", lambda r: self._on_vhost_change_php(service, details, php_versions, dialog))
            change_php_icon = Gtk.Image.new_from_icon_name("emblem-synchronizing-symbolic")
            change_php_row.add_prefix(change_php_icon)
            php_group.add(change_php_row)
        
        content_box.append(php_group)
        
        # Actions
        actions_group = Adw.PreferencesGroup()
        actions_group.set_title(_("Actions"))
        
        # Edit virtual host
        edit_row = Adw.ActionRow()
        edit_row.set_title(_("Edit Virtual Host"))
        edit_row.set_subtitle(_("Modify domain, document root, PHP and SSL settings"))
        edit_row.set_activatable(True)
        edit_row.connect("activated", lambda r: self._on_vhost_edit(service, details, dialog))
        edit_icon = Gtk.Image.new_from_icon_name("document-edit-symbolic")
        edit_row.add_prefix(edit_icon)
        actions_group.add(edit_row)
        
        # Enable/Disable
        os_type = service.platform_manager.os_type.value
        if os_type in ['ubuntu', 'debian']:
            if details['enabled']:
                disable_row = Adw.ActionRow()
                disable_row.set_title(_("Disable Site"))
                disable_row.set_subtitle(_("Temporarily disable this virtual host"))
                disable_row.set_activatable(True)
                disable_row.connect("activated", lambda r: self._on_vhost_disable(service, details, dialog))
                disable_icon = Gtk.Image.new_from_icon_name("media-playback-pause-symbolic")
                disable_row.add_prefix(disable_icon)
                actions_group.add(disable_row)
            else:
                enable_row = Adw.ActionRow()
                enable_row.set_title(_("Enable Site"))
                enable_row.set_subtitle(_("Enable this virtual host"))
                enable_row.set_activatable(True)
                enable_row.connect("activated", lambda r: self._on_vhost_enable(service, details, dialog))
                enable_icon = Gtk.Image.new_from_icon_name("media-playback-start-symbolic")
                enable_row.add_prefix(enable_icon)
                actions_group.add(enable_row)
        
        # Open in browser
        browse_row = Adw.ActionRow()
        browse_row.set_title(_("Open in Browser"))
        browse_row.set_subtitle(f"http://{details.get('server_name', 'N/A')}/")
        browse_row.set_activatable(True)
        browse_row.connect("activated", lambda r: self._on_vhost_open_browser(details))
        browse_icon = Gtk.Image.new_from_icon_name("web-browser-symbolic")
        browse_row.add_prefix(browse_icon)
        actions_group.add(browse_row)
        
        # Delete
        delete_row = Adw.ActionRow()
        delete_row.set_title(_("Delete Virtual Host"))
        delete_row.set_subtitle(_("Permanently remove this site"))
        delete_row.set_activatable(True)
        delete_row.connect("activated", lambda r: self._on_vhost_delete_confirm(service, details, dialog))
        delete_icon = Gtk.Image.new_from_icon_name("user-trash-symbolic")
        delete_row.add_prefix(delete_icon)
        actions_group.add(delete_row)
        
        content_box.append(actions_group)
        
        scrolled.set_child(content_box)
        toolbar_view.set_content(scrolled)
        dialog.set_child(toolbar_view)
        dialog.present(self)
    
    def _on_vhost_change_php(self, service, details, versions, parent_dialog):
        """Change PHP version for vhost"""
        dialog = Adw.MessageDialog.new(self)
        dialog.set_heading(_("Change PHP Version"))
        dialog.set_body(_("Select the PHP version for {name}").format(name=details.get('server_name', 'N/A')))
        
        # Version selector
        list_box = Gtk.ListBox()
        list_box.set_selection_mode(Gtk.SelectionMode.NONE)
        list_box.add_css_class("boxed-list")
        
        selected_version = [details.get('php_version', versions[0] if versions else '')]
        check_buttons = []
        
        for version in versions:
            row = Adw.ActionRow()
            row.set_title(f"PHP {version}")
            row.set_activatable(True)
            
            # Check button
            check = Gtk.CheckButton()
            check.set_active(version == selected_version[0])
            check.set_valign(Gtk.Align.CENTER)
            row.add_suffix(check)
            row.set_activatable_widget(check)
            
            # Store version
            check.version = version
            check_buttons.append(check)
            
            # Make radio behavior (only one selected)
            def on_check_toggled(check_btn):
                if check_btn.get_active():
                    selected_version[0] = check_btn.version
                    # Uncheck others
                    for other in check_buttons:
                        if other != check_btn:
                            other.set_active(False)
            
            check.connect("toggled", on_check_toggled)
            
            list_box.append(row)
        
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_child(list_box)
        scrolled.set_min_content_height(200)
        scrolled.set_margin_top(12)
        
        dialog.set_extra_child(scrolled)
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("change", _("Change"))
        dialog.set_response_appearance("change", Adw.ResponseAppearance.SUGGESTED)
        
        def on_response(dialog, response):
            if response == "change":
                new_version = selected_version[0]
                logger.info(f"Changing PHP version for {details['filename']} to {new_version}")
                
                if not new_version:
                    self._show_toast(_("Please select a PHP version"))
                    return
                
                success, message = service.update_vhost_php_version(details['filename'], new_version)
                logger.info(f"Update result: success={success}, message={message}")
                self._show_toast(message)
                
                if success:
                    dialog.close()
                    parent_dialog.close()
                    if self.current_service and self.current_service.name == service.name:
                        self._refresh_detail_page()
        
        dialog.connect("response", on_response)
        dialog.present()
    
    def _on_vhost_enable(self, service, details, parent_dialog):
        """Enable virtual host"""
        success, message = service.enable_vhost(details['filename'])
        self._show_toast(message)
        if success:
            parent_dialog.close()
            if self.current_service and self.current_service.name == service.name:
                self._refresh_detail_page()
    
    def _on_vhost_disable(self, service, details, parent_dialog):
        """Disable virtual host"""
        success, message = service.disable_vhost(details['filename'])
        self._show_toast(message)
        if success:
            parent_dialog.close()
            if self.current_service and self.current_service.name == service.name:
                self._refresh_detail_page()
    
    def _on_vhost_open_browser(self, details):
        """Open virtual host in browser"""
        import subprocess
        url = f"http://{details.get('server_name', 'localhost')}/"
        try:
            subprocess.Popen(['xdg-open', url])
        except Exception as e:
            logger.error(f"Error opening browser: {e}")
            self._show_toast(_("Could not open browser"))
    
    def _on_vhost_edit(self, service, details, parent_dialog):
        """Edit virtual host configuration"""
        # Create edit dialog
        dialog = Adw.Dialog()
        dialog.set_title(_("Edit Virtual Host: {name}").format(name=details.get('server_name', 'N/A')))
        
        # Create toolbar view
        toolbar_view = Adw.ToolbarView()
        
        # Header bar with cancel and save buttons
        header = Adw.HeaderBar()
        
        cancel_button = Gtk.Button(label=_("Cancel"))
        cancel_button.connect("clicked", lambda b: dialog.close())
        header.pack_start(cancel_button)
        
        save_button = Gtk.Button(label=_("Save"))
        save_button.add_css_class("suggested-action")
        header.pack_end(save_button)
        
        toolbar_view.add_top_bar(header)
        
        # Main content
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_hexpand(True)
        scrolled.set_min_content_width(500)
        scrolled.set_min_content_height(500)
        
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        content_box.set_spacing(24)
        content_box.set_margin_top(24)
        content_box.set_margin_bottom(24)
        content_box.set_margin_start(24)
        content_box.set_margin_end(24)
        
        # Basic Settings Group (Read-only for now)
        basic_group = Adw.PreferencesGroup()
        basic_group.set_title(_("Basic Settings"))
        basic_group.set_description(_("Domain and document root (read-only)"))
        
        # Server name (read-only)
        servername_row = Adw.ActionRow()
        servername_row.set_title(_("Server Name"))
        servername_label = Gtk.Label(label=details.get('server_name', 'N/A'))
        servername_label.set_selectable(True)
        servername_row.add_suffix(servername_label)
        basic_group.add(servername_row)
        
        # Document root (read-only)
        docroot_row = Adw.ActionRow()
        docroot_row.set_title(_("Document Root"))
        docroot_label = Gtk.Label(label=details.get('document_root', 'N/A'))
        docroot_label.set_selectable(True)
        docroot_row.add_suffix(docroot_label)
        basic_group.add(docroot_row)
        
        content_box.append(basic_group)
        
        # PHP Settings Group
        php_group = Adw.PreferencesGroup()
        php_group.set_title(_("PHP Configuration"))
        php_group.set_description(_("Change PHP version for this virtual host"))
        
        # PHP version selector
        php_versions = service.get_installed_php_versions()
        php_row = Adw.ComboRow()
        php_row.set_title(_("PHP Version"))
        
        php_model = Gtk.StringList()
        php_model.append(_("None"))
        php_versions_list = [None]
        
        current_php = details.get('php_version', '')
        selected_index = 0
        
        for i, version in enumerate(php_versions, 1):
            php_model.append(f"PHP {version}")
            php_versions_list.append(version)
            if version == current_php:
                selected_index = i
        
        php_row.set_model(php_model)
        php_row.set_selected(selected_index)
        php_group.add(php_row)
        
        content_box.append(php_group)
        
        # SSL/HTTPS Settings Group
        ssl_group = Adw.PreferencesGroup()
        ssl_group.set_title(_("SSL/HTTPS Configuration"))
        ssl_group.set_description(_("Current SSL status (cannot be changed in edit mode)"))
        
        # SSL status (read-only)
        ssl_status_row = Adw.ActionRow()
        ssl_status_row.set_title(_("SSL Status"))
        ssl_enabled = details.get('ssl', False)
        if ssl_enabled:
            ssl_label = Gtk.Label(label="✅ Enabled")
            ssl_label.add_css_class("success")
        else:
            ssl_label = Gtk.Label(label="❌ Disabled")
        ssl_status_row.add_suffix(ssl_label)
        ssl_group.add(ssl_status_row)
        
        content_box.append(ssl_group)
        
        scrolled.set_child(content_box)
        toolbar_view.set_content(scrolled)
        dialog.set_child(toolbar_view)
        
        # Save button handler
        def on_save_clicked(button):
            php_selected = php_row.get_selected()
            new_php_version = php_versions_list[php_selected]
            old_php_version = details.get('php_version', '')
            
            # Check if PHP version changed
            if new_php_version != old_php_version:
                if new_php_version:
                    # Update to new PHP version
                    success, message = service.update_vhost_php_version(details['filename'], new_php_version)
                else:
                    # Remove PHP configuration (set to empty)
                    success, message = service.update_vhost_php_version(details['filename'], '')
                
                self._show_toast(message)
                
                if success:
                    dialog.close()
                    parent_dialog.close()
                    if self.current_service and self.current_service.name == service.name:
                        self._refresh_detail_page()
            else:
                self._show_toast(_("No changes made"))
                dialog.close()
        
        save_button.connect("clicked", on_save_clicked)
        dialog.present(parent_dialog)
    
    def _on_vhost_delete_confirm(self, service, details, parent_dialog):
        """Confirm and delete virtual host"""
        dialog = Adw.MessageDialog.new(parent_dialog)
        dialog.set_heading(_("Delete {name}?").format(name=details.get('server_name', 'N/A')))
        dialog.set_body(_("This will permanently delete the virtual host configuration. The document root files will not be deleted."))
        
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("delete", _("Delete"))
        dialog.set_response_appearance("delete", Adw.ResponseAppearance.DESTRUCTIVE)
        
        def on_response(dialog, response):
            if response == "delete":
                success, message = service.delete_vhost(details['filename'])
                self._show_toast(message)
                if success:
                    dialog.close()
                    parent_dialog.close()
                    if self.current_service and self.current_service.name == service.name:
                        self._refresh_detail_page()
        
        dialog.connect("response", on_response)
        dialog.present()
    
    def _on_refresh_clicked(self, button):
        """Refresh button clicked"""
        self._load_services()
    
    # ==================== PHP EVENT HANDLERS ====================
    
    def _on_php_install_version(self, service, available_versions):
        """Install new PHP version dialog"""
        # Filter out already installed versions
        php_info = service.get_php_info()
        installed_versions = set(php_info.get('installed_versions', []))
        installable_versions = [v for v in available_versions if v not in installed_versions]
        
        if not installable_versions:
            self._show_toast(_("All available PHP versions are already installed"))
            return
        
        dialog = Adw.MessageDialog.new(self, _("Install PHP Version"), None)
        dialog.set_body(_("Select a PHP version to install"))
        
        # Version selector
        list_box = Gtk.ListBox()
        list_box.set_selection_mode(Gtk.SelectionMode.SINGLE)
        list_box.add_css_class("boxed-list")
        
        selected_version = [None]
        
        for version in installable_versions:
            row = Gtk.ListBoxRow()
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            box.set_spacing(12)
            box.set_margin_top(8)
            box.set_margin_bottom(8)
            box.set_margin_start(12)
            box.set_margin_end(12)
            
            label = Gtk.Label(label=f"PHP {version}")
            label.set_hexpand(True)
            label.set_halign(Gtk.Align.START)
            box.append(label)
            
            row.set_child(box)
            row.version = version
            list_box.append(row)
        
        def on_row_activated(listbox, row):
            selected_version[0] = row.version
        
        list_box.connect("row-activated", on_row_activated)
        
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_child(list_box)
        scrolled.set_min_content_height(200)
        scrolled.set_margin_top(12)
        
        dialog.set_extra_child(scrolled)
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("install", _("Install"))
        dialog.set_response_appearance("install", Adw.ResponseAppearance.SUGGESTED)
        
        def on_response(dialog, response):
            if response == "install" and selected_version[0]:
                version = selected_version[0]
                dialog.close()
                
                # Show progress dialog
                self._show_loading_dialog(f"Installing PHP {version}...")
                
                def install_thread():
                    try:
                        success, message = service.install_version(version)
                        GLib.idle_add(self._on_operation_complete, success, message)
                    except Exception as e:
                        GLib.idle_add(self._on_operation_complete, False, str(e))
                
                import threading
                threading.Thread(target=install_thread, daemon=True).start()
        
        dialog.connect("response", on_response)
        dialog.present()
    
    def _on_php_switch_version(self, service, installed_versions):
        """Switch PHP version dialog"""
        dialog = Adw.MessageDialog.new(self, _("Switch PHP Version"), None)
        dialog.set_body(_("Select the PHP version to activate"))
        
        # Get current active version
        php_info = service.get_php_info()
        current_version = php_info.get('active_version')
        
        # Version selector
        list_box = Gtk.ListBox()
        list_box.set_selection_mode(Gtk.SelectionMode.SINGLE)
        list_box.add_css_class("boxed-list")
        
        selected_version = [current_version]
        
        for version in installed_versions:
            row = Gtk.ListBoxRow()
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            box.set_spacing(12)
            box.set_margin_top(8)
            box.set_margin_bottom(8)
            box.set_margin_start(12)
            box.set_margin_end(12)
            
            label = Gtk.Label(label=f"PHP {version}")
            label.set_hexpand(True)
            label.set_halign(Gtk.Align.START)
            box.append(label)
            
            if version == current_version:
                check = Gtk.Image.new_from_icon_name("emblem-ok-symbolic")
                check.add_css_class("success")
                box.append(check)
            
            row.set_child(box)
            row.version = version
            list_box.append(row)
        
        def on_row_activated(listbox, row):
            selected_version[0] = row.version
        
        list_box.connect("row-activated", on_row_activated)
        
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_child(list_box)
        scrolled.set_min_content_height(200)
        scrolled.set_margin_top(12)
        
        dialog.set_extra_child(scrolled)
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("switch", _("Switch"))
        dialog.set_response_appearance("switch", Adw.ResponseAppearance.SUGGESTED)
        
        def on_response(dialog, response):
            if response == "switch" and selected_version[0]:
                version = selected_version[0]
                if version == current_version:
                    self._show_toast(_("This version is already active"))
                    return
                
                dialog.close()
                
                # Show progress dialog
                self._show_loading_dialog(f"Switching to PHP {version}...")
                
                def switch_thread():
                    try:
                        success, message = service.switch_version(version)
                        GLib.idle_add(self._on_operation_complete, success, message)
                    except Exception as e:
                        GLib.idle_add(self._on_operation_complete, False, str(e))
                
                import threading
                threading.Thread(target=switch_thread, daemon=True).start()
        
        dialog.connect("response", on_response)
        dialog.present()
    
    def _on_php_uninstall_version(self, service, installed_versions):
        """Uninstall PHP version dialog"""
        # Get current active version
        php_info = service.get_php_info()
        current_version = php_info.get('active_version')
        
        # Filter out active version (can't uninstall active version)
        uninstallable_versions = [v for v in installed_versions if v != current_version]
        
        if not uninstallable_versions:
            self._show_toast(_("Cannot uninstall the active PHP version"))
            return
        
        dialog = Adw.MessageDialog.new(self, _("Uninstall PHP Version"), None)
        dialog.set_body(_("Select a PHP version to uninstall. The active version cannot be uninstalled."))
        
        # Version selector
        list_box = Gtk.ListBox()
        list_box.set_selection_mode(Gtk.SelectionMode.SINGLE)
        list_box.add_css_class("boxed-list")
        
        selected_version = [None]
        
        for version in uninstallable_versions:
            row = Gtk.ListBoxRow()
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            box.set_spacing(12)
            box.set_margin_top(8)
            box.set_margin_bottom(8)
            box.set_margin_start(12)
            box.set_margin_end(12)
            
            label = Gtk.Label(label=f"PHP {version}")
            label.set_hexpand(True)
            label.set_halign(Gtk.Align.START)
            box.append(label)
            
            row.set_child(box)
            row.version = version
            list_box.append(row)
        
        def on_row_activated(listbox, row):
            selected_version[0] = row.version
        
        list_box.connect("row-activated", on_row_activated)
        
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_child(list_box)
        scrolled.set_min_content_height(200)
        scrolled.set_margin_top(12)
        
        dialog.set_extra_child(scrolled)
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("uninstall", _("Uninstall"))
        dialog.set_response_appearance("uninstall", Adw.ResponseAppearance.DESTRUCTIVE)
        
        def on_response(dialog, response):
            if response == "uninstall" and selected_version[0]:
                version = selected_version[0]
                dialog.close()
                
                # Confirmation dialog
                confirm_dialog = Adw.MessageDialog.new(self, _("Confirm Uninstall"), None)
                confirm_dialog.set_body(_("Are you sure you want to uninstall PHP {version}? This action cannot be undone.").format(version=version))
                confirm_dialog.add_response("cancel", _("Cancel"))
                confirm_dialog.add_response("uninstall", _("Uninstall"))
                confirm_dialog.set_response_appearance("uninstall", Adw.ResponseAppearance.DESTRUCTIVE)
                
                def on_confirm_response(dialog, response):
                    if response == "uninstall":
                        dialog.close()
                        
                        # Show progress dialog
                        self._show_loading_dialog(f"Uninstalling PHP {version}...")
                        
                        def uninstall_thread():
                            try:
                                success, message = service.uninstall_version(version)
                                GLib.idle_add(self._on_operation_complete, success, message)
                            except Exception as e:
                                GLib.idle_add(self._on_operation_complete, False, str(e))
                        
                        import threading
                        threading.Thread(target=uninstall_thread, daemon=True).start()
                
                confirm_dialog.connect("response", on_confirm_response)
                confirm_dialog.present()
        
        dialog.connect("response", on_response)
        dialog.present()
    
    def _on_php_install_extension(self, service, popular_extensions, installed_extensions):
        """Install PHP extension dialog"""
        dialog = Adw.MessageDialog.new(self, _("Install PHP Extension"), None)
        dialog.set_body(_("Enter the extension name or select from popular extensions"))
        
        # Create form
        form_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        form_box.set_spacing(12)
        form_box.set_margin_top(12)
        
        # Extension name entry
        name_label = Gtk.Label(label=_("Extension Name:"))
        name_label.set_halign(Gtk.Align.START)
        name_entry = Gtk.Entry()
        name_entry.set_placeholder_text("e.g., redis, imagick, xdebug")
        
        form_box.append(name_label)
        form_box.append(name_entry)
        
        # Popular extensions (not already installed)
        available_popular = [ext for ext in popular_extensions if ext not in installed_extensions]
        if available_popular:
            popular_label = Gtk.Label(label=_("Popular Extensions:"))
            popular_label.set_halign(Gtk.Align.START)
            popular_label.set_margin_top(12)
            form_box.append(popular_label)
            
            # Create flow box for popular extensions
            flow_box = Gtk.FlowBox()
            flow_box.set_max_children_per_line(4)
            flow_box.set_selection_mode(Gtk.SelectionMode.SINGLE)
            
            for ext in available_popular[:8]:  # Show max 8 popular extensions
                button = Gtk.Button(label=ext)
                button.add_css_class("pill")
                button.connect("clicked", lambda btn, extension=ext: name_entry.set_text(extension))
                flow_box.append(button)
            
            form_box.append(flow_box)
        
        dialog.set_extra_child(form_box)
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("install", _("Install"))
        dialog.set_response_appearance("install", Adw.ResponseAppearance.SUGGESTED)
        
        def on_response(dialog, response):
            if response == "install":
                extension = name_entry.get_text().strip()
                if not extension:
                    self._show_toast(_("Extension name is required"))
                    return
                
                if not service.validate_extension(extension):
                    self._show_toast(_("Invalid extension name"))
                    return
                
                dialog.close()
                
                # Show progress dialog
                self._show_loading_dialog(f"Installing PHP extension {extension}...")
                
                def install_thread():
                    try:
                        success, message = service.install_extension(extension)
                        GLib.idle_add(self._on_operation_complete, success, message)
                    except Exception as e:
                        GLib.idle_add(self._on_operation_complete, False, str(e))
                
                import threading
                threading.Thread(target=install_thread, daemon=True).start()
        
        dialog.connect("response", on_response)
        dialog.present()
    
    def _on_php_manage_extensions(self, service, installed_extensions):
        """Manage PHP extensions dialog"""
        dialog = Adw.MessageDialog.new(self, _("Manage PHP Extensions"), None)
        dialog.set_body(_("Installed PHP extensions"))
        
        if not installed_extensions:
            dialog.set_body(_("No extensions found"))
            dialog.add_response("ok", _("OK"))
            dialog.present()
            return
        
        # Create extensions list
        list_box = Gtk.ListBox()
        list_box.set_selection_mode(Gtk.SelectionMode.NONE)
        list_box.add_css_class("boxed-list")
        
        # Core extensions that shouldn't be uninstalled
        core_extensions = {'Core', 'standard', 'SPL', 'Reflection', 'pcre', 'date', 'hash'}
        
        for extension in sorted(installed_extensions):
            row = Gtk.ListBoxRow()
            row.set_selectable(False)
            row.set_activatable(False)
            
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            box.set_spacing(12)
            box.set_margin_top(8)
            box.set_margin_bottom(8)
            box.set_margin_start(12)
            box.set_margin_end(12)
            
            label = Gtk.Label(label=extension)
            label.set_hexpand(True)
            label.set_halign(Gtk.Align.START)
            box.append(label)
            
            if extension in core_extensions:
                core_label = Gtk.Label(label=_("Core"))
                core_label.add_css_class("dim-label")
                box.append(core_label)
            else:
                uninstall_btn = Gtk.Button()
                uninstall_btn.set_icon_name("edit-delete-symbolic")
                uninstall_btn.add_css_class("destructive-action")
                uninstall_btn.set_tooltip_text(_("Uninstall"))
                uninstall_btn.connect("clicked", lambda btn, ext=extension: self._on_php_uninstall_extension(service, ext, dialog))
                box.append(uninstall_btn)
            
            row.set_child(box)
            list_box.append(row)
        
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_child(list_box)
        scrolled.set_min_content_height(400)
        scrolled.set_margin_top(12)
        
        dialog.set_extra_child(scrolled)
        dialog.add_response("close", _("Close"))
        dialog.present()
    
    def _on_php_uninstall_extension(self, service, extension, parent_dialog):
        """Uninstall PHP extension"""
        dialog = Adw.MessageDialog.new(parent_dialog, _("Uninstall Extension"), None)
        dialog.set_body(_("Are you sure you want to uninstall the {extension} extension?").format(extension=extension))
        
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("uninstall", _("Uninstall"))
        dialog.set_response_appearance("uninstall", Adw.ResponseAppearance.DESTRUCTIVE)
        
        def on_response(dialog, response):
            if response == "uninstall":
                dialog.close()
                parent_dialog.close()
                
                # Show progress dialog
                self._show_loading_dialog(f"Uninstalling PHP extension {extension}...")
                
                def uninstall_thread():
                    try:
                        success, message = service.uninstall_extension(extension)
                        GLib.idle_add(self._on_operation_complete, success, message)
                    except Exception as e:
                        GLib.idle_add(self._on_operation_complete, False, str(e))
                
                import threading
                threading.Thread(target=uninstall_thread, daemon=True).start()
        
        dialog.connect("response", on_response)
        dialog.present()

    def _show_mysql_databases(self, service, databases):
        """Show MySQL databases list dialog"""
        dialog = Adw.MessageDialog.new(self, _("MySQL Databases"), None)
        
        if not databases:
            dialog.set_body(_("No user databases found. You can create your first database now."))
            dialog.add_response("close", _("Close"))
            dialog.add_response("create", _("Create Database"))
            dialog.set_response_appearance("create", Adw.ResponseAppearance.SUGGESTED)
            
            def on_empty_response(dialog, response):
                if response == "create":
                    dialog.close()
                    self._on_mysql_create_database(service)
            
            dialog.connect("response", on_empty_response)
            dialog.present()
            return
        
        # Create scrollable list
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_min_content_height(200)
        scrolled.set_max_content_height(400)
        
        list_box = Gtk.ListBox()
        list_box.add_css_class("boxed-list")
        
        for db_name in databases:
            row = Adw.ActionRow()
            row.set_title(db_name)
            
            # Add database icon
            db_icon = Gtk.Image.new_from_icon_name("server-database-symbolic")
            row.add_prefix(db_icon)
            
            # Add delete button
            delete_btn = Gtk.Button()
            delete_btn.set_icon_name("user-trash-symbolic")
            delete_btn.add_css_class("flat")
            delete_btn.add_css_class("destructive-action")
            delete_btn.set_tooltip_text(_("Delete Database"))
            delete_btn.connect("clicked", lambda b, db=db_name: self._confirm_delete_database(service, db, dialog))
            row.add_suffix(delete_btn)
            
            list_box.append(row)
        
        scrolled.set_child(list_box)
        
        # Create main box
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        main_box.set_spacing(12)
        main_box.set_margin_top(12)
        
        # Add header
        header_label = Gtk.Label(label=f"Found {len(databases)} user database(s):")
        header_label.set_halign(Gtk.Align.START)
        main_box.append(header_label)
        
        main_box.append(scrolled)
        
        dialog.set_extra_child(main_box)
        dialog.add_response("close", _("Close"))
        dialog.add_response("create", _("Create New"))
        dialog.set_response_appearance("create", Adw.ResponseAppearance.SUGGESTED)
        
        def on_response(dialog, response):
            if response == "create":
                dialog.close()
                self._on_mysql_create_database(service)
        
        dialog.connect("response", on_response)
        dialog.present()
    
    def _show_mysql_users(self, service, users):
        """Show MySQL users list dialog"""
        dialog = Adw.MessageDialog.new(self, _("MySQL Users"), None)
        
        if not users:
            dialog.set_body(_("No users found. You can create your first user now."))
            dialog.add_response("close", _("Close"))
            dialog.add_response("create", _("Create User"))
            dialog.set_response_appearance("create", Adw.ResponseAppearance.SUGGESTED)
            
            def on_empty_user_response(dialog, response):
                if response == "create":
                    dialog.close()
                    self._on_mysql_create_user(service)
            
            dialog.connect("response", on_empty_user_response)
            dialog.present()
            return
        
        # Create scrollable list
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_min_content_height(200)
        scrolled.set_max_content_height(400)
        
        list_box = Gtk.ListBox()
        list_box.add_css_class("boxed-list")
        
        for user in users:
            row = Adw.ActionRow()
            row.set_title(user.get('username', ''))
            row.set_subtitle(f"Host: {user.get('host', 'localhost')}")
            
            # Add user icon
            user_icon = Gtk.Image.new_from_icon_name("system-users-symbolic")
            row.add_prefix(user_icon)
            
            # Show if it's a system user
            if user.get('username') in ['root', 'mysql.session', 'mysql.sys', 'debian-sys-maint']:
                system_label = Gtk.Label(label="System")
                system_label.add_css_class("caption")
                system_label.add_css_class("dim-label")
                row.add_suffix(system_label)
            
            list_box.append(row)
        
        scrolled.set_child(list_box)
        
        # Create main box
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        main_box.set_spacing(12)
        main_box.set_margin_top(12)
        
        # Add header
        header_label = Gtk.Label(label=f"Found {len(users)} user(s):")
        header_label.set_halign(Gtk.Align.START)
        main_box.append(header_label)
        
        main_box.append(scrolled)
        
        dialog.set_extra_child(main_box)
        dialog.add_response("close", _("Close"))
        dialog.add_response("create", _("Create New"))
        dialog.set_response_appearance("create", Adw.ResponseAppearance.SUGGESTED)
        
        def on_response(dialog, response):
            if response == "create":
                dialog.close()
                self._on_mysql_create_user(service)
        
        dialog.connect("response", on_response)
        dialog.present()

    def _confirm_delete_database(self, service, db_name, parent_dialog):
        """Confirm database deletion"""
        confirm_dialog = Adw.MessageDialog.new(self, _("Delete Database"), None)
        confirm_dialog.set_body(f"Are you sure you want to delete database '{db_name}'?\n\nThis action cannot be undone!")
        
        confirm_dialog.add_response("cancel", _("Cancel"))
        confirm_dialog.add_response("delete", _("Delete"))
        confirm_dialog.set_response_appearance("delete", Adw.ResponseAppearance.DESTRUCTIVE)
        
        def on_confirm(dialog, response):
            if response == "delete":
                # Close dialogs
                dialog.close()
                parent_dialog.close()
                
                # Check if we need sudo password
                mysql_info = service.get_mysql_status_info()
                if mysql_info.get('auth_method') == 'Unix Socket (sudo mysql)':
                    # Need sudo password
                    def on_password_provided(sudo_password):
                        self._show_toast(f"Deleting database '{db_name}'...")
                        
                        def delete_thread():
                            try:
                                success, message = service.drop_database(db_name, sudo_password=sudo_password)
                                
                                def update_ui():
                                    self._show_toast(message)
                                    if success and self.current_service and self.current_service.name == "mysql":
                                        self._refresh_detail_page()
                                
                                GLib.idle_add(update_ui)
                                    
                            except Exception as e:
                                def handle_error():
                                    self._show_toast(f"Error deleting database: {str(e)}")
                                
                                GLib.idle_add(handle_error)
                        
                        import threading
                        threading.Thread(target=delete_thread, daemon=True).start()
                    
                    self._show_sudo_password_dialog(on_password_provided)
                else:
                    # Use existing password
                    self._show_toast(f"Deleting database '{db_name}'...")
                    
                    def delete_thread():
                        try:
                            success, message = service.drop_database(db_name)
                            
                            def update_ui():
                                self._show_toast(message)
                                if success and self.current_service and self.current_service.name == "mysql":
                                    self._refresh_detail_page()
                            
                            GLib.idle_add(update_ui)
                                
                        except Exception as e:
                            def handle_error():
                                self._show_toast(f"Error deleting database: {str(e)}")
                            
                            GLib.idle_add(handle_error)
                    
                    import threading
                    threading.Thread(target=delete_thread, daemon=True).start()
        
        confirm_dialog.connect("response", on_confirm)
        confirm_dialog.present()
