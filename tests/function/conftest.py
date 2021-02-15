import json
import os

import pytest

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture
def data_recordsets_function():
    with open(os.path.join(ROOT_DIR, "data/function_recordsets_data.json")) as f:
        return json.load(f)
