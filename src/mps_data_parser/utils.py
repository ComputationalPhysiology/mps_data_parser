from typing import List

import numpy as np
import pint
import yaml


def load_config(config_filename):
    with open(config_filename, "r") as f:
        config = yaml.load(f, Loader=yaml.SafeLoader)

    return config


def dose_sorting(lst: List[str]) -> List[str]:
    """
    Given a list of doses (beeing strings), sort the list
    based on increasing dose with lowest dose first.

    Arguments
    ---------
    lst : list
        List of doses in strings

    Returns
    -------
    sorted_lst : list
        A sorted list base on dose with smallest dose first

    Example
    -------

    .. code::

        dose_sorting(['100uM', '10 uM', '100 nM', '1uM'], argsort=False)
        # Should print '['100 nM', '1 uM', '10 uM', '100 uM']'
    """
    sorted_units = ["pM", "nM", "uM", "mM", "cM", "dM"]
    ureg = pint.UnitRegistry()

    mapping = {
        "pM": ureg.pm,
        "nM": ureg.nm,
        "uM": ureg.um,
        "mM": ureg.mm,
        "cM": ureg.cm,
        "dM": ureg.dm,
    }

    inverse_mapping = {v: k for k, v in mapping.items()}

    # Check if first element in list contains unit
    if not any([s in lst[0] for s in sorted_units]):
        # Just sorted the strings
        return sorted(lst)

    new_lst = []
    for item in lst:
        idx = next(i for i, t in enumerate([s in item for s in sorted_units]) if t)
        unit = sorted_units[idx]
        v = float(item.replace(unit, "")) * mapping[unit]
        new_lst.append(v)

    sorted_lst_pint = []
    for item in sorted(new_lst):
        unit = inverse_mapping[item.u]  # type:ignore
        sorted_lst_pint.append("{} {}".format(item.m, unit))  # type: ignore

    inds = np.array([x for x, y in sorted(enumerate(new_lst), key=lambda x: x[1])])
    # if argsort:
    #     return [x for x, y in sorted(enumerate(new_lst), key=lambda x: x[1])]
    # else:
    #     return sorted_lst

    return np.array(lst)[inds].tolist()
