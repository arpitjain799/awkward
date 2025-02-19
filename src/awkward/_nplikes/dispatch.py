from __future__ import annotations

from awkward._nplikes.numpylike import NumpyLike
from awkward._typing import TypeVar
from awkward._util import unset

D = TypeVar("D")


_type_to_nplike: dict[type, NumpyLike] = {}
_nplike_classes: list[type[NumpyLike]] = []


N = TypeVar("N", bound="type[NumpyLike]")


def register_nplike(cls: N) -> N:
    _nplike_classes.append(cls)
    return cls


def nplike_of(obj, *, default: D = unset) -> NumpyLike | D:
    """
    Args:
        *arrays: iterable of possible array objects
        default: default NumpyLike instance if no array objects found

    Return the nplike that is best-suited to operating upon the given
    iterable of arrays. If no known array types are found, return `default`
    if it is set, otherwise `Numpy.instance()`.
    """

    cls = type(obj)
    try:
        return _type_to_nplike[cls]
    except KeyError:
        # Try and find the nplike for this type
        # caching the result by type
        for nplike_cls in _nplike_classes:
            if nplike_cls.is_own_array_type(cls):
                nplike = nplike_cls.instance()
                break
        else:
            if default is unset:
                raise TypeError(f"cannot find nplike for {cls.__name__}")
            else:
                return default
        _type_to_nplike[cls] = nplike
        return nplike
