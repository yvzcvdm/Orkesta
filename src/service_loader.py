"""
Service Loader - Dinamik Servis Modülü Yükleyici

Bu modül services/ klasöründeki tüm servis modüllerini otomatik olarak
keşfeder ve yükler.
"""

import os
import sys
import importlib
import inspect
from typing import List, Dict, Optional
import logging

# BaseService import et
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.base_service import BaseService

logger = logging.getLogger(__name__)


class ServiceLoader:
    """Servis modüllerini dinamik olarak yükler"""
    
    def __init__(self, platform_manager, services_dir: Optional[str] = None):
        """
        Args:
            platform_manager: PlatformManager instance
            services_dir: Servis modüllerinin bulunduğu klasör (default: services/)
        """
        self.platform_manager = platform_manager
        
        if services_dir is None:
            # Varsayılan services/ klasörü
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.services_dir = os.path.join(os.path.dirname(current_dir), 'services')
        else:
            self.services_dir = services_dir
        
        self.services: Dict[str, BaseService] = {}
        self._load_services()
    
    def _load_services(self) -> None:
        """services/ klasöründeki tüm servis modüllerini yükle"""
        if not os.path.exists(self.services_dir):
            logger.error(f"Servis klasörü bulunamadı: {self.services_dir}")
            return
        
        logger.info(f"Servisler yükleniyor: {self.services_dir}")
        
        # services/ klasörünü Python path'e ekle
        if self.services_dir not in sys.path:
            sys.path.insert(0, os.path.dirname(self.services_dir))
        
        # .py dosyalarını listele
        service_files = [
            f for f in os.listdir(self.services_dir)
            if f.endswith('.py') and not f.startswith('_') and f != 'base_service.py'
        ]
        
        logger.info(f"Bulunan servis dosyaları: {service_files}")
        
        for service_file in service_files:
            module_name = service_file[:-3]  # .py uzantısını kaldır
            self._load_service_module(module_name)
    
    def _load_service_module(self, module_name: str) -> None:
        """Tek bir servis modülünü yükle"""
        try:
            # Modülü import et
            module = importlib.import_module(f'services.{module_name}')
            
            # Modül içindeki BaseService'ten türetilmiş sınıfları bul
            for name, obj in inspect.getmembers(module, inspect.isclass):
                # BaseService'ten türetilmiş mi ve BaseService'in kendisi değil mi?
                if (issubclass(obj, BaseService) and 
                    obj is not BaseService and
                    obj.__module__ == f'services.{module_name}'):
                    
                    try:
                        # Servis instance'ı oluştur
                        service_instance = obj(self.platform_manager)
                        service_key = service_instance.name.lower()
                        
                        self.services[service_key] = service_instance
                        logger.info(f"Servis yüklendi: {service_instance.display_name} ({module_name})")
                    
                    except Exception as e:
                        logger.error(f"Servis instance oluşturma hatası ({name}): {e}")
        
        except ImportError as e:
            logger.error(f"Modül import hatası ({module_name}): {e}")
        except Exception as e:
            logger.error(f"Modül yükleme hatası ({module_name}): {e}")
    
    def get_service(self, service_name: str) -> Optional[BaseService]:
        """
        Servis adına göre servis instance'ını döndür
        
        Args:
            service_name: Servis adı (örn: 'apache', 'mysql')
        
        Returns:
            BaseService instance veya None
        """
        return self.services.get(service_name.lower())
    
    def get_all_services(self) -> List[BaseService]:
        """Tüm yüklenmiş servisleri liste olarak döndür"""
        return list(self.services.values())
    
    def get_services_by_type(self, service_type: str) -> List[BaseService]:
        """
        Tipe göre servisleri filtrele
        
        Args:
            service_type: 'web_server', 'database', 'cache', etc.
        
        Returns:
            Filtrelenmiş servis listesi
        """
        return [
            service for service in self.services.values()
            if service.service_type.value == service_type
        ]
    
    def get_installed_services(self) -> List[BaseService]:
        """Kurulu servisleri döndür"""
        return [
            service for service in self.services.values()
            if service.is_installed()
        ]
    
    def get_running_services(self) -> List[BaseService]:
        """Çalışan servisleri döndür"""
        return [
            service for service in self.services.values()
            if service.is_running()
        ]
    
    def reload_services(self) -> None:
        """Servisleri yeniden yükle"""
        logger.info("Servisler yeniden yükleniyor...")
        self.services.clear()
        
        # Cache'i temizle
        for module_name in list(sys.modules.keys()):
            if module_name.startswith('services.') and module_name != 'services.base_service':
                del sys.modules[module_name]
        
        self._load_services()
    
    def get_service_count(self) -> Dict[str, int]:
        """Servis istatistikleri döndür"""
        return {
            'total': len(self.services),
            'installed': len(self.get_installed_services()),
            'running': len(self.get_running_services())
        }
