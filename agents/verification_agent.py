#!/usr/bin/env python3
"""
Verification Agent - Automated Code Testing and Feedback Loop

Tests fixed code and provides feedback to the healing agent for iterative improvement.
Ensures fixes actually work by running the code and detecting remaining issues.
"""

import os
import sys
import ast
import subprocess
import tempfile
import logging
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path
import json
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class VerificationResult:
    """Results from code verification."""
    file_path: str
    syntax_valid: bool
    execution_successful: bool
    runtime_errors: List[str]
    performance_issues: List[str]
    remaining_issues: List[str]
    execution_time: float
    memory_usage: Optional[float] = None
    
class CodeVerificationAgent:
    """Agent that verifies fixed code and provides feedback."""
    
    def __init__(self, repository_path: str):
        self.repository_path = os.path.abspath(repository_path)
        self.verification_results = {}
        
    def verify_repository(self, max_iterations: int = 4) -> Dict[str, Any]:
        """Main verification workflow with iterative feedback loop."""
        
        print("🔍 Code Verification Agent")
        print("=" * 50)
        print(f"📁 Repository: {self.repository_path}")
        print(f"🔄 Max iterations: {max_iterations}")
        print()
        
        iteration = 0
        all_issues_resolved = False
        
        while iteration < max_iterations and not all_issues_resolved:
            iteration += 1
            print(f"🔄 Verification Iteration {iteration}/{max_iterations}")
            print("-" * 40)
            
            # Step 1: Verify all Python files
            verification_results = self._verify_all_files()
            
            # Step 2: Analyze results
            issues_found = self._analyze_verification_results(verification_results)
            
            # Step 3: Check if all issues are resolved - EXIT EARLY IF SUCCESSFUL
            critical_issues = self._filter_critical_issues(issues_found)
            
            if not critical_issues:
                all_issues_resolved = True
                if issues_found:
                    minor_count = sum(len(issue.get('issues', [])) for issue in issues_found)
                    print(f"🎉 SUCCESS: All critical issues resolved! ({minor_count} minor cosmetic issues remain)")
                else:
                    print("🎉 SUCCESS: All issues resolved! Code verification passed.")
                print(f"✅ Early exit - No more iterations needed.")
                print(f"🏁 Repository is now fully functional.")
                break
                
            # Step 4: If critical issues remain and we have iterations left, trigger healing
            if iteration < max_iterations:
                print(f"⚠️ Found {len(critical_issues)} critical issues requiring healing...")
                if critical_issues:
                    self._trigger_healing_agent(critical_issues)
                    # Wait a moment for healing to complete
                    time.sleep(2)
                else:
                    print("   📝 Note: Only minor cosmetic issues remain (not critical)")
            else:
                if critical_issues:
                    print(f"❌ Maximum iterations ({max_iterations}) reached with {len(critical_issues)} unresolved critical issues.")
                else:
                    print(f"✅ Maximum iterations reached, but only minor issues remain.")
        
        # Final summary
        return self._generate_verification_summary(iteration, all_issues_resolved)
    
    def _verify_all_files(self) -> List[VerificationResult]:
        """Verify all Python files in the repository."""
        results = []
        python_files = self._find_python_files()
        
        print(f"🔍 Verifying {len(python_files)} Python files...")
        
        for file_path in python_files:
            print(f"   📝 Testing: {os.path.basename(file_path)}")
            result = self._verify_single_file(file_path)
            results.append(result)
            
            # Show immediate result
            if result.syntax_valid and result.execution_successful:
                print(f"      ✅ Passed")
            else:
                issues = len(result.runtime_errors) + len(result.remaining_issues)
                print(f"      ❌ Failed ({issues} issues)")
        
        return results
    
    def _verify_single_file(self, file_path: str) -> VerificationResult:
        """Verify a single Python file."""
        result = VerificationResult(
            file_path=file_path,
            syntax_valid=False,
            execution_successful=False,
            runtime_errors=[],
            performance_issues=[],
            remaining_issues=[],
            execution_time=0.0
        )
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            result.remaining_issues.append(f"File read error: {e}")
            return result
        
        # Step 1: Syntax validation
        try:
            ast.parse(content)
            result.syntax_valid = True
        except SyntaxError as e:
            result.remaining_issues.append(f"Syntax error: {e} (line {e.lineno})")
            return result  # Can't test execution if syntax is invalid
        
        # Step 2: Static analysis for common issues
        result.performance_issues.extend(self._check_performance_issues(content))
        
        # Step 3: Execution testing
        if self._is_executable_file(file_path, content):
            result.execution_successful, execution_errors, result.execution_time = self._test_execution(file_path)
            result.runtime_errors.extend(execution_errors)
        else:
            # For non-executable files, just check imports
            import_errors = self._check_imports(content)
            if import_errors:
                result.runtime_errors.extend(import_errors)
            else:
                result.execution_successful = True
        
        # Combine all issues
        result.remaining_issues.extend(result.runtime_errors)
        result.remaining_issues.extend(result.performance_issues)
        
        return result
    
    def _find_python_files(self) -> List[str]:
        """Find all Python files in the repository."""
        python_files = []
        
        for root, dirs, files in os.walk(self.repository_path):
            # Skip hidden directories and common build/cache directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in {
                '__pycache__', 'venv', 'env', 'node_modules', 'build', 'dist'
            }]
            
            for file in files:
                if file.endswith('.py') and not file.startswith('.'):
                    file_path = os.path.join(root, file)
                    python_files.append(file_path)
        
        return python_files
    
    def _check_performance_issues(self, content: str) -> List[str]:
        """Check for performance issues in code."""
        issues = []
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            line_stripped = line.strip()
            
            # Check for print statements (performance issue in production)
            if 'print(' in line_stripped and not line_stripped.startswith('#'):
                issues.append(f"Print statement on line {line_num} (performance impact)")
            
            # Check for time.sleep (blocking operations)
            if 'time.sleep(' in line_stripped:
                issues.append(f"Blocking sleep on line {line_num} (performance bottleneck)")
            
            # Check for inefficient patterns
            if 'for' in line_stripped and 'range(len(' in line_stripped:
                issues.append(f"Inefficient loop pattern on line {line_num} (use enumerate)")
            
            # Check for missing error handling
            if 'open(' in line_stripped and 'with' not in line_stripped:
                issues.append(f"File operation without context manager on line {line_num}")
        
        return issues
    
    def _is_executable_file(self, file_path: str, content: str) -> bool:
        """Check if file is executable (has main block or is a script)."""
        # Check for main block
        if 'if __name__ == "__main__"' in content:
            return True
        
        # Check for script-like patterns
        if content.strip().startswith('#!') or 'main()' in content:
            return True
        
        # Check filename patterns
        filename = os.path.basename(file_path).lower()
        if any(pattern in filename for pattern in ['main', 'run', 'start', 'app', 'script']):
            return True
        
        return False
    
    def _test_execution(self, file_path: str) -> Tuple[bool, List[str], float]:
        """Test if file executes successfully."""
        start_time = time.time()
        
        try:
            # Run the file with timeout
            result = subprocess.run(
                [sys.executable, file_path],
                capture_output=True,
                text=True,
                timeout=30,  # 30 second timeout
                cwd=os.path.dirname(file_path)
            )
            
            execution_time = time.time() - start_time
            
            if result.returncode == 0:
                return True, [], execution_time
            else:
                errors = []
                if result.stderr:
                    errors.append(f"Runtime error: {result.stderr.strip()}")
                if result.stdout and "Error" in result.stdout:
                    errors.append(f"Output error: {result.stdout.strip()}")
                
                return False, errors, execution_time
                
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            return False, ["Execution timeout (>30s) - possible infinite loop"], execution_time
            
        except Exception as e:
            execution_time = time.time() - start_time
            return False, [f"Execution failed: {e}"], execution_time
    
    def _check_imports(self, content: str) -> List[str]:
        """Check if all imports are valid."""
        import_errors = []
        
        try:
            # Create a temporary file to test imports
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp_file:
                # Write only imports to test them
                lines = content.split('\n')
                import_lines = []
                
                for line in lines:
                    line_stripped = line.strip()
                    if line_stripped.startswith(('import ', 'from ')) and not line_stripped.startswith('#'):
                        import_lines.append(line)
                
                tmp_file.write('\n'.join(import_lines))
                tmp_file.flush()
                
                # Test import execution
                result = subprocess.run(
                    [sys.executable, tmp_file.name],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode != 0 and result.stderr:
                    import_errors.append(f"Import error: {result.stderr.strip()}")
                
                # Clean up
                os.unlink(tmp_file.name)
                
        except Exception as e:
            import_errors.append(f"Import check failed: {e}")
        
        return import_errors
    
    def _analyze_verification_results(self, results: List[VerificationResult]) -> List[Dict[str, Any]]:
        """Analyze verification results and identify issues to fix."""
        issues_found = []
        
        for result in results:
            if not result.syntax_valid or not result.execution_successful or result.remaining_issues:
                file_issues = {
                    'file': os.path.relpath(result.file_path, self.repository_path),
                    'issues': result.remaining_issues,
                    'syntax_valid': result.syntax_valid,
                    'execution_successful': result.execution_successful,
                    'execution_time': result.execution_time
                }
                issues_found.append(file_issues)
        
        # Print detailed analysis
        print(f"\n📊 Verification Analysis:")
        print(f"   Total files tested: {len(results)}")
        
        syntax_valid = sum(1 for r in results if r.syntax_valid)
        execution_successful = sum(1 for r in results if r.execution_successful)
        
        print(f"   Syntax valid: {syntax_valid}/{len(results)}")
        print(f"   Execution successful: {execution_successful}/{len(results)}")
        print(f"   Files with issues: {len(issues_found)}")
        
        if issues_found:
            print(f"\n❌ Issues found in {len(issues_found)} files:")
            for issue in issues_found:
                print(f"      📁 {issue['file']}: {len(issue['issues'])} issues")
                for i, problem in enumerate(issue['issues'][:3], 1):  # Show first 3
                    print(f"         {i}. {problem}")
                if len(issue['issues']) > 3:
                    print(f"         ... and {len(issue['issues']) - 3} more")
        
        return issues_found
    
    def _trigger_healing_agent(self, issues_found: List[Dict[str, Any]]):
        """Trigger the healing agent with specific issues."""
        print(f"\n🛠️ Triggering Healing Agent for {len(issues_found)} problematic files...")
        
        # Create issue description from found problems
        issue_descriptions = []
        for issue in issues_found:
            file_issues = issue['issues']
            if file_issues:
                # Categorize issues
                syntax_issues = [i for i in file_issues if 'syntax' in i.lower()]
                runtime_issues = [i for i in file_issues if 'error' in i.lower() and 'syntax' not in i.lower()]
                performance_issues = [i for i in file_issues if 'performance' in i.lower() or 'print' in i.lower()]
                
                if syntax_issues:
                    issue_descriptions.append(f"Syntax errors in {issue['file']}")
                if runtime_issues:
                    issue_descriptions.append(f"Runtime errors in {issue['file']}")
                if performance_issues:
                    issue_descriptions.append(f"Performance issues in {issue['file']}")
        
        # Combine into comprehensive description
        combined_description = "Fix remaining issues: " + "; ".join(set(issue_descriptions))
        
        print(f"   🎯 Issue description: {combined_description}")
        
        # Import and run healing agent
        try:
            from agents.self_healing_agent import SelfHealingAgent
            
            # Use default service account path
            service_account_path = "prj-mm-genai-qa-001_sa-notebook-1c2123a13a2a.json"
            healing_agent = SelfHealingAgent(service_account_path)
            
            healing_session = healing_agent.heal_repository(
                repository_path=self.repository_path,
                issue_description=combined_description,
                max_iterations=2,  # Limit iterations per verification cycle
                timeout_seconds=60
            )
            
            print(f"   ✅ Healing completed: {healing_session.status}")
            print(f"   🔧 Fixes applied: {len(healing_session.fixes_applied)}")
            
        except Exception as e:
            print(f"   ❌ Healing agent failed: {e}")
    
    def _filter_critical_issues(self, issues_found: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter out only critical issues that prevent code execution."""
        critical_issues = []
        
        for issue in issues_found:
            critical_problems = []
            for problem in issue.get('issues', []):
                # Only consider these as critical (blocking execution):
                if any(keyword in problem.lower() for keyword in [
                    'syntax error', 'runtime error', 'import error', 'traceback',
                    'modulenotfounderror', 'importerror', 'syntaxerror', 'nameerror',
                    'indentationerror', 'division by zero', 'zerodivisionerror',
                    'execution timeout', 'infinite loop'
                ]):
                    critical_problems.append(problem)
                
                # Skip cosmetic/performance issues that don't break functionality:
                # - print statements (unless in tight loops)
                # - blocking sleep (unless excessive)
                # - inefficient patterns (unless truly problematic)
            
            if critical_problems:
                critical_issue = issue.copy()
                critical_issue['issues'] = critical_problems
                critical_issues.append(critical_issue)
        
        return critical_issues
    
    def _generate_verification_summary(self, iterations_used: int, all_resolved: bool) -> Dict[str, Any]:
        """Generate final verification summary."""
        print(f"\n🎯 Verification Complete")
        print("=" * 50)
        
        summary = {
            'iterations_used': iterations_used,
            'all_issues_resolved': all_resolved,
            'status': 'SUCCESS' if all_resolved else 'PARTIAL',
            'timestamp': time.time()
        }
        
        if all_resolved:
            print(f"✅ Status: SUCCESS")
            print(f"🔄 Iterations used: {iterations_used}")
            print(f"💬 Result: All issues resolved through iterative verification and healing")
        else:
            print(f"⚠️ Status: PARTIAL SUCCESS")
            print(f"🔄 Iterations used: {iterations_used} (max reached)")
            print(f"💬 Result: Some issues may remain unresolved")
        
        return summary

def main():
    """Main entry point for verification agent."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Code Verification Agent with Healing Feedback Loop"
    )
    parser.add_argument('repository', help='Path to repository to verify')
    parser.add_argument('--max-iterations', type=int, default=4, 
                       help='Maximum verification iterations (default: 4)')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Verbose output')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create and run verification agent
    agent = CodeVerificationAgent(args.repository)
    summary = agent.verify_repository(args.max_iterations)
    
    # Exit with appropriate code
    if summary['all_issues_resolved']:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()