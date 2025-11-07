"""
System Utilities - Sistem İşlemleri İçin Yardımcı Fonksiyonlar

Dosya işlemleri, port kontrolü ve sistem komutları için utilities.
"""

import os
import socket
import subprocess
from typing import Optional, Tuple, List
import logging

logger = logging.getLogger(__name__)


def is_port_available(port: int, host: str = '127.0.0.1') -> bool:
    """
    Portun kullanılabilir olup olmadığını kontrol et
    
    Args:
        port: Kontrol edilecek port
        host: Host adresi
    
    Returns:
        True if port is available, False otherwise
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex((host, port))
            return result != 0  # 0 = port kullanımda
    except Exception as e:
        logger.error(f"Port kontrolü hatası ({port}): {e}")
        return False


def get_process_using_port(port: int) -> Optional[str]:
    """
    Belirli bir portu kullanan process bilgisini döndür
    
    Args:
        port: Kontrol edilecek port
    
    Returns:
        Process bilgisi veya None
    """
    try:
        result = subprocess.run(
            ['lsof', '-i', f':{port}', '-t'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5
        )
        
        if result.returncode == 0:
            pid = result.stdout.decode().strip()
            if pid:
                # Process ismini al
                proc_result = subprocess.run(
                    ['ps', '-p', pid, '-o', 'comm='],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=5
                )
                if proc_result.returncode == 0:
                    return proc_result.stdout.decode().strip()
        
        return None
    except Exception as e:
        logger.error(f"Process kontrolü hatası: {e}")
        return None


def read_file(file_path: str) -> Optional[str]:
    """
    Dosya içeriğini oku
    
    Args:
        file_path: Dosya yolu
    
    Returns:
        Dosya içeriği veya None
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Dosya okuma hatası ({file_path}): {e}")
        return None


def write_file(file_path: str, content: str, backup: bool = True) -> Tuple[bool, str]:
    """
    Dosyaya yaz
    
    Args:
        file_path: Dosya yolu
        content: Yazılacak içerik
        backup: Yedek oluştur
    
    Returns:
        (success: bool, message: str)
    """
    try:
        # Yedek oluştur
        if backup and os.path.exists(file_path):
            backup_path = f"{file_path}.bak"
            subprocess.run(['sudo', 'cp', file_path, backup_path], check=True)
        
        # Geçici dosya oluştur
        temp_path = f"{file_path}.tmp"
        with open(temp_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Sudo ile taşı
        result = subprocess.run(
            ['sudo', 'mv', temp_path, file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10
        )
        
        if result.returncode == 0:
            return True, "Dosya başarıyla yazıldı"
        else:
            return False, f"Dosya yazma hatası: {result.stderr.decode()}"
    
    except Exception as e:
        logger.error(f"Dosya yazma hatası ({file_path}): {e}")
        return False, str(e)


def execute_command(command: List[str], timeout: int = 30, use_sudo: bool = False) -> Tuple[bool, str, str]:
    """
    Sistem komutu çalıştır
    
    Args:
        command: Komut listesi
        timeout: Zaman aşımı (saniye)
        use_sudo: Sudo kullan
    
    Returns:
        (success: bool, stdout: str, stderr: str)
    """
    try:
        if use_sudo and command[0] != 'sudo':
            command = ['sudo'] + command
        
        logger.info(f"Komut çalıştırılıyor: {' '.join(command)}")
        
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout
        )
        
        stdout = result.stdout.decode('utf-8')
        stderr = result.stderr.decode('utf-8')
        
        return result.returncode == 0, stdout, stderr
    
    except subprocess.TimeoutExpired:
        return False, "", "Komut zaman aşımına uğradı"
    except Exception as e:
        logger.error(f"Komut çalıştırma hatası: {e}")
        return False, "", str(e)


def check_sudo_access() -> bool:
    """
    Sudo erişiminin olup olmadığını kontrol et
    
    Returns:
        True if sudo access available
    """
    try:
        result = subprocess.run(
            ['sudo', '-n', 'true'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5
        )
        return result.returncode == 0
    except Exception:
        return False


def ensure_directory(directory: str) -> bool:
    """
    Dizinin var olduğundan emin ol, yoksa oluştur
    
    Args:
        directory: Dizin yolu
    
    Returns:
        True if successful
    """
    try:
        os.makedirs(directory, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Dizin oluşturma hatası ({directory}): {e}")
        return False


def get_file_size(file_path: str) -> Optional[int]:
    """
    Dosya boyutunu döndür (bytes)
    
    Args:
        file_path: Dosya yolu
    
    Returns:
        Dosya boyutu veya None
    """
    try:
        return os.path.getsize(file_path)
    except Exception as e:
        logger.error(f"Dosya boyutu alma hatası ({file_path}): {e}")
        return None


def is_command_available(command: str) -> bool:
    """
    Komutun sistemde mevcut olup olmadığını kontrol et
    
    Args:
        command: Komut adı
    
    Returns:
        True if available
    """
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
