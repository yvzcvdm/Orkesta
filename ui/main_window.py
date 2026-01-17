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
from utils.i18n import get_i18n

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
        menu_button.set_menu_model(self._create_menu())
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
    
    def _create_menu(self):
        """Create application menu"""
        menu = Gio.Menu()
        
        # About section
        about_section = Gio.Menu()
        about_section.append(_("About Orkesta"), "app.about")
        menu.append_section(None, about_section)
        
        # Create actions
        about_action = Gio.SimpleAction.new("about", None)
        about_action.connect("activate", self._on_about)
        self.get_application().add_action(about_action)
        
        return menu
    
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
        
        # İkon (büyük) - öncelikle service klasöründeki icon.svg'yi kullan
        icon_path = service.get_icon_path()  # BaseService.get_icon_path()
        if icon_path and os.path.exists(icon_path):
            icon = Gtk.Image.new_from_file(icon_path)
        else:
            # Fallback: GTK symbolic icon
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
            service = row.service
            self._show_service_detail(service)
    
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
        """
        Create service detail page
        
        Yeni modüler mimari: Her servis kendi UI'ını döndürür.
        """
        # Servis kendi detail view'ını döndürebilir mi?
        custom_view = service.get_detail_view(self)
        
        if custom_view is not None:
            # Servis kendi UI'ını sağladı
            return custom_view
        
        # Default view (BaseServiceView kullan)
        from ui.services.base_view import BaseServiceView
        view = BaseServiceView(service, self)
        return view.create_view()
    
    def _refresh_detail_page(self):
        """Detay sayfasını yenile (view refresh için)"""
        if self.current_service:
            detail_page = self._create_service_detail_page(self.current_service)
            
            # Eski detail page'i kaldır
            old_detail = self.main_stack.get_child_by_name("detail")
            if old_detail:
                self.main_stack.remove(old_detail)
            
            # Yeni detail page ekle
            self.main_stack.add_named(detail_page, "detail")
            self.main_stack.set_visible_child_name("detail")
    
    def _on_refresh_clicked(self, button):
        """Refresh button clicked"""
        self._load_services()
    
    # ==================== MENU HANDLERS ====================
    
    def _on_about(self, action, param):
        """Show about dialog"""
        about = Adw.AboutWindow()
        about.set_transient_for(self)
        about.set_application_name("Orkesta")
        about.set_application_icon("applications-development")
        about.set_version("1.0.0")
        about.set_developer_name("Orkesta Team")
        about.set_comments(_("Local Web Development Environment Manager"))
        about.set_website("https://github.com/orkesta/orkesta")
        about.set_license_type(Gtk.License.GPL_3_0)
        about.present()

