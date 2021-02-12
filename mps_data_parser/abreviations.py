import logging
from collections import Counter
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml

logger = logging.getLogger(__name__)

ABREV_FILE = Path(__file__).parent.joinpath("abrev.yaml")
PathStr = Union[str, Path]


def _load_data(filename: Optional[PathStr] = None) -> Dict[str, Dict[str, List[str]]]:

    if filename is None:
        return {}
    else:
        with open(filename, "r") as f:
            d = yaml.load(f, Loader=yaml.SafeLoader)
        return d


def clean_data(
    data: Dict[str, Dict[str, List[str]]]
) -> Dict[str, Dict[str, List[str]]]:
    new_data = {}
    for key, value in data.items():
        new_data[key] = {k: sorted(list(set(v))) for k, v in value.items()}

    return new_data


def _dump_data(
    d: Dict[str, Any], filename: Optional[PathStr] = None, overwrite=False
) -> Dict[str, Dict[str, List[str]]]:
    if filename is None:
        return clean_data(d)

    if overwrite:
        data = d
    else:
        data = _load_data(filename=filename)
        data.update(d)
    # Sort alphabetically and remove duplicates
    data = clean_data(data)
    with open(filename, "w") as f:
        yaml.dump(data, f)
    return data


class DuplicationError(ValueError):
    pass


class Abbreviations:
    def __init__(
        self,
        data: Optional[Dict[str, Dict[str, List[str]]]] = None,
        filename: Optional[PathStr] = None,
        raise_on_failure: bool = True,
    ):
        self._filename = filename
        self.raise_on_failure = raise_on_failure
        self._data = _load_data(filename=filename)
        if data is not None:
            self.update(data)

    def __repr__(self):
        return f"{self.__class__.__name__}({', '.join(self.keys())})"

    def _check_key(self, key: str) -> None:
        if self.raise_on_failure:
            msg = f"Invald key {key}. Possible keys are {self.keys()}"
            assert key in self.keys(), msg

    def is_persistent(self):
        return self._filename is not None

    def keys(self) -> List[str]:
        return list(self.data.keys())

    def add_key(self, key: str, data: Optional[Dict[str, List[str]]] = None):
        """Add a new key

        Arguments
        ---------
        key : str
            The new key


        Example
        -------
        .. code::

            abrev.add_key("drug")

        """
        if key in self.keys():
            return

        if data is None:
            data = {}
        self._data[key] = {}
        self._update_data(key, data)

    def remove_key(self, key: str):
        """Remove a key

        Arguments
        ---------
        key : str
            The new key


        Example
        -------
        .. code::

            # Add a key
            abrev.add_key("drug")
            # Remove a key
            abrev.remove_key("drug")

        """
        self._check_key(key)
        self._data.pop(key)
        self._dump_data(overwrite=True)

    def update(self, data: Dict[str, Dict[str, List[str]]]) -> None:
        """Update the data in the abbreviations.
        Note that this will overwrite existing keys
        if present.

        Arguments
        ---------
        data : dict
            A dictionary with data that should
            be added to the existing data

        Example
        -------
        .. code::

            abrev.update({"drug": {
                "Lidocaine": ["Lid", "Lidocaine"],
                "Isoproterenol": ["Iso", "Isoproternol"],
                }
            })
        """
        self._data.update(data)

    @property
    def data(self) -> Dict[str, Dict[str, List[str]]]:
        # Just return a copy so that we do not change
        # anything. Dictionaries are mutable
        return deepcopy(self._data)

    def _check_unique_synonyms(self) -> None:
        """Check that there are no duplicate synonyms"""
        for key in self.keys():
            all_synonyms = [v for lst in self._data[key].values() for v in lst]
            for k, v in Counter(all_synonyms).items():
                if v > 1:
                    raise DuplicationError(f"Duplicate synonym {k} for key {key}")
            logger.debug(f"No duplicates for key {key}")

    def _update_data(
        self, key: str, data: Dict[str, Any], overwrite: bool = False
    ) -> None:
        self._data[key].update(data)
        self._data = clean_data(self._data)
        self._check_unique_synonyms()
        self._dump_data(overwrite=overwrite)

    def _dump_data(self, overwrite: bool = False):
        self._data = _dump_data(
            self._data, filename=self._filename, overwrite=overwrite
        )

    def has_value(self, key: str, value: str) -> bool:
        return value in self.list_values(key)

    def list_values(self, key: str) -> List[str]:
        self._check_key(key)
        return list(self.data.get(key, {}).keys())

    def list_synonyms(self, key: str, value: str) -> List[str]:
        self._check_key(key)
        data = self.data.get(key, {})
        values = list(data.keys())
        if value not in values:
            msg = f"Could not find value {value}. " f"Possible values are {values}"
            logger.warning(msg)
            return []

        return data.get(value, [])

    def add_synonym(self, key: str, value: str, synonym: str) -> None:
        """Add a new synonym

        Arguments
        ---------
        key : str
            The key
        value : str
            The value
        synonym : str
            The new synonym

        Example
        -------
        .. code::

            new_synonym = "Lid"
            abrev.add_synonym("drug", "Lidocaine", new_synonym)

        """
        if key not in self.keys():
            self.add_key(key)
        msg = f"Value {value} not found. Please add a new value"
        assert self.has_value(key, value), msg
        if synonym not in self.list_synonyms(key, value):
            data = self.data.get(key, {})
            data[value].append(synonym)
            self._update_data(key, data)

    def remove_synonym(self, key: str, value: str, synonym: str) -> None:
        """Remove a synonuym"""
        self._check_key(key)
        if not self.has_value(key, value):
            logger.warning(f"Value {value} not found for key {key}")
            return None

        if synonym in self.list_synonyms(key, value):
            logger.info(f"Remove synonym {synonym} from {value}")
            data = self.data.get(key, {})
            data[value].remove(synonym)
            self._update_data(key, data, overwrite=True)

    def add_value(self, key: str, value: str, synonyms: Optional[str] = None) -> None:
        """Add a new item new to the
        list of abreviations.

        Example
        -------

        .. code::

            abrev = Abreviations()
            value = "Lidocaine"
            synonyms = ["Lid", "lid", "lidocaine", "Lidocaine"]
            abrev.add_value("drug", "Lidocaine", synonyms=synonyms)

        """
        if key not in self.keys():
            self.add_key(key)
        if synonyms is None:
            synonyms = []  # type:ignore
        assert isinstance(synonyms, list)
        logger.info(f"Add value {value} to {key} with synonyms {synonyms}")
        data = self.data.get(key, {})

        data[value] = data.get(value, [])
        data[value] += synonyms
        self._update_data(key, data)

    def remove_value(self, key: str, value: str) -> None:
        self._check_key(key)

        if self.has_value(key, value):
            logger.info(f"Remove value {value} from {key}")
            self._data.get(key, {}).pop(value)
            self._dump_data(overwrite=True)

    def get_name(self, key: str, synonym: str) -> Optional[str]:
        """Get the name of the synonum

        Example
        -------

        .. code::

            abrev = Abreviations()
            abrev.add_value("drug", "TestDrug", ["test", "testdrug"])
            print(abrev.get_name("test"))
            # Should print 'TestDrug'
        """
        for value in self.list_values(key):
            if synonym in self.list_synonyms(key, value):
                return value
        if self.raise_on_failure:
            raise ValueError(f"Could not find name for key {key} and synonym {synonym}")
        return None
