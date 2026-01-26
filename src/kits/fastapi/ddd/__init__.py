"""FastAPI DDD kit package."""

from .generator import FastAPIDDDGenerator
from .hooks import post_generate, pre_generate

__all__ = [
    "FastAPIDDDGenerator",
    "pre_generate",
    "post_generate",
]
