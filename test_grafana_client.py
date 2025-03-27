from config_manager import ConfigManager
from grafana_client import GrafanaClient
import os

def test_grafana_client():
    # Инициализация конфигурации
    config_manager = ConfigManager('config.ini', 'test_config.ini')
    
    # Создание клиента Grafana
    grafana = GrafanaClient(config_manager)
    
    # Тест 1: Проверка валидации URL
    print("\nТест 1: Проверка валидации URL")
    test_url = "https://grafana.stress-astra.lan.lanit.ru/d/test"
    print(f"Валидация URL {test_url}: {grafana._validate_url(test_url)}")
    
    # Тест 2: Проверка валидации временного диапазона
    print("\nТест 2: Проверка валидации временного диапазона")
    test_time_range = {
        'from': config_manager.test_config['Test']['start_time'],
        'to': config_manager.test_config['Test']['end_time']
    }
    is_valid, message = grafana._validate_time_range(test_time_range)
    print(f"Валидация временного диапазона: {is_valid}")
    if not is_valid:
        print(f"Сообщение об ошибке: {message}")
    
    # Тест 3: Проверка загрузки всех метрик
    print("\nТест 3: Проверка загрузки всех метрик")
    grafana.set_report_directory(config_manager.report_dir)
    
    # Загружаем каждую метрику отдельно для лучшего контроля
    metrics = {
        "spring_boot_cpu": "spring_boot_cpu.png",
        "k8s_panel_5": "k8s_panel_5.png",
        "k8s_panel_7": "k8s_panel_7.png",
        "analytics_panel_199": "cpu_usage_by_pod.png",
        "analytics_panel_176": "memory_usage_by_pod.png",
        "analytics_panel_49": "throttling.png"
    }
    
    grafana.download_all_metrics(metrics)

if __name__ == "__main__":
    test_grafana_client() 