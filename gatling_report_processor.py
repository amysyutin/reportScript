import os
import requests
import zipfile
import shutil
from configparser import ConfigParser
import urllib3
from config_manager import ConfigManager
from datetime import datetime

# Отключаем предупреждения о небезопасном SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Чтение конфигурации
config_manager = ConfigManager('config.ini', 'test_config.ini')
config = config_manager.config

# Переменные из конфига
REPORT_URL = config['Gatling']['report_url']
REPORT_DIR = config['Gatling']['report_dir']
GRAFANA_API_KEY = config['Grafana']['grafana_api_key']
SIMULATION_CONFIG_FILE = config['Simulation']['gatling_config_file']
SIMULATION_CONFIGS = dict(item.split('=') for item in config['Simulation']['simulation_configs'].split(', '))

def download_gatling_report():
    """Скачивает отчёт Gatling с сервера и очищает его."""
    remote_user = config['Gatling']['remote_user']
    remote_host = config['Gatling']['remote_host']
    remote_base_dir = config['Gatling']['remote_base_dir']
    local_dir = config['Gatling']['local_dir']

    # Получаем имя последнего отчета из lastRun.txt
    print("Получаю имя последнего отчета из lastRun.txt...")
    last_report_cmd = f"ssh {remote_user}@{remote_host} 'cat {remote_base_dir}/lastRun.txt'"
    last_report = os.popen(last_report_cmd).read().strip()

    if not last_report:
        raise Exception("Ошибка: не удалось получить имя последнего отчета из lastRun.txt.")

    # Полный путь к последнему отчету на сервере
    remote_report_dir = f"{remote_base_dir}/{last_report}"

    # Создаем локальную директорию, если ее нет
    os.makedirs(local_dir, exist_ok=True)

    # Скачиваем последний отчет
    print(f"Скачиваю отчет {last_report} в {local_dir}...")
    scp_cmd = f"scp -r {remote_user}@{remote_host}:{remote_report_dir} {local_dir}"
    scp_result = os.system(scp_cmd)

    # Проверяем, успешно ли скачалось
    if scp_result != 0:
        raise Exception(f"Ошибка при скачивании отчета: {scp_result}")

    # Получаем параметры для переименования
    test_name = config_manager.test_config['Test']['name']
    start_time = config_manager.test_config['Test']['start_time']
    
    # Преобразуем время в формат для имени папки
    start_dt = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
    new_folder_name = f"{start_dt.strftime('%Y%m%d_%H%M%S')}_{test_name}"
    
    # Переименовываем папку
    old_path = os.path.join(local_dir, last_report)
    new_path = os.path.join(local_dir, new_folder_name)
    os.rename(old_path, new_path)
    print(f"Отчет переименован в {new_folder_name}")

    # Очищаем на сервере
    print(f"Скачивание завершено. Удаляю {remote_report_dir} на сервере...")
    cleanup_cmd = f"ssh {remote_user}@{remote_host} 'rm -rf {remote_report_dir}'"
    os.system(cleanup_cmd)
    print("Директория с отчетом на сервере очищена.")
    
    return new_folder_name

def save_simulation_config():
    """Сохраняет конфигурацию симуляции в файл."""
    print(f"Simulation config saved to {SIMULATION_CONFIG_FILE}")
    with open(SIMULATION_CONFIG_FILE, 'w') as f:
        for key, value in SIMULATION_CONFIGS.items():
            f.write(f"{key}={value}\n")

def main():
    """Основная функция."""
    try:
        # Скачиваем отчет
        report_folder = download_gatling_report()
        
        # Создаем директорию для метрик
        metrics_dir = os.path.join(REPORT_DIR, 'metrics')
        os.makedirs(metrics_dir, exist_ok=True)
        
        # Скачиваем метрики из Grafana
        from grafana_client import GrafanaClient
        grafana = GrafanaClient(config_manager)
        grafana.set_report_directory(REPORT_DIR)
        grafana.download_all_metrics()
        
        # Сохраняем конфигурацию симуляции
        save_simulation_config()
        
    except Exception as e:
        print(f"Error: {str(e)}")
        raise

if __name__ == "__main__":
    main()