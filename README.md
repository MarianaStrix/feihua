## Feihua
___________
#### What is it?
Huawei Cloud API async client. 

Example of use:
```Python
from feihua.client import Client
access_key_id = "EXAMPLE_ACCESS_KEY_ID"
secret_access_key = "EXAMPLE_SECRET_ACCESS_KEY"
host = "dns.region.hc.sbercloud.ru"
zone_id = "EXAMPLE_ID"
client = Client(access_key_id=access_key_id, secret_access_key=secret_access_key, host=host)

# return list recordsets in zone
data_response, code_status = await client.recordsets.list(zone_id=zone_id)

# return created recordset in zone
data = {
    "name": "example6.com.c.sbauto.tech.",
    "type": "A",
    "records": [
        "10.200.200.116",
    ],
}
data_response, code_status = await client.recordsets.create_record(zone_id=zone_id, data=data)

# return updated recordset in zone
recordset_id = "example_id"
data_update = {
    "records": [
        "10.200.200.114",
    ],
}

data_response, code_status = await client.recordsets.update_record(zone_id=zone_id, recordset_id=recordset_id, data=data_update)

# return deleted recordset in zone
data_response, code_status = await client.recordsets.delete_record(zone_id=zone_id, recordset_id=recordset_id)

# return recordset in zone
query = {
    "id": "8a9487e17432ccb701776d23acff776a"
}
data_response, code_status = await client.recordsets.find_records(zone_id=zone_id, query=query)
```

#### Poetry

[Poetry Documentation](https://python-poetry.org/docs/)

Poetry is python package manager.

Poetry resolve dependencies and conflicts in package and make it fast.

Installation

 - `curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -`
 - `source $HOME/.poetry/env`

Basic usage

 - `poetry lock` lock dependencies
 - `poetry update` lock, update and install dependencies
 - `poetry install` for install dependencies from pyproject.toml
 - `poetry install --no-dev` for install dependencies without dev
 - `poetry add <package>` for adding dependency with check on conflicts
 - `poetry remove <package>` for remove
 - `poetry self update` literally
 
If not set explicitly (default), `poetry` will use the virtualenv from the `.venv` directory when one is available. If set to `false`, `poetry` will ignore any existing `.venv` directory.

#### Poetry Dynamic Versioning

__Seems like bump version script__

The tool use git tag for setting version to `__verison__.py` and `__init__.py`
Poetry Dynamic Versioning need to be installed to system python environment cause `Poetry` can't see himself from `venv`.
Poetry Dynamic Versioning triggered by `poetry build` and make package with replaced version vars.

- `pip install poetry-dynamic-versioning` # globally

How to bump the version of the library?
1. Set git tag `git tag 0.1.0 -m "Initial project"`
2. Dump version `poetry-dynamic-versioning`
3. Create distribution archives `poetry build`
4. Push tag in project `git push --tags`
5. Load package to pypi:
    1. Download and install certificates from https://atlas.swec.sbercloud.ru/bitbucket/projects/INFRA/repos/ssl-ca/browse
    2. Create common pem file: `cat sat-root.crt sat-external-ca.crt > sat_pypi.pem`
    3. Connect to VPN
    4. Set the path to the certificate in poetry.toml certificates.feihua.cert = <absolute_path_cert>
    5. Load packege`poetry publish -r feihua`

#### Pre-commit

[Pre-Commit Documentation](https://pre-commit.com/)

Pre-commit hooks apply rules from `.pre-commit-config.yml`

- `pre-commit install` activate hooks
- `pre-commit autoupdate` update hooks (if you know what you do)
- `git commit -m "<message>" -n` where __**-n**__ is for skip hooks (if you really know what you do)

