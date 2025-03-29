# Report Script

Скрипт для автоматизации обработки отчетов Gatling и сбора метрик из Grafana.

## Функциональность

- Скачивание отчетов Gatling
- Сбор метрик из Grafana
- Автоматическое создание структуры директорий
- Поддержка SSL-сертификатов
- Конфигурируемые параметры через config.ini и test_config.ini

## Установка

1. Клонируйте репозиторий:
```bash
git clone git@github.com:amysyutin/reportScript.git
cd reportScript
```

2. Создайте виртуальное окружение и установите зависимости:
```bash
python3 -m venv venv
source venv/bin/activate  # для Linux/Mac
# или
venv\Scripts\activate  # для Windows
pip install -r requirements.txt
```

3. Настройте файлы конфигурации:
   - `config.ini` - основные настройки (API ключи, пути и т.д.)
   - `test_config.ini` - настройки временного диапазона для тестов
   - `metric_urls.txt` - URL метрик Grafana

## Использование

### Скачивание отчетов Gatling
```bash
python3 gatling_reports.py -gatling -dir /путь/к/директории/отчета
```

### Скачивание метрик Grafana
```bash
python3 grafana_metrics.py -grafana -dir /путь/к/директории/отчета
```

## Структура проекта

```
reportScript/
├── config.ini
├── test_config.ini
├── gatling_reports.py
├── grafana_metrics.py
├── metric_urls.txt
├── requirements.txt
└── README.md
```

## Требования

- Python 3.8+
- Доступ к Grafana API
- Доступ к отчетам Gatling 