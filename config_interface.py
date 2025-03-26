import os
from datetime import datetime
import configparser
from config_manager import ConfigManager

def format_date_for_grafana(date_str: str) -> str:
    """Преобразует дату из формата YYYY-MM-DD HH:MM:SS в формат для Grafana."""
    dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    return dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")

def update_config(test_name: str, start_time: str, end_time: str):
    """Обновляет конфигурационный файл с новыми данными."""
    config = configparser.ConfigParser()
    config.read('config.ini')
    
    # Обновляем временной диапазон
    config['Grafana.TimeRange']['from'] = format_date_for_grafana(start_time)
    config['Grafana.TimeRange']['to'] = format_date_for_grafana(end_time)
    
    # Сохраняем название теста
    config['Test']['name'] = test_name
    
    # Сохраняем изменения
    with open('config.ini', 'w') as f:
        config.write(f)
    
    print("\nКонфигурация успешно обновлена!")
    print(f"Название теста: {test_name}")
    print(f"Время начала: {start_time}")
    print(f"Время окончания: {end_time}")

def main():
    print("\n=== Конфигурация теста ===")
    print("Введите данные в указанном формате:")
    
    # Получаем название теста
    while True:
        test_name = input("\nНазвание теста (например, upload): ").strip()
        if test_name:
            break
        print("Название теста не может быть пустым!")
    
    # Получаем время начала
    while True:
        start_time = input("\nВремя начала теста (формат: YYYY-MM-DD HH:MM:SS): ").strip()
        try:
            datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
            break
        except ValueError:
            print("Неверный формат даты! Используйте формат: YYYY-MM-DD HH:MM:SS")
    
    # Получаем время окончания
    while True:
        end_time = input("\nВремя окончания теста (формат: YYYY-MM-DD HH:MM:SS): ").strip()
        try:
            datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
            break
        except ValueError:
            print("Неверный формат даты! Используйте формат: YYYY-MM-DD HH:MM:SS")
    
    # Обновляем конфигурацию
    update_config(test_name, start_time, end_time)

if __name__ == "__main__":
    main() 