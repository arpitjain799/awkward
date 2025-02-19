# BSD 3-Clause License; see https://github.com/scikit-hep/awkward-1.0/blob/main/LICENSE
from __future__ import annotations

import copy

import awkward as ak
from awkward._backends.backend import Backend
from awkward._backends.numpy import NumpyBackend
from awkward._backends.typetracer import TypeTracerBackend
from awkward._errors import AxisError, deprecate
from awkward._layout import maybe_posaxis
from awkward._nplikes.numpy import Numpy
from awkward._nplikes.numpylike import IndexType, NumpyMetadata
from awkward._regularize import is_integer_like
from awkward._slicing import NO_HEAD
from awkward._typing import TYPE_CHECKING, Final, Self, SupportsIndex, final
from awkward._util import unset
from awkward.contents.content import Content
from awkward.forms.emptyform import EmptyForm
from awkward.index import Index

if TYPE_CHECKING:
    from awkward._slicing import SliceItem

np = NumpyMetadata.instance()
numpy = Numpy.instance()


@final
class EmptyArray(Content):
    """
    An EmptyArray is used whenever an array's type is not known because it is empty
    (such as data from #ak.ArrayBuilder without enough sample points to resolve the
    type).

    Unlike all other Content subclasses, EmptyArray cannot contain any parameters
    (parameter values are always None).

    EmptyArray has no equivalent in Apache Arrow.

    To illustrate how the constructor arguments are interpreted, the following is a
    simplified implementation of `__init__`, `__len__`, and `__getitem__`:

        class EmptyArray(Content):
            def __init__(self):
                pass

            def __len__(self):
                return 0

            def __getitem__(self, where):
                if isinstance(where, int):
                    assert False

                elif isinstance(where, slice) and where.step is None:
                    return EmptyArray()

                elif isinstance(where, str):
                    raise ValueError("field " + repr(where) + " not found")

                else:
                    raise AssertionError(where)
    """

    is_unknown = True
    is_leaf = True

    def __init__(self, *, parameters=None, backend=None):
        if not (parameters is None or len(parameters) == 0):
            deprecate(
                f"{type(self).__name__} cannot contain parameters", version="2.2.0"
            )
        if backend is None:
            backend = NumpyBackend.instance()
        self._init(parameters, backend)

    form_cls: Final = EmptyForm

    def copy(
        self,
        *,
        parameters=unset,
        backend=unset,
    ):
        if not (parameters is unset or parameters is None or len(parameters) == 0):
            deprecate(
                f"{type(self).__name__} cannot contain parameters", version="2.2.0"
            )
        return EmptyArray(
            parameters=self._parameters if parameters is unset else parameters,
            backend=self._backend if backend is unset else backend,
        )

    def __copy__(self):
        return self.copy()

    def __deepcopy__(self, memo):
        return self.copy(parameters=copy.deepcopy(self._parameters, memo))

    @classmethod
    def simplified(cls, *, parameters=None, backend=None):
        if not (parameters is None or len(parameters) == 0):
            deprecate(f"{cls.__name__} cannot contain parameters", version="2.2.0")
        return cls(parameters=parameters, backend=backend)

    def _form_with_key(self, getkey):
        return self.form_cls(parameters=self._parameters, form_key=getkey(self))

    def _to_buffers(self, form, getkey, container, backend, byteorder):
        assert isinstance(form, self.form_cls)

    def _to_typetracer(self, forget_length: bool) -> Self:
        return EmptyArray(
            parameters=self._parameters,
            backend=TypeTracerBackend.instance(),
        )

    def _touch_data(self, recursive):
        pass

    def _touch_shape(self, recursive):
        pass

    @property
    def length(self):
        return 0

    def __repr__(self):
        return self._repr("", "", "")

    def _repr(self, indent, pre, post):
        extra = self._repr_extra(indent + "    ")
        if len(extra) == 0:
            return indent + pre + "<EmptyArray len='0'/>" + post
        else:
            out = [indent, pre, "<EmptyArray len='0'>"]
            out.extend(extra)
            out.append("\n" + indent + "</EmptyArray>")
            out.append(post)
            return "".join(out)

    def to_NumpyArray(self, dtype, backend=None):
        backend = backend or self._backend
        return ak.contents.NumpyArray(
            backend.nplike.empty(0, dtype=dtype),
            parameters=self._parameters,
            backend=backend,
        )

    def __array__(self, **kwargs):
        return numpy.empty(0, dtype=np.float64)

    def __iter__(self):
        return iter([])

    def _getitem_nothing(self):
        return self

    def _getitem_at(self, where: IndexType):
        raise ak._errors.index_error(self, where, "array is empty")

    def _getitem_range(self, start: SupportsIndex, stop: IndexType) -> Content:
        return self

    def _getitem_field(
        self, where: str | SupportsIndex, only_fields: tuple[str, ...] = ()
    ) -> Content:
        raise ak._errors.index_error(self, where, "not an array of records")

    def _getitem_fields(
        self, where: list[str | SupportsIndex], only_fields: tuple[str, ...] = ()
    ) -> Content:
        if len(where) == 0:
            return self._getitem_range(0, 0)
        raise ak._errors.index_error(self, where, "not an array of records")

    def _carry(self, carry: Index, allow_lazy: bool) -> EmptyArray:
        assert isinstance(carry, ak.index.Index)

        if not carry.nplike.known_data or carry.length == 0:
            return self
        else:
            raise ak._errors.index_error(self, carry.data, "array is empty")

    def _getitem_next_jagged(self, slicestarts, slicestops, slicecontent, tail):
        raise ak._errors.index_error(
            self,
            ak.contents.ListArray(
                slicestarts, slicestops, slicecontent, parameters=None
            ),
            "too many jagged slice dimensions for array",
        )

    def _getitem_next(
        self,
        head: SliceItem | tuple,
        tail: tuple[SliceItem, ...],
        advanced: Index | None,
    ) -> Content:
        if head is NO_HEAD:
            return self

        elif is_integer_like(head):
            raise ak._errors.index_error(self, head, "array is empty")

        elif isinstance(head, slice):
            raise ak._errors.index_error(self, head, "array is empty")

        elif isinstance(head, str):
            return self._getitem_next_field(head, tail, advanced)

        elif isinstance(head, list):
            return self._getitem_next_fields(head, tail, advanced)

        elif head is np.newaxis:
            return self._getitem_next_newaxis(tail, advanced)

        elif head is Ellipsis:
            return self._getitem_next_ellipsis(tail, advanced)

        elif isinstance(head, ak.index.Index64):
            if not head.nplike.known_data or head.length == 0:
                return self
            else:
                raise ak._errors.index_error(self, head.data, "array is empty")

        elif isinstance(head, ak.contents.ListOffsetArray):
            raise ak._errors.index_error(self, head, "array is empty")

        elif isinstance(head, ak.contents.IndexedOptionArray):
            raise ak._errors.index_error(self, head, "array is empty")

        else:
            raise AssertionError(repr(head))

    def _offsets_and_flattened(self, axis, depth):
        posaxis = maybe_posaxis(self, axis, depth)
        if posaxis is not None and posaxis + 1 == depth:
            raise AxisError(self, "axis=0 not allowed for flatten")
        else:
            offsets = ak.index.Index64.zeros(1, nplike=self._backend.index_nplike)
            return (
                offsets,
                EmptyArray(parameters=self._parameters, backend=self._backend),
            )

    def _mergeable_next(self, other, mergebool):
        return True

    def _mergemany(self, others):
        if len(others) == 0:
            return self
        elif len(others) == 1:
            return others[0]
        else:
            return others[0]._mergemany(others[1:])

    def _fill_none(self, value: Content) -> Content:
        return EmptyArray(parameters=self._parameters, backend=self._backend)

    def _local_index(self, axis, depth):
        posaxis = maybe_posaxis(self, axis, depth)
        if posaxis is not None and posaxis + 1 == depth:
            return ak.contents.NumpyArray(
                self._backend.nplike.empty(0, dtype=np.int64),
                parameters=None,
                backend=self._backend,
            )
        else:
            raise AxisError(f"axis={axis} exceeds the depth of this array ({depth})")

    def _numbers_to_type(self, name, including_unknown):
        if including_unknown:
            return self.to_NumpyArray(ak.types.numpytype.primitive_to_dtype(name))
        else:
            return self

    def _is_unique(self, negaxis, starts, parents, outlength):
        return True

    def _unique(self, negaxis, starts, parents, outlength):
        return self

    def _argsort_next(
        self, negaxis, starts, shifts, parents, outlength, ascending, stable
    ):
        as_numpy = self.to_NumpyArray(np.float64)
        return as_numpy._argsort_next(
            negaxis, starts, shifts, parents, outlength, ascending, stable
        )

    def _sort_next(self, negaxis, starts, parents, outlength, ascending, stable):
        return self

    def _combinations(self, n, replacement, recordlookup, parameters, axis, depth):
        return ak.contents.EmptyArray(
            parameters=self._parameters, backend=self._backend
        )

    def _reduce_next(
        self,
        reducer,
        negaxis,
        starts,
        shifts,
        parents,
        outlength,
        mask,
        keepdims,
        behavior,
    ):
        as_numpy = self.to_NumpyArray(reducer.preferred_dtype)
        return as_numpy._reduce_next(
            reducer,
            negaxis,
            starts,
            shifts,
            parents,
            outlength,
            mask,
            keepdims,
            behavior,
        )

    def _validity_error(self, path):
        return ""

    def _nbytes_part(self):
        return 0

    def _pad_none(self, target, axis, depth, clip):
        posaxis = maybe_posaxis(self, axis, depth)
        if posaxis is not None and posaxis + 1 != depth:
            raise AxisError(f"axis={axis} exceeds the depth of this array ({depth})")
        else:
            return self._pad_none_axis0(target, True)

    def _to_arrow(self, pyarrow, mask_node, validbytes, length, options):
        if options["emptyarray_to"] is None:
            return pyarrow.Array.from_buffers(
                ak._connect.pyarrow.to_awkwardarrow_type(
                    pyarrow.null(),
                    options["extensionarray"],
                    options["record_is_scalar"],
                    mask_node,
                    self,
                ),
                length,
                [
                    ak._connect.pyarrow.to_validbits(validbytes),
                ],
                null_count=length,
            )

        else:
            dtype = np.dtype(options["emptyarray_to"])
            next = ak.contents.NumpyArray(
                numpy.empty(length, dtype=dtype),
                parameters=self._parameters,
                backend=self._backend,
            )
            return next._to_arrow(pyarrow, mask_node, validbytes, length, options)

    def _to_backend_array(self, allow_missing, backend):
        return backend.nplike.empty(0, dtype=np.float64)

    def _remove_structure(self, backend, options):
        return [self]

    def _recursively_apply(
        self, action, behavior, depth, depth_context, lateral_context, options
    ):
        if options["return_array"]:

            def continuation():
                if options["keep_parameters"]:
                    return self
                else:
                    return EmptyArray(parameters=None, backend=self._backend)

        else:

            def continuation():
                pass

        result = action(
            self,
            depth=depth,
            depth_context=depth_context,
            lateral_context=lateral_context,
            continuation=continuation,
            behavior=behavior,
            backend=self._backend,
            options=options,
        )

        if isinstance(result, Content):
            return result
        elif result is None:
            return continuation()
        else:
            raise AssertionError(result)

    def to_packed(self) -> Self:
        return self

    def _to_list(self, behavior, json_conversions):
        if not self._backend.nplike.known_data:
            raise TypeError("cannot convert typetracer arrays to Python lists")
        return []

    def _to_backend(self, backend: Backend) -> Self:
        return EmptyArray(parameters=self._parameters, backend=backend)

    def _is_equal_to(self, other, index_dtype, numpyarray):
        return True
