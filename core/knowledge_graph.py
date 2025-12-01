#!/usr/bin/env python3
"""
Knowledge Graph Integration for Universal Dependency Analyzer

Adds semantic relationships, concept mapping, and graph-based queries
to the existing indexing system.
"""

import json
import os
import time
from typing import Dict, List, Set, Optional, Tuple, Any
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from enum import Enum

@dataclass
class KnowledgeNode:
    """Represents a node in the knowledge graph."""
    id: str
    type: str  # symbol, file, concept, pattern, framework
    name: str
    attributes: Dict[str, Any]
    file_path: Optional[str] = None
    line_number: Optional[int] = None

@dataclass 
class KnowledgeEdge:
    """Represents a relationship in the knowledge graph."""
    source: str  # Node ID
    target: str  # Node ID
    relationship: str  # depends_on, implements, extends, calls, contains
    weight: float = 1.0
    attributes: Dict[str, Any] = None

class RelationType(Enum):
    """Types of relationships in the knowledge graph."""
    DEPENDS_ON = "depends_on"
    IMPLEMENTS = "implements"
    EXTENDS = "extends"
    CALLS = "calls"
    CONTAINS = "contains"
    SIMILAR_TO = "similar_to"
    PART_OF = "part_of"
    USES_PATTERN = "uses_pattern"
    HAS_FRAMEWORK = "has_framework"
    CONFIGURED_BY = "configured_by"

class KnowledgeGraph:
    """Enhanced knowledge graph for code analysis with local persistence."""
    
    def __init__(self, storage_path: str = "dependency_analysis/knowledge_graph.json"):
        self.storage_path = storage_path
        self.nodes: Dict[str, KnowledgeNode] = {}
        self.edges: List[KnowledgeEdge] = []
        self.adjacency: Dict[str, List[str]] = defaultdict(list)
        self.reverse_adjacency: Dict[str, List[str]] = defaultdict(list)
        
        # Semantic indexes
        self.nodes_by_type: Dict[str, List[str]] = defaultdict(list)
        self.concept_patterns: Dict[str, Set[str]] = defaultdict(set)
        self.framework_detection: Dict[str, List[str]] = defaultdict(list)
        
        # Load existing knowledge graph if available
        self.load_from_local_storage()
        
    def add_node(self, node: KnowledgeNode) -> None:
        """Add a node to the knowledge graph."""
        self.nodes[node.id] = node
        self.nodes_by_type[node.type].append(node.id)
        
        # Detect patterns and concepts
        self._detect_patterns(node)
        
    def add_edge(self, edge: KnowledgeEdge) -> None:
        """Add an edge to the knowledge graph."""
        self.edges.append(edge)
        self.adjacency[edge.source].append(edge.target)
        self.reverse_adjacency[edge.target].append(edge.source)
        
    def find_path(self, source: str, target: str, max_depth: int = 5) -> Optional[List[str]]:
        """Find shortest path between two nodes."""
        if source == target:
            return [source]
            
        visited = set()
        queue = deque([(source, [source])])
        
        while queue:
            current, path = queue.popleft()
            
            if len(path) > max_depth:
                continue
                
            if current in visited:
                continue
            visited.add(current)
            
            for neighbor in self.adjacency[current]:
                new_path = path + [neighbor]
                if neighbor == target:
                    return new_path
                queue.append((neighbor, new_path))
        
        return None
    
    def find_similar_components(self, node_id: str, threshold: float = 0.7) -> List[Tuple[str, float]]:
        """Find components similar to the given node."""
        if node_id not in self.nodes:
            return []
            
        node = self.nodes[node_id]
        similar = []
        
        # Compare with nodes of same type
        for candidate_id in self.nodes_by_type[node.type]:
            if candidate_id == node_id:
                continue
                
            similarity = self._calculate_similarity(node, self.nodes[candidate_id])
            if similarity >= threshold:
                similar.append((candidate_id, similarity))
        
        return sorted(similar, key=lambda x: x[1], reverse=True)
    
    def detect_architectural_patterns(self) -> Dict[str, List[str]]:
        """Detect common architectural patterns in the codebase."""
        patterns = defaultdict(list)
        
        # MVC Pattern
        controllers = [n for n in self.nodes_by_type.get('symbol', []) 
                      if 'controller' in self.nodes[n].name.lower()]
        models = [n for n in self.nodes_by_type.get('symbol', []) 
                 if 'model' in self.nodes[n].name.lower()]
        views = [n for n in self.nodes_by_type.get('file', []) 
                if any(ext in self.nodes[n].file_path.lower() if self.nodes[n].file_path else '' 
                      for ext in ['.html', '.template', '.view'])]
        
        if controllers and models:
            patterns['MVC'].extend(controllers + models + views)
        
        # Repository Pattern
        repositories = [n for n in self.nodes_by_type.get('symbol', []) 
                       if 'repository' in self.nodes[n].name.lower()]
        if repositories:
            patterns['Repository'].extend(repositories)
        
        # Factory Pattern
        factories = [n for n in self.nodes_by_type.get('symbol', []) 
                    if 'factory' in self.nodes[n].name.lower()]
        if factories:
            patterns['Factory'].extend(factories)
        
        # Singleton Pattern
        singletons = []
        for node_id in self.nodes_by_type.get('symbol', []):
            node = self.nodes[node_id]
            if 'singleton' in str(node.attributes).lower():
                singletons.append(node_id)
        if singletons:
            patterns['Singleton'].extend(singletons)
        
        return dict(patterns)
    
    def find_dependency_clusters(self, min_cluster_size: int = 3) -> List[List[str]]:
        """Find clusters of highly interconnected components."""
        clusters = []
        visited = set()
        
        for node_id in self.nodes:
            if node_id in visited:
                continue
                
            cluster = self._dfs_cluster(node_id, visited, set())
            if len(cluster) >= min_cluster_size:
                clusters.append(list(cluster))
        
        return clusters
    
    def get_impact_analysis(self, node_id: str, max_depth: int = 3) -> Dict[str, List[str]]:
        """Analyze the impact of changing a specific component."""
        if node_id not in self.nodes:
            return {}
        
        impact = {
            'direct_dependents': [],
            'indirect_dependents': [],
            'affected_patterns': [],
            'risk_level': 'low'
        }
        
        # Direct dependents
        direct = self.reverse_adjacency[node_id]
        impact['direct_dependents'] = direct
        
        # Indirect dependents (BFS)
        visited = set([node_id])
        queue = deque([(dep, 1) for dep in direct])
        
        while queue:
            current, depth = queue.popleft()
            if depth >= max_depth or current in visited:
                continue
            
            visited.add(current)
            impact['indirect_dependents'].append(current)
            
            for next_dep in self.reverse_adjacency[current]:
                if next_dep not in visited:
                    queue.append((next_dep, depth + 1))
        
        # Risk assessment
        total_impact = len(impact['direct_dependents']) + len(impact['indirect_dependents'])
        if total_impact > 10:
            impact['risk_level'] = 'high'
        elif total_impact > 5:
            impact['risk_level'] = 'medium'
        
        return impact
    
    def suggest_refactoring_opportunities(self) -> List[Dict[str, Any]]:
        """Suggest refactoring opportunities based on graph analysis."""
        suggestions = []
        
        # Find highly connected nodes (potential god classes)
        for node_id, neighbors in self.adjacency.items():
            if len(neighbors) > 15:  # High coupling threshold
                suggestions.append({
                    'type': 'high_coupling',
                    'node': node_id,
                    'description': f"Component '{self.nodes[node_id].name}' has {len(neighbors)} dependencies",
                    'suggestion': 'Consider breaking into smaller components',
                    'priority': 'high'
                })
        
        # Find orphaned nodes
        orphans = [node_id for node_id in self.nodes 
                  if not self.adjacency[node_id] and not self.reverse_adjacency[node_id]]
        if orphans:
            suggestions.append({
                'type': 'orphaned_components',
                'nodes': orphans,
                'description': f"Found {len(orphans)} disconnected components",
                'suggestion': 'Review if these components are still needed',
                'priority': 'medium'
            })
        
        # Find circular dependencies
        cycles = self._find_cycles()
        if cycles:
            suggestions.append({
                'type': 'circular_dependencies',
                'cycles': cycles,
                'description': f"Found {len(cycles)} circular dependency chains",
                'suggestion': 'Break circular dependencies using interfaces or dependency injection',
                'priority': 'high'
            })
        
        return suggestions
    
    def save_to_local_storage(self) -> bool:
        """Save knowledge graph to local JSON file."""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            
            # Convert sets to lists for JSON serialization
            concept_patterns_serializable = {
                k: list(v) for k, v in self.concept_patterns.items()
            }
            
            graph_data = {
                'metadata': {
                    'version': '1.0',
                    'created_at': str(os.path.getctime(self.storage_path)) if os.path.exists(self.storage_path) else None,
                    'updated_at': str(time.time()) if 'time' in globals() else None,
                    'node_count': len(self.nodes),
                    'edge_count': len(self.edges)
                },
                'nodes': [asdict(node) for node in self.nodes.values()],
                'edges': [asdict(edge) for edge in self.edges],
                'semantic_indexes': {
                    'nodes_by_type': dict(self.nodes_by_type),
                    'concept_patterns': concept_patterns_serializable,
                    'framework_detection': dict(self.framework_detection)
                },
                'adjacency': dict(self.adjacency),
                'reverse_adjacency': dict(self.reverse_adjacency)
            }
            
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(graph_data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Warning: Could not save knowledge graph: {e}")
            return False
    
    def load_from_local_storage(self) -> bool:
        """Load knowledge graph from local JSON file."""
        if not os.path.exists(self.storage_path):
            return False
        
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                graph_data = json.load(f)
            
            # Reconstruct nodes
            for node_data in graph_data.get('nodes', []):
                node = KnowledgeNode(**node_data)
                self.nodes[node.id] = node
            
            # Reconstruct edges
            for edge_data in graph_data.get('edges', []):
                if edge_data.get('attributes') is None:
                    edge_data['attributes'] = {}
                edge = KnowledgeEdge(**edge_data)
                self.edges.append(edge)
            
            # Reconstruct indexes
            semantic_indexes = graph_data.get('semantic_indexes', {})
            
            self.nodes_by_type = defaultdict(list, semantic_indexes.get('nodes_by_type', {}))
            
            # Convert lists back to sets for concept_patterns
            concept_patterns_data = semantic_indexes.get('concept_patterns', {})
            self.concept_patterns = defaultdict(set)
            for k, v in concept_patterns_data.items():
                self.concept_patterns[k] = set(v)
            
            self.framework_detection = defaultdict(list, semantic_indexes.get('framework_detection', {}))
            
            # Reconstruct adjacency lists
            self.adjacency = defaultdict(list, graph_data.get('adjacency', {}))
            self.reverse_adjacency = defaultdict(list, graph_data.get('reverse_adjacency', {}))
            
            print(f"✅ Loaded knowledge graph: {len(self.nodes)} nodes, {len(self.edges)} edges")
            return True
            
        except Exception as e:
            print(f"Warning: Could not load knowledge graph: {e}")
            return False
    
    def get_storage_info(self) -> Dict[str, Any]:
        """Get information about local storage."""
        if not os.path.exists(self.storage_path):
            return {"exists": False, "path": self.storage_path}
        
        stat = os.stat(self.storage_path)
        return {
            "exists": True,
            "path": self.storage_path,
            "size_bytes": stat.st_size,
            "size_mb": round(stat.st_size / (1024 * 1024), 2),
            "last_modified": stat.st_mtime,
            "nodes": len(self.nodes),
            "edges": len(self.edges)
        }
    
    def export_graph(self, format: str = 'json') -> str:
        """Export the knowledge graph in various formats."""
        if format == 'json':
            return json.dumps({
                'nodes': [asdict(node) for node in self.nodes.values()],
                'edges': [asdict(edge) for edge in self.edges]
            }, indent=2)
        elif format == 'dot':
            return self._export_dot()
        elif format == 'cypher':
            return self._export_cypher()
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _detect_patterns(self, node: KnowledgeNode) -> None:
        """Detect patterns and frameworks from node characteristics."""
        name_lower = node.name.lower()
        
        # Framework detection
        frameworks = {
            'fastapi': ['fastapi', 'starlette', 'pydantic'],
            'django': ['django', 'models.model', 'views.view'],
            'flask': ['flask', 'app.route', 'request'],
            'react': ['react', 'component', 'usestate'],
            'angular': ['angular', 'component', 'service'],
            'spring': ['springframework', 'autowired', 'component']
        }
        
        for framework, indicators in frameworks.items():
            if any(indicator in name_lower for indicator in indicators):
                self.framework_detection[framework].append(node.id)
        
        # Pattern detection
        patterns = {
            'controller': ['controller', 'handler', 'endpoint'],
            'service': ['service', 'business', 'logic'],
            'repository': ['repository', 'dao', 'data'],
            'model': ['model', 'entity', 'dto'],
            'factory': ['factory', 'builder', 'creator'],
            'singleton': ['singleton', 'instance'],
            'observer': ['observer', 'listener', 'subscriber']
        }
        
        for pattern, indicators in patterns.items():
            if any(indicator in name_lower for indicator in indicators):
                self.concept_patterns[pattern].add(node.id)
    
    def _calculate_similarity(self, node1: KnowledgeNode, node2: KnowledgeNode) -> float:
        """Calculate similarity between two nodes."""
        if node1.type != node2.type:
            return 0.0
        
        # Name similarity (simple approach)
        name_sim = len(set(node1.name.lower().split()) & set(node2.name.lower().split()))
        name_sim = name_sim / max(len(node1.name.split()), len(node2.name.split()))
        
        # Attribute similarity
        attr_sim = 0.0
        if node1.attributes and node2.attributes:
            common_keys = set(node1.attributes.keys()) & set(node2.attributes.keys())
            if common_keys:
                attr_sim = len(common_keys) / max(len(node1.attributes), len(node2.attributes))
        
        return (name_sim + attr_sim) / 2
    
    def _dfs_cluster(self, node_id: str, visited: Set[str], current_cluster: Set[str]) -> Set[str]:
        """DFS to find connected components for clustering."""
        if node_id in visited:
            return current_cluster
        
        visited.add(node_id)
        current_cluster.add(node_id)
        
        for neighbor in self.adjacency[node_id] + self.reverse_adjacency[node_id]:
            if neighbor not in visited:
                self._dfs_cluster(neighbor, visited, current_cluster)
        
        return current_cluster
    
    def _find_cycles(self) -> List[List[str]]:
        """Find circular dependencies using DFS."""
        cycles = []
        visited = set()
        rec_stack = set()
        
        def dfs(node: str, path: List[str]) -> None:
            if node in rec_stack:
                # Found cycle
                cycle_start = path.index(node)
                cycles.append(path[cycle_start:] + [node])
                return
            
            if node in visited:
                return
            
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in self.adjacency[node]:
                dfs(neighbor, path + [neighbor])
            
            rec_stack.remove(node)
        
        for node in self.nodes:
            if node not in visited:
                dfs(node, [node])
        
        return cycles
    
    def _export_dot(self) -> str:
        """Export as DOT format for Graphviz."""
        lines = ["digraph knowledge_graph {"]
        
        # Add nodes
        for node in self.nodes.values():
            lines.append(f'  "{node.id}" [label="{node.name}" shape=box];')
        
        # Add edges
        for edge in self.edges:
            lines.append(f'  "{edge.source}" -> "{edge.target}" [label="{edge.relationship}"];')
        
        lines.append("}")
        return "\n".join(lines)
    
    def _export_cypher(self) -> str:
        """Export as Cypher queries for Neo4j."""
        queries = []
        
        # Create nodes
        for node in self.nodes.values():
            attrs = json.dumps(node.attributes) if node.attributes else "{}"
            queries.append(f"CREATE (:{node.type} {{id: '{node.id}', name: '{node.name}', attributes: {attrs}}})")
        
        # Create relationships
        for edge in self.edges:
            queries.append(f"MATCH (a {{id: '{edge.source}'}}), (b {{id: '{edge.target}'}}) CREATE (a)-[:{edge.relationship.upper()}]->(b)")
        
        return ";\n".join(queries) + ";"


def integrate_with_existing_analyzer():
    """Integration point with the existing dependency analyzer."""
    # This would be called from the main analyzer to enhance it with knowledge graph
    pass


if __name__ == "__main__":
    # Example usage
    kg = KnowledgeGraph()
    
    # Add sample nodes
    kg.add_node(KnowledgeNode("main.py", "file", "main.py", {"language": "python"}))
    kg.add_node(KnowledgeNode("UserController", "symbol", "UserController", {"type": "class"}))
    
    # Add relationships
    kg.add_edge(KnowledgeEdge("main.py", "UserController", RelationType.CONTAINS.value))
    
    print("Knowledge Graph created successfully!")