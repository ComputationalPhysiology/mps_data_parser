import yaml

from mps_data_parser import MPSData
from mps_data_parser import abreviations as ab

TEST_ABREV_FILE = "test_abrev_file.yaml"
# shutil.copy(ab.ABREV_FILE, TEST_ABREV_FILE)
DATA = ab.GENERAL_ABBREVIATIONS
with open(TEST_ABREV_FILE, "w") as f:
    yaml.dump(DATA, f)


def test_mps_data():
    abrev = ab.Abbreviations(filename=TEST_ABREV_FILE, raise_on_failure=False)
    drug = "TestDrug"
    drug_synonyms = ["Test", "test", "test_drug"]
    abrev.add_value("drug", drug, synonyms=drug_synonyms)

    chip = "TestChip"
    new_argument = "TestArgument"

    folder = "TestFolder"
    path = "test_path"

    mps_data = MPSData(
        folder=folder,
        path=path,
        chip=chip,
        new_argument=new_argument,
        drug=drug_synonyms[-1],
        abrev=abrev,
    )
    assert mps_data.drug == drug
    assert mps_data.chip == chip
    assert mps_data.new_argument == new_argument


if __name__ == "__main__":
    test_mps_data()
