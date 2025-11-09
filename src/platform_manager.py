"""
Platform Manager - İşletim Sistemi ve Sistem Bilgileri

Bu modül SADECE bilgi toplar ve sağlar - işlem yapmaz!
- OS detection (Fedora, Debian/Ubuntu, Arch)
- Package manager detection (dnf, apt, pacman)
- Package installation status (read-only)
- Service status (read-only)

Prensip: Scripts işlem yapar, PlatformManager sadece bilgi verir.
"""

import os
import subprocess
import platform
from enum import Enum
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class OSType(Enum):
    """Desteklenen işletim sistemi tipleri"""
    FEDORA = "fedora"
    DEBIAN = "debian"
    UBUNTU = "ubuntu"
    ARCH = "arch"
    UNKNOWN = "unknown"


class PackageManager(Enum):
    """Paket yöneticisi tipleri"""
    DNF = "dnf"
    YUM = "yum"
    APT = "apt"
    PACMAN = "pacman"
    UNKNOWN = "unknown"


class PlatformManager:
    """Platform yönetimi ve sistem bilgilerini sağlar"""
    
    def __init__(self):
        self.os_type: OSType = OSType.UNKNOWN
        self.package_manager: PackageManager = PackageManager.UNKNOWN
        self.os_version: str = ""
        self.os_name: str = ""
        self.kernel_version: str = ""
        
        # Sistem bilgilerini topla
        self._detect_os()
        self._detect_package_manager()
        self._get_system_info()
    
    def _detect_os(self) -> None:
        """İşletim sistemini /etc/os-release dosyasından tespit et"""
        try:
            if os.path.exists('/etc/os-release'):
                with open('/etc/os-release', 'r') as f:
                    lines = f.readlines()
                    os_info = {}
                    for line in lines:
                        if '=' in line:
                            key, value = line.strip().split('=', 1)
                            os_info[key] = value.strip('"')
                    
                    # ID ve ID_LIKE alanlarını kontrol et
                    os_id = os_info.get('ID', '').lower()
                    id_like = os_info.get('ID_LIKE', '').lower()
                    self.os_name = os_info.get('NAME', 'Unknown')
                    self.os_version = os_info.get('VERSION_ID', 'Unknown')
                    
                    # OS tipini belirle
                    if 'fedora' in os_id:
                        self.os_type = OSType.FEDORA
                    elif 'ubuntu' in os_id:
                        self.os_type = OSType.UBUNTU
                    elif 'debian' in os_id or 'debian' in id_like:
                        self.os_type = OSType.DEBIAN
                    elif 'arch' in os_id or 'arch' in id_like:
                        self.os_type = OSType.ARCH
                    else:
                        logger.warning(f"Desteklenmeyen OS: {os_id}")
                        self.os_type = OSType.UNKNOWN
                    
                    logger.info(f"OS tespit edildi: {self.os_type.value} - {self.os_name} {self.os_version}")
            else:
                logger.error("/etc/os-release dosyası bulunamadı")
        except Exception as e:
            logger.error(f"OS tespiti başarısız: {e}")
    
    def _detect_package_manager(self) -> None:
        """Uygun paket yöneticisini tespit et"""
        package_managers = {
            PackageManager.DNF: 'dnf',
            PackageManager.YUM: 'yum',
            PackageManager.APT: 'apt',
            PackageManager.PACMAN: 'pacman'
        }
        
        # OS tipine göre öncelikli paket yöneticisini belirle
        priority_map = {
            OSType.FEDORA: [PackageManager.DNF, PackageManager.YUM],
            OSType.DEBIAN: [PackageManager.APT],
            OSType.UBUNTU: [PackageManager.APT],
            OSType.ARCH: [PackageManager.PACMAN]
        }
        
        priority = priority_map.get(self.os_type, list(package_managers.keys()))
        
        # Öncelik sırasına göre kontrol et
        for pm in priority:
            if self._command_exists(package_managers[pm]):
                self.package_manager = pm
                logger.info(f"Paket yöneticisi tespit edildi: {pm.value}")
                return
        
        logger.error("Desteklenen bir paket yöneticisi bulunamadı")
    
    def _command_exists(self, command: str) -> bool:
        """Bir komutun sistemde mevcut olup olmadığını kontrol et"""
        try:
            result = subprocess.run(
                ['which', command],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def _get_system_info(self) -> None:
        """Sistem bilgilerini topla"""
        try:
            self.kernel_version = platform.release()
        except Exception as e:
            logger.error(f"Kernel versiyonu alınamadı: {e}")
            self.kernel_version = "Unknown"
    
    # ============================================
    # PACKAGE INFORMATION (READ-ONLY)
    # ============================================
    
    def is_package_installed(self, package_name: str) -> bool:
        """Paketin kurulu olup olmadığını kontrol et"""
        try:
            if self.package_manager == PackageManager.DNF:
                result = subprocess.run(
                    ['rpm', '-q', package_name],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=10
                )
                return result.returncode == 0
            
            elif self.package_manager == PackageManager.APT:
                result = subprocess.run(
                    ['dpkg', '-l', package_name],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=10
                )
                return result.returncode == 0 and 'ii' in result.stdout.decode()
            
            elif self.package_manager == PackageManager.PACMAN:
                result = subprocess.run(
                    ['pacman', '-Q', package_name],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=10
                )
                return result.returncode == 0
            
            return False
        except Exception as e:
            logger.error(f"Paket kontrolü başarısız ({package_name}): {e}")
            return False
    
    # ============================================
    # SERVICE INFORMATION (READ-ONLY)
    # ============================================
    
    def is_service_active(self, service_name: str) -> bool:
        """Servisin aktif olup olmadığını kontrol et"""
        try:
            result = subprocess.run(
                ['systemctl', 'is-active', service_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5
            )
            return result.stdout.decode().strip() == 'active'
        except Exception as e:
            logger.error(f"Servis kontrolü başarısız ({service_name}): {e}")
            return False
    
    # ============================================
    # SYSTEM INFORMATION
    # ============================================
    
    def get_system_info_dict(self) -> Dict[str, str]:
        """Sistem bilgilerini dict olarak döndür"""
        return {
            'os_type': self.os_type.value,
            'os_name': self.os_name,
            'os_version': self.os_version,
            'kernel_version': self.kernel_version,
            'package_manager': self.package_manager.value,
            'architecture': platform.machine()
        }
