import os
import paramiko
from config_manager import ConfigManager

class SSHClient:
    def __init__(self, config_manager: ConfigManager):
        self.config = config_manager
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.sftp = None
    
    def connect(self):
        """Подключается к удаленному серверу."""
        try:
            self.ssh.connect(
                hostname=self.config.ssh['hostname'],
                username=self.config.ssh['username'],
                port=int(self.config.ssh['port'])
            )
            self.sftp = self.ssh.open_sftp()
            print(f"Успешное подключение к {self.config.ssh['hostname']}")
        except Exception as e:
            print(f"Ошибка при подключении к серверу: {str(e)}")
            raise
    
    def disconnect(self):
        """Отключается от удаленного сервера."""
        if self.sftp:
            self.sftp.close()
        self.ssh.close()
    
    def get_last_report_name(self) -> str:
        """Получает имя последнего отчета из lastRun.txt."""
        try:
            last_run_path = os.path.join(self.config.ssh['remote_report_dir'], 'lastRun.txt')
            with self.sftp.file(last_run_path, 'r') as f:
                last_report = f.read().decode().strip()
            
            if not last_report:
                raise ValueError("Имя последнего отчета пустое")
            
            print(f"Получено имя последнего отчета: {last_report}")
            return last_report
            
        except Exception as e:
            print(f"Ошибка при чтении lastRun.txt: {str(e)}")
            raise
    
    def download_report(self, report_name: str, local_dir: str):
        """Скачивает отчет с удаленного сервера."""
        try:
            remote_report_dir = os.path.join(self.config.ssh['remote_report_dir'], report_name)
            
            print(f"Скачиваю отчет {report_name} в {local_dir}...")
            
            # Создаем локальную директорию
            os.makedirs(local_dir, exist_ok=True)
            
            # Скачиваем все файлы из директории отчета
            for item in self.sftp.listdir(remote_report_dir):
                remote_path = os.path.join(remote_report_dir, item)
                local_path = os.path.join(local_dir, item)
                
                if self.sftp.stat(remote_path).st_mode & 0o40000:  # Это директория
                    os.makedirs(local_path, exist_ok=True)
                    self._download_directory(remote_path, local_path)
                else:  # Это файл
                    self.sftp.get(remote_path, local_path)
            
            print(f"Отчет успешно скачан в {local_dir}")
            
            # Удаляем отчет на сервере
            print(f"Удаляю {remote_report_dir} на сервере...")
            self._remove_remote_directory(remote_report_dir)
            print("Директория с отчетом на сервере очищена.")
            
        except Exception as e:
            print(f"Ошибка при скачивании отчета: {str(e)}")
            raise
    
    def _download_directory(self, remote_dir: str, local_dir: str):
        """Рекурсивно скачивает директорию с удаленного сервера."""
        for item in self.sftp.listdir(remote_dir):
            remote_path = os.path.join(remote_dir, item)
            local_path = os.path.join(local_dir, item)
            
            if self.sftp.stat(remote_path).st_mode & 0o40000:  # Это директория
                os.makedirs(local_path, exist_ok=True)
                self._download_directory(remote_path, local_path)
            else:  # Это файл
                self.sftp.get(remote_path, local_path)
    
    def _remove_remote_directory(self, remote_dir: str):
        """Рекурсивно удаляет директорию на удаленном сервере."""
        for item in self.sftp.listdir(remote_dir):
            remote_path = os.path.join(remote_dir, item)
            
            if self.sftp.stat(remote_path).st_mode & 0o40000:  # Это директория
                self._remove_remote_directory(remote_path)
            else:  # Это файл
                self.sftp.remove(remote_path)
        
        self.sftp.rmdir(remote_dir) 
