import pytest

from feihua import signer


@pytest.mark.parametrize(
    "key, secret, method, url, headers, body, signed_headers, signature",
    [
        (
            "example",
            "example",
            "GET",
            "http://example.com/",
            {"X-Sdk-Date": "20200608T023900Z"},
            None,
            "content-type;host;x-sdk-date",
            "e1f326723bc7bfede577728dad6de64d169b3f4520d4a31d2a19a433f203d1f1",
        ),
        (
            "example",
            "example",
            "GET",
            "http://example.com/",
            {"X-Sdk-Date": "20200608T023900Z"},
            "{'a':111}",
            "content-type;host;x-sdk-date",
            "0de507877ca4d834827d4db652a327d9404484e8f090a400b5d9630c7f59815e",
        ),
        (
            "example",
            "example",
            "GET",
            "http://example.com/",
            {"X-Sdk-Date": "20200608T023900Z", "example2": "example"},
            None,
            "content-type;example2;host;x-sdk-date",
            "887736842c428a3e30d49b4ad56de69b80971fc52aec113623d642e2e9ce22d4",
        ),
    ],
)
@pytest.mark.asyncio
def test_singer(key, secret, method, url, headers, body, signed_headers, signature):
    sig = signer.Signer(key=key, secret=secret)
    r = signer._Request(method=method, url=url, headers=headers, body=body)
    sig.signer(r)
    assert (
        r.headers["Authorization"] == "SDK-HMAC-SHA256 Access=example, "
        f"SignedHeaders={signed_headers}, "
        f"Signature={signature}"
    )
