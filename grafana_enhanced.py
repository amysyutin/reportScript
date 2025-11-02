
#!/usr/bin/env python3
"""
Упрощённый отладочный клиент, использующий src/grafana_service.py.
Основная логика запросов и валидации вынесена в модуль сервиса.
"""

import os
import sys
import argparse
import logging
import urllib3

sys.path.append('src')
from config import load_config
from config_loader import load_metrics_config
from grafana_service import create_session, build_grafana_url, download_metric
from utils import to_utc_iso

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def test_connection(cfg) -> bool:
    import requests
    base_url = cfg['grafana']['base_url']
    api_key = str(cfg['grafana']['api_key'])
    if not api_key.lower().startswith('bearer '):
        api_key = f"Bearer {api_key}"
    try:
        resp = requests.get(f"{base_url}/api/health", headers={"Authorization": api_key}, verify=False, timeout=10)
        if resp.status_code == 200:
            logging.info("✅ Grafana API connection successful")
            return True
        logging.error(f"❌ Grafana API connection failed: {resp.status_code}")
        return False
    except Exception as e:
        logging.error(f"❌ Connection error: {e}")
        return False


def list_metrics(metrics):
    print("\nAvailable metrics:")
    for i, m in enumerate(metrics, 1):
        name = getattr(m, 'name', None) or m.get('name')
        print(f"{i:2d}. {name}")


def download_single_metric(cfg, metric):
    metric_name = getattr(metric, 'name', None) or metric['name']
    base_url = cfg['grafana']['base_url']
    timezone = cfg['mainConfig']['timezone']
    from_time = to_utc_iso(cfg['mainConfig']['from'], timezone)
    to_time = to_utc_iso(cfg['mainConfig']['to'], timezone)

    vars_dict = getattr(metric, 'vars', None) or metric.get('vars', {})
    params = {
        'base_url': base_url,
        'dashboard_uid': getattr(metric, 'dashboard_uid', None) or metric['dashboard_uid'],
        'dashboard_name': getattr(metric, 'dashboard_name', None) or metric['dashboard_name'],
        'orgId': getattr(metric, 'orgId', None) or getattr(metric, 'orgId', None),
        'panelId': getattr(metric, 'panelId', None) or metric['panelId'],
        'width': getattr(metric, 'width', None) or getattr(metric, 'width', None),
        'height': getattr(metric, 'height', None) or getattr(metric, 'height', None),
        'timezone': timezone,
        'from': from_time,
        'to': to_time,
        'vars': vars_dict,
    }
    url = build_grafana_url(params)

    api_key = str(cfg['grafana']['api_key'])
    if not api_key.lower().startswith('bearer '):
        api_key = f"Bearer {api_key}"
    headers = {"Authorization": api_key}

    session = create_session()
    output_dir = "/tmp/grafana_test"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"{metric_name}.png")
    ok = download_metric(session, url, headers, output_file)
    if ok:
        logging.info(f"✅ Saved: {output_file}")
    else:
        logging.error(f"❌ Failed: {metric_name}")
    return ok


def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    parser = argparse.ArgumentParser(description='Grafana debug client')
    parser.add_argument('--test-connection', action='store_true')
    parser.add_argument('--list-metrics', action='store_true')
    parser.add_argument('--test-metric', type=str)
    args = parser.parse_args()

    cfg = load_config('config.yml')
    metrics = load_metrics_config(cfg['grafana']['metrics_config'])

    if args.test_connection:
        test_connection(cfg)
        return

    if args.list_metrics:
        list_metrics(metrics)
        return

    if args.test_metric:
        m = next((mm for mm in metrics if (getattr(mm, 'name', None) or mm.get('name')) == args.test_metric), None)
        if not m:
            logging.error(f"Metric '{args.test_metric}' not found")
            return
        download_single_metric(cfg, m)
        return

    parser.print_help()


if __name__ == "__main__":
    main()
