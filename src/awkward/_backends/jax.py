# BSD 3-Clause License; see https://github.com/scikit-hep/awkward-1.0/blob/main/LICENSE
from __future__ import annotations

import awkward_cpp

import awkward as ak
from awkward._backends.backend import Backend, KernelKeyType
from awkward._backends.dispatch import register_backend
from awkward._kernels import JaxKernel
from awkward._nplikes.jax import Jax
from awkward._nplikes.numpy import Numpy
from awkward._nplikes.numpylike import NumpyMetadata
from awkward._typing import Final

np = NumpyMetadata.instance()
numpy = Numpy.instance()


@register_backend(Jax)
class JaxBackend(Backend):
    name: Final[str] = "jax"

    _jax: Jax
    _numpy: Numpy

    @property
    def nplike(self) -> Jax:
        return self._jax

    @property
    def index_nplike(self) -> Numpy:
        return self._numpy

    def __init__(self):
        self._jax = Jax.instance()
        self._numpy = Numpy.instance()

    def __getitem__(self, index: KernelKeyType) -> JaxKernel:
        # JAX uses Awkward's C++ kernels for index-only operations
        return JaxKernel(awkward_cpp.cpu_kernels.kernel[index], index)

    def apply_reducer(
        self,
        reducer: ak._reducers.Reducer,
        layout: ak.contents.NumpyArray,
        parents: ak.index.Index,
        outlength: int,
    ) -> ak.contents.NumpyArray:
        from awkward._connect.jax import get_jax_reducer

        jax_reducer = get_jax_reducer(reducer)
        return jax_reducer.apply(layout, parents, outlength)

    def apply_ufunc(self, ufunc, method, args, kwargs):
        from awkward._connect.jax import get_jax_ufunc

        if method != "__call__":
            raise ValueError(f"unsupported ufunc method {method} called")

        jax_ufunc = get_jax_ufunc(ufunc)
        return jax_ufunc(*args, **kwargs)
