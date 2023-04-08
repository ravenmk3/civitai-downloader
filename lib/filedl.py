import os
import shutil
import subprocess
import sys
import time
from abc import ABCMeta, abstractmethod

from lib.aria2 import Aria2RpcClient


class FileDownloader(metaclass=ABCMeta):

    @abstractmethod
    def download(self, url: str, filename: str):
        pass


class Aria2Downloader(FileDownloader):

    def __init__(self, temp_dir: str):
        self._temp_dir = temp_dir

    def download(self, url: str, filename: str):
        temp_name = os.path.basename(filename)
        temp_path = os.path.join(self._temp_dir, temp_name)
        args = [
            'aria2c',
            f'--dir={self._temp_dir}',
            f'--out={temp_name}',
            '--max-tries=10',
            '--split=5',
            '--lowest-speed-limit=1K',
            '--user-agent=CivitaiLink:Automatic1111',
            '--file-allocation=falloc',
            f'{url}',
        ]
        proc = subprocess.Popen(args, shell=False,
                                stdout=sys.stdout, stderr=sys.stderr)
        proc.wait()
        exit_code = proc.returncode
        if exit_code != 0:
            raise RuntimeError(f'aria2 exited with code: {exit_code}')
        shutil.move(temp_path, filename)


class Aria2RpcDownloader(FileDownloader):

    def __init__(self, temp_dir: str, token: str = None):
        self._temp_dir = temp_dir
        self._aria2 = Aria2RpcClient(token=token)

    def download(self, url: str, filename: str):
        tmp_filename = os.path.basename(filename)
        opts = {
            'dir': self._temp_dir,
            'out': tmp_filename
        }
        temp_path = os.path.join(self._temp_dir, tmp_filename)
        task_id = self._aria2.add_uri([url], opts)
        task_status = None
        task_active = True
        while task_active:
            time.sleep(5)
            state = self._aria2.tell_status(task_id)
            task_status = state['status']
            task_active = (task_status == 'active')

        completed = (task_status == 'complete')
        if completed:
            shutil.move(temp_path, filename)
            self._aria2.remove_download_result(task_id)
