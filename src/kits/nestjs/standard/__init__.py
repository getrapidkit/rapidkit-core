"""NestJS Standard Kit package."""

from .generator import NestJSStandardGenerator
from .hooks import post_generate, pre_generate

__all__ = [
    "NestJSStandardGenerator",
    "pre_generate",
    "post_generate",
]
