"""
Core types and data structures for the dependency analyzer.
"""

from dataclasses import dataclass
from typing import Dict, List, Set, Optional, Union, Any
from enum import Enum
import os
from pathlib import Path


class SymbolType(Enum):
    """Types of symbols that can be indexed."""
    # Programming constructs
    CLASS = "class"
    METHOD = "method"
    FUNCTION = "function"
    VARIABLE = "variable"
    PROPERTY = "property"
    CONSTANT = "constant"
    IMPORT = "import"
    MODULE = "module"
    INTERFACE = "interface"
    ENUM = "enum"
    TYPE_ALIAS = "type_alias"
    ANNOTATION = "annotation"
    DECORATOR = "decorator"
    
    # Infrastructure & DevOps
    CONTAINER_IMAGE = "container_image"
    CONTAINER_SERVICE = "container_service"
    K8S_RESOURCE = "k8s_resource"
    K8S_NAMESPACE = "k8s_namespace"
    K8S_SERVICE = "k8s_service"
    K8S_DEPLOYMENT = "k8s_deployment"
    TERRAFORM_RESOURCE = "terraform_resource"
    TERRAFORM_MODULE = "terraform_module"
    TERRAFORM_VARIABLE = "terraform_variable"
    ANSIBLE_TASK = "ansible_task"
    ANSIBLE_PLAYBOOK = "ansible_playbook"
    
    # Configuration & Data
    CONFIG_SECTION = "config_section"
    CONFIG_KEY = "config_key"
    JSON_SCHEMA = "json_schema"
    YAML_ANCHOR = "yaml_anchor"
    ENV_VARIABLE = "env_variable"
    
    # Database & Query
    DATABASE_TABLE = "database_table"
    DATABASE_COLUMN = "database_column"
    DATABASE_INDEX = "database_index"
    DATABASE_CONSTRAINT = "database_constraint"
    SQL_PROCEDURE = "sql_procedure"
    SQL_VIEW = "sql_view"
    GRAPHQL_TYPE = "graphql_type"
    GRAPHQL_QUERY = "graphql_query"
    GRAPHQL_MUTATION = "graphql_mutation"
    
    # Web & Frontend
    HTML_ELEMENT = "html_element"
    HTML_COMPONENT = "html_component"
    CSS_CLASS = "css_class"
    CSS_ID = "css_id"
    CSS_SELECTOR = "css_selector"
    VUE_COMPONENT = "vue_component"
    REACT_COMPONENT = "react_component"
    
    # Build & Package
    BUILD_TARGET = "build_target"
    BUILD_TASK = "build_task"
    PACKAGE_DEPENDENCY = "package_dependency"
    MAVEN_ARTIFACT = "maven_artifact"
    NPM_SCRIPT = "npm_script"
    
    # Documentation
    DOC_SECTION = "doc_section"
    DOC_REFERENCE = "doc_reference"
    
    # Generic
    REFERENCE = "reference"
    ENTITY = "entity"
    RELATIONSHIP = "relationship"


class Language(Enum):
    """Supported file types and languages."""
    # Programming Languages
    PYTHON = "python"
    JAVASCRIPT = "javascript" 
    TYPESCRIPT = "typescript"
    JAVA = "java"
    CSHARP = "csharp"
    CPP = "cpp"
    GO = "go"
    RUST = "rust"
    PHP = "php"
    RUBY = "ruby"
    KOTLIN = "kotlin"
    SWIFT = "swift"
    SCALA = "scala"
    
    # Infrastructure & DevOps
    DOCKERFILE = "dockerfile"
    KUBERNETES = "kubernetes"
    TERRAFORM = "terraform"
    ANSIBLE = "ansible"
    CLOUDFORMATION = "cloudformation"
    HELM = "helm"
    
    # Configuration & Data
    JSON = "json"
    YAML = "yaml"
    TOML = "toml"
    XML = "xml"
    INI = "ini"
    ENV = "env"
    PROPERTIES = "properties"
    
    # Database & Query
    SQL = "sql"
    GRAPHQL = "graphql"
    MONGODB = "mongodb"
    
    # Web & Frontend
    HTML = "html"
    CSS = "css"
    SCSS = "scss"
    LESS = "less"
    VUE = "vue"
    SVELTE = "svelte"
    
    # Build & Package
    MAKEFILE = "makefile"
    CMAKE = "cmake"
    GRADLE = "gradle"
    MAVEN = "maven"
    NPM = "npm"
    COMPOSER = "composer"
    CARGO = "cargo"
    
    # Documentation & Markup
    MARKDOWN = "markdown"
    RST = "rst"
    ASCIIDOC = "asciidoc"
    
    # Other
    GENERIC = "generic"


@dataclass
class Position:
    """Represents a position in a source file."""
    line: int
    column: int
    offset: int = 0


@dataclass
class Range:
    """Represents a range in a source file."""
    start: Position
    end: Position


@dataclass
class Symbol:
    """Represents a symbol (class, method, variable, etc.) in the source code."""
    name: str
    symbol_type: SymbolType
    file_path: str
    range: Range
    parent: Optional[str] = None  # Parent symbol name (e.g., class for a method)
    modifiers: Set[str] = None  # public, private, static, etc.
    return_type: Optional[str] = None
    parameters: List[str] = None
    docstring: Optional[str] = None
    references: Set[str] = None  # File paths that reference this symbol
    
    def __post_init__(self):
        if self.modifiers is None:
            self.modifiers = set()
        if self.parameters is None:
            self.parameters = []
        if self.references is None:
            self.references = set()


@dataclass
class Dependency:
    """Represents a dependency relationship between symbols or files."""
    source_file: str
    target_file: str
    source_symbol: Optional[str] = None
    target_symbol: Optional[str] = None
    dependency_type: str = "import"  # import, inheritance, method_call, etc.


@dataclass
class FileInfo:
    """Information about a parsed file."""
    file_path: str
    language: Language
    last_modified: float
    symbols: List[Symbol]
    dependencies: List[Dependency]
    imports: List[str]
    hash: str  # Content hash for change detection


class IndexStats:
    """Statistics about the symbol index."""
    def __init__(self):
        self.total_files = 0
        self.total_symbols = 0
        self.symbols_by_type: Dict[SymbolType, int] = {}
        self.files_by_language: Dict[Language, int] = {}
        self.last_update_time = 0.0
        
    def update_stats(self, files: Dict[str, FileInfo]):
        """Update statistics from the current index."""
        self.total_files = len(files)
        self.total_symbols = sum(len(file_info.symbols) for file_info in files.values())
        
        self.symbols_by_type.clear()
        self.files_by_language.clear()
        
        for file_info in files.values():
            # Count symbols by type
            for symbol in file_info.symbols:
                self.symbols_by_type[symbol.symbol_type] = (
                    self.symbols_by_type.get(symbol.symbol_type, 0) + 1
                )
            
            # Count files by language
            self.files_by_language[file_info.language] = (
                self.files_by_language.get(file_info.language, 0) + 1
            )


def get_language_from_extension(file_path: str) -> Optional[Language]:
    """Determine file type/language from file extension or name."""
    file_name = Path(file_path).name.lower()
    ext = Path(file_path).suffix.lower()
    
    # Check full filename first
    filename_map = {
        'dockerfile': Language.DOCKERFILE,
        'docker-compose.yml': Language.KUBERNETES,
        'docker-compose.yaml': Language.KUBERNETES,
        'makefile': Language.MAKEFILE,
        'cmakelists.txt': Language.CMAKE,
        'package.json': Language.NPM,
        'composer.json': Language.COMPOSER,
        'cargo.toml': Language.CARGO,
        'pom.xml': Language.MAVEN,
        'build.gradle': Language.GRADLE,
        'requirements.txt': Language.PYTHON,
        'setup.py': Language.PYTHON,
        'pyproject.toml': Language.PYTHON,
    }
    
    if file_name in filename_map:
        return filename_map[file_name]
    
    # Check by extension
    extension_map = {
        # Programming Languages
        '.py': Language.PYTHON,
        '.js': Language.JAVASCRIPT,
        '.jsx': Language.JAVASCRIPT,
        '.ts': Language.TYPESCRIPT,
        '.tsx': Language.TYPESCRIPT,
        '.java': Language.JAVA,
        '.cs': Language.CSHARP,
        '.cpp': Language.CPP,
        '.cc': Language.CPP,
        '.cxx': Language.CPP,
        '.c': Language.CPP,
        '.h': Language.CPP,
        '.hpp': Language.CPP,
        '.go': Language.GO,
        '.rs': Language.RUST,
        '.php': Language.PHP,
        '.rb': Language.RUBY,
        '.kt': Language.KOTLIN,
        '.swift': Language.SWIFT,
        '.scala': Language.SCALA,
        
        # Configuration & Data
        '.json': Language.JSON,
        '.yaml': Language.YAML,
        '.yml': Language.YAML,
        '.toml': Language.TOML,
        '.xml': Language.XML,
        '.ini': Language.INI,
        '.env': Language.ENV,
        '.properties': Language.PROPERTIES,
        
        # Infrastructure
        '.tf': Language.TERRAFORM,
        '.tfvars': Language.TERRAFORM,
        
        # Database
        '.sql': Language.SQL,
        '.graphql': Language.GRAPHQL,
        '.gql': Language.GRAPHQL,
        
        # Web & Frontend
        '.html': Language.HTML,
        '.htm': Language.HTML,
        '.css': Language.CSS,
        '.scss': Language.SCSS,
        '.sass': Language.SCSS,
        '.less': Language.LESS,
        '.vue': Language.VUE,
        '.svelte': Language.SVELTE,
        
        # Documentation
        '.md': Language.MARKDOWN,
        '.rst': Language.RST,
        '.adoc': Language.ASCIIDOC,
    }
    
    return extension_map.get(ext)


def normalize_path(path: str) -> str:
    """Normalize file path for consistent indexing."""
    return os.path.abspath(path).replace('\\', '/')