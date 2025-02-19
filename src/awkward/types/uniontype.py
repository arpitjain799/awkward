# BSD 3-Clause License; see https://github.com/scikit-hep/awkward-1.0/blob/main/LICENSE
from __future__ import annotations

from collections.abc import Iterable
from itertools import permutations

from awkward._parameters import parameters_are_equal, type_parameters_equal
from awkward._typing import Self, final
from awkward._util import unset
from awkward.types.type import Type


@final
class UnionType(Type):
    def copy(
        self, *, contents: list[Type] = unset, parameters=unset, typestr=unset
    ) -> Self:
        return UnionType(
            self._contents if contents is unset else contents,
            parameters=self._parameters if parameters is unset else parameters,
            typestr=self._typestr if typestr is unset else typestr,
        )

    def __init__(self, contents, *, parameters=None, typestr=None):
        if not isinstance(contents, Iterable):
            raise TypeError(
                "{} 'contents' must be iterable, not {}".format(
                    type(self).__name__, repr(contents)
                )
            )
        if not isinstance(contents, list):
            contents = list(contents)
        for content in contents:
            if not isinstance(content, Type):
                raise TypeError(
                    "{} all 'contents' must be Type subclasses, not {}".format(
                        type(self).__name__, repr(content)
                    )
                )
        if parameters is not None and not isinstance(parameters, dict):
            raise TypeError(
                "{} 'parameters' must be of type dict or None, not {}".format(
                    type(self).__name__, repr(parameters)
                )
            )
        if typestr is not None and not isinstance(typestr, str):
            raise TypeError(
                "{} 'typestr' must be of type string or None, not {}".format(
                    type(self).__name__, repr(typestr)
                )
            )
        self._contents = contents
        self._parameters = parameters
        self._typestr = typestr

    @property
    def contents(self):
        return self._contents

    def _str(self, indent, compact):
        if self._typestr is not None:
            out = [self._typestr]

        else:
            if compact:
                pre, post = "", ""
            else:
                pre, post = "\n" + indent + "    ", "\n" + indent

            children = []
            for i, x in enumerate(self._contents):
                if i + 1 < len(self._contents):
                    if compact:
                        y = [*x._str(indent, compact), ", "]
                    else:
                        y = [*x._str(indent + "    ", compact), ",\n", indent, "    "]
                else:
                    if compact:
                        y = x._str(indent, compact)
                    else:
                        y = x._str(indent + "    ", compact)
                children.append(y)

            flat_children = [y for x in children for y in x]
            params = self._str_parameters()

            if params is None:
                out = ["union[", pre, *flat_children] + [post, "]"]
            else:
                out = ["union[", pre, *flat_children] + [", ", post, params, "]"]

        return [self._str_categorical_begin(), *out] + [self._str_categorical_end()]

    def __repr__(self):
        args = [repr(self._contents), *self._repr_args()]
        return "{}({})".format(type(self).__name__, ", ".join(args))

    def _is_equal_to(self, other, all_parameters: bool):
        compare_parameters = (
            parameters_are_equal if all_parameters else type_parameters_equal
        )
        return (
            isinstance(other, type(self))
            and compare_parameters(self._parameters, other._parameters)
            and len(self._contents) == len(other._contents)
            and any(
                all(
                    this._is_equal_to(that, all_parameters)
                    for this, that in zip(self._contents, contents)
                )
                for contents in permutations(other._contents)
            )
        )
