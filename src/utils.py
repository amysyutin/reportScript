import os
import logging
from datetime import datetime
import pytz

# Настройка логирования с выводом в файл и консоль
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),  # Логирование в файл
        logging.StreamHandler()          # Логирование в консоль
    ]
)
logger = logging.getLogger(__name__)

def create_folder_if_not_exists(path):
    """
    Создает директорию, если она не существует.
    
    Args:
        path (str): Путь к директории, которую нужно создать
        
    Raises:
        Exception: Если возникла ошибка при создании директории
    """
    try:
        if not os.path.exists(path):
            os.makedirs(path)
            logger.info(f"Создана директория: {path}")
    except Exception as e:
        logger.error(f"Ошибка при создании директории {path}: {str(e)}")
        raise

def format_datetime(dt):
    """
    Форматирует объект datetime в строку в формате YYYY-MM-DD HH:MM:SS.
    
    Args:
        dt (datetime): Объект datetime для форматирования
        
    Returns:
        str: Отформатированная строка даты и времени
    """
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def parse_datetime(dt_str):
    """
    Парсит строку даты и времени в объект datetime.
    
    Args:
        dt_str (str): Строка даты и времени в формате YYYY-MM-DD HH:MM:SS
        
    Returns:
        datetime: Объект datetime
    """
    return datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")

def ensure_file_exists(file_path):
    """
    Проверяет существование файла.
    
    Args:
        file_path (str): Путь к файлу для проверки
        
    Returns:
        bool: True, если файл существует
        
    Raises:
        FileNotFoundError: Если файл не найден
    """
    if not os.path.exists(file_path):
        logger.error(f"Файл не найден: {file_path}")
        raise FileNotFoundError(f"Файл не найден: {file_path}")
    return True

def create_main_folder_name(cfg):
    """
    Создает имя основной папки на основе конфигурации.
    
    Args:
        cfg (dict): Конфигурационный словарь с параметрами:
            - mainConfig.timezone: часовой пояс
            - mainConfig.from: начальное время
            - mainConfig.type_of_script: тип скрипта
            - mainConfig.scenario: название сценария
            
    Returns:
        str: Имя папки в формате "DD.MM.YY_scenario_HH.MM_type"
    """
    # Логируем входные данные
    logging.info(f"Создание имени папки из конфига: {cfg['mainConfig']}")
    
    # Получаем часовой пояс из конфигурации
    tz = pytz.timezone(cfg['mainConfig']['timezone'])
    
    # Конвертируем строку времени в объект datetime с учетом часового пояса
    from_time = datetime.strptime(cfg['mainConfig']['from'], "%Y-%m-%d %H:%M:%S").astimezone(tz)
    logging.info(f"Преобразованное время: {from_time}")

    # Форматируем дату и время для имени папки
    date_str = from_time.strftime("%d.%m.%y")
    time_str = from_time.strftime("%H.%M")
    
    # Получаем тип скрипта и сценарий
    script_type = cfg['mainConfig']['type_of_script']
    scenario = cfg['mainConfig']['scenario']
    
    # Формируем имя папки
    folder_name = f"{date_str}_{scenario}_{time_str}_{script_type}"
    logging.info(f"Сформированное имя папки: {folder_name}")
    
    return folder_name

def create_main_folder(cfg):
    """
    Создает основную папку для отчетов.
    
    Args:
        cfg (dict): Конфигурационный словарь с параметрами:
            - main_folder: базовый путь для отчетов
            - mainConfig: параметры для генерации имени папки
            
    Returns:
        str: Полный путь к созданной папке
    """
    # Генерируем имя папки
    folder_name = create_main_folder_name(cfg)
    
    # Формируем полный путь
    full_path = os.path.join(cfg['main_folder'], folder_name)
    
    # Создаем папку, если она не существует
    if not os.path.exists(full_path):
        os.makedirs(full_path)
        
    return full_path 