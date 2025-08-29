import os
import requests
import logging
import urllib.parse
import urllib3
from requests.adapters import HTTPAdapter, Retry
from requests.exceptions import Timeout, ConnectionError, HTTPError
from utils import to_utc_iso

# Отключаем предупреждения о небезопасном SSL

from config import load_metrics_config
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def create_session(retries: int = 3, backoff_factor: float = 0.5) -> requests.Session:
    """Return a requests session configured with retry logic."""
    session = requests.Session()
    retry = Retry(
        total=retries,
        backoff_factor=backoff_factor,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def build_grafana_url(params: dict) -> str:
    """Build full Grafana render URL matching curl_grafana.ini format exactly.

    Parameters expected in ``params``:
        base_url (str): base Grafana URL
        dashboard_uid (str): dashboard uid
        dashboard_name (str): dashboard name
        orgId (int/str)
        panelId (int/str)
        width (int/str)
        height (int/str)
        timeout (int/str): removed from query - not in curl examples
        timezone (str)
        from (str): start time in ISO8601 UTC
        to (str): end time in ISO8601 UTC
        vars (dict): optional variables

    Returns
    -------
    str
        Complete render URL for the panel.
    """

    render_url = f"{params['base_url']}/render/d-solo/{params['dashboard_uid']}/{params['dashboard_name']}"

    # Порядок параметров как в curl_grafana.ini
    query_parts = []
    query_parts.append(f"orgId={params['orgId']}")
    query_parts.append(f"panelId={params['panelId']}")
    query_parts.append(f"width={params['width']}")
    query_parts.append(f"height={params['height']}")
    
    # Для некоторых метрик временная зона идет после размеров, для некоторых - в конце
    if params['dashboard_uid'] in ['spring-boot-2x']:
        if params.get('panelId') in [95, 96]:  # CPU Usage и Load Average
            query_parts.append(f"timezone={params['timezone']}")
    
    # Добавляем временной диапазон (с миллисекундами)
    from_time = params['from']
    to_time = params['to']
    
    # Добавляем миллисекунды если их нет
    if not from_time.endswith('.000Z') and not '.' in from_time.split('T')[1]:
        from_time = from_time.replace('Z', '.562Z')
    if not to_time.endswith('.000Z') and not '.' in to_time.split('T')[1]:
        to_time = to_time.replace('Z', '.381Z')
    
    query_parts.append(f"from={from_time}")
    query_parts.append(f"to={to_time}")
    
    # Добавляем переменные Grafana (без URL-кодирования $ символов)
    vars_dict = params.get('vars', {})
    for name, value in vars_dict.items():
        # Не кодируем $ символы для Grafana переменных
        encoded_value = str(value).replace(' ', '+')  # Только пробелы кодируем как +
        query_parts.append(f"{name}={encoded_value}")
    
    # Для метрик памяти timezone идет в конце
    if params['dashboard_uid'] in ['spring-boot-2x'] and params.get('panelId') not in [95, 96]:
        query_parts.append(f"timezone={params['timezone']}")
    
    # Для Kubernetes метрик
    if params['dashboard_uid'] == 'kuber_api':
        query_parts.append(f"timezone={params['timezone']}")
    
    # Для Gatling метрик
    if params['dashboard_uid'] == 'de9jk1ju5vmdcb':
        query_parts.append(f"timezone={params['timezone']}")
    
    # Для PostgreSQL метрик
    if params['dashboard_uid'] == 'fepxcz1pv79q8d':
        query_parts.append(f"timezone={params['timezone']}")
    
    query_string = '&'.join(query_parts)
    return f"{render_url}?{query_string}"


def download_metric(session: requests.Session, url: str, headers: dict, output_file: str) -> bool:
    """Download a single Grafana panel image to ``output_file``.

    Returns ``True`` on success, ``False`` otherwise.
    """
    try:
        response = session.get(url, headers=headers, verify=False, timeout=120)
        if response.status_code != 200:
            logging.error(
                f"HTTP {response.status_code} while downloading {url}: {response.text}"
            )
            return False

        with open(output_file, "wb") as f:
            f.write(response.content)

        logging.info(f"Файл сохранен: {output_file}")
        return True

    except (Timeout, ConnectionError, HTTPError, FileNotFoundError) as e:
        logging.error(f"Ошибка при скачивании {url}: {e}")
        return False

def download_gatling_metrics(cfg, main_folder_path):
    """
    Скачивает метрики Gatling для всех включенных скриптов.
    
    Args:
        cfg (dict): Конфигурационный словарь из config.yml
        main_folder_path (str): Путь к основной папке для сохранения метрик
    """
    try:
        if not cfg['services'].get('gatling_metrics_service', False):
            return
            
        logging.info("\n🚀 Начинаем скачивание Gatling метрик")
        
        # Получаем включенные Gatling скрипты
        gatling_scripts = cfg['gatling_grafana'].get('gatling_scripts', {})
        enabled_scripts = [script_name for script_name, enabled in gatling_scripts.items() if enabled]
        
        if not enabled_scripts:
            logging.info("⚠️  Нет включенных Gatling скриптов для скачивания")
            return
            
        logging.info(f"📋 Включенные Gatling скрипты: {', '.join(enabled_scripts)}")
        
        # Получаем конфигурацию для Gatling метрик
        gatling_metrics_config = load_metrics_config(cfg['gatling_grafana']['gatling_metrics_config'])
        
        # Настраиваем заголовки для аутентификации в Gatling Grafana
        base_url = str(cfg['gatling_grafana'].get('base_url', '') or '')
        if (not base_url) or base_url.startswith('/'):
            fallback = str(cfg.get('grafana', {}).get('base_url', '') or '')
            if fallback:
                logging.warning("GATLING_GRAFANA_BASE_URL не задан. Использую grafana.base_url как fallback")
                base_url = fallback
            else:
                logging.error("GATLING_GRAFANA_BASE_URL не задан или некорректен. Укажите корректный URL в .env")
                return

        api_key = str(cfg['gatling_grafana']['api_key'])
        if not api_key.lower().startswith('bearer '):
            api_key = f"Bearer {api_key}"
        gatling_headers = {
            'Authorization': api_key
        }
        
        # Параметры времени
        timezone = cfg['mainConfig']['timezone']
        from_time = to_utc_iso(cfg['mainConfig']['from'], timezone)
        to_time = to_utc_iso(cfg['mainConfig']['to'], timezone)
        
        # Создаем HTTP сессию
        session = create_session()
        
        total_successful = 0
        total_failed = 0
        
        # Проходим по каждому включенному скрипту
        for script_index, script_name in enumerate(enabled_scripts, 1):
            logging.info(f"\n📝 [{script_index}/{len(enabled_scripts)}] Обрабатываем скрипт: {script_name}")
            
            # Создаем папку для каждого скрипта
            script_folder = os.path.join(main_folder_path, "metrics", "gatling_metrics", script_name)
            os.makedirs(script_folder, exist_ok=True)
            logging.info(f"📁 Папка скрипта: {script_folder}")
            
            successful_downloads = 0
            failed_downloads = 0
            
            # Скачиваем все метрики для текущего скрипта
            for metric_index, metric in enumerate(gatling_metrics_config, 1):
                metric_name = metric.get('name', f'metric_{metric_index}')
                logging.info(f"  📈 [{metric_index}/{len(gatling_metrics_config)}] Скачиваем метрику: {metric_name}")
                
                try:
                    # Копируем переменные метрики для модификации
                    vars_dict = metric.get('vars', {}).copy()
                    
                    # Заменяем PLACEHOLDER в переменных Grafana на текущее имя скрипта
                    for full_var_name, value in vars_dict.items():
                        if isinstance(value, str) and "PLACEHOLDER" in value:
                            vars_dict[full_var_name] = value.replace("PLACEHOLDER", script_name)
                            logging.debug(f"    🔄 Заменили {full_var_name}: {vars_dict[full_var_name]}")
                    
                    # Параметры запроса
                    params = {
                        'base_url': cfg['gatling_grafana']['base_url'],
                        'dashboard_uid': metric['dashboard_uid'],
                        'dashboard_name': metric['dashboard_name'],
                        'orgId': metric['orgId'],
                        'panelId': metric['panelId'],
                        'width': metric['width'],
                        'height': metric['height'],
                        'timeout': vars_dict.get('timeout', 60),
                        'timezone': cfg['gatling_grafana']['timezone'],
                        'from': from_time,
                        'to': to_time,
                        'vars': vars_dict
                    }
                    
                    # Формируем полный URL для скачивания панели
                    render_url = build_grafana_url(params)
                    if not render_url.startswith('http'):
                        render_url = base_url.rstrip('/') + render_url
                    logging.debug(f"    🌐 URL: {render_url}")
                    
                    # Определяем имя файла
                    file_name = f"{metric_name}.png"
                    output_file = os.path.join(script_folder, file_name)
                    
                    # Скачиваем метрику
                    if download_metric(session, render_url, gatling_headers, output_file):
                        successful_downloads += 1
                        logging.info(f"    ✅ Успешно загружено: {file_name}")
                    else:
                        failed_downloads += 1
                        logging.error(f"    ❌ Ошибка при загрузке: {file_name}")
                        
                except Exception as e:
                    failed_downloads += 1
                    logging.error(f"    💥 Критическая ошибка при скачивании метрики {metric_name}: {str(e)}")
                    continue
            
            # Статистика по скрипту
            logging.info(f"\n📊 Статистика для скрипта {script_name}:")
            logging.info(f"  ✅ Успешно скачано: {successful_downloads}")
            logging.info(f"  ❌ Ошибок: {failed_downloads}")
            script_total = successful_downloads + failed_downloads
            if script_total > 0:
                logging.info(f"  📈 Процент успеха: {(successful_downloads/script_total*100):.1f}%")
                
            total_successful += successful_downloads
            total_failed += failed_downloads
        
        # Общая статистика по всем Gatling метрикам
        logging.info(f"\n🎉 Общая статистика Gatling метрик:")
        logging.info(f"  ✅ Всего успешно скачано: {total_successful}")
        logging.info(f"  ❌ Всего ошибок: {total_failed}")
        grand_total = total_successful + total_failed
        if grand_total > 0:
            logging.info(f"  📈 Общий процент успеха: {(total_successful/grand_total*100):.1f}%")
            
    except Exception as e:
        logging.error(f"💥 Критическая ошибка при скачивании Gatling метрик: {str(e)}")
        raise


def download_postgresql_metrics(cfg, main_folder_path):
    """
    Скачивает метрики PostgreSQL.

    Args:
        cfg (dict): Конфигурационный словарь из config.yml
        main_folder_path (str): Путь к основной папке для сохранения метрик
    """
    try:
        if not cfg['services'].get('postgresql_metrics_service', False):
            return

        logging.info("\n🚀 Начинаем скачивание PostgreSQL метрик")

        # Получаем конфигурацию для PostgreSQL метрик
        all_metrics_config = load_metrics_config(cfg['postgresql_grafana']['metrics_config'])
        
        # Фильтруем только PostgreSQL метрики
        postgresql_metrics_config = [
            metric for metric in all_metrics_config 
            if metric.get('name', '').startswith('postgresql_')
        ]
        
        if not postgresql_metrics_config:
            logging.info("⚠️  Нет PostgreSQL метрик для скачивания")
            return

        # Настраиваем заголовки для аутентификации в основной Grafana
        pg_base_url = str(cfg['postgresql_grafana'].get('base_url', '') or '')
        if (not pg_base_url) or pg_base_url.startswith('/'):
            fallback = str(cfg.get('grafana', {}).get('base_url', '') or '')
            if fallback:
                logging.warning("POSTGRESQL_GRAFANA_BASE_URL не задан. Использую grafana.base_url как fallback")
                pg_base_url = fallback
            else:
                logging.error("POSTGRESQL_GRAFANA_BASE_URL не задан или некорректен. Укажите корректный URL в .env")
                return

        pg_api_key = str(cfg['postgresql_grafana']['api_key'])
        if not pg_api_key.lower().startswith('bearer '):
            pg_api_key = f"Bearer {pg_api_key}"
        headers = {
            'Authorization': pg_api_key
        }

        # Параметры времени
        timezone = cfg['mainConfig']['timezone']
        from_time = to_utc_iso(cfg['mainConfig']['from'], timezone)
        to_time = to_utc_iso(cfg['mainConfig']['to'], timezone)

        # Создаем HTTP сессию
        session = create_session()

        successful_downloads = 0
        failed_downloads = 0

        # Переменные Grafana берём из каждой метрики (metrics_urls.yml)

        # Создаем папку для метрик PostgreSQL
        postgresql_folder = os.path.join(main_folder_path, "metrics", "postgresql_metrics")
        os.makedirs(postgresql_folder, exist_ok=True)
        logging.info(f"📁 Папка для метрик PostgreSQL: {postgresql_folder}")

        # Проходим по PostgreSQL метрикам
        for metric_index, metric in enumerate(postgresql_metrics_config, 1):
            metric_name = metric.get('name', f'metric_{metric_index}')
            logging.info(f"  📈 [{metric_index}/{len(postgresql_metrics_config)}] Скачиваем метрику: {metric_name}")

            try:
                # Берём переменные из метрики (и убираем служебные ключи вроде timeout)
                vars_dict = dict(metric.get('vars', {})) if isinstance(metric.get('vars', {}), dict) else {}
                if 'timeout' in vars_dict:
                    vars_dict.pop('timeout', None)

                # Параметры запроса
                params = {
                    'base_url': cfg['postgresql_grafana']['base_url'],
                    'dashboard_uid': metric['dashboard_uid'],
                    'dashboard_name': metric['dashboard_name'],
                    'orgId': metric['orgId'],
                    'panelId': metric['panelId'],
                    'width': metric['width'],
                    'height': metric['height'],
                    'timezone': cfg['postgresql_grafana']['timezone'],
                    'from': from_time,
                    'to': to_time,
                    'vars': vars_dict
                }

                # Формируем полный URL для скачивания панели
                render_url = build_grafana_url(params)
                if not render_url.startswith('http'):
                    render_url = pg_base_url.rstrip('/') + render_url
                logging.debug(f"    🌐 URL: {render_url}")

                # Определяем имя файла
                file_name = f"{metric_name}.png"
                output_file = os.path.join(postgresql_folder, file_name)

                # Скачиваем метрику
                if download_metric(session, render_url, headers, output_file):
                    successful_downloads += 1
                    logging.info(f"    ✅ Успешно загружено: {file_name}")
                else:
                    failed_downloads += 1
                    logging.error(f"    ❌ Ошибка при загрузке: {file_name}")

            except Exception as e:
                failed_downloads += 1
                logging.error(f"    💥 Критическая ошибка при скачивании метрики {metric_name}: {str(e)}")
                continue

        # Статистика по PostgreSQL метрикам
        logging.info(f"\n📊 Статистика для PostgreSQL метрик:")
        logging.info(f"  ✅ Успешно скачано: {successful_downloads}")
        logging.info(f"  ❌ Ошибок: {failed_downloads}")
        total = successful_downloads + failed_downloads
        if total > 0:
            logging.info(f"  📈 Общий процент успеха: {(successful_downloads/total*100):.1f}%")

    except Exception as e:
        logging.error(f"💥 Критическая ошибка при скачивании PostgreSQL метрик: {str(e)}")
        raise

def download_grafana_metrics(cfg, metrics, main_folder_path, services):
    """
    Скачивает метрики из Grafana для всех включенных сервисов приложений.
    
    Функция:
    1. Создает основную папку metrics
    2. Для каждого включенного сервиса (где значение = true) создает отдельную папку
    3. Скачивает все метрики для каждого сервиса в его папку
    4. Заменяет PLACEHOLDER на реальные названия сервисов
    5. Скачивает Gatling метрики (если включено)
    
    Args:
        cfg (dict): Конфигурационный словарь из config.yml
        metrics (list): Список метрик из metrics_urls.yml  
        main_folder_path (str): Путь к основной папке для сохранения метрик
        services (list): Список названий включенных сервисов приложений (где значение = true)
        
    Raises:
        Exception: Если возникла критическая ошибка при скачивании метрик
    """
    try:
        # ========== ПОДГОТОВКА ПАПОК И КОНФИГУРАЦИИ ==========
        
        # Создаем базовую папку для всех метрик
        base_metrics_folder = os.path.join(main_folder_path, "metrics")
        os.makedirs(base_metrics_folder, exist_ok=True)
        logging.info(f"📁 Создана базовая папка для метрик: {base_metrics_folder}")
        
        # Настраиваем заголовки для аутентификации в основной Grafana
        gr_base_url = str(cfg['grafana'].get('base_url', '') or '')
        if (not gr_base_url) or gr_base_url.startswith('/'):
            logging.error("GRAFANA_BASE_URL не задан или некорректен. Укажите корректный URL в .env")
            return

        gr_api_key = str(cfg['grafana']['api_key'])
        if not gr_api_key.lower().startswith('bearer '):
            gr_api_key = f"Bearer {gr_api_key}"
        headers = {
            'Authorization': gr_api_key  # Bearer token для доступа к API
        }
        
        # ========== ПАРАМЕТРЫ ВРЕМЕНИ ==========
        
        # Извлекаем параметры времени из конфигурации
        timezone = cfg['mainConfig']['timezone']        # Часовой пояс (например, Europe/Moscow)
        from_time = to_utc_iso(cfg['mainConfig']['from'], timezone)  # Начальное время в UTC ISO
        to_time = to_utc_iso(cfg['mainConfig']['to'], timezone)      # Конечное время в UTC ISO
        
        logging.info(f"⏰ Временной диапазон: {cfg['mainConfig']['from']} - {cfg['mainConfig']['to']} ({timezone})")
        logging.info(f"🔄 Конвертировано в UTC: {from_time} - {to_time}")

        # Создаем HTTP сессию с настройками повторных попыток
        session = create_session()
        
        # ========== СКАЧИВАНИЕ GATLING МЕТРИК ==========
        download_gatling_metrics(cfg, main_folder_path)
        
        # ========== СКАЧИВАНИЕ POSTGRESQL МЕТРИК ==========
        download_postgresql_metrics(cfg, main_folder_path)
        
        # ========== ОБРАБОТКА СЕРВИСОВ ==========
        
        total_services = len(services)
        logging.info(f"🚀 Начинаем скачивание метрик для {total_services} сервисов: {', '.join(services)}")
        
        # Проходим по всем активным сервисам приложений
        for service_index, service in enumerate(services, 1):
            logging.info(f"\n📊 [{service_index}/{total_services}] Обрабатываем сервис: {service}")
            
            # Создаем отдельную папку для каждого сервиса
            service_folder = os.path.join(base_metrics_folder, service)
            os.makedirs(service_folder, exist_ok=True)
            logging.info(f"📁 Папка сервиса: {service_folder}")

            # ========== ОБРАБОТКА МЕТРИК ==========
            
            total_metrics = len(metrics)
            successful_downloads = 0
            failed_downloads = 0
            
            # Фильтруем PostgreSQL метрики, так как они скачиваются отдельно
            service_metrics = [metric for metric in metrics if not getattr(metric, 'name', '').startswith('postgresql_')]
            
            for metric_index, metric in enumerate(service_metrics, 1):
                metric_name = getattr(metric, 'name', f'metric_{metric_index}')  # Инициализируем metric_name сразу
                try:
                    logging.info(f"  📈 [{metric_index}/{len(service_metrics)}] Скачиваем метрику: {metric_name}")

                    # Копируем переменные метрики для модификации
                    vars_dict = getattr(metric, 'vars', {}).copy()

                    # ========== ЗАМЕНА PLACEHOLDER НА РЕАЛЬНЫЕ ЗНАЧЕНИЯ ==========
                    
                    # Заменяем PLACEHOLDER в переменных Grafana на название текущего сервиса
                    # Переменные уже имеют префикс var- в конфиге, поэтому работаем с полными именами
                    for full_var_name, value in vars_dict.items():
                        if isinstance(value, str) and "PLACEHOLDER" in value:
                            vars_dict[full_var_name] = value.replace("PLACEHOLDER", service)
                            logging.debug(f"    🔄 Заменили {full_var_name}: {vars_dict[full_var_name]}")

                    # ========== ФОРМИРОВАНИЕ ПАРАМЕТРОВ ЗАПРОСА ==========
                    
                    params = {
                        'base_url': cfg['grafana']['base_url'],           # URL Grafana сервера
                        'dashboard_uid': metric.dashboard_uid,         # Уникальный ID dashboard'а
                        'dashboard_name': metric.dashboard_name,       # Название dashboard'а
                        'orgId': metric.orgId,                         # ID организации
                        'panelId': metric.panelId,                     # ID панели
                        'width': metric.width,                         # Ширина изображения
                        'height': metric.height,                       # Высота изображения
                        'timeout': getattr(metric, 'timeout', vars_dict.get('timeout', 60)),  # Таймаут
                        'timezone': timezone,                             # Часовой пояс
                        'from': from_time,                                # Начальное время (UTC)
                        'to': to_time,                                    # Конечное время (UTC)
                        'vars': vars_dict                                 # Переменные dashboard'а
                    }

                    # Формируем полный URL для скачивания панели
                    render_url = build_grafana_url(params)
                    if not render_url.startswith('http'):
                        render_url = gr_base_url.rstrip('/') + render_url
                    logging.info(f"    🌐 Полный URL: {render_url}")

                    # ========== ОПРЕДЕЛЕНИЕ ИМЕНИ ФАЙЛА ==========
                    
                    # Формируем имя файла для сохранения
                    file_name = f"{metric_name}.png"
                    output_file = os.path.join(service_folder, file_name)

                    # ========== СКАЧИВАНИЕ МЕТРИКИ ==========
                    
                    # Скачиваем изображение панели
                    if download_metric(session, render_url, headers, output_file):
                        successful_downloads += 1
                        logging.info(f"    ✅ Успешно: {file_name}")
                    else:
                        failed_downloads += 1
                        logging.warning(f"    ❌ Ошибка: {file_name}")

                except Exception as e:
                    failed_downloads += 1
                    logging.error(f"    💥 Критическая ошибка при скачивании метрики {metric_name}: {str(e)}")
                    continue
            
            # ========== СТАТИСТИКА ПО СЕРВИСУ ==========
            
            logging.info(f"\n📊 Статистика для сервиса {service}:")
            logging.info(f"  ✅ Успешно скачано: {successful_downloads}")
            logging.info(f"  ❌ Ошибок: {failed_downloads}")
            if successful_downloads + failed_downloads > 0:
                logging.info(f"  📈 Общий процент успеха: {(successful_downloads/(successful_downloads+failed_downloads)*100):.1f}%")
        
        # ========== ОБЩАЯ СТАТИСТИКА ==========
        
        logging.info(f"\n🎉 Скачивание метрик завершено для всех {total_services} сервисов!")
        logging.info(f"📁 Результаты сохранены в: {base_metrics_folder}")

    except Exception as e:
        logging.error(f"💥 Критическая ошибка при скачивании метрик Grafana: {str(e)}")
        raise
