import logging
import re
from pathlib import Path
from typing import Any, Dict, Optional, Union

import parse

from .abreviations import Abbreviations
from .mps_data import MPSData

logger = logging.getLogger(__name__)

PathStr = Union[str, Path]

VOLTAGE_CHANNELS = ["Red", "berst", "volt"]
CALCIUM_CHANNELS = ["Cyan", "gcamp"]
BF_CHANNELS = ["BF", "bf", "brightfield"]

TRACE_TYPES = ["voltage", "calcium", "brightfield"]


def channel_to_trace_type(channel: Optional[str]) -> Optional[str]:

    if channel in VOLTAGE_CHANNELS:
        return TRACE_TYPES[0]
    elif channel in CALCIUM_CHANNELS:
        return TRACE_TYPES[1]
    elif channel in BF_CHANNELS:
        return TRACE_TYPES[2]
    else:
        return None


class PathMatcher:
    """Base class for retrieving information about an experiment from the path

    Arguments
    ---------
    config : dict
        A dictionary with information about the experiment that
        you want to analyze.
    root : str
        A path to the root directory of the experiment
    strict : bool
        If set to True (default) then a path need to by matched with
        a regex given in the config file. If there is not match then
        it will raise a RuntimeError. If set to False then no exception
        will be raised, but all field will end up being None.
    abrev_file : str
        Path to a file with abbrevieations
    additional_abbreviations : dict
        A dictionary on the same for as the abbreviation file. If both the
        `abrev_file` and this dictionary is provided and they have conflicting
        keys, then this dictionary will win.
    """

    def __init__(
        self,
        config: Dict[str, Any],
        root: PathStr = "",
        strict: bool = True,
        abrev_file: Optional[PathStr] = None,
        additional_abbreviations: Optional[Dict[str, Any]] = None,
    ):

        self.root = Path(root)
        self._strict = strict
        self.folder = self.root.name
        self._operator = config.get("operator")
        self._regexs = config.get("regexs", [])
        self._rules = config.get("rules", [])
        self.excludes = config.get("excludes", [])
        self._config = config.copy()
        self.abrev = Abbreviations(
            data=additional_abbreviations, filename=abrev_file, raise_on_failure=False
        )
        if additional_abbreviations is not None:
            self.abrev.update(additional_abbreviations)

        try:
            self._extension = Path(self._regexs[0]).suffix
        except Exception:
            self._extension = ""

        # All keys for all regexes
        self._keys = [
            tuple(
                parse.search(
                    re.sub("\:(.*?)\}", "}", r),  # noqa: W605
                    re.sub("\:(.*?)\}", "}", r),  # noqa: W605
                ).named.keys()
            )
            for r in self._regexs
        ]
        # List of only the unique keys
        self._unique_keys = set([item for sublist in self._keys for item in sublist])
        # Keys that are not in all regexes
        self._diffs = [set(self._unique_keys).difference(set(k)) for k in self._keys]

    @staticmethod
    def _check_rule(rule: str, result: Dict[str, Any]) -> bool:
        """
        Since we allow the user to provide code that is executed, we
        need to be careful with what is provided.
        """
        # We cannot allow imports
        if "import" in rule:
            return False
        for k, v in result.items():
            if "import" in str(k):
                return False
            if "import" in str(v):
                return False

        return True

    def __call__(self, path: PathStr) -> MPSData:

        relative_path = Path(path).relative_to(self.root)
        result: Dict[str, Optional[str]] = {
            "path": relative_path.as_posix(),
            "folder": self.folder,
            "operator": self._operator,
            "extension": relative_path.suffix,
        }

        for regex, diff in zip(self._regexs, self._diffs):
            res = parse.search(regex, str(relative_path))
            if res is not None:
                result.update(res.named)
                for d in diff:
                    # Set this to the string none to indicate
                    # that this key is missing
                    result[d] = "none"

                if self._rules != []:

                    for r in self._rules:

                        if PathMatcher._check_rule(r, result):
                            exec(r, result)
                            result.pop("__builtins__")
                        else:
                            logger.warning(f"Rule {r} is not safe")
                break

        else:
            # We could not find a match for the given path
            if self._strict:
                msg = (
                    f"No match where found for path {path}, with relative path "
                    f"{relative_path}, and the following regexes: \n"
                )
                msg += "\n".join(self._regexs)
                raise RuntimeError(msg)

        result["trace_type"] = channel_to_trace_type(result.get("channel"))

        for key in MPSData.arguments():
            if key not in result:
                # Check if this is set in the cofig, and set
                # to None otherwise
                result[key] = self._config.get(key, None)

        # Pack this into the MPSData object
        logger.debug(f"Raw data: \n {result}")
        cleaned_data = MPSData(**result, abrev=self.abrev)  # type: ignore
        logger.debug(f"Clean data: \n{cleaned_data.to_dict()}")

        return cleaned_data
