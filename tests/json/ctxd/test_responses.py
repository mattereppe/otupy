from jsonschema import validate
import json

import pytest
import parametrize_from_file

from helpers import load_json

response_path_good = "tests/responses/good"
response_path_bad = "tests/responses/bad"

response_path_schema = "openc2-json-schema/rsp_ctxd.json"

@pytest.mark.parametrize("cmd", load_json(response_path_good) )
def test_good_parameters(cmd):
	with open(response_path_schema,'r') as f:
		schema = json.loads(f.read())
	validate(instance=cmd, schema=schema)

@pytest.mark.parametrize("cmd", load_json(response_path_bad) )
def test_bad_parameters(cmd):
	with open(response_path_schema,'r') as f:
		schema = json.loads(f.read())
	with pytest.raises(Exception):
		validate(instance=cmd, schema=schema)
