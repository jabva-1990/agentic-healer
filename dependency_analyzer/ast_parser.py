"""
AST Parser module for extracting symbols from source code.
Supports multiple programming languages with a unified interface.
"""

import ast
import os
import hashlib
from typing import Dict, List, Optional, Set, Any
from pathlib import Path
import logging

from .types import (
    Symbol, SymbolType, Language, Position, Range, FileInfo, Dependency,
    get_language_from_extension, normalize_path
)

logger = logging.getLogger(__name__)


class BaseLanguageParser:
    """Base class for language-specific parsers."""
    
    def __init__(self, language: Language):
        self.language = language
    
    def parse_file(self, file_path: str, content: str) -> FileInfo:
        """Parse a file and extract symbol information."""
        raise NotImplementedError("Subclasses must implement parse_file")
    
    def extract_symbols(self, ast_node: Any, file_path: str) -> List[Symbol]:
        """Extract symbols from an AST node."""
        raise NotImplementedError("Subclasses must implement extract_symbols")
    
    def extract_dependencies(self, ast_node: Any, file_path: str) -> List[Dependency]:
        """Extract dependencies from an AST node."""
        raise NotImplementedError("Subclasses must implement extract_dependencies")


class PythonParser(BaseLanguageParser):
    """Parser for Python source code."""
    
    def __init__(self):
        super().__init__(Language.PYTHON)
    
    def parse_file(self, file_path: str, content: str) -> FileInfo:
        """Parse a Python file and extract symbols and dependencies."""
        try:
            tree = ast.parse(content)
            symbols = self.extract_symbols(tree, file_path)
            dependencies = self.extract_dependencies(tree, file_path)
            imports = self._extract_imports(tree)
            
            content_hash = hashlib.md5(content.encode()).hexdigest()
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
        except SyntaxError as e:
            logger.error(f"Syntax error in {file_path}: {e}")
            return FileInfo(
                file_path=normalize_path(file_path),
                language=self.language,
                last_modified=0,
                symbols=[],
                dependencies=[],
                imports=[],
                hash=""
            )
    
    def extract_symbols(self, tree: ast.AST, file_path: str) -> List[Symbol]:
        """Extract symbols from Python AST."""
        symbols = []
        
        for node in ast.walk(tree):
            symbol = None
            
            if isinstance(node, ast.ClassDef):
                symbol = self._create_class_symbol(node, file_path)
            elif isinstance(node, ast.FunctionDef):
                symbol = self._create_function_symbol(node, file_path)
            elif isinstance(node, ast.AsyncFunctionDef):
                symbol = self._create_function_symbol(node, file_path, is_async=True)
            elif isinstance(node, ast.Assign):
                symbols.extend(self._create_variable_symbols(node, file_path))
            elif isinstance(node, ast.AnnAssign) and node.target:
                symbol = self._create_annotated_variable_symbol(node, file_path)
            
            if symbol:
                symbols.append(symbol)
        
        return symbols
    
    def extract_dependencies(self, tree: ast.AST, file_path: str) -> List[Dependency]:
        """Extract dependencies from Python AST."""
        dependencies = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                deps = self._create_import_dependencies(node, file_path)
                dependencies.extend(deps)
        
        return dependencies
    
    def _create_class_symbol(self, node: ast.ClassDef, file_path: str) -> Symbol:
        """Create a symbol for a class definition."""
        range_obj = Range(
            start=Position(node.lineno, node.col_offset),
            end=Position(node.end_lineno or node.lineno, node.end_col_offset or node.col_offset)
        )
        
        modifiers = set()
        if node.name.startswith('_'):
            modifiers.add('private' if node.name.startswith('__') else 'protected')
        
        return Symbol(
            name=node.name,
            symbol_type=SymbolType.CLASS,
            file_path=normalize_path(file_path),
            range=range_obj,
            modifiers=modifiers,
            docstring=ast.get_docstring(node)
        )
    
    def _create_function_symbol(self, node: ast.FunctionDef, file_path: str, is_async: bool = False) -> Symbol:
        """Create a symbol for a function definition."""
        range_obj = Range(
            start=Position(node.lineno, node.col_offset),
            end=Position(node.end_lineno or node.lineno, node.end_col_offset or node.col_offset)
        )
        
        modifiers = set()
        if is_async:
            modifiers.add('async')
        if node.name.startswith('_'):
            modifiers.add('private' if node.name.startswith('__') else 'protected')
        
        # Check if it's a method (inside a class)
        parent_class = self._find_parent_class(node)
        symbol_type = SymbolType.METHOD if parent_class else SymbolType.FUNCTION
        
        parameters = [arg.arg for arg in node.args.args]
        
        return Symbol(
            name=node.name,
            symbol_type=symbol_type,
            file_path=normalize_path(file_path),
            range=range_obj,
            parent=parent_class,
            modifiers=modifiers,
            parameters=parameters,
            docstring=ast.get_docstring(node)
        )
    
    def _create_variable_symbols(self, node: ast.Assign, file_path: str) -> List[Symbol]:
        """Create symbols for variable assignments."""
        symbols = []
        
        for target in node.targets:
            if isinstance(target, ast.Name):
                range_obj = Range(
                    start=Position(node.lineno, node.col_offset),
                    end=Position(node.end_lineno or node.lineno, node.end_col_offset or node.col_offset)
                )
                
                modifiers = set()
                if target.id.isupper():
                    symbol_type = SymbolType.CONSTANT
                    modifiers.add('const')
                else:
                    symbol_type = SymbolType.VARIABLE
                
                symbol = Symbol(
                    name=target.id,
                    symbol_type=symbol_type,
                    file_path=normalize_path(file_path),
                    range=range_obj,
                    modifiers=modifiers
                )
                symbols.append(symbol)
        
        return symbols
    
    def _create_annotated_variable_symbol(self, node: ast.AnnAssign, file_path: str) -> Optional[Symbol]:
        """Create a symbol for an annotated variable assignment."""
        if isinstance(node.target, ast.Name):
            range_obj = Range(
                start=Position(node.lineno, node.col_offset),
                end=Position(node.end_lineno or node.lineno, node.end_col_offset or node.col_offset)
            )
            
            return Symbol(
                name=node.target.id,
                symbol_type=SymbolType.VARIABLE,
                file_path=normalize_path(file_path),
                range=range_obj,
                return_type=ast.unparse(node.annotation) if hasattr(ast, 'unparse') else None
            )
        return None
    
    def _create_import_dependencies(self, node: ast.AST, file_path: str) -> List[Dependency]:
        """Create dependencies for import statements (optimized - no duplicates)."""
        dependencies = []
        
        if isinstance(node, ast.Import):
            for alias in node.names:
                dependencies.append(Dependency(
                    source_file=normalize_path(file_path),
                    target_file=alias.name,  # Module name
                    dependency_type="import"
                ))
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module:  # Only create one dependency per module, not per imported symbol
                # Collect all imported symbols for this dependency
                imported_symbols = [alias.name for alias in node.names]
                dependencies.append(Dependency(
                    source_file=normalize_path(file_path),
                    target_file=module,
                    target_symbol=', '.join(imported_symbols),  # Store all symbols together
                    dependency_type="import_from"
                ))
        
        return dependencies
    
    def _extract_imports(self, tree: ast.AST) -> List[str]:
        """Extract all import statements as strings."""
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}" if module else alias.name)
        
        return imports
    
    def _find_parent_class(self, node: ast.FunctionDef) -> Optional[str]:
        """Find the parent class of a function node."""
        # This is a simplified approach - in a full implementation,
        # you'd need to traverse the AST tree upwards
        # For now, we'll assume methods are detected by their context
        return None  # TODO: Implement proper parent detection


class JavaScriptParser(BaseLanguageParser):
    """Parser for JavaScript source code."""
    
    def __init__(self):
        super().__init__(Language.JAVASCRIPT)
        # Note: For full JavaScript/TypeScript support, you'd want to use
        # a proper JavaScript parser like Babel or TypeScript compiler API
        # This is a simplified implementation
    
    def parse_file(self, file_path: str, content: str) -> FileInfo:
        """Parse a JavaScript file - simplified implementation."""
        logger.warning("JavaScript parsing is simplified - consider using a proper JS parser")
        
        content_hash = hashlib.md5(content.encode()).hexdigest()
        last_modified = os.path.getmtime(file_path) if os.path.exists(file_path) else 0
        
        return FileInfo(
            file_path=normalize_path(file_path),
            language=self.language,
            last_modified=last_modified,
            symbols=[],  # TODO: Implement JavaScript symbol extraction
            dependencies=[],
            imports=[],
            hash=content_hash
        )
    
    def extract_symbols(self, ast_node: Any, file_path: str) -> List[Symbol]:
        """Extract symbols from JavaScript AST - placeholder."""
        return []
    
    def extract_dependencies(self, ast_node: Any, file_path: str) -> List[Dependency]:
        """Extract dependencies from JavaScript AST - placeholder."""
        return []


class ASTParser:
    """Main AST parser that delegates to language-specific parsers."""
    
    def __init__(self):
        self.parsers: Dict[Language, BaseLanguageParser] = {
            Language.PYTHON: PythonParser(),
            Language.JAVASCRIPT: JavaScriptParser(),
            # Add more language parsers as needed
        }
        
        # Import universal parsers here to avoid circular imports
        try:
            from .universal_parsers import UniversalFileParser
            self.universal_parser = UniversalFileParser()
        except ImportError:
            self.universal_parser = None
        
        # Use the get_language_from_extension function from types.py
        # No need to maintain our own extension mapping
    
    def can_parse(self, file_path: str) -> bool:
        """Check if we can parse the given file."""
        language = get_language_from_extension(file_path)
        
        # Check if language-specific parser exists
        if language in self.parsers:
            return True
        
        # Check if universal parser can handle it
        if self.universal_parser and self.universal_parser.can_parse(language):
            return True
        
        return False
    
    def parse_file(self, file_path: str, content: Optional[str] = None) -> Optional[FileInfo]:
        """Parse a source file and return FileInfo."""
        if not self.can_parse(file_path):
            return None
        
        language = get_language_from_extension(file_path)
        
        if content is None:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except (IOError, UnicodeDecodeError) as e:
                logger.error(f"Error reading file {file_path}: {e}")
                return None
        
        # Try language-specific parser first
        if language in self.parsers:
            parser = self.parsers[language]
            return parser.parse_file(file_path, content)
        
        # Fall back to universal parser
        if self.universal_parser and self.universal_parser.can_parse(language):
            return self.universal_parser.parse_file(file_path, content, language)
        
        logger.warning(f"No parser available for language: {language}")
        return None
    
    def get_supported_languages(self) -> List[Language]:
        """Get list of supported languages."""
        languages = set(self.parsers.keys())
        
        # Add languages from universal parser
        if self.universal_parser:
            languages.update(self.universal_parser.parsers.keys())
        
        return list(languages)
    
    def add_parser(self, language: Language, parser: BaseLanguageParser):
        """Add a custom language parser."""
        self.parsers[language] = parser