# Python standard libraries
from typing import Dict
import numpy as np

def dict2matlab(input_dict: Dict) -> Dict:
    """
    Cleans a python dict and makes it compatible with matlab

    Dict must be cleaned from 'None's to np.nan (= NaN in Matlab)
    see https://stackoverflow.com/questions/35985923/replace-none-in-a-python-dictionary

    :param input_dict: dictionary to be cleaned
    :type input_dict: dict

    :return: 'clean' matlab-compatible transistor dictionary
    :rtype: dict
    """
    result = {}
    for key, value in input_dict:
        if value is None:
            value = np.nan
        result[key] = value
    return result