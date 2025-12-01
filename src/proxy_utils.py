#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Утилиты для работы с SOCKS5 прокси.

Модуль предоставляет функции для:
- Проверки доступности прокси
- Настройки proxies для requests
- Логирования использования прокси
"""

import logging
import socket
import socks
from typing import Optional, Dict

logger = logging.getLogger(__name__)


def check_proxy_availability(proxy_host: str, proxy_port: int, timeout: int = 5) -> bool:
    """
    Проверяет доступность SOCKS5 прокси.
    
    Args:
        proxy_host (str): Хост прокси (IP или hostname)
        proxy_port (int): Порт прокси
        timeout (int): Таймаут подключения в секундах
        
    Returns:
        bool: True если прокси доступен, False если нет
    """
    try:
        # Создаем SOCKS5 сокет
        test_socket = socks.socksocket(socket.AF_INET, socket.SOCK_STREAM)
        test_socket.set_proxy(
            proxy_type=socks.SOCKS5,
            addr=proxy_host,
            port=proxy_port
        )
        test_socket.settimeout(timeout)
        
        # Пытаемся подключиться к любому публичному DNS (Google DNS)
        # Это проверит, что прокси работает и может резолвить/подключаться
        test_socket.connect(('8.8.8.8', 53))
        test_socket.close()
        
        logger.info(f"✅ Прокси {proxy_host}:{proxy_port} доступен")
        return True
        
    except Exception as e:
        logger.error(f"❌ Прокси {proxy_host}:{proxy_port} недоступен: {str(e)}")
        return False


def get_proxies_dict(proxy_url: str) -> Dict[str, str]:
    """
    Формирует словарь proxies для библиотеки requests.
    
    Args:
        proxy_url (str): URL прокси (например, socks5h://45.132.75.118:1081)
        
    Returns:
        dict: Словарь вида {'http': '...', 'https': '...'}
    """
    return {
        'http': proxy_url,
        'https': proxy_url,
    }


def validate_and_prepare_proxy(cfg: dict) -> Optional[Dict[str, str]]:
    """
    Валидирует конфигурацию прокси и возвращает готовый словарь для requests.
    
    Args:
        cfg (dict): Конфигурация из config.yml
        
    Returns:
        dict или None: Словарь proxies если прокси включен, None если выключен
        
    Raises:
        ValueError: Если конфигурация прокси некорректна
        RuntimeError: Если прокси включен, но недоступен
    """
    proxy_cfg = cfg.get('proxy', {})
    
    # Если прокси выключен - возвращаем None
    if not proxy_cfg.get('enabled'):
        logger.info("🌐 Прокси отключен, используется прямое подключение")
        return None
    
    proxy_url = proxy_cfg.get('url')
    if not proxy_url:
        raise ValueError("PROXY_ENABLED=true, но PROXY_URL не задан")
    
    logger.info(f"🔒 Использование прокси: {proxy_url}")
    
    # Проверяем доступность прокси
    # Парсим host:port из URL
    try:
        # Извлекаем host и port из URL вида socks5h://host:port
        if '://' in proxy_url:
            proto_and_host = proxy_url.split('://', 1)[1]
        else:
            proto_and_host = proxy_url
            
        if ':' in proto_and_host:
            proxy_host, proxy_port_str = proto_and_host.rsplit(':', 1)
            proxy_port = int(proxy_port_str)
        else:
            raise ValueError(f"Некорректный формат PROXY_URL: {proxy_url}")
        
        # Проверяем доступность
        check_timeout = proxy_cfg.get('check_timeout', 5)
        logger.info(f"🔍 Проверка доступности прокси {proxy_host}:{proxy_port}...")
        
        if not check_proxy_availability(proxy_host, proxy_port, timeout=check_timeout):
            raise RuntimeError(
                f"Прокси {proxy_host}:{proxy_port} недоступен. "
                f"Убедитесь, что SSH туннель запущен: ssh -D {proxy_port} user@{proxy_host}"
            )
        
        logger.info(f"✅ Прокси проверен и готов к использованию")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при проверке прокси: {str(e)}")
        raise
    
    # Возвращаем словарь для requests
    return get_proxies_dict(proxy_url)