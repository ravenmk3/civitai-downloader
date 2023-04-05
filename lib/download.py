import logging
import os

from lib.civitai import CivitaiClient
from lib.util import safe_filename, save_yaml, md5_hex


class CivitaiDownloader:

    def __init__(self, download_dir: str = 'downloads', proxy: str = None):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._download_dir = download_dir
        self._client = CivitaiClient(proxy)

    def download_one(self, model_id: int):
        info = self._client.get_model(model_id)
        name = info['name']
        model_type = info['type']
        versions = info['modelVersions']
        logging.info('[%d:%s] downloading model: %s (%s), versions: %d', model_id, name, name, model_type,
                     len(versions))

        safe_name = safe_filename(name)
        model_dir_name = f'{model_id}_{safe_name}'
        model_dir = os.path.join(self._download_dir, model_type, model_dir_name)
        os.makedirs(model_dir, exist_ok=True)

        info_file_name = f'{model_id}_{safe_name}.yaml'
        info_file_path = os.path.join(model_dir, info_file_name)
        save_yaml(info_file_path, info)

        last_ver = versions[0]
        ver_id = last_ver['id']
        ver_name = last_ver['name']
        safe_ver_name = safe_filename(ver_name)
        logging.info('[%d:%s] downloading version: %s (%s)', model_id, name, ver_name, ver_id)

        images = last_ver['images']
        files = last_ver['files']

        img_count = len(images)
        for i, img in enumerate(images):
            img_num = i + 1
            img_url = img['url']
            img_url_hash = md5_hex(img_url)
            img_file = f'm{model_id}_v{ver_id}_{img_url_hash}.jpg'
            img_path = os.path.join(model_dir, img_file)

            if os.path.isfile(img_path):
                logging.info('[%d:%s] ignore existing image (%d/%d): %s',
                             model_id, name, img_num, img_count, img_url)
                continue

            logging.info('[%d:%s] downloading image (%d/%d): %s',
                         model_id, name, img_num, img_count, img_url)
            img_data = self._client.get_image_data(img_url)
            with open(img_path, 'wb+') as fp:
                fp.write(img_data)
