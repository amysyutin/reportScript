# Grafana Screenshot Automation 📊

## Status: ✅ WORKING PERFECTLY!

Your Grafana API automation is **fully functional**! No more manual screenshots needed.

## 🎯 What's Working

✅ **Grafana API Integration** - Successfully downloading screenshots via API  
✅ **Authentication** - Bearer token authentication working  
✅ **Multiple Dashboards** - Supporting both "spring-boot-2x" and "kuber-analitics"  
✅ **5 Metrics Automated** - All your performance metrics captured automatically  
✅ **Time Range Handling** - Proper timezone conversion (Europe/Moscow)  
✅ **File Organization** - Clean folder structure with timestamps  
✅ **Error Handling** - Robust retry logic and validation

## Структура проекта
```
reportsScript/
├── config.yml              # Основной конфиг в YAML
├── metrics_urls.yml       # Конфиг метрик Grafana
├── requirements.txt       # Зависимости проекта
└── src/                  # Исходный код
    ├── config.py         # Работа с конфигурацией
    ├── ssh_service.py    # Работа с SSH
    ├── grafana_service.py # Работа с Grafana
    ├── utils.py          # Вспомогательные функции
    └── main.py           # Точка входа
```

## Конфигурация

### config.yml
```yaml
ssh:
  hostname: "172.19.93.113"
  username: "tester"
  port: 22
  remote_report_dir: "/home/tester/Gatling/dh-nt-gatling/target/gatling"

grafana:
  api_key: "glc_eyJvIjoiYWRtaW4iLCJuIjoiYWRtaW4iLCJpZCI6MSwiYXV0aCI6ImFkbWluIn0="
  base_url: "http://172.19.93.113:3000"
  timezone: "Europe/Moscow"

local:
  base_dir: "/Users/alex/PerformanceTesting/LANIT/gatlingScriptResults"
  report_dir: "/Users/alex/PerformanceTesting/LANIT/gatlingScript/reportsScript"
```

### metrics_urls.yml
```yaml
metrics:
  - name: "k8s_panel_5"
    url: "/render/d-solo/..."
  - name: "k8s_panel_7"
    url: "/render/d-solo/..."
  # ... другие метрики
```

## Логика работы

### 1. Скачивание отчета Gatling
1. Подключение к серверу по SSH
2. Получение имени последнего отчета из файла `lastRun.txt`
3. Скачивание отчета в локальную директорию
4. Переименование отчета в формате `Gatling_Report_{test_name}_{date}_{time}`
5. Удаление отчета на сервере после успешного скачивания

### 2. Скачивание метрик Grafana
1. Получение списка метрик из `metrics_urls.yml`
2. Формирование URL для каждой метрики с учетом:
   - Временного диапазона
   - Часового пояса
   - API ключа
3. Скачивание каждой метрики в формате PNG
4. Сохранение в директорию с отчетами

## 🚀 Quick Start

### 1. Original Working Method
```bash
# Download all screenshots (your current working method)
python3 src/main.py -grafana
```

### 2. Enhanced Automation (NEW!)

#### Simple wrapper script:
```bash
# Download all screenshots (default)
./get_screenshots.sh

# Test connection
./get_screenshots.sh test

# List available metrics
./get_screenshots.sh list

# Test single metric
./get_screenshots.sh single cpu_usage
```

#### Advanced Python script:
```bash
# Test Grafana API connection
python3 grafana_enhanced.py --test-connection

# Download all with progress tracking
python3 grafana_enhanced.py --download-all

# Test individual metric
python3 grafana_enhanced.py --test-metric cpu_usage

# List all metrics
python3 grafana_enhanced.py --list-metrics
```

### 3. Installation
```bash
pip install -r requirements.txt
```

## 📋 Available Metrics

Your automation currently captures:
1. **cpu_usage** - Spring Boot 2x dashboard
2. **load_average** - Spring Boot 2x dashboard
3. **cpu_by_pod** - Kuber Analytics dashboard
4. **memory_usage_pod** - Kuber Analytics dashboard
5. **throttling** - Kuber Analytics dashboard

## Логирование
- Все операции логируются в консоль
- Уровни логирования:
  - INFO - основные операции
  - WARNING - предупреждения
  - ERROR - ошибки
  - CRITICAL - критические ошибки

## Обработка ошибок
- Проверка наличия конфигурационных файлов
- Проверка SSH-подключения
- Проверка успешности скачивания файлов
- Проверка успешности удаления на сервере
- Обработка ошибок сети и API Grafana

## Результаты
1. Отчет Gatling:
   - Сохраняется в директорию `local.base_dir`
   - Имя файла: `Gatling_Report_{test_name}_{date}_{time}`

2. Метрики Grafana:
   - Сохраняются в директорию `local.report_dir`
   - Имена файлов: `{metric_name}.png`

## Требования
- Python 3.6+
- Доступ к серверу по SSH
- API ключ Grafana
- Достаточно места на диске для сохранения отчетов 