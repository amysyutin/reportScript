import os
import requests
import urllib3
from datetime import datetime
from config_manager import ConfigManager
from urllib.parse import urlparse, urljoin
import re
import json
from typing import Dict, Optional, Tuple

# Отключаем предупреждения о небезопасном SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class GrafanaClient:
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
        
        # Валидируем URL метрик при инициализации
        self._validate_metric_urls()
    
    def _validate_url(self, url: str) -> bool:
        """Проверяет корректность URL метрики."""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    def _parse_time(self, time_str: str) -> datetime:
        """Парсит время из различных форматов."""
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%dT%H:%M:%SZ"
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(time_str, fmt)
            except ValueError:
                continue
                
        raise ValueError(f"Неверный формат времени: {time_str}")
    
    def _validate_time_range(self, time_range: Dict[str, str]) -> Tuple[bool, str]:
        """Проверяет корректность временного диапазона."""
        try:
            from_time = self._parse_time(time_range['from'])
            to_time = self._parse_time(time_range['to'])
            
            if to_time <= from_time:
                return False, "Время окончания должно быть позже времени начала"
            
            if (to_time - from_time).total_seconds() > 86400:  # 24 часа
                return False, "Временной диапазон не должен превышать 24 часа"
                
            return True, ""
        except ValueError as e:
            return False, f"Неверный формат времени: {str(e)}"
    
    def _validate_metric_urls(self) -> None:
        """Проверяет все URL метрик на корректность."""
        invalid_urls = []
        for name, url in self.metric_urls.items():
            if not self._validate_url(url):
                invalid_urls.append(name)
        
        if invalid_urls:
            raise ValueError(f"Найдены некорректные URL для метрик: {', '.join(invalid_urls)}")
    
    def _load_metric_urls(self) -> Dict[str, str]:
        """Загружает URL метрик из файла и добавляет временной диапазон."""
        urls = {}
        try:
            with open('metric_urls.txt', 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        name, url = line.split('=', 1)
                        # Добавляем временной диапазон к URL
                        url = url.strip()
                        if '?' in url:
                            url += f"&from={self.config.time_range['from']}&to={self.config.time_range['to']}"
                        else:
                            url += f"?from={self.config.time_range['from']}&to={self.config.time_range['to']}"
                        urls[name.strip()] = url
        except Exception as e:
            print(f"Ошибка при загрузке URL метрик: {str(e)}")
        return urls
    
    def update_metric_url(self, metric_name: str, new_url: str) -> bool:
        """Обновляет URL для конкретной метрики."""
        if not self._validate_url(new_url):
            print(f"Некорректный URL для метрики {metric_name}")
            return False
            
        # Добавляем временной диапазон к новому URL
        if '?' in new_url:
            new_url += f"&from={self.config.time_range['from']}&to={self.config.time_range['to']}"
        else:
            new_url += f"?from={self.config.time_range['from']}&to={self.config.time_range['to']}"
            
        self.metric_urls[metric_name] = new_url
        return True
    
    def update_metric_urls_file(self) -> bool:
        """Обновляет файл metric_urls.txt текущими URL метрик."""
        try:
            with open('metric_urls.txt', 'w') as f:
                for name, url in self.metric_urls.items():
                    # Удаляем временной диапазон перед сохранением
                    base_url = url.split('?')[0]
                    f.write(f"{name}={base_url}\n")
            return True
        except Exception as e:
            print(f"Ошибка при обновлении файла URL метрик: {str(e)}")
            return False
    
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
            
            response = self.session.get(panel_url)
            
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
    
    def download_all_metrics(self, metrics: Dict[str, str] = None):
        """Скачивает все метрики из конфигурации."""
        if metrics is None:
            # Если словарь не передан, используем конфигурацию
            for metric_name, metric_config in self.config.metrics.items():
                _, output_filename = metric_config.split(',')
                self.download_metric(metric_name, output_filename)
        else:
            # Если словарь передан, используем его
            for metric_name, output_filename in metrics.items():
                self.download_metric(metric_name, output_filename) 
