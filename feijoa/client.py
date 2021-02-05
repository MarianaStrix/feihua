import asyncio
import json
import logging
from types import TracebackType
from typing import Any, Dict, Optional, Type, Union

import aiohttp
from yarl import URL

from .exceptions import ClientError
from .recordset import Recordsets
from .signer import sign
from .utils import _AsyncCM, parse_result

__all__ = ("Client",)

log = logging.getLogger(__name__)


class Client:
    def __init__(
            self,
            access_key_id: str,
            secret_access_key: str,
            host: str,
            scheme: Optional[str] = "https",
            connector: Optional[aiohttp.BaseConnector] = None,
            session: Optional[aiohttp.ClientSession] = None,
    ) -> None:

        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key

        self.scheme = scheme
        self.host = host

        if connector is None:
            connector = aiohttp.TCPConnector(ssl=None)
        self.connector = connector

        if session is None:
            session = aiohttp.ClientSession(connector=self.connector)
        self.session = session

        self.recordsets = Recordsets(self)

    async def __aenter__(self) -> "Client":
        return self

    async def __aexit__(
            self,
            exc_type: Optional[Type[BaseException]],
            exc_val: Optional[BaseException],
            exc_tb: Optional[TracebackType],
    ) -> None:
        await self.close()

    async def close(self) -> None:
        await self.session.close()

    def _canonicalize_url(self, api_version: Union[str, URL], path: Union[str, URL], query: Union[str, Dict]) -> URL:
        if query is None:
            query = ""
        return URL.build(scheme=self.scheme, host=self.host, path=f"{api_version}{path}", query=query)

    async def _query_json(
            self,
            api_version: Union[str, URL],
            path: Union[str, URL],
            query: Union[str, URL] = None,
            method: str = "GET",
            *,
            data: Any = None,
            headers=None,
            timeout=None,
            read_until_eof: bool = True,
    ):
        """
        A shorthand of _query() that treats the input as JSON.
        """
        if headers is None:
            headers = {}
        headers["Content-Type"] = "application/json"

        if data is not None and not isinstance(data, (str, bytes)):
            data = json.dumps(data)

        async with self._query(
                api_version=api_version,
                path=path,
                query=query,
                method=method,
                data=data,
                headers=headers,
                timeout=timeout,
                read_until_eof=read_until_eof,
        ) as response:
            data = await parse_result(response)
            return data, response.status

    def _query(
            self,
            api_version: Union[str, URL],
            path: Union[str, URL],
            query: Union[str, URL],
            method: str = "GET",
            *,
            data: Any = None,
            headers=None,
            timeout=None,
            chunked=None,
            read_until_eof: bool = True,
    ):
        """
        Get the response object by performing the HTTP request.
        The caller is responsible to finalize the response object.
        """
        return _AsyncCM(
            self._do_query(
                api_version=api_version,
                path=path,
                query=query,
                method=method,
                data=data,
                headers=headers,
                timeout=timeout,
                chunked=chunked,
                read_until_eof=read_until_eof,
            )
        )

    async def _do_query(
            self,
            api_version: Union[str, URL],
            path: Union[str, URL],
            query: Union[str, URL],
            method: str,
            *,
            data: Any,
            headers,
            timeout,
            chunked,
            read_until_eof: bool,
    ):

        url = self._canonicalize_url(api_version, path, query)

        sign_handlers = sign(
            key=self.access_key_id,
            secret=self.secret_access_key,
            method=method,
            headers=headers,
            url=url,
            body=data,
        )
        try:
            response = await self.session.request(
                method=method,
                url=url,
                headers=sign_handlers,
                data=data,
                timeout=timeout,
                chunked=chunked,
                read_until_eof=read_until_eof,
            )
        except asyncio.TimeoutError:
            raise
        except aiohttp.ClientConnectionError as exc:
            raise ClientError(
                503,
                {"message": f"Cannot connect to SberCloud at {url} [{exc}]"},
            )
        if (response.status // 100) in [4, 5]:
            pass
            # TODO: добавлю обработку когда оттестю эту часть
            # what = await response.read()
            # content_type = response.headers.get("content-type", "")
            # response.close()
            # if content_type == "application/json":
            #     raise Exception
            # else:
            #     raise Exception
        return response

