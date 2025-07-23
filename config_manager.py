import yaml
import os
from datetime import datetime
import pytz

class ConfigManager:
    def __init__(self, config_path='config.yml'):
        self.config_path = config_path
        self.config = self._load_config()
        
    def _load_config(self):
        """Загрузка конфигурации из YAML файла"""
        try:
            with open(self.config_path, 'r') as file:
                return yaml.safe_load(file)
        except Exception as e:
            raise Exception(f"Ошибка при загрузке конфигурации: {str(e)}")
    
    def get_main_config(self):
        """Получение основной конфигурации"""
        return self.config.get('mainConfig', {})
    
    def get_services_config(self):
        """Получение конфигурации сервисов"""
        return self.config.get('services', {})
    
    def get_ssh_config(self):
        """Получение конфигурации SSH"""
        return self.config.get('ssh_config', {})
    
    def get_grafana_config(self):
        """Получение конфигурации Grafana"""
        return self.config.get('grafana', {})
    
    def get_metrics_config_path(self):
        """Получение пути к конфигурации метрик"""
        return self.config.get('grafana', {}).get('metrics_config', 'metrics_urls.yml')
    
    def get_main_folder(self):
        """Получение пути к основной папке"""
        return self.config.get('main_folder', './reports')
    
    def format_time_for_grafana(self, time_str):
        """Форматирование времени в формат ISO 8601 с UTC"""
        try:
            # Получаем timezone из конфига
            timezone = self.get_main_config().get('timezone', 'UTC')
            tz = pytz.timezone(timezone)
            
            # Парсим время с учетом timezone
            dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
            dt = tz.localize(dt)
            
            # Конвертируем в UTC
            dt_utc = dt.astimezone(pytz.UTC)
            
            # Форматируем в ISO 8601
            return dt_utc.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        except Exception as e:
            raise Exception(f"Ошибка при форматировании времени: {str(e)}")
    
    def get_formatted_time_range(self):
        """Получение отформатированного временного диапазона для Grafana"""
        main_config = self.get_main_config()
        from_time = self.format_time_for_grafana(main_config.get('from'))
        to_time = self.format_time_for_grafana(main_config.get('to'))
        return from_time, to_time 