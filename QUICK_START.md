# Краткий старт

## TL;DR — как запустить

### 1) Установите зависимости
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Настройте `.env`
Создайте файл `.env` с доступами:
```bash
TIMEZONE=Europe/Moscow

# SSH (для скачивания Gatling отчётов)
SSH_HOST=1.2.3.4
SSH_USERNAME=tester
SSH_PASSWORD=secret
SSH_REMOTE_PATH=/path/to/gatling/results

# Grafana (для скачивания метрик)
GRAFANA_BASE_URL=https://grafana.example.com
GRAFANA_API_KEY=Bearer <your-token>

# Gatling Grafana (опционально)
GATLING_GRAFANA_BASE_URL=https://grafana-gatling.example.com
GATLING_GRAFANA_API_KEY=Bearer <your-token>
```

### 3) Настройте `config.yml`
```yaml
mainConfig:
  scenario: "my_test"
  from: "2025-01-01 10:00:00"
  to: "2025-01-01 12:00:00"

services:
  ssh_service: true              # Gatling отчёты
  grafana_service: true          # Метрики сервисов
  gatling_metrics_service: true  # Gatling метрики
  
  # Включите нужные сервисы
  dh-documents-service: true
  dh-files-service: false
  
  # Включите нужные Gatling скрипты
  gatling_scripts:
    Get_Document: true
    Upload_File: false
```

### 4) Запустите скрипт
```bash
# Из корня проекта (рекомендуется)
python -m src.main -grafana          # Только метрики Grafana
python -m src.main -gatling          # Только отчёты Gatling
python -m src.main -gatling -grafana # Всё вместе

# Справка
python -m src.main --help
```

### 5) Проверьте результаты
```
reports/
├── gatling/                    # Отчёты Gatling
│   └── <report-folder>/
├── metrics/
│   ├── gatling_metrics/        # Gatling метрики
│   │   └── Get_Document/
│   └── dh-documents-service/   # Метрики сервисов
│       ├── cpu_usage.png
│       └── ...
```

Логи: `app.log`

---

## Важные файлы

| Файл | Описание |
|------|----------|
| `config.yml` | Основной конфиг (время, сервисы, флаги) |
| `metrics_urls.yml` | Описание метрик для сервисов |
| `gatling_metrics_urls.yml` | Описание Gatling метрик |
| `.env` | Секреты (SSH, Grafana API) |

---

## Быстрые команды

```bash
# Скачать только метрики Grafana
python -m src.main -grafana

# Скачать только Gatling отчёты
python -m src.main -gatling

# Скачать всё
python -m src.main -grafana -gatling

# Посмотреть логи
tail -f app.log
```

---

## Помощь

- 📖 Полное руководство — [README.md](README.md)
- 🔧 Настройка Gatling метрик — [GATLING_METRICS_SETUP.md](GATLING_METRICS_SETUP.md)
- 📋 Логи — `app.log`
- ❓ Справка CLI — `python -m src.main --help`
