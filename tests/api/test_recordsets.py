from http import HTTPStatus
from unittest import mock

import pytest

from feihua.exceptions import ClientError
from feihua.recordset import Recordset
from tests.identical import identical


@pytest.mark.parametrize(
    "name_data, expected_status",
    [
        (
            "data_list_right",
            HTTPStatus.ACCEPTED,
        ),
        (
            "data_list_empty",
            HTTPStatus.OK,
        ),
    ],
)
@pytest.mark.asyncio
async def test_api_list(client, data_recordsets, name_data, expected_status):

    with mock.patch("feihua.client.Client._query_json") as mock_do_query:
        mock_do_query.return_value = (data_recordsets[name_data], expected_status)
        response, status_code = await client.recordsets.list(zone_id="example")
        assert identical(response, data_recordsets[name_data])
        assert status_code == expected_status


@pytest.mark.parametrize(
    "name_data, expected_status, error",
    [
        ("right_record", HTTPStatus.ACCEPTED, False),
        (
            "repeat_name",
            HTTPStatus.BAD_REQUEST,
            "Attribute 'name' conflicts with Record Set 'example.c.sbauto.tech.' type 'A'.",
        ),
    ],
)
@pytest.mark.asyncio
async def test_api_create_record(client, data_recordsets, name_data, expected_status, error):
    received_data = data_recordsets["data_for_create_record"][name_data]["received"]

    if error:
        with mock.patch(
            "feihua.client.Client._do_query",
            side_effect=ClientError(status=expected_status, data={"message": error}),
        ):
            with pytest.raises(ClientError) as excinfo:
                await client.recordsets.create_record(
                    zone_id="example",
                    data=received_data,
                )
            assert excinfo.value.message == error
            assert excinfo.value.status == expected_status
    else:
        expected_data = data_recordsets["data_for_create_record"][name_data]["expected"]

        with mock.patch("feihua.client.Client._query_json") as mock_do_query:
            mock_do_query.return_value = (expected_data, expected_status)
            response, status_code = await client.recordsets.create_record(
                zone_id="8a9487e17432ccb70175276848636135", data=received_data
            )
            assert status_code == expected_status
            assert identical(response, expected_data)
            assert isinstance(response, Recordset)
            for item in received_data:
                if item in expected_data:
                    assert identical(expected_data[item], received_data[item])


@pytest.mark.parametrize(
    "name_data, expected_status, error",
    [
        (
            "repeat_name",
            HTTPStatus.BAD_REQUEST,
            "Attribute 'name' is invalid, record set name must be ended with this zone name.",
        ),
        (
            "empty_data",
            HTTPStatus.BAD_REQUEST,
            "Attribute 'name' is invalid, record set name should be non-empty.",
        ),
    ],
)
@pytest.mark.asyncio
async def test_api_create_record_bad_data(client, data_recordsets, name_data, expected_status, error):
    received_data = data_recordsets["data_for_create_record"][name_data]["received"]

    with mock.patch(
        "feihua.client.Client._do_query",
        side_effect=ClientError(status=expected_status, data={"message": error}),
    ):
        with pytest.raises(ClientError) as excinfo:
            await client.recordsets.create_record(
                zone_id="example",
                data=received_data,
            )
        assert excinfo.value.message == error
        assert excinfo.value.status == expected_status


@pytest.mark.parametrize(
    "name_data, expected_status",
    [
        ("change_record", HTTPStatus.ACCEPTED),
        ("empty_data", HTTPStatus.ACCEPTED),
    ],
)
@pytest.mark.asyncio
async def test_api_update_record(client, data_recordsets, name_data, expected_status):
    expected_data = data_recordsets["data_for_update_record"][name_data]["expected"]
    received_data = data_recordsets["data_for_update_record"][name_data]["received"]

    with mock.patch("feihua.client.Client._query_json") as mock_do_query:
        mock_do_query.return_value = (expected_data, expected_status)
        response, status_code = await client.recordsets.update_record(
            zone_id="example", recordset_id="example_id", data=received_data
        )
        assert status_code == expected_status
        assert identical(response, expected_data)
        assert isinstance(response, Recordset)
        for item in expected_data:
            if item in received_data:
                assert identical(expected_data[item], received_data[item])


@pytest.mark.parametrize(
    "name_data, expected_status, error",
    [
        (
            "change_ip_is_invalid",
            HTTPStatus.BAD_REQUEST,
            "Attribute 'records' is invalid. When type is 'A', records should be ipv4 address list",
        ),
    ],
)
@pytest.mark.asyncio
async def test_api_update_record_bad_data(client, data_recordsets, name_data, expected_status, error):
    received_data = data_recordsets["data_for_update_record"][name_data]["received"]
    with mock.patch(
        "feihua.client.Client._do_query",
        side_effect=ClientError(status=expected_status, data={"message": error}),
    ):
        with pytest.raises(ClientError) as excinfo:
            await client.recordsets.update_record(zone_id="example", recordset_id="example", data=received_data)
        assert excinfo.value.message == error
        assert excinfo.value.status == expected_status


@pytest.mark.parametrize(
    "name_data, expected_status, error",
    [
        (
            "change_name",
            HTTPStatus.BAD_REQUEST,
            "Attribute 'name' is immutable.",
        ),
    ],
)
@pytest.mark.asyncio
async def test_api_update_record_bad_data(client, data_recordsets, name_data, expected_status, error):
    received_data = data_recordsets["data_for_update_record"][name_data]["received"]

    with pytest.raises(ClientError) as excinfo:
        await client.recordsets.update_record(zone_id="example", recordset_id="example", data=received_data)
    assert excinfo.value.message == error
    assert excinfo.value.status == expected_status


@pytest.mark.parametrize(
    "name_data, expected_status, error",
    [
        ("delete_exist_id", HTTPStatus.ACCEPTED, None),
        (
            "delete_not_exist_id",
            HTTPStatus.BAD_REQUEST,
            "This record set does not exist.",
        ),
    ],
)
@pytest.mark.asyncio
async def test_api_delete_record(client, data_recordsets, name_data, expected_status, error):
    if not error:
        expected_data = data_recordsets["data_for_delete_record"][name_data]["expected"]
        with mock.patch("feihua.client.Client._query_json") as mock_do_query:
            mock_do_query.return_value = (expected_data, expected_status)
            response, status_code = await client.recordsets.delete_record(zone_id="example", recordset_id="example")
            assert status_code == expected_status
            assert identical(response, expected_data)
            assert isinstance(response, Recordset)
            assert response.status == "PENDING_DELETE"
    else:
        with mock.patch(
            "feihua.client.Client._do_query",
            side_effect=ClientError(status=expected_status, data={"message": error}),
        ):
            with pytest.raises(ClientError) as excinfo:
                await client.recordsets.delete_record(zone_id="example", recordset_id="example")

            assert excinfo.value.message == error
            assert excinfo.value.status == expected_status


@pytest.mark.parametrize(
    "name_data, expected_status",
    [
        (
            "data_for_find_records",
            HTTPStatus.ACCEPTED,
        ),
        (
            "data_list_empty",
            HTTPStatus.OK,
        ),
    ],
)
@pytest.mark.asyncio
async def test_api_find_recordets(client, data_recordsets, name_data, expected_status):

    with mock.patch("feihua.client.Client._query_json") as mock_do_query:
        mock_do_query.return_value = (data_recordsets[name_data], expected_status)
        query = {"id": "example"}
        response, status_code = await client.recordsets.find_records(zone_id="example", query=query)
        assert identical(response, data_recordsets[name_data])
        assert status_code == expected_status
