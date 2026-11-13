"""Synchronous Python client. No JVM or MCP dependencies needed by API callers."""
import json
from urllib.request import Request, urlopen
from urllib.error import HTTPError


class Client:
    def __init__(self, url='http://127.0.0.1:8766', timeout=1800):
        self.url, self.timeout = url.rstrip('/'), timeout

    def call(self, method, **params):
        req = Request(self.url+'/api/call', json.dumps(dict(method=method, params=params)).encode(),
                      {'Content-Type': 'application/json'})
        try:
            with urlopen(req, timeout=self.timeout) as response:
                return json.load(response)['result']
        except HTTPError as error:
            raise RuntimeError(error.read().decode()) from error

    def __getattr__(self, method):
        return lambda **params: self.call(method, **params)

    def all_functions(self, programs=None, query=''):
        offset = 0
        while True:
            page = self.list_functions(programs=programs, query=query, offset=offset, limit=10000)
            yield from page['functions']
            offset += len(page['functions'])
            if offset >= page['total']:
                return
