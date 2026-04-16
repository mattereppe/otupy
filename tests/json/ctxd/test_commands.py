from jsonschema import validate
import json

import pytest
import parametrize_from_file

from helpers import load_json

command_path_good = "tests/commands/good"
command_path_bad = "tests/commands/bad"

command_path_schema = "openc2-json-schema/cmd_ctxd.json"


@pytest.mark.parametrize("cmd", load_json(command_path_good) )
def test_good_parameters(cmd):
	with open(command_path_schema,'r') as f:
		schema = json.loads(f.read())
	validate(instance=cmd, schema=schema)

@pytest.mark.parametrize("cmd", load_json(command_path_bad) )
def test_bad_parameters(cmd):
	with open(command_path_schema,'r') as f:
		schema = json.loads(f.read())
	with pytest.raises(Exception):
		validate(instance=cmd, schema=schema)
