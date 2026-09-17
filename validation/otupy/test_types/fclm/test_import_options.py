import pytest
import parametrize_from_file
from otupy.profiles.fclm.data.import_options import ImportOptions
from otupy.types.data.duration import Duration


@parametrize_from_file("parameters/test_import_options.yml")
def test_good_import_options(options):
    parsed = {k: (Duration(v) if isinstance(v, int) else v) for k, v in options.items()}
    obj = ImportOptions(**parsed)
    assert isinstance(obj, ImportOptions)


@parametrize_from_file("parameters/test_import_options.yml")
def test_bad_import_options(bad_options):
    with pytest.raises(Exception):
        parsed = {k: (Duration(v) if isinstance(v, int) else v) for k, v in bad_options.items()}
        ImportOptions(**parsed)
