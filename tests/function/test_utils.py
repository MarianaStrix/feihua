import pytest

from feihua.utils import parse_content_type


@pytest.mark.parametrize(
    "content_type, main_type, sub_type, option, error",
    [
        ("text/plain", "text", "plain", {}, False),
        ("text/plain; charset=utf-8", "text", "plain", {"charset": "utf-8"}, False),
        ("text/plain; ", "text", "plain", {}, False),
        ("textplain", "textplain", "", {}, ValueError),
        ("text/plain; asd", "text", "plain", {}, ValueError),
    ],
)
@pytest.mark.asyncio
def test_parse_content_type(content_type, main_type, sub_type, option, error):
    if error:
        with pytest.raises(error):
            parse_content_type(content_type)
    else:
        mt, st, opts = parse_content_type(content_type)
        assert mt == main_type
        assert st == sub_type
        assert opts == option
