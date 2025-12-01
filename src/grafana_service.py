import os
import requests
import logging
import urllib.parse
import urllib3
from typing import List, Tuple, Optional, Dict
from requests.adapters import HTTPAdapter, Retry
from requests.exceptions import Timeout, ConnectionError, HTTPError
from utils import to_utc_iso, to_utc_epoch_ms

# ========== ИМПОРТ ПРОКСИ УТИЛИТ ==========
from proxy_utils import validate_and_prepare_proxy
# ==========================================

# Отключаем предупреждения о небезопасном SSL
from config import load_metrics_config
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def create_session(
    retries: int = 3, 
    backoff_factor: float = 0.5,
    proxies: Optional[Dict[str, str]] = None
) -> requests.Session:
    """
    Создаёт HTTP сессию с настройками повторных попыток и прокси.
    
    Args:
        retries (int): Количество повторных попыток при ошибках
        backoff_factor (float): Множитель задержки между попытками
        proxies (dict, optional): Словарь прокси {'http': '...', 'https': '...'}
        
    Returns:
        requests.Session: Настроенная сессия
    """
    session = requests.Session()

    # ========== НАСТРОЙКА ПРОКСИ ==========
    if proxies:
        session.proxies.update(proxies)
        logging.info(f"🔒 HTTP сессия настроена с прокси: {proxies.get('https', proxies.get('http'))}")
    else:
        logging.info("🌐 HTTP сессия без прокси (прямое подключение)")
    # ======================================

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
    """Собирает полный URL рендера панели Grafana.

    Обязательные ключи в ``params``:
        - base_url, dashboard_uid, dashboard_name, orgId, panelId, width, height, timezone, from, to
        - vars (dict, опционально): элементы могут быть строками или списками. Имена будут приведены к виду 'var-*'
    """

    render_url = f"{params['base_url']}/render/d-solo/{params['dashboard_uid']}/{params['dashboard_name']}"

    # Базовые параметры
    query: List[Tuple[str, str]] = []
    for key in ["orgId", "panelId", "width", "height", "timezone", "from", "to"]:
        value = params.get(key)
        if value is not None:
            query.append((key, str(value)))

    # Переменные Grafana: нормализуем к виду var-*
    vars_dict = params.get("vars", {}) or {}
    for raw_name, raw_value in vars_dict.items():
        name = raw_name if raw_name.startswith("var-") else f"var-{raw_name}"
        # Поддержка списков значений (doseq)
        if isinstance(raw_value, list):
            for item in raw_value:
                query.append((name, str(item)))
        else:
            query.append((name, str(raw_value)))

    # Формируем строку запроса c поддержкой повторяющихся ключей
    query_string = urllib.parse.urlencode(query, doseq=True)
    return f"{render_url}?{query_string}"


def _is_png_file(path: str) -> bool:
    """Проверяет PNG по сигнатуре файла."""
    try:
        with open(path, "rb") as f:
            header = f.read(8)
        return header.startswith(b"\x89PNG")
    except Exception:
        return False


def download_metric(session: requests.Session, url: str, headers: dict, output_file: str) -> bool:
    """Download a single Grafana panel image to ``output_file``.

    Returns ``True`` on success, ``False`` otherwise.
    """
    try:
        req_headers = dict(headers or {})
        req_headers.setdefault("Accept", "image/png")
        response = session.get(url, headers=req_headers, verify=False, timeout=120)
        if response.status_code != 200:
            logging.error(
                f"HTTP {response.status_code} while downloading {url}: {response.text}"
            )
            return False

        content_type = response.headers.get("Content-Type", "").lower()
        content_length = int(response.headers.get("Content-Length", "0") or 0)

        # Если это не PNG – вероятно, ошибка авторизации/HTML страница
        if "image/png" not in content_type:
            snippet = response.text[:200] if hasattr(response, "text") else ""
            logging.error(f"Неверный Content-Type '{content_type}' для {url}. Фрагмент ответа: {snippet}")
            return False

        # Сохраняем файл
        with open(output_file, "wb") as f:
            f.write(response.content)

        # Проверка содержимого файла: размер и PNG-сигнатура
        if content_length and content_length < 8000:
            logging.warning(f"Возможна пустая картинка (<8KB): {output_file} ({content_length} байт)")
        if not _is_png_file(output_file):
            logging.error(f"Файл {output_file} не является валидным PNG")
            try:
                os.remove(output_file)
            except Exception:
                pass
            return False

        logging.info(f"Файл сохранен: {output_file}")
        return True

    except (Timeout, ConnectionError, HTTPError, FileNotFoundError) as e:
        logging.error(f"Ошибка при скачивании {url}: {e}")
        return False

def download_gatling_metrics(cfg, main_folder_path, session: Optional[requests.Session] = None):
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
        
        # Получаем включенные Gatling скрипты (поддерживаем разные размещения в конфиге)
        gatling_scripts = {}
        source_hint = ""

        cand = (cfg.get('gatling_grafana') or {}).get('gatling_scripts') or {}
        if isinstance(cand, dict) and cand:
            gatling_scripts = cand
            source_hint = "gatling_grafana.gatling_scripts"
        else:
            cand = (cfg.get('services') or {}).get('gatling_scripts') or {}
            if isinstance(cand, dict) and cand:
                gatling_scripts = cand
                source_hint = "services.gatling_scripts"
            else:
                cand = cfg.get('gatling_scripts') or {}
                if isinstance(cand, dict) and cand:
                    gatling_scripts = cand
                    source_hint = "gatling_scripts"

        enabled_scripts = [script_name for script_name, enabled in gatling_scripts.items() if enabled]

        if not enabled_scripts:
            logging.info("⚠️  Нет включенных Gatling скриптов для скачивания")
            return
        else:
            if source_hint:
                logging.info(f"📋 Использую список Gatling-скриптов из: {source_hint}")
            
        logging.info(f"📋 Включенные Gatling скрипты: {', '.join(enabled_scripts)}")


        # ========== СОЗДАЁМ/ПЕРЕИСПОЛЬЗУЕМ HTTP СЕССИЮ ==========
        if session is None:
            # Если сессия не передана, создаём новую с прокси
            proxies = validate_and_prepare_proxy(cfg)
            session = create_session(proxies=proxies)
        # ========================================================
        
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
        from_time = to_utc_epoch_ms(cfg['mainConfig']['from'], timezone)
        to_time = to_utc_epoch_ms(cfg['mainConfig']['to'], timezone)
        
        # Создаем/переиспользуем HTTP сессию
        session = session or create_session()
        
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
                        'base_url': base_url,
                        'dashboard_uid': metric['dashboard_uid'],
                        'dashboard_name': metric['dashboard_name'],
                        'orgId': metric['orgId'],
                        'panelId': metric['panelId'],
                        'width': metric['width'],
                        'height': metric['height'],
                        'timeout': vars_dict.get('timeout', 60),
                        'timezone': timezone,
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


def download_postgresql_metrics(cfg, main_folder_path, session: Optional[requests.Session] = None):
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
        from_time = to_utc_epoch_ms(cfg['mainConfig']['from'], timezone)
        to_time = to_utc_epoch_ms(cfg['mainConfig']['to'], timezone)

        # Создаем/переиспользуем HTTP сессию
        session = session or create_session()

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
                    'base_url': pg_base_url,
                    'dashboard_uid': metric['dashboard_uid'],
                    'dashboard_name': metric['dashboard_name'],
                    'orgId': metric['orgId'],
                    'panelId': metric['panelId'],
                    'width': metric['width'],
                    'height': metric['height'],
                    'timezone': timezone,
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


        # ========== СОЗДАЁМ/ПЕРЕИСПОЛЬЗУЕМ HTTP СЕССИЮ ==========
        if session is None:
            # Если сессия не передана, создаём новую с прокси
            proxies = validate_and_prepare_proxy(cfg)
            session = create_session(proxies=proxies)
        # ======================================================== 

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

        # ========== НАСТРОЙКА ПРОКСИ ==========
        proxies = validate_and_prepare_proxy(cfg)
        # ======================================
        
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
        from_time = to_utc_epoch_ms(cfg['mainConfig']['from'], timezone)  # Начальное время (epoch ms)
        to_time = to_utc_epoch_ms(cfg['mainConfig']['to'], timezone)      # Конечное время (epoch ms)
        
        logging.info(f"⏰ Временной диапазон: {cfg['mainConfig']['from']} - {cfg['mainConfig']['to']} ({timezone})")
        logging.info(f"🔄 Конвертировано в UTC: {from_time} - {to_time}")

        # ========== СОЗДАЁМ HTTP СЕССИЮ С ПРОКСИ ==========
        session = create_session(proxies=proxies)
        # ==================================================
        
        # ========== СКАЧИВАНИЕ GATLING МЕТРИК ==========
        download_gatling_metrics(cfg, main_folder_path, session)
        
        # ========== СКАЧИВАНИЕ POSTGRESQL МЕТРИК ==========
        download_postgresql_metrics(cfg, main_folder_path, session)
        
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
                        'base_url': gr_base_url,           # URL Grafana сервера
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
