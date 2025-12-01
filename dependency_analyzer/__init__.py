"""
Dependency Analyzer - A module for building an in-memory index of source code symbols
and their dependencies for IDE-like functionality.

This module provides:
- AST parsing for multiple programming languages
- Symbol indexing (classes, methods, variables, imports)
- Dependency tracking between files and symbols
- Fast lookups for autocomplete and refactoring
- Incremental updates when files change
"""

from .core import DependencyAnalyzer
from .ast_parser import ASTParser
from .symbol_index import SymbolIndex
from .dependency_tracker import DependencyTracker
from .incremental_updater import IncrementalUpdater

__version__ = "1.0.0"
__all__ = [
    "DependencyAnalyzer",
    "ASTParser", 
    "SymbolIndex",
    "DependencyTracker",
    "IncrementalUpdater"
]