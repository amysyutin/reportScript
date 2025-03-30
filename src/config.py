import yaml
import os
from utils import logger, ensure_file_exists

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
        try:
            ensure_file_exists(self.config_path)
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Загружен конфиг из {self.config_path}")
            return config
        except Exception as e:
            logger.error(f"Ошибка при загрузке конфига: {str(e)}")
            raise

    def _load_metrics_config(self):
        """Загружает конфиг метрик."""
        try:
            metrics_path = self.config['grafana']['metrics_config']
            ensure_file_exists(metrics_path)
            with open(metrics_path, 'r') as f:
                metrics_config = yaml.safe_load(f)
            logger.info(f"Загружен конфиг метрик из {metrics_path}")
            return metrics_config['metrics']
        except Exception as e:
            logger.error(f"Ошибка при загрузке конфига метрик: {str(e)}")
            raise

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