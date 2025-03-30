import os
import logging
import requests
from datetime import datetime
import pytz
from utils import create_folder_if_not_exists

def download_grafana_metrics(cfg, metrics, main_folder_path):
    """
    Скачивает метрики из Grafana.
    
    Функция выполняет следующие действия:
    1. Создает папку для метрик
    2. Настраивает заголовки для запросов к Grafana
    3. Получает временной диапазон из конфигурации
    4. Скачивает каждую метрику в указанном временном диапазоне
    
    Args:
        cfg (dict): Конфигурационный словарь с параметрами:
            - grafana.api_key: API ключ для доступа к Grafana
            - mainConfig.timezone: часовой пояс
            - mainConfig.from: начальное время
            - mainConfig.to: конечное время
        metrics (dict): Словарь с метриками и их URL
        main_folder_path (str): Путь к основной папке для сохранения метрик
        
    Raises:
        Exception: Если возникла ошибка при скачивании метрик
    """
    try:
        # Создаем папку для метрик внутри основной папки
        metrics_folder = os.path.join(main_folder_path, "metrics")
        create_folder_if_not_exists(metrics_folder)
        
        # Настраиваем заголовки для запросов к Grafana
        headers = {
            'Authorization': f"Bearer {cfg['grafana']['api_key']}"
        }
        
        # Получаем временной диапазон из конфигурации
        tz = pytz.timezone(cfg['mainConfig']['timezone'])
        from_time = datetime.strptime(cfg['mainConfig']['from'], "%Y-%m-%d %H:%M:%S").astimezone(tz)
        to_time = datetime.strptime(cfg['mainConfig']['to'], "%Y-%m-%d %H:%M:%S").astimezone(tz)
        
        # Скачиваем каждую метрику
        for metric_name, metric_url in metrics.items():
            try:
                # Формируем URL с временным диапазоном
                # Конвертируем время в миллисекунды (формат, требуемый Grafana)
                url = f"{metric_url}&from={int(from_time.timestamp()*1000)}&to={int(to_time.timestamp()*1000)}"
                
                # Выполняем запрос к Grafana
                response = requests.get(url, headers=headers)
                response.raise_for_status()  # Проверяем успешность запроса
                
                # Сохраняем метрику в JSON-файл
                metric_file = os.path.join(metrics_folder, f"{metric_name}.json")
                with open(metric_file, 'w') as f:
                    f.write(response.text)
                    
                logging.info(f"Метрика {metric_name} успешно скачана")
                
            except Exception as e:
                logging.error(f"Ошибка при скачивании метрики {metric_name}: {str(e)}")
                
    except Exception as e:
        logging.error(f"Ошибка при скачивании метрик Grafana: {str(e)}")
        raise 