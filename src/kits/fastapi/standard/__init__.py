"""FastAPI Standard kit package."""

from .generator import FastAPIStandardGenerator
from .hooks import post_generate, pre_generate

__all__ = [
    "FastAPIStandardGenerator",
    "pre_generate",
    "post_generate",
]
