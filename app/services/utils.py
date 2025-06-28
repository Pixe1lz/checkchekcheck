import asyncio
import logging
import traceback

import aiohttp
import aiohttp.client_exceptions
from aiohttp.client_reqrep import ClientResponse


class AsyncHTTPClient:
    def __init__(self, base_url: str, headers: dict = None):
        self.base_url = base_url.rstrip('/')
        self.headers = headers or {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 YaBrowser/25.2.0.0 Safari/537.36',
        }
        self.session = None

    async def __aenter__(self):
        await self.start_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close_session()

    async def start_session(self):
        self.session = aiohttp.ClientSession(headers=self.headers)

    async def close_session(self):
        if self.session:
            await self.session.close()
            self.session = None

    async def request(
            self,
            method: str,
            endpoint: str,
            params: dict = None,
            data: dict = None,
            json: dict = None,
            headers: dict = None
    ):
        if not self.session:
            await self.start_session()

        url = f'{self.base_url}{endpoint}'
        request_headers = {**self.headers, **(headers or {})}

        async with self.session.request(
            method=method,
            url=url,
            params=params,
            data=data,
            json=json,
            headers=request_headers
        ) as response:
            response: ClientResponse
            response.raise_for_status()
            if response.content_type == 'application/json':
                return await response.json()
            return await response.text()

    async def get(self, endpoint: str, params: dict = None, headers: dict = None):
        while True:
            try:
                return await self.request('GET', endpoint, params=params, headers=headers)
            except aiohttp.client_exceptions.ClientResponseError:
                logging.error(traceback.format_exc())
                return None
            except aiohttp.client_exceptions.ConnectionTimeoutError:
                await asyncio.sleep(1)

    async def post(self, endpoint: str, data: dict = None, json: dict = None, headers: dict = None):
        return await self.request('POST', endpoint, data=data, json=json, headers=headers)


def translator(text: str) -> str:
    return text
