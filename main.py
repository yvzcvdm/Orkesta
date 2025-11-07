#!/usr/bin/env python3
"""
Orkesta - Web Development Environment Manager

Ana uygulama giriş noktası
"""

import sys
import os

# Proje dizinini path'e ekle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.utils import get_logger

logger = get_logger('orkesta.main')


def main():
    """Ana uygulama fonksiyonu - GTK arayüzünü başlat"""
    try:
        # GTK uygulamasını başlat
        from src.app import main as gtk_main
        return gtk_main()
    except ImportError as e:
        # GTK yüklü değilse console modunda çalış
        logger.warning(f"GTK yüklenemedi: {e}")
        logger.info("Console modunda başlatılıyor...")
        
        from src.platform_manager import PlatformManager
        from src.service_loader import ServiceLoader
        
        print("=" * 60)
        print("🎼 Orkesta - Web Development Environment Manager")
        print("=" * 60)
        print()
        
        # Platform yöneticisini başlat
        logger.info("Platform yöneticisi başlatılıyor...")
        platform_manager = PlatformManager()
        
        # Sistem bilgilerini göster
        system_info = platform_manager.get_system_info_dict()
        print("📊 Sistem Bilgileri:")
        print(f"  • İşletim Sistemi: {system_info['os_name']} {system_info['os_version']}")
        print(f"  • Dağıtım: {system_info['os_type']}")
        print(f"  • Kernel: {system_info['kernel_version']}")
        print(f"  • Mimari: {system_info['architecture']}")
        print(f"  • Paket Yöneticisi: {system_info['package_manager']}")
        print()
        
        # Servis yükleyiciyi başlat
        logger.info("Servis modülleri yükleniyor...")
        service_loader = ServiceLoader(platform_manager)
        
        # Servis istatistikleri
        stats = service_loader.get_service_count()
        print(f"📦 Servis İstatistikleri:")
        print(f"  • Toplam Servis: {stats['total']}")
        print(f"  • Kurulu Servisler: {stats['installed']}")
        print(f"  • Çalışan Servisler: {stats['running']}")
        print()
        
        # Servisleri listele
        all_services = service_loader.get_all_services()
        if all_services:
            print("🔧 Yüklü Servis Modülleri:")
            for service in all_services:
                status_icon = "✅" if service.is_installed() else "❌"
                running_icon = "🟢" if service.is_running() else "🔴"
                
                print(f"  {status_icon} {service.display_name}")
                print(f"     Tip: {service.service_type.value}")
                print(f"     Durum: {running_icon} {service.get_status().value}")
                if service.default_port:
                    print(f"     Port: {service.default_port}")
                print()
        else:
            print("⚠️  Henüz servis modülü yüklenmedi")
            print("   services/ klasörüne servis modülleri ekleyin")
            print()
        
        print("=" * 60)
        print("✨ Orkesta başarıyla başlatıldı!")
        print("=" * 60)
        print("\n⚠️  GTK arayüzü için PyGObject kurulumu gerekiyor:")
        print("   sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0 gir1.2-adw-1")
        print()
        
        return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n👋 Güle güle!")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Kritik hata: {e}", exc_info=True)
        print(f"\n❌ Hata: {e}")
        sys.exit(1)
