import os
import sys
import urllib.parse

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.grafana_service import build_grafana_url


def test_list_variable_expansion():
    params = {
        'base_url': 'http://localhost:3000',
        'dashboard_uid': 'uid1',
        'dashboard_name': 'dash',
        'orgId': 1,
        'panelId': 2,
        'width': 100,
        'height': 50,
        'timeout': 60,
        'timezone': 'UTC',
        'from': '2025-07-21T10:00:00Z',
        'to': '2025-07-21T11:00:00Z',
        'vars': {
            'container': ['a', 'b']
        }
    }
    url = build_grafana_url(params)
    parsed = urllib.parse.urlparse(url)
    query = urllib.parse.parse_qs(parsed.query)
    assert query['var-container'] == ['a', 'b']
    assert query['timezone'] == ['UTC']
    assert query['from'] == ['2025-07-21T10:00:00Z']
    assert query['to'] == ['2025-07-21T11:00:00Z']
    expected_path = '/render/d-solo/uid1/dash'
    assert parsed.path == expected_path
