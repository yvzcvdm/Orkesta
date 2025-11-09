"""
MySQL Database Server Module

Service management module for MySQL database server.
"""

from typing import Dict, List, Optional, Any, Tuple
from services.base_service import BaseService, ServiceType
import subprocess
import logging

logger = logging.getLogger(__name__)

# Simple translation function - using English for now
def _(text):
    """Simple translation function"""
    return text


class MySQLService(BaseService):
    """MySQL Database Server service management"""
    
    SCRIPT_NAME = 'mysql.sh'
    
    @property
    def name(self) -> str:
        return "mysql"
    
    @property
    def display_name(self) -> str:
        return "MySQL"
    
    @property
    def description(self) -> str:
        return _("MySQL Database Server - Relational database management system")
    
    @property
    def icon_name(self) -> str:
        return "server-database"
    
    @property
    def service_type(self) -> ServiceType:
        return ServiceType.DATABASE
    
    @property
    def default_port(self) -> Optional[int]:
        return 3306
    
    def is_installed(self) -> bool:
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

    # ==================== DATABASE-SPECIFIC METHODS ====================
    
    def get_databases(self) -> Tuple[bool, List[str]]:
        success, output = self._execute_script(self.SCRIPT_NAME, 'database-list', '--json', timeout=30)
        if not success:
            return False, []
        try:
            import json
            return True, json.loads(output)
        except:
            return False, []
    
    def create_database(self, database_name: str) -> Tuple[bool, str]:
        return self._execute_script(self.SCRIPT_NAME, 'database-create', database_name, timeout=30)
    
    def drop_database(self, database_name: str) -> Tuple[bool, str]:
        return self._execute_script(self.SCRIPT_NAME, 'database-drop', database_name, timeout=30)
    
    # ==================== PASSWORD MANAGEMENT METHODS ====================
    
    def check_root_password(self, password: str = "") -> Tuple[bool, str]:
        return self._execute_script(self.SCRIPT_NAME, 'check-root-password', password, timeout=10)
    
    def set_root_password(self, new_password: str, current_password: str = "") -> Tuple[bool, str]:
        args = ['set-root-password', new_password]
        if current_password:
            args.append(current_password)
        return self._execute_script(self.SCRIPT_NAME, *args, timeout=30)
    
    def run_mysql_secure_installation(self) -> Tuple[bool, str]:
        return self._execute_script(self.SCRIPT_NAME, 'secure-installation', timeout=10)
    
    def get_mysql_status_info(self) -> Dict[str, Any]:
        success, output = self._execute_script(self.SCRIPT_NAME, 'status-info', '--json', timeout=30)
        if not success:
            return {'installed': self.is_installed(), 'running': self.is_running()}
        try:
            import json
            return json.loads(output)
        except:
            return {'installed': self.is_installed(), 'running': self.is_running()}
    
    def create_user(self, username: str, password: str, host: str = 'localhost') -> Tuple[bool, str]:
        return self._execute_script(self.SCRIPT_NAME, 'user-create', username, password, host, timeout=30)
    
    def grant_privileges(self, username: str, database: str = "*", 
                        privileges: str = "ALL", host: str = 'localhost',
                        root_password: str = "") -> Tuple[bool, str]:
        args = ['grant-privileges', username, database, privileges, host]
        if root_password:
            args.append(root_password)
        return self._execute_script(self.SCRIPT_NAME, *args, timeout=30)
