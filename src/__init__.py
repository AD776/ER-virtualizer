"""Application package for the Entity Relationship Visualizer."""

from .app import create_app  # noqa: F401

__all__ = [
    "pipeline",
    "cli",
    "create_app",
]
