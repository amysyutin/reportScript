import argparse
import os
from config import load_config, load_metrics_config
from ssh_service import ssh_download_last_report
from grafana_service import download_grafana_metrics
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
        cfg = load_config()
        
        # Создание основной папки для отчетов
        main_folder_path = create_main_folder(cfg)
        logger.info(f"Создана основная папка: {main_folder_path}")

        # Скачивание отчета Gatling, если указан соответствующий флаг
        if args.gatling and cfg['services'].get('ssh_service', True):
            logger.info("Начинаем скачивание отчета Gatling...")
            report_path = ssh_download_last_report(cfg, main_folder_path)
            if report_path:
                logger.info(f"Отчет Gatling успешно скачан: {report_path}")
            else:
                logger.error("Не удалось скачать отчет Gatling")

        # Скачивание метрик Grafana, если указан соответствующий флаг
        if args.grafana and cfg['services'].get('grafana_service', True):
            logger.info("Начинаем скачивание метрик Grafana...")
            try:
                metrics_config_path = cfg['grafana']['metrics_config']
                if not os.path.exists(metrics_config_path):
                    logger.error(f"Файл конфигурации метрик не найден: {metrics_config_path}")
                    return
                    
                metrics = load_metrics_config()
                download_grafana_metrics(cfg, metrics, main_folder_path)
                logger.info("Метрики Grafana успешно скачаны")
            except Exception as e:
                logger.error(f"Ошибка при скачивании метрик Grafana: {str(e)}")
                
    except Exception as e:
        logger.error(f"Критическая ошибка: {str(e)}")
        raise

if __name__ == "__main__":
    main() 