# Настройка загрузки Gatling‑метрик

## Обзор

Функциональность позволяет скачивать панели из Gatling‑дашборда (в отдельной Grafana) как PNG. Inteграция встроена в общий флаг `-grafana` и использует единый временной диапазон.

## Шаги конфигурации

### 1) Включите сервис Gatling‑метрик

В `config.yml`:
```yaml
services:
  gatling_metrics_service: true
```

### 2) Укажите подключение ко второй Grafana

В `config.yml` (переменные можно задать через `.env`):
```yaml
gatling_grafana:
  local_path: "${GATLING_GRAFANA_LOCAL_PATH}"
  base_url: "${GATLING_GRAFANA_BASE_URL}"
  api_key: "${GATLING_GRAFANA_API_KEY}"
  timezone: "${TIMEZONE}"
  gatling_metrics_config: "gatling_metrics_urls.yml"
  gatling_scripts:
    Attribute_Search_1: true
    Attribute_Search_2: true
    # ... включайте/выключайте нужные скрипты
```

### 3) Проверьте конфигурацию метрик

Файл `gatling_metrics_urls.yml` содержит преднастроенные панели:
`panel_3`, `panel_9`, `panel_1`, `panel_6`, `panel_7`, `panel_4`.

В `vars` используется значение `PLACEHOLDER` — оно автоматически заменяется на имя скрипта из `gatling_scripts`.

## Запуск

```bash
python3 src/main.py -grafana          # Загрузит и обычные метрики, и Gatling (если включено)
python3 src/main.py -gatling -grafana # Плюс скачает SSH-отчёт Gatling
```

## Где искать результат

```
reports/
└── metrics/
    └── gatling_metrics/
        └── <имя-скрипта>/
            ├── panel_3.png
            ├── panel_9.png
            └── ...
```

## Кастомизация

### Добавить новые панели

1) Найдите `panelId` в URL Grafana (`viewPanel=`) и `dashboard_uid`
2) Добавьте запись в `gatling_metrics_urls.yml`:
```yaml
- name: "panel_5"
  dashboard_uid: "de9jk1ju5vmdcb"
  dashboard_name: "gatling-metrics"
  orgId: 1
  panelId: 5
  width: 1000
  height: 500
  vars:
    var-DS_PROMETHEUS: "PBFA97CFB590B2093"
    var-group: "$__all"
    var-node_name: "$__all"
    var-script_name: "PLACEHOLDER"   # Будет заменён на имя Gatling-скрипта
    timeout: 60
```

### Динамически менять список скриптов

Включайте/выключайте элементы в `gatling_grafana.gatling_scripts`.

## Частые проблемы

1) Ничего не скачивается
- Проверьте `services.gatling_metrics_service: true`
- Проверьте доступность `GATLING_GRAFANA_BASE_URL`
- Проверьте токен `GATLING_GRAFANA_API_KEY`

2) Не те данные по скрипту
- Убедитесь, что имя скрипта в `gatling_scripts` совпадает с тем, что используется на дашборде

3) Ошибка панели
- Проверьте `panelId` и `dashboard_uid` в `gatling_metrics_urls.yml`

## Отладка

```bash
tail -f app.log
```
В логах ищите блоки со словом "Gatling" — там виден прогресс и возможные ошибки.

## Технические детали

- UID дашборда: `de9jk1ju5vmdcb`
- Название: `gatling-metrics`
- Подстановка переменных: `PLACEHOLDER` → имя скрипта
- Временной диапазон: общий из `mainConfig` → конвертация в UTC
- Формат: PNG (напр., 1000x500)

## Интеграция с общим процессом

- Флаг `-grafana` запускает загрузку обычных метрик сервисов, Gatling‑метрик и PostgreSQL‑метрик (если соответствующие сервисы включены)
- Всё логируется в `app.log`
