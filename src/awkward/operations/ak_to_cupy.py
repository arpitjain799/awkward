# BSD 3-Clause License; see https://github.com/scikit-hep/awkward-1.0/blob/main/LICENSE
__all__ = ("to_cupy",)

import awkward as ak
from awkward._backends.cupy import CupyBackend


def to_cupy(array):
    """
    Args:
        array: Array-like data (anything #ak.to_layout recognizes).

    Converts `array` (many types supported) into a CuPy array, if possible.

    If the data are numerical and regular (nested lists have equal lengths
    in each dimension, as described by the #ak.Array.type), they can be losslessly
    converted to a CuPy array and this function returns without an error.

    Otherwise, the function raises an error.

    If `array` is a scalar, it is converted into a CuPy scalar.

    See also #ak.from_cupy and #ak.to_numpy.
    """
    with ak._errors.OperationErrorContext(
        "ak.to_cupy",
        {"array": array},
    ):
        return _impl(array)


def _impl(array):
    layout = ak.to_layout(array, allow_record=False)

    backend = CupyBackend.instance()
    cupy_layout = layout.to_backend(backend)

    return cupy_layout.to_backend_array(allow_missing=False)
