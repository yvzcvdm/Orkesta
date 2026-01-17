"""
Base Service Class

Prensip: Servisler SADECE script'leri çağırır, işlem yapmaz!
Script-First Approach: Her işlem için ayrı script var.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, List, Tuple, Any
from enum import Enum
import logging
import subprocess
import os

logger = logging.getLogger(__name__)

try:
    from src.utils.i18n import get_i18n
    _ = get_i18n().get_translator()
except:
    _ = lambda s: s

# Script dizini
SCRIPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'scripts')


class ServiceStatus(Enum):
    RUNNING = "running"
    STOPPED = "stopped"
    UNKNOWN = "unknown"
    NOT_INSTALLED = "not_installed"


class ServiceType(Enum):
    WEB_SERVER = "web_server"
    DATABASE = "database"
    CACHE = "cache"
    OTHER = "other"


class BaseService(ABC):
    """
    Ultra-minimal Base Service Class
    
    Servisler SADECE script'leri çağırır!
    Tüm bilgiler ve iş mantığı script'lerde.
    """
    
    def __init__(self, platform_manager):
        self.platform_manager = platform_manager
        self._status = ServiceStatus.UNKNOWN
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Service name (tek zorunlu property)"""
        pass
    
    # Optional properties with defaults (UI compatibility)
    @property
    def display_name(self) -> str:
        """Display name for UI (default: capitalized name)"""
        return self.name.upper()
    
    @property
    def description(self) -> str:
        """Service description (optional)"""
        return f"{self.display_name} service"
    
    @property
    def icon_name(self) -> str:
        """Icon name (optional)"""
        return "application-x-executable"
    
    @property
    def service_type(self) -> ServiceType:
        """Service type (optional, default: OTHER)"""
        return ServiceType.OTHER
    
    @property
    def default_port(self) -> Optional[int]:
        """Default port for the service (optional)"""
        return None
    
    @property
    def can_uninstall(self) -> bool:
        """Can this service be uninstalled? (default: True)"""
        return True
    
    def get_status(self) -> ServiceStatus:
        if not self.is_installed():
            return ServiceStatus.NOT_INSTALLED
        elif self.is_running():
            return ServiceStatus.RUNNING
        else:
            return ServiceStatus.STOPPED
    
    @abstractmethod
    def is_installed(self) -> bool:
        pass
    
    @abstractmethod
    def install(self) -> Tuple[bool, str]:
        pass
    
    @abstractmethod
    def uninstall(self) -> Tuple[bool, str]:
        pass
    
    @abstractmethod
    def start(self) -> Tuple[bool, str]:
        pass
    
    @abstractmethod
    def stop(self) -> Tuple[bool, str]:
        pass
    
    @abstractmethod
    def restart(self) -> Tuple[bool, str]:
        pass
    
    @abstractmethod
    def is_running(self) -> bool:
        pass
    
    @abstractmethod
    def enable(self) -> Tuple[bool, str]:
        pass
    
    @abstractmethod
    def disable(self) -> Tuple[bool, str]:
        pass
    
    # ============================================
    # UI METHODS - Service-Specific Views
    # ============================================
    
    def get_detail_view(self, main_window) -> Optional[Any]:
        """
        Servisin detay görünümünü döndürür.
        Her servis kendi UI'ını buradan döndürebilir.
        
        Args:
            main_window: MainWindow instance (callbacks için)
        
        Returns:
            Gtk.Widget veya None (default view kullanılacak)
        """
        return None  # Default: BaseServiceView kullanılacak
    
    # ============================================
    # HELPER METHODS - Script Execution
    # ============================================
    
    def _execute_script(self, script_path: str, *args, timeout: int = 300) -> Tuple[bool, str]:
        """
        Script çalıştır (CLI-First yaklaşımı)
        
        Yeni modüler yapı: Script servisin kendi klasöründe.
        Örnek: services/apache/apache.sh
        
        Args:
            script_path: Script adı (örn: 'apache.sh')
            args: Script parametreleri
            timeout: Timeout (saniye)
        
        Returns:
            (success: bool, message: str)
        """
        # Script tam yolu - servisle aynı klasörde
        if not os.path.isabs(script_path):
            # Servisin bulunduğu modül klasörünü bul
            import inspect
            service_file = inspect.getfile(self.__class__)
            service_dir = os.path.dirname(service_file)
            script_path = os.path.join(service_dir, script_path)
        
        # Script var mı kontrol et
        if not os.path.exists(script_path):
            logger.error(f"Script bulunamadı: {script_path}")
            return False, _("Script file not found: {path}").format(path=script_path)
        
        # Read-only komutlar - sudo gerektirmez
        # NOT: /etc/hosts okumak bile sudo gerektirebilir, bu yüzden hosts komutları sudo ile çalışır
        readonly_commands = [
            'is-installed', 'is-running', 'version-get-active', 
            'version-list-installed', 'version-list-available',
            'extension-list',
            'database-list', 'user-list',
            'php-get-active', 'php-list-versions', 'ssl-is-enabled',
            'get-version', 'log-tail', 'log-view',
            'vhost-list', 'vhost-details',
            'module-list', 'status-info', 'check-root-password',
            'info', 'extension-list-installed',
            # Hosts file - /etc/hosts okumak bile sudo gerektirir
            # 'list', 'exists', 'validate'  # Bu komutlar sudo ile çalışacak
        ]
        
        # İlk argüman read-only komut mu?
        needs_sudo = True
        if args and args[0] in readonly_commands:
            needs_sudo = False
        
        # Komutu oluştur
        cmd = []
        if needs_sudo:
            # sudo kullan - başlangıçta cache'lenmiş olacak
            cmd.append('sudo')
        
        cmd.append(script_path)
        cmd.extend(args)
        
        logger.info(f"Script çalıştırılıyor: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout,
                text=True
            )
            
            if result.returncode == 0:
                message = result.stdout.strip() or _("Operation completed successfully")
                logger.info(f"Script başarılı: {script_path}")
                return True, message
            else:
                error = result.stderr.strip() or result.stdout.strip() or _("Unknown error")
                logger.error(f"Script hatası ({script_path}): {error}")
                
                # PolicyKit cancelled check
                if "cancelled" in error.lower() or "authentication failed" in error.lower():
                    return False, _("Authentication cancelled or failed")
                
                return False, error
        
        except subprocess.TimeoutExpired:
            logger.error(f"Script timeout: {script_path}")
            return False, _("Operation timed out")
        
        except Exception as e:
            logger.error(f"Script execution error: {e}")
            return False, str(e)
