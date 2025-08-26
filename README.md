# Автоматизация скачивания отчётов Gatling и метрик Grafana

## Обзор

Проект автоматизирует скачивание отчётов производительности Gatling (по SSH) и метрик Grafana (через API-рендер в PNG). Конфигурация вынесена в YAML и поддерживает несколько сервисов, Gatling‑метрики, а также PostgreSQL‑метрики.

## Возможности

- 🚀 **Gatling отчёты по SSH**: загрузка последнего отчёта с удалённой машины
- 📊 **Скриншоты панелей Grafana**: рендер панелей в PNG по API
- ⚙️ **Гибкая конфигурация**: YAML + подстановка значений из окружения `${VAR}`
- 🔧 **Включение/выключение сервисов**: выборочно по списку в `services`
- 🕐 **Часовые пояса**: корректная конвертация временного диапазона в UTC
- 🗂️ **Структурированный вывод**: понятная иерархия директорий результатов
- 🧩 **Дополнительно**: Gatling‑метрики из отдельной Grafana и PostgreSQL‑метрики

## Структура проекта

```
reportsScript/
├── config.yml              # Основной конфиг (поддержка ${ENV})
├── metrics_urls.yml        # Конфигурация метрик Grafana
├── requirements.txt        # Зависимости Python
├── example_usage.py        # Примеры обновления конфига и запуска
├── grafana_enhanced.py     # Расширенные функции для Grafana
├── grafana_report.py       # Альтернативный загрузчик метрик
├── get_screenshots.sh      # Обёртка для запуска из shell
├── config_manager.py       # Утилиты работы с конфигом
├── test_url.py             # Тест генерации URL
├── src/
│   ├── main.py             # Точка входа CLI (-gatling, -grafana)
│   ├── config.py           # Загрузка config.yml, подстановка ENV
│   ├── config_loader.py    # Чтение metrics_urls.yml (валидируемая)
│   ├── ssh_service.py      # Скачивание последних Gatling отчётов по SSH
│   ├── grafana_service.py  # Скачивание метрик (App, Gatling, PostgreSQL)
│   └── utils.py            # Логирование, время, директории
└── tests/
    ├── test_config_loader.py
    ├── test_grafana_service.py
    └── test_utils.py
```

## Установка

1) Установите зависимости Python:
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

2) Заполните конфигурацию:
- Отредактируйте `config.yml`
- При необходимости обновите `metrics_urls.yml`
- (Опционально) создайте файл `.env` — значения из него автоматически подхватятся

Пример `.env`:
```bash
TIMEZONE=Europe/Moscow
REPORTS_BASE_DIR=/absolute/path/to/reports

SSH_HOST=1.2.3.4
SSH_USERNAME=tester
SSH_PASSWORD=secret
SSH_REMOTE_PATH=/home/tester/Gatling/.../target/gatling
SSH_LOCAL_PATH=./reports/gatling

GRAFANA_BASE_URL=https://grafana.example.com
GRAFANA_API_KEY=Bearer <token>
GRAFANA_LOCAL_PATH=./reports/metrics

GATLING_GRAFANA_BASE_URL=https://grafana-gatling.example.com
GATLING_GRAFANA_API_KEY=Bearer <token>
GATLING_GRAFANA_LOCAL_PATH=./reports/metrics/gatling_metrics

POSTGRESQL_GRAFANA_BASE_URL=https://grafana.example.com
POSTGRESQL_GRAFANA_API_KEY=Bearer <token>
POSTGRESQL_GRAFANA_LOCAL_PATH=./reports/metrics/postgresql_metrics
PG_VAR_DS_PROMETHEUS=PBFA97CFB590B2093
PG_VAR_NODE=$__all
PG_VAR_DATNAME=$__all
```

## Конфигурация

### Основной конфиг (`config.yml`)

Поддерживается подстановка переменных окружения: строки вида `${VARNAME}` будут заменены значениями из ENV или `.env`.

Ключевые разделы:
- `mainConfig`: `scenario`, `type_of_script`, `from`, `to`, `timezone`
- `main_folder`: базовая директория результатов
- `services`:
  - системные: `ssh_service`, `grafana_service`, `gatling_metrics_service`, `postgresql_metrics_service`
  - приложения: список сервисов (`dh-*-service: true/false`), для которых будут скачиваться метрики
- `ssh_config`: параметры SSH
- `grafana`: базовые параметры Grafana (основные метрики сервисов)
- `gatling_grafana`: отдельная Grafana для метрик Gatling (панели дашборда Gatling)
- `postgresql_grafana`: параметры для PostgreSQL‑метрик и их переменных

### Конфигурация метрик (`metrics_urls.yml`)

Список метрик с обязательными полями: `name`, `dashboard_uid`, `dashboard_name`, `panelId`, а также `orgId`, `width`, `height`, `vars`. Значения `PLACEHOLDER` в `vars` автоматически заменяются на имя текущего сервиса (или имя Gatling‑скрипта для Gatling‑метрик).

## Запуск

Из каталога `src/`:
```bash
cd src
python3 main.py -grafana          # Только метрики Grafana (включая Gatling/PG по флагам)
python3 main.py -gatling          # Только отчёты Gatling по SSH
python3 main.py -gatling -grafana # Всё вместе

python3 main.py --help            # Справка по флагам
```

Из корня проекта:
```bash
python3 src/main.py -grafana
```

## Что скачивается

### Метрики приложений (основная Grafana)
- CPU, Load Average, Threads, Classes
- Память: Eden, Survivor, Old Gen, Metaspace, Compressed Class Space, Allocation/Promotion
- GC: Count, Stop-the-world Duration
- HTTP: Codes, RPS, Duration
- Kubernetes: CPU by Pod, Memory by Pods

### Gatling‑метрики (вторая Grafana)
- Панели: `panel_3`, `panel_9`, `panel_1`, `panel_6`, `panel_7`, `panel_4`

### PostgreSQL‑метрики (основная Grafana)
- Метрики с префиксом `postgresql_` из `metrics_urls.yml` скачиваются отдельно при `postgresql_metrics_service: true`

## Структура результата

```
reports/
├── gatling/
│   └── <папка-отчёта-gatling>/
└── metrics/
    ├── gatling_metrics/
    │   └── <имя-скрипта>/
    │       ├── panel_3.png
    │       ├── panel_9.png
    │       └── ...
    ├── postgresql_metrics/
    │   ├── postgresql_connections.png
    │   └── ...
    └── <имя-сервиса>/
        ├── cpu_usage.png
        ├── requests_per_second.png
        └── ...
```

## Как добавить новый сервис

1) Включите его в `config.yml`:
```yaml
services:
  my-new-service: true
```
2) Запустите `-grafana` — скрипт автоматически подставит имя сервиса в `vars` (вместо `PLACEHOLDER`) и сохранит PNG панели в папку сервиса.

## Как добавить новую метрику

1) Возьмите UID дашборда, ID панели и необходимые переменные Grafana
2) Добавьте элемент в `metrics_urls.yml`:
```yaml
- name: "my_new_metric"
  dashboard_uid: "dashboard-uid"
  dashboard_name: "dashboard-name"
  orgId: 1
  panelId: 123
  width: 1000
  height: 500
  vars:
    var-application: "PLACEHOLDER"
```

## Безопасность секретов

- Никогда не коммитьте реальные ключи API/пароли. Используйте `.env` и `${VARNAME}` в `config.yml`
- Файл `.gitignore` уже исключает `.env` и ключи
- Для GitHub Push Protection используйте примерные файлы и переменные окружения

## Логирование и помощь

- Логи пишутся в `app.log` и в консоль
- Справка: `python3 src/main.py --help`
- Просмотр логов: `tail -f app.log`

## Требования

- Python 3.8+
- Доступ к SSH‑серверу (для Gatling)
- Доступ к Grafana (API key)
- Достаточно места на диске

## Зависимости

См. `requirements.txt`:
- `paramiko` — SSH клиент
- `requests` — HTTP клиент
- `PyYAML` — YAML парсер
- `python-dateutil`, `python-dotenv`
