from config_manager import ConfigManager
from grafana_client import GrafanaClient
from gatling_report_manager import GatlingReportManager

def main():
    # Инициализируем менеджер конфигурации
    config_manager = ConfigManager()
    
    # Создаем менеджер отчетов Gatling
    report_manager = GatlingReportManager(config_manager)
    
    # Скачиваем и организуем отчет Gatling
    report_manager.download_and_organize_report()
    
    # Создаем клиент Grafana
    grafana_client = GrafanaClient(config_manager)
    
    # Скачиваем метрики в директорию metrics
    grafana_client.download_all_metrics()

if __name__ == "__main__":
    main() 
