#!/usr/bin/env python3
"""
Fast Universal Dependency Analyzer - Optimized Main Entry Point

High-performance version with:
- Progress reporting
- Smart file filtering  
- Batch processing
- Memory optimization
- Duplicate elimination

Usage:
    python fast_main.py <repository_path>
    python fast_main.py /path/to/project --quick
    python fast_main.py . --verbose
"""

import os
import sys
import json
import argparse
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Set
import logging

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dependency_analyzer import DependencyAnalyzer
from dependency_analyzer.types import Language, SymbolType

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class FastRepositoryAnalyzer:
    """High-performance repository analysis with optimizations."""
    
    def __init__(self, repository_path: str, quick_mode: bool = False):
        self.repository_path = os.path.abspath(repository_path)
        self.repository_name = os.path.basename(self.repository_path)
        self.analyzer = DependencyAnalyzer()
        self.analysis_timestamp = datetime.now()
        self.quick_mode = quick_mode
        
        # Performance tracking
        self.start_time = time.time()
        
        # Use fixed output directory (will clean and replace previous)
        self.output_base = "dependency_analysis"
        
        if not quick_mode:
            self.create_output_structure()
    
    def create_output_structure(self):
        """Create clean output folder, removing previous analysis."""
        # Clean previous analysis results
        if os.path.exists(self.output_base):
            import shutil
            # Remove all old files (keep only README.md)
            for item in os.listdir(self.output_base):
                if item != 'README.md':
                    item_path = os.path.join(self.output_base, item)
                    if os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                    else:
                        os.remove(item_path)
        
        # Create minimal folder structure
        os.makedirs(self.output_base, exist_ok=True)
        
        print(f"📁 Output: {self.output_base} (cleaned previous results)")
    
    def quick_file_count(self) -> int:
        """Quick estimation of files to be analyzed."""
        file_count = 0
        supported_extensions = {
            '.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.cpp', '.c', '.h', '.hpp',
            '.cs', '.go', '.rs', '.php', '.rb', '.swift', '.kt', '.scala',
            '.json', '.yaml', '.yml', '.xml', '.toml', '.ini', '.env',
            '.dockerfile', '.sql', '.css', '.html', '.vue', '.svelte',
            '.md', '.rst', '.txt', '.cfg', '.conf', '.properties'
        }
        
        try:
            for root, dirs, files in os.walk(self.repository_path):
                # Skip common large directories early
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in {
                    'node_modules', '__pycache__', '.git', 'venv', 'env', 'build', 
                    'dist', 'target', 'bin', 'obj', '.idea', '.vs', 'logs', 'tmp'
                }]
                
                for file in files:
                    if any(file.lower().endswith(ext) for ext in supported_extensions):
                        file_count += 1
                        
                # Stop counting after 10000 files for very large repos
                if file_count > 10000:
                    return 10000
                    
        except (OSError, PermissionError):
            pass
            
        return file_count
    
    def analyze_repository(self) -> bool:
        """Perform fast repository analysis."""
        print(f"🚀 Fast Universal Dependency Analyzer")
        print(f"📁 Repository: {self.repository_name}")
        print(f"📍 Path: {self.repository_path}")
        print(f"⏰ Started: {self.analysis_timestamp.strftime('%H:%M:%S')}")
        
        if self.quick_mode:
            print("⚡ Quick mode enabled - minimal output")
        
        print("-" * 60)
        
        # Quick file count estimation
        estimated_files = self.quick_file_count()
        print(f"📊 Estimated files to analyze: {estimated_files}")
        
        if estimated_files > 1000:
            print("⚠️  Large repository detected - this may take a few minutes")
        
        # Initialize analyzer with progress tracking
        start_time = time.time()
        success = self.analyzer.initialize([self.repository_path])
        init_time = time.time() - start_time
        
        if not success:
            print("❌ Failed to initialize analyzer")
            return False
        
        print(f"✅ Analysis completed in {init_time:.1f}s")
        return True
    
    def generate_analysis_summary(self):
        """Generate fast analysis summary."""
        print("\n📋 Analysis Summary")
        print("-" * 30)
        
        # Collect data efficiently
        total_files = len(self.analyzer.symbol_index.files)
        total_symbols = 0
        total_deps = 0
        language_stats = {}
        symbol_type_stats = {}
        
        for file_path, file_info in self.analyzer.symbol_index.files.items():
            total_symbols += len(file_info.symbols)
            total_deps += len(file_info.dependencies)
            
            # Language stats
            lang = file_info.language.value
            if lang not in language_stats:
                language_stats[lang] = {'files': 0, 'symbols': 0}
            language_stats[lang]['files'] += 1
            language_stats[lang]['symbols'] += len(file_info.symbols)
            
            # Symbol type stats (sample first 1000 symbols for large repos)
            symbols_to_process = file_info.symbols[:1000] if len(file_info.symbols) > 1000 else file_info.symbols
            for symbol in symbols_to_process:
                sym_type = symbol.symbol_type.value
                symbol_type_stats[sym_type] = symbol_type_stats.get(sym_type, 0) + 1
        
        # Print results
        print(f"📊 Files: {total_files}")
        print(f"🔍 Symbols: {total_symbols:,}")
        print(f"🔗 Dependencies: {total_deps}")
        print(f"🌍 Languages: {len(language_stats)}")
        
        # Top languages
        print(f"\n🏆 Top Languages:")
        for lang, stats in sorted(language_stats.items(), key=lambda x: x[1]['files'], reverse=True)[:5]:
            print(f"  {lang:<15} {stats['files']:>3} files  {stats['symbols']:>5} symbols")
        
        # Dependency analysis (quick sample)
        dep_types = {}
        sample_deps = []
        count = 0
        for file_info in self.analyzer.symbol_index.files.values():
            sample_deps.extend(file_info.dependencies)
            count += len(file_info.dependencies)
            if count > 1000:  # Limit for performance
                break
        
        for dep in sample_deps:
            dep_type = dep.dependency_type
            dep_types[dep_type] = dep_types.get(dep_type, 0) + 1
        
        if dep_types:
            print(f"\n🔗 Top Dependencies:")
            for dep_type, count in sorted(dep_types.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"  {dep_type:<20} {count:>3} relationships")
        
        # Performance stats
        total_time = time.time() - self.start_time
        print(f"\n⚡ Performance:")
        print(f"  Analysis time: {total_time:.1f}s")
        print(f"  Files/second: {total_files/total_time:.1f}")
        print(f"  Symbols/second: {total_symbols/total_time:.0f}")
        
        # Save summary if not in quick mode
        if not self.quick_mode:
            self.save_minimal_results({
                'files': total_files,
                'symbols': total_symbols,
                'dependencies': total_deps,
                'languages': language_stats,
                'symbol_types': symbol_type_stats,
                'dependency_types': dep_types,
                'analysis_time': total_time,
                'performance': {
                    'files_per_second': total_files/total_time,
                    'symbols_per_second': total_symbols/total_time
                }
            })
    
    def save_minimal_results(self, summary_data: Dict[str, Any]):
        """Save only essential data needed for dependency fixing."""
        
        # Save only essential dependency mapping for fixing
        deps_file = f"{self.output_base}/dependencies.json"
        
        # Build efficient dependency lookup structure
        dependency_map = {}
        file_info_map = {}
        
        for file_path, file_info in self.analyzer.symbol_index.files.items():
            rel_path = os.path.relpath(file_path, self.repository_path)
            
            # File dependencies (what this file needs)
            file_deps = []
            for dep in file_info.dependencies:
                file_deps.append({
                    'target': dep.target_file,
                    'type': dep.dependency_type
                })
            
            dependency_map[rel_path] = file_deps
            file_info_map[rel_path] = {
                'language': file_info.language.value,
                'symbols': len(file_info.symbols),
                'deps_count': len(file_info.dependencies)
            }
        
        # Save compact essential data
        essential_data = {
            'repository': self.repository_name,
            'analyzed_at': self.analysis_timestamp.isoformat(),
            'files': file_info_map,
            'dependencies': dependency_map
        }
        
        with open(deps_file, 'w', encoding='utf-8') as f:
            json.dump(essential_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Essential data saved: {deps_file}")
        print(f"   📋 {len(dependency_map)} files with dependency mappings")


def main():
    """Fast main entry point."""
    parser = argparse.ArgumentParser(
        description="Fast Universal Dependency Analyzer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python fast_main.py /path/to/project
  python fast_main.py . --quick
  python fast_main.py /large/project --verbose
        """
    )
    
    parser.add_argument('repository', help='Path to repository')
    parser.add_argument('--quick', action='store_true', help='Quick mode - console output only')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    
    args = parser.parse_args()
    
    # Validate repository
    if not os.path.exists(args.repository):
        print(f"❌ Repository not found: {args.repository}")
        sys.exit(1)
    
    if not os.path.isdir(args.repository):
        print(f"❌ Not a directory: {args.repository}")
        sys.exit(1)
    
    # Configure logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    elif args.quick:
        logging.getLogger().setLevel(logging.WARNING)
    
    try:
        # Create and run fast analysis
        analyzer = FastRepositoryAnalyzer(args.repository, args.quick)
        
        if analyzer.analyze_repository():
            analyzer.generate_analysis_summary()
            
            if not args.quick:
                print(f"\n🎉 Fast analysis complete!")
            else:
                print(f"\n⚡ Quick analysis complete!")
                
        else:
            print("❌ Analysis failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️ Analysis interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()