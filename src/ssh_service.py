import paramiko
import os
import shutil
import logging
from utils import logger, create_folder_if_not_exists

class SSHService:
    """
    Класс для работы с SSH-соединением и скачивания отчетов.
    
    Attributes:
        config: Объект конфигурации с параметрами SSH
        ssh: SSH-клиент
        sftp: SFTP-клиент
    """
    
    def __init__(self, config):
        """
        Инициализация сервиса SSH.
        
        Args:
            config: Объект конфигурации с параметрами SSH
        """
        self.config = config
        self.ssh = None
        self.sftp = None

    def connect(self):
        """
        Устанавливает SSH-соединение с сервером.
        
        Создает SSH-клиент, настраивает политику ключей и устанавливает соединение.
        После успешного соединения открывает SFTP-сессию.
        
        Raises:
            Exception: Если не удалось установить соединение
        """
        try:
            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh.connect(
                self.config.ssh_config['host'],
                username=self.config.ssh_config['username'],
                password=self.config.ssh_config['password']
            )
            self.sftp = self.ssh.open_sftp()
            logger.info("SSH-соединение установлено")
        except Exception as e:
            logger.error(f"Ошибка при установке SSH-соединения: {str(e)}")
            raise

    def close(self):
        """
        Закрывает SSH-соединение.
        
        Корректно закрывает SFTP-сессию и SSH-соединение.
        """
        if self.sftp:
            self.sftp.close()
        if self.ssh:
            self.ssh.close()
            logger.info("SSH-соединение закрыто")

    def get_last_report_name(self):
        """
        Получает имя последнего отчета из файла lastRun.txt.
        
        Returns:
            str: Имя последнего отчета
            
        Raises:
            Exception: Если не удалось прочитать файл
        """
        try:
            remote_file = f"{self.config.ssh_config['remote_path']}/lastRun.txt"
            with self.sftp.file(remote_file, "r") as file:
                last_run_name = file.read().decode().strip()
            logger.info(f"Получено имя последнего отчета: {last_run_name}")
            return last_run_name
        except Exception as e:
            logger.error(f"Ошибка при получении имени последнего отчета: {str(e)}")
            raise

    def download_report(self, report_name):
        """
        Скачивает отчет с сервера.
        
        Args:
            report_name (str): Имя отчета для скачивания
            
        Returns:
            str: Путь к скачанному отчету или None, если отчет не найден
            
        Raises:
            Exception: Если возникла ошибка при скачивании
        """
        try:
            # Создаем локальную директорию для отчета
            create_folder_if_not_exists(self.config.ssh_config['local_path'])
            
            # Формируем пути для удаленного и локального отчета
            remote_folder = f"{self.config.ssh_config['remote_path']}/{report_name}"
            local_folder = os.path.join(self.config.ssh_config['local_path'], report_name)

            # Проверяем существование удаленной папки
            try:
                self.sftp.stat(remote_folder)
            except FileNotFoundError:
                logger.warning(f"Папка с отчетом не найдена на сервере: {remote_folder}")
                logger.warning("Возможно, отчет был уже скачан и удален ранее")
                return None

            # Скачиваем всю папку с отчетом
            self.sftp.get(remote_folder, local_folder)
            logger.info(f"Отчет скачан в {local_folder}")
            return local_folder
        except Exception as e:
            logger.error(f"Ошибка при скачивании отчета: {str(e)}")
            raise

    def cleanup_server(self, report_name):
        """
        Удаляет отчет на сервере после успешного скачивания.
        
        Args:
            report_name (str): Имя отчета для удаления
            
        Raises:
            Exception: Если не удалось удалить отчет
        """
        try:
            remote_folder = f"{self.config.ssh_config['remote_path']}/{report_name}"
            self.sftp.rmdir(remote_folder)
            logger.info(f"Отчет удален на сервере: {remote_folder}")
        except Exception as e:
            logger.error(f"Ошибка при удалении отчета на сервере: {str(e)}")
            raise

    def download_last_report(self):
        """
        Основной метод для скачивания последнего отчета.
        
        Выполняет следующие действия:
        1. Устанавливает SSH-соединение
        2. Получает имя последнего отчета
        3. Скачивает отчет
        4. Удаляет отчет на сервере
        5. Закрывает соединение
        
        Returns:
            str: Путь к скачанному отчету или None, если отчет не найден
        """
        try:
            self.connect()
            report_name = self.get_last_report_name()
            local_path = self.download_report(report_name)
            
            if local_path is None:
                logger.info("Пропускаем удаление отчета на сервере, так как он не найден")
                return None
                
            self.cleanup_server(report_name)
            return local_path
        finally:
            self.close()

def ssh_download_last_report(cfg, main_folder_path):
    """
    Функция для скачивания последнего отчета Gatling с сервера.
    
    Args:
        cfg (dict): Конфигурационный словарь с параметрами SSH
        main_folder_path (str): Путь к основной папке для сохранения отчета
        
    Returns:
        str: Путь к скачанному отчету или None, если возникла ошибка
    """
    try:
        # Создаем папку для отчета Gatling внутри основной папки
        local_path = os.path.join(main_folder_path, "gatling")
        create_folder_if_not_exists(local_path)
        
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
        
        if not report_name:
            logging.warning("Имя отчета не найдено в lastRun.txt")
            return None
            
        # Формируем пути для удаленного и локального отчета
        remote_path = os.path.join(cfg['ssh_config']['remote_path'], report_name)
        local_report_path = os.path.join(local_path, report_name)
        
        # Открываем SFTP-сессию и скачиваем отчет
        sftp = ssh.open_sftp()
        try:
            sftp.get(remote_path, local_report_path)
            logging.info(f"Отчет успешно скачан: {local_report_path}")
            
            # Удаляем отчет с сервера после успешного скачивания
            stdin, stdout, stderr = ssh.exec_command(f"rm -rf {remote_path}")
            if stderr.channel.recv_exit_status() == 0:
                logging.info(f"Отчет удален с сервера: {remote_path}")
            else:
                logging.warning(f"Не удалось удалить отчет с сервера: {stderr.read().decode()}")
                
            return local_report_path
            
        except FileNotFoundError:
            logging.warning(f"Отчет не найден на сервере: {remote_path}")
            return None
        finally:
            sftp.close()
            
    except Exception as e:
        logging.error(f"Ошибка при скачивании отчета: {str(e)}")
        return None
    finally:
        ssh.close() 