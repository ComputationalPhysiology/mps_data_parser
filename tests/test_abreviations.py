import shutil
from copy import deepcopy

import pytest
import yaml

from mps_data_parser import abreviations as ab

TEST_ABREV_FILE = "test_abrev_file.yaml"
shutil.copy(ab.ABREV_FILE, TEST_ABREV_FILE)
with open(TEST_ABREV_FILE, "r") as f:
    DATA = yaml.load(f, Loader=yaml.SafeLoader)


def get_kwargs():
    return [
        pytest.param(dict(filename=TEST_ABREV_FILE), id="file"),
        pytest.param(dict(data=deepcopy(DATA)), id="data"),
        pytest.param(
            dict(data=deepcopy(DATA), filename=TEST_ABREV_FILE), id="data+file"
        ),
    ]


def test_empty():

    abrev = ab.Abbreviations()
    abrev.add_key("drug")
    assert "drug" in abrev.keys()

    pacing = {"1Hz": ["1hz", "1 hz"], "0Hz": ["0hz", "0Hz"]}
    abrev.add_key("pacing", pacing)
    assert set(abrev.list_values("pacing")) == set(pacing.keys())


@pytest.mark.parametrize("kwargs", get_kwargs())
def test_value(kwargs):

    abrev = ab.Abbreviations(**kwargs)

    if "filename" in kwargs:
        assert abrev.is_persistent()
    else:
        assert not abrev.is_persistent()

    old_data = abrev.data
    value = "TestDrug"
    synonyms = ["Test", "test", "test_drug"]

    abrev.add_value("drug", value, synonyms=synonyms)
    data = abrev.data

    new_abrev = ab.Abbreviations(**kwargs)
    new_data = new_abrev.data

    # breakpoint()
    assert "drug" not in old_data.keys()
    assert value in data["drug"].keys()

    if abrev.is_persistent():
        assert value in new_data["drug"].keys()
        assert value in new_abrev.list_values("drug")
        assert set(new_data["drug"][value]) == set(synonyms)
        assert set(new_abrev.list_synonyms("drug", value)) == set(synonyms)
    else:
        assert "drug" not in new_data.keys()
        assert "drug" not in new_abrev.keys()

    assert value in abrev.list_values("drug")

    assert abrev.has_value("drug", value)

    assert set(data["drug"][value]) == set(synonyms)
    assert set(abrev.list_synonyms("drug", value)) == set(synonyms)

    # Now we try to remove the value
    abrev.remove_value("drug", value)
    assert not abrev.has_value("drug", value)
    assert value not in abrev.data["drug"].keys()

    if abrev.is_persistent():
        # Changes should be reflacted if we load a new file
        new_abrev = ab.Abbreviations(**kwargs)

        assert not new_abrev.has_value("drug", value)
        assert value not in new_abrev.data["drug"].keys()
        new_abrev.remove_key("drug")


@pytest.mark.parametrize("kwargs", get_kwargs())
def test_synonym(kwargs):

    abrev = ab.Abbreviations(**kwargs)
    value = "TestDrug"
    synonyms = synonyms = ["Test", "test", "test_drug"]
    abrev.add_key("drug")
    abrev.add_value("drug", value, synonyms=synonyms)

    new_synonym = "synonym"
    abrev.add_synonym("drug", value, new_synonym)
    assert new_synonym in abrev.list_synonyms("drug", value)

    if abrev.is_persistent():
        new_abrev = ab.Abbreviations(**kwargs)
        assert new_synonym in new_abrev.list_synonyms("drug", value)
    # assert value in abrev.list_values("drug")
    abrev.remove_synonym("drug", value, new_synonym)
    assert new_synonym not in abrev.list_synonyms("drug", value)

    if abrev.is_persistent():
        new_abrev = ab.Abbreviations(**kwargs)
        assert new_synonym not in new_abrev.list_synonyms("drug", value)


@pytest.mark.parametrize("kwargs", get_kwargs())
def test_duplicate_synonyms(kwargs):

    abrev = ab.Abbreviations(**kwargs)

    value = "TestDrug"
    synonyms = synonyms = ["Test", "test", "test_drug"]
    abrev.add_value("drug", value, synonyms=synonyms)

    value = "TestDrug2"
    synonyms = synonyms = ["Test", "test2", "test_drug2"]
    with pytest.raises(ab.DuplicationError) as excinfo:
        abrev.add_value("drug", value, synonyms=synonyms)

    assert "Duplicate synonym Test for key drug" in str(excinfo.value)


@pytest.mark.parametrize("kwargs", get_kwargs())
def test_get_name(kwargs):

    abrev = ab.Abbreviations(**kwargs)
    value = "TestDrug"
    synonyms = ["Test", "test", "test_drug"]

    # Test with add value
    abrev.add_value("drug", value, synonyms=synonyms)
    for synonym in synonyms:
        name = abrev.get_name("drug", synonym)
        assert name == value

    # Test with add synonym
    new_synonym = "testDrug"
    abrev.add_synonym("drug", value, new_synonym)
    assert value == abrev.get_name("drug", new_synonym)

    # Test when synonym does not exist
    syn = "no_test_drug"
    with pytest.raises(ValueError) as excinfo:
        abrev.get_name("drug", syn)
    assert f"Could not find name for key drug and synonym {syn}" == str(excinfo.value)

    abrev.raise_on_failure = False
    name = abrev.get_name("drug", syn)
    assert name is None


if __name__ == "__main__":
    # test_get_synonyms()
    # test_remove_value()
    # test_synonym()
    # test_synonym(dict(data=DATA, filename=TEST_ABREV_FILE))
    # test_duplicate_synonyms()
    # test_get_name()
    test_empty()
