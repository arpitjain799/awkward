# BSD 3-Clause License; see https://github.com/scikit-hep/awkward-1.0/blob/main/LICENSE
__all__ = ("from_regular",)
import awkward as ak
from awkward._behavior import behavior_of
from awkward._errors import AxisError
from awkward._layout import maybe_posaxis, wrap_layout
from awkward._nplikes.numpylike import NumpyMetadata
from awkward._regularize import regularize_axis

np = NumpyMetadata.instance()


def from_regular(array, axis=1, *, highlevel=True, behavior=None):
    """
    Args:
        array: Array-like data (anything #ak.to_layout recognizes).
        axis (int or None): The dimension at which this operation is applied.
            The outermost dimension is `0`, followed by `1`, etc., and negative
            values count backward from the innermost: `-1` is the innermost
            dimension, `-2` is the next level up, etc. If None, convert all
            regular dimensions into variable ones.
        highlevel (bool): If True, return an #ak.Array; otherwise, return
            a low-level #ak.contents.Content subclass.
        behavior (None or dict): Custom #ak.behavior for the output array, if
            high-level.

    Converts a regular axis into an irregular one.

        >>> regular = ak.Array(np.arange(2*3*5).reshape(2, 3, 5))
        >>> regular.type.show()
        2 * 3 * 5 * int64
        >>> ak.from_regular(regular).type.show()
        2 * var * 5 * int64
        >>> ak.from_regular(regular, axis=2).type.show()
        2 * 3 * var * int64
        >>> ak.from_regular(regular, axis=-1).type.show()
        2 * 3 * var * int64

    See also #ak.to_regular.
    """
    with ak._errors.OperationErrorContext(
        "ak.from_regular",
        {"array": array, "axis": axis, "highlevel": highlevel, "behavior": behavior},
    ):
        return _impl(array, axis, highlevel, behavior)


def _impl(array, axis, highlevel, behavior):
    axis = regularize_axis(axis)
    layout = ak.operations.to_layout(array)
    behavior = behavior_of(array, behavior=behavior)

    if axis is None:

        def action(layout, continuation, **kwargs):
            if layout.is_regular:
                return continuation().to_ListOffsetArray64(False)

        out = ak._do.recursively_apply(layout, action, behavior, numpy_to_regular=True)

    elif maybe_posaxis(layout, axis, 1) == 0:
        out = layout  # the top-level is already regular (ArrayType)

    else:

        def action(layout, depth, **kwargs):
            posaxis = maybe_posaxis(layout, axis, depth)
            if posaxis == depth and layout.is_regular:
                return layout.to_ListOffsetArray64(False)
            elif posaxis == depth and layout.is_list:
                return layout
            elif layout.is_leaf:
                raise AxisError(
                    f"axis={axis} exceeds the depth of this array ({depth})"
                )

        out = ak._do.recursively_apply(layout, action, behavior, numpy_to_regular=True)

    return wrap_layout(out, behavior, highlevel)
