from typing import Mapping, Tuple


async def parse_result(response, response_type=None, *, encoding="utf-8"):
    """
    Convert the response to native objects by the given response type
    or the auto-detected HTTP content-type.
    It also ensures release of the response object.
    """
    if response_type is None:
        ct = response.headers.get("content-type")
        if ct is None:
            cl = response.headers.get("content-length")
            if cl is None or cl == "0":
                return ""
            raise TypeError(
                "Cannot auto-detect response type "
                "due to missing Content-Type header."
            )
        main_type, sub_type, extras = parse_content_type(ct)
        if sub_type == "json":
            response_type = "json"
        # left as an example
        # elif sub_type == "x-tar":
            # response_type = "tar"
        elif (main_type, sub_type) == ("text", "plain"):
            response_type = "text"
            encoding = extras.get("charset", encoding)
        else:
            raise TypeError("Unrecognized response type: {ct}".format(ct=ct))
    # left as an example
    # if "tar" == response_type:
    #     what = await response.read()
    #     return tarfile.open(mode="r", fileobj=BytesIO(what))
    if "json" == response_type:
        data = await response.json(encoding=encoding)
    elif "text" == response_type:
        data = await response.text(encoding=encoding)
    else:
        data = await response.read()
    return data


def parse_content_type(ct: str) -> Tuple[str, str, Mapping[str, str]]:
    """
    Decompose the value of HTTP "Content-Type" header into
    the main/sub MIME types and other extra options as a dictionary.
    All parsed values are lower-cased automatically.
    """
    pieces = ct.split(";")
    try:
        main_type, sub_type = pieces[0].split("/")
    except ValueError:
        msg = 'Invalid mime-type component: "{0}"'.format(pieces[0])
        raise ValueError(msg)
    if len(pieces) > 1:
        options = {}
        for opt in pieces[1:]:
            opt = opt.strip()
            if not opt:
                continue
            try:
                k, v = opt.split("=", 1)
            except ValueError:
                msg = 'Invalid option component: "{0}"'.format(opt)
                raise ValueError(msg)
            else:
                options[k.lower()] = v.lower()
    else:
        options = {}
    return main_type.lower(), sub_type.lower(), options


class _AsyncCM:
    __slots__ = ("_coro", "_resp")

    def __init__(self, coro):
        self._coro = coro
        self._resp = None

    async def __aenter__(self):
        resp = await self._coro
        self._resp = resp
        return await resp.__aenter__()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return await self._resp.__aexit__(exc_type, exc_val, exc_tb)
