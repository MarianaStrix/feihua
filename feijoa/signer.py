import binascii
import copy
import hashlib
import hmac
from datetime import datetime
from typing import Dict, Union
from urllib.parse import parse_qs, quote, unquote, urlparse

from yarl import URL

ALGORITHM = "SDK-HMAC-SHA256"
BASIC_DATE_FORMAT = "%Y%m%dT%H%M%SZ"
HEADER_AUTHORIZATION = "Authorization"
HEADER_CONTENT_SHA256 = "x-sdk-content-sha256"
HEADER_CONTENT_TYPE = "content-type"
HEADER_HOST = "host"
HEADER_X_DATE = "X-Sdk-Date"


# HWS API Gateway Signature
class _Request:
    def __init__(self, method: str, url: Union[str, URL], headers: Dict = None, body: Dict = None):
        if isinstance(url, URL):
            url = str(url)
        parsing_url = urlparse(url)

        self.method = method
        self.scheme = parsing_url.scheme
        self.host = parsing_url.hostname
        self.uri = parsing_url.path
        self.query = parse_qs(parsing_url.query, keep_blank_values=True)
        if headers is None:
            self.headers = {}
        else:
            self.headers = copy.deepcopy(headers)
        if body is None:
            body = ""
        self.body = body.encode("utf-8")


class Signer:
    def __init__(self, key: str, secret: str):
        self.key = key
        self.secret = secret

    # SignRequest set Authorization header
    def signer(self, r: _Request):
        header_time = self._find_header(r, HEADER_X_DATE)
        if header_time is None:
            t = datetime.utcnow()
            r.headers[HEADER_X_DATE] = datetime.strftime(t, BASIC_DATE_FORMAT)
        else:
            t = datetime.strptime(header_time, BASIC_DATE_FORMAT)

        header_host = self._find_header(r, HEADER_HOST)
        if header_host is None:
            r.headers["host"] = r.host

        header_content_type = self._find_header(r, HEADER_CONTENT_TYPE)
        if header_content_type is None:
            r.headers["content-type"] = "application/json"

        signed_headers = self._get_list_signed_headers(r)
        canonical_request = self._get_canonical_request(r, signed_headers)
        string_to_sign = self._get_string_to_sign(canonical_request, t)
        signature = self._sign_string_to_sign(string_to_sign, self.secret)
        auth_value = self._auth_header_value(signature, self.key, signed_headers)
        r.headers[HEADER_AUTHORIZATION] = auth_value
        r.headers["content-length"] = str(len(r.body))
        query_string = self._get_canonical_query_string(r)
        if query_string != "":
            r.uri = r.uri + "?" + query_string

    # Build a get_canonical_request from a regular request string
    #
    # get_canonical_request =
    #    HTTPRequestMethod + '\n' +
    #    get_canonical_uri + '\n' +
    #    get_canonical_query_string + '\n' +
    #    get_canonical_headers + '\n' +
    #    get_list_signed_headers + '\n' +
    #    HexEncode(Hash(RequestPayload))
    def _get_canonical_request(self, r: _Request, signed_headers: list):
        canonical_headers = self._get_canonical_headers(r, signed_headers)
        hexencode = self._find_header(r, HEADER_CONTENT_SHA256)
        if hexencode is None:
            hexencode = self._hex_encode_sha256_hash(r.body)

        return "%s\n%s\n%s\n%s\n%s\n%s" % (
            r.method.upper(),
            self._get_canonical_uri(r),
            self._get_canonical_query_string(r),
            canonical_headers,
            ";".join(signed_headers),
            hexencode,
        )

    def _get_canonical_uri(self, r: _Request):
        pattens = unquote(r.uri).split("/")
        uri = [self._urlencode(v) for v in pattens]
        urlpath = "/".join(uri)
        if urlpath[-1] != "/":
            urlpath = urlpath + "/"  # always end with /
        return urlpath

    def _get_canonical_query_string(self, r: _Request):
        keys = [key for key in r.query]
        keys.sort()

        a = []
        for key in keys:
            k = self._urlencode(key)
            value = r.query[key]
            if type(value) is list:
                value.sort()
                for v in value:
                    kv = k + "=" + self._urlencode(str(v))
                    a.append(kv)
            else:
                kv = k + "=" + self._urlencode(str(value))
                a.append(kv)

        return "&".join(a)

    @staticmethod
    def _get_canonical_headers(r: _Request, signed_headers: list):
        a = []
        __headers = {}
        for key in r.headers:
            key_encoded = key.lower()
            value_encoded = r.headers[key].strip()
            __headers[key_encoded] = value_encoded
            r.headers[key] = value_encoded.encode("utf-8").decode("iso-8859-1")
        for key in signed_headers:
            a.append(key + ":" + __headers[key])
        return "\n".join(a) + "\n"

    @staticmethod
    def _get_list_signed_headers(r: _Request):
        a = []
        for key in r.headers:
            a.append(key.lower())
        a.sort()
        return a

    @staticmethod
    def _hex_encode_sha256_hash(data: bytes):
        sha256 = hashlib.sha256()
        sha256.update(data)
        return sha256.hexdigest()

    # Create a "String to Sign".
    def _get_string_to_sign(self, canonical_request: str, t: datetime):
        to_bytes = self._hex_encode_sha256_hash(canonical_request.encode("utf-8"))
        return "%s\n%s\n%s" % (ALGORITHM, datetime.strftime(t, BASIC_DATE_FORMAT), to_bytes)

    # Create the HWS Signature.
    # @staticmethod
    def _sign_string_to_sign(self, string_to_sign: str, signing_key: str):
        hm = self._hmacsha256(signing_key, string_to_sign)
        return binascii.hexlify(hm).decode()

    # Get the finalized value for the "Authorization" header.  The signature
    # parameter is the output from SignStringToSign
    @staticmethod
    def _auth_header_value(signature: str, app_key: str, signed_headers: list):
        return "%s Access=%s, SignedHeaders=%s, Signature=%s" % (
            ALGORITHM,
            app_key,
            ";".join(signed_headers),
            signature,
        )

    @staticmethod
    def _hmacsha256(key_byte: str, message: str):
        return hmac.new(key_byte.encode("utf-8"), message.encode("utf-8"), digestmod=hashlib.sha256).digest()

    @staticmethod
    def _urlencode(s: str):
        return quote(s, safe="~")

    @staticmethod
    def _find_header(r: _Request, header: str):
        for k in r.headers:
            if k.lower() == header.lower():
                return r.headers[k]
        return None


def sign(key: str, secret: str, method: str, url: Union[str, URL], headers: Dict = None, body: Dict = None):
    sig = Signer(key=key, secret=secret)

    r = _Request(method=method, url=url, headers=headers, body=body)
    sig.signer(r)

    return r.headers


__all__ = ("sign",)
