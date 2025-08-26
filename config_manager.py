from configparser import ConfigParser
import os
from datetime import datetime

class ConfigManager:
    def __init__(self, config_file='config.ini', test_config_file='test_config.ini'):
        self.config = ConfigParser()
        self.test_config = ConfigParser()
        
        # Читаем оба файла конфигурации
        self.config.read(config_file)
        self.test_config.read(test_config_file)
        
        # Обновляем временной диапазон
        self._update_time_range()
    
    def _update_time_range(self):
        """Обновляет временной диапазон в config.ini на основе значений из test_config.ini."""
        if 'Test' in self.test_config:
            start_time = self.test_config['Test']['start_time']
            end_time = self.test_config['Test']['end_time']
            
            # Преобразуем время в формат ISO 8601
            start_dt = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
            end_dt = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
            
            self.config['Grafana']['time_from'] = start_dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")
            self.config['Grafana']['time_to'] = end_dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")
            
            # Сохраняем обновленный config.ini
            with open('config.ini', 'w') as f:
                self.config.write(f)
    
    @property
    def report_dir(self):
        return self.config['Gatling']['report_dir']
    
    @property
    def grafana_api_key(self):
        return self.config['Grafana']['grafana_api_key']
    
    @property
    def time_range(self):
        return {
            'from': self.config['Grafana']['time_from'],
            'to': self.config['Grafana']['time_to']
        }
    
    @property
    def test(self):
        return self.test_config['Test']

    @property
    def base_url(self):
        return self.config['Grafana']['base_url']
    
    @property
    def variables(self):
        return self.config['Grafana.Variables']
    
    @property
    def dashboards(self):
        return self.config['Grafana.Dashboards']
    
    @property
    def metrics(self):
        return self.config['Grafana.Metrics']
    
    @property
    def ssh(self):
        return self.config['SSH']

    def _update_grafana_time_range(self):
        """Обновляет временной диапазон в Grafana на основе значений из Test секции."""
        if 'Test' in self.test_config:
            start_time = self.test_config['Test']['start_time']
            end_time = self.test_config['Test']['end_time']
            
            # Преобразуем время в формат ISO 8601
            start_dt = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
            end_dt = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
            
            self.config['Grafana.TimeRange']['from'] = start_dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")
            self.config['Grafana.TimeRange']['to'] = end_dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    