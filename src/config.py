import yaml
import os
import re
from pathlib import Path
from utils import logger, ensure_file_exists

# Опционально подгружаем .env, если установлен python-dotenv
try:
    from dotenv import load_dotenv
    # 1) Пытаемся загрузить .env из текущей директории
    load_dotenv()
    # 2) Явно пробуем .env из корня проекта (относительно src/)
    project_root_env = Path(__file__).resolve().parent.parent / '.env'
    if project_root_env.exists():
        load_dotenv(dotenv_path=project_root_env, override=False)
except Exception:
    # Библиотека может быть не установлена; это не критично
    pass

_ENV_PATTERN = re.compile(r"^\$\{([A-Z0-9_]+)\}$")


def _resolve_env_placeholders(obj):
    """Рекурсивно заменяет строки вида ${ENV_VAR} на значения из окружения.

    Если переменная окружения не задана, оставляет исходное значение.
    """
    if isinstance(obj, dict):
        return {k: _resolve_env_placeholders(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_resolve_env_placeholders(v) for v in obj]
    if isinstance(obj, str):
        m = _ENV_PATTERN.match(obj)
        if m:
            env_name = m.group(1)
            return os.getenv(env_name, obj)
        return obj
    return obj


def load_config(config_path='config.yml'):
    """
    Загружает основной конфиг из YAML файла и подставляет значения из ENV
    для плейсхолдеров вида ${VARNAME}.

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
            raw_config = yaml.safe_load(f)
        config = _resolve_env_placeholders(raw_config)
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
