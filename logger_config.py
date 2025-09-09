"""
Logging configuration cho Factorio Mod Translator
"""
import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """Custom formatter với màu sắc cho console output"""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green  
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record):
        # Add color to levelname
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['RESET']}"
        
        return super().format(record)


class LoggerManager:
    """Manager cho logging system"""
    
    def __init__(self, app_name: str = "FactorioModTranslator", log_dir: str = "logs"):
        self.app_name = app_name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Tạo các log files
        self.main_log_file = self.log_dir / "app.log"
        self.error_log_file = self.log_dir / "errors.log"
        self.debug_log_file = self.log_dir / "debug.log"
        
        self._setup_loggers()
    
    def _setup_loggers(self):
        """Setup tất cả loggers"""
        # Main logger
        self.logger = logging.getLogger(self.app_name)
        self.logger.setLevel(logging.DEBUG)
        self.logger.handlers.clear()  # Clear existing handlers
        
        # Console handler với màu sắc
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = ColoredFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler cho tất cả logs
        file_handler = logging.handlers.RotatingFileHandler(
            self.main_log_file,
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
        # Error file handler
        error_handler = logging.handlers.RotatingFileHandler(
            self.error_log_file,
            maxBytes=2*1024*1024,  # 2MB
            backupCount=2,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        self.logger.addHandler(error_handler)
        
        # Debug file handler (optional, chỉ khi debug mode)
        if self._is_debug_mode():
            debug_handler = logging.handlers.RotatingFileHandler(
                self.debug_log_file,
                maxBytes=10*1024*1024,  # 10MB
                backupCount=2,
                encoding='utf-8'
            )
            debug_handler.setLevel(logging.DEBUG)
            debug_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(module)s.%(funcName)s:%(lineno)d - %(message)s'
            )
            debug_handler.setFormatter(debug_formatter)
            self.logger.addHandler(debug_handler)
    
    def _is_debug_mode(self) -> bool:
        """Kiểm tra có đang ở debug mode không"""
        return os.getenv('DEBUG', '').lower() in ['1', 'true', 'yes']
    
    def get_logger(self, name: Optional[str] = None) -> logging.Logger:
        """
        Lấy logger instance
        
        Args:
            name: Tên của logger (optional)
            
        Returns:
            Logger instance
        """
        if name:
            return logging.getLogger(f"{self.app_name}.{name}")
        return self.logger
    
    def set_level(self, level: int):
        """Set logging level cho console output"""
        for handler in self.logger.handlers:
            if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
                handler.setLevel(level)
    
    def log_system_info(self):
        """Log thông tin system"""
        import platform
        import sys
        
        logger = self.get_logger("system")
        logger.info("="*50)
        logger.info(f"Application: {self.app_name}")
        logger.info(f"Python Version: {sys.version}")
        logger.info(f"Platform: {platform.platform()}")
        logger.info(f"Architecture: {platform.architecture()}")
        logger.info(f"Processor: {platform.processor()}")
        logger.info(f"Current Time: {datetime.now().isoformat()}")
        logger.info("="*50)
    
    def log_translation_start(self, mod_count: int, target_lang: str, endpoint: str):
        """Log bắt đầu translation"""
        logger = self.get_logger("translation")
        logger.info(f"Starting translation process:")
        logger.info(f"  - Mods to translate: {mod_count}")
        logger.info(f"  - Target language: {target_lang}")
        logger.info(f"  - DeepL endpoint: {endpoint}")
    
    def log_translation_progress(self, current: int, total: int, mod_name: str):
        """Log tiến độ translation"""
        logger = self.get_logger("translation")
        percentage = (current / total) * 100 if total > 0 else 0
        logger.info(f"Progress: {current}/{total} ({percentage:.1f}%) - Processing: {mod_name}")
    
    def log_translation_complete(self, success_count: int, failed_count: int, duration: float):
        """Log kết thúc translation"""
        logger = self.get_logger("translation")
        logger.info(f"Translation completed:")
        logger.info(f"  - Successful: {success_count}")
        logger.info(f"  - Failed: {failed_count}")
        logger.info(f"  - Duration: {duration:.2f}s")
    
    def log_api_usage(self, character_count: int, character_limit: int):
        """Log API usage"""
        logger = self.get_logger("api")
        percentage = (character_count / character_limit) * 100 if character_limit > 0 else 0
        logger.info(f"DeepL API Usage: {character_count:,}/{character_limit:,} characters ({percentage:.1f}%)")
    
    def log_file_operation(self, operation: str, file_path: str, success: bool, details: str = ""):
        """Log file operations"""
        logger = self.get_logger("file")
        status = "SUCCESS" if success else "FAILED"
        message = f"File {operation} {status}: {file_path}"
        if details:
            message += f" - {details}"
        
        if success:
            logger.info(message)
        else:
            logger.error(message)
    
    def log_error(self, error: Exception, context: str = ""):
        """Log errors với full traceback"""
        logger = self.get_logger("error")
        message = f"Error in {context}: {str(error)}" if context else f"Error: {str(error)}"
        logger.error(message, exc_info=True)
    
    def cleanup_old_logs(self, days_to_keep: int = 7):
        """Cleanup logs cũ hơn n ngày"""
        try:
            import time
            cutoff_time = time.time() - (days_to_keep * 24 * 60 * 60)
            
            for log_file in self.log_dir.glob("*.log*"):
                if log_file.stat().st_mtime < cutoff_time:
                    log_file.unlink()
                    self.logger.info(f"Cleaned up old log file: {log_file}")
                    
        except Exception as e:
            self.logger.error(f"Failed to cleanup old logs: {e}")


# Global logger manager instance
_logger_manager: Optional[LoggerManager] = None


def setup_logging(app_name: str = "FactorioModTranslator", log_dir: str = "logs") -> LoggerManager:
    """
    Setup logging cho toàn bộ ứng dụng
    
    Args:
        app_name: Tên ứng dụng
        log_dir: Thư mục chứa log files
        
    Returns:
        LoggerManager instance
    """
    global _logger_manager
    _logger_manager = LoggerManager(app_name, log_dir)
    _logger_manager.log_system_info()
    return _logger_manager


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Lấy logger instance
    
    Args:
        name: Tên logger (optional)
        
    Returns:
        Logger instance
    """
    global _logger_manager
    if _logger_manager is None:
        _logger_manager = setup_logging()
    return _logger_manager.get_logger(name)


def get_logger_manager() -> LoggerManager:
    """Lấy logger manager instance"""
    global _logger_manager
    if _logger_manager is None:
        _logger_manager = setup_logging()
    return _logger_manager


# Convenience functions
def log_info(message: str, logger_name: Optional[str] = None):
    """Log info message"""
    get_logger(logger_name).info(message)


def log_warning(message: str, logger_name: Optional[str] = None):
    """Log warning message"""
    get_logger(logger_name).warning(message)


def log_error(message: str, logger_name: Optional[str] = None):
    """Log error message"""
    get_logger(logger_name).error(message)


def log_debug(message: str, logger_name: Optional[str] = None):
    """Log debug message"""
    get_logger(logger_name).debug(message)
