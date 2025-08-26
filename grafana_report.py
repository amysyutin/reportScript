import os
import yaml
import requests
from config_manager import ConfigManager
import logging

class GrafanaReport:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.grafana_config = config_manager.get_grafana_config()
        api_key = str(self.grafana_config.get('api_key', ''))
        if api_key and not api_key.lower().startswith('bearer '):
            api_key = f"Bearer {api_key}"
        self.api_key = api_key
        self.metrics_config_path = config_manager.get_metrics_config_path()
        self.metrics_config = self._load_metrics_config()
        self.timezone = config_manager.get_main_config().get('timezone', 'UTC')
        
    def _load_metrics_config(self):
        """Загрузка конфигурации метрик"""
        try:
            with open(self.metrics_config_path, 'r') as file:
                return yaml.safe_load(file)
        except Exception as e:
            raise Exception(f"Ошибка при загрузке конфигурации метрик: {str(e)}")
    
    def _convert_dashboard_url_to_render(self, dashboard_url):
        """Конвертация URL дашборда в URL для рендеринга"""
        try:
            # Получаем отформатированное время из конфига
            from_time, to_time = self.config_manager.get_formatted_time_range()
            
            # Добавляем параметры времени и timezone к существующему URL
            separator = '&' if '?' in dashboard_url else '?'
            render_url = f"{dashboard_url}{separator}from={from_time}&to={to_time}&timezone={self.timezone}"
            
            return render_url
        except Exception as e:
            raise Exception(f"Ошибка при конвертации URL: {str(e)}")
    
    def download_metrics(self, output_dir):
        """Скачивание метрик из Grafana"""
        try:
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            headers = {'Authorization': self.api_key}
            
            for metric_name, metric_url in self.metrics_config.items():
                try:
                    render_url = self._convert_dashboard_url_to_render(metric_url)
                    logging.info(f"Скачивание метрики {metric_name} из {render_url}")
                    
                    response = requests.get(render_url, headers=headers)
                    response.raise_for_status()
                    
                    output_path = os.path.join(output_dir, f"{metric_name}.png")
                    with open(output_path, 'wb') as f:
                        f.write(response.content)
                    
                    logging.info(f"Метрика {metric_name} успешно сохранена в {output_path}")
                except Exception as e:
                    logging.error(f"Ошибка при скачивании метрики {metric_name}: {str(e)}")
                    continue
            
            logging.info("Загрузка метрик завершена")
        except Exception as e:
            raise Exception(f"Ошибка при скачивании метрик: {str(e)}") 