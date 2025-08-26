import argparse
import os
from config import load_config
from config_loader import load_metrics_config
from ssh_service import ssh_download_last_report
from grafana_service import download_grafana_metrics, download_postgresql_metrics, download_gatling_metrics
from utils import create_main_folder, logger

def main():
    """
    Основная функция скрипта.
    
    Скрипт выполняет следующие действия:
    1. Парсит аргументы командной строки
    2. Загружает конфигурацию
    3. Создает основную папку для отчетов
    4. Скачивает отчет Gatling (если указан флаг -gatling)
    5. Скачивает метрики Grafana (если указан флаг -grafana)
    """
    try:
        # Настройка парсера аргументов командной строки
        parser = argparse.ArgumentParser(description='Скачивание отчетов и метрик')
        parser.add_argument('-gatling', action='store_true', help='Скачать отчет Gatling')
        parser.add_argument('-grafana', action='store_true', help='Скачать метрики Grafana')
        args = parser.parse_args()

        # Загрузка конфигурации из файла config.yml
        cfg = load_config('config.yml')
        
        # Создание основной папки для отчетов
        main_folder_path = create_main_folder(cfg)
        logger.info(f"Создана основная папка: {main_folder_path}")

        # Извлекаем сервисы из конфигурации
        service_flags = cfg.get('services', {})
        
        # Отделяем системные сервисы от сервисов приложений
        grafana_enabled = service_flags.get('grafana_service', True)
        ssh_enabled = service_flags.get('ssh_service', True)
        
        # Собираем только включенные сервисы приложений (исключая системные)
        system_services = {'grafana_service', 'ssh_service', 'gatling_metrics_service', 'postgresql_metrics_service'}
        metric_services = [
            name for name, enabled in service_flags.items() 
            if enabled and name not in system_services
        ]
        
        logger.info(f"Включенные сервисы приложений: {metric_services}")

        # Скачивание отчета Gatling, если указан соответствующий флаг
        if args.gatling and ssh_enabled:
            logger.info("Начинаем скачивание отчета Gatling...")
            report_path = ssh_download_last_report(cfg, main_folder_path)
            if report_path:
                logger.info(f"Отчет Gatling успешно скачан: {report_path}")
            else:
                logger.error("Не удалось скачать отчет Gatling")

        # Скачивание GATLING метрик независимо от grafana_service
        # Если передан флаг -grafana и включён gatling_metrics_service, но grafana_service отключён,
        # запускаем скачивание Gatling метрик отдельно, чтобы не зависеть от основного сервиса метрик.
        if args.grafana and cfg.get('services', {}).get('gatling_metrics_service', False) and not grafana_enabled:
            logger.info("Начинаем независимое скачивание Gatling метрик (grafana_service: false)...")
            try:
                download_gatling_metrics(cfg, main_folder_path)
                logger.info("Gatling метрики успешно скачаны")
            except Exception as e:
                logger.error(f"Ошибка при скачивании Gatling метрик: {str(e)}")

        # Скачивание метрик Grafana, если указан соответствующий флаг
        if args.grafana and grafana_enabled:
            logger.info("Начинаем скачивание метрик Grafana...")
            try:
                metrics_config_path = cfg['grafana']['metrics_config']
                # Используем путь относительно текущей директории
                if not os.path.exists(metrics_config_path):
                    logger.error(f"Файл конфигурации метрик не найден: {metrics_config_path}")
                    return

                metrics = load_metrics_config(metrics_config_path)
                download_grafana_metrics(cfg, metrics, main_folder_path, metric_services)
                logger.info("Метрики Grafana успешно скачаны")
            except Exception as e:
                logger.error(f"Ошибка при скачивании метрик Grafana: {str(e)}")
                
    except Exception as e:
        logger.error(f"Критическая ошибка: {str(e)}")
        raise

if __name__ == "__main__":
    main() 
