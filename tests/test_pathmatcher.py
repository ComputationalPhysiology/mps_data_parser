from pathlib import Path

import pytest

from mps_data_parser import PathMatcher

config = {
    "folder": "190820_Ver_Alf_SCVI273_direct",
    "regexs": [
        "{date}_{dose}_{pacing_frequency}/Point12/Point{chip}_{media}_{drug}_Channel{channel}_VC_Seq{seq_nr}.nd2",
        "{date}_{dose}_{pacing_frequency}/Point{chip}_{media}_{drug}_Channel{channel}_VC_Seq{seq_nr}.nd2",
    ],
    "operator": "John_Dose",
}

attributes = dict(
    date="190820",
    dose="0nM",
    pacing_frequency="paced",
    chip="1A",
    media="MM",
    drug="Alf",
    channel="Red",
    seq_nr="0001",
)
folder = Path(config["folder"])  # type: ignore
example_path = folder.joinpath(str(Path(config["regexs"][0])).format(**attributes))
test_data = attributes.copy()
test_data.update(  # type: ignore
    folder=str(folder),
    path=str(example_path.relative_to(folder)),
    trace_type="voltage",
    operator=config["operator"],
    extension=example_path.suffix,
)


def test_path_matcher():

    pathmatcher = PathMatcher(config, root=folder, strict=True)
    data = pathmatcher(example_path)

    # Check that all data items are correct
    for k, v in data.to_dict().items():

        attr = test_data.get(k)
        value = pathmatcher.abrev.get_name(k, attr) or attr

        assert v == value

    # Check that we did not miss any attributes
    for k, attr in attributes.items():
        v = data.get(k)
        value = pathmatcher.abrev.get_name(k, attr) or attr
        assert value == v


def test_path_matcher_with_diffs():

    funky_regex = "{date}_{dose}_{pacing_frequency}/Point{chip}_{media}_{roi}_Channel{channel}_VC_Seq{seq_nr}.nd2"
    config["regexs"].append(funky_regex)
    pathmatcher = PathMatcher(config, root=folder, strict=True)
    data = pathmatcher(example_path)
    assert data.roi == "none"


def test_path_matcher_raises_RuntimeError():

    config_ = config.copy()
    config_["regexs"] = ["regex1", "regex2"]
    pathmatcher = PathMatcher(config_, root=folder, strict=True)
    with pytest.raises(RuntimeError):
        pathmatcher(example_path)


if __name__ == "__main__":
    # test_path_matcher()
    test_path_matcher_with_diffs()
    # test_path_matcher_raises_RuntimeError()
