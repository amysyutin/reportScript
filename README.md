# Скрипт для скачивания отчетов Gatling и метрик Grafana

## Описание
Скрипт предназначен для автоматизации процесса скачивания отчетов тестирования производительности (Gatling) и метрик (Grafana) с удаленного сервера. 

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

## Использование

### Установка зависимостей
```bash
pip install -r requirements.txt
```

### Запуск скрипта
```bash
python src/main.py
```

### Аргументы командной строки
- `-gatling` - скачать только отчет Gatling
- `-grafana` - скачать только метрики Grafana
- `-all` - скачать и отчет, и метрики (по умолчанию)

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