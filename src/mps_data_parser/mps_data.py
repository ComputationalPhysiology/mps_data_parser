import logging
from typing import Optional

from .abreviations import Abbreviations

logger = logging.getLogger(__name__)

SQL_KEYS = [
    "path",
    "media",
    "dose",
    "pacing_frequency",
    "trace_type",
    "chip",
]


class MPSData:
    def __init__(
        self, folder: str, path: str, abrev: Optional[Abbreviations], **kwargs
    ):
        self.folder = folder
        self.path = path
        if abrev is None:
            abrev = Abbreviations(raise_on_failure=False)
        optional_arguments = MPSData.default_optional_arguments()
        # Check if we have a new argument
        for key in kwargs:
            if key not in optional_arguments:
                msg = (
                    f"Key {key} is not a valid argument. "
                    "Please add this argument to the list of arguments to "
                    "MPSData class if you want it to be searchable. "
                )
                logger.debug(msg)

        optional_arguments.update(kwargs)
        for k, v in optional_arguments.items():
            # Try to see if name is an abrevation, and if not use
            # the orignal value
            name = abrev.get_name(k, v) or v
            setattr(self, k, name)

    def __repr__(self):
        return f"{self.__class__.__name__}(folder={self.folder}, path={self.path})"

    def get(self, key: str) -> str:
        return self.to_dict().get(key)

    def to_dict(self):
        return {k: v for k, v in self.__dict__.items() if v is not None}

    def sql_data(self):
        return {k: v for k, v in self.to_dict().items() if k in SQL_KEYS}

    def json_keys(self):
        return {k: v for k, v in self.to_dict().items() if k not in SQL_KEYS}

    @staticmethod
    def default_optional_arguments():
        """Default optional arguments are set
        to None, but takes string type if set.
        """
        return dict(
            media=None,
            dose=None,
            pacing_frequency=None,
            trace_type=None,
            drug=None,
            cell_line=None,
            chip=None,
            date=None,
            operator=None,
            channel=None,
            seq_nr=None,
            extension=None,
            roi=None,
            framerate=None,
            binsize=None,
            secondary_drug=None,
        )

    @staticmethod
    def required_arguments():
        return ("folder", "path")

    @staticmethod
    def arguments():
        return MPSData.required_arguments() + tuple(
            MPSData.default_optional_arguments().keys()
        )
