import os
import logging
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def create_folder_if_not_exists(path):
    """Создает директорию, если она не существует."""
    try:
        if not os.path.exists(path):
            os.makedirs(path)
            logger.info(f"Создана директория: {path}")
    except Exception as e:
        logger.error(f"Ошибка при создании директории {path}: {str(e)}")
        raise

def format_datetime(dt):
    """Форматирует datetime в строку."""
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def parse_datetime(dt_str):
    """Парсит строку в datetime."""
    return datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")

def ensure_file_exists(file_path):
    """Проверяет существование файла."""
    if not os.path.exists(file_path):
        logger.error(f"Файл не найден: {file_path}")
        raise FileNotFoundError(f"Файл не найден: {file_path}")
    return True 