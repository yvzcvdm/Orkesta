"""
Logger Utility - Merkezi Loglama Yapılandırması

Uygulama genelinde kullanılacak loglama yapılandırması.
"""

import logging
import os
from datetime import datetime
from typing import Optional


class OrkestaLogger:
    """Orkestra için özelleştirilmiş logger"""
    
    _instance: Optional['OrkestaLogger'] = None
    _initialized: bool = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(OrkestaLogger, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not OrkestaLogger._initialized:
            self._setup_logging()
            OrkestaLogger._initialized = True
    
    def _setup_logging(self):
        """Logging yapılandırmasını ayarla"""
        # Log klasörü
        log_dir = os.path.expanduser('~/.local/share/orkesta/logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # Log dosyası
        log_file = os.path.join(
            log_dir,
            f'orkesta_{datetime.now().strftime("%Y%m%d")}.log'
        )
        
        # Root logger yapılandırması
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()  # Console'a da yazdır
            ]
        )
        
        # Orkesta logger
        self.logger = logging.getLogger('orkesta')
        self.logger.setLevel(logging.DEBUG)
    
    def get_logger(self, name: str = 'orkesta') -> logging.Logger:
        """Logger instance döndür"""
        return logging.getLogger(name)


def get_logger(name: str = 'orkesta') -> logging.Logger:
    """
    Logger instance al
    
    Args:
        name: Logger adı
    
    Returns:
        logging.Logger instance
    """
    orkesta_logger = OrkestaLogger()
    return orkesta_logger.get_logger(name)
