#!/usr/bin/env python3
"""
Self-Healing Repository Agent

Automatically fixes repository issues using multi-layer intelligence:
- Layer 1: Indexing (fast file/symbol lookups)  
- Layer 2: Knowledge Graph (relationship understanding)
- Layer 3: LLM (intelligent code fixing with GCP Vertex AI)

Usage:
    python self_healing_agent.py /path/to/repo "Memory usage too high in Kubernetes deployment" --max-iterations 3 --timeout 120
    python self_healing_agent.py . "main.py import error" --max-iterations 5 --timeout 60
"""

import os
import sys
import json
import time
import argparse
import logging
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import subprocess
import tempfile
import shutil

# Google GenAI imports
try:
    from google import genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    print("⚠️  Google GenAI library not available. Install with: pip install google-genai")

# Import our existing intelligence layers
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.enhanced_analyzer import EnhancedDependencyAnalyzer
from core.knowledge_graph import KnowledgeGraph
from agents.fast_analyzer import FastRepositoryAnalyzer
from agents.planning_agent import StrategicPlanningAgent, RepairPlan, RepairTask

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class HealingSession:
    """Tracks a complete healing session."""
    repo_path: str
    issue_description: str
    max_iterations: int
    timeout_seconds: int
    start_time: datetime = field(default_factory=datetime.now)
    
    # Progress tracking
    current_iteration: int = 0
    files_modified: Set[str] = field(default_factory=set)
    fixes_applied: List[Dict[str, Any]] = field(default_factory=list)
    errors_encountered: List[str] = field(default_factory=list)
    
    # Results
    status: str = "in_progress"  # in_progress, solved, timeout, failed
    final_message: str = ""
    total_time: float = 0.0

@dataclass
class FileFix:
    """Represents a fix applied to a specific file."""
    file_path: str
    issue_found: str
    fix_applied: str
    original_content: str
    modified_content: str
    confidence: float
    iteration: int

class GenAIClient:
    """Google GenAI client for LLM interactions using the google-genai library."""
    
    def __init__(self, service_account_path: str):
        self.service_account_path = service_account_path
        self.client = None
        self.model_name = "gemini-2.5-flash"
        self._initialize()
    
    def _initialize(self):
        """Initialize GenAI client."""
        if not GENAI_AVAILABLE:
            raise Exception("Google GenAI library not installed")
        
        try:
            # Set credentials environment variable
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = self.service_account_path
            
            # Initialize client
            self.client = genai.Client(
                vertexai=True,
                project="prj-mm-genai-qa-001",
                location="us-central1"
            )
            
            logger.info(f"✅ GenAI initialized with model: {self.model_name}")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize GenAI: {e}")
            raise
    
    def generate_text(self, prompt: str, max_tokens: int = 2048) -> str:
        """Generate text using GenAI."""
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[prompt]
            )
            
            if response and response.text:
                return response.text.strip()
            else:
                raise Exception("Empty response from GenAI")
                
        except Exception as e:
            logger.error(f"❌ GenAI generation failed: {e}")
            return f"Error generating response: {e}"

class SelfHealingAgent:
    """Self-healing repository agent with multi-layer intelligence."""
    
    def __init__(self, service_account_path: str):
        self.service_account_path = service_account_path
        
        # Initialize intelligence layers
        self.analyzer = EnhancedDependencyAnalyzer()
        self.genai_client = None
        
        # Session tracking
        self.current_session: Optional[HealingSession] = None
        
        # Initialize LLM client
        try:
            self.genai_client = GenAIClient(service_account_path)
        except Exception as e:
            logger.warning(f"⚠️  GenAI not available: {e}")
    
    def start_healing_session(self, repo_path: str, issue: str, max_iterations: int, timeout: int) -> HealingSession:
        """Start a new healing session."""
        session = HealingSession(
            repo_path=os.path.abspath(repo_path),
            issue_description=issue,
            max_iterations=max_iterations,
            timeout_seconds=timeout
        )
        
        self.current_session = session
        
        logger.info(f"🚀 Starting Self-Healing Session")
        logger.info(f"📁 Repository: {session.repo_path}")
        logger.info(f"🎯 Issue: {session.issue_description}")
        logger.info(f"🔄 Max iterations: {session.max_iterations}")
        logger.info(f"⏰ Timeout: {session.timeout_seconds}s")
        logger.info("=" * 60)
        
        return session
    
    def analyze_repository(self) -> bool:
        """Analyze repository and build intelligence layers."""
        if not self.current_session:
            return False
        
        logger.info("🧠 Building Intelligence Layers...")
        
        # Step 1: Fast analysis with indexing
        analyzer = FastRepositoryAnalyzer(self.current_session.repo_path, quick_mode=True)
        if not analyzer.analyze_repository():
            logger.error("❌ Failed to analyze repository")
            return False
        
        # Step 2: Load enhanced data with knowledge graph
        if not self.analyzer.load_and_enhance_data():
            logger.error("❌ Failed to load enhanced dependency data")
            return False
        
        files_count = len(self.analyzer.dependency_data.get('files', {}))
        graph_nodes = len(self.analyzer.kg.nodes) if self.analyzer.kg else 0
        
        logger.info(f"✅ Intelligence layers ready:")
        logger.info(f"   📊 Indexed files: {files_count}")
        logger.info(f"   🕸️  Graph nodes: {graph_nodes}")
        logger.info(f"   🤖 LLM: {'Ready' if self.genai_client else 'Unavailable'}")
        
        # Initialize strategic planning agent
        self.planning_agent = StrategicPlanningAgent(
            analyzer=self.analyzer,
            genai_client=self.genai_client
        )
        logger.info(f"   🧠 Planning Agent: Ready")
        
        return True
    
    def identify_source_files(self, issue: str) -> List[str]:
        """Identify files likely causing the issue using multi-layer intelligence."""
        logger.info("🔍 Identifying Source Files...")
        
        candidate_files = []
        
        # Layer 1: Keyword-based identification  
        issue_keywords = issue.lower().split()
        
        for file_path in self.analyzer.dependency_data.get('files', {}):
            # Ensure absolute path
            if not os.path.isabs(file_path):
                file_path = os.path.join(self.current_session.repo_path, file_path)
            
            file_name = os.path.basename(file_path).lower()
            
            # Check for keyword matches in filename
            for keyword in issue_keywords:
                if keyword in file_name:
                    candidate_files.append((file_path, 0.8, f"filename contains '{keyword}'"))
        
        # Layer 2: Knowledge graph analysis
        if self.analyzer.kg:
            # Look for critical components that match issue context
            critical_files = self.analyzer.find_critical_components()[:5]
            for file_info in critical_files:
                file_path = file_info.get('name', '').replace('file:', '')
                if file_path and file_path not in [f[0] for f in candidate_files]:
                    candidate_files.append((file_path, 0.6, "critical component"))
        
        # Layer 3: Main entry points (high impact)
        main_files = ['main.py', 'app.py', 'server.py', 'index.js', 'index.ts']
        for file_path in self.analyzer.dependency_data.get('files', {}):
            # Ensure absolute path
            if not os.path.isabs(file_path):
                file_path = os.path.join(self.current_session.repo_path, file_path)
            
            file_name = os.path.basename(file_path)
            if file_name in main_files:
                if file_path not in [f[0] for f in candidate_files]:
                    candidate_files.append((file_path, 0.9, "main entry point"))
        
        # Fallback: If no files found, include all Python files for LLM analysis
        if not candidate_files:
            logger.info("🔍 No candidates found, including all Python files for LLM analysis...")
            for root, dirs, files in os.walk(self.current_session.repo_path):
                for file in files:
                    if file.endswith('.py') and not file.startswith('.') and not file.endswith('.backup'):
                        file_path = os.path.join(root, file)
                        candidate_files.append((file_path, 0.7, "Python file for analysis"))
        
        # Sort by confidence and return top candidates
        candidate_files.sort(key=lambda x: x[1], reverse=True)
        
        top_files = [f[0] for f in candidate_files[:5]]  # Top 5 candidates
        
        logger.info(f"📋 Identified {len(top_files)} potential source files:")
        for i, (file_path, confidence, reason) in enumerate(candidate_files[:5], 1):
            rel_path = os.path.relpath(file_path, self.current_session.repo_path)
            logger.info(f"   {i}. {rel_path} (confidence: {confidence:.1f}, reason: {reason})")
        
        return top_files
    
    def generate_fix_for_file(self, file_path: str, issue: str) -> Optional[FileFix]:
        """Generate a fix for a specific file using LLM with rich context."""
        
        # Use LLM for intelligent code fixing
        if not self.genai_client:
            logger.warning(f"⚠️  LLM unavailable, skipping {file_path}")
            return None
        
        try:
            # Read current file content
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                original_content = f.read()
            
            # Generate rich context using all intelligence layers
            context = self._generate_comprehensive_context(file_path, issue)
            
            # Create enhanced LLM prompt with better prioritization
            prompt = f"""You are an expert Python developer specializing in critical bug fixes. Fix ONLY the most critical issues in this file.

File: {os.path.basename(file_path)}
Issue Context: {issue}

Repository Context:
{context}

Current File Content:
```python
{original_content}
```

CRITICAL FIXING PRIORITIES (fix in this order):
1. RUNTIME ERRORS: NameError, AttributeError, ImportError, TypeError
2. SYNTAX ERRORS: Missing colons, parentheses, indentation
3. WINDOWS COMPATIBILITY: Unicode/encoding issues (use ASCII-safe characters)
4. MISSING DEPENDENCIES: Undefined classes, functions, imports
5. LOGIC ERRORS: Type mismatches, incorrect algorithms

IMPORTANT RULES:
- For Windows console: Replace Unicode symbols (✅❌🔍) with ASCII (OK/FAIL/INFO)
- Fix undefined classes/functions by either importing or defining them
- Only fix critical issues that break execution
- Ignore cosmetic issues like print statements unless they cause encoding errors
- Preserve original functionality and structure
- Use proper error handling and type checking

Provide your response in this exact format:

ISSUE_FOUND: [Describe the specific critical issue you found, or "No critical issues found"]
CONFIDENCE: [Your confidence level from 0.0 to 1.0]
FIXED_CODE:
```
[The complete corrected file content, or "NO_FIX_NEEDED" if no changes required]
```

Important: Always provide the complete file content in FIXED_CODE section, never partial code."""

            logger.info(f"🤖 Generating fix for {os.path.relpath(file_path, self.current_session.repo_path)}")
            
            # Get LLM response
            response = self.genai_client.generate_text(prompt, max_tokens=4096)
            
            # Parse response
            return self._parse_fix_response(file_path, issue, original_content, response)
            
        except Exception as e:
            logger.error(f"❌ Failed to generate fix for {file_path}: {e}")
            return None
    
    def _parse_fix_response(self, file_path: str, issue: str, original_content: str, response: str) -> Optional[FileFix]:
        """Parse LLM response into a FileFix object."""
        try:
            lines = response.split('\n')
            
            issue_found = "Unknown issue"
            confidence = 0.5
            fixed_code = None
            
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                
                if line.startswith('ISSUE_FOUND:'):
                    issue_found = line.replace('ISSUE_FOUND:', '').strip()
                elif line.startswith('CONFIDENCE:'):
                    confidence_str = line.replace('CONFIDENCE:', '').strip()
                    try:
                        confidence = float(confidence_str)
                    except ValueError:
                        confidence = 0.5
                elif line.startswith('FIXED_CODE:'):
                    # Read the code block
                    i += 1
                    # Skip to the opening ```python or just ```
                    while i < len(lines) and not lines[i].strip().startswith('```'):
                        i += 1
                    
                    if i < len(lines):  # Found opening ```
                        i += 1  # Skip the ``` line
                        code_lines = []
                        while i < len(lines) and not lines[i].strip().startswith('```'):
                            code_lines.append(lines[i])
                            i += 1
                        fixed_code = '\n'.join(code_lines).strip()
                i += 1
            
            # Check if no fix needed
            if fixed_code and fixed_code.strip() == "NO_FIX_NEEDED":
                return None
            
            if not fixed_code:
                logger.warning(f"⚠️  No fixed code found in LLM response for {file_path}")
                return None
            
            return FileFix(
                file_path=file_path,
                issue_found=issue_found,
                fix_applied=f"LLM fix: {issue_found}",
                original_content=original_content,
                modified_content=fixed_code,
                confidence=confidence,
                iteration=self.current_session.current_iteration if self.current_session else 1
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to parse fix response: {e}")
            return None
    
    def apply_fix(self, file_fix: FileFix) -> bool:
        """Apply a fix to a file with backup."""
        try:
            # Create backup
            backup_path = f"{file_fix.file_path}.backup.{int(time.time())}"
            shutil.copy2(file_fix.file_path, backup_path)
            
            # Apply fix
            with open(file_fix.file_path, 'w', encoding='utf-8') as f:
                f.write(file_fix.modified_content)
            
            # Track fix
            self.current_session.files_modified.add(file_fix.file_path)
            self.current_session.fixes_applied.append({
                'iteration': file_fix.iteration,
                'file': os.path.relpath(file_fix.file_path, self.current_session.repo_path),
                'issue': file_fix.issue_found,
                'confidence': file_fix.confidence,
                'backup': backup_path
            })
            
            rel_path = os.path.relpath(file_fix.file_path, self.current_session.repo_path)
            logger.info(f"✅ Applied fix to {rel_path} (confidence: {file_fix.confidence:.2f})")
            logger.info(f"   Issue: {file_fix.issue_found}")
            logger.info(f"   Backup: {os.path.basename(backup_path)}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to apply fix to {file_fix.file_path}: {e}")
            return False
    
    def test_python_file_execution(self, file_path: str) -> tuple[bool, str]:
        """Test if a Python file can run without syntax errors."""
        try:
            rel_path = os.path.relpath(file_path, self.current_session.repo_path)
            logger.info(f"🧪 Testing execution: {rel_path}")
            
            # Change to the file's directory for proper imports
            file_dir = os.path.dirname(file_path)
            original_cwd = os.getcwd()
            
            try:
                os.chdir(file_dir)
                
                # Use subprocess to run the file with a timeout
                result = subprocess.run(
                    [sys.executable, os.path.basename(file_path)], 
                    capture_output=True, 
                    text=True, 
                    timeout=10,  # 10 second timeout
                    cwd=file_dir
                )
                
                if result.returncode == 0:
                    logger.info(f"   ✅ Execution successful!")
                    if result.stdout.strip():
                        logger.info(f"   📄 Output: {result.stdout.strip()[:100]}...")
                    return True, result.stdout
                else:
                    logger.warning(f"   ❌ Execution failed with return code {result.returncode}")
                    if result.stderr.strip():
                        logger.warning(f"   📄 Error: {result.stderr.strip()[:200]}...")
                    return False, result.stderr
                    
            finally:
                os.chdir(original_cwd)
                
        except subprocess.TimeoutExpired:
            logger.warning(f"   ⏰ Execution timeout (10s) - file may have infinite loop or long-running process")
            return False, "Execution timeout"
        except FileNotFoundError:
            logger.warning(f"   ❌ Python interpreter not found")
            return False, "Python interpreter not found"
        except Exception as e:
            logger.warning(f"   ❌ Execution test failed: {e}")
            return False, str(e)
    
    def verify_fix_effectiveness(self) -> bool:
        """Verify if the applied fixes resolved the issue."""
        logger.info("🔍 Verifying fix effectiveness...")
        
        # Step 1: Basic syntax analysis
        try:
            # Re-analyze repository to check for obvious errors
            analyzer = FastRepositoryAnalyzer(self.current_session.repo_path, quick_mode=True)
            success = analyzer.analyze_repository()
            
            if not success:
                logger.warning("⚠️  Repository analysis failed - may have introduced errors")
                return False
        except Exception as e:
            logger.error(f"❌ Syntax verification failed: {e}")
            return False
        
        # Step 2: Runtime testing of modified Python files
        runtime_results = []
        for file_path in self.current_session.files_modified:
            if file_path.endswith('.py'):
                can_run, output = self.test_python_file_execution(file_path)
                runtime_results.append((file_path, can_run, output))
        
        # Report results
        if runtime_results:
            successful_runs = sum(1 for _, can_run, _ in runtime_results if can_run)
            total_tests = len(runtime_results)
            
            logger.info(f"🧪 Runtime Test Results: {successful_runs}/{total_tests} files executed successfully")
            
            # Show details for failed runs
            for file_path, can_run, output in runtime_results:
                rel_path = os.path.relpath(file_path, self.current_session.repo_path)
                if not can_run:
                    logger.warning(f"   ❌ {rel_path}: {output[:100]}...")
                else:
                    logger.info(f"   ✅ {rel_path}: Working correctly")
            
            # Consider it successful if at least 80% of files run correctly
            success_rate = successful_runs / total_tests if total_tests > 0 else 1.0
            
            if success_rate >= 0.8:
                logger.info(f"✅ Verification successful - {success_rate:.1%} success rate")
                return True
            else:
                logger.warning(f"⚠️  Low success rate: {success_rate:.1%} - some fixes may need refinement")
                return False
        else:
            logger.info("✅ Repository analysis successful - no obvious syntax errors")
            return True
    
    def _generate_comprehensive_context(self, file_path: str, issue: str) -> str:
        """Generate rich context for LLM using all intelligence layers."""
        context_parts = []
        
        # Layer 1: Available classes and functions across the repository
        available_symbols = {}
        for file_path_key, file_info in self.analyzer.dependency_data.get('files', {}).items():
            try:
                symbols = file_info.get('symbols', [])
                if symbols and isinstance(symbols, list):
                    file_name = os.path.basename(file_path_key)
                    classes = []
                    functions = []
                    
                    for s in symbols:
                        if isinstance(s, dict):
                            symbol_type = s.get('type', '')
                            symbol_name = s.get('name', '')
                            if symbol_name:
                                if symbol_type == 'class':
                                    classes.append(symbol_name)
                                elif symbol_type == 'function':
                                    functions.append(symbol_name)
                    
                    if classes or functions:
                        available_symbols[file_name] = {
                            'classes': classes,
                            'functions': functions,
                            'imports': file_info.get('imports', []) if isinstance(file_info.get('imports', []), list) else []
                        }
            except Exception as e:
                # Skip this file if there's an issue with symbol processing
                continue
        
        context_parts.append(f"AVAILABLE SYMBOLS ACROSS REPOSITORY:")
        for file_name, symbols in available_symbols.items():
            if symbols['classes'] or symbols['functions']:
                context_parts.append(f"  {file_name}:")
                if symbols['classes']:
                    context_parts.append(f"    Classes: {', '.join(symbols['classes'])}")
                if symbols['functions']:
                    context_parts.append(f"    Functions: {', '.join(symbols['functions'][:10])}...")  # Limit to first 10
        
        # Layer 2: Current file info
        file_info = self.analyzer.dependency_data.get('files', {}).get(file_path, {})
        if file_info:
            context_parts.append(f"\nCURRENT FILE INFO:")
            context_parts.append(f"  Imports: {file_info.get('imports', [])}")
            context_parts.append(f"  Symbols: {len(file_info.get('symbols', []))} defined")
        
        # Layer 3: Common Python patterns for missing dependencies
        context_parts.append(f"\nCOMMON FIX PATTERNS:")
        context_parts.append(f"  - For missing classes: Define class or import from another file")
        context_parts.append(f"  - For encoding errors: Replace Unicode with ASCII equivalents")
        context_parts.append(f"  - For NameError: Check if function/variable is defined or imported")
        context_parts.append(f"  - For Windows: Use 'utf-8' encoding and ASCII symbols")
        
        return '\n'.join(context_parts)
    
    def heal_repository(self, repo_path: str, issue: str, max_iterations: int = 3, timeout: int = 120) -> HealingSession:
        """Main healing process with strategic planning."""
        session = self.start_healing_session(repo_path, issue, max_iterations, timeout)
        
        try:
            # Step 1: Analyze repository
            if not self.analyze_repository():
                session.status = "failed"
                session.final_message = "Failed to analyze repository"
                return session
            
            # Step 2: Create strategic repair plan
            logger.info("🧠 Creating strategic repair plan...")
            if self.planning_agent:
                self.current_plan = self.planning_agent.create_repair_plan(
                    repository_path=repo_path,
                    issues_description=issue
                )
                logger.info(f"📋 Plan created with {len(self.current_plan.tasks)} strategic tasks")
                
                # Export plan for reference
                plan_file = os.path.join(repo_path, f"repair_plan_{int(datetime.now().timestamp())}.json")
                try:
                    self.planning_agent.export_plan(plan_file)
                except Exception as e:
                    logger.warning(f"Could not export plan: {e}")
            else:
                logger.warning("⚠️ Planning agent not available - using legacy file identification")
            
            # Step 3: Identify source files (enhanced by planning or fallback)
            source_files = self._get_planned_source_files() or self.identify_source_files(issue)
            
            if not source_files:
                session.status = "failed"
                session.final_message = "No source files identified for the issue"
                return session
            
            # Step 4: Strategic task-based healing process
            if self.current_plan and self.current_plan.tasks:
                logger.info(f"🎯 Executing strategic repair plan with {len(self.current_plan.tasks)} tasks")
                self._execute_strategic_plan(session, max_iterations, timeout)
            else:
                logger.info("📝 Using legacy iteration-based healing")
                self._execute_legacy_healing(session, source_files, max_iterations)
            
        except Exception as e:
            logger.error(f"❌ Healing failed: {e}")
            session.status = "failed"
            session.final_message = f"Healing failed: {str(e)}"
        finally:
            session.total_time = (datetime.now() - session.start_time).total_seconds()
        
        return session
    
    def _execute_strategic_plan(self, session: HealingSession, max_iterations: int, timeout: int):
        """Execute healing using strategic task-based approach."""
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            session.current_iteration = iteration
            
            # Check timeout
            elapsed = (datetime.now() - session.start_time).total_seconds()
            if elapsed >= timeout:
                session.status = "timeout"
                session.final_message = f"Reached timeout of {timeout}s"
                break
            
            # Get next strategic task
            current_task = self.planning_agent.get_next_task()
            if not current_task:
                logger.info("✅ All strategic tasks completed!")
                session.status = "solved"
                session.final_message = "All planned tasks completed successfully"
                break
            
            logger.info(f"🎯 Executing Task {current_task.priority}: {current_task.task_id}")
            logger.info(f"   Strategy: {current_task.strategy}")
            logger.info(f"   Files: {len(current_task.target_files)} target files")
            logger.info(f"   Issues: {len(current_task.issues_to_fix)} issues to fix")
            
            fixes_applied = 0
            
            # Execute task on target files
            for file_path in current_task.target_files:
                if not os.path.exists(file_path):
                    logger.warning(f"⚠️ File not found: {file_path}")
                    continue
                
                logger.info(f"🔧 Processing: {os.path.relpath(file_path, session.repo_path)}")
                
                # Create task-specific issue description
                task_issues = [issue.description for issue in current_task.issues_to_fix if issue.file_path == file_path]
                task_description = f"Task {current_task.priority}: {current_task.strategy}. Issues: {'; '.join(task_issues[:3])}"
                
                # Generate strategic fix
                file_fix = self.generate_fix_for_file(file_path, task_description)
                
                if file_fix and file_fix.confidence > 0.3:
                    if self.apply_fix(file_fix):
                        fixes_applied += 1
                        session.fixes_applied += 1
                    else:
                        logger.warning(f"❌ Failed to apply fix to {os.path.basename(file_path)}")
                else:
                    logger.info(f"❌ No suitable fix generated for {os.path.basename(file_path)}")
            
            logger.info(f"📊 Task {current_task.task_id}: {fixes_applied} fixes applied")
            
            # Mark task as completed and move to next
            self.planning_agent.mark_task_completed(current_task.task_id)
            
            if fixes_applied == 0:
                logger.warning(f"⚠️ No fixes applied in task {current_task.task_id}")
            
        # Final status update
        if session.current_iteration >= max_iterations:
            session.status = "failed" 
            session.final_message = f"Max iterations ({max_iterations}) reached"
        elif not session.status:
            session.status = "solved"
            session.final_message = "Strategic healing completed successfully"
    
    def _execute_legacy_healing(self, session: HealingSession, source_files: List[str], max_iterations: int):
        """Execute healing using legacy iteration-based approach."""
        for iteration in range(1, max_iterations + 1):
            session.current_iteration = iteration
            logger.info(f"🔄 Legacy Iteration {iteration}/{max_iterations}")
            
            fixes_applied_this_iteration = 0
            
            for file_path in source_files:
                if not os.path.exists(file_path):
                    continue
                
                file_fix = self.generate_fix_for_file(file_path, session.issue_description)
                if file_fix and file_fix.confidence > 0.3:
                    if self.apply_fix(file_fix):
                        fixes_applied_this_iteration += 1
                        session.fixes_applied += 1
            
            logger.info(f"📊 Iteration {iteration} complete: {fixes_applied_this_iteration} fixes applied")
            
            if fixes_applied_this_iteration == 0:
                logger.info("ℹ️ No more fixes possible with current approach")
                break
        
        session.status = "solved" if session.fixes_applied > 0 else "failed"
        session.final_message = f"Legacy healing completed: {session.fixes_applied} fixes applied"
    
    def _get_planned_source_files(self) -> Optional[List[str]]:
        """Get source files from strategic plan if available."""
        if not self.current_plan or not self.current_plan.tasks:
            return None
        
        # Combine all target files from all tasks, prioritized by critical path
        planned_files = []
        
        # Add critical path files first
        for file_path in self.current_plan.critical_path:
            if file_path not in planned_files:
                planned_files.append(file_path)
        
        # Add remaining task target files
        for task in self.current_plan.tasks:
            for file_path in task.target_files:
                if file_path not in planned_files:
                    planned_files.append(file_path)
        
        return planned_files[:10]  # Limit to top 10 files
    
    def _finalize_session(self, session: HealingSession):
        """Finalize healing session with summary."""
        logger.info("=" * 60)
        logger.info(f"🎯 Self-Healing Session Complete")
        logger.info(f"📊 Status: {session.status.upper()}")
        logger.info(f"⏱️  Total time: {session.total_time:.1f}s")
        logger.info(f"🔄 Iterations: {session.current_iteration}/{session.max_iterations}")
        logger.info(f"📝 Files modified: {len(session.files_modified)}")
        logger.info(f"🔧 Total fixes applied: {len(session.fixes_applied)}")
        
        if session.final_message:
            logger.info(f"💬 Result: {session.final_message}")
        
        # Show modified files
        if session.files_modified:
            logger.info("📋 Modified files:")
            for file_path in session.files_modified:
                rel_path = os.path.relpath(file_path, session.repo_path)
                logger.info(f"   - {rel_path}")
        
        # Show fixes applied
        if session.fixes_applied:
            logger.info("🔧 Fixes applied:")
            for fix in session.fixes_applied:
                logger.info(f"   [{fix['iteration']}] {fix['file']}: {fix['issue']} (conf: {fix['confidence']:.2f})")


def main():
    """Main entry point for self-healing agent."""
    parser = argparse.ArgumentParser(
        description="Self-Healing Repository Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python self_healing_agent.py /path/to/repo "Memory usage too high in Kubernetes" --max-iterations 3 --timeout 120
  python self_healing_agent.py . "main.py import error" --max-iterations 5 --timeout 60
  python self_healing_agent.py ~/project "Deployment fails" --max-iterations 2 --timeout 90
        """
    )
    
    parser.add_argument('repository', help='Path to repository to heal')
    parser.add_argument('issue', help='Description of the issue to fix')
    parser.add_argument('--max-iterations', type=int, default=3, help='Maximum number of fix iterations (default: 3)')
    parser.add_argument('--timeout', type=int, default=120, help='Timeout in seconds (default: 120)')
    parser.add_argument('--service-account', default='prj-mm-genai-qa-001_sa-notebook-1c2123a13a2a.json', help='Path to GCP service account JSON')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')
    
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    
    args = parser.parse_args()
    
    # Validate inputs
    if not os.path.exists(args.repository):
        print(f"❌ Repository not found: {args.repository}")
        sys.exit(1)
    
    if not os.path.isdir(args.repository):
        print(f"❌ Not a directory: {args.repository}")
        sys.exit(1)
    
    if not os.path.exists(args.service_account):
        print(f"❌ Service account file not found: {args.service_account}")
        sys.exit(1)
    
    # Configure logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Create and run self-healing agent
        agent = SelfHealingAgent(args.service_account)
        
        session = agent.heal_repository(
            repo_path=args.repository,
            issue=args.issue,
            max_iterations=args.max_iterations,
            timeout=args.timeout
        )
        
        # Exit with appropriate code
        if session.status == "solved":
            print(f"\n🎉 SUCCESS: {session.final_message}")
            sys.exit(0)
        elif session.status == "timeout":
            print(f"\n⏰ TIMEOUT: {session.final_message}")
            sys.exit(2)
        else:
            print(f"\n❌ FAILED: {session.final_message}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  Healing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()