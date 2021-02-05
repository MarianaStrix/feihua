from typing import Dict, List

SUCCESSFUL_STATUS_CODE = (200, 202, 204)


class Recordset:
    """Recordset Resource"""

    def __init__(
            self,
            id: str,
            zone_id: str,
            name: str,
            description: str,
            type: str,
            ttl: int,
            records: List[str],
            status: str,
            zone_name: str,
            default: bool,
            links: Dict,
            project_id: str,
            create_at: str,
            update_at: str,
    ):
        # The id if recordset
        self.id = id
        #: Properties
        #: The id of the Zone which this recordset belongs to
        self.zone_id = zone_id
        #: Recordset name
        self.name = name
        #: Recordset description
        self.description = description
        #: DNS type of the recordset
        #: Valid values include ``A``, ``AAA``, ``MX``, ``CNAME``, ``TXT``, ``NS``
        self.type = type
        #: Time to live, default 300, available value 300-2147483647 (seconds)
        self.ttl = ttl
        #: DNS record value list
        self.records = records
        #: Recordset status
        #: Valid values include ``PENDING_CREATE``, ``ACTIVE``,
        #:                       ``PENDING_DELETE``, ``ERROR``
        self.status = status
        #: The name of the Zone which this recordset belongs to
        self.zone_name = zone_name
        #: Is the recordset created by system.
        self.default = default

        #: Links contains a `self` pertaining to this zone or a `next` pertaining
        #: to next page
        self.links = links
        #: ID of the project which the recordset belongs to
        self.project_id = project_id
        #: Timestamp when the zone was created
        self.create_at = create_at
        #: Timestamp when the zone was last updated
        self.update_at = update_at

    def to_dict(self):
        return vars(self)


class Recordsets:
    """Recordsets resource represent list all recordset API response"""

    base_path = "/zones/{zone_id}/recordsets"
    api_version = "/v2"

    def __init__(self, client) -> None:
        self.client = client

    async def list(self, zone_id: str):
        """
        List of images
        """
        response, status_code = await self.client._query_json(
            api_version=self.api_version,
            path=self.base_path.format(zone_id=zone_id),
            method="GET",
        )
        return await self._return_list_objects(response, status_code)

    async def create_record(self, zone_id: str, data: Dict):
        response, status_code = await self.client._query_json(
            api_version=self.api_version,
            path=self.base_path.format(zone_id=zone_id),
            method="POST",
            data=data,
        )
        return await self._return_single_object(response, status_code)

    async def update_record(self, zone_id: str, recordset_id: str, data: Dict):
        response, status_code = await self.client._query_json(
            api_version=self.api_version,
            path=self.base_path.format(zone_id=zone_id) + "/" + recordset_id,
            method="PUT",
            data=data,
        )
        return await self._return_single_object(response, status_code)

    async def delete_record(self, zone_id: str, recordset_id: str):
        response, status_code = await self.client._query_json(
            api_version=self.api_version,
            path=self.base_path.format(zone_id=zone_id) + "/" + recordset_id,
            method="DELETE",
        )
        return await self._return_single_object(response, status_code)

    async def find_records(self, zone_id: str, query: str):
        response, status_code = await self.client._query_json(
            api_version=self.api_version,
            path=self.base_path.format(zone_id=zone_id),
            query=query,
            method="GET",
        )
        return await self._return_list_objects(response, status_code)

    @staticmethod
    async def _return_single_object(response, status_code):
        if status_code in SUCCESSFUL_STATUS_CODE:
            response = Recordset(**response)
        return response, status_code

    @staticmethod
    async def _return_list_objects(response, status_code):
        if status_code in SUCCESSFUL_STATUS_CODE:
            recordsets = response["recordsets"]
            if recordsets:
                recordsets = [Recordset(**record) for record in recordsets]
                response["recordsets"] = recordsets
        return response, status_code

