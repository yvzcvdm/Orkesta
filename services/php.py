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
    
    # ==================== ADDITIONAL METHODS ====================
    
    def get_php_info(self) -> Dict[str, Any]:
        """Get comprehensive PHP information"""
        success, output = self._execute_script(self.SCRIPT_NAME, 'info', '--json', timeout=30)
        if not success:
            return {
                'installed': self.is_installed(),
                'running': self.is_running(),
                'active_version': self.get_active_version(),
                'installed_versions': self.get_installed_versions(),
                'available_versions': self.get_available_versions()
            }
        try:
            import json
            return json.loads(output)
        except:
            return {
                'installed': self.is_installed(),
                'running': self.is_running(),
                'active_version': self.get_active_version(),
                'installed_versions': self.get_installed_versions(),
                'available_versions': self.get_available_versions()
            }
    
    def get_config_info(self, version: Optional[str] = None) -> Dict[str, Any]:
        """Get PHP configuration information"""
        args = ['config-show']
        if version:
            args.extend(['--version', version])
        
        success, output = self._execute_script(self.SCRIPT_NAME, *args, timeout=30)
        if not success:
            return {}
        
        # Parse the output to extract configuration info
        config_info = {}
        for line in output.strip().split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower().replace(' ', '_')
                value = value.strip()
                if key.startswith('config_file'):
                    config_info['config_file'] = value
                elif key.startswith('extension_dir'):
                    config_info['extension_dir'] = value.lstrip('> ')
                elif key.startswith('memory_limit'):
                    config_info['memory_limit'] = value
                elif key.startswith('max_execution_time'):
                    config_info['max_execution_time'] = value
                elif key.startswith('upload_max_size'):
                    config_info['upload_max_size'] = value
        
        return config_info
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get detailed service status including versions and extensions"""
        info = self.get_php_info()
        active_version = info.get('active_version')
        
        status = {
            'service_name': 'PHP',
            'installed': info.get('installed', False),
            'running': info.get('running', False),
            'active_version': active_version,
            'installed_versions': info.get('installed_versions', []),
            'available_versions': info.get('available_versions', []),
        }
        
        # Add configuration info for active version
        if active_version:
            status['config'] = self.get_config_info(active_version)
            status['extensions'] = self.get_installed_extensions(active_version)
        
        return status
    
    def validate_version(self, version: str) -> bool:
        """Validate if version is available for installation"""
        available_versions = self.get_available_versions()
        return version in available_versions
    
    def validate_extension(self, extension: str) -> bool:
        """Basic extension name validation"""
        # Basic validation - extension name should be alphanumeric with possible dash/underscore
        return bool(re.match(r'^[a-zA-Z0-9_-]+$', extension))
    
    def get_popular_extensions(self) -> List[str]:
        """Get list of popular PHP extensions"""
        return [
            'mbstring', 'xml', 'gd', 'curl', 'zip', 'json',
            'mysql', 'mysqli', 'pdo_mysql', 'sqlite3', 'pdo_sqlite',
            'redis', 'memcached', 'imagick', 'intl', 'bcmath',
            'opcache', 'xdebug', 'soap', 'xmlrpc', 'ldap',
            'fileinfo', 'exif', 'gettext', 'iconv', 'openssl'
        ]
    
    def bulk_install_extensions(self, extensions: List[str], version: Optional[str] = None) -> Dict[str, Tuple[bool, str]]:
        """Install multiple extensions at once"""
        results = {}
        for extension in extensions:
            if self.validate_extension(extension):
                success, message = self.install_extension(extension, version)
                results[extension] = (success, message)
            else:
                results[extension] = (False, f"Invalid extension name: {extension}")
        return results
