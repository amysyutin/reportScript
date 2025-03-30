import paramiko
import os
import shutil
from utils import logger, create_folder_if_not_exists

class SSHService:
    def __init__(self, config):
        self.config = config
        self.ssh = None
        self.sftp = None

    def connect(self):
        """Устанавливает SSH-соединение."""
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
        """Закрывает SSH-соединение."""
        if self.sftp:
            self.sftp.close()
        if self.ssh:
            self.ssh.close()
            logger.info("SSH-соединение закрыто")

    def get_last_report_name(self):
        """Получает имя последнего отчета."""
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
        """Скачивает отчет."""
        try:
            create_folder_if_not_exists(self.config.ssh_config['local_path'])
            
            remote_folder = f"{self.config.ssh_config['remote_path']}/{report_name}"
            local_folder = os.path.join(self.config.ssh_config['local_path'], report_name)

            # Проверяем существование удаленной папки
            try:
                self.sftp.stat(remote_folder)
            except FileNotFoundError:
                logger.warning(f"Папка с отчетом не найдена на сервере: {remote_folder}")
                logger.warning("Возможно, отчет был уже скачан и удален ранее")
                return None

            # Скачивание всей папки
            self.sftp.get(remote_folder, local_folder)
            logger.info(f"Отчет скачан в {local_folder}")
            return local_folder
        except Exception as e:
            logger.error(f"Ошибка при скачивании отчета: {str(e)}")
            raise

    def cleanup_server(self, report_name):
        """Удаляет отчет на сервере."""
        try:
            remote_folder = f"{self.config.ssh_config['remote_path']}/{report_name}"
            self.sftp.rmdir(remote_folder)
            logger.info(f"Отчет удален на сервере: {remote_folder}")
        except Exception as e:
            logger.error(f"Ошибка при удалении отчета на сервере: {str(e)}")
            raise

    def download_last_report(self):
        """Основной метод для скачивания последнего отчета."""
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