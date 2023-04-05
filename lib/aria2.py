import json
import uuid
from typing import Union

import requests


class Aria2RpcError(RuntimeError):

    def __init__(self, code: int, message: str, **kwargs):
        super().__init__(message, kwargs)
        self.code = code
        self.message = message

    def __str__(self):
        return f'[Code:{self.code}] {self.message}'


class Aria2RpcClient:

    def __init__(self, rpc_url: str = 'http://localhost:6800/jsonrpc', token: str = None):
        self.rpc_url = rpc_url
        self.token = token

    def random_id(self) -> str:
        return uuid.uuid4().hex

    def invoke(self, req_id: str, method: str, params: list) -> Union[str, list, dict]:
        if self.token is not None:
            params.insert(0, f'token:{self.token}')
        json_data = {
            'jsonrpc': '2.0',
            'id': req_id,
            'method': method,
            'params': params,
        }
        data = json.dumps(json_data).encode(encoding='utf-8')
        response = requests.post(self.rpc_url, data)
        json_res = json.loads(response.text)
        if response.status_code == 200:
            return json_res['result']
        error = json_res['error']
        error_code = int(error['code'])
        raise Aria2RpcError(error_code, error['message'])

    def invoke_with_id(self, method: str, params: list) -> Union[str, list, dict]:
        return self.invoke(self.random_id(), method, params)

    def get_version(self) -> dict:
        return self.invoke_with_id('aria2.getVersion', [])

    def add_uri(self, uris: list, options: dict = None) -> str:
        params = [uris]
        if options:
            params.append(options)
        return self.invoke_with_id('aria2.addUri', params)

    def get_uris(self, gid: str) -> list:
        params = [gid]
        return self.invoke_with_id('aria2.getUris', params)

    def remove(self, gid: str) -> str:
        params = [gid]
        return self.invoke_with_id('aria2.remove', params)

    def force_remove(self, gid: str) -> str:
        params = [gid]
        return self.invoke_with_id('aria2.forceRemove', params)

    def pause(self, gid: str) -> str:
        params = [gid]
        return self.invoke_with_id('aria2.pause', params)

    def force_pause(self, gid: str) -> str:
        params = [gid]
        return self.invoke_with_id('aria2.forcePause', params)

    def pause_all(self) -> str:
        return self.invoke_with_id('aria2.pauseAll', [])

    def force_pause_all(self) -> str:
        return self.invoke_with_id('aria2.forcePauseAll', [])

    def unpause(self, gid: str) -> str:
        params = [gid]
        return self.invoke_with_id('aria2.unpause', params)

    def unpause_all(self) -> str:
        return self.invoke_with_id('aria2.unpauseAll', [])

    def tell_status(self, gid: str, keys: list = None) -> dict:
        params = [gid]
        if keys:
            params.append(keys)
        return self.invoke_with_id('aria2.tellStatus', params)

    def change_uri(self, gid: str, del_uris: list, add_uris: list) -> list:
        params = [gid, 1, del_uris, add_uris]
        return self.invoke_with_id('aria2.changeUri', params)

    def get_global_stat(self) -> dict:
        return self.invoke_with_id('aria2.getGlobalStat', [])

    def purge_download_result(self) -> str:
        return self.invoke_with_id('aria2.purgeDownloadResult', [])

    def remove_download_result(self, gid: str) -> str:
        params = [gid]
        return self.invoke_with_id('aria2.removeDownloadResult', params)

    def shutdown(self) -> str:
        return self.invoke_with_id('aria2.shutdown', [])

    def force_shutdown(self) -> str:
        return self.invoke_with_id('aria2.forceShutdown', [])

    def save_session(self) -> str:
        return self.invoke_with_id('aria2.saveSession', [])
