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
- 🧩 **Gatling‑метрики**: метрики из отдельной Grafana для каждого скрипта
- 🐘 **PostgreSQL‑метрики**: метрики базы данных

## Структура проекта

```
reportsScript/
├── config.yml                 # Основной конфиг (поддержка ${ENV})
├── metrics_urls.yml           # Конфигурация метрик Grafana для сервисов
├── gatling_metrics_urls.yml   # Конфигурация метрик Gatling
├── requirements.txt           # Зависимости Python
├── example_usage.py           # Примеры обновления конфига и запуска
├── grafana_enhanced.py        # Расширенные функции для Grafana
├── get_screenshots.sh         # Обёртка для запуска из shell
├── QUICK_START.md             # Быстрый старт
├── GATLING_METRICS_SETUP.md   # Настройка Gatling метрик
├── src/
│   ├── main.py                # Точка входа CLI (-gatling, -grafana)
│   ├── config.py              # Загрузка config.yml, подстановка ENV
│   ├── config_loader.py       # Чтение metrics_urls.yml (валидируемая)
│   ├── ssh_service.py         # Скачивание Gatling отчётов по SSH/SCP
│   ├── grafana_service.py     # Скачивание метрик (App, Gatling, PostgreSQL)
│   └── utils.py               # Логирование, время, директории
└── tests/
    ├── test_config_loader.py
    ├── test_grafana_service.py
    ├── test_url.py
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
- При необходимости обновите `metrics_urls.yml` и `gatling_metrics_urls.yml`
- (Опционально) создайте файл `.env` — значения из него автоматически подхватятся

Пример `.env`:
```bash
TIMEZONE=Europe/Moscow
REPORTS_BASE_DIR=/absolute/path/to/reports

# SSH для скачивания Gatling отчётов
SSH_HOST=1.2.3.4
SSH_USERNAME=tester
SSH_PASSWORD=secret
SSH_REMOTE_PATH=/home/tester/Gatling/.../target/gatling
SSH_LOCAL_PATH=./reports/gatling

# Основная Grafana (метрики сервисов)
GRAFANA_BASE_URL=https://grafana.example.com
GRAFANA_API_KEY=Bearer <token>
GRAFANA_LOCAL_PATH=./reports/metrics

# Gatling Grafana (метрики нагрузки)
GATLING_GRAFANA_BASE_URL=https://grafana-gatling.example.com
GATLING_GRAFANA_API_KEY=Bearer <token>
GATLING_GRAFANA_LOCAL_PATH=./reports/metrics/gatling_metrics

# PostgreSQL Grafana (метрики БД)
POSTGRESQL_GRAFANA_BASE_URL=https://grafana.example.com
POSTGRESQL_GRAFANA_API_KEY=Bearer <token>
POSTGRESQL_GRAFANA_LOCAL_PATH=./reports/metrics/postgresql_metrics
```

## Конфигурация

### Основной конфиг (`config.yml`)

Поддерживается подстановка переменных окружения: строки вида `${VARNAME}` будут заменены значениями из ENV или `.env`.

Ключевые разделы:

```yaml
mainConfig:
  scenario: "test_scenario"      # Название сценария (для имени папки)
  type_of_script: "scalability"  # Тип теста
  from: "2025-01-01 10:00:00"    # Начало временного диапазона
  to: "2025-01-01 12:00:00"      # Конец временного диапазона

services:
  # Системные сервисы
  ssh_service: true              # Скачивание отчётов Gatling по SSH
  grafana_service: true          # Скачивание метрик из Grafana
  gatling_metrics_service: true  # Скачивание Gatling метрик
  postgresql_metrics_service: false
  
  # Сервисы приложений (для которых скачиваются метрики)
  dh-documents-service: true
  dh-files-service: false
  # ... другие сервисы
  
  # Gatling скрипты (для которых скачиваются Gatling метрики)
  gatling_scripts:
    Get_Document: true
    Upload_File: false
    # ... другие скрипты
```

### Конфигурация метрик (`metrics_urls.yml`)

Список метрик с обязательными полями: `name`, `dashboard_uid`, `dashboard_name`, `panelId`, а также `orgId`, `width`, `height`, `vars`. 

Значение `PLACEHOLDER` в `vars` автоматически заменяется на имя текущего сервиса.

```yaml
metrics:
  - name: "cpu_usage"
    dashboard_uid: "spring-boot-2x"
    dashboard_name: "spring-boot-2x"
    orgId: 1
    panelId: 95
    width: 1000
    height: 500
    vars:
      var-application: "PLACEHOLDER"
      var-namespace: "astra-stress"
```

### Конфигурация Gatling метрик (`gatling_metrics_urls.yml`)

Аналогично `metrics_urls.yml`, но `PLACEHOLDER` заменяется на имя Gatling скрипта.

## Запуск

Из корня проекта:
```bash
# Только метрики Grafana (включая Gatling/PostgreSQL по флагам в config.yml)
python -m src.main -grafana

# Только отчёты Gatling по SSH
python -m src.main -gatling

# Всё вместе
python -m src.main -gatling -grafana

# Справка
python -m src.main --help
```

Или из каталога `src/`:
```bash
cd src
python main.py -grafana -gatling
```

## Что скачивается

### Метрики приложений (основная Grafana)
- CPU, Load Average, Threads, Classes
- Память: Eden, Survivor, Old Gen, Metaspace, Compressed Class Space, Allocation/Promotion
- GC: Count, Stop-the-world Duration
- HTTP: Codes, RPS, Duration
- Kubernetes: CPU by Pod, Memory by Pods

### Gatling‑метрики (Gatling Grafana)
- Панели с метриками нагрузки для каждого включённого скрипта
- Сохраняются в `metrics/gatling_metrics/<имя-скрипта>/`

### PostgreSQL‑метрики
- Метрики с префиксом `postgresql_` из `metrics_urls.yml`
- Скачиваются при `postgresql_metrics_service: true`

## Структура результата

```
<REPORTS_BASE_DIR>/
└── <from> <scenario> <type_of_script>/
    ├── gatling/
    │   └── <папка-отчёта-gatling>/
    │       ├── index.html
    │       └── ...
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
            ├── memory_allocate_promote.png
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

## Как добавить новый Gatling скрипт

1) Добавьте скрипт в `config.yml`:
```yaml
services:
  gatling_scripts:
    My_New_Script: true
```
2) Запустите `-grafana` — скрипт скачает метрики для этого скрипта.

## Безопасность секретов

- Никогда не коммитьте реальные ключи API/пароли. Используйте `.env` и `${VARNAME}` в `config.yml`
- Файл `.gitignore` уже исключает `.env` и ключи
- Для GitHub Push Protection используйте примерные файлы и переменные окружения

## Логирование

- Логи пишутся в `app.log` и в консоль
- Справка: `python -m src.main --help`
- Просмотр логов: `tail -f app.log`

## Требования

- Python 3.8+
- Доступ к SSH‑серверу (для Gatling отчётов)
- Доступ к Grafana (API key с правами на рендер)
- Достаточно места на диске

## Зависимости

См. `requirements.txt`:
- `paramiko` — SSH клиент
- `requests` — HTTP клиент
- `PyYAML` — YAML парсер
- `python-dateutil` — работа с датами
- `python-dotenv` — загрузка .env файлов
