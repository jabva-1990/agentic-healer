#!/usr/bin/env python3
"""
Enhanced Query Tool with Knowledge Graph Integration

Adds semantic analysis, pattern detection, and graph-based insights
to the existing dependency analysis system.
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Any, Set

# Import existing functionality
from core.knowledge_graph import KnowledgeGraph, KnowledgeNode, KnowledgeEdge, RelationType

def load_dependencies():
    """Load dependencies from the JSON file."""
    dependencies_path = Path("dependency_analysis/dependencies.json")
    if dependencies_path.exists():
        with open(dependencies_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"files": {}, "dependencies": {}}

class EnhancedDependencyAnalyzer:
    """Enhanced analyzer with knowledge graph capabilities."""
    
    def __init__(self):
        self.kg = KnowledgeGraph()
        self.dependency_data = None
        
    def load_and_enhance_data(self) -> bool:
        """Load existing dependency data and build knowledge graph."""
        self.dependency_data = load_dependencies()
        if not self.dependency_data:
            return False
        
        # Try to load existing knowledge graph first
        if not self.kg.load_from_local_storage():
            print("📊 Building new knowledge graph...")
            self._build_knowledge_graph()
            # Save the newly built knowledge graph
            if self.kg.save_to_local_storage():
                print("✅ Knowledge graph saved locally")
        else:
            print("📊 Using cached knowledge graph")
        
        return True
    
    def _build_knowledge_graph(self):
        """Build knowledge graph from dependency data."""
        # Add file nodes
        for file_path, file_info in self.dependency_data['files'].items():
            node = KnowledgeNode(
                id=f"file:{file_path}",
                type="file",
                name=file_path,
                attributes={
                    "language": file_info['language'],
                    "symbols": file_info['symbols'],
                    "deps_count": file_info['deps_count']
                },
                file_path=file_path
            )
            self.kg.add_node(node)
        
        # Add dependency edges
        for source_file, deps in self.dependency_data['dependencies'].items():
            source_id = f"file:{source_file}"
            
            for dep in deps:
                target_id = f"file:{dep['target']}" if dep['target'] in self.dependency_data['files'] else f"external:{dep['target']}"
                
                # Add external dependencies as nodes
                if target_id.startswith("external:"):
                    ext_node = KnowledgeNode(
                        id=target_id,
                        type="external",
                        name=dep['target'],
                        attributes={"type": "external_dependency"}
                    )
                    self.kg.add_node(ext_node)
                
                edge = KnowledgeEdge(
                    source=source_id,
                    target=target_id,
                    relationship=dep['type'],
                    attributes={"dependency_type": dep['type']}
                )
                self.kg.add_edge(edge)
    
    def analyze_architecture(self) -> Dict[str, Any]:
        """Perform architectural analysis using knowledge graph."""
        analysis = {}
        
        # Detect patterns
        patterns = self.kg.detect_architectural_patterns()
        analysis['architectural_patterns'] = patterns
        
        # Find clusters
        clusters = self.kg.find_dependency_clusters()
        analysis['dependency_clusters'] = clusters
        
        # Framework detection
        frameworks = {}
        for framework, files in self.kg.framework_detection.items():
            if files:
                frameworks[framework] = [self.kg.nodes[f].name for f in files]
        analysis['detected_frameworks'] = frameworks
        
        return analysis
    
    def find_critical_components(self) -> List[Dict[str, Any]]:
        """Find components critical to the system architecture."""
        critical = []
        
        # High-dependency components
        for node_id, neighbors in self.kg.adjacency.items():
            if len(neighbors) > 5:  # Threshold for high dependency
                node = self.kg.nodes[node_id]
                critical.append({
                    'component': node.name,
                    'type': 'high_dependency',
                    'dependency_count': len(neighbors),
                    'risk': 'high' if len(neighbors) > 10 else 'medium'
                })
        
        # Highly depended-upon components
        for node_id, dependents in self.kg.reverse_adjacency.items():
            if len(dependents) > 5:
                node = self.kg.nodes[node_id]
                critical.append({
                    'component': node.name,
                    'type': 'highly_depended_upon',
                    'dependent_count': len(dependents),
                    'risk': 'high' if len(dependents) > 10 else 'medium'
                })
        
        return critical
    
    def suggest_optimizations(self) -> List[Dict[str, Any]]:
        """Suggest optimizations based on graph analysis."""
        suggestions = self.kg.suggest_refactoring_opportunities()
        
        # Add more specific suggestions
        frameworks = self.kg.framework_detection
        
        # Framework consolidation suggestions
        if len(frameworks) > 3:
            suggestions.append({
                'type': 'framework_consolidation',
                'description': f"Multiple frameworks detected: {list(frameworks.keys())}",
                'suggestion': 'Consider consolidating to fewer frameworks for better maintainability',
                'priority': 'medium'
            })
        
        return suggestions
    
    def query_enhanced_dependencies(self, file_path: str) -> Dict[str, Any]:
        """Enhanced dependency query with semantic information."""
        # Get basic dependencies
        basic_deps = self._get_basic_dependencies(file_path)
        
        # Add semantic enhancements
        node_id = f"file:{file_path}"
        if node_id not in self.kg.nodes:
            return {"error": f"File not found: {file_path}"}
        
        # Impact analysis
        impact = self.kg.get_impact_analysis(node_id)
        
        # Similar components
        similar = self.kg.find_similar_components(node_id)
        
        # Dependency path analysis
        external_deps = [f"external:{dep['target']}" for dep in basic_deps.get('dependencies', []) 
                        if f"external:{dep['target']}" in self.kg.nodes]
        
        paths_to_external = {}
        for ext_dep in external_deps[:5]:  # Limit to first 5
            path = self.kg.find_path(node_id, ext_dep)
            if path:
                paths_to_external[ext_dep] = path
        
        return {
            'basic_info': basic_deps,
            'impact_analysis': impact,
            'similar_components': [(self.kg.nodes[s[0]].name, s[1]) for s in similar[:3]],
            'dependency_paths': paths_to_external,
            'architectural_role': self._determine_architectural_role(node_id)
        }
    
    def _get_basic_dependencies(self, file_path: str) -> Dict[str, Any]:
        """Get basic dependency information."""
        # Normalize path
        if file_path not in self.dependency_data['dependencies']:
            matches = [f for f in self.dependency_data['dependencies'].keys() if f.endswith(file_path)]
            if matches:
                file_path = matches[0]
            else:
                return {"error": f"File not found: {file_path}"}
        
        file_info = self.dependency_data['files'][file_path]
        dependencies = self.dependency_data['dependencies'][file_path]
        
        return {
            'file_path': file_path,
            'language': file_info['language'],
            'symbols': file_info['symbols'],
            'dependencies': dependencies
        }
    
    def _determine_architectural_role(self, node_id: str) -> str:
        """Determine the architectural role of a component."""
        node = self.kg.nodes[node_id]
        name_lower = node.name.lower()
        
        # Check for common patterns
        roles = []
        
        if 'main' in name_lower or 'app' in name_lower:
            roles.append('entry_point')
        if 'controller' in name_lower or 'handler' in name_lower:
            roles.append('controller')
        if 'service' in name_lower or 'business' in name_lower:
            roles.append('service')
        if 'model' in name_lower or 'entity' in name_lower:
            roles.append('model')
        if 'util' in name_lower or 'helper' in name_lower:
            roles.append('utility')
        if 'config' in name_lower or 'setting' in name_lower:
            roles.append('configuration')
        if 'test' in name_lower:
            roles.append('test')
        
        # Analyze connectivity patterns
        incoming = len(self.kg.reverse_adjacency.get(node_id, []))
        outgoing = len(self.kg.adjacency.get(node_id, []))
        
        if incoming > outgoing * 2:
            roles.append('shared_utility')
        elif outgoing > incoming * 2:
            roles.append('integration_point')
        
        return ', '.join(roles) if roles else 'standard_component'


def main():
    """Enhanced main entry point with knowledge graph features."""
    if len(sys.argv) < 2:
        print("Enhanced Dependency Query Tool with Knowledge Graph")
        print("\nUsage:")
        print("  python enhanced_query.py <file_path>     # Enhanced dependency query")
        print("  python enhanced_query.py --architecture  # Architectural analysis")
        print("  python enhanced_query.py --critical      # Find critical components")
        print("  python enhanced_query.py --optimize      # Optimization suggestions")
        print("  python enhanced_query.py --export <format>  # Export graph (json/dot/cypher)")
        sys.exit(1)
    
    analyzer = EnhancedDependencyAnalyzer()
    if not analyzer.load_and_enhance_data():
        print("❌ No dependency data found. Run analysis first:")
        print("   python fast_main.py /path/to/repository")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == '--architecture':
        print("🏗️  Architectural Analysis")
        print("=" * 50)
        analysis = analyzer.analyze_architecture()
        
        print(f"\n📋 Detected Patterns:")
        for pattern, components in analysis['architectural_patterns'].items():
            print(f"  {pattern}: {len(components)} components")
        
        print(f"\n🔗 Dependency Clusters:")
        for i, cluster in enumerate(analysis['dependency_clusters'], 1):
            print(f"  Cluster {i}: {len(cluster)} components")
        
        print(f"\n🚀 Detected Frameworks:")
        for framework, files in analysis['detected_frameworks'].items():
            print(f"  {framework}: {len(files)} files")
    
    elif command == '--critical':
        print("⚠️  Critical Components Analysis")
        print("=" * 50)
        critical = analyzer.find_critical_components()
        
        for comp in critical:
            print(f"\n🔴 {comp['component']}")
            print(f"   Type: {comp['type']}")
            if 'dependency_count' in comp:
                print(f"   Dependencies: {comp['dependency_count']}")
            if 'dependent_count' in comp:
                print(f"   Dependents: {comp['dependent_count']}")
            print(f"   Risk: {comp['risk']}")
    
    elif command == '--optimize':
        print("💡 Optimization Suggestions")
        print("=" * 50)
        suggestions = analyzer.suggest_optimizations()
        
        for i, suggestion in enumerate(suggestions, 1):
            print(f"\n{i}. {suggestion['type'].replace('_', ' ').title()}")
            print(f"   {suggestion['description']}")
            print(f"   💡 {suggestion['suggestion']}")
            print(f"   Priority: {suggestion['priority']}")
    
    elif command == '--export':
        format_type = sys.argv[2] if len(sys.argv) > 2 else 'json'
        output = analyzer.kg.export_graph(format_type)
        
        filename = f"knowledge_graph.{format_type}"
        with open(filename, 'w') as f:
            f.write(output)
        print(f"📊 Knowledge graph exported to: {filename}")
    
    else:
        # Enhanced file query
        result = analyzer.query_enhanced_dependencies(command)
        
        if 'error' in result:
            print(f"❌ {result['error']}")
            return
        
        basic = result['basic_info']
        print(f"🔍 Enhanced Analysis: {basic['file_path']}")
        print(f"📋 Language: {basic['language']}")
        print(f"🔢 Symbols: {basic['symbols']}")
        print(f"🏗️  Role: {result['architectural_role']}")
        print("-" * 50)
        
        print(f"\n📦 Dependencies ({len(basic['dependencies'])}):")
        for dep in basic['dependencies']:
            print(f"   {dep['type']}: {dep['target']}")
        
        impact = result['impact_analysis']
        print(f"\n💥 Impact Analysis:")
        print(f"   Direct dependents: {len(impact['direct_dependents'])}")
        print(f"   Indirect dependents: {len(impact['indirect_dependents'])}")
        print(f"   Risk level: {impact['risk_level']}")
        
        if result['similar_components']:
            print(f"\n🔗 Similar Components:")
            for name, similarity in result['similar_components']:
                print(f"   {name} (similarity: {similarity:.2f})")


if __name__ == "__main__":
    main()