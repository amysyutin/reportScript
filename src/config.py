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


from copy import deepcopy
def deep_merge(base: dict, override: dict) -> dict:
    result = deepcopy(base)
    for k, v in (override or {}).items():
        if isinstance(v, dict) and isinstance(result.get(k), dict):
            result[k] = deep_merge(result[k], v)
        else:
            result[k] = v
    return result


def build_env_defaults() -> dict:
    return {
                "mainConfig": {
            "timezone": os.getenv("TIMEZONE"),
        },
        "main_folder": os.getenv("REPORTS_BASE_DIR"),
        "ssh_config": {
            "host": os.getenv("SSH_HOST"),
            "username": os.getenv("SSH_USERNAME"),
            "password": os.getenv("SSH_PASSWORD"),
            "remote_path": os.getenv("SSH_REMOTE_PATH"),
            "local_path": os.getenv("SSH_LOCAL_PATH"),
        },
        "grafana": {
            "local_path": os.getenv("GRAFANA_LOCAL_PATH"),
            "base_url": os.getenv("GRAFANA_BASE_URL"),
            "api_key": os.getenv("GRAFANA_API_KEY"),
            # при желании можно задать дефолт имени файла
            "metrics_config": "metrics_urls.yml",
        },
        "gatling_grafana": {
            "local_path": os.getenv("GATLING_GRAFANA_LOCAL_PATH"),
            "base_url": os.getenv("GATLING_GRAFANA_BASE_URL"),
            "api_key": os.getenv("GATLING_GRAFANA_API_KEY"),
            "gatling_metrics_config": "gatling_metrics_urls.yml",
        },
        "postgresql_grafana": {
            "local_path": os.getenv("POSTGRESQL_GRAFANA_LOCAL_PATH"),
            "base_url": os.getenv("POSTGRESQL_GRAFANA_BASE_URL"),
            "api_key": os.getenv("POSTGRESQL_GRAFANA_API_KEY"),
            "metrics_config": "metrics_urls.yml",
        },

    }



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


def validate_config(cfg: dict) -> None:
    services = cfg.get('services', {})

    if services.get('ssh_service'):
        ssh = cfg.get('ssh_config', {})
        required = ['host', 'username', 'password', 'remote_path', 'local_path']
        missing = [k for k in required if not ssh.get(k)]
        if missing:
            raise ValueError(f"SSH config is incomplete, missing: {', '.join(missing)}")

    if services.get('grafana_service') or services.get('gatling_metrics_service'):
        g = cfg.get('grafana', {})
        missing = [k for k in ['base_url', 'api_key'] if not g.get(k)]
        if missing:
            raise ValueError(f"Grafana config is incomplete, missing: {', '.join(missing)}")

    if services.get('gatling_metrics_service'):
        gg = cfg.get('gatling_grafana', {})
        missing = [k for k in ['base_url', 'api_key'] if not gg.get(k)]
        if missing:
            raise ValueError(f"Gatling Grafana config is incomplete, missing: {', '.join(missing)}")

    if services.get('postgresql_metrics_service'):
        pg = cfg.get('postgresql_grafana', {})
        missing = [k for k in ['base_url', 'api_key'] if not pg.get(k)]
        if missing:
            raise ValueError(f"PostgreSQL Grafana config is incomplete, missing: {', '.join(missing)}")    


def load_config(config_path='config.yml'):
    try:
        # Если запускаем из src/, ищем файл на уровень выше
        if not os.path.exists(config_path) and os.path.basename(os.getcwd()) == 'src':
            config_path = os.path.join('..', config_path)
        
        ensure_file_exists(config_path)
        with open(config_path, 'r', encoding='utf-8') as f:
            raw_config = yaml.safe_load(f) or {}

        # 1) Собираем дефолты из ENV
        env_defaults = build_env_defaults()

        # 2) YAML-параметры перебивают ENV-дефолты
        config = deep_merge(env_defaults, raw_config)

        # 3) На переходный период можно оставить подстановку плейсхолдеров (безопасно)
        config = _resolve_env_placeholders(config)

        # 4) Заполняем таймзону по умолчанию, если её нет ни в YAML, ни в ENV
        config.setdefault('mainConfig', {})
        if not config['mainConfig'].get('timezone'):
            config['mainConfig']['timezone'] = os.getenv('TIMEZONE', 'UTC')

        # 5) Валидация включённых сервисов и обязательных полей
        validate_config(config)

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
