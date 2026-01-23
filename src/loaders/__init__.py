"""Data loaders for populating PostgreSQL with embeddings."""

from src.loaders.base import batch_embed, batch_insert
from src.loaders.cities import load_cities
from src.loaders.countries import load_countries
from src.loaders.states import load_states

__all__ = [
    "load_countries",
    "load_states",
    "load_cities",
    "batch_embed",
    "batch_insert",
]
