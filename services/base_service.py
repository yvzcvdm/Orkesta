"""
Base Service Class
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, List, Tuple, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)

try:
    from src.utils.i18n import get_i18n
    _ = get_i18n().get_translator()
except:
    _ = lambda s: s


class ServiceStatus(Enum):
    RUNNING = "running"
    STOPPED = "stopped"
    UNKNOWN = "unknown"
    NOT_INSTALLED = "not_installed"


class ServiceType(Enum):
    WEB_SERVER = "web_server"
    DATABASE = "database"
    CACHE = "cache"
    OTHER = "other"


class BaseService(ABC):
    
    def __init__(self, platform_manager):
        self.platform_manager = platform_manager
        self._status = ServiceStatus.UNKNOWN
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @property
    @abstractmethod
    def display_name(self) -> str:
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        pass
    
    @property
    @abstractmethod
    def service_type(self) -> ServiceType:
        pass
    
    @property
    @abstractmethod
    def icon_name(self) -> str:
        pass
    
    @property
    @abstractmethod
    def package_names(self) -> Dict[str, List[str]]:
        pass
    
    @property
    @abstractmethod
    def systemd_service_name(self) -> Optional[str]:
        pass
    
    @property
    @abstractmethod
    def default_port(self) -> Optional[int]:
        pass
    
    @property
    @abstractmethod
    def config_file_paths(self) -> Dict[str, str]:
        pass
    
    @abstractmethod
    def get_configuration_options(self) -> List[Dict[str, Any]]:
        pass
    
    def get_packages_for_current_os(self) -> List[str]:
        os_type = self.platform_manager.os_type.value
        return self.package_names.get(os_type, [])
    
    def get_config_file_for_current_os(self) -> Optional[str]:
        os_type = self.platform_manager.os_type.value
        return self.config_file_paths.get(os_type)
    
    def get_status(self) -> ServiceStatus:
        if not self.is_installed():
            return ServiceStatus.NOT_INSTALLED
        elif self.is_running():
            return ServiceStatus.RUNNING
        else:
            return ServiceStatus.STOPPED
    
    @abstractmethod
    def is_installed(self) -> bool:
        pass
    
    @abstractmethod
    def install(self) -> Tuple[bool, str]:
        pass
    
    @abstractmethod
    def uninstall(self) -> Tuple[bool, str]:
        pass
    
    @abstractmethod
    def start(self) -> Tuple[bool, str]:
        pass
    
    @abstractmethod
    def stop(self) -> Tuple[bool, str]:
        pass
    
    @abstractmethod
    def restart(self) -> Tuple[bool, str]:
        pass
    
    @abstractmethod
    def is_running(self) -> bool:
        pass
    
    @abstractmethod
    def enable(self) -> Tuple[bool, str]:
        pass
    
    @abstractmethod
    def disable(self) -> Tuple[bool, str]:
        pass
