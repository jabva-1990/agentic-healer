"""
Symbol Index module for fast symbol lookups and storage.
Provides in-memory indexing with multiple access patterns for IDE functionality.
"""

import os
import time
from typing import Dict, List, Set, Optional, Tuple, Any
from collections import defaultdict
import logging
from pathlib import Path

from .types import (
    Symbol, SymbolType, Language, FileInfo, Dependency,
    IndexStats, normalize_path
)
from .ast_parser import ASTParser

logger = logging.getLogger(__name__)


class SymbolIndex:
    """In-memory index of symbols with fast lookup capabilities."""
    
    def __init__(self):
        self.ast_parser = ASTParser()
        
        # Core storage
        self.files: Dict[str, FileInfo] = {}
        
        # Symbol indexes for fast lookups
        self.symbols_by_name: Dict[str, List[Symbol]] = defaultdict(list)
        self.symbols_by_type: Dict[SymbolType, List[Symbol]] = defaultdict(list)
        self.symbols_by_file: Dict[str, List[Symbol]] = defaultdict(list)
        self.symbols_by_parent: Dict[str, List[Symbol]] = defaultdict(list)
        
        # Dependency indexes
        self.dependencies_by_source: Dict[str, List[Dependency]] = defaultdict(list)
        self.dependencies_by_target: Dict[str, List[Dependency]] = defaultdict(list)
        self.reverse_dependencies: Dict[str, Set[str]] = defaultdict(set)
        
        # Search indexes
        self.symbol_name_prefixes: Dict[str, Set[str]] = defaultdict(set)
        
        # Statistics
        self.stats = IndexStats()
        
        logger.info("Symbol index initialized")
    
    def index_file(self, file_path: str, content: Optional[str] = None) -> bool:
        """Index a single file and update all indexes."""
        normalized_path = normalize_path(file_path)
        
        if not self.ast_parser.can_parse(file_path):
            logger.debug(f"Skipping unsupported file: {file_path}")
            return False
        
        try:
            file_info = self.ast_parser.parse_file(file_path, content)
            if not file_info:
                return False
            
            # Remove old entries if file was previously indexed
            self._remove_file_from_indexes(normalized_path)
            
            # Add to core storage
            self.files[normalized_path] = file_info
            
            # Update all indexes
            self._add_symbols_to_indexes(file_info.symbols)
            self._add_dependencies_to_indexes(file_info.dependencies)
            
            logger.debug(f"Indexed file: {file_path} ({len(file_info.symbols)} symbols)")
            return True
            
        except Exception as e:
            logger.error(f"Error indexing file {file_path}: {e}")
            return False
    
    def index_directory(self, directory_path: str, 
                       include_patterns: Optional[List[str]] = None,
                       exclude_patterns: Optional[List[str]] = None) -> int:
        """Index all supported files in a directory recursively."""
        directory_path = normalize_path(directory_path)
        indexed_count = 0
        
        if not os.path.isdir(directory_path):
            logger.error(f"Directory not found: {directory_path}")
            return 0
        
        exclude_patterns = exclude_patterns or [
            '__pycache__', '.git', '.svn', 'node_modules', '.vscode',
            '*.pyc', '*.pyo', '*.pyd', '.DS_Store', 'venv', 'env',
            'build', 'dist', 'target', '.pytest_cache', '.mypy_cache',
            '.tox', '.coverage', 'htmlcov', '.nyc_output', 'coverage',
            'logs', 'tmp', 'temp', '.idea', '.vs', 'bin', 'obj', '.next',
            '*.log', '*.tmp', '*.swp', '*.swo', '*.bak'
        ]
        
        # First pass: collect all files for progress tracking
        all_files = []
        for root, dirs, files in os.walk(directory_path):
            # Filter out excluded directories
            dirs[:] = [d for d in dirs if not self._should_exclude(d, exclude_patterns)]
            
            for file in files:
                file_path = os.path.join(root, file)
                if not self._should_exclude(file, exclude_patterns):
                    all_files.append(file_path)
        
        total_files = len(all_files)
        logger.info(f"Found {total_files} files to analyze")
        
        # Second pass: process files with progress reporting
        for i, file_path in enumerate(all_files, 1):
            if self.index_file(file_path):
                indexed_count += 1
            
            # Progress reporting
            if total_files <= 20:
                logger.info(f"Progress: {i}/{total_files} files")
            elif i % 50 == 0 or i == total_files:
                logger.info(f"Progress: {i}/{total_files} files ({indexed_count} indexed)")
        
        self._update_stats()
        logger.info(f"Indexed {indexed_count} files in directory: {directory_path}")
        return indexed_count
    
    def remove_file(self, file_path: str):
        """Remove a file from all indexes."""
        normalized_path = normalize_path(file_path)
        self._remove_file_from_indexes(normalized_path)
        self._update_stats()
    
    def find_symbol(self, name: str, symbol_type: Optional[SymbolType] = None) -> List[Symbol]:
        """Find symbols by name and optionally by type."""
        symbols = self.symbols_by_name.get(name, [])
        
        if symbol_type:
            symbols = [s for s in symbols if s.symbol_type == symbol_type]
        
        return symbols
    
    def find_symbols_by_prefix(self, prefix: str, limit: int = 50) -> List[Symbol]:
        """Find symbols that start with the given prefix for autocomplete."""
        results = []
        
        for name, symbols in self.symbols_by_name.items():
            if name.startswith(prefix):
                results.extend(symbols)
                if len(results) >= limit:
                    break
        
        return results[:limit]
    
    def find_symbols_in_file(self, file_path: str) -> List[Symbol]:
        """Get all symbols defined in a specific file."""
        normalized_path = normalize_path(file_path)
        return self.symbols_by_file.get(normalized_path, [])
    
    def find_symbols_by_type(self, symbol_type: SymbolType) -> List[Symbol]:
        """Find all symbols of a specific type."""
        return self.symbols_by_type.get(symbol_type, [])
    
    def find_methods_in_class(self, class_name: str) -> List[Symbol]:
        """Find all methods defined in a specific class."""
        return [s for s in self.symbols_by_parent.get(class_name, []) 
                if s.symbol_type == SymbolType.METHOD]
    
    def find_references(self, symbol_name: str, symbol_file: Optional[str] = None) -> List[Symbol]:
        """Find all references to a symbol."""
        references = []
        
        # Find the symbol definition
        candidates = self.find_symbol(symbol_name)
        if symbol_file:
            candidates = [s for s in candidates if s.file_path == normalize_path(symbol_file)]
        
        for symbol in candidates:
            # Find files that reference this symbol
            for ref_file in symbol.references:
                file_symbols = self.find_symbols_in_file(ref_file)
                references.extend(file_symbols)
        
        return references
    
    def get_dependencies(self, file_path: str) -> List[Dependency]:
        """Get all dependencies from a file."""
        normalized_path = normalize_path(file_path)
        return self.dependencies_by_source.get(normalized_path, [])
    
    def get_reverse_dependencies(self, file_path: str) -> Set[str]:
        """Get all files that depend on the given file."""
        normalized_path = normalize_path(file_path)
        return self.reverse_dependencies.get(normalized_path, set())
    
    def get_file_info(self, file_path: str) -> Optional[FileInfo]:
        """Get complete file information."""
        normalized_path = normalize_path(file_path)
        return self.files.get(normalized_path)
    
    def is_file_indexed(self, file_path: str) -> bool:
        """Check if a file is currently indexed."""
        normalized_path = normalize_path(file_path)
        return normalized_path in self.files
    
    def needs_update(self, file_path: str) -> bool:
        """Check if a file needs to be re-indexed based on modification time."""
        normalized_path = normalize_path(file_path)
        
        if not self.is_file_indexed(normalized_path):
            return True
        
        if not os.path.exists(file_path):
            return True
        
        file_info = self.files[normalized_path]
        current_mtime = os.path.getmtime(file_path)
        
        return current_mtime > file_info.last_modified
    
    def get_stats(self) -> IndexStats:
        """Get current index statistics."""
        self._update_stats()
        return self.stats
    
    def clear(self):
        """Clear all indexes."""
        self.files.clear()
        self.symbols_by_name.clear()
        self.symbols_by_type.clear()
        self.symbols_by_file.clear()
        self.symbols_by_parent.clear()
        self.dependencies_by_source.clear()
        self.dependencies_by_target.clear()
        self.reverse_dependencies.clear()
        self.symbol_name_prefixes.clear()
        self.stats = IndexStats()
        logger.info("Symbol index cleared")
    
    def _add_symbols_to_indexes(self, symbols: List[Symbol]):
        """Add symbols to all relevant indexes."""
        for symbol in symbols:
            # Add to name index
            self.symbols_by_name[symbol.name].append(symbol)
            
            # Add to type index
            self.symbols_by_type[symbol.symbol_type].append(symbol)
            
            # Add to file index
            self.symbols_by_file[symbol.file_path].append(symbol)
            
            # Add to parent index if applicable
            if symbol.parent:
                self.symbols_by_parent[symbol.parent].append(symbol)
            
            # Add to prefix index for autocomplete
            self._add_to_prefix_index(symbol)
    
    def _add_dependencies_to_indexes(self, dependencies: List[Dependency]):
        """Add dependencies to indexes."""
        for dep in dependencies:
            # Add to source index
            self.dependencies_by_source[dep.source_file].append(dep)
            
            # Add to target index
            self.dependencies_by_target[dep.target_file].append(dep)
            
            # Add to reverse dependencies
            self.reverse_dependencies[dep.target_file].add(dep.source_file)
    
    def _remove_file_from_indexes(self, file_path: str):
        """Remove all entries for a file from indexes."""
        if file_path not in self.files:
            return
        
        file_info = self.files[file_path]
        
        # Remove symbols from indexes
        for symbol in file_info.symbols:
            self.symbols_by_name[symbol.name] = [
                s for s in self.symbols_by_name[symbol.name] if s.file_path != file_path
            ]
            self.symbols_by_type[symbol.symbol_type] = [
                s for s in self.symbols_by_type[symbol.symbol_type] if s.file_path != file_path
            ]
            if symbol.parent:
                self.symbols_by_parent[symbol.parent] = [
                    s for s in self.symbols_by_parent[symbol.parent] if s.file_path != file_path
                ]
            self._remove_from_prefix_index(symbol)
        
        # Remove from file index
        del self.symbols_by_file[file_path]
        
        # Remove dependencies
        for dep in file_info.dependencies:
            self.dependencies_by_source[dep.source_file] = [
                d for d in self.dependencies_by_source[dep.source_file] if d != dep
            ]
            self.dependencies_by_target[dep.target_file] = [
                d for d in self.dependencies_by_target[dep.target_file] if d != dep
            ]
            self.reverse_dependencies[dep.target_file].discard(dep.source_file)
        
        # Remove from core storage
        del self.files[file_path]
    
    def _add_to_prefix_index(self, symbol: Symbol):
        """Add symbol to prefix index for autocomplete."""
        name = symbol.name
        for i in range(1, min(len(name) + 1, 10)):  # Index prefixes up to 10 chars
            prefix = name[:i]
            # Store symbol name instead of symbol object to avoid hashability issues
            self.symbol_name_prefixes[prefix].add(symbol.name)
    
    def _remove_from_prefix_index(self, symbol: Symbol):
        """Remove symbol from prefix index."""
        name = symbol.name
        for i in range(1, min(len(name) + 1, 10)):
            prefix = name[:i]
            self.symbol_name_prefixes[prefix].discard(symbol.name)
    
    def _should_exclude(self, name: str, exclude_patterns: List[str]) -> bool:
        """Check if a file/directory should be excluded based on patterns."""
        for pattern in exclude_patterns:
            if pattern.startswith('*'):
                if name.endswith(pattern[1:]):
                    return True
            elif pattern.endswith('*'):
                if name.startswith(pattern[:-1]):
                    return True
            elif pattern in name:
                return True
        return False
    
    def _update_stats(self):
        """Update index statistics."""
        self.stats.update_stats(self.files)
        self.stats.last_update_time = time.time()