import itertools

import numpy as np
import pytest
from mps_data_parser import utils

dose_lists = [
    ["0nM", "1nM", "10nM", "100nM", "1000nM"],
    ["0nM", "1nM", "1uM", "10uM", "10uM"],
    ["dose1", "dose2", "dose3", "dose4"],
    ["Dose_1", "Dose_2", "Dose_3", "Dose_4"],
]


@pytest.mark.parametrize("dose_list, seed", itertools.product(dose_lists, range(4)))
def test_dose_sorting(dose_list, seed):
    np.random.seed(seed)
    shuffled_list = dose_list.copy()
    np.random.shuffle(shuffled_list)
    sorted_list = utils.dose_sorting(shuffled_list)

    assert dose_list == sorted_list


if __name__ == "__main__":
    test_dose_sorting(dose_lists[0], 0)
