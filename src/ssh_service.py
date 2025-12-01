import paramiko
import os
import shutil
import logging
import subprocess
from pathlib import Path
import socks 

def ssh_download_last_report(cfg, main_folder_path):
    """
    Функция для скачивания последнего отчета Gatling с сервера.
    
    Args:
        cfg (dict): Конфигурационный словарь с параметрами SSH
        main_folder_path (str): Путь к основной папке для сохранения отчета
        
    Returns:
        str: Путь к скачанному отчету или None, если возникла ошибка
    """
    ssh = None
    proxy_sock = None
    try:
        # Создаем базовую директорию для отчетов Gatling
        local_path = os.path.join(main_folder_path, "gatling")
        os.makedirs(local_path, exist_ok=True)
        logging.info(f"Создана базовая директория: {local_path}")
        
        # Устанавливаем SSH-соединение (ключ или пароль, порт по умолчанию 22)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        host = cfg['ssh_config'].get('host')
        username = cfg['ssh_config'].get('username')
        password = cfg['ssh_config'].get('password')

        # Валидация обязательных полей
        if not host or str(host).strip() in {"", "${SSH_HOST}"}:
            logging.error("SSH_HOST не задан. Укажите SSH_HOST в .env или config.yml")
            return None
        if not username or str(username).strip() in {"", "${SSH_USERNAME}"}:
            logging.error("SSH_USERNAME не задан. Укажите SSH_USERNAME в .env или config.yml")
            return None
        port = int(cfg['ssh_config'].get('port', 22) or 22)
        key_path_str = cfg['ssh_config'].get('key_path')

        pkey = None
        if key_path_str:
            expanded_key_path = os.path.expanduser(str(key_path_str))
            if os.path.exists(expanded_key_path):
                try:
                    pkey = paramiko.RSAKey.from_private_key_file(expanded_key_path)
                except Exception:
                    # Попробуем Ed25519/EC ключи
                    try:
                        pkey = paramiko.Ed25519Key.from_private_key_file(expanded_key_path)
                    except Exception:
                        pkey = None

        # ========== НАСТРОЙКА ПРОКСИ ДЛЯ SSH ==========
        proxy_cfg = cfg.get('proxy', {})
        if proxy_cfg.get('enabled'):
            proxy_sock = create_ssh_proxy_socket(cfg)
        else:
            proxy_sock = None
            logging.info("🌐 SSH подключение без прокси (прямое)")
        # ==============================================                        

        # ========== SSH ПОДКЛЮЧЕНИЕ ==========
        ssh.connect(
            hostname=host,
            port=port,
            username=username,
            pkey=pkey,
            password=None if pkey else password,
            sock=proxy_sock,  # Добавили параметр sock для прокси
            look_for_keys=False,
            allow_agent=False,
        )
        # =====================================

        logging.info(f"✅ SSH подключение установлено к {host}:{port}")
        
        # Получаем имя последнего отчета из файла lastRun.txt
        stdin, stdout, stderr = ssh.exec_command(f"cat {cfg['ssh_config']['remote_path']}/lastRun.txt")
        report_name = stdout.read().decode().strip()
        error = stderr.read().decode()
        
        if error:
            logging.error(f"Ошибка при чтении lastRun.txt: {error}")
            return None
            
        if not report_name:
            logging.warning("Имя отчета не найдено в lastRun.txt")
            return None
            
        # Формируем пути для удаленного и локального отчета
        remote_path = os.path.join(cfg['ssh_config']['remote_path'], report_name)
        local_report_path = os.path.join(local_path, report_name)
        
        logging.info(f"Попытка скачать отчет: {remote_path} -> {local_report_path}")
        
        # Проверяем существование удаленной директории через SSH
        stdin, stdout, stderr = ssh.exec_command(f"test -d {remote_path} && echo 'exists'")
        if not stdout.read().decode().strip():
            logging.warning(f"Отчет не найден на сервере: {remote_path}")
            return None
            
        # Удаляем локальную директорию отчета, если она существует
        if os.path.exists(local_report_path):
            if os.path.isdir(local_report_path):
                shutil.rmtree(local_report_path)
            else:
                os.remove(local_report_path)
            logging.info(f"Удалена существующая директория/файл отчета: {local_report_path}")
            
     # ========== СКАЧИВАНИЕ ЧЕРЕЗ SFTP (вместо SCP) ==========
        # Используем SFTP вместо SCP, так как SCP работает через subprocess
        # и не может использовать уже установленное SSH соединение через прокси
        
        logging.info(f"📥 Начинаем скачивание через SFTP...")
        sftp = ssh.open_sftp()
        
        # Рекурсивно копируем директорию
        def sftp_get_recursive(sftp_client, remote_dir, local_dir):
            """Рекурсивное скачивание директории через SFTP."""
            os.makedirs(local_dir, exist_ok=True)
            
            for item in sftp_client.listdir_attr(remote_dir):
                remote_item_path = os.path.join(remote_dir, item.filename)
                local_item_path = os.path.join(local_dir, item.filename)
                
                if item.st_mode & 0o040000:  # Это директория
                    sftp_get_recursive(sftp_client, remote_item_path, local_item_path)
                else:  # Это файл
                    logging.debug(f"  Скачиваем файл: {item.filename}")
                    sftp_client.get(remote_item_path, local_item_path)
                    
        sftp_get_recursive(sftp, remote_path, local_report_path)
        sftp.close()
        
        logging.info(f"✅ Отчет успешно скачан через SFTP: {local_report_path}")
        # =========================================================
        
        # Удаляем отчет с сервера после успешного скачивания
        stdin, stdout, stderr = ssh.exec_command(f"rm -rf {remote_path}")
        if stderr.channel.recv_exit_status() == 0:
            logging.info(f"🗑️  Отчет удален с сервера: {remote_path}")
        else:
            error = stderr.read().decode()
            logging.warning(f"⚠️  Не удалось удалить отчет с сервера: {error}")
            
        return local_report_path
            
    except Exception as e:
        logging.error(f"❌ Ошибка при скачивании отчета: {str(e)}")
        logging.error(f"Тип ошибки: {type(e).__name__}")
        return None
    finally:
        if ssh:
            ssh.close()
        if proxy_sock:
            try:
                proxy_sock.close()
            except:
                pass                        


def create_ssh_proxy_socket(cfg) -> paramiko.ProxyCommand:
    """
    Создаёт ProxyCommand для SSH подключения через SOCKS5 прокси.
    
    Args:
        cfg (dict): Конфигурация
        
    Returns:
        paramiko.ProxyCommand или None: ProxyCommand если прокси включен, None если нет
    """
    proxy_cfg = cfg.get('proxy', {})
    
    if not proxy_cfg.get('enabled'):
        return None
    
    proxy_host = proxy_cfg.get('ssh_proxy_host')
    proxy_port = proxy_cfg.get('ssh_proxy_port', 1081)
    
    ssh_host = cfg['ssh_config'].get('host')
    ssh_port = int(cfg['ssh_config'].get('port', 22) or 22)
    
    logging.info(f"🔒 SSH подключение через SOCKS5 прокси {proxy_host}:{proxy_port}")
    
    # Создаём SOCKS5 сокет через paramiko.ProxyCommand
    # Альтернатива: использовать ProxyCommand с nc или connect-proxy
    # Но проще и надёжнее - через sock параметр
    
    try:
        import socket
        
        # Создаём SOCKS5 сокет
        sock = socks.socksocket(socket.AF_INET, socket.SOCK_STREAM)
        sock.set_proxy(
            proxy_type=socks.SOCKS5,
            addr=proxy_host,
            port=proxy_port
        )
        sock.connect((ssh_host, ssh_port))
        
        logging.info(f"✅ SOCKS5 туннель для SSH установлен")
        return sock
        
    except Exception as e:
        logging.error(f"❌ Ошибка при создании SOCKS5 туннеля для SSH: {str(e)}")
        raise            