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
    
    @property
    def name(self) -> str:
        return "mysql"
    
    @property
    def display_name(self) -> str:
        return "MySQL Database Server"
    
    @property
    def description(self) -> str:
        return "Popular open-source relational database management system"
    
    @property
    def service_type(self) -> ServiceType:
        return ServiceType.DATABASE
    
    @property
    def icon_name(self) -> str:
        return "network-workgroup"
    
    @property
    def package_names(self) -> Dict[str, List[str]]:
        return {
            'fedora': ['mysql-server', 'mysql'],
            'ubuntu': ['mysql-server', 'mysql-client'],
            'debian': ['mysql-server', 'mysql-client'],
            'arch': ['mysql']
        }
    
    @property
    def systemd_service_name(self) -> Optional[str]:
        # mysqld for Fedora/Arch, mysql for Debian/Ubuntu
        os_type = self.platform_manager.os_type.value
        if os_type in ['fedora', 'arch']:
            return 'mysqld.service'
        else:
            return 'mysql.service'
    
    @property
    def default_port(self) -> Optional[int]:
        return 3306
    
    @property
    def config_file_paths(self) -> Dict[str, str]:
        return {
            'fedora': '/etc/my.cnf',
            'ubuntu': '/etc/mysql/mysql.conf.d/mysqld.cnf',
            'debian': '/etc/mysql/mysql.conf.d/mysqld.cnf',
            'arch': '/etc/mysql/my.cnf'
        }
    
    def get_configuration_options(self) -> List[Dict[str, Any]]:
        """MySQL configuration options"""
        return [
            {
                'name': 'port',
                'display_name': 'MySQL Port',
                'type': 'int',
                'default': 3306,
                'description': 'MySQL listening port'
            },
            {
                'name': 'bind_address',
                'display_name': 'Bind Address',
                'type': 'string',
                'default': '127.0.0.1',
                'description': 'IP address to bind (127.0.0.1 for localhost only)'
            },
            {
                'name': 'max_connections',
                'display_name': 'Max Connections',
                'type': 'int',
                'default': 151,
                'description': 'Maximum number of simultaneous connections'
            },
            {
                'name': 'innodb_buffer_pool_size',
                'display_name': 'InnoDB Buffer Pool Size',
                'type': 'string',
                'default': '128M',
                'description': 'InnoDB buffer pool size (e.g., 128M, 1G)'
            },
            {
                'name': 'query_cache_size',
                'display_name': 'Query Cache Size',
                'type': 'string',
                'default': '16M',
                'description': 'Query cache size (0 to disable)'
            },
            {
                'name': 'max_allowed_packet',
                'display_name': 'Max Allowed Packet',
                'type': 'string',
                'default': '64M',
                'description': 'Maximum size of one packet'
            }
        ]
    
    # ==================== SERVICE IMPLEMENTATION ====================
    
    def is_installed(self) -> bool:
        """Check if MySQL is installed"""
        packages = self.get_packages_for_current_os()
        if not packages:
            logger.warning(f"{self.name}: No package definition for this OS")
            return False
        
        # Check if at least the server package is installed
        server_packages = [pkg for pkg in packages if 'server' in pkg or pkg == 'mysql']
        for package in server_packages:
            if self.platform_manager.is_package_installed(package):
                return True
        
        return False
    
    def install(self) -> Tuple[bool, str]:
        """Install MySQL with automatic root password setup"""
        packages = self.get_packages_for_current_os()
        if not packages:
            return False, _("No package definition found for this OS")
        
        try:
            # Generate a random root password
            import secrets
            import string
            root_password = self._generate_root_password()
            
            # Create installation script with automatic MySQL setup
            script_content = self._create_install_script_with_password(packages, root_password)
            
            # Write script to temporary file
            import tempfile
            import os
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
                f.write(script_content)
                script_path = f.name
            
            # Make script executable
            os.chmod(script_path, 0o755)
            
            # Execute script with pkexec
            logger.info(f"{self.name} installing packages: {packages}")
            result = subprocess.run(
                ['pkexec', 'bash', script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=600,  # 10 dakika
                text=True
            )
            
            # Clean up script file
            try:
                os.unlink(script_path)
            except:
                pass
            
            if result.returncode != 0:
                error_msg = result.stderr if result.stderr else "Unknown error"
                # PolicyKit cancelled check
                if "cancelled" in error_msg.lower() or "authentication failed" in error_msg.lower():
                    return False, _("Authentication cancelled or failed")
                logger.error(f"Installation error: {error_msg[:200]}")
                return False, _("Installation failed: {error}").format(error=error_msg[:200])
            
            # Save root password to local storage
            success_save = self._save_root_password(root_password)
            if not success_save:
                logger.warning("Failed to save root password to local storage")
            
            # Enable and start service after installation
            success, start_msg = self._post_install_setup()
            if success:
                return True, _("{service} installed successfully").format(service=self.display_name) + f"\n\n✅ Root password: {root_password}\n\n" + _("Password saved locally for management operations")
            else:
                return True, _("{service} installed successfully but failed to start: {error}").format(service=self.display_name, error=start_msg) + f"\n\n✅ Root password: {root_password}\n\n" + _("Password saved locally for management operations")
        
        except subprocess.TimeoutExpired:
            logger.error("Installation timeout")
            return False, _("Installation timed out (>10 minutes)")
        except Exception as e:
            logger.error(f"Post-install setup error: {e}")
            return False, f"Post-install setup failed: {str(e)}"
    
    def _detect_root_credentials(self) -> Dict[str, Any]:
        """Detect MySQL root authentication method and credentials"""
        result = {
            'root_access': False,
            'root_password_set': False,
            'root_password': 'Unknown',
            'auth_method': 'Unknown'
        }
        
        if not self.is_running():
            return result
        
        # First try the saved password
        saved_password = self._load_root_password()
        
        # Test different authentication methods
        auth_methods = [
            ('no_password', ''),
            ('empty_password', ''),
        ]
        
        # Add saved password if available
        if saved_password:
            auth_methods.insert(0, ('saved_password', saved_password))
        
        # Add common passwords to test
        auth_methods.extend([
            ('root_password', 'root'),
            ('mysql_password', 'mysql'),
            ('admin_password', 'admin'),
            ('password_password', 'password'),
            ('toor_password', 'toor')
        ])
        
        for method_name, password in auth_methods:
            try:
                if method_name == 'no_password':
                    # Try without password (Unix socket authentication)
                    cmd = ['pkexec', 'mysql', '-u', 'root', '-e', 'SELECT USER();']
                else:
                    # Try with password
                    cmd = ['mysql', '-u', 'root', f'-p{password}', '-e', 'SELECT USER();']
                
                proc_result = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=10,
                    text=True
                )
                
                if proc_result.returncode == 0:
                    result['root_access'] = True
                    if method_name == 'no_password':
                        result['auth_method'] = 'Unix Socket (sudo mysql)'
                        result['root_password'] = 'No password needed (use sudo)'
                        result['root_password_set'] = False
                    elif method_name == 'saved_password':
                        result['auth_method'] = 'Saved Password'
                        result['root_password'] = password
                        result['root_password_set'] = True
                    else:
                        result['auth_method'] = 'Password Authentication'
                        result['root_password'] = password if password else 'Empty'
                        result['root_password_set'] = bool(password)
                    
                    logger.info(f"MySQL root access: {method_name} works")
                    break
                    
            except subprocess.TimeoutExpired:
                logger.warning(f"MySQL auth test timeout: {method_name}")
                continue
            except Exception as e:
                logger.debug(f"MySQL auth test failed {method_name}: {e}")
                continue
        
        # If no method worked, try to get more info about auth method
        if not result['root_access']:
            result['auth_method'] = 'Password Required (Unknown)'
            result['root_password'] = 'Set via mysql_secure_installation'
        
        return result
    
    def get_detected_root_password(self) -> str:
        """Get the detected root password for automatic operations"""
        root_info = self._detect_root_credentials()
        
        if root_info['auth_method'] == 'Unix Socket (sudo mysql)':
            return ''  # No password needed, use sudo
        elif root_info['root_access']:
            return root_info['root_password']
        else:
            return ''  # Unknown, try empty
    
    def _execute_mysql_command(self, sql_command: str, use_sudo: Optional[bool] = None) -> Tuple[bool, str]:
        """Execute MySQL command with automatic authentication"""
        if not self.is_running():
            return False, "MySQL is not running"
        
        root_info = self._detect_root_credentials()
        
        if not root_info['root_access']:
            return False, "Cannot access MySQL. Root password unknown."
        
        try:
            if root_info['auth_method'] == 'Unix Socket (sudo mysql)' or use_sudo:
                # Use pkexec for GUI sudo
                cmd = ['pkexec', 'mysql', '-u', 'root', '-e', sql_command]
            else:
                # Use password authentication
                password = root_info['root_password']
                if password and password != 'Empty':
                    cmd = ['mysql', '-u', 'root', f'-p{password}', '-e', sql_command]
                else:
                    cmd = ['mysql', '-u', 'root', '-e', sql_command]
            
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30,
                text=True
            )
            
            if result.returncode == 0:
                return True, result.stdout.strip()
            else:
                return False, result.stderr.strip()
                
        except Exception as e:
            logger.error(f"MySQL command execution error: {e}")
            return False, str(e)
    
    def uninstall(self) -> Tuple[bool, str]:
        """Uninstall MySQL using a single script"""
        packages = self.get_packages_for_current_os()
        if not packages:
            return False, _("No package definition found for this OS")
        
        try:
            # Stop service first
            if self.is_running():
                logger.info("Stopping MySQL before uninstall")
                self.stop()
            
            # Create uninstall script
            script_content = self._create_uninstall_script(packages)
            
            # Write script to temporary file
            import tempfile
            import os
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
                f.write(script_content)
                script_path = f.name
            
            # Make script executable
            os.chmod(script_path, 0o755)
            
            # Execute script with pkexec
            logger.info(f"{self.name} uninstalling packages: {packages}")
            result = subprocess.run(
                ['pkexec', 'bash', script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=600,  # 10 dakika
                text=True
            )
            
            # Clean up script file
            try:
                os.unlink(script_path)
            except:
                pass
            
            if result.returncode != 0:
                error_msg = result.stderr if result.stderr else "Unknown error"
                # PolicyKit cancelled check
                if "cancelled" in error_msg.lower() or "authentication failed" in error_msg.lower():
                    return False, _("Authentication cancelled or failed")
                logger.error(f"Uninstall error: {error_msg[:200]}")
                return False, _("Uninstall failed: {error}").format(error=error_msg[:200])
            
            # Veri dosyalarının kaldırılması hakkında uyarı
            data_warning = _("\n\nNOTE: Database files in /var/lib/mysql are preserved. Remove manually if needed.")
            return True, _("{service} uninstalled successfully").format(service=self.display_name) + data_warning
        
        except subprocess.TimeoutExpired:
            logger.error("Uninstall timeout")
            return False, _("Uninstall timed out (>10 minutes)")
        except Exception as e:
            logger.error(f"Uninstall error: {e}")
            import traceback
            traceback.print_exc()
            return False, _("Uninstall error: {error}").format(error=str(e))
    
    def start(self) -> Tuple[bool, str]:
        """Start MySQL"""
        if not self.is_installed():
            return False, _("{service} is not installed").format(service=self.display_name)
        
        if not self.systemd_service_name:
            return False, _("Systemd service name not defined")
        
        try:
            result = subprocess.run(
                ['pkexec', 'systemctl', 'start', self.systemd_service_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30,
                text=True
            )
            
            if result.returncode == 0:
                return True, _("{service} started").format(service=self.display_name)
            else:
                error_msg = result.stderr if result.stderr else "Unknown error"
                if "cancelled" in error_msg.lower() or "authentication failed" in error_msg.lower():
                    return False, _("Authentication cancelled or failed")
                return False, _("Start error: {error}").format(error=error_msg[:200])
        
        except Exception as e:
            logger.error(f"Start error: {e}")
            return False, _("Start error: {error}").format(error=str(e))
    
    def stop(self) -> Tuple[bool, str]:
        """Stop MySQL"""
        if not self.is_installed():
            return False, _("{service} is not installed").format(service=self.display_name)
        
        if not self.systemd_service_name:
            return False, _("Systemd service name not defined")
        
        try:
            result = subprocess.run(
                ['pkexec', 'systemctl', 'stop', self.systemd_service_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30,
                text=True
            )
            
            if result.returncode == 0:
                return True, _("{service} stopped").format(service=self.display_name)
            else:
                error_msg = result.stderr if result.stderr else "Unknown error"
                if "cancelled" in error_msg.lower() or "authentication failed" in error_msg.lower():
                    return False, _("Authentication cancelled or failed")
                return False, _("Stop error: {error}").format(error=error_msg[:200])
        
        except Exception as e:
            logger.error(f"Stop error: {e}")
            return False, _("Stop error: {error}").format(error=str(e))
    
    def restart(self) -> Tuple[bool, str]:
        """Restart MySQL"""
        if not self.is_installed():
            return False, _("{service} is not installed").format(service=self.display_name)
        
        if not self.systemd_service_name:
            return False, _("Systemd service name not defined")
        
        try:
            result = subprocess.run(
                ['pkexec', 'systemctl', 'restart', self.systemd_service_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30,
                text=True
            )
            
            if result.returncode == 0:
                return True, _("{service} restarted").format(service=self.display_name)
            else:
                error_msg = result.stderr if result.stderr else "Unknown error"
                if "cancelled" in error_msg.lower() or "authentication failed" in error_msg.lower():
                    return False, _("Authentication cancelled or failed")
                return False, _("Restart error: {error}").format(error=error_msg[:200])
        
        except Exception as e:
            logger.error(f"Restart error: {e}")
            return False, _("Restart error: {error}").format(error=str(e))
    
    def is_running(self) -> bool:
        """Check if MySQL is running"""
        if not self.is_installed() or not self.systemd_service_name:
            return False
        
        return self.platform_manager.is_service_active(self.systemd_service_name)
    
    def enable(self) -> Tuple[bool, str]:
        """Enable MySQL autostart"""
        if not self.is_installed():
            return False, _("{service} is not installed").format(service=self.display_name)
        
        if not self.systemd_service_name:
            return False, _("Systemd service name not defined")
        
        try:
            result = subprocess.run(
                ['pkexec', 'systemctl', 'enable', self.systemd_service_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30,
                text=True
            )
            
            if result.returncode == 0:
                return True, _("{service} automatic startup enabled").format(service=self.display_name)
            else:
                error_msg = result.stderr if result.stderr else "Unknown error"
                if "cancelled" in error_msg.lower() or "authentication failed" in error_msg.lower():
                    return False, _("Authentication cancelled or failed")
                return False, _("Enable error: {error}").format(error=error_msg[:200])
        
        except Exception as e:
            logger.error(f"Enable error: {e}")
            return False, _("Enable error: {error}").format(error=str(e))
    
    def disable(self) -> Tuple[bool, str]:
        """Disable MySQL autostart"""
        if not self.is_installed():
            return False, _("{service} is not installed").format(service=self.display_name)
        
        if not self.systemd_service_name:
            return False, _("Systemd service name not defined")
        
        try:
            result = subprocess.run(
                ['pkexec', 'systemctl', 'disable', self.systemd_service_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30,
                text=True
            )
            
            if result.returncode == 0:
                return True, _("{service} automatic startup disabled").format(service=self.display_name)
            else:
                error_msg = result.stderr if result.stderr else "Unknown error"
                if "cancelled" in error_msg.lower() or "authentication failed" in error_msg.lower():
                    return False, _("Authentication cancelled or failed")
                return False, _("Disable error: {error}").format(error=error_msg[:200])
        
        except Exception as e:
            logger.error(f"Disable error: {e}")
            return False, _("Disable error: {error}").format(error=str(e))

    # ==================== DATABASE-SPECIFIC METHODS ====================
    
    def get_databases(self) -> Tuple[bool, List[str]]:
        """Get list of databases (requires MySQL client and authentication)"""
        try:
            if not self.is_running():
                return False, []
            
            # Try to list databases (this will likely require authentication)
            result = subprocess.run(
                ['mysql', '-u', 'root', '-e', 'SHOW DATABASES;'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10,
                text=True
            )
            
            if result.returncode == 0:
                # Parse output to get database names
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                databases = [line.strip() for line in lines if line.strip()]
                return True, databases
            else:
                return False, []
        
        except Exception as e:
            logger.error(f"Error getting databases: {e}")
            return False, []
    
    def create_database(self, database_name: str) -> Tuple[bool, str]:
        """Create a new database using automatic authentication"""
        try:
            # Validate database name (basic validation)
            if not database_name or not database_name.replace('_', '').replace('-', '').isalnum():
                return False, "Invalid database name"
            
            sql_command = f'CREATE DATABASE `{database_name}`;'
            success, result = self._execute_mysql_command(sql_command)
            
            if success:
                return True, f"Database '{database_name}' created successfully"
            else:
                return False, f"Database creation failed: {result[:200]}"
        
        except Exception as e:
            logger.error(f"Error creating database: {e}")
            return False, f"Database creation error: {str(e)}"
    
    def drop_database(self, database_name: str) -> Tuple[bool, str]:
        """Drop a database (requires MySQL client and authentication)"""
        try:
            if not self.is_running():
                return False, _("MySQL is not running")
            
            # Validate database name and prevent dropping system databases
            system_dbs = ['information_schema', 'mysql', 'performance_schema', 'sys']
            if database_name in system_dbs:
                return False, _("Cannot drop system database")
            
            result = subprocess.run(
                ['mysql', '-u', 'root', '-e', f'DROP DATABASE `{database_name}`;'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10,
                text=True
            )
            
            if result.returncode == 0:
                return True, _("Database '{db}' dropped successfully").format(db=database_name)
            else:
                error_msg = result.stderr if result.stderr else "Unknown error"
                return False, _("Database drop failed: {error}").format(error=error_msg[:200])
        
        except Exception as e:
            logger.error(f"Error dropping database: {e}")
            return False, _("Database drop error: {error}").format(error=str(e))
    
    # ==================== PASSWORD MANAGEMENT METHODS ====================
    
    def check_root_password(self, password: str = "") -> Tuple[bool, str]:
        """Check if root password is correct"""
        try:
            if not self.is_running():
                return False, _("MySQL is not running")
            
            # Test connection with given password
            cmd = ['mysql', '-u', 'root']
            if password:
                cmd.extend([f'-p{password}'])
            cmd.extend(['-e', 'SELECT 1;'])
            
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10,
                text=True,
                input='\n' if not password else None
            )
            
            if result.returncode == 0:
                if password:
                    return True, _("Root password is correct")
                else:
                    return True, _("Root login without password (SECURITY WARNING!)")
            else:
                if "Access denied" in result.stderr:
                    return False, _("Access denied - incorrect password")
                elif "ERROR 1045" in result.stderr:
                    return False, _("Authentication failed")
                else:
                    return False, _("Connection failed: {error}").format(error=result.stderr[:100])
        
        except Exception as e:
            logger.error(f"Error checking root password: {e}")
            return False, _("Password check error: {error}").format(error=str(e))
    
    def set_root_password(self, new_password: str, current_password: str = "") -> Tuple[bool, str]:
        """Set MySQL root password"""
        try:
            if not self.is_running():
                return False, "MySQL is not running"
            
            if not new_password:
                return False, "New password cannot be empty"
            
            # First, check current access
            root_info = self._detect_root_credentials()
            if not root_info['root_access']:
                return False, "Cannot access MySQL with current credentials"
            
            # Set new password and change plugin for external access (DBgate, etc.)
            # Combine ALTER USER and FLUSH PRIVILEGES in single command to avoid multiple authentication
            sql_command = f"ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '{new_password}'; FLUSH PRIVILEGES;"
            success, result = self._execute_mysql_command(sql_command)
            
            if success:
                return True, "Root password changed successfully (external access enabled)"
            else:
                # Try alternative method for older MySQL versions
                sql_command_old = f"SET PASSWORD FOR 'root'@'localhost' = PASSWORD('{new_password}'); FLUSH PRIVILEGES;"
                success_old, result_old = self._execute_mysql_command(sql_command_old)
                
                if success_old:
                    return True, "Root password changed successfully (legacy method)"
                else:
                    return False, f"Password change failed: {result[:200]}"
        
        except Exception as e:
            logger.error(f"Error setting root password: {e}")
            return False, f"Password change error: {str(e)}"
    
    def run_mysql_secure_installation(self) -> Tuple[bool, str]:
        """Guide user to run mysql_secure_installation"""
        try:
            if not self.is_installed():
                return False, _("MySQL is not installed")
            
            # Check if mysql_secure_installation exists
            result = subprocess.run(
                ['which', 'mysql_secure_installation'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            if result.returncode == 0:
                return True, _("Run 'mysql_secure_installation' in terminal to secure MySQL installation")
            else:
                return False, _("mysql_secure_installation command not found")
        
        except Exception as e:
            logger.error(f"Error checking mysql_secure_installation: {e}")
            return False, _("Error: {error}").format(error=str(e))
    
    def get_mysql_status_info(self) -> Dict[str, Any]:
        """Get detailed MySQL status information"""
        info = {
            'installed': self.is_installed(),
            'running': self.is_running(),
            'root_access': False,
            'root_password_set': False,
            'root_password': 'Unknown',
            'auth_method': 'Unknown',
            'version': 'Unknown',
            'databases_count': 0,
            'port': self.default_port
        }
        
        try:
            if info['running']:
                # Detect root password and authentication method
                root_info = self._detect_root_credentials()
                info.update(root_info)
                
                # Get MySQL version
                result = subprocess.run(
                    ['mysql', '--version'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                if result.returncode == 0:
                    version_line = result.stdout.strip()
                    # Extract version number (e.g., "mysql  Ver 8.0.35-0ubuntu0.22.04.1")
                    import re
                    version_match = re.search(r'Ver (\d+\.\d+\.\d+)', version_line)
                    if version_match:
                        info['version'] = version_match.group(1)
                
                # Get databases count if we have access
                if info['root_access']:
                    success, databases = self.get_databases()
                    if success:
                        info['databases_count'] = len(databases)
            
        except Exception as e:
            logger.error(f"Error getting MySQL status info: {e}")
        
        return info
    
    def create_user(self, username: str, password: str, host: str = 'localhost') -> Tuple[bool, str]:
        """Create a new MySQL user using automatic authentication"""
        try:
            if not username or not password:
                return False, "Username and password are required"
            
            # Validate username (basic validation)
            if not username.replace('_', '').replace('-', '').isalnum():
                return False, "Invalid username"
            
            sql_command = f"CREATE USER '{username}'@'{host}' IDENTIFIED BY '{password}';"
            success, result = self._execute_mysql_command(sql_command)
            
            if success:
                return True, f"User '{username}' created successfully"
            else:
                if "already exists" in result:
                    return False, "User already exists"
                return False, f"User creation failed: {result[:200]}"
        
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return False, _("User creation error: {error}").format(error=str(e))
    
    def grant_privileges(self, username: str, database: str = "*", 
                        privileges: str = "ALL", host: str = 'localhost',
                        root_password: str = "") -> Tuple[bool, str]:
        """Grant privileges to a MySQL user"""
        try:
            if not self.is_running():
                return False, _("MySQL is not running")
            
            if not username:
                return False, _("Username is required")
            
            cmd = ['mysql', '-u', 'root']
            if root_password:
                cmd.extend([f'-p{root_password}'])
            
            sql_commands = [
                f"GRANT {privileges} ON {database}.* TO '{username}'@'{host}';",
                "FLUSH PRIVILEGES;"
            ]
            
            for sql_command in sql_commands:
                cmd_exec = cmd + ['-e', sql_command]
                result = subprocess.run(
                    cmd_exec,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=10,
                    text=True,
                    input='\n' if not root_password else None
                )
                
                if result.returncode != 0:
                    error_msg = result.stderr if result.stderr else "Unknown error"
                    return False, _("Grant privileges failed: {error}").format(error=error_msg[:200])
            
            return True, _("Privileges granted to '{user}' successfully").format(user=username)
        
        except Exception as e:
            logger.error(f"Error granting privileges: {e}")
            return False, _("Grant privileges error: {error}").format(error=str(e))
    
    # ==================== HELPER METHODS ====================
    
    def _create_install_script(self, packages: List[str]) -> str:
        """Create installation script"""
        os_type = self.platform_manager.os_type.value
        
        if os_type == 'fedora':
            package_manager = 'dnf'
            install_cmd = f'{package_manager} install -y'
        elif os_type in ['ubuntu', 'debian']:
            package_manager = 'apt'
            install_cmd = f'{package_manager} update && {package_manager} install -y'
        elif os_type == 'arch':
            package_manager = 'pacman'
            install_cmd = f'{package_manager} -S --noconfirm'
        else:
            install_cmd = 'echo "Unsupported OS"'
        
        script = f"""#!/bin/bash
set -e

echo "Installing MySQL packages: {' '.join(packages)}"

# Update package cache and install packages
{install_cmd} {' '.join(packages)}

echo "MySQL packages installed successfully"
"""
        return script
    
    def _create_uninstall_script(self, packages: List[str]) -> str:
        """Create uninstallation script"""
        os_type = self.platform_manager.os_type.value
        
        if os_type == 'fedora':
            remove_cmd = 'dnf remove -y'
        elif os_type in ['ubuntu', 'debian']:
            remove_cmd = 'apt remove -y'
        elif os_type == 'arch':
            remove_cmd = 'pacman -R --noconfirm'
        else:
            remove_cmd = 'echo "Unsupported OS"'
        
        script = f"""#!/bin/bash
set -e

echo "Removing MySQL packages: {' '.join(packages)}"

# Stop MySQL service if running
systemctl stop {self.systemd_service_name} 2>/dev/null || true

# Disable MySQL service
systemctl disable {self.systemd_service_name} 2>/dev/null || true

# Remove packages
{remove_cmd} {' '.join(packages)}

echo "MySQL packages removed successfully"
echo "NOTE: Database files in /var/lib/mysql are preserved"
"""
        return script
    
    def _post_install_setup(self) -> Tuple[bool, str]:
        """Setup MySQL after installation (enable and start service)"""
        try:
            if not self.systemd_service_name:
                return False, _("Systemd service name not defined")
            
            # Enable service
            enable_result = subprocess.run(
                ['pkexec', 'systemctl', 'enable', self.systemd_service_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30,
                text=True
            )
            
            if enable_result.returncode != 0:
                logger.warning(f"Failed to enable MySQL service: {enable_result.stderr}")
            
            # Start service
            start_result = subprocess.run(
                ['pkexec', 'systemctl', 'start', self.systemd_service_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30,
                text=True
            )
            
            if start_result.returncode == 0:
                return True, _("MySQL service started successfully")
            else:
                error_msg = start_result.stderr if start_result.stderr else "Unknown error"
                return False, _("Failed to start MySQL: {error}").format(error=error_msg[:200])
        
        except Exception as e:
            logger.error(f"Post-install setup error: {e}")
            return False, _("Post-install setup failed: {error}").format(error=str(e))
    
    def _generate_root_password(self) -> str:
        """Generate a secure random password for MySQL root"""
        import secrets
        import string
        
        # Generate 12 character password with letters and numbers
        alphabet = string.ascii_letters + string.digits
        password = ''.join(secrets.choice(alphabet) for _ in range(12))
        return password
    
    def _save_root_password(self, password: str) -> bool:
        """Save root password to local storage"""
        try:
            import os
            import json
            
            # Create config directory if it doesn't exist
            config_dir = os.path.expanduser('~/.config/orkesta')
            os.makedirs(config_dir, exist_ok=True)
            
            # Save password to config file
            config_file = os.path.join(config_dir, 'mysql_config.json')
            config = {'root_password': password}
            
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            # Set secure permissions (owner read/write only)
            os.chmod(config_file, 0o600)
            
            logger.info("MySQL root password saved to local config")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save root password: {e}")
            return False
    
    def _load_root_password(self) -> str:
        """Load root password from local storage"""
        try:
            import os
            import json
            
            config_file = os.path.expanduser('~/.config/orkesta/mysql_config.json')
            if not os.path.exists(config_file):
                return ''
            
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            return config.get('root_password', '')
            
        except Exception as e:
            logger.error(f"Failed to load root password: {e}")
            return ''
    
    def _create_install_script_with_password(self, packages: List[str], root_password: str) -> str:
        """Create installation script with automatic MySQL setup"""
        os_type = self.platform_manager.os_type.value
        
        if os_type == 'fedora':
            package_manager = 'dnf'
            install_cmd = f'{package_manager} install -y'
        elif os_type in ['ubuntu', 'debian']:
            package_manager = 'apt'
            install_cmd = f'{package_manager} update && {package_manager} install -y'
        elif os_type == 'arch':
            package_manager = 'pacman'
            install_cmd = f'{package_manager} -S --noconfirm'
        else:
            install_cmd = 'echo "Unsupported OS"'
        
        script = f"""#!/bin/bash
set -e

echo "Installing MySQL packages: {' '.join(packages)}"

# Set MySQL root password via debconf (for Debian/Ubuntu)
if command -v debconf-set-selections >/dev/null 2>&1; then
    echo "mysql-server mysql-server/root_password password {root_password}" | debconf-set-selections
    echo "mysql-server mysql-server/root_password_again password {root_password}" | debconf-set-selections
fi

# Update package cache and install packages
{install_cmd} {' '.join(packages)}

# Start MySQL service to ensure it's running
systemctl enable mysql 2>/dev/null || systemctl enable mysqld 2>/dev/null || true
systemctl start mysql 2>/dev/null || systemctl start mysqld 2>/dev/null || true

# Wait for MySQL to start
sleep 5

# Set root password and configure for external access
mysql -u root -e "ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '{root_password}';" 2>/dev/null || \\
mysql -u root -e "SET PASSWORD FOR 'root'@'localhost' = PASSWORD('{root_password}');" 2>/dev/null || \\
mysqladmin -u root password '{root_password}' 2>/dev/null || true

# Flush privileges
mysql -u root -p{root_password} -e "FLUSH PRIVILEGES;" 2>/dev/null || true

echo "MySQL installation completed with root password configured"
"""
        return script
