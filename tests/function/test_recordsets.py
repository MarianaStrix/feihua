from http import HTTPStatus

import pytest

from feihua.recordset import SUCCESSFUL_STATUS_CODE, Recordset, Recordsets
from tests.identical import identical


@pytest.mark.parametrize(
    "name_data, status",
    [
        (
            "data_list_recordsets",
            HTTPStatus.ACCEPTED,
        ),
        (
            "data_list_recordsets",
            HTTPStatus.INTERNAL_SERVER_ERROR,
        ),
        (
            "data_list_empty",
            HTTPStatus.OK,
        ),
    ],
)
@pytest.mark.asyncio
async def test_return_list_objects(data_recordsets_function, name_data, status):
    recordsets, returned_status = await Recordsets._return_list_objects(data_recordsets_function[name_data], status)
    if status in SUCCESSFUL_STATUS_CODE:
        assert isinstance(recordsets["recordsets"], list)
        for recordset in recordsets["recordsets"]:
            assert isinstance(recordset, Recordset)
            assert recordset.to_dict() in data_recordsets_function[name_data]["recordsets"]
    else:
        assert recordsets == data_recordsets_function[name_data]


@pytest.mark.parametrize(
    "name_data, status, error",
    [
        ("data_single_recordset", HTTPStatus.OK, False),
        ("data_single_recordset", HTTPStatus.INTERNAL_SERVER_ERROR, False),
    ],
)
@pytest.mark.asyncio
async def test_return_single_object(data_recordsets_function, name_data, status, error):
    rec, returned_status = await Recordsets._return_single_object(data_recordsets_function[name_data], status)
    if error:
        with pytest.raises(error):
            await Recordsets._return_single_object(data_recordsets_function[name_data], status)
    elif returned_status in SUCCESSFUL_STATUS_CODE:
        assert isinstance(rec, Recordset)
        assert identical(rec, data_recordsets_function[name_data])
    else:
        assert rec == {}
