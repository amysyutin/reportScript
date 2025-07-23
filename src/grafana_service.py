import os
import requests
import logging
import urllib.parse
import urllib3
from requests.adapters import HTTPAdapter, Retry
from requests.exceptions import Timeout, ConnectionError, HTTPError
from src.utils import to_utc_iso

# Отключаем предупреждения о небезопасном SSL
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
    """Build full Grafana render URL.

    Parameters expected in ``params``:
        base_url (str): base Grafana URL
        dashboard_uid (str): dashboard uid
        dashboard_name (str): dashboard name
        orgId (int/str)
        panelId (int/str)
        width (int/str)
        height (int/str)
        timeout (int/str)
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

    query = {
        'orgId': params['orgId'],
        'panelId': params['panelId'],
        'width': params['width'],
        'height': params['height'],
        'timeout': params['timeout'],
        'timezone': params['timezone'],
        'from': params['from'],
        'to': params['to']
    }

    vars_dict = params.get('vars', {})
    for name, value in vars_dict.items():
        query[f'var-{name}'] = value

    query_string = urllib.parse.urlencode(query, doseq=True)
    return f"{render_url}?{query_string}"


def download_metric(session: requests.Session, url: str, headers: dict, output_file: str) -> bool:
    """Download a single Grafana panel image to ``output_file``.

    Returns ``True`` on success, ``False`` otherwise.
    """
    try:
        response = session.get(url, headers=headers, verify=True, timeout=120)
        if response.status_code != 200:
            logging.error(
                f"HTTP {response.status_code} while downloading {url}: {response.text}"
            )
            return False

        with open(output_file, "wb") as f:
            f.write(response.content)

        logging.info(f"Файл сохранен: {output_file}")
        return True

    except (Timeout, ConnectionError, HTTPError) as e:
        logging.error(f"Ошибка при скачивании {url}: {e}")
        return False

def download_grafana_metrics(cfg, metrics, main_folder_path, services):
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
        # Создаем базовую папку для метрик
        base_metrics_folder = os.path.join(main_folder_path, "metrics")
        os.makedirs(base_metrics_folder, exist_ok=True)
        logging.info(f"Создана папка для метрик: {base_metrics_folder}")
        
        # Настраиваем заголовки для запросов к Grafana
        headers = {
            'Authorization': cfg['grafana']['api_key']
        }
        
        # Получаем временной диапазон из конфигурации
        timezone = cfg['mainConfig']['timezone']
        from_time = to_utc_iso(cfg['mainConfig']['from'], timezone)
        to_time = to_utc_iso(cfg['mainConfig']['to'], timezone)

        session = create_session()
        
        # Проходим по всем сервисам, для которых нужно скачать метрики
        for service in services:
            service_folder = os.path.join(base_metrics_folder, service)
            os.makedirs(service_folder, exist_ok=True)
            logging.info(f"Скачиваем метрики для сервиса {service} в {service_folder}")

            for metric in metrics:
                try:
                    metric_name = metric['name']
                    logging.info(f"Скачивание метрики {metric_name}...")

                    vars_dict = metric.get('vars', {}).copy()

                    orig_container = vars_dict.get('var-container')
                    multi_service = isinstance(orig_container, list)

                    # Подставляем название сервиса в переменные
                    if 'var-application' in vars_dict:
                        vars_dict['var-application'] = service

                    if 'var-container' in vars_dict:
                        vars_dict['var-container'] = service

                    if 'var-instance' in vars_dict:
                        old_app = metric.get('vars', {}).get('var-application')
                        if old_app and isinstance(vars_dict['var-instance'], str):
                            vars_dict['var-instance'] = vars_dict['var-instance'].replace(old_app, service)
                        else:
                            vars_dict['var-instance'] = service

                    params = {
                        'base_url': cfg['grafana']['base_url'],
                        'dashboard_uid': metric['dashboard_uid'],
                        'dashboard_name': metric['dashboard_name'],
                        'orgId': metric['orgId'],
                        'panelId': metric['panelId'],
                        'width': metric['width'],
                        'height': metric['height'],
                        'timeout': metric.get('timeout', vars_dict.get('timeout', 60)),
                        'timezone': timezone,
                        'from': from_time,
                        'to': to_time,
                        'vars': vars_dict
                    }

                    render_url = build_grafana_url(params)

                    if multi_service:
                        file_name = f"{metric_name}__{service}.png"
                    else:
                        file_name = f"{metric_name}.png"

                    output_file = os.path.join(service_folder, file_name)

                    if not download_metric(session, render_url, headers, output_file):
                        continue

                except Exception as e:
                    logging.error(f"Ошибка при скачивании метрики {metric_name}: {str(e)}")
                    continue

    except Exception as e:
        logging.error(f"Ошибка при скачивании метрик Grafana: {str(e)}")
        raise
