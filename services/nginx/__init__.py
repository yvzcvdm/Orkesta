"""
Nginx Service - Test Plugin

Bu bir test plugin'idir. Sadece metadata.json ekleyerek
otomatik yüklendiğini gösterir.
"""

from services.base_service import BaseService, ServiceStatus, ServiceType
from typing import Tuple
import logging

logger = logging.getLogger(__name__)

# Import standalone i18n (bağımsız)
try:
    from .i18n import get_i18n
    _ = get_i18n().get_translator()
except:
    _ = lambda s: s


class NginxService(BaseService):
    """Nginx Web Server - Test Plugin"""
    
    SCRIPT_NAME = 'nginx.sh'
    
    @property
    def name(self) -> str:
        return "nginx"
    
    @property
    def service_type(self) -> ServiceType:
        return ServiceType.WEB_SERVER
    
    def is_installed(self) -> bool:
        """Nginx yüklü mü? (test için basit kontrol)"""
        import subprocess
        try:
            result = subprocess.run(['which', 'nginx'], 
                                   capture_output=True, 
                                   text=True, 
                                   timeout=5)
            return result.returncode == 0
        except:
            return False
    
    def get_status(self) -> ServiceStatus:
        """Service durumu"""
        if not self.is_installed():
            return ServiceStatus.NOT_INSTALLED
        return ServiceStatus.UNKNOWN  # Test plugin, detaylı status yok
    
    def install(self) -> Tuple[bool, str]:
        """Yükleme (test - gerçek işlem yapmaz)"""
        logger.info("🧪 Test Plugin: Nginx install çağrıldı (gerçek işlem yapmaz)")
        return False, "Bu bir test plugin'idir - gerçek yükleme yapmaz"
    
    def uninstall(self) -> Tuple[bool, str]:
        """Kaldırma (test - gerçek işlem yapmaz)"""
        return False, "Bu bir test plugin'idir"
    
    def start(self) -> Tuple[bool, str]:
        """Başlatma (test)"""
        return False, "Test plugin"
    
    def stop(self) -> Tuple[bool, str]:
        """Durdurma (test)"""
        return False, "Test plugin"
    
    def restart(self) -> Tuple[bool, str]:
        """Yeniden başlatma (test)"""
        return False, "Test plugin"
