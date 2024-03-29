import logging
import os
import sys

from tqdm import tqdm

from lib.civitai import CivitaiClient
from lib.filedl import Aria2Downloader
from lib.util import safe_filename, save_yaml


BLACK_IDS = [17748]


def image_url_to_filename(url: str) -> str:
    basename = os.path.basename(url)
    name, ext = os.path.splitext(basename)
    if ext:
        return basename
    return name + '.jpg'


def filter_version_files(files: list[dict]) -> list[dict]:
    # 当一个版本中类型为 Model 的文件多于一个时
    # 排除掉非 SafeTensor 类型的 Model 文件
    num_models = 0
    filtered = []

    for file in files:
        type = file['type'].lower()
        fmt = file['metadata']['format'].lower()
        if type in ['model', 'prunedmodel', 'pruned model']:
            num_models += 1
            if fmt == 'pickletensor':
                continue
        filtered.append(file)

    if num_models > 1:
        return filtered
    else:
        return files


class CivitaiDownloader:

    def __init__(self, storage_dir: str = 'downloads', proxy: str = None):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._storage_dir = storage_dir
        self._client = CivitaiClient(proxy)
        self._downloader = Aria2Downloader(os.path.join(storage_dir, '@temp'))

    def download(self, model_id: int, latest_only: bool = False, data_only: bool = False):
        self._logger.info('[M:%d] Fetching model details', model_id)

        info = self._client.get_model(model_id)
        name = info['name']
        model_type = info['type']
        versions = info['modelVersions']
        self._logger.info('[M:%d] Downloading model: %s (Type: %s, Versions: %d)',
                          model_id, name, model_type, len(versions))

        safe_name = safe_filename(name)
        model_dir_name = f'{model_id}_{safe_name}'
        model_dir = os.path.join(self._storage_dir, model_type, model_dir_name)
        os.makedirs(model_dir, exist_ok=True)

        info_file_name = f'model_{model_id}_{safe_name}.yaml'
        info_file_path = os.path.join(model_dir, info_file_name)
        if os.path.isfile(info_file_path):
            self._logger.info('[M:%d] Skip existing: %s',
                              model_id, info_file_name)
        else:
            save_yaml(info_file_path, info)

        num_versions = len(versions)
        for i, version in enumerate(versions):
            if latest_only and i > 0:
                skipped = num_versions - 1
                self._logger.info('[M:%d] Skip remaining version(s): %d', model_id, skipped)
                break
            try:
                self._download_version(model_id, model_dir, version, data_only)
            except Exception as e:
                self._logger.error(e, exc_info=True)

        self._logger.info('[M:%d] Download finished: %s', model_id, name)

    def _download_version(self, model_id: int, model_dir: str,
                          version: dict, data_only: bool = False):
        ver_id = version['id']
        ver_name = version['name']
        self._logger.info('[M:%d,V:%d] Downloading version: %s (%s)',
                          model_id, ver_id, ver_name, ver_id)

        images = version['images']
        img_count = len(images)
        img_skipped = 0
        img_desc = '[M:{0},V:{1}] Downloading images'.format(model_id, ver_id)
        progress = tqdm(images, file=sys.stdout, desc=img_desc)

        for i, img in enumerate(progress):
            img_num = i + 1
            img_url = img['url']
            img_filename = image_url_to_filename(img_url)
            img_file = f'image_{model_id}_{ver_id}_{img_filename}'
            img_path = os.path.join(model_dir, img_file)

            if os.path.isfile(img_path):
                img_skipped += 1
                continue

            img_data = self._client.get_file_data(img_url)
            with open(img_path, 'wb+') as fp:
                fp.write(img_data)

        if img_skipped > 0:
            self._logger.info('[M:%d,V:%d] Images skipped: %d',
                              model_id, ver_id, img_skipped)

        if data_only:
            self._logger.info('[M:%d,V:%d] Data only, skip file download',
                              model_id, ver_id)
            return

        files = version['files']
        file_count = len(files)
        filtered = filter_version_files(files)
        filtered_count = len(filtered)
        dropped = file_count - filtered_count
        if dropped > 0:
            files = filtered
            file_count = filtered_count
            self._logger.warning('[M:%d,V:%d] Dropped PickleTensor models: %d',
                                 model_id, ver_id, dropped)

        for i, file in enumerate(files):
            file_num = i + 1
            file_id = file['id']
            file_url = file['downloadUrl']
            file_name = file['name']
            final_name = f'file_{model_id}_{ver_id}_{file_id}_{file_name}'
            file_path = os.path.join(model_dir, final_name)

            if os.path.isfile(file_path):
                self._logger.info('[M:%d,V:%d,F:%d(%d/%d)] Skip existing: %s',
                                  model_id, ver_id, file_id, file_num, file_count, file_name)
                continue

            self._logger.info('[M:%d,V:%d,F:%d(%d/%d)] Downloading file: %s',
                              model_id, ver_id, file_id, file_num, file_count, file_name)
            real_url = self._client.get_redirected_url(file_url)
            self._downloader.download(real_url, file_path)

    def download_batch(self, type: str = 'LORA',
                       min_page: int = 1, max_page: int = 10,
                       latest_only: bool = False, data_only: bool = False):
        for p in range(min_page, max_page + 1):
            self._logger.info('fetching list - type:%s, page:%d', type, p)
            resp = self._client.get_models(p, types=[type], sort='Highest Rated')
            for item in resp['items']:
                model_id = item['id']
                if model_id in BLACK_IDS:
                    self._logger.error('model id blocked: %d', model_id)
                    continue
                try:
                    self.download(model_id, latest_only, data_only)
                except Exception as e:
                    self._logger.error(e, exc_info=True)
            total_page = resp['metadata']['totalPages']
            if p >= total_page:
                break
