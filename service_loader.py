"""
Service Loader - Zero-Configuration Plugin Auto-Discovery

metadata.json bazlı tam otomatik plugin sistemi.
Yeni bir service klasörü eklendiğinde main.py'de hiçbir değişiklik gerekmez.
"""

import os
import sys
import json
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
            self.services_dir = os.path.join(current_dir, 'services')
        else:
            self.services_dir = services_dir
        
        self.services: Dict[str, BaseService] = {}
        self._load_services()
    
    def _load_services(self) -> None:
        """
        Zero-Configuration Plugin Auto-Discovery
        
        Her service klasöründe metadata.json varsa otomatik yüklenir:
        services/
          my-awesome-service/
            metadata.json     # {"entry_class": "MyService", ...}
            __init__.py       # class MyService(BaseService)
            script.sh         # İşlem scripti
            ui.py            # Özel UI (opsiyonel)
            icon.svg         # Servis ikonu (opsiyonel)
        
        Sunucudan indirilen service klasörü doğrudan /services/ altına
        açıldığında otomatik çalışır - main.py'de kod değişikliği gerekmez!
        """
        if not os.path.exists(self.services_dir):
            logger.error(f"Servis klasörü bulunamadı: {self.services_dir}")
            return
        
        logger.info(f"🔍 Plugin auto-discovery başlıyor: {self.services_dir}")
        
        # services/ klasörünü Python path'e ekle
        if self.services_dir not in sys.path:
            sys.path.insert(0, os.path.dirname(self.services_dir))
        
        # Tüm klasörleri tara
        for entry in os.listdir(self.services_dir):
            service_path = os.path.join(self.services_dir, entry)
            
            # Klasör değilse veya _ ile başlıyorsa atla
            if not os.path.isdir(service_path) or entry.startswith('_'):
                continue
            
            # metadata.json var mı kontrol et
            metadata_file = os.path.join(service_path, 'metadata.json')
            if os.path.exists(metadata_file):
                self._load_plugin_from_metadata(entry, metadata_file)
            else:
                # Geriye dönük uyumluluk: metadata.json yoksa klasik yükle
                init_file = os.path.join(service_path, '__init__.py')
                if os.path.exists(init_file):
                    logger.warning(f"⚠️ {entry}: metadata.json yok, klasik yöntemle yükleniyor")
                    self._load_service_classic(entry)
    
    def _load_plugin_from_metadata(self, plugin_dir: str, metadata_file: str) -> None:
        """metadata.json bazlı plugin yükleme (WordPress tarzı)"""
        try:
            # metadata.json oku
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            # Gerekli alanlar var mı?
            if 'name' not in metadata or 'entry_class' not in metadata:
                logger.error(f"❌ {plugin_dir}: metadata.json'da 'name' veya 'entry_class' eksik")
                return
            
            # Plugin devre dışı mı?
            if not metadata.get('enabled', True):
                logger.info(f"⏸️ {plugin_dir}: Plugin devre dışı (enabled=false)")
                return
            
            # Modülü import et
            module = importlib.import_module(f'services.{plugin_dir}')
            
            # entry_class'ı bul
            entry_class_name = metadata['entry_class']
            if not hasattr(module, entry_class_name):
                logger.error(f"❌ {plugin_dir}: '{entry_class_name}' sınıfı bulunamadı")
                return
            
            service_class = getattr(module, entry_class_name)
            
            # BaseService'ten türemiş mi kontrol et
            if not issubclass(service_class, BaseService):
                logger.error(f"❌ {plugin_dir}: '{entry_class_name}' BaseService'ten türememiş")
                return
            
            # Servis instance'ı oluştur
            service_instance = service_class(self.platform_manager)
            service_key = metadata['name'].lower()
            
            # Metadata'yı servise ekle
            service_instance.metadata = metadata
            service_instance.plugin_dir = os.path.join(self.services_dir, plugin_dir)
            
            self.services[service_key] = service_instance
            logger.info(f"✅ Plugin yüklendi: {metadata.get('display_name', plugin_dir)} (v{metadata.get('version', '?')})")
        
        except json.JSONDecodeError as e:
            logger.error(f"❌ {plugin_dir}: metadata.json parse hatası: {e}")
        except ImportError as e:
            logger.error(f"❌ {plugin_dir}: Import hatası: {e}")
        except Exception as e:
            logger.error(f"❌ {plugin_dir}: Yükleme hatası: {e}")
    
    def _load_service_classic(self, module_name: str) -> None:
        """Eski yapı için klasik yükleme (geriye dönük uyumluluk)"""
        try:
            module = importlib.import_module(f'services.{module_name}')
            
            # BaseService'ten türetilmiş sınıfları bul
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if (issubclass(obj, BaseService) and 
                    obj is not BaseService and
                    obj.__module__ == f'services.{module_name}'):
                    
                    service_instance = obj(self.platform_manager)
                    service_key = service_instance.name.lower()
                    
                    self.services[service_key] = service_instance
                    logger.info(f"✅ Servis yüklendi (klasik): {service_instance.display_name}")
                    break
        
        except Exception as e:
            logger.error(f"❌ Klasik yükleme hatası ({module_name}): {e}")
    
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
