"""
Çevirileri toplamak için script
"""
import os
import subprocess
from pathlib import Path

def extract_strings():
    """Python dosyalarından çevrilecek metinleri çıkar"""
    
    project_root = Path(__file__).parent
    locale_dir = project_root / 'locale'
    pot_file = locale_dir / 'orkesta.pot'
    
    # Locale dizini yoksa oluştur
    locale_dir.mkdir(exist_ok=True)
    
    # Python dosyalarını bul
    python_files = []
    for root, dirs, files in os.walk(project_root / 'src'):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    for root, dirs, files in os.walk(project_root / 'services'):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    # main.py ekle
    python_files.append(str(project_root / 'main.py'))
    
    print(f"Bulunan dosyalar: {len(python_files)}")
    
    # xgettext ile POT dosyası oluştur
    cmd = [
        'xgettext',
        '--language=Python',
        '--keyword=_',
        '--output=' + str(pot_file),
        '--from-code=UTF-8',
        '--package-name=Orkesta',
        '--package-version=1.0',
        '--msgid-bugs-address=your@email.com',
    ] + python_files
    
    try:
        subprocess.run(cmd, check=True)
        print(f"POT dosyası oluşturuldu: {pot_file}")
    except subprocess.CalledProcessError as e:
        print(f"Hata: {e}")
        print("xgettext kurulu değil olabilir: sudo apt install gettext")

def create_or_update_po(lang_code):
    """Bir dil için PO dosyası oluştur veya güncelle"""
    
    project_root = Path(__file__).parent
    locale_dir = project_root / 'locale'
    pot_file = locale_dir / 'orkesta.pot'
    
    lang_dir = locale_dir / lang_code / 'LC_MESSAGES'
    lang_dir.mkdir(parents=True, exist_ok=True)
    
    po_file = lang_dir / 'orkesta.po'
    
    if po_file.exists():
        # Güncelle
        cmd = ['msgmerge', '--update', str(po_file), str(pot_file)]
        print(f"PO dosyası güncelleniyor: {lang_code}")
    else:
        # Yeni oluştur
        cmd = ['msginit', '--input=' + str(pot_file), '--output=' + str(po_file), '--locale=' + lang_code, '--no-translator']
        print(f"Yeni PO dosyası oluşturuluyor: {lang_code}")
    
    try:
        subprocess.run(cmd, check=True)
        print(f"✓ {lang_code} PO dosyası hazır")
    except subprocess.CalledProcessError as e:
        print(f"Hata: {e}")

def compile_translations():
    """PO dosyalarını MO'ya derle"""
    
    project_root = Path(__file__).parent
    locale_dir = project_root / 'locale'
    
    for lang_dir in locale_dir.iterdir():
        if not lang_dir.is_dir():
            continue
        
        po_file = lang_dir / 'LC_MESSAGES' / 'orkesta.po'
        mo_file = lang_dir / 'LC_MESSAGES' / 'orkesta.mo'
        
        if po_file.exists():
            cmd = ['msgfmt', str(po_file), '-o', str(mo_file)]
            try:
                subprocess.run(cmd, check=True)
                print(f"✓ {lang_dir.name} derlenidi")
            except subprocess.CalledProcessError as e:
                print(f"Hata ({lang_dir.name}): {e}")

if __name__ == '__main__':
    print("=== Orkesta Çeviri Aracı ===\n")
    
    print("1. Metinler çıkartılıyor...")
    extract_strings()
    
    print("\n2. PO dosyaları oluşturuluyor/güncelleniyor...")
    # Desteklenen diller
    languages = ['tr', 'de', 'fr', 'es']
    for lang in languages:
        create_or_update_po(lang)
    
    print("\n3. Çeviriler derleniyor...")
    compile_translations()
    
    print("\n✓ Tamamlandı!")
    print("\nŞimdi locale/*/LC_MESSAGES/orkesta.po dosyalarını düzenleyip çevirileri ekleyin.")
    print("Sonra tekrar bu scripti çalıştırın.")
