import requests
import os
from datetime import datetime, timedelta
from utils import logger, create_folder_if_not_exists, format_datetime

class GrafanaService:
    def __init__(self, config):
        self.config = config
        self.headers = {
            'Authorization': f"Bearer {self.config.grafana_config['api_key']}"
        }

    def _format_time_for_grafana(self, time_str):
        """Конвертирует время из московского в UTC."""
        try:
            dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
            # Конвертируем из московского времени (UTC+3) в UTC
            dt = dt - timedelta(hours=3)
            return dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        except Exception as e:
            logger.error(f"Ошибка при форматировании времени: {str(e)}")
            raise

    def download_metric(self, metric):
        """Скачивает одну метрику."""
        try:
            response = requests.get(
                metric['url'],
                headers=self.headers,
                verify=False  # Для самоподписанных сертификатов
            )
            response.raise_for_status()
            
            filename = os.path.join(
                self.config.grafana_config['local_path'],
                f"{metric['name']}.png"
            )
            
            with open(filename, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"Метрика {metric['name']} скачана в {filename}")
            return filename
        except Exception as e:
            logger.error(f"Ошибка при скачивании метрики {metric['name']}: {str(e)}")
            raise

    def download_metrics(self):
        """Скачивает все метрики."""
        try:
            create_folder_if_not_exists(self.config.grafana_config['local_path'])
            
            for metric in self.config.metrics_config:
                self.download_metric(metric)
                
            logger.info("Все метрики успешно скачаны")
        except Exception as e:
            logger.error(f"Ошибка при скачивании метрик: {str(e)}")
            raise 