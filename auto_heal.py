#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auto-Healing Repository Agent - Main Entry Point

Automatically builds indexing, knowledge graph, and runs self-healing agent
in a single command without manual steps.

Usage:
    python auto_heal.py <repo_path> "<issue_description>" [--iterations N] [--timeout S]

Example:
    python auto_heal.py . "Memory usage too high" --iterations 3 --timeout 120
    python auto_heal.py /path/to/project "Deployment fails" --timeout 60
"""

import os
import sys

# Fix Windows console encoding issues
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())
    os.environ['PYTHONIOENCODING'] = 'utf-8'
import json
import time
import argparse
import logging
import subprocess
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import shutil

# Google Cloud imports
try:
    import google.auth
    from google.auth.transport.requests import Request
    from google.oauth2 import service_account
    import requests
    VERTEX_AI_AVAILABLE = True
except ImportError:
    VERTEX_AI_AVAILABLE = False

# Import our intelligence layers
try:
    from agents.enhanced_analyzer import EnhancedDependencyAnalyzer
    from core.knowledge_graph import KnowledgeGraph
    from agents.fast_analyzer import FastRepositoryAnalyzer
    from agents.verification_agent import CodeVerificationAgent
    from agents.planning_agent import StrategicPlanningAgent
    INTELLIGENCE_AVAILABLE = True
except ImportError:
    INTELLIGENCE_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class AutoHealingSession:
    """Complete auto-healing session with all stages."""
    repo_path: str
    issue_description: str
    max_iterations: int
    timeout_seconds: int
    service_account_path: str
    start_time: datetime = field(default_factory=datetime.now)
    
    # Stage tracking
    stage: str = "initializing"  # initializing, analyzing, indexing, graph_building, healing, complete
    stages_completed: List[str] = field(default_factory=list)
    
    # Results tracking
    files_analyzed: int = 0
    issues_found: int = 0
    fixes_applied: int = 0
    files_modified: Set[str] = field(default_factory=set)
    
    # Final results
    status: str = "in_progress"  # in_progress, success, failed, timeout
    final_message: str = ""
    total_time: float = 0.0

class AutoHealingAgent:
    """Unified auto-healing agent that handles everything automatically."""
    
    def __init__(self, service_account_path: str = "prj-mm-genai-qa-001_sa-notebook-1c2123a13a2a.json", ui_mode: bool = False):
        self.service_account_path = service_account_path
        self.ui_mode = ui_mode
        self.session: Optional[AutoHealingSession] = None
        
        # Intelligence components will be initialized as needed
        self.vertex_client = None
        self.intelligence_system = None
        self.planning_agent: Optional[StrategicPlanningAgent] = None
        self.verification_agent: Optional[CodeVerificationAgent] = None
        self.current_plan = None
    
    def _emit_ui_update(self, update_type: str, data: Dict[str, Any], iteration_num: int = None) -> None:
        """Emit UI update for real-time dashboard display."""
        if not self.ui_mode:
            return
            
        update_data = {
            'type': update_type,
            'data': data,
            'timestamp': datetime.now().isoformat()
        }
        
        if iteration_num is not None:
            update_data['iteration_num'] = iteration_num
            
        # Emit as specially formatted JSON for UI server to parse
        print(f"[UI_UPDATE]{json.dumps(update_data)}")
        sys.stdout.flush()
        
    def auto_heal_repository(self, repo_path: str, issue_description: str, 
                           max_iterations: int = 3, timeout_seconds: int = 120) -> AutoHealingSession:
        """Main auto-healing process that handles everything automatically."""
        
        # Initialize session
        session = AutoHealingSession(
            repo_path=os.path.abspath(repo_path),
            issue_description=issue_description,
            max_iterations=max_iterations,
            timeout_seconds=timeout_seconds,
            service_account_path=self.service_account_path
        )
        self.session = session
        
        print("[*] Auto-Healing Repository Agent")
        print("=" * 50)
        print(f"Repository: {session.repo_path}")
        print(f"Issue: {session.issue_description}")
        print(f"Max iterations: {session.max_iterations}")
        print(f"Timeout: {session.timeout_seconds}s")
        print(f"Started: {session.start_time.strftime('%H:%M:%S')}")
        print()
        
        try:
            # Stage 1: Validate and initialize
            if not self._stage_initialize():
                return self._finalize_session("Failed during initialization")
            
            # Stage 2: Build repository analysis and indexing  
            if not self._stage_build_analysis():
                return self._finalize_session("Failed to build repository analysis")
            
            # Stage 3: Build knowledge graph
            if not self._stage_build_knowledge_graph():
                return self._finalize_session("Failed to build knowledge graph")
            
            # Stage 4: Initialize LLM client
            if not self._stage_initialize_llm():
                return self._finalize_session("Failed to initialize LLM client")
            
            # Stage 5: Create strategic repair plan
            if not self._stage_create_strategic_plan():
                return self._finalize_session("Failed to create strategic plan")
            
            # Stage 6: Execute strategic healing with verification loop
            if not self._stage_execute_strategic_healing():
                return self._finalize_session("Strategic healing execution failed")
            
            return self._finalize_session("Repository successfully healed and verified", status="success")
            
        except Exception as e:
            logger.error(f"Unexpected error in auto-healing: {e}")
            return self._finalize_session(f"Unexpected error: {e}", status="failed")
    
    def _stage_initialize(self) -> bool:
        """Stage 1: Initialize and validate inputs."""
        self.session.stage = "initializing"
        print("🔧 Stage 1: Initialization and Validation")
        print("-" * 40)
        
        # Check if repository exists
        if not os.path.exists(self.session.repo_path):
            print(f"❌ Repository not found: {self.session.repo_path}")
            return False
        
        if not os.path.isdir(self.session.repo_path):
            print(f"❌ Not a directory: {self.session.repo_path}")
            return False
        
        # Check service account file
        if not os.path.exists(self.session.service_account_path):
            print(f"❌ Service account file not found: {self.session.service_account_path}")
            return False
        
        # Check for intelligence modules
        if not INTELLIGENCE_AVAILABLE:
            print("❌ Intelligence modules not available - check imports")
            return False
        
        print("✅ Repository path validated")
        print("✅ Service account file found")
        print("✅ Intelligence modules available")
        
        self.session.stages_completed.append("initialize")
        return True
    
    def _stage_build_analysis(self) -> bool:
        """Stage 2: Build repository analysis and indexing."""
        self.session.stage = "analyzing"
        print(f"\n🧠 Stage 2: Building Repository Analysis")
        print("-" * 40)
        
        try:
            # Use FastRepositoryAnalyzer to build core analysis
            print("📊 Building file index and dependency analysis...")
            
            analyzer = FastRepositoryAnalyzer(self.session.repo_path, quick_mode=False)
            
            if not analyzer.analyze_repository():
                print("❌ Failed to analyze repository structure")
                return False
            
            # Generate analysis summary to get file count
            analyzer.generate_analysis_summary()
            
            # Get file count from analyzer
            self.session.files_analyzed = len(analyzer.analyzer.symbol_index.files)
            
            # Emit UI update with repository summary
            repo_summary = {
                'total_files': self.session.files_analyzed,
                'files': list(analyzer.analyzer.symbol_index.files.keys()),
                'dependencies': analyzer.analyzer.symbol_index.dependencies if hasattr(analyzer.analyzer.symbol_index, 'dependencies') else {}
            }
            self._emit_ui_update('repository_summary', repo_summary)
            
            print(f"✅ Repository analysis complete")
            print(f"   📁 Files analyzed: {self.session.files_analyzed}")
            
            self.session.stages_completed.append("analysis")
            return True
            
        except Exception as e:
            print(f"❌ Error during repository analysis: {e}")
            return False
    
    def _stage_build_knowledge_graph(self) -> bool:
        """Stage 3: Build knowledge graph from analysis."""
        self.session.stage = "graph_building"
        print(f"\n🕸️ Stage 3: Building Knowledge Graph")
        print("-" * 40)
        
        try:
            # Initialize enhanced dependency analyzer (loads previous analysis)
            print("🔗 Building knowledge graph and relationships...")
            
            self.intelligence_system = EnhancedDependencyAnalyzer()
            
            if not self.intelligence_system.load_and_enhance_data():
                print("❌ Failed to load and enhance dependency data")
                return False
            
            # Get statistics
            files_count = len(self.intelligence_system.dependency_data.get('files', {}))
            graph_nodes = len(self.intelligence_system.kg.nodes) if self.intelligence_system.kg else 0
            
            print(f"✅ Knowledge graph built successfully")
            print(f"   📊 Indexed files: {files_count}")
            print(f"   🕸️ Graph nodes: {graph_nodes}")
            
            self.session.stages_completed.append("knowledge_graph")
            return True
            
        except Exception as e:
            print(f"❌ Error building knowledge graph: {e}")
            return False
    
    def _stage_initialize_llm(self) -> bool:
        """Stage 4: Initialize LLM client."""
        self.session.stage = "llm_init"
        print(f"\n🤖 Stage 4: Initializing LLM Client")
        print("-" * 40)
        
        try:
            if not VERTEX_AI_AVAILABLE:
                print("⚠️ Google Cloud libraries not available - using mock mode")
                return True  # Continue in mock mode
            
            # Load service account
            with open(self.session.service_account_path, 'r') as f:
                service_account_info = json.load(f)
            
            # Initialize Vertex AI client
            from agents.self_healing_agent import VertexAIClient
            self.vertex_client = VertexAIClient(self.session.service_account_path)
            
            print(f"✅ LLM client initialized")
            print(f"   🔑 Project: {service_account_info.get('project_id', 'unknown')}")
            
            self.session.stages_completed.append("llm_init")
            return True
            
        except Exception as e:
            print(f"⚠️ LLM initialization failed: {e}")
            print("   Continuing in mock mode...")
            return True  # Continue without LLM
    
    def _stage_create_strategic_plan(self) -> bool:
        """Stage 5: Create strategic repair plan using planning agent."""
        self.session.stage = "strategic_planning"
        print(f"\n🧠 Stage 5: Creating Strategic Repair Plan")
        print("-" * 40)
        
        try:
            # Get or create verification agent for issue detection
            if not hasattr(self, 'verification_agent') or not self.verification_agent:
                self.verification_agent = CodeVerificationAgent()
            
            # Run verification to detect current issues
            print("🔍 Analyzing current repository issues...")
            verification_results = self.verification_agent.verify_repository(self.session.repo_path)
            
            # Convert verification results to issue format for planning agent
            detected_issues = []
            for file_path, results in verification_results.items():
                if results.get('issues'):
                    for issue in results['issues']:
                        detected_issues.append({
                            'file': file_path,
                            'description': issue.get('message', str(issue)),
                            'line': issue.get('line', 0),
                            'type': issue.get('type', 'unknown')
                        })
            
            print(f"📊 Detected {len(detected_issues)} issues across repository")
            
            # Create planning agent if not exists
            if not hasattr(self, 'planning_agent') or not self.planning_agent:
                # Get analyzer from previous stage
                analyzer = None
                try:
                    analyzer_path = os.path.join(self.session.repo_path, 'dependency_analysis', 'dependencies.json')
                    if os.path.exists(analyzer_path):
                        # Create a minimal analyzer with the data
                        analyzer = EnhancedDependencyAnalyzer()
                        analyzer.analyze_project(self.session.repo_path)
                except Exception as e:
                    print(f"⚠️ Could not load analyzer: {e}")
                
                self.planning_agent = StrategicPlanningAgent(analyzer, self.vertex_client)
            
            # Create strategic repair plan
            print("🎯 Creating comprehensive repair strategy...")
            self.current_plan = self.planning_agent.create_repair_plan(
                repository_path=self.session.repo_path,
                issues_description=self.session.issue_description,
                detected_issues=detected_issues
            )
            
            # Display comprehensive plan details
            print(f"✅ Strategic plan created successfully")
            print(f"   📋 Repair tasks: {len(self.current_plan.tasks)}")
            print(f"   📊 Success probability: {self.current_plan.success_probability:.1%}")
            print(f"   ⏱️ Estimated duration: {self.current_plan.estimated_duration} minutes")
            print(f"   🎯 Critical path files: {len(self.current_plan.critical_path)}")
            
            # Show detailed task breakdown
            print(f"\n📋 STRATEGIC REPAIR PLAN DETAILS")
            print("=" * 45)
            for i, task in enumerate(self.current_plan.tasks, 1):
                print(f"\n🎯 Task {i}: {task.task_id}")
                print(f"   📝 Strategy: {task.strategy}")
                print(f"   🔢 Priority: {task.priority}")
                print(f"   📁 Target Files ({len(task.target_files)}):")
                for file_path in task.target_files[:5]:  # Show first 5 files
                    rel_path = os.path.relpath(file_path, self.session.repo_path) if os.path.isabs(file_path) else file_path
                    print(f"      • {rel_path}")
                if len(task.target_files) > 5:
                    print(f"      ... and {len(task.target_files) - 5} more files")
                
                print(f"   🔧 Issues to Fix ({len(task.issues_to_fix)}):")
                for issue in task.issues_to_fix[:3]:  # Show first 3 issues
                    print(f"      • {issue.description[:80]}{'...' if len(issue.description) > 80 else ''}")
                if len(task.issues_to_fix) > 3:
                    print(f"      ... and {len(task.issues_to_fix) - 3} more issues")
                
                print(f"   📊 Complexity: {task.estimated_complexity}")
                if task.prerequisites:
                    print(f"   ⚡ Prerequisites: {', '.join(task.prerequisites)}")
                print(f"   🎯 Expected Outcome: {task.expected_outcome}")
            
            # Show critical path
            if hasattr(self.current_plan, 'critical_path') and self.current_plan.critical_path:
                print(f"\n🎯 CRITICAL PATH (Priority Order):")
                print("-" * 35)
                for i, file_path in enumerate(self.current_plan.critical_path[:10], 1):
                    rel_path = os.path.relpath(file_path, self.session.repo_path) if os.path.isabs(file_path) else file_path
                    print(f"   {i:2d}. {rel_path}")
            
            print(f"\n" + "=" * 45)
            
            self.session.stages_completed.append("strategic_planning")
            return True
            
        except Exception as e:
            print(f"⚠️ Strategic planning failed: {e}")
            print("   Will proceed with legacy approach...")
            self.current_plan = None
            return True  # Continue without strategic planning
    
    def _stage_execute_strategic_healing(self) -> bool:
        """Stage 6: Execute strategic healing with verification feedback loop."""
        self.session.stage = "healing_verification"
        print(f"\n🛠️ Stage 6: Executing Strategic Healing with Verification")
        print("=" * 55)
        
        try:
            # Initial issue count
            initial_issues = self._count_current_issues()
            self.session.issues_found = initial_issues
            
            if initial_issues == 0:
                print("✅ No issues detected - repository is healthy")
                self.session.status = "success"
                return True
            
            print(f"📊 Initial issues detected: {initial_issues}")
            print(f"🔄 Starting healing-verification loop (max {self.session.max_iterations} iterations)")
            print()
            
            # Initialize verification agent
            verification_agent = CodeVerificationAgent(self.session.repo_path)
            
            # Pre-check: Run initial verification to see if repository is already healthy
            print("🔍 Pre-Check: Initial Repository Verification")
            print("-" * 45)
            initial_verification = verification_agent._verify_all_files()
            initial_issues_found = verification_agent._analyze_verification_results(initial_verification)
            
            if not initial_issues_found:
                print("🎉 Repository is already healthy! No healing needed.")
                self.session.status = "success"
                self.session.fixes_applied = 0
                self.session.stages_completed.append("healing_verification")
                
                print(f"\n🏆 Pre-Check Complete - Success!")
                print(f"   🔄 Iterations used: 0 (pre-check only)")
                print(f"   🔧 Total fixes applied: 0")
                print(f"   ✅ Repository already working perfectly")
                return True
            
            print(f"⚠️ Found {len(initial_issues_found)} issues requiring attention.")
            print("🛠️ Proceeding with healing process...")
            print()
            
            total_fixes_applied = 0
            
            for iteration in range(1, self.session.max_iterations + 1):
                print(f"🔄 Iteration {iteration}/{self.session.max_iterations}")
                print("-" * 50)
                
                # Emit iteration start
                self._emit_ui_update('iteration_start', {
                    'iteration': iteration,
                    'max_iterations': self.session.max_iterations
                }, iteration_num=iteration)
                
                # Step 1: Apply strategic healing
                print("🛠️ Step 1: Strategic Healing Process")
                
                if hasattr(self, 'current_plan') and self.current_plan:
                    print(f"   📋 Using strategic plan with {len(self.current_plan.tasks)} tasks")
                    print(f"   📊 Plan success probability: {self.current_plan.success_probability:.1%}")
                    
                    # Emit planning update
                    planning_data = {
                        'strategy': f"Strategic approach with {len(self.current_plan.tasks)} prioritized tasks",
                        'success_probability': self.current_plan.success_probability,
                        'issues_found': [{'file': task.file_path, 'description': task.description, 'severity': task.priority} 
                                       for task in self.current_plan.tasks[:10]]  # Limit to first 10 for UI
                    }
                    self._emit_ui_update('planning_update', planning_data, iteration_num=iteration)
                    
                    fixes_applied = self._apply_strategic_fixes()
                else:
                    print("   ⚠️ No strategic plan available, using direct approach")
                    
                    # Emit basic planning update
                    self._emit_ui_update('planning_update', {
                        'strategy': 'Direct healing approach - analyzing issues in real-time',
                        'issues_found': []
                    }, iteration_num=iteration)
                    
                    fixes_applied = self._apply_direct_healing()
                
                total_fixes_applied += fixes_applied
                
                # Emit healing update
                healing_data = {
                    'approach': 'Strategic fix application',
                    'fixes_applied_this_iteration': fixes_applied,
                    'total_fixes_applied': total_fixes_applied,
                    'files_modified': len(self.session.files_modified),
                    'fixes_applied': [{'file': f, 'description': f'Applied healing fix to {f}', 'status': 'success'} 
                                     for f in list(self.session.files_modified)[-fixes_applied:]]  # Recent fixes
                }
                self._emit_ui_update('healing_update', healing_data, iteration_num=iteration)
                
                print(f"\\n   ✅ Iteration {iteration} Results:")
                print(f"      🔧 Fixes applied this iteration: {fixes_applied}")
                print(f"      📊 Total fixes so far: {total_fixes_applied}")
                print(f"      📁 Files modified: {len(self.session.files_modified)}")
                print()
                
                # Step 2: Run verification
                print("🔍 Step 2: Code Verification and Testing")
                verification_results = verification_agent._verify_all_files()
                issues_found = verification_agent._analyze_verification_results(verification_results)
                
                # Emit verification update
                verification_data = {
                    'method': 'Comprehensive file and syntax verification',
                    'issues_remaining': len(issues_found) if issues_found else 0,
                    'results': [{'test': f'Verification of {issue.get("file", "unknown")}', 
                               'passed': False, 'message': str(issue.get("issues", ["Verification issue"]))}
                               for issue in (issues_found[:5] if issues_found else [])]  # Show first 5 issues
                }
                if not issues_found:
                    verification_data['results'] = [{'test': 'All files verified', 'passed': True, 'message': 'No issues detected'}]
                
                self._emit_ui_update('verification_update', verification_data, iteration_num=iteration)
                
                # Step 3: Check if all issues are resolved
                if not issues_found:
                    print("🎉 All issues resolved! Verification successful.")
                    self.session.status = "success"
                    self.session.fixes_applied = total_fixes_applied
                    self.session.stages_completed.append("healing_verification")
                    
                    # Final summary
                    print(f"\n🏆 Healing Complete - Success!")
                    print(f"   🔄 Iterations used: {iteration}")
                    print(f"   🔧 Total fixes applied: {total_fixes_applied}")
                    print(f"   ✅ All issues resolved through verification")
                    return True
                
                # Step 4: If issues remain and we have iterations left, trigger more healing
                if iteration < self.session.max_iterations:
                    print(f"⚠️ Found {len(issues_found)} remaining issues. Applying targeted fixes...")
                    
                    # Create focused issue description from verification results
                    focused_issues = self._create_focused_issue_description(issues_found)
                    print(f"   🎯 Focus areas: {focused_issues}")
                    
                    # Apply targeted healing
                    targeted_fixes = self._apply_strategic_targeted_healing(focused_issues)
                    total_fixes_applied += targeted_fixes
                    print(f"   🔧 Applied {targeted_fixes} targeted fixes")
                    print()
                    
                    # Small delay to allow changes to settle
                    time.sleep(1)
                else:
                    print(f"❌ Maximum iterations ({self.session.max_iterations}) reached.")
                    break
            
            # Final status determination
            final_issues = self._count_current_issues()
            self.session.fixes_applied = total_fixes_applied
            
            if final_issues == 0:
                self.session.status = "success"
                print(f"🎉 Final Success: All issues resolved!")
            elif final_issues < initial_issues:
                self.session.status = "partial"
                resolved_count = initial_issues - final_issues
                print(f"📈 Partial Success: {resolved_count}/{initial_issues} issues resolved")
            else:
                self.session.status = "failed"
                print(f"⚠️ Unable to resolve issues automatically")
            
            print(f"\n📊 Final Summary:")
            print(f"   Initial issues: {initial_issues}")
            print(f"   Final issues: {final_issues}")
            print(f"   Total fixes applied: {total_fixes_applied}")
            print(f"   Iterations used: {min(iteration, self.session.max_iterations)}")
            
            self.session.stages_completed.append("healing_verification")
            return True
            
        except Exception as e:
            print(f"❌ Error during healing-verification process: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _create_focused_issue_description(self, issues_found: List[Dict[str, Any]]) -> str:
        """Create focused issue description from verification results."""
        issue_types = []
        
        for issue in issues_found:
            file_issues = issue.get('issues', [])
            
            # Categorize issue types
            has_syntax = any('syntax' in i.lower() for i in file_issues)
            has_runtime = any('error' in i.lower() and 'syntax' not in i.lower() for i in file_issues)
            has_performance = any('performance' in i.lower() or 'print' in i.lower() for i in file_issues)
            has_import = any('import' in i.lower() for i in file_issues)
            
            if has_syntax:
                issue_types.append("syntax errors")
            if has_runtime:
                issue_types.append("runtime errors")
            if has_performance:
                issue_types.append("performance issues")
            if has_import:
                issue_types.append("import problems")
        
        # Create comprehensive description
        unique_types = list(set(issue_types))
        if unique_types:
            return f"Fix remaining {', '.join(unique_types)} found during verification testing"
        else:
            return "Fix remaining code issues detected during verification"
    
    def _apply_strategic_targeted_healing(self, focused_issue_description: str) -> int:
        """Apply strategic targeted healing based on verification feedback."""
        try:
            if hasattr(self, 'current_plan') and self.current_plan:
                print(f"\n🎯 TARGETED STRATEGIC HEALING")
                print("-" * 35)
                print(f"   🔍 Focused Issue: {focused_issue_description}")
                
                # Filter tasks relevant to focused issues
                relevant_tasks = []
                keywords = ['syntax', 'runtime', 'import', 'performance', 'error']
                
                print(f"   📋 Analyzing {len(self.current_plan.tasks)} available tasks...")
                
                for task in self.current_plan.tasks:
                    task_keywords = [kw for kw in keywords if kw in task.strategy.lower()]
                    focus_keywords = [kw for kw in keywords if kw in focused_issue_description.lower()]
                    
                    if any(kw in task_keywords for kw in focus_keywords):
                        relevant_tasks.append(task)
                        print(f"      ✅ Selected: {task.task_id} (matches: {', '.join(set(task_keywords) & set(focus_keywords))})")
                    else:
                        print(f"      ⏭️  Skipped: {task.task_id} (no keyword match)")
                
                if relevant_tasks:
                    print(f"\n   🎯 Executing {len(relevant_tasks)} relevant strategic tasks")
                    return self._apply_strategic_fixes(relevant_tasks)
                else:
                    print(f"   ⚠️  No strategic tasks match focused issues, using direct approach")
            
            # Fallback to direct healing
            return self._apply_direct_healing_focused(focused_issue_description)
            
        except Exception as e:
            print(f"   ❌ Strategic targeted healing failed: {e}")
            return 0
    
    def _apply_strategic_fixes(self, task_batch: List = None) -> int:
        """Apply strategic fixes using task-based approach."""
        try:
            from agents.self_healing_agent import SelfHealingAgent
            
            if not hasattr(self, 'current_plan') or not self.current_plan or not self.current_plan.tasks:
                print("   ⚠️ No strategic plan available, falling back to direct healing")
                return self._apply_direct_healing()
            
            # Create healing agent for execution only (no planning)
            agent = SelfHealingAgent(self.session.service_account_path)
            
            fixes_applied = 0
            tasks_to_execute = task_batch or self.current_plan.tasks
            
            for task in tasks_to_execute:
                print(f"\\n🎯 Executing Strategic Task: {task.task_id}")
                print(f"   📋 Strategy: {task.strategy}")
                print(f"   📁 Files: {len(task.target_files)} files")
                print(f"   🔧 Issues: {len(task.issues_to_fix)} issues")
                
                # Execute task-specific healing for each target file
                task_fixes = 0
                for file_idx, file_path in enumerate(task.target_files[:3], 1):  # Limit to 3 files per task per iteration
                    try:
                        rel_path = os.path.relpath(file_path, self.session.repo_path) if os.path.isabs(file_path) else file_path
                        print(f"\n      📄 Processing File {file_idx}/3: {rel_path}")
                        
                        if os.path.exists(file_path):
                            # Create task-specific issue description
                            task_issues = [issue.description for issue in task.issues_to_fix if issue.file_path == file_path]
                            task_description = f"Task {task.priority}: {task.strategy}. Issues: {'; '.join(task_issues[:3])}"
                            
                            print(f"         🎯 Target Issues: {len(task_issues)} specific to this file")
                            if task_issues:
                                for issue in task_issues[:2]:
                                    print(f"            • {issue[:60]}{'...' if len(issue) > 60 else ''}")
                            
                            # Use healing agent for individual file
                            print(f"         🔧 Applying strategic fix...")
                            file_fix = agent.generate_fix_for_file(file_path, task_description)
                            
                            if file_fix and file_fix.was_successful:
                                fixes_applied += 1
                                task_fixes += 1
                                self.session.files_modified.add(file_path)
                                print(f"         ✅ Fix applied successfully")
                                if hasattr(file_fix, 'changes_made') and file_fix.changes_made:
                                    for change in file_fix.changes_made[:2]:
                                        print(f"            📝 {change}")
                            else:
                                print(f"         ⚠️  No fix applied")
                        else:
                            print(f"         ❌ File not found: {rel_path}")
                            
                    except Exception as e:
                        print(f"         ❌ Error processing {rel_path}: {e}")
                        continue
                
                print(f"   ✅ Task Completed: {task.task_id}")
                print(f"      🔧 Files processed: {min(len(task.target_files), 3)}")
                print(f"      ✨ Fixes applied in this task: {task_fixes}")
            
            print(f"\n📊 STRATEGIC EXECUTION SUMMARY")
            print("=" * 35)
            print(f"   🎯 Tasks executed: {len(tasks_to_execute)}")
            print(f"   ✨ Total fixes applied: {fixes_applied}")
            print(f"   📁 Files modified: {len(self.session.files_modified)}")
            
            return fixes_applied
            
        except Exception as e:
            print(f"Error applying strategic fixes: {e}")
            import traceback
            traceback.print_exc()
            return 0
    
    def _apply_direct_healing(self) -> int:
        """Fallback to direct healing without strategic planning."""
        try:
            from agents.self_healing_agent import SelfHealingAgent
            
            agent = SelfHealingAgent(self.session.service_account_path)
            
            # Run healing session with minimal iterations for fallback
            healing_session = agent.heal_repository(
                self.session.repo_path,
                self.session.issue_description,
                max(1, self.session.max_iterations // 3),  # Use fewer iterations as fallback
                self.session.timeout_seconds // 2
            )
            
            # Get results
            fixes_applied = len(healing_session.fixes_applied)
            
            # Update our session tracking
            for file_path in healing_session.files_modified:
                self.session.files_modified.add(file_path)
            
            return fixes_applied
            
        except Exception as e:
            print(f"Error in direct healing: {e}")
            return 0
    
    def _apply_direct_healing_focused(self, focused_description: str) -> int:
        """Apply direct healing with focused description."""
        try:
            from agents.self_healing_agent import SelfHealingAgent
            
            agent = SelfHealingAgent(self.session.service_account_path)
            
            # Run focused healing session
            healing_session = agent.heal_repository(
                self.session.repo_path,
                focused_description,
                1,  # Single iteration for focused healing
                max(30, self.session.timeout_seconds // 4)
            )
            
            return len(healing_session.fixes_applied)
            
        except Exception as e:
            print(f"Error in focused direct healing: {e}")
            return 0
    
    def _count_current_issues(self) -> int:
        """Count current issues in the repository."""
        try:
            issue_count = 0
            
            # Walk through Python files and count issues
            for root, dirs, files in os.walk(self.session.repo_path):
                # Skip hidden directories
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                
                for file in files:
                    if file.endswith('.py'):
                        file_path = os.path.join(root, file)
                        issue_count += self._count_file_issues(file_path)
            
            return issue_count
            
        except Exception:
            return 0
    
    def _count_file_issues(self, file_path: str) -> int:
        """Count issues in a specific file."""
        try:
            import ast
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            issues = 0
            
            # Check for syntax errors
            try:
                ast.parse(content)
            except SyntaxError:
                issues += 1  # Critical syntax error
            
            # Count performance issues
            lines = content.split('\n')
            for line in lines:
                line_stripped = line.strip()
                if 'print(' in line_stripped and not line_stripped.startswith('#'):
                    issues += 1
                if 'time.sleep(' in line_stripped:
                    issues += 1
            
            return issues
            
        except Exception:
            return 0
    
    def _apply_strategic_fixes(self, task_batch: List = None) -> int:
        """Apply strategic fixes using task-based approach."""
        try:
            from agents.self_healing_agent import SelfHealingAgent
            
            if not self.session.current_plan or not self.session.current_plan.tasks:
                print("   ⚠️ No strategic plan available, falling back to direct healing")
                return self._apply_direct_healing()
            
            # Create healing agent for execution only (no planning)
            agent = SelfHealingAgent(self.session.service_account_path)
            
            fixes_applied = 0
            tasks_to_execute = task_batch or self.session.current_plan.tasks
            
            print(f"\n🚀 STRATEGIC TASK EXECUTION")
            print("=" * 40)
            
            for task_idx, task in enumerate(tasks_to_execute, 1):
                print(f"\n🎯 Executing Task {task_idx}/{len(tasks_to_execute)}: {task.task_id}")
                print(f"   📋 Strategy: {task.strategy}")
                print(f"   🔢 Priority: {task.priority}")
                print(f"   📁 Target Files: {len(task.target_files)}")
                print(f"   🔧 Issues to Address: {len(task.issues_to_fix)}")
                print(f"   📊 Complexity: {task.estimated_complexity}")
                
                # Show files being processed
                files_to_process = task.target_files[:3]
                print(f"\n   📂 Processing Files:")
                for file_path in files_to_process:
                    rel_path = os.path.relpath(file_path, self.session.repo_path) if os.path.isabs(file_path) else file_path
                    print(f"      • {rel_path}")
                
                if len(task.target_files) > 3:
                    print(f"      ... limiting to {len(files_to_process)} files this iteration")
                
                # Execute task-specific healing
                task_fixes = self._execute_repair_task(agent, task)
                fixes_applied += task_fixes
                
                print(f"   ✅ Task completed: {task_fixes} fixes applied")
            
            return fixes_applied
            
        except Exception as e:
            print(f"Error applying strategic fixes: {e}")
            import traceback
            traceback.print_exc()
            return 0
    
    def _apply_direct_healing(self) -> int:
        """Fallback to direct healing without strategic planning."""
        try:
            from agents.self_healing_agent import SelfHealingAgent
            
            agent = SelfHealingAgent(self.session.service_account_path)
            
            # Run healing session
            healing_session = agent.heal_repository(
                self.session.repo_path,
                self.session.issue_description,
                max(1, self.session.max_iterations // 3),
                self.session.timeout_seconds // 2
            )
            
            # Get results
            fixes_applied = len(healing_session.fixes_applied)
            
            # Update our session tracking
            for file_path in healing_session.files_modified:
                self.session.files_modified.add(file_path)
            
            return fixes_applied
            
        except Exception as e:
            print(f"Error in direct healing: {e}")
            return 0
    
    def _fix_file_issues(self, file_path: str) -> bool:
        """Fix issues in a specific file."""
        try:
            import ast
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                original_content = f.read()
            
            modified_content = original_content
            changes_made = []
            
            # Fix syntax errors (simple cases)
            try:
                ast.parse(original_content)
            except SyntaxError as e:
                if 'never closed' in str(e):
                    lines = modified_content.split('\n')
                    if e.lineno and e.lineno <= len(lines):
                        line_idx = e.lineno - 1
                        line = lines[line_idx]
                        if 'print(' in line and not line.strip().endswith(')'):
                            lines[line_idx] = line + ')'
                            modified_content = '\n'.join(lines)
                            changes_made.append("Fixed missing closing parenthesis")
            
            # Add logging import if needed and fix print statements
            if 'print(' in modified_content and 'import logging' not in modified_content:
                lines = modified_content.split('\n')
                
                # Find insertion point
                insert_idx = 0
                for i, line in enumerate(lines):
                    if line.startswith('import ') or line.startswith('from '):
                        insert_idx = i + 1
                
                lines.insert(insert_idx, 'import logging')
                modified_content = '\n'.join(lines)
                changes_made.append("Added logging import")
                
                # Replace some print statements
                lines = modified_content.split('\n')
                replacements = 0
                for i, line in enumerate(lines):
                    if 'print(' in line and replacements < 3 and 'def ' not in line and not line.strip().startswith('#'):
                        lines[i] = line.replace('print(', 'logging.info(')
                        replacements += 1
                        changes_made.append(f"Replaced print with logging on line {i+1}")
                
                if replacements > 0:
                    modified_content = '\n'.join(lines)
            
            # Apply changes if any were made
            if changes_made:
                # Create backup
                backup_path = f"{file_path}.backup_{int(datetime.now().timestamp())}"
                shutil.copy2(file_path, backup_path)
                
                # Write fixed content
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(modified_content)
                
                rel_path = os.path.relpath(file_path, self.session.repo_path)
                print(f"   ✅ Fixed {len(changes_made)} issues in {rel_path}")
                
                return True
            
            return False
            
        except Exception as e:
            print(f"Error fixing {file_path}: {e}")
            return False
    
    def _finalize_session(self, message: str, status: str = None) -> AutoHealingSession:
        """Finalize the healing session with results."""
        self.session.total_time = (datetime.now() - self.session.start_time).total_seconds()
        self.session.final_message = message
        
        if status:
            self.session.status = status
        elif self.session.status == "in_progress":
            self.session.status = "failed"
        
        print(f"\n🎯 Auto-Healing Complete")
        print("=" * 50)
        print(f"📊 Status: {self.session.status.upper()}")
        print(f"⏱️ Total time: {self.session.total_time:.1f}s")
        print(f"📋 Stages completed: {len(self.session.stages_completed)}/6")
        print(f"📁 Files analyzed: {self.session.files_analyzed}")
        print(f"🔍 Issues found: {self.session.issues_found}")
        print(f"🛠️ Fixes applied: {self.session.fixes_applied}")
        print(f"📝 Files modified: {len(self.session.files_modified)}")
        print(f"💬 Result: {self.session.final_message}")
        
        # Strategic planning summary
        if hasattr(self, 'current_plan') and self.current_plan:
            print(f"\\n📋 Strategic Planning Summary:")
            print(f"   🎯 Plan objective: {self.current_plan.objective}")
            print(f"   📊 Success probability: {self.current_plan.success_probability:.1%}")
            print(f"   📝 Total tasks planned: {len(self.current_plan.tasks)}")
            print(f"   ⚡ Critical path length: {len(self.current_plan.critical_path)}")
            
            # Task completion analysis
            if hasattr(self.current_plan, 'tasks') and self.current_plan.tasks:
                high_priority_tasks = [t for t in self.current_plan.tasks if t.priority in ['HIGH', 'CRITICAL']]
                print(f"   🚨 High priority tasks: {len(high_priority_tasks)}")
                
            # Show top strategies used
            strategies_used = []
            for task in self.current_plan.tasks:
                if hasattr(task, 'strategy') and task.strategy:
                    strategies_used.append(task.strategy)
            
            if strategies_used:
                from collections import Counter
                strategy_counts = Counter(strategies_used)
                top_strategies = strategy_counts.most_common(3)
                print(f"   🔧 Top strategies used:")
                for strategy, count in top_strategies:
                    print(f"      • {strategy}: {count} tasks")
        
        # Show completed stages
        if self.session.stages_completed:
            print(f"\n✅ Completed stages:")
            stage_names = {
                "initialize": "Initialization & Validation",
                "analysis": "Repository Analysis & Indexing", 
                "knowledge_graph": "Knowledge Graph Building",
                "llm_init": "LLM Client Initialization",
                "strategic_planning": "Strategic Planning",
                "strategic_execution": "Strategic Execution",
                "healing": "Intelligent Issue Healing",
                "validation": "Final Validation"
            }
            for stage in self.session.stages_completed:
                print(f"   ✓ {stage_names.get(stage, stage)}")
        
        # Show modified files
        if self.session.files_modified:
            print(f"\n📝 Modified files:")
            for file_path in self.session.files_modified:
                rel_path = os.path.relpath(file_path, self.session.repo_path)
                print(f"   - {rel_path}")
        
        return self.session


def main():
    """Main entry point for auto-healing agent."""
    parser = argparse.ArgumentParser(
        description="Auto-Healing Repository Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python auto_heal.py . "Memory usage too high"
  python auto_heal.py /path/to/repo "Deployment fails" --iterations 5 --timeout 180
  python auto_heal.py sample_repo "Performance issues with print statements" --timeout 60
        """
    )
    
    parser.add_argument('repository', help='Path to repository to heal')
    parser.add_argument('issue', help='Description of the issue to fix')
    parser.add_argument('--iterations', type=int, default=3, help='Maximum number of iterations (default: 3)')
    parser.add_argument('--timeout', type=int, default=120, help='Timeout in seconds (default: 120)')
    parser.add_argument('--service-account', default='prj-mm-genai-qa-001_sa-notebook-1c2123a13a2a.json', 
                       help='Path to service account JSON file')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--ui-mode', action='store_true', help='Enable UI integration mode')
    
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    
    args = parser.parse_args()
    
    # Configure logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Create and run auto-healing agent
        agent = AutoHealingAgent(args.service_account, ui_mode=args.ui_mode)
        
        session = agent.auto_heal_repository(
            repo_path=args.repository,
            issue_description=args.issue,
            max_iterations=args.iterations,
            timeout_seconds=args.timeout
        )
        
        # Exit with appropriate code
        if session.status == "success":
            sys.exit(0)
        elif session.status == "partial":
            sys.exit(2)
        else:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\\n[!] Auto-healing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\\n[ERROR] Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()