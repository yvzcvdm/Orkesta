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
    
    def __init__(self, platform_manager):
        super().__init__(platform_manager)
        self.available_versions = ['7.4', '8.0', '8.1', '8.2', '8.3']
        self.installed_versions = []
        self.active_version = None
        self._refresh_installed_versions()
    
    @property
    def name(self) -> str:
        return "php"
    
    @property
    def display_name(self) -> str:
        return "PHP"
    
    @property
    def description(self) -> str:
        return "Server-side scripting language for web development"
    
    @property
    def service_type(self) -> ServiceType:
        return ServiceType.OTHER
    
    @property
    def icon_name(self) -> str:
        return "application-x-php"
    
    @property
    def package_names(self) -> Dict[str, List[str]]:
        """Base PHP packages - versions will be added dynamically"""
        os_type = self.platform_manager.os_type.value
        
        if os_type in ['ubuntu', 'debian']:
            return {
                'ubuntu': ['php-fpm', 'php-cli', 'php-common'],
                'debian': ['php-fpm', 'php-cli', 'php-common']
            }
        elif os_type == 'fedora':
            return {
                'fedora': ['php-fpm', 'php-cli', 'php-common']
            }
        elif os_type == 'arch':
            return {
                'arch': ['php', 'php-fpm']
            }
        
        return {}
    
    @property
    def systemd_service_name(self) -> Optional[str]:
        """Service name depends on PHP version"""
        if self.active_version:
            os_type = self.platform_manager.os_type.value
            if os_type in ['ubuntu', 'debian']:
                return f'php{self.active_version}-fpm.service'
            elif os_type == 'fedora':
                return 'php-fpm.service'
            elif os_type == 'arch':
                return 'php-fpm.service'
        return 'php-fpm.service'
    
    @property
    def default_port(self) -> Optional[int]:
        return 9000  # PHP-FPM default port
    
    @property
    def config_file_paths(self) -> Dict[str, str]:
        """Config paths - will be version-specific"""
        os_type = self.platform_manager.os_type.value
        if os_type in ['ubuntu', 'debian']:
            if self.active_version:
                return {
                    'ubuntu': f'/etc/php/{self.active_version}/fpm/php.ini',
                    'debian': f'/etc/php/{self.active_version}/fpm/php.ini'
                }
            return {
                'ubuntu': '/etc/php/php.ini',
                'debian': '/etc/php/php.ini'
            }
        elif os_type == 'fedora':
            return {'fedora': '/etc/php.ini'}
        elif os_type == 'arch':
            return {'arch': '/etc/php/php.ini'}
        
        return {}
    
    def get_configuration_options(self) -> List[Dict[str, Any]]:
        """PHP configuration options"""
        return [
            {
                'name': 'version',
                'display_name': 'PHP Version',
                'type': 'select',
                'options': self.available_versions,
                'default': self.active_version or '8.2',
                'description': 'Active PHP version'
            },
            {
                'name': 'memory_limit',
                'display_name': 'Memory Limit',
                'type': 'string',
                'default': '128M',
                'description': 'Maximum memory per script'
            },
            {
                'name': 'max_execution_time',
                'display_name': 'Max Execution Time',
                'type': 'int',
                'default': 30,
                'description': 'Maximum execution time in seconds'
            },
            {
                'name': 'upload_max_filesize',
                'display_name': 'Upload Max Filesize',
                'type': 'string',
                'default': '2M',
                'description': 'Maximum upload file size'
            },
            {
                'name': 'post_max_size',
                'display_name': 'Post Max Size',
                'type': 'string',
                'default': '8M',
                'description': 'Maximum POST data size'
            }
        ]
    
    # ==================== VERSION MANAGEMENT ====================
    
    def _refresh_installed_versions(self):
        """Refresh list of installed PHP versions"""
        self.installed_versions = []
        os_type = self.platform_manager.os_type.value
        
        if os_type in ['ubuntu', 'debian']:
            for version in self.available_versions:
                if self.platform_manager.is_package_installed(f'php{version}-fpm'):
                    self.installed_versions.append(version)
        elif os_type in ['fedora', 'arch']:
            # Fedora/Arch typically has single PHP version
            if self.platform_manager.is_package_installed('php'):
                result = subprocess.run(
                    ['php', '-v'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                if result.returncode == 0:
                    match = re.search(r'PHP (\d+\.\d+)', result.stdout)
                    if match:
                        self.installed_versions.append(match.group(1))
        
        # Set active version
        if self.installed_versions:
            self.active_version = self.installed_versions[0]
        
        logger.info(f"PHP installed versions: {self.installed_versions}")
        logger.info(f"PHP active version: {self.active_version}")
    
    def get_installed_versions(self) -> List[str]:
        """Get list of installed PHP versions"""
        self._refresh_installed_versions()
        return self.installed_versions
    
    def get_available_versions(self) -> List[str]:
        """Get list of available PHP versions"""
        return self.available_versions
    
    def install_version(self, version: str) -> Tuple[bool, str]:
        """Install specific PHP version"""
        if version not in self.available_versions:
            return False, _("Invalid PHP version: {version}").format(version=version)
        
        os_type = self.platform_manager.os_type.value
        
        try:
            if os_type in ['ubuntu', 'debian']:
                logger.info(f"Installing PHP {version} with ondrej/php repository...")
                
                # Tüm işlemleri tek bir script'te yap (tek password)
                packages = [
                    f'php{version}-fpm',
                    f'php{version}-cli',
                    f'php{version}-common',
                    f'php{version}-mysql',
                    f'php{version}-xml',
                    f'php{version}-curl',
                    f'php{version}-mbstring',
                    f'php{version}-zip',
                    f'php{version}-gd'
                ]
                
                packages_str = ' '.join(packages)
                
                # Bash script oluştur
                script = f'''#!/bin/bash
export DEBIAN_FRONTEND=noninteractive

# Wait for apt lock to be released (max 5 minutes)
echo "Checking apt/dpkg locks..."
for i in {{1..60}}; do
    if ! fuser /var/lib/dpkg/lock-frontend >/dev/null 2>&1; then
        break
    fi
    if [ $i -eq 1 ]; then
        echo "Waiting for other package managers to finish..."
    fi
    sleep 5
done

# Check if still locked
if fuser /var/lib/dpkg/lock-frontend >/dev/null 2>&1; then
    echo "ERROR: Package manager is locked by another process"
    exit 99
fi

echo "Installing software-properties-common..."
apt-get install -y software-properties-common 2>&1 || exit 1

echo "Adding ondrej/php repository..."
add-apt-repository -y ppa:ondrej/php 2>&1 || exit 2

echo "Updating package lists..."
apt-get update 2>&1 || exit 3

echo "Installing PHP {version} packages..."
apt-get install -y {packages_str} 2>&1 || exit 4

echo "PHP {version} installation completed successfully!"
exit 0
'''
                
                # Script'i geçici dosyaya yaz
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
                    f.write(script)
                    script_path = f.name
                
                try:
                    # Script'i çalıştırılabilir yap
                    subprocess.run(['chmod', '+x', script_path], check=True)
                    
                    # Script'i pkexec ile çalıştır (tek password)
                    logger.info(f"Running installation script: {script_path}")
                    result = subprocess.run(
                        ['pkexec', 'bash', script_path],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,  # Tüm output'u stdout'a yönlendir
                        timeout=900,  # 15 dakika
                        text=True
                    )
                    
                    if result.returncode != 0:
                        error_msg = result.stdout if result.stdout else "Unknown error"
                        if "cancelled" in error_msg.lower() or "authentication" in error_msg.lower():
                            return False, _("Authentication cancelled or failed")
                        
                        # Exit code'a göre hata mesajı
                        if result.returncode == 1:
                            error_detail = "Failed to install software-properties-common"
                        elif result.returncode == 2:
                            error_detail = "Failed to add ondrej/php repository"
                        elif result.returncode == 3:
                            error_detail = "Failed to update package lists"
                        elif result.returncode == 4:
                            error_detail = "Failed to install PHP packages"
                        elif result.returncode == 99:
                            error_detail = "Package manager is locked by another process. Please wait and try again."
                        else:
                            error_detail = f"Exit code: {result.returncode}"
                        
                        logger.error(f"Installation failed ({error_detail}): {error_msg[:300]}")
                        return False, _("Installation failed: {error}").format(error=error_detail)
                    
                    logger.info(f"PHP {version} installed successfully")
                    
                finally:
                    # Geçici dosyayı sil
                    import os
                    try:
                        os.unlink(script_path)
                    except:
                        pass
            
            elif os_type == 'fedora':
                packages = ['php', 'php-fpm', 'php-cli', 'php-mysqlnd', 'php-xml', 'php-mbstring']
                for package in packages:
                    cmd = self.platform_manager.get_install_command(package)
                    result = subprocess.run(
                        cmd,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.PIPE,
                        timeout=600,
                        text=True,
                        check=False
                    )
            
            elif os_type == 'arch':
                packages = ['php', 'php-fpm']
                for package in packages:
                    cmd = self.platform_manager.get_install_command(package)
                    result = subprocess.run(
                        cmd,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.PIPE,
                        timeout=600,
                        text=True,
                        check=False
                    )
            
            self._refresh_installed_versions()
            return True, _("PHP {version} installed successfully").format(version=version)
        
        except subprocess.TimeoutExpired:
            logger.error("PHP installation timeout")
            return False, _("Installation timed out (>15 minutes)")
        except Exception as e:
            logger.error(f"PHP version install error: {e}")
            return False, _("Installation error: {error}").format(error=str(e))
    
    def uninstall_version(self, version: str) -> Tuple[bool, str]:
        """Uninstall specific PHP version"""
        if version not in self.installed_versions:
            return False, _("PHP {version} is not installed").format(version=version)
        
        os_type = self.platform_manager.os_type.value
        
        try:
            if os_type in ['ubuntu', 'debian']:
                logger.info(f"Uninstalling PHP {version}...")
                
                # Tek script ile tüm işlemleri yap
                script = f'''#!/bin/bash
export DEBIAN_FRONTEND=noninteractive

systemctl stop php{version}-fpm.service 2>&1 || true
systemctl disable php{version}-fpm.service 2>&1 || true
apt-get remove -y php{version}-* 2>&1 || exit 1
apt-get autoremove -y 2>&1 || true

exit 0
'''
                
                # Script'i geçici dosyaya yaz
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
                    f.write(script)
                    script_path = f.name
                
                try:
                    # Script'i çalıştırılabilir yap
                    subprocess.run(['chmod', '+x', script_path], check=True)
                    
                    # Script'i pkexec ile çalıştır
                    logger.info(f"Running uninstallation script: {script_path}")
                    result = subprocess.run(
                        ['pkexec', 'bash', script_path],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,  # Tüm output'u stdout'a yönlendir
                        timeout=600,  # 10 dakika
                        text=True
                    )
                    
                    if result.returncode != 0:
                        error_msg = result.stdout if result.stdout else "Unknown error"
                        if "cancelled" in error_msg.lower() or "authentication" in error_msg.lower():
                            return False, _("Authentication cancelled or failed")
                        logger.error(f"Uninstallation had errors: {error_msg[:300]}")
                        # Hata olsa bile devam et, başarılı say
                    
                    logger.info(f"PHP {version} uninstalled successfully")
                    
                finally:
                    # Geçici dosyayı sil
                    import os
                    try:
                        os.unlink(script_path)
                    except:
                        pass
            
            self._refresh_installed_versions()
            return True, _("PHP {version} uninstalled successfully").format(version=version)
        
        except subprocess.TimeoutExpired:
            logger.error("PHP uninstall timeout")
            return False, _("Uninstall timed out (>10 minutes)")
        except Exception as e:
            logger.error(f"PHP version uninstall error: {e}")
            return False, _("Uninstall error: {error}").format(error=str(e))
    
    def switch_version(self, version: str) -> Tuple[bool, str]:
        """Switch active PHP version"""
        if version not in self.installed_versions:
            return False, _("PHP {version} is not installed").format(version=version)
        
        os_type = self.platform_manager.os_type.value
        
        try:
            if os_type in ['ubuntu', 'debian']:
                # Stop current version
                if self.active_version:
                    old_service = f'php{self.active_version}-fpm.service'
                    subprocess.run(['pkexec', 'systemctl', 'stop', old_service], check=False)
                    subprocess.run(['pkexec', 'systemctl', 'disable', old_service], check=False)
                
                # Start new version
                new_service = f'php{version}-fpm.service'
                subprocess.run(['pkexec', 'systemctl', 'enable', new_service], check=False)
                subprocess.run(['pkexec', 'systemctl', 'start', new_service], check=False)
                
                # Update alternatives
                subprocess.run(
                    ['pkexec', 'update-alternatives', '--set', 'php', f'/usr/bin/php{version}'],
                    check=False
                )
                
                self.active_version = version
                return True, _("Switched to PHP {version}").format(version=version)
            
            return False, _("Version switching not supported on this OS")
        
        except Exception as e:
            logger.error(f"PHP version switch error: {e}")
            return False, _("Switch error: {error}").format(error=str(e))
    
    # ==================== EXTENSION MANAGEMENT ====================
    
    def get_installed_extensions(self, version: Optional[str] = None) -> List[str]:
        """Get list of installed PHP extensions"""
        if not version:
            version = self.active_version
        
        if not version:
            return []
        
        try:
            result = subprocess.run(
                [f'php{version}', '-m'] if version else ['php', '-m'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            if result.returncode == 0:
                extensions = result.stdout.strip().split('\n')
                # Filter out section headers
                return [ext.strip() for ext in extensions if ext.strip() and not ext.startswith('[')]
            
            return []
        
        except Exception as e:
            logger.error(f"Get extensions error: {e}")
            return []
    
    def install_extension(self, extension: str, version: Optional[str] = None) -> Tuple[bool, str]:
        """Install PHP extension"""
        if not version:
            version = self.active_version
        
        if not version:
            return False, _("No PHP version specified")
        
        os_type = self.platform_manager.os_type.value
        
        try:
            if os_type in ['ubuntu', 'debian']:
                package = f'php{version}-{extension}'
                cmd = self.platform_manager.get_install_command(package)
                
                result = subprocess.run(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                    timeout=300,  # 5 dakika
                    text=True
                )
                
                if result.returncode == 0:
                    # Restart PHP-FPM
                    subprocess.run(
                        ['pkexec', 'systemctl', 'restart', f'php{version}-fpm.service'],
                        check=False
                    )
                    return True, _("Extension {ext} installed").format(ext=extension)
                else:
                    return False, _("Installation failed: {error}").format(error=result.stderr[:200] if result.stderr else "Unknown error")
            
            return False, _("Extension installation not supported on this OS")
        
        except Exception as e:
            logger.error(f"Extension install error: {e}")
            return False, _("Installation error: {error}").format(error=str(e))
    
    def uninstall_extension(self, extension: str, version: Optional[str] = None) -> Tuple[bool, str]:
        """Uninstall PHP extension"""
        if not version:
            version = self.active_version
        
        if not version:
            return False, _("No PHP version specified")
        
        os_type = self.platform_manager.os_type.value
        
        try:
            if os_type in ['ubuntu', 'debian']:
                package = f'php{version}-{extension}'
                cmd = self.platform_manager.get_remove_command(package)
                
                result = subprocess.run(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                    timeout=300,  # 5 dakika
                    text=True
                )
                
                if result.returncode == 0:
                    # Restart PHP-FPM
                    subprocess.run(
                        ['pkexec', 'systemctl', 'restart', f'php{version}-fpm.service'],
                        check=False
                    )
                    return True, _("Extension {ext} uninstalled").format(ext=extension)
                else:
                    return False, _("Uninstall failed: {error}").format(error=result.stderr[:200] if result.stderr else "Unknown error")
            
            return False, _("Extension uninstallation not supported on this OS")
        
        except Exception as e:
            logger.error(f"Extension uninstall error: {e}")
            return False, _("Uninstall error: {error}").format(error=str(e))
    
    # ==================== BASE SERVICE IMPLEMENTATION ====================
    
    def is_installed(self) -> bool:
        """Check if any PHP version is installed"""
        self._refresh_installed_versions()
        return len(self.installed_versions) > 0
    
    def install(self) -> Tuple[bool, str]:
        """Install default PHP version (8.2)"""
        logger.info("Installing default PHP version 8.2")
        return self.install_version('8.2')
    
    def uninstall(self) -> Tuple[bool, str]:
        """Uninstall all PHP versions"""
        if not self.installed_versions:
            return False, _("PHP is not installed")
        
        errors = []
        for version in self.installed_versions[:]:  # Copy list
            success, message = self.uninstall_version(version)
            if not success:
                errors.append(f"{version}: {message}")
        
        if errors:
            return False, _("Errors: {errors}").format(errors=", ".join(errors))
        
        return True, _("All PHP versions uninstalled")
    
    def start(self) -> Tuple[bool, str]:
        """Start PHP-FPM service"""
        if not self.is_installed():
            return False, _("PHP is not installed")
        
        if not self.active_version:
            return False, _("No active PHP version")
        
        try:
            service_name = self.systemd_service_name
            cmd = self.platform_manager.get_service_command('start', service_name)
            
            result = subprocess.run(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                timeout=30,
                text=True
            )
            
            if result.returncode == 0:
                return True, _("PHP {version} started").format(version=self.active_version)
            else:
                return False, _("Start error: {error}").format(error=result.stderr[:200] if result.stderr else "Unknown error")
        
        except Exception as e:
            logger.error(f"Start error: {e}")
            return False, _("Start error: {error}").format(error=str(e))
    
    def stop(self) -> Tuple[bool, str]:
        """Stop PHP-FPM service"""
        if not self.is_installed():
            return False, _("PHP is not installed")
        
        if not self.active_version:
            return False, _("No active PHP version")
        
        try:
            service_name = self.systemd_service_name
            cmd = self.platform_manager.get_service_command('stop', service_name)
            
            result = subprocess.run(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                timeout=30,
                text=True
            )
            
            if result.returncode == 0:
                return True, _("PHP {version} stopped").format(version=self.active_version)
            else:
                return False, _("Stop error: {error}").format(error=result.stderr[:200] if result.stderr else "Unknown error")
        
        except Exception as e:
            logger.error(f"Stop error: {e}")
            return False, _("Stop error: {error}").format(error=str(e))
    
    def restart(self) -> Tuple[bool, str]:
        """Restart PHP-FPM service"""
        if not self.is_installed():
            return False, _("PHP is not installed")
        
        if not self.active_version:
            return False, _("No active PHP version")
        
        try:
            service_name = self.systemd_service_name
            cmd = self.platform_manager.get_service_command('restart', service_name)
            
            result = subprocess.run(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                timeout=30,
                text=True
            )
            
            if result.returncode == 0:
                return True, _("PHP {version} restarted").format(version=self.active_version)
            else:
                return False, _("Restart error: {error}").format(error=result.stderr[:200] if result.stderr else "Unknown error")
        
        except Exception as e:
            logger.error(f"Restart error: {e}")
            return False, _("Restart error: {error}").format(error=str(e))
    
    def is_running(self) -> bool:
        """Check if PHP-FPM is running"""
        if not self.is_installed() or not self.active_version:
            return False
        
        service_name = self.systemd_service_name
        return self.platform_manager.is_service_active(service_name)
    
    def enable(self) -> Tuple[bool, str]:
        """Enable PHP-FPM autostart"""
        if not self.is_installed():
            return False, _("PHP is not installed")
        
        if not self.active_version:
            return False, _("No active PHP version")
        
        try:
            service_name = self.systemd_service_name
            cmd = self.platform_manager.get_service_command('enable', service_name)
            
            result = subprocess.run(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                timeout=30,
                text=True
            )
            
            if result.returncode == 0:
                return True, _("PHP {version} autostart enabled").format(version=self.active_version)
            else:
                return False, _("Enable error: {error}").format(error=result.stderr[:200] if result.stderr else "Unknown error")
        
        except Exception as e:
            logger.error(f"Enable error: {e}")
            return False, _("Enable error: {error}").format(error=str(e))
    
    def disable(self) -> Tuple[bool, str]:
        """Disable PHP-FPM autostart"""
        if not self.is_installed():
            return False, _("PHP is not installed")
        
        if not self.active_version:
            return False, _("No active PHP version")
        
        try:
            service_name = self.systemd_service_name
            cmd = self.platform_manager.get_service_command('disable', service_name)
            
            result = subprocess.run(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                timeout=30,
                text=True
            )
            
            if result.returncode == 0:
                return True, _("PHP {version} autostart disabled").format(version=self.active_version)
            else:
                return False, _("Disable error: {error}").format(error=result.stderr[:200] if result.stderr else "Unknown error")
        
        except Exception as e:
            logger.error(f"Disable error: {e}")
            return False, _("Disable error: {error}").format(error=str(e))
