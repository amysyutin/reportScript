import os
from datetime import datetime
from config_manager import ConfigManager
from ssh_client import SSHClient
from grafana_client import GrafanaClient

class GatlingReportManager:
    def __init__(self, config_manager: ConfigManager):
        self.config = config_manager
        self.ssh_client = SSHClient(config_manager)
        self.grafana_client = GrafanaClient(config_manager)
        self.report_dir = None
    
    def _get_formatted_date(self):
        """Возвращает отформатированную дату и время для имени директории."""
        time_from = self.config.time_range['from']
        dt = datetime.strptime(time_from, "%Y-%m-%dT%H:%M:%S.%fZ")
        formatted_date = dt.strftime("%d.%m.%y_%H.%M")
        test_name = self.config.test['name']
        return f"{test_name}_{formatted_date}"
    
    def download_and_organize_report(self):
        """Скачивает отчет с сервера и организует его в нужную структуру."""
        try:
            # Подключаемся к SSH
            self.ssh_client.connect()
            
            # Получаем имя последнего отчета
            last_report = self.ssh_client.get_last_report_name()
            
            # Формируем новое имя директории
            new_dir_name = self._get_formatted_date()
            self.report_dir = os.path.join(self.config.report_dir, new_dir_name)
            
            # Скачиваем отчет
            self.ssh_client.download_report(last_report, self.report_dir)
            
            # Устанавливаем директорию для метрик Grafana
            self.grafana_client.set_report_directory(self.report_dir)
            
            # Скачиваем метрики
            self.grafana_client.download_all_metrics()
            
            print(f"Отчет успешно скачан и организован в {self.report_dir}")
            
        finally:
            # Закрываем SSH соединение
            self.ssh_client.disconnect() 
