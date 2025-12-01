"""
Universal parsers for ANY file type containing structured data,
dependencies, symbols, and cross-references.
"""

import json
import yaml
import re
import xml.etree.ElementTree as ET
from typing import Dict, List, Set, Optional, Any
import hashlib
import os
from pathlib import Path

from .ast_parser import BaseLanguageParser
from .types import (
    Symbol, SymbolType, Language, Position, Range, FileInfo, Dependency,
    normalize_path
)


class UniversalBaseParser(BaseLanguageParser):
    """Enhanced base parser with utility methods for universal parsing."""
    
    def _create_file_info(self, file_path: str, content: str, symbols: List[Symbol], 
                         dependencies: List[Dependency], imports: List[str]) -> FileInfo:
        """Create FileInfo object with computed hash and metadata."""
        content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
        last_modified = os.path.getmtime(file_path) if os.path.exists(file_path) else 0
        
        return FileInfo(
            file_path=normalize_path(file_path),
            language=self.language,
            last_modified=last_modified,
            symbols=symbols,
            dependencies=dependencies,
            imports=imports,
            hash=content_hash
        )


class UniversalFileParser:
    """Universal parser that can handle any structured file format."""
    
    def __init__(self):
        self.parsers = {
            Language.JSON: JsonParser(),
            Language.YAML: YamlParser(),
            Language.TOML: TomlParser(),
            Language.XML: XmlParser(),
            Language.INI: IniParser(),
            Language.ENV: EnvParser(),
            Language.DOCKERFILE: DockerfileParser(),
            Language.KUBERNETES: KubernetesParser(),
            Language.TERRAFORM: TerraformParser(),
            Language.SQL: SqlParser(),
            Language.GRAPHQL: GraphQLParser(),
            Language.HTML: HtmlParser(),
            Language.CSS: CssParser(),
            Language.MARKDOWN: MarkdownParser(),
            Language.MAKEFILE: MakefileParser(),
            Language.NPM: PackageJsonParser(),
            Language.MAVEN: MavenParser(),
            Language.GRADLE: GradleParser(),
            Language.PROPERTIES: PropertiesParser(),
        }
    
    def can_parse(self, language: Language) -> bool:
        """Check if we can parse this language/file type."""
        return language in self.parsers
    
    def parse_file(self, file_path: str, content: str, language: Language) -> Optional[FileInfo]:
        """Parse any supported file type."""
        if not self.can_parse(language):
            return None
        
        parser = self.parsers[language]
        return parser.parse_file(file_path, content)


class JsonParser(UniversalBaseParser):
    """Parser for JSON files."""
    
    def __init__(self):
        super().__init__(Language.JSON)
    
    def parse_file(self, file_path: str, content: str) -> FileInfo:
        symbols = []
        dependencies = []
        imports = []
        
        try:
            data = json.loads(content)
            self._extract_json_symbols(data, symbols, file_path, [])
            self._extract_json_references(data, dependencies, file_path)
        except json.JSONDecodeError as e:
            # Handle malformed JSON
            pass
        
        return self._create_file_info(file_path, content, symbols, dependencies, imports)
    
    def _extract_json_symbols(self, data: Any, symbols: List[Symbol], file_path: str, path: List[str]):
        """Recursively extract symbols from JSON data."""
        if isinstance(data, dict):
            for key, value in data.items():
                current_path = path + [key]
                
                # Create symbol for this key
                symbols.append(Symbol(
                    name=key,
                    symbol_type=self._get_json_symbol_type(key, value),
                    file_path=normalize_path(file_path),
                    range=Range(Position(1, 0), Position(1, 0)),  # JSON doesn't have precise locations
                    parent='.'.join(path) if path else None
                ))
                
                # Recurse into nested structures
                if isinstance(value, (dict, list)):
                    self._extract_json_symbols(value, symbols, file_path, current_path)
        
        elif isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, (dict, list)):
                    self._extract_json_symbols(item, symbols, file_path, path + [str(i)])
    
    def _get_json_symbol_type(self, key: str, value: Any) -> SymbolType:
        """Determine symbol type based on JSON key and value."""
        key_lower = key.lower()
        
        if key_lower in ['dependencies', 'devdependencies', 'peerdependencies']:
            return SymbolType.PACKAGE_DEPENDENCY
        elif key_lower in ['scripts']:
            return SymbolType.NPM_SCRIPT
        elif key_lower in ['schema', '$schema']:
            return SymbolType.JSON_SCHEMA
        elif isinstance(value, dict):
            return SymbolType.CONFIG_SECTION
        else:
            return SymbolType.CONFIG_KEY
    
    def _extract_json_references(self, data: Any, dependencies: List[Dependency], file_path: str):
        """Extract references and dependencies from JSON."""
        if isinstance(data, dict):
            # Handle common reference patterns
            for key, value in data.items():
                if key in ['$ref', 'extends', 'import', 'include']:
                    if isinstance(value, str):
                        dependencies.append(Dependency(
                            source_file=normalize_path(file_path),
                            target_file=value,
                            dependency_type=key
                        ))
                elif isinstance(value, (dict, list)):
                    self._extract_json_references(value, dependencies, file_path)
        
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, (dict, list)):
                    self._extract_json_references(item, dependencies, file_path)


class YamlParser(UniversalBaseParser):
    """Parser for YAML files."""
    
    def __init__(self):
        super().__init__(Language.YAML)
    
    def parse_file(self, file_path: str, content: str) -> FileInfo:
        symbols = []
        dependencies = []
        imports = []
        
        try:
            # Parse multiple YAML documents
            docs = list(yaml.safe_load_all(content))
            
            for doc_idx, doc in enumerate(docs):
                if doc:
                    self._extract_yaml_symbols(doc, symbols, file_path, [], doc_idx)
                    self._extract_yaml_references(doc, dependencies, file_path)
        except yaml.YAMLError:
            pass
        
        return self._create_file_info(file_path, content, symbols, dependencies, imports)
    
    def _extract_yaml_symbols(self, data: Any, symbols: List[Symbol], file_path: str, path: List[str], doc_idx: int = 0):
        """Extract symbols from YAML data."""
        if isinstance(data, dict):
            for key, value in data.items():
                current_path = path + [str(key)]
                
                symbols.append(Symbol(
                    name=str(key),
                    symbol_type=self._get_yaml_symbol_type(key, value),
                    file_path=normalize_path(file_path),
                    range=Range(Position(1, 0), Position(1, 0)),
                    parent='.'.join(path) if path else f"doc_{doc_idx}"
                ))
                
                if isinstance(value, (dict, list)):
                    self._extract_yaml_symbols(value, symbols, file_path, current_path, doc_idx)
        
        elif isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, (dict, list)):
                    self._extract_yaml_symbols(item, symbols, file_path, path + [str(i)], doc_idx)
    
    def _get_yaml_symbol_type(self, key: str, value: Any) -> SymbolType:
        """Determine YAML symbol type."""
        key_str = str(key).lower()
        
        # Kubernetes-specific
        if key_str == 'kind':
            return SymbolType.K8S_RESOURCE
        elif key_str in ['apiversion', 'metadata', 'spec']:
            return SymbolType.CONFIG_SECTION
        # Ansible-specific
        elif key_str in ['tasks', 'handlers', 'plays']:
            return SymbolType.ANSIBLE_TASK
        elif key_str == 'playbook':
            return SymbolType.ANSIBLE_PLAYBOOK
        # Docker Compose
        elif key_str in ['services', 'networks', 'volumes']:
            return SymbolType.CONTAINER_SERVICE
        elif isinstance(value, dict):
            return SymbolType.CONFIG_SECTION
        else:
            return SymbolType.CONFIG_KEY
    
    def _extract_yaml_references(self, data: Any, dependencies: List[Dependency], file_path: str):
        """Extract YAML references and anchors."""
        if isinstance(data, dict):
            for key, value in data.items():
                # Handle YAML anchors and references
                if isinstance(value, str) and value.startswith('*'):
                    dependencies.append(Dependency(
                        source_file=normalize_path(file_path),
                        target_file=value[1:],  # Remove the *
                        dependency_type="yaml_reference"
                    ))
                elif isinstance(value, (dict, list)):
                    self._extract_yaml_references(value, dependencies, file_path)
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, (dict, list)):
                    self._extract_yaml_references(item, dependencies, file_path)


class DockerfileParser(UniversalBaseParser):
    """Parser for Dockerfile."""
    
    def __init__(self):
        super().__init__(Language.DOCKERFILE)
    
    def parse_file(self, file_path: str, content: str) -> FileInfo:
        symbols = []
        dependencies = []
        imports = []
        
        lines = content.split('\\n')
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            parts = line.split()
            if not parts:
                continue
            
            instruction = parts[0].upper()
            
            if instruction == 'FROM':
                image = parts[1] if len(parts) > 1 else ''
                symbols.append(Symbol(
                    name=f"base_image_{image}",
                    symbol_type=SymbolType.CONTAINER_IMAGE,
                    file_path=normalize_path(file_path),
                    range=Range(Position(line_num, 0), Position(line_num, len(line)))
                ))
                dependencies.append(Dependency(
                    source_file=normalize_path(file_path),
                    target_file=image,
                    dependency_type="base_image"
                ))
            
            elif instruction in ['COPY', 'ADD']:
                if len(parts) >= 3:
                    source = parts[1]
                    symbols.append(Symbol(
                        name=f"file_copy_{source}",
                        symbol_type=SymbolType.REFERENCE,
                        file_path=normalize_path(file_path),
                        range=Range(Position(line_num, 0), Position(line_num, len(line)))
                    ))
            
            elif instruction == 'RUN':
                command = ' '.join(parts[1:])
                symbols.append(Symbol(
                    name=f"run_command_{line_num}",
                    symbol_type=SymbolType.BUILD_TASK,
                    file_path=normalize_path(file_path),
                    range=Range(Position(line_num, 0), Position(line_num, len(line))),
                    docstring=command
                ))
        
        return self._create_file_info(file_path, content, symbols, dependencies, imports)


class KubernetesParser(YamlParser):
    """Specialized parser for Kubernetes YAML files."""
    
    def __init__(self):
        super().__init__()
        self.language = Language.KUBERNETES
    
    def _get_yaml_symbol_type(self, key: str, value: Any) -> SymbolType:
        """Kubernetes-specific symbol types."""
        key_str = str(key).lower()
        
        if key_str == 'kind':
            return SymbolType.K8S_RESOURCE
        elif key_str == 'namespace':
            return SymbolType.K8S_NAMESPACE
        elif key_str in ['service', 'services']:
            return SymbolType.K8S_SERVICE
        elif key_str in ['deployment', 'deployments']:
            return SymbolType.K8S_DEPLOYMENT
        else:
            return super()._get_yaml_symbol_type(key, value)


class SqlParser(UniversalBaseParser):
    """Parser for SQL files."""
    
    def __init__(self):
        super().__init__(Language.SQL)
    
    def parse_file(self, file_path: str, content: str) -> FileInfo:
        symbols = []
        dependencies = []
        imports = []
        
        # Simple SQL parsing using regex
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip().upper()
            
            # CREATE TABLE
            table_match = re.match(r'CREATE\s+TABLE\s+([\w.]+)', line)
            if table_match:
                table_name = table_match.group(1)
                symbols.append(Symbol(
                    name=table_name,
                    symbol_type=SymbolType.DATABASE_TABLE,
                    file_path=normalize_path(file_path),
                    range=Range(Position(line_num, 0), Position(line_num, len(line)))
                ))
            
            # CREATE VIEW
            view_match = re.match(r'CREATE\s+VIEW\s+([\w.]+)', line)
            if view_match:
                view_name = view_match.group(1)
                symbols.append(Symbol(
                    name=view_name,
                    symbol_type=SymbolType.SQL_VIEW,
                    file_path=normalize_path(file_path),
                    range=Range(Position(line_num, 0), Position(line_num, len(line)))
                ))
            
            # REFERENCES (Foreign Keys)
            ref_match = re.search(r'REFERENCES\s+([\w.]+)', line)
            if ref_match:
                referenced_table = ref_match.group(1)
                dependencies.append(Dependency(
                    source_file=normalize_path(file_path),
                    target_file=referenced_table,
                    dependency_type="foreign_key"
                ))
        
        return self._create_file_info(file_path, content, symbols, dependencies, imports)


class CssParser(UniversalBaseParser):
    """Parser for CSS files."""
    
    def __init__(self):
        super().__init__(Language.CSS)
    
    def parse_file(self, file_path: str, content: str) -> FileInfo:
        symbols = []
        dependencies = []
        imports = []
        
        # Parse CSS selectors and imports
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            
            # @import statements
            import_match = re.match(r'@import\s+["\']([^"\']*)["\'];?', line)
            if import_match:
                imported_file = import_match.group(1)
                dependencies.append(Dependency(
                    source_file=normalize_path(file_path),
                    target_file=imported_file,
                    dependency_type="css_import"
                ))
                imports.append(imported_file)
            
            # CSS classes
            class_matches = re.findall(r'\.([a-zA-Z][\w-]*)', line)
            for class_name in class_matches:
                symbols.append(Symbol(
                    name=class_name,
                    symbol_type=SymbolType.CSS_CLASS,
                    file_path=normalize_path(file_path),
                    range=Range(Position(line_num, 0), Position(line_num, len(line)))
                ))
            
            # CSS IDs
            id_matches = re.findall(r'#([a-zA-Z][\w-]*)', line)
            for id_name in id_matches:
                symbols.append(Symbol(
                    name=id_name,
                    symbol_type=SymbolType.CSS_ID,
                    file_path=normalize_path(file_path),
                    range=Range(Position(line_num, 0), Position(line_num, len(line)))
                ))
        
        return self._create_file_info(file_path, content, symbols, dependencies, imports)


class PackageJsonParser(JsonParser):
    """Specialized parser for package.json files."""
    
    def __init__(self):
        super().__init__()
        self.language = Language.NPM
    
    def _get_json_symbol_type(self, key: str, value: Any) -> SymbolType:
        """Package.json specific symbol types."""
        key_lower = key.lower()
        
        if key_lower in ['dependencies', 'devdependencies', 'peerdependencies']:
            return SymbolType.PACKAGE_DEPENDENCY
        elif key_lower == 'scripts':
            return SymbolType.NPM_SCRIPT
        else:
            return super()._get_json_symbol_type(key, value)


# Add more specialized parsers for other formats...

class MakefileParser(UniversalBaseParser):
    """Parser for Makefiles."""
    
    def __init__(self):
        super().__init__(Language.MAKEFILE)
    
    def parse_file(self, file_path: str, content: str) -> FileInfo:
        symbols = []
        dependencies = []
        imports = []
        
        lines = content.split('\\n')
        
        for line_num, line in enumerate(lines, 1):
            line = line.rstrip()
            
            # Make targets (lines ending with :)
            if ':' in line and not line.startswith('\t'):
                target_line = line.split(':')[0].strip()
                targets = target_line.split()
                
                for target in targets:
                    if target and not target.startswith('.'):
                        symbols.append(Symbol(
                            name=target,
                            symbol_type=SymbolType.BUILD_TARGET,
                            file_path=normalize_path(file_path),
                            range=Range(Position(line_num, 0), Position(line_num, len(line)))
                        ))
                
                # Dependencies after the colon
                if ':' in line:
                    deps_part = line.split(':', 1)[1].strip()
                    if deps_part:
                        deps = deps_part.split()
                        for dep in deps:
                            dependencies.append(Dependency(
                                source_file=normalize_path(file_path),
                                target_file=dep,
                                dependency_type="make_dependency"
                            ))
            
            # Include statements
            elif line.startswith('include ') or line.startswith('-include '):
                included_file = line.split()[1] if len(line.split()) > 1 else ''
                if included_file:
                    dependencies.append(Dependency(
                        source_file=normalize_path(file_path),
                        target_file=included_file,
                        dependency_type="make_include"
                    ))
                    imports.append(included_file)
        
        return self._create_file_info(file_path, content, symbols, dependencies, imports)


# Base implementations for other parsers
class TomlParser(UniversalBaseParser):
    def __init__(self):
        super().__init__(Language.TOML)
    
    def parse_file(self, file_path: str, content: str) -> FileInfo:
        # TODO: Implement TOML parsing (similar to JSON/YAML)
        return self._create_file_info(file_path, content, [], [], [])


class XmlParser(UniversalBaseParser):
    def __init__(self):
        super().__init__(Language.XML)
    
    def parse_file(self, file_path: str, content: str) -> FileInfo:
        # TODO: Implement XML parsing
        return self._create_file_info(file_path, content, [], [], [])


class IniParser(UniversalBaseParser):
    def __init__(self):
        super().__init__(Language.INI)
    
    def parse_file(self, file_path: str, content: str) -> FileInfo:
        # TODO: Implement INI parsing
        return self._create_file_info(file_path, content, [], [], [])


class EnvParser(UniversalBaseParser):
    def __init__(self):
        super().__init__(Language.ENV)
    
    def parse_file(self, file_path: str, content: str) -> FileInfo:
        symbols = []
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key = line.split('=')[0].strip()
                symbols.append(Symbol(
                    name=key,
                    symbol_type=SymbolType.ENV_VARIABLE,
                    file_path=normalize_path(file_path),
                    range=Range(Position(line_num, 0), Position(line_num, len(line)))
                ))
        
        return self._create_file_info(file_path, content, symbols, [], [])


class TerraformParser(UniversalBaseParser):
    def __init__(self):
        super().__init__(Language.TERRAFORM)
    
    def parse_file(self, file_path: str, content: str) -> FileInfo:
        # TODO: Implement Terraform HCL parsing
        return self._create_file_info(file_path, content, [], [], [])


class GraphQLParser(UniversalBaseParser):
    def __init__(self):
        super().__init__(Language.GRAPHQL)
    
    def parse_file(self, file_path: str, content: str) -> FileInfo:
        # TODO: Implement GraphQL schema parsing
        return self._create_file_info(file_path, content, [], [], [])


class HtmlParser(UniversalBaseParser):
    def __init__(self):
        super().__init__(Language.HTML)
    
    def parse_file(self, file_path: str, content: str) -> FileInfo:
        # TODO: Implement HTML parsing
        return self._create_file_info(file_path, content, [], [], [])


class MarkdownParser(UniversalBaseParser):
    def __init__(self):
        super().__init__(Language.MARKDOWN)
    
    def parse_file(self, file_path: str, content: str) -> FileInfo:
        # TODO: Implement Markdown parsing
        return self._create_file_info(file_path, content, [], [], [])


class MavenParser(XmlParser):
    def __init__(self):
        super().__init__()
        self.language = Language.MAVEN


class GradleParser(UniversalBaseParser):
    def __init__(self):
        super().__init__(Language.GRADLE)
    
    def parse_file(self, file_path: str, content: str) -> FileInfo:
        # TODO: Implement Gradle parsing
        return self._create_file_info(file_path, content, [], [], [])


class PropertiesParser(UniversalBaseParser):
    def __init__(self):
        super().__init__(Language.PROPERTIES)
    
    def parse_file(self, file_path: str, content: str) -> FileInfo:
        # TODO: Implement Properties file parsing
        return self._create_file_info(file_path, content, [], [], [])