#!/usr/bin/env python3

import sys
import os
sys.path.append('.')

from src.config import load_config
from src.config_loader import load_metrics_config
from src.grafana_service import build_grafana_url
from src.utils import to_utc_iso

def test_url_generation():
    """Test URL generation for CPU usage metric"""
    
    # Load config
    cfg = load_config()
    metrics = load_metrics_config(cfg['grafana']['metrics_config'])
    
    # Get first metric (cpu_usage)
    cpu_metric = metrics[0]
    service = "dh-documents-service"
    
    print(f"Testing metric: {cpu_metric.name}")
    print(f"Service: {service}")
    
    # Process variables
    vars_dict = getattr(cpu_metric, 'vars', {}).copy()
    
    # Replace PLACEHOLDER and add var- prefix
    for var_name in ['application', 'instance', 'memory_pool_heap', 'memory_pool_nonheap']:
        if var_name in vars_dict:
            vars_dict[f"var-{var_name}"] = vars_dict.pop(var_name).replace("PLACEHOLDER", service)
    
    print("Variables after processing:")
    for k, v in vars_dict.items():
        print(f"  {k}: {v}")
    
    # Build time range
    timezone = cfg['mainConfig']['timezone']
    from_time = to_utc_iso(cfg['mainConfig']['from'], timezone)
    to_time = to_utc_iso(cfg['mainConfig']['to'], timezone)
    
    print(f"Time range: {from_time} - {to_time}")
    
    # Build params
    params = {
        'base_url': cfg['grafana']['base_url'],
        'dashboard_uid': cpu_metric.dashboard_uid,
        'dashboard_name': cpu_metric.dashboard_name,
        'orgId': cpu_metric.orgId,
        'panelId': cpu_metric.panelId,
        'width': cpu_metric.width,
        'height': cpu_metric.height,
        'timezone': timezone,
        'from': from_time,
        'to': to_time,
        'vars': vars_dict
    }
    
    # Generate URL
    our_url = build_grafana_url(params)
    
    print("\n" + "="*80)
    print("OUR GENERATED URL:")
    print(our_url)
    
    print("\n" + "="*80)
    print("EXPECTED URL FROM curl_grafana.ini:")
    expected_url = "https://grafana.stress-astra.lan.lanit.ru/render/d-solo/spring-boot-2x/spring-boot-2x?orgId=1&panelId=95&width=1000&height=500&timezone=Europe/Moscow&from=2025-07-21T10:13:45.562Z&to=2025-07-21T11:52:33.381Z&var-application=dh-documents-service&var-instance=$__all&var-memory_pool_heap=$__all&var-memory_pool_nonheap=$__all"
    print(expected_url)
    
    print("\n" + "="*80)
    print("DIFFERENCES:")
    
    # Split URLs into components for comparison
    our_parts = our_url.split('?')[1].split('&') if '?' in our_url else []
    expected_parts = expected_url.split('?')[1].split('&') if '?' in expected_url else []
    
    print(f"Our parts ({len(our_parts)}):")
    for i, part in enumerate(our_parts):
        print(f"  {i}: {part}")
    
    print(f"\nExpected parts ({len(expected_parts)}):")
    for i, part in enumerate(expected_parts):
        print(f"  {i}: {part}")

if __name__ == "__main__":
    test_url_generation()
