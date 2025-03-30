import os
import requests
from datetime import datetime
import pytz
from utils import logger
import urllib.parse

def convert_dashboard_url_to_render(url):
    """
    Преобразует URL дашборда в URL для render.
    
    Args:
        url (str): URL дашборда
        
    Returns:
        str: URL для render
    """
    # Извлекаем ID дашборда и панели
    dashboard_id = url.split('/d/')[1].split('/')[0]
    panel_id = url.split('viewPanel=')[1]
    
    # Формируем базовый URL для render
    base_url = url.split('/d/')[0]
    render_url = f"{base_url}/render/d-solo/{dashboard_id}"
    
    # Добавляем параметры
    params = {
        'orgId': '1',
        'panelId': panel_id,
        'width': '1000',
        'height': '500',
        'timeout': '60',
        'tz': 'Europe/Moscow'
    }
    
    # Добавляем переменные из оригинального URL
    original_params = dict(urllib.parse.parse_qsl(urllib.parse.urlparse(url).query))
    for key, value in original_params.items():
        if key.startswith('var-'):
            params[key] = value
    
    # Формируем финальный URL
    query_string = urllib.parse.urlencode(params)
    return f"{render_url}?{query_string}"

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
        os.makedirs(metrics_folder, exist_ok=True)
        logger.info(f"Создана папка для метрик: {metrics_folder}")
        
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
                metric_url = metric['url']
                
                # Преобразуем URL дашборда в URL для render
                render_url = convert_dashboard_url_to_render(metric_url)
                
                # Добавляем временной диапазон
                render_url = f"{render_url}&from={int(from_time.timestamp()*1000)}&to={int(to_time.timestamp()*1000)}"
                
                # Формируем команду curl
                output_file = os.path.join(metrics_folder, f"{metric_name}.png")
                curl_command = f'curl -L -k -v --connect-timeout 30 --max-time 120 -H "Authorization: {cfg["grafana"]["api_key"]}" "{render_url}" -o "{output_file}"'
                
                logger.info(f"Выполняем команду: {curl_command}")
                
                # Выполняем команду через shell
                result = os.system(curl_command)
                
                if result == 0:
                    logger.info(f"Метрика {metric_name} успешно скачана")
                else:
                    logger.error(f"Ошибка при скачивании метрики {metric_name}")
                
            except Exception as e:
                logger.error(f"Ошибка при скачивании метрики {metric_name}: {str(e)}")
                
    except Exception as e:
        logger.error(f"Ошибка при скачивании метрик Grafana: {str(e)}")
        raise 