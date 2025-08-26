# Краткий старт

## TL;DR — как запустить

### 1) Установите зависимости
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Настройте конфиг
Отредактируйте `config.yml`:
- Укажите временной диапазон (`mainConfig.from` / `mainConfig.to`)
- Включите нужные сервисы в `services`
- Заполните доступы SSH и Grafana

Опционально создайте `.env` — значения `${VAR}` из `config.yml` подставятся автоматически.

### 3) Запустите скрипт
```bash
# Из каталога src/
cd src
python3 main.py -grafana          # Только метрики Grafana
python3 main.py -gatling          # Только отчёты Gatling
python3 main.py -gatling -grafana # Всё вместе

# Или из корня проекта
python3 src/main.py -grafana
```

### 4) Проверьте результаты
- Gatling: `./reports/gatling/`
- Метрики Grafana: `./reports/metrics/<service>/`
- Логи: `app.log`

## Важные файлы

- `config.yml` — основной конфиг (время, сервисы, доступы)
- `metrics_urls.yml` — описание метрик Grafana

## Альтернативы

### Примеры настройки конфигурации
```bash
python3 example_usage.py
```

### Shell-обёртка
```bash
./get_screenshots.sh download     # Скачать всё
./get_screenshots.sh test         # Проверить подключение
./get_screenshots.sh list         # Показать список метрик
```

### Расширенные возможности Grafana
```bash
python3 grafana_enhanced.py --test-connection
python3 grafana_enhanced.py --download-all
```

## Помощь

- Полное руководство — см. [README.md](README.md)
- Логи — `app.log`
- Справка по CLI — `python3 src/main.py --help`
