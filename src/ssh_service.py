import paramiko
import os
import shutil
import logging
import subprocess

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
    try:
        # Создаем базовую директорию для отчетов Gatling
        local_path = os.path.join(main_folder_path, "gatling")
        os.makedirs(local_path, exist_ok=True)
        logging.info(f"Создана базовая директория: {local_path}")
        
        # Устанавливаем SSH-соединение
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            hostname=cfg['ssh_config']['host'],
            username=cfg['ssh_config']['username'],
            password=cfg['ssh_config']['password']
        )
        
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
            
        # Формируем команду SCP для копирования всей директории
        scp_command = f'scp -r "{cfg["ssh_config"]["username"]}@{cfg["ssh_config"]["host"]}:{remote_path}" "{local_path}"'
        logging.info(f"Выполняем команду: {scp_command}")
        
        # Выполняем команду через shell
        result = subprocess.run(scp_command, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            logging.info(f"Отчет успешно скачан: {local_report_path}")
            
            # Удаляем отчет с сервера после успешного скачивания
            stdin, stdout, stderr = ssh.exec_command(f"rm -rf {remote_path}")
            if stderr.channel.recv_exit_status() == 0:
                logging.info(f"Отчет удален с сервера: {remote_path}")
            else:
                error = stderr.read().decode()
                logging.warning(f"Не удалось удалить отчет с сервера: {error}")
                
            return local_report_path
        else:
            logging.error(f"Ошибка при выполнении scp: {result.stderr}")
            return None
            
    except Exception as e:
        logging.error(f"Ошибка при скачивании отчета: {str(e)}")
        logging.error(f"Тип ошибки: {type(e).__name__}")
        return None
    finally:
        if ssh:
            ssh.close() 