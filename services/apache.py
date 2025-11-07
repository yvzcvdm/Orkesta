"""
Apache HTTP Server Module

Service management module for Apache web server.
"""

from typing import Dict, List, Optional, Any, Tuple
from services.base_service import BaseService, ServiceType
import subprocess
import logging

logger = logging.getLogger(__name__)

# Import i18n
try:
    from src.utils.i18n import get_i18n
    _ = get_i18n().get_translator()
except:
    _ = lambda s: s


class ApacheService(BaseService):
    """Apache HTTP Server service management"""
    
    @property
    def name(self) -> str:
        return "apache"
    
    @property
    def display_name(self) -> str:
        return "Apache HTTP Server"
    
    @property
    def description(self) -> str:
        return "Popular open-source web server"
    
    @property
    def service_type(self) -> ServiceType:
        return ServiceType.WEB_SERVER
    
    @property
    def icon_name(self) -> str:
        return "network-server"
    
    @property
    def package_names(self) -> Dict[str, List[str]]:
        return {
            'fedora': ['httpd', 'mod_ssl'],
            'ubuntu': ['apache2'],
            'debian': ['apache2'],
            'arch': ['apache']
        }
    
    @property
    def systemd_service_name(self) -> Optional[str]:
        # httpd for Fedora, apache2 for Debian/Ubuntu
        os_type = self.platform_manager.os_type.value
        if os_type == 'fedora':
            return 'httpd.service'
        else:
            return 'apache2.service'
    
    @property
    def default_port(self) -> Optional[int]:
        return 80
    
    @property
    def config_file_paths(self) -> Dict[str, str]:
        return {
            'fedora': '/etc/httpd/conf/httpd.conf',
            'ubuntu': '/etc/apache2/apache2.conf',
            'debian': '/etc/apache2/apache2.conf',
            'arch': '/etc/httpd/conf/httpd.conf'
        }
    
    def get_configuration_options(self) -> List[Dict[str, Any]]:
        """Apache configuration options"""
        return [
            {
                'name': 'port',
                'display_name': 'HTTP Port',
                'type': 'int',
                'default': 80,
                'description': 'HTTP listening port'
            },
            {
                'name': 'ssl_port',
                'display_name': 'HTTPS Port',
                'type': 'int',
                'default': 443,
                'description': 'HTTPS listening port'
            },
            {
                'name': 'document_root',
                'display_name': 'Document Root',
                'type': 'path',
                'default': '/var/www/html',
                'description': 'Web files directory'
            },
            {
                'name': 'server_admin',
                'display_name': 'Server Admin',
                'type': 'email',
                'default': 'webmaster@localhost',
                'description': 'Server administrator email address'
            }
        ]
    
    # ==================== SERVICE IMPLEMENTATION ====================
    
    def is_installed(self) -> bool:
        """Check if Apache is installed"""
        packages = self.get_packages_for_current_os()
        if not packages:
            logger.warning(f"{self.name}: No package definition for this OS")
            return False
        
        # Check if all packages are installed
        for package in packages:
            if not self.platform_manager.is_package_installed(package):
                return False
        
        return True
    
    def install(self) -> Tuple[bool, str]:
        """Install Apache"""
        packages = self.get_packages_for_current_os()
        if not packages:
            return False, _("No package definition found for this OS")
        
        try:
            for package in packages:
                # Önce paket yüklü mü kontrol et
                if self.platform_manager.is_package_installed(package):
                    logger.info(f"{package} already installed, skipping")
                    continue
                
                logger.info(f"{self.name} installing: {package}")
                cmd = self.platform_manager.get_install_command(package)
                
                result = subprocess.run(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                    timeout=600,  # 10 dakika
                    text=True
                )
                
                if result.returncode != 0:
                    error_msg = result.stderr if result.stderr else "Unknown error"
                    # PolicyKit cancelled check
                    if "cancelled" in error_msg.lower() or "authentication failed" in error_msg.lower():
                        return False, _("Authentication cancelled or failed")
                    logger.error(f"Installation error: {error_msg[:200]}")
                    return False, _("Installation failed: {error}").format(error=error_msg[:200])
            
            return True, _("{service} installed successfully").format(service=self.display_name)
        
        except subprocess.TimeoutExpired:
            logger.error("Installation timeout")
            return False, _("Installation timed out (>10 minutes)")
        except Exception as e:
            logger.error(f"Installation error: {e}")
            return False, _("Installation error: {error}").format(error=str(e))
    
    def uninstall(self) -> Tuple[bool, str]:
        """Uninstall Apache"""
        packages = self.get_packages_for_current_os()
        if not packages:
            return False, _("No package definition found for this OS")
        
        try:
            # Stop service first
            if self.is_running():
                logger.info("Stopping Apache before uninstall")
                self.stop()
            
            for package in packages:
                # Paket yüklü mü kontrol et
                if not self.platform_manager.is_package_installed(package):
                    logger.info(f"{package} not installed, skipping")
                    continue
                    
                logger.info(f"{self.name} uninstalling: {package}")
                cmd = self.platform_manager.get_remove_command(package)
                
                result = subprocess.run(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                    timeout=600,  # 10 dakika
                    text=True
                )
                
                if result.returncode != 0:
                    error_msg = result.stderr if result.stderr else "Unknown error"
                    # PolicyKit cancelled check
                    if "cancelled" in error_msg.lower() or "authentication failed" in error_msg.lower():
                        return False, _("Authentication cancelled or failed")
                    logger.error(f"Uninstall error: {error_msg[:200]}")
                    # Devam et, diğer paketleri de kaldırmaya çalış
            
            return True, _("{service} uninstalled successfully").format(service=self.display_name)
        
        except subprocess.TimeoutExpired:
            logger.error("Uninstall timeout")
            return False, _("Uninstall timed out (>10 minutes)")
        except Exception as e:
            logger.error(f"Uninstall error: {e}")
            import traceback
            traceback.print_exc()
            return False, _("Uninstall error: {error}").format(error=str(e))
    
    def start(self) -> Tuple[bool, str]:
        """Start Apache"""
        if not self.is_installed():
            return False, _("{service} is not installed").format(service=self.display_name)
        
        if not self.systemd_service_name:
            return False, _("Systemd service name not defined")
        
        try:
            cmd = self.platform_manager.get_service_command('start', self.systemd_service_name)
            result = subprocess.run(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                timeout=30,
                text=True
            )
            
            if result.returncode == 0:
                return True, _("{service} started").format(service=self.display_name)
            else:
                error_msg = result.stderr if result.stderr else "Unknown error"
                return False, _("Start error: {error}").format(error=error_msg[:200])
        
        except Exception as e:
            logger.error(f"Start error: {e}")
            return False, _("Start error: {error}").format(error=str(e))
    
    def stop(self) -> Tuple[bool, str]:
        """Stop Apache"""
        if not self.is_installed():
            return False, _("{service} is not installed").format(service=self.display_name)
        
        if not self.systemd_service_name:
            return False, _("Systemd service name not defined")
        
        try:
            cmd = self.platform_manager.get_service_command('stop', self.systemd_service_name)
            result = subprocess.run(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                timeout=30,
                text=True
            )
            
            if result.returncode == 0:
                return True, _("{service} stopped").format(service=self.display_name)
            else:
                error_msg = result.stderr if result.stderr else "Unknown error"
                return False, _("Stop error: {error}").format(error=error_msg[:200])
        
        except Exception as e:
            logger.error(f"Stop error: {e}")
            return False, _("Stop error: {error}").format(error=str(e))
    
    def restart(self) -> Tuple[bool, str]:
        """Restart Apache"""
        if not self.is_installed():
            return False, _("{service} is not installed").format(service=self.display_name)
        
        if not self.systemd_service_name:
            return False, _("Systemd service name not defined")
        
        try:
            cmd = self.platform_manager.get_service_command('restart', self.systemd_service_name)
            result = subprocess.run(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                timeout=30,
                text=True
            )
            
            if result.returncode == 0:
                return True, _("{service} restarted").format(service=self.display_name)
            else:
                error_msg = result.stderr if result.stderr else "Unknown error"
                return False, _("Restart error: {error}").format(error=error_msg[:200])
        
        except Exception as e:
            logger.error(f"Restart error: {e}")
            return False, _("Restart error: {error}").format(error=str(e))
    
    def is_running(self) -> bool:
        """Check if Apache is running"""
        if not self.is_installed() or not self.systemd_service_name:
            return False
        
        return self.platform_manager.is_service_active(self.systemd_service_name)
    
    def enable(self) -> Tuple[bool, str]:
        """Enable Apache autostart"""
        if not self.is_installed():
            return False, _("{service} is not installed").format(service=self.display_name)
        
        if not self.systemd_service_name:
            return False, _("Systemd service name not defined")
        
        try:
            cmd = self.platform_manager.get_service_command('enable', self.systemd_service_name)
            result = subprocess.run(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                timeout=30,
                text=True
            )
            
            if result.returncode == 0:
                return True, _("{service} automatic startup enabled").format(service=self.display_name)
            else:
                error_msg = result.stderr if result.stderr else "Unknown error"
                return False, _("Enable error: {error}").format(error=error_msg[:200])
        
        except Exception as e:
            logger.error(f"Enable error: {e}")
            return False, _("Enable error: {error}").format(error=str(e))
    
    def disable(self) -> Tuple[bool, str]:
        """Disable Apache autostart"""
        if not self.is_installed():
            return False, _("{service} is not installed").format(service=self.display_name)
        
        if not self.systemd_service_name:
            return False, _("Systemd service name not defined")
        
        try:
            cmd = self.platform_manager.get_service_command('disable', self.systemd_service_name)
            result = subprocess.run(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                timeout=30,
                text=True
            )
            
            if result.returncode == 0:
                return True, _("{service} automatic startup disabled").format(service=self.display_name)
            else:
                error_msg = result.stderr if result.stderr else "Unknown error"
                return False, _("Disable error: {error}").format(error=error_msg[:200])
        
        except Exception as e:
            logger.error(f"Disable error: {e}")
            return False, _("Disable error: {error}").format(error=str(e))
