from config import Config
from ssh_service import SSHService
from grafana_service import GrafanaService
from utils import logger
import argparse

def main():
    try:
        # Парсинг аргументов командной строки
        parser = argparse.ArgumentParser(description='Скрипт для скачивания отчетов Gatling и метрик Grafana')
        parser.add_argument('-gatling', action='store_true', help='Скачать только отчет Gatling')
        parser.add_argument('-grafana', action='store_true', help='Скачать только метрики Grafana')
        parser.add_argument('-all', action='store_true', help='Скачать и отчет, и метрики (по умолчанию)')
        args = parser.parse_args()

        # Определение сервисов для запуска
        services = {
            'ssh_service': args.gatling or args.all or (not args.gatling and not args.grafana),
            'grafana_service': args.grafana or args.all or (not args.gatling and not args.grafana)
        }

        # Инициализация конфигурации
        config = Config(services=services)
        
        # Скачивание отчета Gatling
        if config.services['ssh_service']:
            logger.info("Запуск сервиса SSH")
            ssh_service = SSHService(config)
            report_path = ssh_service.download_last_report()
            if report_path:
                logger.info(f"Отчет Gatling успешно скачан: {report_path}")
            else:
                logger.warning("Отчет Gatling не был скачан, так как не найден на сервере")
        
        # Скачивание метрик Grafana
        if config.services['grafana_service']:
            logger.info("Запуск сервиса Grafana")
            grafana_service = GrafanaService(config)
            grafana_service.download_metrics()
            logger.info("Метрики Grafana успешно скачаны")
            
    except Exception as e:
        logger.error(f"Критическая ошибка: {str(e)}")
        raise

if __name__ == "__main__":
    main() 