import os
import argparse
from datetime import datetime
from config_manager import ConfigManager

def download_gatling_report():
    """Скачивает отчёт Gatling с сервера и очищает его."""
    config_manager = ConfigManager()
    config = config_manager.config
    
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
    new_folder_name = f"Gatling_Report_{test_name}_{start_dt.strftime('%Y-%m-%d_%H-%M')}"
    
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

def main():
    parser = argparse.ArgumentParser(description='Скачивание отчета Gatling')
    parser.add_argument('-gatling', action='store_true', help='Скачать отчет Gatling')
    args = parser.parse_args()

    if args.gatling:
        try:
            report_folder = download_gatling_report()
            print(f"Отчет успешно скачан и переименован в {report_folder}")
        except Exception as e:
            print(f"Ошибка при скачивании отчета: {str(e)}")
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 