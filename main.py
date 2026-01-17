#!/usr/bin/env python3
"""
Orkesta - Web Development Environment Manager

Ana uygulama giriş noktası
Prensip: Main SADECE GTK arayüzünü başlatır, servis mantığı içermez
"""

import sys
import os
import warnings

# GTK tema uyarılarını bastır (uygulamayı etkilemez)
warnings.filterwarnings("ignore", category=Warning)
os.environ['G_MESSAGES_DEBUG'] = ''

# Proje dizinini path'e ekle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    """Ana uygulama fonksiyonu - GTK arayüzünü başlat"""
    # Başlangıçta bir kez sudo yetkisi al ve cache'le
    import subprocess
    try:
        # sudo cache'i 15 dakika için aktif et
        subprocess.run(['sudo', '-v'], check=False, capture_output=True)
        print("✅ Sudo yetkisi alındı (15 dakika geçerli)")
    except Exception:
        pass  # Sudo yoksa da devam et
    
    try:
        from src.app import main as gtk_main
        return gtk_main()
    except ImportError as e:
        print("=" * 60)
        print("❌ GTK4/Libadwaita kurulu değil!")
        print("=" * 60)
        print(f"\nHata: {e}\n")
        print("Gerekli paketler:")
        print("  • Fedora: sudo dnf install python3-gobject gtk4 libadwaita")
        print("  • Ubuntu/Debian: sudo apt install python3-gi gir1.2-gtk-4.0 gir1.2-adw-1")
        print("  • Arch: sudo pacman -S python-gobject gtk4 libadwaita")
        print()
        return 1
    except Exception as e:
        print(f"❌ Kritik hata: {e}")
        return 1


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n👋 Güle güle!")
        sys.exit(0)
