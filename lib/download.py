import logging
import os
import shutil
import time
from abc import abstractmethod, ABCMeta

from lib.aria2 import Aria2RpcClient
from lib.civitai import CivitaiClient
from lib.util import safe_filename, save_yaml


BLACK_IDS = [17748]


class FileDownloader(metaclass=ABCMeta):

    @abstractmethod
    def download(self, url: str, filename: str):
        pass


class Aria2Downloader(FileDownloader):

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


def image_url_to_filename(url: str) -> str:
    basename = os.path.basename(url)
    name, ext = os.path.splitext(basename)
    if ext:
        return basename
    return name + '.jpg'


class CivitaiDownloader:

    def __init__(self, storage_dir: str = 'downloads', proxy: str = None):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._storage_dir = storage_dir
        self._client = CivitaiClient(proxy)
        self._downloader = Aria2Downloader(os.path.join(storage_dir, 'temp'))

    def download(self, model_id: int):
        info = self._client.get_model(model_id)
        name = info['name']
        model_type = info['type']
        versions = info['modelVersions']
        self._logger.info('[%d:%s] downloading model: %s (%s), versions: %d',
                          model_id, name, name, model_type, len(versions))

        safe_name = safe_filename(name)
        model_dir_name = f'{model_id}_{safe_name}'
        model_dir = os.path.join(self._storage_dir, model_type, model_dir_name)
        os.makedirs(model_dir, exist_ok=True)

        info_file_name = f'model_{model_id}_{safe_name}.yaml'
        info_file_path = os.path.join(model_dir, info_file_name)
        if os.path.isfile(info_file_path):
            self._logger.info('[%d:%s] ignore existing data file: %s',
                              model_id, name, info_file_name)
        else:
            save_yaml(info_file_path, info)

        for version in versions:
            try:
                self._download_version(model_id, name, model_dir, version)
            except Exception as e:
                self._logger.error(e, exc_info=True)

        self._logger.info('[%d:%s] download finished.', model_id, name)

    def _download_version(self, model_id: int, model_name: str,
                          model_dir: str, version: dict):
        ver_id = version['id']
        ver_name = version['name']
        safe_ver_name = safe_filename(ver_name)
        self._logger.info('[%d:%s] downloading version: %s (%s)',
                          model_id, model_name, ver_name, ver_id)

        images = version['images']
        img_count = len(images)
        for i, img in enumerate(images):
            img_num = i + 1
            img_url = img['url']
            img_filename = image_url_to_filename(img_url)
            img_file = f'image_{model_id}_{ver_id}_{img_filename}'
            img_path = os.path.join(model_dir, img_file)

            if os.path.isfile(img_path):
                self._logger.info('[%d:%s] ignore existing image (%d/%d): %s',
                                  model_id, model_name, img_num, img_count, img_url)
                continue

            self._logger.info('[%d:%s] downloading image (%d/%d): %s',
                              model_id, model_name, img_num, img_count, img_url)
            img_data = self._client.get_file_data(img_url)
            with open(img_path, 'wb+') as fp:
                fp.write(img_data)

        files = version['files']
        file_count = len(files)
        for i, file in enumerate(files):
            file_num = i + 1
            file_id = file['id']
            file_url = file['downloadUrl']
            file_name = file['name']
            final_name = f'file_{model_id}_{ver_id}_{file_id}_{file_name}'
            file_path = os.path.join(model_dir, final_name)

            if os.path.isfile(file_path):
                self._logger.info('[%d:%s] ignore existing file (%d/%d): %s',
                                  model_id, model_name, file_num, file_count, file_name)
                continue

            self._logger.info('[%d:%s] downloading file (%d/%d): %s, %s',
                              model_id, model_name, file_num, file_count, file_name, file_url)
            real_url = self._client.get_redirected_url(file_url)
            self._downloader.download(real_url, file_path)

    def download_batch(self, type: str = 'LORA', max_page: int = 10):
        for p in range(1, max_page + 1):
            self._logger.info('fetching list - type:%s, page:%d', type, p)
            resp = self._client.get_models(p, types=[type], sort='Highest Rated')
            for item in resp['items']:
                model_id = item['id']
                if model_id in BLACK_IDS:
                    self._logger.error('model id blocked: %d', model_id)
                    continue
                try:
                    self.download(model_id)
                except Exception as e:
                    self._logger.error(e, exc_info=True)
            total_page = resp['metadata']['totalPages']
            if p >= total_page:
                break
