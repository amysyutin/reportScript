import os
import sys
import yaml
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.config_loader import load_metrics_config, Metric


def test_timeout_autofix(tmp_path, caplog):
    metrics_data = {
        'metrics': [
            {
                'name': 'm1',
                'dashboard_uid': 'uid',
                'dashboard_name': 'dash',
                'panelId': 1,
                'vars': {
                    'timeout': 15,
                    'var-application': 'app'
                }
            }
        ]
    }
    path = tmp_path / 'metrics.yml'
    path.write_text(yaml.safe_dump(metrics_data))

    with caplog.at_level(logging.WARNING):
        metrics = load_metrics_config(str(path))
        assert metrics[0].timeout == 15
        assert "Autofixed timeout" in caplog.text

def test_missing_required_field(tmp_path):
    metrics_data = {'metrics': [{'dashboard_uid': 'uid', 'dashboard_name': 'dash', 'panelId': 1}]}
    path = tmp_path / 'metrics.yml'
    path.write_text(yaml.safe_dump(metrics_data))
    try:
        load_metrics_config(str(path))
        assert False, "Expected ValueError"
    except ValueError as e:
        assert "name" in str(e)
