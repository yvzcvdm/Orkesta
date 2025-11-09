"""
Apache HTTP Server Module

Service management module for Apache web server.
"""

from typing import Dict, List, Optional, Any, Tuple
from services.base_service import BaseService, ServiceType
import logging

logger = logging.getLogger(__name__)

# Import i18n
try:
    from src.utils.i18n import get_i18n
    _ = get_i18n().get_translator()
except:
    _ = lambda s: s


class ApacheService(BaseService):
    """Apache HTTP Server - Script-First Service Interface"""
    
    SCRIPT_NAME = 'apache.sh'
    
    @property
    def name(self) -> str:
        return "apache"
    
    @property
    def display_name(self) -> str:
        return "Apache"
    
    @property
    def description(self) -> str:
        return _("Apache HTTP Server - Web server for hosting websites")
    
    @property
    def icon_name(self) -> str:
        return "network-server"
    
    @property
    def service_type(self) -> ServiceType:
        return ServiceType.WEB_SERVER
    
    @property
    def default_port(self) -> Optional[int]:
        return 80
    
    def is_installed(self) -> bool:
        """Check if installed via script"""
        success, output = self._execute_script(self.SCRIPT_NAME, 'is-installed', timeout=10)
        return success and output.strip().lower() == 'true'
    
    def install(self) -> Tuple[bool, str]:
        return self._execute_script(self.SCRIPT_NAME, 'install', timeout=600)
    
    def uninstall(self) -> Tuple[bool, str]:
        return self._execute_script(self.SCRIPT_NAME, 'uninstall', timeout=600)
    
    def start(self) -> Tuple[bool, str]:
        return self._execute_script(self.SCRIPT_NAME, 'start', timeout=30)
    
    def stop(self) -> Tuple[bool, str]:
        return self._execute_script(self.SCRIPT_NAME, 'stop', timeout=30)
    
    def restart(self) -> Tuple[bool, str]:
        return self._execute_script(self.SCRIPT_NAME, 'restart', timeout=30)
    
    def is_running(self) -> bool:
        success, output = self._execute_script(self.SCRIPT_NAME, 'is-running', timeout=10)
        return success and output.strip().lower() == 'true'
    
    def enable(self) -> Tuple[bool, str]:
        return self._execute_script(self.SCRIPT_NAME, 'enable', timeout=30)
    
    def disable(self) -> Tuple[bool, str]:
        return self._execute_script(self.SCRIPT_NAME, 'disable', timeout=30)
    
    # ==================== VHOST MANAGEMENT ====================
    
    def list_vhosts(self) -> List[Dict[str, Any]]:
        success, output = self._execute_script(self.SCRIPT_NAME, 'vhost-list', '--json', timeout=30)
        if not success:
            return []
        try:
            import json
            return json.loads(output)
        except:
            return []
    
    def create_vhost(self, server_name: str, document_root: str, 
                     ssl: bool = False, ssl_cert: Optional[str] = None, 
                     ssl_key: Optional[str] = None, php_version: Optional[str] = None) -> Tuple[bool, str]:
        args = ['vhost-create', server_name, document_root]
        if ssl:
            args.append('--ssl')
        if ssl_cert:
            args.extend(['--ssl-cert', ssl_cert])
        if ssl_key:
            args.extend(['--ssl-key', ssl_key])
        if php_version:
            args.extend(['--php-version', php_version])
        return self._execute_script(self.SCRIPT_NAME, *args, timeout=300)
    
    def enable_vhost(self, filename: str) -> Tuple[bool, str]:
        return self._execute_script(self.SCRIPT_NAME, 'vhost-enable', filename, timeout=30)
    
    def disable_vhost(self, filename: str) -> Tuple[bool, str]:
        return self._execute_script(self.SCRIPT_NAME, 'vhost-disable', filename, timeout=30)
    
    def delete_vhost(self, filename: str) -> Tuple[bool, str]:
        return self._execute_script(self.SCRIPT_NAME, 'vhost-delete', filename, timeout=30)
    
    def get_vhost_details(self, filename: str) -> Optional[Dict[str, Any]]:
        success, output = self._execute_script(self.SCRIPT_NAME, 'vhost-details', filename, '--json', timeout=30)
        if not success:
            return None
        try:
            import json
            return json.loads(output)
        except:
            return None
    
    def update_vhost_php_version(self, filename: str, php_version: str) -> Tuple[bool, str]:
        return self._execute_script(self.SCRIPT_NAME, 'vhost-update-php', filename, php_version, timeout=60)
    
    def reload_config(self) -> Tuple[bool, str]:
        return self._execute_script(self.SCRIPT_NAME, 'reload', timeout=30)
    
    # ==================== PHP VERSION MANAGEMENT ====================
    
    def get_installed_php_versions(self) -> List[str]:
        success, output = self._execute_script(self.SCRIPT_NAME, 'php-list-versions', '--json', timeout=30)
        if not success:
            return []
        try:
            import json
            return json.loads(output)
        except:
            return []
    
    def get_active_php_version(self) -> Optional[str]:
        success, output = self._execute_script(self.SCRIPT_NAME, 'php-get-active', timeout=30)
        return output.strip() if success else None
    
    def switch_php_version(self, version: str) -> Tuple[bool, str]:
        return self._execute_script(self.SCRIPT_NAME, 'php-switch', version, timeout=60)
    
    # ==================== SSL MANAGEMENT ====================
    
    def is_ssl_module_enabled(self) -> bool:
        success, output = self._execute_script(self.SCRIPT_NAME, 'ssl-is-enabled', timeout=30)
        return success and output.strip().lower() == 'true'
    
    def enable_ssl_module(self) -> Tuple[bool, str]:
        return self._execute_script(self.SCRIPT_NAME, 'ssl-enable', timeout=120)
    
    def create_self_signed_certificate(self, domain: str, 
                                       cert_path: Optional[str] = None,
                                       key_path: Optional[str] = None) -> Tuple[bool, str, Dict[str, str]]:
        args = ['ssl-create-cert', domain]
        if cert_path:
            args.extend(['--cert-path', cert_path])
        if key_path:
            args.extend(['--key-path', key_path])
        success, message = self._execute_script(self.SCRIPT_NAME, *args, timeout=60)
        
        cert_info = {}
        if success:
            cert_info = {
                'cert_path': cert_path or f"/etc/ssl/certs/{domain}.crt",
                'key_path': key_path or f"/etc/ssl/private/{domain}.key"
            }
        return success, message, cert_info
