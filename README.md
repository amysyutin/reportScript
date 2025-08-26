# Report Script

Скрипт для автоматизации обработки отчетов Gatling и сбора метрик из Grafana.

## Функциональность

- Скачивание отчетов Gatling
- Сбор метрик из Grafana
- Автоматическое создание структуры директорий
- Поддержка SSL-сертификатов
- Конфигурируемые параметры через config.json

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

3. Создайте файл `config.json` на основе `config.json.example` и настройте параметры:
```json
{
    "grafana_api_key": "ваш_ключ_api",
    "time_range": {
        "from": "2025-03-25T22:28:26.000Z",
        "to": "2025-03-25T23:10:23.000Z"
    }
}
```

4. Создайте файл `metric_urls.txt` с URL метрик Grafana.

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
├── config.json.example
├── config.json
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