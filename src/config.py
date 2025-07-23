import yaml
import os
from utils import logger, ensure_file_exists

def load_config(config_path='config.yml'):
    """
    Загружает основной конфиг из YAML файла.
    
    Args:
        config_path (str): Путь к файлу конфигурации
        
    Returns:
        dict: Загруженная конфигурация
        
    Raises:
        Exception: Если не удалось загрузить конфигурацию
    """
    try:
        # Если запускаем из src/, ищем файл на уровень выше
        if not os.path.exists(config_path) and os.path.basename(os.getcwd()) == 'src':
            config_path = os.path.join('..', config_path)
        
        ensure_file_exists(config_path)
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        logger.info(f"Загружен конфиг из {config_path}")
        return config
    except Exception as e:
        logger.error(f"Ошибка при загрузке конфига: {str(e)}")
        raise

def load_metrics_config(metrics_path='metrics_urls.yml'):
    """
    Загружает конфигурацию метрик из YAML файла.
    
    Args:
        metrics_path (str): Путь к файлу конфигурации метрик
        
    Returns:
        list: Список метрик
        
    Raises:
        Exception: Если не удалось загрузить конфигурацию метрик
    """
    try:
        # Если запускаем из src/, ищем файл на уровень выше
        if not os.path.exists(metrics_path) and os.path.basename(os.getcwd()) == 'src':
            metrics_path = os.path.join('..', metrics_path)
            
        ensure_file_exists(metrics_path)
        with open(metrics_path, 'r', encoding='utf-8') as f:
            metrics_config = yaml.safe_load(f)
        logger.info(f"Загружен конфиг метрик из {metrics_path}")
        return metrics_config['metrics']
    except Exception as e:
        logger.error(f"Ошибка при загрузке конфига метрик: {str(e)}")
        raise

class Config:
    def __init__(self, config_path='config.yml', services=None):
        self.config_path = config_path
        self.config = self._load_config()
        self.metrics_config = self._load_metrics_config()
        self._services = services or {
            'ssh_service': True,
            'grafana_service': True
        }

    def _load_config(self):
        """Загружает основной конфиг."""
        return load_config(self.config_path)

    def _load_metrics_config(self):
        """Загружает конфиг метрик."""
        return load_metrics_config(self.config['grafana']['metrics_config'])

    @property
    def ssh_config(self):
        """Возвращает конфигурацию SSH."""
        return self.config['ssh_config']

    @property
    def grafana_config(self):
        """Возвращает конфигурацию Grafana."""
        return self.config['grafana']

    @property
    def services(self):
        """Возвращает настройки сервисов."""
        return self._services 