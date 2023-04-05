import requests

HEADERS = {
    'User-Agent': 'CivitaiLink:Automatic1111',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Cache-Control': 'max-age=0',
}

API_BASE_URI = 'https://civitai.com/api/v1/'


# https://github.com/civitai/civitai/wiki/REST-API-Reference

class CivitaiClient():

    def __init__(self, proxy: str = None):
        self._base_uri = API_BASE_URI
        self._session = self._init_session(proxy)

    def _init_session(self, proxy: str = None):
        headers = HEADERS.copy()
        session = requests.session()
        session.headers = headers
        if proxy:
            session.proxies = {
                'http': proxy,
                'https': proxy,
            }
        return session

    def _invoke_get(self, path: str, params: dict[str, any] = None) -> dict:
        url = f'{self._base_uri}{path}'
        resp = self._session.get(url, params=params)
        resp.raise_for_status()
        return resp.json()

    def get_models(self, page: int = 1, types: str = None, sort: str = None) -> dict:
        """
        :param page: page number
        :param types: enums (Checkpoint, TextualInversion, Hypernetwork, AestheticGradient, LORA, Controlnet, Poses)
        :param sort: enum (Highest Rated, Most Downloaded, Newest)
        :return:
        """
        params = {
            'page': page,
            'types': types,
            'sort': sort,
        }
        params = {k: v for k, v in params.items() if v is not None}
        return self._invoke_get('models', params)

    def get_model(self, model_id: int) -> dict:
        path = f'models/{model_id}'
        return self._invoke_get(path)

    def get_image_data(self, url: str) -> bytes:
        resp = self._session.get(url)
        resp.raise_for_status()
        return resp.content
