"""
PHP Service Module

Service management module for PHP with version and extension management.
"""

from typing import Dict, List, Optional, Any, Tuple
from services.base_service import BaseService, ServiceType
import subprocess
import re
import logging

logger = logging.getLogger(__name__)

# Import i18n
try:
    from src.utils.i18n import get_i18n
    _ = get_i18n().get_translator()
except:
    _ = lambda s: s


class PHPService(BaseService):
    """PHP service management with multi-version support"""
    
    SCRIPT_NAME = 'php.sh'
    
    @property
    def name(self) -> str:
        return "php"
    
    @property
    def display_name(self) -> str:
        return "PHP"
    
    @property
    def description(self) -> str:
        return _("PHP - Server-side scripting language for web development")
    
    @property
    def icon_name(self) -> str:
        return "text-x-script"
    
    @property
    def service_type(self) -> ServiceType:
        return ServiceType.OTHER
    
    @property
    def default_port(self) -> Optional[int]:
        return None  # PHP doesn't have a default port
    
    # ==================== VERSION MANAGEMENT ====================
    
    def get_installed_versions(self) -> List[str]:
        """Get list of installed PHP versions"""
        success, output = self._execute_script(self.SCRIPT_NAME, 'version-list-installed', '--json', timeout=30)
        if not success:
            return []
        try:
            import json
            return json.loads(output)
        except:
            return []
    
    def get_available_versions(self) -> List[str]:
        """Get list of available PHP versions"""
        success, output = self._execute_script(self.SCRIPT_NAME, 'version-list-available', '--json', timeout=30)
        if not success:
            return ['7.4', '8.0', '8.1', '8.2', '8.3']
        try:
            import json
            return json.loads(output)
        except:
            return ['7.4', '8.0', '8.1', '8.2', '8.3']
    
    def get_active_version(self) -> Optional[str]:
        """Get active PHP version"""
        success, output = self._execute_script(self.SCRIPT_NAME, 'version-get-active', timeout=10)
        return output.strip() if success and output.strip() else None
    
    def install_version(self, version: str) -> Tuple[bool, str]:
        """Install specific PHP version"""
        return self._execute_script(self.SCRIPT_NAME, 'version-install', version, timeout=900)
    
    def uninstall_version(self, version: str) -> Tuple[bool, str]:
        """Uninstall specific PHP version"""
        return self._execute_script(self.SCRIPT_NAME, 'version-uninstall', version, timeout=600)
    
    def switch_version(self, version: str) -> Tuple[bool, str]:
        """Switch active PHP version"""
        return self._execute_script(self.SCRIPT_NAME, 'version-switch', version, timeout=60)
    
    # ==================== EXTENSION MANAGEMENT ====================
    
    def get_installed_extensions(self, version: Optional[str] = None) -> List[str]:
        """Get list of installed PHP extensions"""
        args = ['extension-list', '--json']
        if version:
            args.extend(['--version', version])
        success, output = self._execute_script(self.SCRIPT_NAME, *args, timeout=30)
        if not success:
            return []
        try:
            import json
            return json.loads(output)
        except:
            return []
    
    def install_extension(self, extension: str, version: Optional[str] = None) -> Tuple[bool, str]:
        """Install PHP extension"""
        args = ['extension-install', extension]
        if version:
            args.extend(['--version', version])
        return self._execute_script(self.SCRIPT_NAME, *args, timeout=300)
    
    def uninstall_extension(self, extension: str, version: Optional[str] = None) -> Tuple[bool, str]:
        """Uninstall PHP extension"""
        args = ['extension-uninstall', extension]
        if version:
            args.extend(['--version', version])
        return self._execute_script(self.SCRIPT_NAME, *args, timeout=300)
    
    # ==================== BASE SERVICE IMPLEMENTATION ====================
    
    def is_installed(self) -> bool:
        """Check if any PHP version is installed"""
        success, output = self._execute_script(self.SCRIPT_NAME, 'is-installed', timeout=10)
        return success and output.strip().lower() == 'true'
    
    def install(self) -> Tuple[bool, str]:
        """Install default PHP version (8.2)"""
        return self._execute_script(self.SCRIPT_NAME, 'install', timeout=900)
    
    def uninstall(self) -> Tuple[bool, str]:
        """Uninstall all PHP versions"""
        return self._execute_script(self.SCRIPT_NAME, 'uninstall', timeout=600)
    
    def start(self) -> Tuple[bool, str]:
        """Start PHP-FPM service"""
        return self._execute_script(self.SCRIPT_NAME, 'start', timeout=30)
    
    def stop(self) -> Tuple[bool, str]:
        """Stop PHP-FPM service"""
        return self._execute_script(self.SCRIPT_NAME, 'stop', timeout=30)
    
    def restart(self) -> Tuple[bool, str]:
        """Restart PHP-FPM service"""
        return self._execute_script(self.SCRIPT_NAME, 'restart', timeout=30)
    
    def is_running(self) -> bool:
        """Check if PHP-FPM is running"""
        success, output = self._execute_script(self.SCRIPT_NAME, 'is-running', timeout=10)
        return success and output.strip().lower() == 'true'
    
    def enable(self) -> Tuple[bool, str]:
        """Enable PHP-FPM autostart"""
        return self._execute_script(self.SCRIPT_NAME, 'enable', timeout=30)
    
    def disable(self) -> Tuple[bool, str]:
        """Disable PHP-FPM autostart"""
        return self._execute_script(self.SCRIPT_NAME, 'disable', timeout=30)
