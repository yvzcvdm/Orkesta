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
        split_view.set_max_sidebar_width(250)
        split_view.set_min_sidebar_width(200)
        
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
        
        # Detay sayfası oluştur
        detail_page = self._create_service_detail_page(service)
        
        # Eski detay sayfasını kaldır (varsa)
        old_detail = self.main_stack.get_child_by_name("detail")
        if old_detail:
            self.main_stack.remove(old_detail)
        
        # Yeni detay sayfasını ekle
        self.main_stack.add_named(detail_page, "detail")
        
        # Detay sayfasına geç
        self.main_stack.set_visible_child_name("detail")
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
            
            # Root password display (if known)
            if mysql_info.get('root_access') and mysql_info.get('auth_method') != 'Unix Socket (sudo mysql)':
                password_display_row = Adw.ActionRow()
                password_display_row.set_title(_("Root Password"))
                password_text = mysql_info.get('root_password', 'Unknown')
                if password_text == 'Empty':
                    password_text = "(Empty)"
                password_display_label = Gtk.Label(label=password_text)
                password_display_label.add_css_class("monospace")
                password_display_row.add_suffix(password_display_label)
                mysql_info_group.add(password_display_row)
            
            # Version row
            version_row = Adw.ActionRow()
            version_row.set_title(_("MySQL Version"))
            version_label = Gtk.Label(label=mysql_info.get('version', 'Unknown'))
            version_label.add_css_class("monospace")
            version_row.add_suffix(version_label)
            mysql_info_group.add(version_row)
            
            # Database count
            db_count_row = Adw.ActionRow()
            db_count_row.set_title(_("Databases"))
            db_count_label = Gtk.Label(label=str(mysql_info.get('databases_count', 0)))
            db_count_label.add_css_class("monospace")
            db_count_row.add_suffix(db_count_label)
            mysql_info_group.add(db_count_row)
            
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
        mysql_actions_group = Adw.PreferencesGroup()
        mysql_actions_group.set_title(_("MySQL Management"))
        
        # Change root password
        password_row = Adw.ActionRow()
        password_row.set_title(_("Change Root Password"))
        password_row.set_subtitle(_("Set or change MySQL root password"))
        password_row.set_activatable(True)
        password_row.connect("activated", lambda r: self._on_mysql_change_password(service))
        password_icon = Gtk.Image.new_from_icon_name("dialog-password-symbolic")
        password_row.add_prefix(password_icon)
        mysql_actions_group.add(password_row)
        
        # Secure installation
        secure_row = Adw.ActionRow()
        secure_row.set_title(_("Secure Installation"))
        secure_row.set_subtitle(_("Run mysql_secure_installation"))
        secure_row.set_activatable(True)
        secure_row.connect("activated", lambda r: self._on_mysql_secure_installation(service))
        secure_icon = Gtk.Image.new_from_icon_name("security-high-symbolic")
        secure_row.add_prefix(secure_icon)
        mysql_actions_group.add(secure_row)
        
        # Create database
        create_db_row = Adw.ActionRow()
        create_db_row.set_title(_("Create Database"))
        create_db_row.set_subtitle(_("Create a new database"))
        create_db_row.set_activatable(True)
        create_db_row.connect("activated", lambda r: self._on_mysql_create_database(service))
        create_db_icon = Gtk.Image.new_from_icon_name("list-add-symbolic")
        create_db_row.add_prefix(create_db_icon)
        mysql_actions_group.add(create_db_row)
        
        # Create user
        create_user_row = Adw.ActionRow()
        create_user_row.set_title(_("Create User"))
        create_user_row.set_subtitle(_("Create a new MySQL user"))
        create_user_row.set_activatable(True)
        create_user_row.connect("activated", lambda r: self._on_mysql_create_user(service))
        create_user_icon = Gtk.Image.new_from_icon_name("system-users-symbolic")
        create_user_row.add_prefix(create_user_icon)
        mysql_actions_group.add(create_user_row)
        
        main_box.append(mysql_actions_group)
    
    def _on_mysql_change_password(self, service):
        """MySQL root password change dialog"""
        dialog = Adw.MessageDialog.new(self, _("Change MySQL Root Password"), None)
        dialog.set_body(_("Enter the current and new passwords for MySQL root user"))
        
        # Create form
        form_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        form_box.set_spacing(12)
        form_box.set_margin_top(12)
        
        # Current password
        current_label = Gtk.Label(label=_("Current Password (leave empty if none):"))
        current_label.set_halign(Gtk.Align.START)
        current_entry = Gtk.PasswordEntry()
        current_entry.set_property("placeholder-text", "Current password")
        
        # New password
        new_label = Gtk.Label(label=_("New Password:"))
        new_label.set_halign(Gtk.Align.START)
        new_entry = Gtk.PasswordEntry()
        new_entry.set_property("placeholder-text", "New password")
        
        # Confirm password
        confirm_label = Gtk.Label(label=_("Confirm New Password:"))
        confirm_label.set_halign(Gtk.Align.START)
        confirm_entry = Gtk.PasswordEntry()
        confirm_entry.set_property("placeholder-text", "Confirm new password")
        
        form_box.append(current_label)
        form_box.append(current_entry)
        form_box.append(new_label)
        form_box.append(new_entry)
        form_box.append(confirm_label)
        form_box.append(confirm_entry)
        
        dialog.set_extra_child(form_box)
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("change", _("Change Password"))
        dialog.set_response_appearance("change", Adw.ResponseAppearance.SUGGESTED)
        
        def on_response(dialog, response):
            if response == "change":
                current_password = current_entry.get_text()
                new_password = new_entry.get_text()
                confirm_password = confirm_entry.get_text()
                
                if not new_password:
                    self._show_toast(_("New password cannot be empty"))
                    return
                
                if new_password != confirm_password:
                    self._show_toast(_("Passwords do not match"))
                    return
                
                # Change password
                success, message = service.set_root_password(new_password, current_password)
                self._show_toast(message)
                
                if success:
                    dialog.close()
                    # Refresh detail page
                    if self.current_service and self.current_service.name == service.name:
                        self._refresh_detail_page()
        
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
                
                success, message = service.create_database(db_name)
                self._show_toast(message)
                
                if success:
                    dialog.close()
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
                
                success, message = service.create_user(username, password, host)
                self._show_toast(message)
                
                if success:
                    dialog.close()
                    # Refresh detail page
                    if self.current_service and self.current_service.name == service.name:
                        self._refresh_detail_page()
        
        dialog.connect("response", on_response)
        dialog.present()
    
    def _add_apache_sections(self, main_box, service):
        """Add Apache-specific sections to detail page"""
        
        # PHP Version Management
        php_group = Adw.PreferencesGroup()
        php_group.set_title(_("PHP Configuration"))
        
        try:
            php_versions = service.get_installed_php_versions()
            active_version = service.get_active_php_version()
            
            # Active PHP version row
            php_version_row = Adw.ActionRow()
            php_version_row.set_title(_("Active PHP Version"))
            if active_version:
                php_version_label = Gtk.Label(label=f"PHP {active_version}")
                php_version_label.add_css_class("monospace")
                php_version_row.add_suffix(php_version_label)
            else:
                php_version_label = Gtk.Label(label=_("Not detected"))
                php_version_label.add_css_class("dim-label")
                php_version_row.add_suffix(php_version_label)
            php_group.add(php_version_row)
            
            # Switch PHP version (if multiple versions available)
            if len(php_versions) > 1:
                switch_php_row = Adw.ActionRow()
                switch_php_row.set_title(_("Switch PHP Version"))
                switch_php_row.set_subtitle(_("Change the active PHP version for Apache"))
                switch_php_row.set_activatable(True)
                switch_php_row.connect("activated", lambda r: self._on_apache_switch_php(service, php_versions))
                switch_php_icon = Gtk.Image.new_from_icon_name("emblem-synchronizing-symbolic")
                switch_php_row.add_prefix(switch_php_icon)
                php_group.add(switch_php_row)
            elif php_versions:
                info_label = Gtk.Label()
                info_label.set_markup(f"<span size='small'>{_('Installed: ')} {', '.join(php_versions)}</span>")
                info_label.set_halign(Gtk.Align.START)
                info_label.set_margin_top(6)
                info_label.add_css_class("dim-label")
                # Add as a separate row
                info_row = Adw.ActionRow()
                info_row.set_title(_("Installed Versions"))
                info_row.set_subtitle(', '.join(f"PHP {v}" for v in php_versions))
                php_group.add(info_row)
        
        except Exception as e:
            logger.error(f"Error getting PHP info: {e}")
        
        main_box.append(php_group)
        
        # SSL Configuration
        ssl_group = Adw.PreferencesGroup()
        ssl_group.set_title(_("SSL/HTTPS Configuration"))
        
        try:
            ssl_enabled = service.is_ssl_module_enabled()
            
            # SSL status row
            ssl_status_row = Adw.ActionRow()
            ssl_status_row.set_title(_("SSL Module"))
            if ssl_enabled:
                ssl_status_label = Gtk.Label(label="✅ Enabled")
                ssl_status_label.add_css_class("success")
            else:
                ssl_status_label = Gtk.Label(label="❌ Disabled")
                ssl_status_label.add_css_class("error")
            ssl_status_row.add_suffix(ssl_status_label)
            ssl_group.add(ssl_status_row)
            
            if not ssl_enabled:
                # Enable SSL button
                enable_ssl_row = Adw.ActionRow()
                enable_ssl_row.set_title(_("Enable SSL Module"))
                enable_ssl_row.set_subtitle(_("Enable HTTPS support in Apache"))
                enable_ssl_row.set_activatable(True)
                enable_ssl_row.connect("activated", lambda r: self._on_apache_enable_ssl(service))
                enable_ssl_icon = Gtk.Image.new_from_icon_name("security-high-symbolic")
                enable_ssl_row.add_prefix(enable_ssl_icon)
                ssl_group.add(enable_ssl_row)
            else:
                # Create self-signed certificate button
                create_cert_row = Adw.ActionRow()
                create_cert_row.set_title(_("Create Self-Signed Certificate"))
                create_cert_row.set_subtitle(_("Generate SSL certificate for a domain"))
                create_cert_row.set_activatable(True)
                create_cert_row.connect("activated", lambda r: self._on_apache_create_certificate(service))
                create_cert_icon = Gtk.Image.new_from_icon_name("document-new-symbolic")
                create_cert_row.add_prefix(create_cert_icon)
                ssl_group.add(create_cert_row)
        
        except Exception as e:
            logger.error(f"Error getting SSL info: {e}")
        
        main_box.append(ssl_group)
        
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
                    
                    # Use filename as title if server_name not available
                    # Don't call get_vhost_details here to avoid blocking
                    title = vhost.get('server_name', vhost.get('filename', 'Unknown'))
                    if title.endswith('.conf'):
                        title = title[:-5]  # Remove .conf extension
                    
                    vhost_row.set_title(title)
                    
                    # Subtitle with basic info
                    subtitle_parts = []
                    if vhost.get('enabled'):
                        subtitle_parts.append("✅ Enabled")
                    else:
                        subtitle_parts.append("❌ Disabled")
                    
                    if vhost.get('filename'):
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
    
    def _on_apache_switch_php(self, service, versions):
        """Switch PHP version dialog"""
        dialog = Adw.MessageDialog.new(self, _("Switch PHP Version"), None)
        dialog.set_body(_("Select the PHP version to use with Apache"))
        
        # Create version selector
        list_box = Gtk.ListBox()
        list_box.set_selection_mode(Gtk.SelectionMode.SINGLE)
        list_box.add_css_class("boxed-list")
        
        active_version = service.get_active_php_version()
        selected_version = [active_version]  # Use list to allow modification in closure
        
        for version in versions:
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
            
            if version == active_version:
                check = Gtk.Image.new_from_icon_name("emblem-ok-symbolic")
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
                success, message = service.switch_php_version(selected_version[0])
                self._show_toast(message)
                if success:
                    dialog.close()
                    if self.current_service and self.current_service.name == service.name:
                        self._refresh_detail_page()
        
        dialog.connect("response", on_response)
        dialog.present()
    
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
        """Create virtual host dialog"""
        dialog = Adw.MessageDialog.new(self, _("Create Virtual Host"), None)
        dialog.set_body(_("Configure the new virtual host"))
        
        # Create form
        form_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        form_box.set_spacing(12)
        form_box.set_margin_top(12)
        
        # Server name
        servername_label = Gtk.Label(label=_("Server Name (domain):"))
        servername_label.set_halign(Gtk.Align.START)
        servername_entry = Gtk.Entry()
        servername_entry.set_property("placeholder-text", "example.local")
        
        # Document root
        docroot_label = Gtk.Label(label=_("Document Root:"))
        docroot_label.set_halign(Gtk.Align.START)
        docroot_entry = Gtk.Entry()
        docroot_entry.set_property("placeholder-text", "/var/www/example.local")
        
        # Port
        port_label = Gtk.Label(label=_("Port:"))
        port_label.set_halign(Gtk.Align.START)
        port_adjustment = Gtk.Adjustment(value=80, lower=1, upper=65535, step_increment=1)
        port_spin = Gtk.SpinButton(adjustment=port_adjustment)
        port_spin.set_digits(0)
        
        # SSL checkbox
        ssl_check = Gtk.CheckButton(label=_("Enable SSL (HTTPS)"))
        
        # PHP version selector
        php_label = Gtk.Label(label=_("PHP Version (optional):"))
        php_label.set_halign(Gtk.Align.START)
        
        php_versions = service.get_installed_php_versions()
        php_combo = Gtk.ComboBoxText()
        php_combo.append("", _("None"))
        for version in php_versions:
            php_combo.append(version, f"PHP {version}")
        php_combo.set_active(0)
        
        form_box.append(servername_label)
        form_box.append(servername_entry)
        form_box.append(docroot_label)
        form_box.append(docroot_entry)
        form_box.append(ssl_check)
        form_box.append(php_label)
        form_box.append(php_combo)
        
        dialog.set_extra_child(form_box)
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("create", _("Create"))
        dialog.set_response_appearance("create", Adw.ResponseAppearance.SUGGESTED)
        
        def on_response(dialog, response):
            if response == "create":
                server_name = servername_entry.get_text().strip()
                document_root = docroot_entry.get_text().strip()
                ssl = ssl_check.get_active()
                php_version = php_combo.get_active_id()
                
                if not server_name:
                    self._show_toast(_("Server name cannot be empty"))
                    return
                
                if not document_root:
                    document_root = f"/var/www/{server_name}"
                
                success, message = service.create_vhost(
                    server_name=server_name,
                    document_root=document_root,
                    ssl=ssl,
                    php_version=php_version if php_version else None
                )
                
                self._show_toast(message)
                
                if success:
                    dialog.close()
                    if self.current_service and self.current_service.name == service.name:
                        self._refresh_detail_page()
        
        dialog.connect("response", on_response)
        dialog.present()
    
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
        # Get detailed information if not already loaded
        if 'server_name' not in vhost or 'document_root' not in vhost:
            filename = vhost.get('filename', '')
            if not filename:
                self._show_toast(_("Invalid virtual host data"))
                return
            details = service.get_vhost_details(filename)
            if not details:
                self._show_toast(_("Could not load virtual host details"))
                return
        else:
            details = vhost
        
        # Create detail dialog
        dialog = Adw.Dialog()
        dialog.set_title(details['server_name'])
        
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
        name_label = Gtk.Label(label=details['server_name'])
        name_label.set_selectable(True)
        name_row.add_suffix(name_label)
        info_group.add(name_row)
        
        # Document root
        docroot_row = Adw.ActionRow()
        docroot_row.set_title(_("Document Root"))
        docroot_label = Gtk.Label(label=details['document_root'] or "N/A")
        docroot_label.set_selectable(True)
        docroot_row.add_suffix(docroot_label)
        info_group.add(docroot_row)
        
        # SSL status
        ssl_row = Adw.ActionRow()
        ssl_row.set_title(_("SSL/HTTPS"))
        if details['ssl_enabled']:
            ssl_label = Gtk.Label(label="✅ Enabled")
            ssl_label.add_css_class("success")
        else:
            ssl_label = Gtk.Label(label="❌ Disabled")
        ssl_row.add_suffix(ssl_label)
        info_group.add(ssl_row)
        
        # PHP version
        php_row = Adw.ActionRow()
        php_row.set_title(_("PHP Version"))
        if details['php_version']:
            php_label = Gtk.Label(label=f"PHP {details['php_version']}")
        else:
            php_label = Gtk.Label(label=_("Not configured"))
        php_row.add_suffix(php_label)
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
        browse_row.set_subtitle(f"http://{details['server_name']}/")
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
        dialog = Adw.MessageDialog.new(parent_dialog, _("Change PHP Version"), None)
        dialog.set_body(_("Select the PHP version for {name}").format(name=details['server_name']))
        
        # Version selector
        list_box = Gtk.ListBox()
        list_box.set_selection_mode(Gtk.SelectionMode.SINGLE)
        list_box.add_css_class("boxed-list")
        
        selected_version = [details['php_version']]
        
        for version in versions:
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
            
            if version == details['php_version']:
                check = Gtk.Image.new_from_icon_name("emblem-ok-symbolic")
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
        dialog.add_response("change", _("Change"))
        dialog.set_response_appearance("change", Adw.ResponseAppearance.SUGGESTED)
        
        def on_response(dialog, response):
            if response == "change" and selected_version[0]:
                success, message = service.update_vhost_php_version(details['filename'], selected_version[0])
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
        url = f"http://{details['server_name']}/"
        try:
            subprocess.Popen(['xdg-open', url])
        except Exception as e:
            logger.error(f"Error opening browser: {e}")
            self._show_toast(_("Could not open browser"))
    
    def _on_vhost_delete_confirm(self, service, details, parent_dialog):
        """Confirm and delete virtual host"""
        dialog = Adw.MessageDialog.new(parent_dialog)
        dialog.set_heading(_("Delete {name}?").format(name=details['server_name']))
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
