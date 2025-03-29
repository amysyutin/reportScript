import os
import argparse
import requests
import urllib3
from datetime import datetime
from config_manager import ConfigManager

# Отключаем предупреждения о небезопасном SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class GrafanaMetricsManager:
    def __init__(self, config_manager: ConfigManager):
        self.config = config_manager
        self.headers = {
            'Authorization': self.config.grafana_api_key
        }
        self.report_dir = None
        # Создаем сессию с отключенной проверкой SSL
        self.session = requests.Session()
        self.session.verify = False
        self.session.headers.update(self.headers)
        
        # Загружаем URL метрик из файла
        self.metric_urls = self._load_metric_urls()
    
    def _load_metric_urls(self):
        """Загружает URL метрик из файла и добавляет временной диапазон."""
        urls = {}
        try:
            with open('metric_urls.txt', 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        name, url = line.split('=', 1)
                        url = url.strip()
                        # Добавляем параметры для рендеринга
                        if '?' in url:
                            url += f"&width=1000&height=500&timeout=60&tz=Europe/Moscow&render=1"
                        else:
                            url += f"?width=1000&height=500&timeout=60&tz=Europe/Moscow&render=1"
                        # Добавляем временной диапазон
                        url += f"&from={self.config.time_range['from']}&to={self.config.time_range['to']}"
                        urls[name.strip()] = url
        except Exception as e:
            print(f"Ошибка при загрузке URL метрик: {str(e)}")
        return urls
    
    def set_report_directory(self, report_dir: str):
        """Устанавливает директорию для сохранения метрик."""
        self.report_dir = report_dir
        self.metrics_dir = os.path.join(self.report_dir, 'metrics')
        os.makedirs(self.metrics_dir, exist_ok=True)
    
    def download_metric(self, metric_name: str, output_filename: str) -> bool:
        """Скачивает одну метрику из Grafana."""
        try:
            if metric_name not in self.metric_urls:
                print(f"Метрика {metric_name} не найдена в конфигурации")
                return False
                
            panel_url = self.metric_urls[metric_name]
            print(f"Загружаю метрику {metric_name}...")
            print(f"URL: {panel_url}")
            
            response = self.session.get(panel_url, timeout=120)
            
            if response.status_code == 200:
                output_path = os.path.join(self.metrics_dir, output_filename)
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                print(f"Метрика {metric_name} успешно сохранена в {output_filename}")
                return True
            else:
                print(f"Ошибка при загрузке метрики {metric_name}: {response.status_code}")
                print(f"Ответ сервера: {response.text}")
                return False
                
        except Exception as e:
            print(f"Ошибка при обработке метрики {metric_name}: {str(e)}")
            return False
    
    def download_all_metrics(self):
        """Скачивает все метрики из конфигурации."""
        for metric_name, url in self.metric_urls.items():
            output_filename = f"{metric_name}.png"
            self.download_metric(metric_name, output_filename)

def download_grafana_metrics(report_dir=None):
    """Скачивает метрики из Grafana."""
    config_manager = ConfigManager()
    
    # Если директория отчета не указана, используем путь из config.ini
    if report_dir is None:
        report_dir = config_manager.report_dir
    
    # Скачиваем метрики
    grafana = GrafanaMetricsManager(config_manager)
    grafana.set_report_directory(report_dir)
    grafana.download_all_metrics()

def main():
    parser = argparse.ArgumentParser(description='Скачивание метрик Grafana')
    parser.add_argument('-grafana', action='store_true', required=True, help='Скачать метрики Grafana')
    parser.add_argument('-dir', '--directory', help='Директория для сохранения метрик (по умолчанию текущая)')
    args = parser.parse_args()

    try:
        download_grafana_metrics(args.directory)
        print("Метрики успешно скачаны")
    except Exception as e:
        print(f"Ошибка при скачивании метрик: {str(e)}")

if __name__ == "__main__":
    main() 