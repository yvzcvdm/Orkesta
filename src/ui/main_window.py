"""
Ana Pencere - Main Window

GTK4/Libadwaita tabanlı ana uygulama penceresi.
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gio
import logging
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
    
    def _create_content_area(self):
        """DEPRECATED - use _create_service_list_page"""
        return self._create_service_list_page()
    
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
        dialog.set_body(_("This will install {service} and its dependencies. Administrator password will be required.").format(service=service.display_name))
        
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("install", _("Install"))
        dialog.set_response_appearance("install", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_default_response("install")
        dialog.set_close_response("cancel")
        
        def on_response(dialog, response):
            if response == "install":
                self._show_loading_dialog(_("Installing {service}...").format(service=service.display_name))
                
                def install_thread():
                    try:
                        success, message = service.install()
                        GLib.idle_add(self._on_operation_complete, success, message)
                    except Exception as e:
                        logger.error(f"Install thread error: {e}")
                        GLib.idle_add(self._on_operation_complete, False, str(e))
                
                import threading
                thread = threading.Thread(target=install_thread, daemon=True)
                thread.start()
        
        dialog.connect("response", on_response)
        dialog.present()
    
    def _on_service_uninstall(self, service):
        """Uninstall service"""
        # Onay dialog'u göster
        dialog = Adw.MessageDialog.new(self)
        dialog.set_heading(_("Uninstall {service}?").format(service=service.display_name))
        dialog.set_body(_("This will remove {service} from your system. Administrator password will be required.").format(service=service.display_name))
        
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("uninstall", _("Uninstall"))
        dialog.set_response_appearance("uninstall", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_default_response("cancel")
        dialog.set_close_response("cancel")
        
        def on_response(dialog, response):
            if response == "uninstall":
                self._show_loading_dialog(_("Uninstalling {service}...").format(service=service.display_name))
                
                def uninstall_thread():
                    try:
                        success, message = service.uninstall()
                        GLib.idle_add(self._on_operation_complete, success, message)
                    except Exception as e:
                        logger.error(f"Uninstall thread error: {e}")
                        GLib.idle_add(self._on_operation_complete, False, str(e))
                
                import threading
                thread = threading.Thread(target=uninstall_thread, daemon=True)
                thread.start()
        
        dialog.connect("response", on_response)
        dialog.present()
    
    def _on_service_start(self, service):
        """Start service"""
        success, message = service.start()
        self._show_toast(message)
        self._load_services()
    
    def _on_service_stop(self, service):
        """Stop service"""
        success, message = service.stop()
        self._show_toast(message)
        self._load_services()
    
    def _on_service_restart(self, service):
        """Restart service"""
        success, message = service.restart()
        self._show_toast(message)
        self._load_services()
    
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
                GLib.source_remove(self.progress_timeout_id)
                self.progress_timeout_id = None
            
            # Progress bar referansını temizle
            if hasattr(self, 'progress_bar'):
                self.progress_bar = None
            
            # Dialog'u kapat
            if hasattr(self, 'progress_dialog') and self.progress_dialog:
                self.progress_dialog.close()
                self.progress_dialog = None
            
            # Toast göster ve servisleri yenile
            self._show_toast(message)
            
            # Servisleri yeniden yükle
            try:
                self._load_services()
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
                    self._show_service_detail(service)
        
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
                    self._show_service_detail(service)
        
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
        
        dialog.connect("response", on_response)
        dialog.present()
    
    def _on_refresh_clicked(self, button):
        """Refresh button clicked"""
        self._load_services()
