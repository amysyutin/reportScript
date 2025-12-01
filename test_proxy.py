#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧪 ТЕСТОВЫЙ СКРИПТ ДЛЯ ПРОВЕРКИ ПРОКСИ

Этот скрипт можно легко удалить после тестирования.
Он проверяет:
1. Доступность SOCKS5 прокси
2. HTTP запросы через прокси
3. SSH подключение через прокси

Использование:
    python test_proxy.py
"""

import os
import sys
import logging
from pathlib import Path

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Добавляем src в путь
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def test_proxy_config():
    """Тест 1: Проверка загрузки конфигурации прокси"""
    logger.info("\n" + "="*80)
    logger.info("🧪 ТЕСТ 1: Загрузка конфигурации прокси")
    logger.info("="*80)
    
    try:
        from config import load_config
        cfg = load_config('config.yml')
        
        proxy_cfg = cfg.get('proxy', {})
        logger.info(f"✅ Конфигурация загружена:")
        logger.info(f"   PROXY_ENABLED: {proxy_cfg.get('enabled')}")
        logger.info(f"   PROXY_URL: {proxy_cfg.get('url')}")
        logger.info(f"   SSH_PROXY_HOST: {proxy_cfg.get('ssh_proxy_host')}")
        logger.info(f"   SSH_PROXY_PORT: {proxy_cfg.get('ssh_proxy_port')}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка при загрузке конфигурации: {str(e)}")
        return False


def test_proxy_availability():
    """Тест 2: Проверка доступности SOCKS5 прокси"""
    logger.info("\n" + "="*80)
    logger.info("🧪 ТЕСТ 2: Проверка доступности SOCKS5 прокси")
    logger.info("="*80)
    
    try:
        from config import load_config
        from proxy_utils import validate_and_prepare_proxy
        
        cfg = load_config('config.yml')
        
        if not cfg.get('proxy', {}).get('enabled'):
            logger.warning("⚠️  Прокси отключен в конфигурации (PROXY_ENABLED=false)")
            logger.info("   Пропускаем проверку доступности")
            return True
        
        proxies = validate_and_prepare_proxy(cfg)
        
        if proxies:
            logger.info(f"✅ Прокси настроен и доступен:")
            logger.info(f"   HTTP: {proxies.get('http')}")
            logger.info(f"   HTTPS: {proxies.get('https')}")
            return True
        else:
            logger.info("✅ Прокси отключен, используется прямое подключение")
            return True
            
    except Exception as e:
        logger.error(f"❌ Ошибка при проверке прокси: {str(e)}")
        logger.error(f"   Убедитесь, что SSH туннель запущен:")
        logger.error(f"   ssh -N -D 1081 lex@45.132.75.118")
        return False


def test_http_through_proxy():
    """Тест 3: HTTP запрос через прокси"""
    logger.info("\n" + "="*80)
    logger.info("🧪 ТЕСТ 3: HTTP запрос через прокси (тест на httpbin.org)")
    logger.info("="*80)
    
    try:
        import requests
        from config import load_config
        from proxy_utils import validate_and_prepare_proxy
        
        cfg = load_config('config.yml')
        proxies = validate_and_prepare_proxy(cfg)
        
        # Тестовый запрос к httpbin.org для проверки IP
        test_url = "http://httpbin.org/ip"
        
        logger.info(f"📡 Отправка запроса на {test_url}")
        
        if proxies:
            logger.info(f"   Через прокси: {proxies.get('http')}")
            response = requests.get(test_url, proxies=proxies, timeout=10)
        else:
            logger.info(f"   Без прокси (прямое подключение)")
            response = requests.get(test_url, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"✅ Запрос успешен!")
            logger.info(f"   Ваш внешний IP: {result.get('origin')}")
            
            if proxies:
                logger.info(f"   ℹ️  Это должен быть IP вашей VM (если прокси работает)")
            
            return True
        else:
            logger.error(f"❌ Неожиданный статус: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Ошибка при HTTP запросе: {str(e)}")
        return False


def test_ssh_connection():
    """Тест 4: SSH подключение через прокси"""
    logger.info("\n" + "="*80)
    logger.info("🧪 ТЕСТ 4: SSH подключение через прокси")
    logger.info("="*80)
    
    try:
        import paramiko
        from config import load_config
        
        cfg = load_config('config.yml')
        
        ssh_enabled = cfg.get('services', {}).get('ssh_service', False)
        if not ssh_enabled:
            logger.warning("⚠️  SSH сервис отключен (ssh_service: false)")
            logger.info("   Пропускаем проверку SSH подключения")
            return True
        
        proxy_cfg = cfg.get('proxy', {})
        ssh_config = cfg.get('ssh_config', {})
        
        host = ssh_config.get('host')
        username = ssh_config.get('username')
        
        if not host or not username:
            logger.warning("⚠️  SSH_HOST или SSH_USERNAME не заданы")
            logger.info("   Пропускаем проверку SSH подключения")
            return True
        
        logger.info(f"🔐 Попытка SSH подключения к {username}@{host}")
        
        if proxy_cfg.get('enabled'):
            logger.info(f"   Через прокси: {proxy_cfg.get('ssh_proxy_host')}:{proxy_cfg.get('ssh_proxy_port')}")
        else:
            logger.info(f"   Без прокси (прямое подключение)")
        
        # Для полного теста нужно будет вызвать ssh_download_last_report
        # Но здесь мы просто проверяем, что модуль импортируется
        from ssh_service import create_ssh_proxy_socket
        
        if proxy_cfg.get('enabled'):
            sock = create_ssh_proxy_socket(cfg)
            if sock:
                logger.info(f"✅ SOCKS5 сокет для SSH создан успешно")
                try:
                    sock.close()
                except:
                    pass
                return True
        else:
            logger.info(f"✅ Прокси отключен, SSH будет работать напрямую")
            return True
            
    except Exception as e:
        logger.error(f"❌ Ошибка при проверке SSH: {str(e)}")
        return False


def main():
    """Запуск всех тестов"""
    logger.info("\n")
    logger.info("🚀 " + "="*76 + " 🚀")
    logger.info("🚀 " + " "*20 + "ТЕСТИРОВАНИЕ ПРОКСИ КОНФИГУРАЦИИ" + " "*24 + "🚀")
    logger.info("🚀 " + "="*76 + " 🚀")
    
    tests = [
        ("Загрузка конфигурации", test_proxy_config),
        ("Доступность прокси", test_proxy_availability),
        ("HTTP через прокси", test_http_through_proxy),
        ("SSH через прокси", test_ssh_connection),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"💥 Критическая ошибка в тесте '{test_name}': {str(e)}")
            results.append((test_name, False))
    
    # Итоговая статистика
    logger.info("\n" + "="*80)
    logger.info("📊 ИТОГОВАЯ СТАТИСТИКА")
    logger.info("="*80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status} - {test_name}")
    
    logger.info("-"*80)
    logger.info(f"Пройдено тестов: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        logger.info("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Прокси настроен корректно.")
        logger.info("\n💡 Можно удалить этот тестовый файл:")
        logger.info(f"   rm {__file__}")
    else:
        logger.info("\n⚠️  НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОШЛИ")
        logger.info("\nРекомендации:")
        logger.info("1. Убедитесь, что SSH туннель запущен:")
        logger.info("   ssh -N -D 1081 lex@45.132.75.118")
        logger.info("2. Проверьте, что порт 1081 слушается:")
        logger.info("   lsof -i :1081")
        logger.info("3. Проверьте переменные в .env:")
        logger.info("   PROXY_ENABLED=true")
        logger.info("   PROXY_URL=socks5h://127.0.0.1:1081")
    
    logger.info("="*80 + "\n")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

