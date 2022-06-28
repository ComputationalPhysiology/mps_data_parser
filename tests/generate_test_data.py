import shutil
from itertools import product
from pathlib import Path
from typing import Any
from typing import Dict
from typing import List
from typing import Union

import yaml

PathStr = Union[Path, str]

HERE = Path(__file__).absolute().parent


class SeqNr:
    """Dummy class that can be used an infinite counter"""

    def __init__(self):
        self.n = -1

    def __next__(self):
        self.n += 1
        # Yield 4 digit number with zeros filled in front
        return str(self.n).zfill(4)

    def __iter__(self):
        return self


CONTENT = {
    "190820_Ver_Alf_SCVI273_direct": {
        "date": [190820],
        "dose": ["no dose", "1uM"],
        "pacing_frequency": ["1Hz", "spont"],
        "chip": ["1A", "3B"],
        "media": ["SM", "MM"],
        "drug": ["Alf", "Ver"],
        "channel": ["Red", "Cyan"],
    },
    "181113_Isoproterenol_SCVi20": {
        "date": [181113],
        "dose": ["0nM", "1nM"],
        "pacing_frequency": ["1Hz", "0Hz"],
        "chip": ["2a", "3a"],
        "media": ["SM", "MM"],
        "channel": ["Red", "Cyan"],
        "roi": ["VC"],
        "control": ["Ctrl"],
    },
    "181116_Lidocaine": {
        "date": [181116],
        "dose": ["0uM", "1uM", "10uM"],
        "pacing_frequency": ["1Hz", "0Hz"],
        "chip": ["1A", "2A", "1B"],
        "media": ["SM", "MM"],
        "channel": ["Red", "Cyan"],
        "roi": ["VC"],
        "control": ["Ctrl"],
    },
}


def copy_data_traces(channel, dst):
    calcium_data = HERE.joinpath("example_traces/calcium_data.npy")
    voltage_data = HERE.joinpath("example_traces/voltage_data.npy")

    channel_to_data = {"Red": voltage_data, "Cyan": calcium_data}
    shutil.copy(channel_to_data[channel], dst)


def generate_data(
    config: Dict[str, Any],
    content: Dict[str, List[str]],
    data_dir: PathStr,
    config_dir: PathStr,
):

    data_dir = Path(data_dir)
    config_dir = Path(config_dir)
    data_dir.mkdir(exist_ok=True, parents=True)
    config_dir.mkdir(exist_ok=True, parents=True)

    folder = data_dir.joinpath(config["folder"])
    for path_str in config["regexs"]:
        for p, seq_nr in zip(product(*list(content.values())), SeqNr()):
            params = dict(zip(content.keys(), p))
            params["seq_nr"] = seq_nr

            path = folder.joinpath(path_str.format(**params))
            # Create directory
            path.parent.mkdir(exist_ok=True, parents=True)
            # Create empty file
            path.touch()

            # Create directory to store data
            outdir = path.parent.joinpath(path.stem)
            outdir.mkdir(exist_ok=True)

            copy_data_traces(params["channel"], outdir.joinpath("data.npy"))

    # Dump config file
    with open(config_dir.joinpath(f"{config['folder']}.yaml"), "w") as f:
        yaml.dump(config, f)


def get_original_config(folder):
    with open(f"../config_files/{folder}.yaml", "r") as f:
        d = yaml.load(f, Loader=yaml.SafeLoader)
    return d


def main():

    main_dir = Path("test_data")
    data_dir = main_dir.joinpath("data")
    config_dir = main_dir.joinpath("config")

    config_dir.mkdir(exist_ok=True, parents=True)

    for folder, content in CONTENT.items():
        config = get_original_config(folder)
        generate_data(config, content, data_dir, config_dir)


if __name__ == "__main__":
    main()
