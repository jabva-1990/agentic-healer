"""
Incremental Updater module for efficient file watching and index updates.
Monitors file changes and updates only affected parts of the index.
"""

import os
import time
import threading
from typing import Dict, List, Set, Optional, Callable, Any
from dataclasses import dataclass
from pathlib import Path
import logging
import hashlib

from .types import normalize_path, get_language_from_extension
from .symbol_index import SymbolIndex
from .dependency_tracker import DependencyTracker

logger = logging.getLogger(__name__)


@dataclass
class FileChange:
    """Represents a file change event."""
    file_path: str
    change_type: str  # 'created', 'modified', 'deleted', 'renamed'
    timestamp: float
    old_path: Optional[str] = None  # For rename events


class FileWatcher:
    """Basic file watcher implementation."""
    
    def __init__(self, watch_directories: List[str], callback: Callable[[FileChange], None]):
        self.watch_directories = [normalize_path(d) for d in watch_directories]
        self.callback = callback
        self.file_mtimes: Dict[str, float] = {}
        self.is_watching = False
        self.watch_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        
        # Supported file extensions
        self.supported_extensions = {'.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.cs', '.cpp', '.h', '.go', '.rs'}
        
    def start_watching(self, polling_interval: float = 1.0):
        """Start watching for file changes."""
        if self.is_watching:
            return
        
        self.is_watching = True
        self.stop_event.clear()
        self.watch_thread = threading.Thread(
            target=self._watch_loop,
            args=(polling_interval,),
            daemon=True
        )
        self.watch_thread.start()
        logger.info(f"Started file watching for {len(self.watch_directories)} directories")
    
    def stop_watching(self):
        """Stop watching for file changes."""
        if not self.is_watching:
            return
        
        self.is_watching = False
        self.stop_event.set()
        
        if self.watch_thread:
            self.watch_thread.join(timeout=2.0)
        
        logger.info("Stopped file watching")
    
    def _watch_loop(self, polling_interval: float):
        """Main watching loop."""
        while not self.stop_event.wait(polling_interval):
            try:
                self._scan_for_changes()
            except Exception as e:
                logger.error(f"Error in file watcher: {e}")
    
    def _scan_for_changes(self):
        """Scan directories for file changes."""
        current_files = {}
        
        # Scan all watched directories
        for directory in self.watch_directories:
            if not os.path.exists(directory):
                continue
            
            for root, dirs, files in os.walk(directory):
                # Skip hidden directories and common ignore patterns
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in {'__pycache__', 'node_modules'}]
                
                for file in files:
                    file_path = normalize_path(os.path.join(root, file))
                    
                    # Only watch supported file types
                    if Path(file_path).suffix.lower() not in self.supported_extensions:
                        continue
                    
                    try:
                        mtime = os.path.getmtime(file_path)
                        current_files[file_path] = mtime
                    except OSError:
                        # File might have been deleted during scan
                        continue
        
        # Detect changes
        self._detect_changes(current_files)
        
        # Update our file tracking
        self.file_mtimes = current_files
    
    def _detect_changes(self, current_files: Dict[str, float]):
        """Detect and report file changes."""
        current_time = time.time()
        
        # Check for new or modified files
        for file_path, mtime in current_files.items():
            if file_path not in self.file_mtimes:
                # New file
                change = FileChange(
                    file_path=file_path,
                    change_type='created',
                    timestamp=current_time
                )
                self.callback(change)
            elif mtime > self.file_mtimes[file_path]:
                # Modified file
                change = FileChange(
                    file_path=file_path,
                    change_type='modified',
                    timestamp=current_time
                )
                self.callback(change)
        
        # Check for deleted files
        for file_path in self.file_mtimes:
            if file_path not in current_files:
                change = FileChange(
                    file_path=file_path,
                    change_type='deleted',
                    timestamp=current_time
                )
                self.callback(change)


class IncrementalUpdater:
    """Manages incremental updates to the symbol index and dependency tracker."""
    
    def __init__(self, symbol_index: SymbolIndex, dependency_tracker: DependencyTracker):
        self.symbol_index = symbol_index
        self.dependency_tracker = dependency_tracker
        self.file_watcher: Optional[FileWatcher] = None
        
        # Update queue and processing
        self.update_queue: List[FileChange] = []
        self.update_lock = threading.Lock()
        self.batch_size = 10
        self.batch_timeout = 2.0  # seconds
        self.last_batch_time = time.time()
        
        # Processing thread
        self.update_thread: Optional[threading.Thread] = None
        self.stop_processing = threading.Event()
        
        logger.info("Incremental updater initialized")
    
    def start_watching(self, directories: List[str], polling_interval: float = 1.0):
        """Start watching directories for changes."""
        if self.file_watcher:
            self.file_watcher.stop_watching()
        
        self.file_watcher = FileWatcher(directories, self._on_file_change)
        self.file_watcher.start_watching(polling_interval)
        
        # Start update processing thread
        self._start_update_processing()
    
    def stop_watching(self):
        """Stop watching for file changes."""
        if self.file_watcher:
            self.file_watcher.stop_watching()
            self.file_watcher = None
        
        # Stop update processing
        self._stop_update_processing()
    
    def force_update(self, file_paths: List[str]):
        """Force update of specific files."""
        current_time = time.time()
        
        with self.update_lock:
            for file_path in file_paths:
                change = FileChange(
                    file_path=normalize_path(file_path),
                    change_type='modified',
                    timestamp=current_time
                )
                self.update_queue.append(change)
    
    def update_file(self, file_path: str, content: Optional[str] = None) -> bool:
        """Update a single file immediately."""
        normalized_path = normalize_path(file_path)
        
        try:
            if not os.path.exists(file_path):
                # File was deleted
                self.symbol_index.remove_file(normalized_path)
                self._update_dependency_tracker()
                logger.debug(f"Removed deleted file from index: {file_path}")
                return True
            
            # Check if file needs update
            if not self.symbol_index.needs_update(file_path):
                logger.debug(f"File is up to date: {file_path}")
                return True
            
            # Update the file in the index
            success = self.symbol_index.index_file(file_path, content)
            
            if success:
                # Update dependency tracker with new file information
                self._update_dependency_tracker()
                
                # Update dependent files if needed
                self._update_dependent_files(normalized_path)
                
                logger.debug(f"Updated file in index: {file_path}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error updating file {file_path}: {e}")
            return False
    
    def batch_update(self, file_changes: List[FileChange]) -> Dict[str, bool]:
        """Update multiple files in a batch."""
        results = {}
        updated_files = []
        
        for change in file_changes:
            if change.change_type == 'deleted':
                self.symbol_index.remove_file(change.file_path)
                results[change.file_path] = True
            else:
                success = self.symbol_index.index_file(change.file_path)
                results[change.file_path] = success
                if success:
                    updated_files.append(change.file_path)
        
        # Update dependency tracker once for all changes
        if updated_files:
            self._update_dependency_tracker()
            
            # Update dependent files
            all_dependents = set()
            for file_path in updated_files:
                dependents = self.dependency_tracker.get_file_dependents(file_path)
                all_dependents.update(dependents)
            
            self._update_dependent_files_batch(all_dependents)
        
        logger.info(f"Batch updated {len(file_changes)} files, {sum(results.values())} successful")
        return results
    
    def get_update_statistics(self) -> Dict[str, Any]:
        """Get statistics about incremental updates."""
        stats = self.symbol_index.get_stats()
        
        return {
            'total_files_indexed': stats.total_files,
            'total_symbols': stats.total_symbols,
            'last_update_time': stats.last_update_time,
            'is_watching': self.file_watcher is not None and self.file_watcher.is_watching,
            'queued_updates': len(self.update_queue) if hasattr(self, 'update_queue') else 0,
            'watched_directories': (
                self.file_watcher.watch_directories 
                if self.file_watcher else []
            )
        }
    
    def _on_file_change(self, change: FileChange):
        """Handle file change events."""
        with self.update_lock:
            self.update_queue.append(change)
            logger.debug(f"File change detected: {change.change_type} - {change.file_path}")
    
    def _start_update_processing(self):
        """Start the update processing thread."""
        if self.update_thread and self.update_thread.is_alive():
            return
        
        self.stop_processing.clear()
        self.update_thread = threading.Thread(
            target=self._process_update_queue,
            daemon=True
        )
        self.update_thread.start()
        logger.debug("Started update processing thread")
    
    def _stop_update_processing(self):
        """Stop the update processing thread."""
        self.stop_processing.set()
        
        if self.update_thread:
            self.update_thread.join(timeout=5.0)
        
        logger.debug("Stopped update processing thread")
    
    def _process_update_queue(self):
        """Process queued file updates."""
        while not self.stop_processing.is_set():
            batch = []
            
            # Collect batch of updates
            with self.update_lock:
                if self.update_queue:
                    batch_size = min(self.batch_size, len(self.update_queue))
                    batch = self.update_queue[:batch_size]
                    self.update_queue = self.update_queue[batch_size:]
                    self.last_batch_time = time.time()
            
            if batch:
                try:
                    self.batch_update(batch)
                except Exception as e:
                    logger.error(f"Error processing update batch: {e}")
            
            # Wait before next batch
            time.sleep(0.1)
    
    def _update_dependency_tracker(self):
        """Update the dependency tracker with current file information."""
        try:
            self.dependency_tracker.update_dependencies(self.symbol_index.files)
        except Exception as e:
            logger.error(f"Error updating dependency tracker: {e}")
    
    def _update_dependent_files(self, file_path: str):
        """Update files that depend on the given file."""
        dependents = self.dependency_tracker.get_file_dependents(file_path)
        
        for dependent_file in dependents:
            if self.symbol_index.needs_update(dependent_file):
                self.symbol_index.index_file(dependent_file)
    
    def _update_dependent_files_batch(self, dependent_files: Set[str]):
        """Update multiple dependent files efficiently."""
        files_to_update = [
            f for f in dependent_files 
            if self.symbol_index.needs_update(f)
        ]
        
        for file_path in files_to_update:
            try:
                self.symbol_index.index_file(file_path)
            except Exception as e:
                logger.error(f"Error updating dependent file {file_path}: {e}")
        
        if files_to_update:
            logger.debug(f"Updated {len(files_to_update)} dependent files")
    
    def __del__(self):
        """Cleanup when the updater is destroyed."""
        self.stop_watching()