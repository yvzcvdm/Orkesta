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
    
    @property
    def has_advanced_features(self) -> bool:
        """MySQL has basic service management features"""
        return False
    
    def _execute_script_with_sudo(self, script_name: str, args: list, sudo_password: str = "", timeout: int = 300) -> Tuple[bool, str]:
        """Execute script with sudo password"""
        import os
        import subprocess
        
        script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'scripts', script_name)
        
        if not os.path.exists(script_path):
            return False, f"Script not found: {script_path}"
        
        cmd = ['sudo', '-S', script_path] + args
        
        try:
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Send sudo password if provided
            stdin_input = sudo_password + '\n' if sudo_password else None
            
            stdout, stderr = process.communicate(input=stdin_input, timeout=timeout)
            
            if process.returncode == 0:
                message = stdout.strip() or "Operation completed successfully"
                return True, message
            else:
                error = stderr.strip() or stdout.strip() or "Unknown error"
                return False, f"Script hatası ({script_path}): {error}"
                
        except subprocess.TimeoutExpired:
            return False, "Operation timed out"
        except Exception as e:
            return False, str(e)
    
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

    # ==================== DATABASE MANAGEMENT METHODS ====================
    
    def get_databases(self, root_password: str = "") -> Tuple[bool, List[str]]:
        """Get list of databases"""
        # Use saved password if not provided
        if not root_password:
            root_password = self._get_saved_root_password()
            
        args = ['database-list', '--json']
        if root_password:
            args.extend(['--root-password', root_password])
        
        success, output = self._execute_script(self.SCRIPT_NAME, *args, timeout=30)
        if not success:
            return False, []
        try:
            import json
            return True, json.loads(output)
        except:
            return False, []
    
    def create_database(self, database_name: str, root_password: str = "", sudo_password: str = "") -> Tuple[bool, str]:
        """Create a new database"""
        # Use saved password if not provided
        if not root_password:
            root_password = self._get_saved_root_password()
            
        args = ['database-create', database_name]
        if root_password:
            args.append(root_password)
        return self._execute_script_with_sudo(self.SCRIPT_NAME, args, sudo_password, timeout=30)
    
    def drop_database(self, database_name: str, root_password: str = "", sudo_password: str = "") -> Tuple[bool, str]:
        """Drop a database"""
        # Use saved password if not provided
        if not root_password:
            root_password = self._get_saved_root_password()
            
        args = ['database-drop', database_name]
        if root_password:
            args.append(root_password)
        return self._execute_script_with_sudo(self.SCRIPT_NAME, args, sudo_password, timeout=30)

    # ==================== USER MANAGEMENT METHODS ====================
    
    def create_user(self, username: str, password: str, host: str = 'localhost', root_password: str = "", sudo_password: str = "") -> Tuple[bool, str]:
        """Create a new MySQL user"""
        # Use saved password if not provided
        if not root_password:
            root_password = self._get_saved_root_password()
            
        args = ['user-create', username, password, host]
        if root_password:
            args.append(root_password)
        return self._execute_script_with_sudo(self.SCRIPT_NAME, args, sudo_password, timeout=30)
    
    def get_users(self) -> Tuple[bool, List[Dict[str, Any]]]:
        """Get list of MySQL users"""
        if not self.is_running():
            return False, []
            
        saved_password = self._get_saved_root_password()
        if not saved_password:
            return False, []
        
        try:
            # Execute MySQL query to get users
            import subprocess
            socket_path = "/var/run/mysqld/mysqld.sock"
            mysql_cmd = [
                'mysql', '-u', 'root', f'-p{saved_password}', 
                f'--socket={socket_path}', '-e', 
                "SELECT User, Host FROM mysql.user WHERE User != '' AND User != 'mysql.session' AND User != 'mysql.sys' ORDER BY User;",
                '-s', '-N'
            ]
            
            result = subprocess.run(mysql_cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                logger.error(f"MySQL users query failed: {result.stderr}")
                return False, []
            
            users = []
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        users.append({
                            'username': parts[0],
                            'host': parts[1],
                            'full_name': f"{parts[0]}@{parts[1]}"
                        })
            
            return True, users
            
        except Exception as e:
            logger.error(f"Error getting MySQL users: {e}")
            return False, []

    # ==================== PASSWORD MANAGEMENT METHODS ====================
    
    def set_root_password(self, new_password: str, current_password: str = "") -> Tuple[bool, str]:
        """Set MySQL root password (if current password is known)"""
        args = ['set-root-password', new_password]
        if current_password:
            args.append(current_password)
        
        success, output = self._execute_script(self.SCRIPT_NAME, *args, timeout=30)
        if success:
            self._save_root_password(new_password)
        
        return success, output
    
    def reset_root_password(self, new_password: str) -> Tuple[bool, str]:
        """Reset root password without knowing current password"""
        success, output = self._execute_script(self.SCRIPT_NAME, 'reset-root-password', new_password, timeout=60)
        if success:
            self._save_root_password(new_password)
        
        return success, output
    
    def run_mysql_secure_installation(self) -> Tuple[bool, str]:
        """Show secure installation guide"""
        return self._execute_script(self.SCRIPT_NAME, 'secure-installation', timeout=10)
    
    def get_mysql_status_info(self) -> Dict[str, Any]:
        """Get MySQL status information"""
        success, output = self._execute_script(self.SCRIPT_NAME, 'status-info', '--json', timeout=30)
        if not success:
            return {'installed': self.is_installed(), 'running': self.is_running(), 'databases_count': 0}
        try:
            import json
            status_data = json.loads(output)
            
            # Add root password info if available
            saved_password = self._get_saved_root_password()
            if saved_password:
                status_data['root_password'] = saved_password
                status_data['auth_method'] = 'Password Auth'
                
                # Test connection with saved password
                test_success, _ = self._execute_script(self.SCRIPT_NAME, 'check-root-password', saved_password, timeout=10)
                status_data['root_access'] = test_success
            else:
                status_data['root_password'] = 'Unknown'
                status_data['auth_method'] = 'Unix Socket (sudo mysql)'
                status_data['root_access'] = True  # Assume sudo works
            
            # Add databases count and user count - sadece sudo ile değil, güvenli şekilde
            if self.is_running():
                # Eğer SUDO_ASKPASS set edilmişse, güvenle database listesini al
                import os
                if saved_password or os.environ.get('SUDO_ASKPASS'):
                    db_success, databases = self.get_databases()
                    if db_success:
                        status_data['databases_count'] = len(databases)
                        status_data['databases'] = databases
                    else:
                        status_data['databases_count'] = 0
                        status_data['databases'] = []
                    
                    # Get users count
                    users_success, users = self.get_users()
                    if users_success:
                        status_data['users_count'] = len(users)
                        status_data['users'] = users
                    else:
                        status_data['users_count'] = 0
                        status_data['users'] = []
                else:
                    # Sudo password gerekli, boş değerler dön
                    status_data['databases_count'] = 0
                    status_data['databases'] = []
                    status_data['users_count'] = 0
                    status_data['users'] = []
            else:
                status_data['databases_count'] = 0
                status_data['databases'] = []
                status_data['users_count'] = 0
                status_data['users'] = []
            
            return status_data
        except:
            return {'installed': self.is_installed(), 'running': self.is_running(), 'databases_count': 0}
    
    def _get_saved_root_password(self) -> str:
        """Get saved root password from local storage"""
        try:
            import os
            password_file = os.path.expanduser('~/.orkesta/mysql_root_password')
            if os.path.exists(password_file):
                with open(password_file, 'r') as f:
                    return f.read().strip()
        except:
            pass
        return ""
    
    def _save_root_password(self, password: str) -> None:
        """Save root password to local storage"""
        try:
            import os
            config_dir = os.path.expanduser('~/.orkesta')
            os.makedirs(config_dir, exist_ok=True)
            
            password_file = os.path.join(config_dir, 'mysql_root_password')
            with open(password_file, 'w') as f:
                f.write(password)
            
            # Set secure permissions (600 - only owner can read/write)
            os.chmod(password_file, 0o600)
        except Exception as e:
            logger.warning(f"Failed to save MySQL password: {e}")
    
    def _clear_saved_password(self) -> None:
        """Clear saved password"""
        try:
            import os
            password_file = os.path.expanduser('~/.orkesta/mysql_root_password')
            if os.path.exists(password_file):
                os.remove(password_file)
        except:
            pass
