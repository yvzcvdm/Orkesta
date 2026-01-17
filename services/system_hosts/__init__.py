"""
System Hosts File Manager Service

Service for managing /etc/hosts file entries for local domain mapping.
"""

from typing import List, Dict, Any, Tuple, Optional
from services.base_service import BaseService, ServiceType
import logging

logger = logging.getLogger(__name__)

# Import i18n
try:
    from src.utils.i18n import get_i18n
    _ = get_i18n().get_translator()
except:
    _ = lambda s: s


class SystemHostsService(BaseService):
    """System Hosts File Manager - /etc/hosts management"""
    
    # Script bu klasörde (services/system_hosts/hosts.sh)
    SCRIPT_NAME = 'hosts.sh'
    
    @property
    def name(self) -> str:
        return "system_hosts"
    
    @property
    def display_name(self) -> str:
        return "Hosts Manager"
    
    @property
    def description(self) -> str:
        return _("Manage /etc/hosts file for local domain mapping")
    
    @property
    def icon_name(self) -> str:
        return "network-server-symbolic"
    
    @property
    def service_type(self) -> ServiceType:
        return ServiceType.OTHER
    
    @property
    def can_uninstall(self) -> bool:
        """Hosts file cannot be uninstalled"""
        return False
    
    # ==================== UI INTEGRATION ====================
    
    def get_detail_view(self, main_window) -> Optional[Any]:
        """Servise özel UI döndür"""
        from services.system_hosts.ui import SystemHostsView
        view = SystemHostsView(self, main_window)
        return view.create_view()
    
    # ==================== REQUIRED BASE SERVICE METHODS ====================
    
    def is_installed(self) -> bool:
        """Hosts file always exists on Linux systems"""
        return True
    
    def install(self) -> Tuple[bool, str]:
        """Not applicable for hosts file"""
        return True, _("Hosts file is a system component")
    
    def uninstall(self) -> Tuple[bool, str]:
        """Not applicable for hosts file"""
        return False, _("Cannot uninstall system hosts file")
    
    def start(self) -> Tuple[bool, str]:
        """Not applicable for hosts file"""
        return True, _("Hosts file is always active")
    
    def stop(self) -> Tuple[bool, str]:
        """Not applicable for hosts file"""
        return False, _("Cannot stop hosts file")
    
    def restart(self) -> Tuple[bool, str]:
        """Not applicable for hosts file"""
        return True, _("Hosts file changes take effect immediately")
    
    def is_running(self) -> bool:
        """Hosts file is always active"""
        return True
    
    def enable(self) -> Tuple[bool, str]:
        """Not applicable for hosts file"""
        return True, _("Hosts file is always enabled")
    
    def disable(self) -> Tuple[bool, str]:
        """Not applicable for hosts file"""
        return False, _("Cannot disable hosts file")
    
    # NOT: is_service = False olarak işaretle ki UI'da start/stop butonları gösterilmesin
    @property
    def is_service(self) -> bool:
        """Hosts file is not a system service"""
        return False
    
    # ==================== HOSTS FILE MANAGEMENT ====================
    
    def list_entries(self) -> List[Dict[str, str]]:
        """
        List all Orkesta-managed hosts entries
        
        Returns:
            List of dicts with 'ip' and 'domain' keys
        """
        success, output = self._execute_script(self.SCRIPT_NAME, 'list', '--json', timeout=10)
        if not success:
            logger.warning(f"Failed to list hosts entries: {output}")
            return []
        
        try:
            import json
            entries = json.loads(output)
            return entries if entries else []
        except Exception as e:
            logger.error(f"Failed to parse hosts entries JSON: {e}")
            return []
    
    def add_entry(self, ip: str, domain: str) -> Tuple[bool, str]:
        """
        Add new hosts entry
        
        Args:
            ip: IP address (IPv4 or IPv6)
            domain: Domain name
        
        Returns:
            (success, message)
        """
        if not ip or not domain:
            return False, _("IP and domain are required")
        
        # Validate IP format first
        valid, _ = self._execute_script(self.SCRIPT_NAME, 'validate', ip, timeout=5)
        if not valid:
            return False, _("Invalid IP address format: {ip}").format(ip=ip)
        
        # Add entry
        return self._execute_script(self.SCRIPT_NAME, 'add', ip, domain, timeout=10)
    
    def remove_entry(self, domain: str) -> Tuple[bool, str]:
        """
        Remove hosts entry by domain
        
        Args:
            domain: Domain name to remove
        
        Returns:
            (success, message)
        """
        if not domain:
            return False, _("Domain is required")
        
        return self._execute_script(self.SCRIPT_NAME, 'remove', domain, timeout=10)
    
    def entry_exists(self, domain: str) -> bool:
        """
        Check if domain exists in hosts file
        
        Args:
            domain: Domain name to check
        
        Returns:
            True if domain exists
        """
        if not domain:
            return False
        
        success, output = self._execute_script(self.SCRIPT_NAME, 'exists', domain, timeout=5)
        return success and output.strip().lower() == 'true'
    
    def backup(self) -> Tuple[bool, str]:
        """
        Backup hosts file
        
        Returns:
            (success, message)
        """
        return self._execute_script(self.SCRIPT_NAME, 'backup', timeout=10)
    
    def restore(self) -> Tuple[bool, str]:
        """
        Restore hosts file from backup
        
        Returns:
            (success, message)
        """
        return self._execute_script(self.SCRIPT_NAME, 'restore', timeout=10)
    
    def validate_ip(self, ip: str) -> bool:
        """
        Validate IP address format
        
        Args:
            ip: IP address to validate
        
        Returns:
            True if valid IP format
        """
        if not ip:
            return False
        
        success, output = self._execute_script(self.SCRIPT_NAME, 'validate', ip, timeout=5)
        return success and output.strip().lower() == 'true'
    
    # ==================== UTILITY METHODS ====================
    
    def suggest_domain_for_vhost(self, server_name: str) -> str:
        """
        Suggest a domain name for a vhost
        
        Args:
            server_name: Server name from vhost
        
        Returns:
            Suggested domain (usually same as server_name)
        """
        # Just return the server name as-is
        # Could be extended to add .local suffix if not present
        if not server_name.endswith('.local') and '.' not in server_name:
            return f"{server_name}.local"
        return server_name
    
    def get_entry_count(self) -> int:
        """
        Get count of managed hosts entries
        
        Returns:
            Number of entries
        """
        entries = self.list_entries()
        return len(entries)
