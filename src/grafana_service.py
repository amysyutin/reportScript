import os
import requests
from datetime import datetime
import pytz
import logging
import urllib.parse
import urllib3

# Отключаем предупреждения о небезопасном SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def build_grafana_url(metric_config, base_url, from_time, to_time, timezone):
    """
    Формирует URL для рендеринга панели Grafana.
    
    Args:
        metric_config (dict): Конфигурация метрики из metrics_urls.yml
        base_url (str): Базовый URL Grafana
        from_time (datetime): Начальное время
        to_time (datetime): Конечное время
        timezone (str): Часовой пояс
        
    Returns:
        str: Полный URL для рендеринга панели
    """
    # Формируем базовый URL для render
    render_url = f"{base_url}/render/d-solo/{metric_config['dashboard_uid']}"
    
    # Базовые параметры
    params = {
        'orgId': str(metric_config['orgId']),
        'panelId': str(metric_config['panelId']),
        'width': str(metric_config['width']),
        'height': str(metric_config['height']),
        'timeout': '60',
        'tz': timezone,
        'from': int(from_time.timestamp() * 1000),
        'to': int(to_time.timestamp() * 1000)
    }
    
    # Добавляем переменные из конфига
    if 'vars' in metric_config:
        params.update(metric_config['vars'])
    
    # Формируем финальный URL
    query_string = urllib.parse.urlencode(params)
    return f"{render_url}?{query_string}"

def download_grafana_metrics(cfg, metrics, main_folder_path):
    """
    Скачивает метрики из Grafana.
    
    Args:
        cfg (dict): Конфигурационный словарь
        metrics (list): Список метрик из metrics_urls.yml
        main_folder_path (str): Путь к основной папке для сохранения метрик
        
    Raises:
        Exception: Если возникла ошибка при скачивании метрик
    """
    try:
        # Создаем папку для метрик
        metrics_folder = os.path.join(main_folder_path, "metrics")
        os.makedirs(metrics_folder, exist_ok=True)
        logging.info(f"Создана папка для метрик: {metrics_folder}")
        
        # Настраиваем заголовки для запросов к Grafana
        headers = {
            'Authorization': cfg['grafana']['api_key']
        }
        
        # Получаем временной диапазон из конфигурации
        tz = pytz.timezone(cfg['mainConfig']['timezone'])
        from_time = datetime.strptime(cfg['mainConfig']['from'], "%Y-%m-%d %H:%M:%S").astimezone(tz)
        to_time = datetime.strptime(cfg['mainConfig']['to'], "%Y-%m-%d %H:%M:%S").astimezone(tz)
        
        # Скачиваем каждую метрику
        for metric in metrics:
            try:
                metric_name = metric['name']
                logging.info(f"Скачивание метрики {metric_name}...")
                
                # Формируем URL для рендеринга
                render_url = build_grafana_url(
                    metric,
                    cfg['grafana']['base_url'],
                    from_time,
                    to_time,
                    cfg['mainConfig']['timezone']
                )
                
                # Выполняем запрос к Grafana с отключенной проверкой SSL
                response = requests.get(render_url, headers=headers, verify=False)
                response.raise_for_status()
                
                # Сохраняем результат
                output_file = os.path.join(metrics_folder, f"{metric_name}.png")
                with open(output_file, 'wb') as f:
                    f.write(response.content)
                
                logging.info(f"Метрика {metric_name} успешно скачана в {output_file}")
                
            except Exception as e:
                logging.error(f"Ошибка при скачивании метрики {metric_name}: {str(e)}")
                continue
                
    except Exception as e:
        logging.error(f"Ошибка при скачивании метрик Grafana: {str(e)}")
        raise 