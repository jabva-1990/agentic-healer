"""
Dependency Tracker module for analyzing and managing code dependencies.
Provides advanced dependency analysis for refactoring and impact analysis.
"""

import os
from typing import Dict, List, Set, Optional, Tuple, Any
from collections import defaultdict, deque
from dataclasses import dataclass
import logging

from .types import (
    Symbol, SymbolType, Language, FileInfo, Dependency,
    normalize_path
)

logger = logging.getLogger(__name__)


@dataclass
class DependencyGraph:
    """Represents a dependency graph with nodes and edges."""
    nodes: Set[str]  # File paths or symbol names
    edges: Dict[str, Set[str]]  # node -> set of dependencies
    reverse_edges: Dict[str, Set[str]]  # node -> set of dependents
    
    def __post_init__(self):
        if not hasattr(self, 'nodes'):
            self.nodes = set()
        if not hasattr(self, 'edges'):
            self.edges = defaultdict(set)
        if not hasattr(self, 'reverse_edges'):
            self.reverse_edges = defaultdict(set)


@dataclass
class ImpactAnalysis:
    """Results of impact analysis for a change."""
    changed_files: Set[str]
    directly_affected: Set[str]
    transitively_affected: Set[str]
    total_affected: Set[str]
    dependency_chain: Dict[str, List[str]]  # file -> chain of dependencies
    
    def __post_init__(self):
        self.total_affected = (
            self.changed_files | 
            self.directly_affected | 
            self.transitively_affected
        )


class DependencyTracker:
    """Tracks and analyzes dependencies between files and symbols."""
    
    def __init__(self):
        self.file_dependencies = DependencyGraph(set(), defaultdict(set), defaultdict(set))
        self.symbol_dependencies = DependencyGraph(set(), defaultdict(set), defaultdict(set))
        self.import_graph = DependencyGraph(set(), defaultdict(set), defaultdict(set))
        
        # Cache for expensive operations
        self._circular_deps_cache: Optional[List[List[str]]] = None
        self._topological_order_cache: Optional[List[str]] = None
        
        logger.info("Dependency tracker initialized")
    
    def update_dependencies(self, files: Dict[str, FileInfo]):
        """Update dependency graphs from file information."""
        self._clear_caches()
        
        # Clear existing graphs
        self.file_dependencies = DependencyGraph(set(), defaultdict(set), defaultdict(set))
        self.symbol_dependencies = DependencyGraph(set(), defaultdict(set), defaultdict(set))
        self.import_graph = DependencyGraph(set(), defaultdict(set), defaultdict(set))
        
        # Build file dependency graph
        for file_path, file_info in files.items():
            self.file_dependencies.nodes.add(file_path)
            
            for dep in file_info.dependencies:
                target_file = self._resolve_import_to_file(dep.target_file, files)
                if target_file:
                    self.file_dependencies.edges[file_path].add(target_file)
                    self.file_dependencies.reverse_edges[target_file].add(file_path)
                    self.file_dependencies.nodes.add(target_file)
        
        # Build symbol dependency graph
        for file_path, file_info in files.items():
            for symbol in file_info.symbols:
                symbol_key = f"{file_path}::{symbol.name}"
                self.symbol_dependencies.nodes.add(symbol_key)
                
                # Add parent relationships
                if symbol.parent:
                    parent_key = f"{file_path}::{symbol.parent}"
                    self.symbol_dependencies.edges[symbol_key].add(parent_key)
                    self.symbol_dependencies.reverse_edges[parent_key].add(symbol_key)
        
        # Build import graph
        for file_path, file_info in files.items():
            self.import_graph.nodes.add(file_path)
            for import_name in file_info.imports:
                self.import_graph.edges[file_path].add(import_name)
                self.import_graph.reverse_edges[import_name].add(file_path)
        
        logger.info(f"Updated dependency graphs: {len(self.file_dependencies.nodes)} files, "
                   f"{len(self.symbol_dependencies.nodes)} symbols")
    
    def get_file_dependencies(self, file_path: str) -> Set[str]:
        """Get all files that the given file depends on."""
        normalized_path = normalize_path(file_path)
        return self.file_dependencies.edges.get(normalized_path, set())
    
    def get_file_dependents(self, file_path: str) -> Set[str]:
        """Get all files that depend on the given file."""
        normalized_path = normalize_path(file_path)
        return self.file_dependencies.reverse_edges.get(normalized_path, set())
    
    def get_transitive_dependencies(self, file_path: str, max_depth: int = 10) -> Dict[int, Set[str]]:
        """Get transitive dependencies organized by depth level."""
        normalized_path = normalize_path(file_path)
        result = defaultdict(set)
        visited = set()
        queue = deque([(normalized_path, 0)])
        
        while queue and max_depth > 0:
            current_file, depth = queue.popleft()
            
            if current_file in visited or depth >= max_depth:
                continue
            
            visited.add(current_file)
            dependencies = self.file_dependencies.edges.get(current_file, set())
            
            if dependencies:
                result[depth + 1].update(dependencies)
                for dep in dependencies:
                    if dep not in visited:
                        queue.append((dep, depth + 1))
        
        return dict(result)
    
    def get_transitive_dependents(self, file_path: str, max_depth: int = 10) -> Dict[int, Set[str]]:
        """Get transitive dependents organized by depth level."""
        normalized_path = normalize_path(file_path)
        result = defaultdict(set)
        visited = set()
        queue = deque([(normalized_path, 0)])
        
        while queue and max_depth > 0:
            current_file, depth = queue.popleft()
            
            if current_file in visited or depth >= max_depth:
                continue
            
            visited.add(current_file)
            dependents = self.file_dependencies.reverse_edges.get(current_file, set())
            
            if dependents:
                result[depth + 1].update(dependents)
                for dep in dependents:
                    if dep not in visited:
                        queue.append((dep, depth + 1))
        
        return dict(result)
    
    def analyze_impact(self, changed_files: List[str]) -> ImpactAnalysis:
        """Analyze the impact of changing the given files."""
        changed_set = {normalize_path(f) for f in changed_files}
        directly_affected = set()
        transitively_affected = set()
        dependency_chains = {}
        
        # Find directly affected files
        for file_path in changed_set:
            direct_deps = self.get_file_dependents(file_path)
            directly_affected.update(direct_deps)
            
            # Record dependency chains
            for dep in direct_deps:
                dependency_chains[dep] = [file_path, dep]
        
        # Find transitively affected files
        for file_path in directly_affected.copy():
            transitive_deps = self.get_transitive_dependents(file_path, max_depth=5)
            
            for depth, deps in transitive_deps.items():
                transitively_affected.update(deps)
                
                # Record dependency chains
                for dep in deps:
                    if dep not in dependency_chains:
                        base_chain = dependency_chains.get(file_path, [file_path])
                        dependency_chains[dep] = base_chain + [dep]
        
        return ImpactAnalysis(
            changed_files=changed_set,
            directly_affected=directly_affected,
            transitively_affected=transitively_affected,
            total_affected=set(),  # Will be computed in __post_init__
            dependency_chain=dependency_chains
        )
    
    def find_circular_dependencies(self) -> List[List[str]]:
        """Find circular dependencies in the file dependency graph."""
        if self._circular_deps_cache is not None:
            return self._circular_deps_cache
        
        cycles = []
        visited = set()
        rec_stack = set()
        path = []
        
        def dfs(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in self.file_dependencies.edges.get(node, set()):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    # Found a cycle - extract it from the path
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    cycles.append(cycle)
                    return True
            
            rec_stack.remove(node)
            path.pop()
            return False
        
        for node in self.file_dependencies.nodes:
            if node not in visited:
                dfs(node)
        
        self._circular_deps_cache = cycles
        return cycles
    
    def get_topological_order(self) -> Optional[List[str]]:
        """Get topological ordering of files (None if cycles exist)."""
        if self._topological_order_cache is not None:
            return self._topological_order_cache
        
        # Check for cycles first
        if self.find_circular_dependencies():
            return None
        
        # Kahn's algorithm
        in_degree = defaultdict(int)
        for node in self.file_dependencies.nodes:
            in_degree[node] = 0
        
        for node in self.file_dependencies.nodes:
            for neighbor in self.file_dependencies.edges.get(node, set()):
                in_degree[neighbor] += 1
        
        queue = deque([node for node, degree in in_degree.items() if degree == 0])
        result = []
        
        while queue:
            node = queue.popleft()
            result.append(node)
            
            for neighbor in self.file_dependencies.edges.get(node, set()):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        if len(result) != len(self.file_dependencies.nodes):
            return None  # Cycle detected
        
        self._topological_order_cache = result
        return result
    
    def suggest_refactoring_order(self, files: List[str]) -> List[str]:
        """Suggest the order to refactor files to minimize breaks."""
        file_set = {normalize_path(f) for f in files}
        
        # Create subgraph with only the specified files
        subgraph_edges = {}
        for file_path in file_set:
            deps = self.file_dependencies.edges.get(file_path, set())
            subgraph_edges[file_path] = deps.intersection(file_set)
        
        # Topological sort on subgraph
        in_degree = {f: 0 for f in file_set}
        for file_path in file_set:
            for dep in subgraph_edges.get(file_path, set()):
                in_degree[dep] += 1
        
        queue = deque([f for f, degree in in_degree.items() if degree == 0])
        result = []
        
        while queue:
            file_path = queue.popleft()
            result.append(file_path)
            
            for dep in subgraph_edges.get(file_path, set()):
                in_degree[dep] -= 1
                if in_degree[dep] == 0:
                    queue.append(dep)
        
        # Add any remaining files (those in cycles)
        remaining = file_set - set(result)
        result.extend(sorted(remaining))
        
        return result
    
    def get_dependency_metrics(self) -> Dict[str, Any]:
        """Get various dependency metrics for the codebase."""
        metrics = {
            'total_files': len(self.file_dependencies.nodes),
            'total_dependencies': sum(len(deps) for deps in self.file_dependencies.edges.values()),
            'average_dependencies_per_file': 0,
            'max_dependencies': 0,
            'max_dependents': 0,
            'circular_dependencies': len(self.find_circular_dependencies()),
            'strongly_connected_components': 0,
            'dependency_depth': 0
        }
        
        if metrics['total_files'] > 0:
            metrics['average_dependencies_per_file'] = (
                metrics['total_dependencies'] / metrics['total_files']
            )
        
        # Find max dependencies and dependents
        for file_path in self.file_dependencies.nodes:
            deps_count = len(self.file_dependencies.edges.get(file_path, set()))
            dependents_count = len(self.file_dependencies.reverse_edges.get(file_path, set()))
            
            metrics['max_dependencies'] = max(metrics['max_dependencies'], deps_count)
            metrics['max_dependents'] = max(metrics['max_dependents'], dependents_count)
        
        # Calculate dependency depth
        topo_order = self.get_topological_order()
        if topo_order:
            metrics['dependency_depth'] = self._calculate_max_depth()
        
        return metrics
    
    def _resolve_import_to_file(self, import_name: str, files: Dict[str, FileInfo]) -> Optional[str]:
        """Resolve an import name to an actual file path."""
        # This is a simplified resolution - in practice, you'd need more
        # sophisticated logic based on the language's import system
        
        # Try direct file match
        if import_name in files:
            return import_name
        
        # Try adding common extensions
        for ext in ['.py', '.js', '.ts']:
            candidate = f"{import_name}{ext}"
            if candidate in files:
                return candidate
        
        # Try treating as module name
        for file_path in files:
            if os.path.basename(file_path).startswith(import_name):
                return file_path
        
        return None
    
    def _calculate_max_depth(self) -> int:
        """Calculate the maximum dependency depth."""
        max_depth = 0
        
        for node in self.file_dependencies.nodes:
            depth = self._calculate_node_depth(node, set())
            max_depth = max(max_depth, depth)
        
        return max_depth
    
    def _calculate_node_depth(self, node: str, visited: Set[str]) -> int:
        """Calculate the depth of a node in the dependency graph."""
        if node in visited:
            return 0  # Avoid infinite recursion in cycles
        
        visited.add(node)
        dependencies = self.file_dependencies.edges.get(node, set())
        
        if not dependencies:
            return 0
        
        max_child_depth = max(
            self._calculate_node_depth(dep, visited.copy()) 
            for dep in dependencies
        )
        
        return max_child_depth + 1
    
    def _clear_caches(self):
        """Clear cached results."""
        self._circular_deps_cache = None
        self._topological_order_cache = None