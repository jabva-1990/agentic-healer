"""
Core DependencyAnalyzer class that orchestrates all components.
Provides the main interface for IDE-like functionality.
"""

import os
import time
from typing import Dict, List, Set, Optional, Any, Tuple
from dataclasses import dataclass
import logging

from .types import (
    Symbol, SymbolType, Language, FileInfo, Dependency,
    IndexStats, normalize_path
)
from .symbol_index import SymbolIndex
from .dependency_tracker import DependencyTracker, ImpactAnalysis
from .incremental_updater import IncrementalUpdater
from .ast_parser import ASTParser

logger = logging.getLogger(__name__)


@dataclass
class AutocompleteResult:
    """Result for autocomplete suggestions."""
    symbol: Symbol
    score: float
    context: str


@dataclass
class FindReferencesResult:
    """Result for find references operation."""
    symbol: Symbol
    file_path: str
    line: int
    column: int
    context_line: str


@dataclass
class RefactoringPlan:
    """Plan for a refactoring operation."""
    files_to_change: List[str]
    impact_analysis: ImpactAnalysis
    suggested_order: List[str]
    warnings: List[str]


class DependencyAnalyzer:
    """
    Main dependency analyzer that provides IDE-like functionality.
    
    Features:
    - Symbol indexing and fast lookups
    - Dependency tracking and analysis
    - Autocomplete suggestions
    - Find references
    - Refactoring support
    - Incremental updates
    """
    
    def __init__(self, enable_watching: bool = True):
        self.symbol_index = SymbolIndex()
        self.dependency_tracker = DependencyTracker()
        self.incremental_updater = IncrementalUpdater(
            self.symbol_index, 
            self.dependency_tracker
        ) if enable_watching else None
        
        self.indexed_directories: Set[str] = set()
        self.is_initialized = False
        
        logger.info("Dependency analyzer initialized")
    
    def initialize(self, project_roots: List[str], watch_changes: bool = True) -> bool:
        """Initialize the analyzer with project directories."""
        try:
            total_indexed = 0
            
            for root in project_roots:
                if not os.path.exists(root):
                    logger.warning(f"Project root does not exist: {root}")
                    continue
                
                logger.info(f"Indexing project root: {root}")
                count = self.symbol_index.index_directory(root)
                total_indexed += count
                self.indexed_directories.add(normalize_path(root))
            
            # Update dependency tracker
            self.dependency_tracker.update_dependencies(self.symbol_index.files)
            
            # Start file watching if requested
            if watch_changes and self.incremental_updater:
                self.incremental_updater.start_watching(list(self.indexed_directories))
            
            self.is_initialized = True
            logger.info(f"Initialization complete: {total_indexed} files indexed")
            return True
            
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            return False
    
    def shutdown(self):
        """Shutdown the analyzer and cleanup resources."""
        if self.incremental_updater:
            self.incremental_updater.stop_watching()
        
        self.symbol_index.clear()
        logger.info("Dependency analyzer shutdown complete")
    
    # Symbol lookup methods
    
    def find_symbol_definition(self, symbol_name: str, 
                             file_context: Optional[str] = None) -> List[Symbol]:
        """Find the definition of a symbol."""
        symbols = self.symbol_index.find_symbol(symbol_name)
        
        if file_context:
            # Prioritize symbols from the same file or related files
            file_context = normalize_path(file_context)
            same_file = [s for s in symbols if s.file_path == file_context]
            other_files = [s for s in symbols if s.file_path != file_context]
            symbols = same_file + other_files
        
        return symbols
    
    def find_all_references(self, symbol_name: str, 
                          definition_file: Optional[str] = None) -> List[FindReferencesResult]:
        """Find all references to a symbol."""
        # This is a simplified implementation
        # In practice, you'd need to scan for actual usage patterns
        symbols = self.find_symbol_definition(symbol_name, definition_file)
        results = []
        
        for symbol in symbols:
            # Add the definition itself
            result = FindReferencesResult(
                symbol=symbol,
                file_path=symbol.file_path,
                line=symbol.range.start.line,
                column=symbol.range.start.column,
                context_line=f"Definition: {symbol.name}"
            )
            results.append(result)
            
            # Add references from other files
            for ref_file in symbol.references:
                # This would need actual code scanning to find usage locations
                # For now, just indicate that references exist
                ref_result = FindReferencesResult(
                    symbol=symbol,
                    file_path=ref_file,
                    line=1,  # Would need actual line number
                    column=1,  # Would need actual column
                    context_line=f"Reference in {os.path.basename(ref_file)}"
                )
                results.append(ref_result)
        
        return results
    
    def get_autocomplete_suggestions(self, prefix: str, 
                                   file_context: Optional[str] = None,
                                   limit: int = 50) -> List[AutocompleteResult]:
        """Get autocomplete suggestions for a prefix."""
        symbols = self.symbol_index.find_symbols_by_prefix(prefix, limit * 2)
        results = []
        
        for symbol in symbols:
            # Calculate relevance score
            score = self._calculate_autocomplete_score(symbol, prefix, file_context)
            
            # Create context string
            context = self._create_symbol_context(symbol)
            
            result = AutocompleteResult(
                symbol=symbol,
                score=score,
                context=context
            )
            results.append(result)
        
        # Sort by score and limit results
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:limit]
    
    def get_symbols_in_file(self, file_path: str) -> List[Symbol]:
        """Get all symbols defined in a specific file."""
        return self.symbol_index.find_symbols_in_file(file_path)
    
    def get_class_members(self, class_name: str) -> List[Symbol]:
        """Get all members (methods, properties) of a class."""
        return self.symbol_index.find_methods_in_class(class_name)
    
    # Dependency analysis methods
    
    def get_file_dependencies(self, file_path: str) -> List[str]:
        """Get files that the given file depends on."""
        deps = self.dependency_tracker.get_file_dependencies(file_path)
        return list(deps)
    
    def get_file_dependents(self, file_path: str) -> List[str]:
        """Get files that depend on the given file."""
        deps = self.dependency_tracker.get_file_dependents(file_path)
        return list(deps)
    
    def analyze_change_impact(self, files: List[str]) -> ImpactAnalysis:
        """Analyze the impact of changing the given files."""
        return self.dependency_tracker.analyze_impact(files)
    
    def find_circular_dependencies(self) -> List[List[str]]:
        """Find circular dependencies in the codebase."""
        return self.dependency_tracker.find_circular_dependencies()
    
    def get_dependency_metrics(self) -> Dict[str, Any]:
        """Get metrics about the codebase dependencies."""
        return self.dependency_tracker.get_dependency_metrics()
    
    # Refactoring support methods
    
    def plan_refactoring(self, files_to_change: List[str]) -> RefactoringPlan:
        """Create a plan for refactoring the given files."""
        impact = self.analyze_change_impact(files_to_change)
        suggested_order = self.dependency_tracker.suggest_refactoring_order(files_to_change)
        
        warnings = []
        
        # Check for circular dependencies
        cycles = self.find_circular_dependencies()
        affected_cycles = [
            cycle for cycle in cycles 
            if any(f in files_to_change for f in cycle)
        ]
        if affected_cycles:
            warnings.append(f"Refactoring affects {len(affected_cycles)} circular dependencies")
        
        # Check for high-impact changes
        if len(impact.total_affected) > 20:
            warnings.append(f"High impact change: {len(impact.total_affected)} files affected")
        
        return RefactoringPlan(
            files_to_change=files_to_change,
            impact_analysis=impact,
            suggested_order=suggested_order,
            warnings=warnings
        )
    
    def suggest_safe_refactoring_order(self, files: List[str]) -> List[str]:
        """Suggest a safe order to refactor files."""
        return self.dependency_tracker.suggest_refactoring_order(files)
    
    # Index management methods
    
    def update_file(self, file_path: str, content: Optional[str] = None) -> bool:
        """Update a specific file in the index."""
        if self.incremental_updater:
            return self.incremental_updater.update_file(file_path, content)
        else:
            return self.symbol_index.index_file(file_path, content)
    
    def refresh_index(self):
        """Refresh the entire index."""
        logger.info("Refreshing entire index...")
        self.symbol_index.clear()
        
        for directory in self.indexed_directories:
            self.symbol_index.index_directory(directory)
        
        self.dependency_tracker.update_dependencies(self.symbol_index.files)
        logger.info("Index refresh complete")
    
    def get_index_stats(self) -> IndexStats:
        """Get statistics about the current index."""
        return self.symbol_index.get_stats()
    
    def export_dependency_graph(self, format: str = 'dot') -> str:
        """Export dependency graph in specified format."""
        if format == 'dot':
            return self._export_dot_graph()
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    # Search and query methods
    
    def search_symbols(self, query: str, symbol_types: Optional[List[SymbolType]] = None) -> List[Symbol]:
        """Search for symbols matching the query."""
        results = []
        
        # Simple substring search
        for name, symbols in self.symbol_index.symbols_by_name.items():
            if query.lower() in name.lower():
                filtered_symbols = symbols
                if symbol_types:
                    filtered_symbols = [s for s in symbols if s.symbol_type in symbol_types]
                results.extend(filtered_symbols)
        
        return results
    
    def get_project_overview(self) -> Dict[str, Any]:
        """Get an overview of the indexed project."""
        stats = self.get_index_stats()
        metrics = self.get_dependency_metrics()
        cycles = self.find_circular_dependencies()
        
        return {
            'statistics': {
                'total_files': stats.total_files,
                'total_symbols': stats.total_symbols,
                'symbols_by_type': dict(stats.symbols_by_type),
                'files_by_language': dict(stats.files_by_language),
            },
            'dependency_metrics': metrics,
            'circular_dependencies': len(cycles),
            'circular_dependency_details': cycles[:5],  # First 5 cycles
            'indexed_directories': list(self.indexed_directories),
            'last_update': stats.last_update_time,
        }
    
    # Private helper methods
    
    def _calculate_autocomplete_score(self, symbol: Symbol, prefix: str, 
                                    file_context: Optional[str]) -> float:
        """Calculate relevance score for autocomplete."""
        score = 0.0
        
        # Exact prefix match gets higher score
        if symbol.name.startswith(prefix):
            score += 10.0
        
        # Shorter names are often more relevant
        if len(symbol.name) < 20:
            score += 5.0 - (len(symbol.name) / 4.0)
        
        # Same file context gets bonus
        if file_context and symbol.file_path == normalize_path(file_context):
            score += 15.0
        
        # Different symbol types get different base scores
        type_scores = {
            SymbolType.FUNCTION: 8.0,
            SymbolType.METHOD: 8.0,
            SymbolType.CLASS: 9.0,
            SymbolType.VARIABLE: 5.0,
            SymbolType.CONSTANT: 6.0,
        }
        score += type_scores.get(symbol.symbol_type, 3.0)
        
        return score
    
    def _create_symbol_context(self, symbol: Symbol) -> str:
        """Create a context string for a symbol."""
        parts = []
        
        if symbol.symbol_type == SymbolType.METHOD and symbol.parent:
            parts.append(f"{symbol.parent}.{symbol.name}")
        else:
            parts.append(symbol.name)
        
        parts.append(f"({symbol.symbol_type.value})")
        
        if symbol.parameters:
            param_str = ", ".join(symbol.parameters)
            parts.append(f"({param_str})")
        
        if symbol.return_type:
            parts.append(f"-> {symbol.return_type}")
        
        return " ".join(parts)
    
    def _export_dot_graph(self) -> str:
        """Export dependency graph in DOT format."""
        lines = ["digraph Dependencies {"]
        lines.append("  rankdir=TB;")
        lines.append("  node [shape=box];")
        
        # Add nodes
        for file_path in self.dependency_tracker.file_dependencies.nodes:
            clean_name = os.path.basename(file_path).replace(".", "_")
            lines.append(f'  "{clean_name}" [label="{os.path.basename(file_path)}"];')
        
        # Add edges
        for source, targets in self.dependency_tracker.file_dependencies.edges.items():
            source_name = os.path.basename(source).replace(".", "_")
            for target in targets:
                target_name = os.path.basename(target).replace(".", "_")
                lines.append(f'  "{source_name}" -> "{target_name}";')
        
        lines.append("}")
        return "\n".join(lines)
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.shutdown()