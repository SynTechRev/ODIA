"""C.O.N.T.R.A. entity registry — commercial entity resolution and name normalization."""

from .normalize import normalize_corporate_suffix
from .registry import Entity, EntityRegistry

__all__ = [
    "Entity",
    "EntityRegistry",
    "normalize_corporate_suffix",
]
