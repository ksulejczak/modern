__all__ = [
    "AnnotatedType",
    "EnumType",
    "GenericAliases",
    "UnionTypes",
]

import types
import typing

try:  # pragma: no cover
    from enum import EnumType  # type: ignore[attr-defined]
except ImportError:  # pragma: no cover
    from enum import EnumMeta as EnumType  # type: ignore[attr-defined]


_U = typing.Union[int, str]
UnionTypes = (types.UnionType, type(_U))
del _U


_L = typing.List[int]
GenericAliases = types.GenericAlias, type(_L)
del _L


_A = typing.Annotated[int, lambda x: x]
AnnotatedType = type(_A)
del _A
