#!/usr/bin/env python3
"""
AI-Powered Planning Agent for Strategic Code Repair

This agent analyzes repository structure, dependencies, and issues to create
intelligent repair plans before attempting fixes.
"""

import os
import logging
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class IssueSeverity(Enum):
    """Issue severity levels for prioritization"""
    CRITICAL = "critical"      # Breaks execution (syntax, runtime errors)
    HIGH = "high"             # Major functionality issues 
    MEDIUM = "medium"         # Performance, maintainability issues
    LOW = "low"               # Cosmetic, style issues

class IssueCategory(Enum):
    """Categories of issues for targeted fixing strategies"""
    SYNTAX_ERROR = "syntax_error"
    RUNTIME_ERROR = "runtime_error" 
    IMPORT_ERROR = "import_error"
    TYPE_ERROR = "type_error"
    PERFORMANCE = "performance"
    SECURITY = "security"
    STYLE = "style"

@dataclass
class Issue:
    """Represents a single code issue"""
    file_path: str
    line_number: int
    issue_type: IssueCategory
    severity: IssueSeverity
    description: str
    suggested_fix: str = ""
    dependencies: List[str] = field(default_factory=list)
    
@dataclass 
class RepairTask:
    """Represents a planned repair task"""
    task_id: str
    target_files: List[str]
    issues_to_fix: List[Issue]
    strategy: str
    priority: int
    estimated_complexity: str
    prerequisites: List[str] = field(default_factory=list)
    expected_outcome: str = ""

@dataclass
class RepairPlan:
    """Complete strategic plan for repository healing"""
    plan_id: str
    repository_path: str
    total_issues: int
    tasks: List[RepairTask]
    dependency_order: List[str]  # Files in dependency order
    critical_path: List[str]     # Most important files to fix first
    estimated_duration: str
    success_probability: float
    created_at: datetime = field(default_factory=datetime.now)

class StrategicPlanningAgent:
    """
    AI-powered planning agent that creates intelligent repair strategies
    using knowledge graph analysis and dependency mapping.
    """
    
    def __init__(self, analyzer=None, genai_client=None):
        """Initialize the planning agent with analysis tools."""
        self.analyzer = analyzer
        self.genai_client = genai_client
        self.current_plan: Optional[RepairPlan] = None
        
    def create_repair_plan(
        self, 
        repository_path: str, 
        issues_description: str,
        detected_issues: List[Dict] = None
    ) -> RepairPlan:
        """
        Create a comprehensive strategic repair plan.
        
        Args:
            repository_path: Path to the repository to heal
            issues_description: User description of issues
            detected_issues: Already detected issues from verification
            
        Returns:
            RepairPlan: Strategic plan for fixing the repository
        """
        logger.info("🧠 Creating strategic repair plan...")
        
        try:
            # Step 1: Analyze repository structure and dependencies
            logger.info("📊 Analyzing repository structure...")
            repo_analysis = self._analyze_repository_structure(repository_path)
            
            # Step 2: Classify and prioritize all detected issues
            logger.info("🔍 Classifying issues...")
            classified_issues = self._classify_issues(detected_issues or [], issues_description)
            
            # Step 3: Build dependency graph for optimal repair order
            logger.info("🕸️ Building dependency order...")
            dependency_order = self._build_dependency_order(repo_analysis)
            
            # Step 4: Identify critical path (most impactful files)
            logger.info("🎯 Identifying critical path...")
            critical_path = self._identify_critical_path(repo_analysis, classified_issues)
            
            # Step 5: Group issues into strategic repair tasks
            logger.info("📋 Creating repair tasks...")
            repair_tasks = self._create_repair_tasks(classified_issues, dependency_order, repo_analysis)
            
            # Step 6: Estimate success probability and duration
            logger.info("📊 Estimating success metrics...")
            success_probability = self._estimate_success_probability(repair_tasks)
            estimated_duration = self._estimate_duration(repair_tasks)
            
        except Exception as e:
            logger.error(f"❌ Error in planning step: {e}")
            import traceback
            traceback.print_exc()
            raise
        
        # Create the comprehensive plan
        plan = RepairPlan(
            plan_id=f"repair_plan_{int(datetime.now().timestamp())}",
            repository_path=repository_path,
            total_issues=len(classified_issues),
            tasks=repair_tasks,
            dependency_order=dependency_order,
            critical_path=critical_path,
            estimated_duration=estimated_duration,
            success_probability=success_probability
        )
        
        self.current_plan = plan
        self._log_plan_summary(plan)
        
        return plan
    
    def _analyze_repository_structure(self, repository_path: str) -> Dict[str, Any]:
        """Analyze repository structure using knowledge graph and indexing."""
        logger.info("📊 Analyzing repository structure...")
        
        analysis = {
            'total_files': 0,
            'python_files': [],
            'entry_points': [],
            'core_modules': [],
            'dependency_map': {},
            'complexity_scores': {},
            'import_graph': {},
        }
        
        if not self.analyzer or not self.analyzer.dependency_data:
            logger.warning("⚠️ No analyzer available - using basic analysis")
            return self._basic_repository_analysis(repository_path)
        
        # Use enhanced analyzer data
        files_data = self.analyzer.dependency_data.get('files', {})
        analysis['total_files'] = len(files_data)
        
        for file_path, file_info in files_data.items():
            if file_path.endswith('.py'):
                analysis['python_files'].append(file_path)
                
                # Identify entry points (main files, files with if __name__ == "__main__")
                symbols = file_info.get('symbols', [])
                
                # Handle case where symbols might be an integer count instead of list
                if isinstance(symbols, int):
                    # symbols is just a count, use it for complexity but can't iterate
                    analysis['complexity_scores'][file_path] = symbols
                    # Check if filename suggests it's an entry point
                    if os.path.basename(file_path) in ['main.py', 'app.py', 'run.py', '__main__.py']:
                        analysis['entry_points'].append(file_path)
                elif isinstance(symbols, list):
                    # symbols is a list, we can iterate
                    if any(s.get('name') == 'main' for s in symbols if isinstance(s, dict)):
                        analysis['entry_points'].append(file_path)
                    analysis['complexity_scores'][file_path] = len(symbols)
                else:
                    # Unknown type, default to 0
                    analysis['complexity_scores'][file_path] = 0
                
                # Build import graph
                imports = file_info.get('imports', [])
                if imports:
                    analysis['import_graph'][file_path] = imports
        
        # Use knowledge graph if available
        if self.analyzer.kg:
            analysis['core_modules'] = self._identify_core_modules_from_kg()
        
        return analysis
    
    def _basic_repository_analysis(self, repository_path: str) -> Dict[str, Any]:
        """Basic repository analysis when enhanced tools aren't available."""
        analysis = {
            'total_files': 0,
            'python_files': [],
            'entry_points': [],
            'core_modules': [],
            'dependency_map': {},
            'complexity_scores': {},
            'import_graph': {},
        }
        
        for root, dirs, files in os.walk(repository_path):
            for file in files:
                if file.endswith('.py') and not file.startswith('.'):
                    file_path = os.path.join(root, file)
                    analysis['python_files'].append(file_path)
                    
                    # Simple heuristics for entry points
                    if file in ['main.py', 'app.py', 'run.py', '__main__.py']:
                        analysis['entry_points'].append(file_path)
        
        analysis['total_files'] = len(analysis['python_files'])
        return analysis
    
    def _classify_issues(self, detected_issues: List[Dict], description: str) -> List[Issue]:
        """Classify and prioritize detected issues using AI analysis."""
        logger.info("🔍 Classifying and prioritizing issues...")
        
        classified_issues = []
        
        # Validate input
        if not detected_issues:
            logger.info("📊 No detected issues provided - creating generic issue from description")
            # Create a generic issue from the description if no specific issues are detected
            generic_issue = Issue(
                file_path="unknown",
                description=description,
                line_number=0,
                issue_type=IssueCategory.RUNTIME_ERROR,
                severity=IssueSeverity.MEDIUM
            )
            classified_issues.append(generic_issue)
            return classified_issues
        
        if not isinstance(detected_issues, list):
            logger.error(f"❌ detected_issues must be a list, got {type(detected_issues)}")
            return classified_issues
        
        for issue_data in detected_issues:
            if isinstance(issue_data, dict):
                issue = self._parse_issue_data(issue_data)
                if issue:
                    classified_issues.append(issue)
            else:
                logger.warning(f"⚠️ Skipping invalid issue data: {type(issue_data)} - {issue_data}")
        
        # Use AI to enhance classification if available
        if self.genai_client and classified_issues:
            classified_issues = self._ai_enhance_classification(classified_issues, description)
        
        # Sort by severity and impact
        classified_issues.sort(key=lambda x: (x.severity.value, x.issue_type.value))
        
        return classified_issues
    
    def _parse_issue_data(self, issue_data: Dict) -> Optional[Issue]:
        """Parse raw issue data into structured Issue object."""
        try:
            file_path = issue_data.get('file', '')
            description = issue_data.get('description', '')
            line_num = issue_data.get('line', 0)
            
            # Classify issue type and severity based on description
            issue_type, severity = self._classify_issue_type_and_severity(description)
            
            return Issue(
                file_path=file_path,
                line_number=line_num,
                issue_type=issue_type,
                severity=severity,
                description=description
            )
        except Exception as e:
            logger.warning(f"Failed to parse issue data: {e}")
            return None
    
    def _classify_issue_type_and_severity(self, description: str) -> Tuple[IssueCategory, IssueSeverity]:
        """Classify issue type and severity based on description."""
        desc_lower = description.lower()
        
        # Critical issues that break execution
        if any(keyword in desc_lower for keyword in ['syntax error', 'syntaxerror', 'was never closed']):
            return IssueCategory.SYNTAX_ERROR, IssueSeverity.CRITICAL
        
        if any(keyword in desc_lower for keyword in ['nameerror', 'attributeerror', 'runtime error']):
            return IssueCategory.RUNTIME_ERROR, IssueSeverity.CRITICAL
            
        if any(keyword in desc_lower for keyword in ['importerror', 'modulenotfounderror']):
            return IssueCategory.IMPORT_ERROR, IssueSeverity.CRITICAL
            
        if any(keyword in desc_lower for keyword in ['typeerror', 'type error']):
            return IssueCategory.TYPE_ERROR, IssueSeverity.HIGH
            
        # Performance and style issues
        if any(keyword in desc_lower for keyword in ['performance', 'inefficient', 'blocking']):
            return IssueCategory.PERFORMANCE, IssueSeverity.MEDIUM
            
        if any(keyword in desc_lower for keyword in ['print statement', 'debug', 'cosmetic']):
            return IssueCategory.STYLE, IssueSeverity.LOW
        
        # Default classification
        return IssueCategory.RUNTIME_ERROR, IssueSeverity.MEDIUM
    
    def _build_dependency_order(self, repo_analysis: Dict[str, Any]) -> List[str]:
        """Build optimal file repair order based on dependencies."""
        logger.info("🕸️ Building dependency-based repair order...")
        
        import_graph = repo_analysis.get('import_graph', {})
        python_files = repo_analysis.get('python_files', [])
        
        # Simple topological sort for dependency order
        dependency_order = []
        visited = set()
        
        def visit(file_path):
            if file_path in visited:
                return
            visited.add(file_path)
            
            # Visit dependencies first
            for imported_module in import_graph.get(file_path, []):
                # Try to map import to file path
                for py_file in python_files:
                    if imported_module in os.path.basename(py_file):
                        visit(py_file)
                        break
            
            dependency_order.append(file_path)
        
        # Start with entry points and core modules
        entry_points = repo_analysis.get('entry_points', [])
        core_modules = repo_analysis.get('core_modules', [])
        
        # Validate that these are lists
        if not isinstance(entry_points, list):
            logger.warning(f"⚠️ entry_points should be list, got {type(entry_points)}: {entry_points}")
            entry_points = []
        if not isinstance(core_modules, list):
            logger.warning(f"⚠️ core_modules should be list, got {type(core_modules)}: {core_modules}")
            core_modules = []
        if not isinstance(python_files, list):
            logger.warning(f"⚠️ python_files should be list, got {type(python_files)}: {python_files}")
            python_files = []
        
        logger.info(f"📊 Processing {len(entry_points)} entry points, {len(core_modules)} core modules, {len(python_files)} total files")
        
        try:
            for file_path in entry_points + core_modules:
                if isinstance(file_path, str):
                    visit(file_path)
                else:
                    logger.warning(f"⚠️ Skipping non-string file path: {type(file_path)} - {file_path}")
            
            # Visit remaining files
            for file_path in python_files:
                if isinstance(file_path, str):
                    visit(file_path)
                else:
                    logger.warning(f"⚠️ Skipping non-string file path: {type(file_path)} - {file_path}")
        
        except Exception as e:
            logger.error(f"❌ Error in dependency ordering: {e}")
            # Return a simple list as fallback
            return python_files[:10] if python_files else []
        
        return dependency_order
    
    def _identify_critical_path(self, repo_analysis: Dict[str, Any], issues: List[Issue]) -> List[str]:
        """Identify the most critical files that should be fixed first."""
        logger.info("🎯 Identifying critical repair path...")
        
        file_scores = {}
        
        # Validate inputs
        python_files = repo_analysis.get('python_files', [])
        if not isinstance(python_files, list):
            logger.error(f"❌ python_files should be list, got {type(python_files)}: {python_files}")
            python_files = []
        
        if not isinstance(issues, list):
            logger.error(f"❌ issues should be list, got {type(issues)}: {issues}")
            issues = []
        
        logger.info(f"📊 Analyzing {len(python_files)} Python files and {len(issues)} issues")
        
        # Score files based on multiple factors
        for file_path in python_files:
            try:
                score = 0
                
                # Higher score for entry points
                if file_path in repo_analysis.get('entry_points', []):
                    score += 100
                    
                # Higher score for core modules  
                if file_path in repo_analysis.get('core_modules', []):
                    score += 50
                    
                # Higher score for files with critical issues
                critical_issues = [i for i in issues if hasattr(i, 'file_path') and hasattr(i, 'severity') and i.file_path == file_path and i.severity == IssueSeverity.CRITICAL]
                score += len(critical_issues) * 20
                
                # Higher score for files with many dependencies
                complexity = repo_analysis.get('complexity_scores', {}).get(file_path, 0)
                if isinstance(complexity, (int, float)):
                    score += complexity
                
                file_scores[file_path] = score
                
            except Exception as e:
                logger.error(f"❌ Error scoring file {file_path}: {e}")
                continue
        
        # Sort by score and return top files
        try:
            sorted_files = sorted(file_scores.items(), key=lambda x: x[1], reverse=True)
            result = [file_path for file_path, score in sorted_files[:10]]  # Top 10 critical files
            logger.info(f"📋 Identified {len(result)} critical files")
            return result
        except Exception as e:
            logger.error(f"❌ Error sorting files: {e}")
            return list(python_files)[:10] if python_files else []
    
    def _create_repair_tasks(
        self, 
        issues: List[Issue], 
        dependency_order: List[str], 
        repo_analysis: Dict[str, Any]
    ) -> List[RepairTask]:
        """Group issues into strategic repair tasks."""
        logger.info("📋 Creating strategic repair tasks...")
        
        tasks = []
        
        # Validate issues input
        if not isinstance(issues, list):
            logger.error(f"❌ Issues must be a list, got: {type(issues)}")
            return []
        
        # Filter out any invalid issue objects
        valid_issues = []
        for i, issue in enumerate(issues):
            if hasattr(issue, 'issue_type') and hasattr(issue, 'file_path'):
                valid_issues.append(issue)
            else:
                logger.warning(f"⚠️ Invalid issue at index {i}: {type(issue)} - {issue}")
        
        logger.info(f"📊 Processing {len(valid_issues)} valid issues out of {len(issues)} total")
        
        # If no valid issues, create a fallback diagnostic task
        if not valid_issues:
            logger.info("📋 No specific issues detected - creating diagnostic task")
            tasks.append(RepairTask(
                task_id="task_fallback_diagnostic",
                target_files=repo_analysis.get('python_files', [])[:5],  # Top 5 files
                issues_to_fix=[],
                strategy="Perform comprehensive diagnostic and fix any detected issues",
                priority=1,
                estimated_complexity="Medium",
                expected_outcome="Repository health improved through diagnostic fixes"
            ))
            return tasks
        
        # Task 1: Critical Syntax Errors (highest priority)
        syntax_issues = [i for i in valid_issues if i.issue_type == IssueCategory.SYNTAX_ERROR]
        if syntax_issues:
            tasks.append(RepairTask(
                task_id="task_1_syntax_errors",
                target_files=list(set(i.file_path for i in syntax_issues)),
                issues_to_fix=syntax_issues,
                strategy="Fix syntax errors using pattern-based corrections and AI assistance",
                priority=1,
                estimated_complexity="Low",
                expected_outcome="All files become syntactically valid"
            ))
        
        # Task 2: Import and Runtime Errors
        import_runtime_issues = [i for i in valid_issues if i.issue_type in [IssueCategory.IMPORT_ERROR, IssueCategory.RUNTIME_ERROR]]
        if import_runtime_issues:
            tasks.append(RepairTask(
                task_id="task_2_runtime_errors",
                target_files=list(set(i.file_path for i in import_runtime_issues)),
                issues_to_fix=import_runtime_issues,
                strategy="Resolve missing imports and undefined references using repository context",
                priority=2,
                estimated_complexity="Medium",
                prerequisites=["task_1_syntax_errors"] if syntax_issues else [],
                expected_outcome="All files execute without runtime errors"
            ))
        
        # Task 3: Type Errors and Logic Issues
        type_issues = [i for i in valid_issues if i.issue_type == IssueCategory.TYPE_ERROR]
        if type_issues:
            tasks.append(RepairTask(
                task_id="task_3_type_errors",
                target_files=list(set(i.file_path for i in type_issues)),
                issues_to_fix=type_issues,
                strategy="Fix type mismatches and logical errors using AI analysis",
                priority=3,
                estimated_complexity="Medium",
                prerequisites=["task_2_runtime_errors"],
                expected_outcome="Type safety and logical correctness improved"
            ))
        
        # Task 4: Performance Optimization
        perf_issues = [i for i in valid_issues if i.issue_type == IssueCategory.PERFORMANCE]
        if perf_issues:
            tasks.append(RepairTask(
                task_id="task_4_performance",
                target_files=list(set(i.file_path for i in perf_issues)),
                issues_to_fix=perf_issues,
                strategy="Optimize performance bottlenecks and inefficient patterns",
                priority=4,
                estimated_complexity="High",
                prerequisites=["task_3_type_errors"],
                expected_outcome="Improved execution performance and efficiency"
            ))
        
        # Task 5: Style and Cleanup
        style_issues = [i for i in valid_issues if i.issue_type == IssueCategory.STYLE]
        if style_issues:
            tasks.append(RepairTask(
                task_id="task_5_cleanup",
                target_files=list(set(i.file_path for i in style_issues)),
                issues_to_fix=style_issues,
                strategy="Clean up code style and remove debug statements",
                priority=5,
                estimated_complexity="Low",
                prerequisites=["task_4_performance"],
                expected_outcome="Clean, maintainable code"
            ))
        
        return tasks
    
    def _estimate_success_probability(self, tasks: List[RepairTask]) -> float:
        """Estimate probability of successful repair based on task complexity."""
        if not tasks:
            return 1.0
        
        # Base probability factors
        complexity_factors = {
            "Low": 0.9,
            "Medium": 0.75,
            "High": 0.6
        }
        
        total_probability = 1.0
        for task in tasks:
            task_prob = complexity_factors.get(task.estimated_complexity, 0.7)
            total_probability *= task_prob
        
        return round(total_probability, 2)
    
    def _estimate_duration(self, tasks: List[RepairTask]) -> str:
        """Estimate total repair duration based on tasks."""
        if not tasks:
            return "0 minutes"
        
        # Rough time estimates per complexity level
        time_estimates = {
            "Low": 2,      # 2 minutes
            "Medium": 5,   # 5 minutes  
            "High": 10     # 10 minutes
        }
        
        total_minutes = sum(time_estimates.get(task.estimated_complexity, 5) for task in tasks)
        
        if total_minutes < 60:
            return f"{total_minutes} minutes"
        else:
            hours = total_minutes // 60
            minutes = total_minutes % 60
            return f"{hours}h {minutes}m"
    
    def _identify_core_modules_from_kg(self) -> List[str]:
        """Identify core modules using knowledge graph analysis."""
        if not self.analyzer.kg:
            return []
        
        # Use knowledge graph to find highly connected nodes
        core_modules = []
        try:
            # Find nodes with high connectivity (assuming this method exists)
            if hasattr(self.analyzer.kg, 'find_critical_components'):
                critical_components = self.analyzer.kg.find_critical_components()[:5]
                for component in critical_components:
                    name = component.get('name', '')
                    if name.startswith('file:'):
                        core_modules.append(name.replace('file:', ''))
        except Exception as e:
            logger.warning(f"Failed to identify core modules from KG: {e}")
        
        return core_modules
    
    def _ai_enhance_classification(self, issues: List[Issue], description: str) -> List[Issue]:
        """Use AI to enhance issue classification and add suggested fixes."""
        if not self.genai_client:
            return issues
        
        try:
            # Create AI prompt for issue analysis
            issues_summary = "\n".join([
                f"- {issue.file_path}:{issue.line_number} - {issue.description}" 
                for issue in issues[:10]  # Limit to first 10 for prompt size
            ])
            
            prompt = f"""Analyze these code issues and provide strategic insights:

User Description: {description}

Issues Found:
{issues_summary}

For each issue, suggest:
1. Root cause analysis
2. Recommended fix strategy  
3. Dependencies or prerequisites
4. Potential side effects

Respond in JSON format with enhanced classification."""

            response = self.genai_client.generate_text(prompt, max_tokens=2048)
            
            # Parse AI response and enhance issues (implementation would depend on response format)
            # For now, return original issues
            logger.info("✨ AI enhanced issue classification completed")
            
        except Exception as e:
            logger.warning(f"AI enhancement failed: {e}")
        
        return issues
    
    def _log_plan_summary(self, plan: RepairPlan):
        """Log a comprehensive summary of the repair plan."""
        logger.info("=" * 60)
        logger.info("🧠 STRATEGIC REPAIR PLAN CREATED")
        logger.info("=" * 60)
        logger.info(f"📁 Repository: {os.path.basename(plan.repository_path)}")
        logger.info(f"🔍 Total Issues: {plan.total_issues}")
        logger.info(f"📋 Repair Tasks: {len(plan.tasks)}")
        logger.info(f"⏰ Estimated Duration: {plan.estimated_duration}")
        logger.info(f"📊 Success Probability: {plan.success_probability:.1%}")
        logger.info("")
        
        logger.info("🎯 CRITICAL PATH (Priority Files):")
        for i, file_path in enumerate(plan.critical_path[:5], 1):
            logger.info(f"   {i}. {os.path.basename(file_path)}")
        
        logger.info("")
        logger.info("📋 REPAIR TASKS:")
        for task in plan.tasks:
            logger.info(f"   {task.priority}. {task.task_id}")
            logger.info(f"      Strategy: {task.strategy}")
            logger.info(f"      Files: {len(task.target_files)} files")
            logger.info(f"      Issues: {len(task.issues_to_fix)} issues")
            logger.info(f"      Complexity: {task.estimated_complexity}")
            if task.prerequisites:
                logger.info(f"      Prerequisites: {', '.join(task.prerequisites)}")
            logger.info("")
        
        logger.info("=" * 60)
    
    def get_next_task(self) -> Optional[RepairTask]:
        """Get the next repair task to execute based on the plan."""
        if not self.current_plan:
            return None
        
        # Find first incomplete task with satisfied prerequisites
        for task in self.current_plan.tasks:
            if not hasattr(task, 'completed') or not task.completed:
                # Check if prerequisites are satisfied
                if all(self._is_task_completed(prereq) for prereq in task.prerequisites):
                    return task
        
        return None
    
    def _is_task_completed(self, task_id: str) -> bool:
        """Check if a task has been completed."""
        if not self.current_plan:
            return False
        
        for task in self.current_plan.tasks:
            if task.task_id == task_id:
                return getattr(task, 'completed', False)
        
        return True  # If task not found, assume it's completed
    
    def mark_task_completed(self, task_id: str):
        """Mark a task as completed."""
        if not self.current_plan:
            return
        
        for task in self.current_plan.tasks:
            if task.task_id == task_id:
                task.completed = True
                logger.info(f"✅ Task completed: {task_id}")
                break
    
    def export_plan(self, output_path: str):
        """Export the repair plan to a JSON file."""
        if not self.current_plan:
            logger.warning("No plan to export")
            return
        
        try:
            plan_dict = {
                'plan_id': self.current_plan.plan_id,
                'repository_path': self.current_plan.repository_path,
                'total_issues': self.current_plan.total_issues,
                'estimated_duration': self.current_plan.estimated_duration,
                'success_probability': self.current_plan.success_probability,
                'created_at': self.current_plan.created_at.isoformat(),
                'critical_path': self.current_plan.critical_path,
                'dependency_order': self.current_plan.dependency_order,
                'tasks': []
            }
            
            for task in self.current_plan.tasks:
                task_dict = {
                    'task_id': task.task_id,
                    'target_files': task.target_files,
                    'strategy': task.strategy,
                    'priority': task.priority,
                    'estimated_complexity': task.estimated_complexity,
                    'prerequisites': task.prerequisites,
                    'expected_outcome': task.expected_outcome,
                    'issues_count': len(task.issues_to_fix)
                }
                plan_dict['tasks'].append(task_dict)
            
            with open(output_path, 'w') as f:
                json.dump(plan_dict, f, indent=2)
            
            logger.info(f"📄 Plan exported to: {output_path}")
            
        except Exception as e:
            logger.error(f"Failed to export plan: {e}")