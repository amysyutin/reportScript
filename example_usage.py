#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Пример использования параметризованного скрипта скачивания метрик Grafana

Этот скрипт демонстрирует, как легко изменять:
1. 📅 Временной диапазон (from/to)
2. 🌍 Часовой пояс (timezone)
3. 🔧 Активные сервисы приложений
4. 📊 Набор метрик для скачивания

Автор: Система мониторинга LANIT
"""

import yaml
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def update_config_time_range(config_file: str, hours_back: int = 2):
    """
    Обновляет временной диапазон в конфигурации.
    
    Args:
        config_file (str): Путь к файлу config.yml
        hours_back (int): Сколько часов назад начинать (по умолчанию 2)
    """
    try:
        # Загружаем текущую конфигурацию
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Вычисляем новые временные границы
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours_back)
        
        # Обновляем временные параметры
        config['mainConfig']['from'] = start_time.strftime('%Y-%m-%d %H:%M:%S')
        config['mainConfig']['to'] = end_time.strftime('%Y-%m-%d %H:%M:%S')
        
        # Сохраняем обновленную конфигурацию
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        
        logging.info(f"✅ Обновлен временной диапазон:")
        logging.info(f"   📅 От: {config['mainConfig']['from']}")
        logging.info(f"   📅 До: {config['mainConfig']['to']}")
        logging.info(f"   🌍 Часовой пояс: {config['mainConfig']['timezone']}")
        
    except Exception as e:
        logging.error(f"❌ Ошибка при обновлении времени: {str(e)}")

def update_active_services(config_file: str, services_to_enable: list):
    """
    Обновляет список активных сервисов в конфигурации.
    
    Args:
        config_file (str): Путь к файлу config.yml
        services_to_enable (list): Список сервисов для активации
    """
    try:
        # Загружаем текущую конфигурацию
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Получаем все сервисы (исключая системные)
        system_services = ['ssh_service', 'grafana_service']
        all_services = config.get('services', {})
        
        # Отключаем все сервисы приложений
        for service_name in all_services:
            if service_name not in system_services:
                all_services[service_name] = False
        
        # Включаем только выбранные сервисы
        for service_name in services_to_enable:
            if service_name in all_services and service_name not in system_services:
                all_services[service_name] = True
                logging.info(f"🔧 Активировали сервис: {service_name}")
            else:
                logging.warning(f"⚠️  Сервис не найден: {service_name}")
        
        # Сохраняем обновленную конфигурацию
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        
        # Показываем итоговый список активных сервисов
        active_services = [name for name, enabled in all_services.items() 
                          if enabled and name not in system_services]
        logging.info(f"✅ Активные сервисы приложений: {', '.join(active_services) if active_services else 'нет'}")
        
    except Exception as e:
        logging.error(f"❌ Ошибка при обновлении сервисов: {str(e)}")

def show_available_metrics(metrics_file: str):
    """
    Показывает список доступных метрик для скачивания.
    
    Args:
        metrics_file (str): Путь к файлу metrics_urls.yml
    """
    try:
        with open(metrics_file, 'r', encoding='utf-8') as f:
            metrics_config = yaml.safe_load(f)
        
        metrics = metrics_config.get('metrics', [])
        
        logging.info(f"📊 Доступные метрики ({len(metrics)} штук):")
        
        # Группируем метрики по категориям
        categories = {
            'SPRING BOOT МЕТРИКИ': [],
            'ПАМЯТЬ': [],
            'ПОТОКИ И КЛАССЫ': [],
            'GARBAGE COLLECTION': [],
            'HTTP МЕТРИКИ': [],
            'KUBERNETES МЕТРИКИ': []
        }
        
        for metric in metrics:
            name = metric.get('name', 'Неизвестно')
            panel_id = metric.get('panelId', 'N/A')
            dashboard = metric.get('dashboard_uid', 'N/A')
            
            # Определяем категорию по названию и dashboard'у
            if 'cpu_usage' in name or 'load_average' in name:
                categories['SPRING BOOT МЕТРИКИ'].append(f"  📈 {name} (panel: {panel_id})")
            elif any(mem_word in name for mem_word in ['eden', 'old_gen', 'survivor', 'metaspace', 'compressed']):
                categories['ПАМЯТЬ'].append(f"  🧠 {name} (panel: {panel_id})")
            elif any(thread_word in name for thread_word in ['threads', 'classes']):
                categories['ПОТОКИ И КЛАССЫ'].append(f"  🔧 {name} (panel: {panel_id})")
            elif 'gc_' in name:
                categories['GARBAGE COLLECTION'].append(f"  🗑️  {name} (panel: {panel_id})")
            elif any(http_word in name for http_word in ['http', 'requests']):
                categories['HTTP МЕТРИКИ'].append(f"  🌐 {name} (panel: {panel_id})")
            elif 'pod' in name or 'kuber' in dashboard:
                categories['KUBERNETES МЕТРИКИ'].append(f"  ☸️  {name} (panel: {panel_id})")
            else:
                categories['SPRING BOOT МЕТРИКИ'].append(f"  📊 {name} (panel: {panel_id})")
        
        # Выводим метрики по категориям
        for category, items in categories.items():
            if items:
                logging.info(f"\n🏷️  {category}:")
                for item in items:
                    logging.info(item)
                    
    except Exception as e:
        logging.error(f"❌ Ошибка при чтении метрик: {str(e)}")

def main():
    """
    Основная функция демонстрации параметризации.
    """
    logging.info("🚀 Демонстрация параметризованного скрипта метрик Grafana")
    logging.info("="*80)
    
    config_file = "config.yml"
    metrics_file = "metrics_urls.yml"
    
    # Проверяем существование файлов
    if not Path(config_file).exists():
        logging.error(f"❌ Файл конфигурации не найден: {config_file}")
        return
    
    if not Path(metrics_file).exists():
        logging.error(f"❌ Файл метрик не найден: {metrics_file}")
        return
    
    # 1. Показываем доступные метрики
    logging.info("\n📋 Шаг 1: Просмотр доступных метрик")
    show_available_metrics(metrics_file)
    
    # 2. Обновляем временной диапазон (последние 2 часа)
    logging.info("\n⏰ Шаг 2: Обновление временного диапазона")
    update_config_time_range(config_file, hours_back=2)
    
    # 3. Активируем нужные сервисы
    logging.info("\n🔧 Шаг 3: Настройка активных сервисов")
    services_to_activate = [
        "dh-documents-service",    # Основной сервис документов
        "dh-files-service"         # Сервис файлов
        # "dh-auth-service",       # Можно раскомментировать при необходимости
        # "dh-notifications-service" # Можно раскомментировать при необходимости
    ]
    update_active_services(config_file, services_to_activate)
    
    # 4. Показываем, как запустить скрипт
    logging.info("\n🎯 Шаг 4: Запуск скрипта")
    logging.info("Теперь вы можете запустить основной скрипт:")
    logging.info("")
    logging.info("  # Скачать только метрики Grafana:")
    logging.info("  python -m src.main -grafana")
    logging.info("")
    logging.info("  # Скачать отчеты Gatling и метрики Grafana:")
    logging.info("  python -m src.main -gatling -grafana")
    logging.info("")
    
    # 5. Показываем структуру результатов
    logging.info("📁 Структура результатов:")
    logging.info("")
    logging.info("  reports/")
    logging.info("  ├── gatling/          # Отчеты Gatling (если включен -gatling)")
    logging.info("  └── metrics/          # Метрики Grafana")
    logging.info("      ├── dh-documents-service/  # Метрики для сервиса документов")
    logging.info("      │   ├── cpu_usage.png")
    logging.info("      │   ├── memory_allocate_promote.png")
    logging.info("      │   ├── gc_count.png")
    logging.info("      │   └── ... (все остальные метрики)")
    logging.info("      └── dh-files-service/      # Метрики для сервиса файлов")
    logging.info("          ├── cpu_usage.png")
    logging.info("          ├── requests_per_second.png")
    logging.info("          └── ... (все остальные метрики)")
    
    logging.info("\n✅ Конфигурация обновлена! Готово к запуску.")
    logging.info("="*80)

if __name__ == "__main__":
    main()
