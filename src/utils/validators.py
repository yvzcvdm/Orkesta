"""
Validators - Veri Doğrulama Fonksiyonları

Port numarası, IP adresi, dosya yolu vb. doğrulama işlemleri.
"""

import os
import re
from typing import Optional
import ipaddress


def validate_port(port: int) -> tuple[bool, Optional[str]]:
    """
    Port numarasını doğrula
    
    Args:
        port: Port numarası
    
    Returns:
        (is_valid: bool, error_message: Optional[str])
    """
    if not isinstance(port, int):
        return False, "Port bir sayı olmalıdır"
    
    if port < 1 or port > 65535:
        return False, "Port numarası 1-65535 arasında olmalıdır"
    
    if port < 1024:
        return True, "Düşük port numarası (root izni gerekebilir)"
    
    return True, None


def validate_ip_address(ip: str) -> tuple[bool, Optional[str]]:
    """
    IP adresini doğrula
    
    Args:
        ip: IP adresi
    
    Returns:
        (is_valid: bool, error_message: Optional[str])
    """
    try:
        ipaddress.ip_address(ip)
        return True, None
    except ValueError:
        return False, "Geçersiz IP adresi"


def validate_hostname(hostname: str) -> tuple[bool, Optional[str]]:
    """
    Hostname'i doğrula
    
    Args:
        hostname: Hostname
    
    Returns:
        (is_valid: bool, error_message: Optional[str])
    """
    if not hostname:
        return False, "Hostname boş olamaz"
    
    if len(hostname) > 253:
        return False, "Hostname çok uzun (max 253 karakter)"
    
    # Hostname pattern
    pattern = r'^(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.[A-Za-z0-9-]{1,63})*$'
    
    if re.match(pattern, hostname):
        return True, None
    else:
        return False, "Geçersiz hostname formatı"


def validate_file_path(path: str, must_exist: bool = False) -> tuple[bool, Optional[str]]:
    """
    Dosya yolunu doğrula
    
    Args:
        path: Dosya yolu
        must_exist: Dosyanın var olması gerekiyor mu
    
    Returns:
        (is_valid: bool, error_message: Optional[str])
    """
    if not path:
        return False, "Dosya yolu boş olamaz"
    
    # Absolute path kontrolü
    if not os.path.isabs(path):
        return False, "Dosya yolu absolute olmalıdır"
    
    if must_exist:
        if not os.path.exists(path):
            return False, "Dosya bulunamadı"
        
        if not os.path.isfile(path):
            return False, "Belirtilen yol bir dosya değil"
    
    return True, None


def validate_directory_path(path: str, must_exist: bool = False) -> tuple[bool, Optional[str]]:
    """
    Dizin yolunu doğrula
    
    Args:
        path: Dizin yolu
        must_exist: Dizinin var olması gerekiyor mu
    
    Returns:
        (is_valid: bool, error_message: Optional[str])
    """
    if not path:
        return False, "Dizin yolu boş olamaz"
    
    # Absolute path kontrolü
    if not os.path.isabs(path):
        return False, "Dizin yolu absolute olmalıdır"
    
    if must_exist:
        if not os.path.exists(path):
            return False, "Dizin bulunamadı"
        
        if not os.path.isdir(path):
            return False, "Belirtilen yol bir dizin değil"
    
    return True, None


def validate_database_name(db_name: str) -> tuple[bool, Optional[str]]:
    """
    Veritabanı adını doğrula
    
    Args:
        db_name: Veritabanı adı
    
    Returns:
        (is_valid: bool, error_message: Optional[str])
    """
    if not db_name:
        return False, "Veritabanı adı boş olamaz"
    
    if len(db_name) > 64:
        return False, "Veritabanı adı çok uzun (max 64 karakter)"
    
    # Sadece harf, rakam ve alt çizgi
    pattern = r'^[a-zA-Z0-9_]+$'
    
    if not re.match(pattern, db_name):
        return False, "Veritabanı adı sadece harf, rakam ve alt çizgi içerebilir"
    
    # Rakamla başlamamalı
    if db_name[0].isdigit():
        return False, "Veritabanı adı rakamla başlayamaz"
    
    return True, None


def validate_username(username: str) -> tuple[bool, Optional[str]]:
    """
    Kullanıcı adını doğrula
    
    Args:
        username: Kullanıcı adı
    
    Returns:
        (is_valid: bool, error_message: Optional[str])
    """
    if not username:
        return False, "Kullanıcı adı boş olamaz"
    
    if len(username) < 3:
        return False, "Kullanıcı adı en az 3 karakter olmalıdır"
    
    if len(username) > 32:
        return False, "Kullanıcı adı çok uzun (max 32 karakter)"
    
    # Sadece harf, rakam ve alt çizgi
    pattern = r'^[a-zA-Z0-9_]+$'
    
    if not re.match(pattern, username):
        return False, "Kullanıcı adı sadece harf, rakam ve alt çizgi içerebilir"
    
    return True, None


def validate_password(password: str, min_length: int = 8) -> tuple[bool, Optional[str]]:
    """
    Şifre güvenliğini doğrula
    
    Args:
        password: Şifre
        min_length: Minimum uzunluk
    
    Returns:
        (is_valid: bool, error_message: Optional[str])
    """
    if not password:
        return False, "Şifre boş olamaz"
    
    if len(password) < min_length:
        return False, f"Şifre en az {min_length} karakter olmalıdır"
    
    # En az bir büyük harf
    if not re.search(r'[A-Z]', password):
        return False, "Şifre en az bir büyük harf içermelidir"
    
    # En az bir küçük harf
    if not re.search(r'[a-z]', password):
        return False, "Şifre en az bir küçük harf içermelidir"
    
    # En az bir rakam
    if not re.search(r'[0-9]', password):
        return False, "Şifre en az bir rakam içermelidir"
    
    return True, None
