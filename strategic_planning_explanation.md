# 🧠 Strategic Planning Agent - Detailed Explanation

## **How Planning Works in Each Iteration**

You're absolutely correct about the flow! Here's exactly what happens in each iteration:

### **🔄 Iteration Flow Overview**
```
Input: --iterations N (e.g., 3)
├── Iteration 1: Initial Issues → Planning → Self-Healing (10x calls) → Verification
├── Iteration 2: Remaining Issues → Updated Planning → Self-Healing (5x calls) → Verification  
└── Iteration 3: Final Issues → Targeted Planning → Self-Healing (3x calls) → Verification
```

---

## **📋 What Strategic Planning Looks Like**

### **1. Real Planning Structure** 

```json
{
  "plan_id": "repair_plan_1764557466",
  "repository_path": "test_repo_2",
  "total_issues": 15,
  "estimated_duration": "25 minutes", 
  "success_probability": 0.82,
  "critical_path": [
    "backend/user_service.py",
    "backend/product_service.js", 
    "k8s/deployment.yaml",
    "requirements.txt",
    "docker-compose.yml"
  ],
  "dependency_order": [
    "requirements.txt",           // Fix dependencies first
    "backend/user_service.py",    // Core service
    "backend/product_service.js", // Dependent service
    "k8s/services.yaml",          // Infrastructure
    "k8s/deployment.yaml"         // Final deployment
  ],
  "tasks": [
    {
      "task_id": "task_1_syntax_errors",
      "target_files": ["requirements.txt", "docker-compose.yml"],
      "strategy": "Fix syntax errors using pattern-based corrections",
      "priority": 1,
      "estimated_complexity": "Low",
      "prerequisites": [],
      "issues_to_fix": [
        {
          "file_path": "requirements.txt",
          "line_number": 77,
          "issue_type": "SYNTAX_ERROR", 
          "severity": "CRITICAL",
          "description": "Invalid pkg-resources==0.0.0 line causes parsing error",
          "suggested_fix": "Remove invalid pkg-resources line"
        },
        {
          "file_path": "docker-compose.yml",
          "line_number": 28,
          "issue_type": "SYNTAX_ERROR",
          "severity": "CRITICAL", 
          "description": "Missing quote in volume syntax",
          "suggested_fix": "Fix volume syntax: './uploads:/app/uploads'"
        }
      ],
      "expected_outcome": "All files become syntactically valid"
    },
    {
      "task_id": "task_2_runtime_errors",
      "target_files": ["backend/user_service.py"],
      "strategy": "Resolve missing imports and undefined references",
      "priority": 2,
      "estimated_complexity": "Medium",
      "prerequisites": ["task_1_syntax_errors"],
      "issues_to_fix": [
        {
          "file_path": "backend/user_service.py", 
          "line_number": 8,
          "issue_type": "IMPORT_ERROR",
          "severity": "HIGH",
          "description": "ModuleNotFoundError: No module named 'flask_sqlalchemy'",
          "suggested_fix": "Add Flask-SQLAlchemy==2.5.1 to requirements.txt"
        }
      ],
      "expected_outcome": "All files execute without runtime errors"
    },
    {
      "task_id": "task_3_security_issues", 
      "target_files": ["backend/user_service.py", "k8s/deployment.yaml"],
      "strategy": "Fix hardcoded credentials and security vulnerabilities",
      "priority": 3,
      "estimated_complexity": "High",
      "prerequisites": ["task_2_runtime_errors"],
      "issues_to_fix": [
        {
          "file_path": "backend/user_service.py",
          "line_number": 15,
          "issue_type": "SECURITY",
          "severity": "CRITICAL",
          "description": "Hardcoded secret key: 'dev_secret_key_123'",
          "suggested_fix": "Use environment variable: os.getenv('SECRET_KEY')"
        },
        {
          "file_path": "k8s/deployment.yaml", 
          "line_number": 35,
          "issue_type": "SECURITY",
          "severity": "HIGH",
          "description": "Hardcoded database password in environment",
          "suggested_fix": "Use Kubernetes secrets for sensitive data"
        }
      ],
      "expected_outcome": "Security vulnerabilities resolved"
    },
    {
      "task_id": "task_4_performance",
      "target_files": ["backend/user_service.py", "backend/product_service.js"],
      "strategy": "Remove debug prints and optimize performance",
      "priority": 4, 
      "estimated_complexity": "Low",
      "prerequisites": ["task_3_security_issues"],
      "issues_to_fix": [
        {
          "file_path": "backend/user_service.py",
          "line_number": 71,
          "issue_type": "PERFORMANCE", 
          "severity": "LOW",
          "description": "Debug print statement impacts performance",
          "suggested_fix": "Replace with proper logging or remove"
        }
      ],
      "expected_outcome": "Improved performance and clean code"
    }
  ]
}
```

---

## **🔄 Iteration-by-Iteration Execution**

### **Iteration 1: Initial Comprehensive Analysis**

**Input Issues**: `"Fix critical security vulnerabilities, configuration errors, and syntax issues"`

**Planning Agent Analysis**:
```python
# 1. Repository Structure Analysis
repo_analysis = {
  'python_files': ['backend/user_service.py'],
  'javascript_files': ['backend/product_service.js'], 
  'yaml_files': ['k8s/deployment.yaml', 'k8s/services.yaml'],
  'config_files': ['requirements.txt', 'docker-compose.yml'],
  'total_files': 18,
  'complexity_score': 8.5
}

# 2. Issue Detection & Classification
detected_issues = [
  'CRITICAL: pkg-resources syntax error (requirements.txt:77)',
  'CRITICAL: Hardcoded secrets (user_service.py:15,18)', 
  'HIGH: Missing imports (user_service.py:2)',
  'HIGH: Volume syntax error (docker-compose.yml:28)',
  'MEDIUM: Debug prints (user_service.py:71,107)',
  'LOW: Missing health checks (docker-compose.yml)'
]

# 3. Dependency Order Calculation
dependency_order = [
  'requirements.txt',      # Dependencies first
  'backend/user_service.py', # Core service 
  'k8s/services.yaml',     # Service definitions
  'k8s/deployment.yaml',   # Deployments last
  'docker-compose.yml'     # Container orchestration
]
```

**Self-Healing Agent Execution** (10 calls in this iteration):
```python
# Task 1: Fix Syntax Errors (2 calls)
self_healing_agent.fix_file('requirements.txt', 'Remove pkg-resources line')
self_healing_agent.fix_file('docker-compose.yml', 'Fix volume syntax')

# Task 2: Fix Import Errors (3 calls) 
self_healing_agent.fix_file('requirements.txt', 'Add Flask-SQLAlchemy')
self_healing_agent.fix_file('backend/user_service.py', 'Add missing imports')
self_healing_agent.fix_file('backend/user_service.py', 'Fix import order')

# Task 3: Fix Security Issues (3 calls)
self_healing_agent.fix_file('backend/user_service.py', 'Replace hardcoded secrets')
self_healing_agent.fix_file('k8s/deployment.yaml', 'Use Kubernetes secrets')
self_healing_agent.fix_file('.env.example', 'Add environment variables')

# Task 4: Performance Issues (2 calls)
self_healing_agent.fix_file('backend/user_service.py', 'Remove debug prints')
self_healing_agent.fix_file('backend/product_service.js', 'Optimize queries')
```

**Verification Results**:
```
✅ Syntax errors: RESOLVED (2/2)
✅ Import errors: RESOLVED (1/1) 
⚠️ Security issues: PARTIAL (2/4 fixed)
⚠️ Performance: PARTIAL (3/5 fixed)
❌ Configuration: NOT STARTED (0/3)

Remaining Issues: 8
Issues Resolved: 7
```

---

### **Iteration 2: Focused on Remaining Issues**

**Input Issues**: 
```
Previous iteration results + "Fix remaining security hardcoded credentials, 
missing Kubernetes resource limits, and container health checks"
```

**Updated Planning Agent Analysis**:
```python
# Focus on unresolved issues from iteration 1
remaining_issues = [
  'CRITICAL: Missing resource limits (k8s/deployment.yaml)',
  'HIGH: Hardcoded credentials (k8s/monitoring.yaml)',  
  'HIGH: Missing health checks (Dockerfile.user, Dockerfile.product)',
  'MEDIUM: Insecure CORS settings (user_service.py)',
  'MEDIUM: Missing error handling (product_service.js)'
]

# Updated task priorities based on verification feedback
updated_tasks = [
  {
    "task_id": "task_2_1_kubernetes_security",
    "strategy": "Add resource limits and security contexts to K8s manifests", 
    "priority": 1,  # Bumped to highest priority
    "target_files": ["k8s/deployment.yaml", "k8s/monitoring.yaml"]
  },
  {
    "task_id": "task_2_2_container_health", 
    "strategy": "Add health checks and optimize Docker configurations",
    "priority": 2,
    "target_files": ["backend/Dockerfile.user", "backend/Dockerfile.product"]
  }
]
```

**Self-Healing Agent Execution** (5 calls - more focused):
```python
# Kubernetes Security (3 calls)
self_healing_agent.fix_file('k8s/deployment.yaml', 'Add resource limits')
self_healing_agent.fix_file('k8s/deployment.yaml', 'Add security context')
self_healing_agent.fix_file('k8s/monitoring.yaml', 'Replace hardcoded passwords')

# Container Health (2 calls)
self_healing_agent.fix_file('backend/Dockerfile.user', 'Add health check')
self_healing_agent.fix_file('backend/Dockerfile.product', 'Add health check')
```

**Verification Results**:
```
✅ Kubernetes security: RESOLVED (3/3)
✅ Container health: RESOLVED (2/2)  
⚠️ Application security: PARTIAL (1/2 fixed)
⚠️ Error handling: PARTIAL (2/3 fixed)

Remaining Issues: 3
Issues Resolved: 12  
```

---

### **Iteration 3: Final Cleanup & Validation**

**Input Issues**: 
```
"Fix final application security issues and improve error handling 
based on verification feedback from iterations 1-2"
```

**Final Planning Agent Analysis**:
```python
# Target remaining critical issues only
final_issues = [
  'HIGH: Insecure CORS configuration (user_service.py:12)',
  'MEDIUM: Missing try-catch (product_service.js:45,67)',
  'LOW: Missing input validation (user_service.py:42)'
]

# Surgical fixes only
final_tasks = [
  {
    "task_id": "task_3_1_final_security",
    "strategy": "Apply final security patches and input validation",
    "priority": 1,
    "target_files": ["backend/user_service.py"]
  }
]
```

**Self-Healing Agent Execution** (3 calls - surgical fixes):
```python
# Final Security Patches (3 calls)  
self_healing_agent.fix_file('backend/user_service.py', 'Fix CORS configuration')
self_healing_agent.fix_file('backend/user_service.py', 'Add input validation')
self_healing_agent.fix_file('backend/product_service.js', 'Add error handling')
```

**Final Verification Results**:
```
✅ ALL ISSUES RESOLVED!
✅ Security: COMPLETE (15/15)
✅ Configuration: COMPLETE (8/8) 
✅ Performance: COMPLETE (5/5)
✅ Error handling: COMPLETE (6/6)

Total Issues Found: 15
Total Issues Resolved: 15
Success Rate: 100%
```

---

## **🎯 Key Planning Features**

### **1. Issue Classification System**
```python
class IssueSeverity(Enum):
    CRITICAL = "critical"    # Breaks execution (syntax, runtime)
    HIGH = "high"           # Major functionality issues  
    MEDIUM = "medium"       # Performance, maintainability
    LOW = "low"             # Cosmetic, style issues

class IssueCategory(Enum):
    SYNTAX_ERROR = "syntax_error"     # Invalid syntax
    RUNTIME_ERROR = "runtime_error"   # Import/execution errors  
    SECURITY = "security"             # Hardcoded secrets, vulnerabilities
    PERFORMANCE = "performance"       # Debug prints, inefficiencies
    STYLE = "style"                   # Code style, cleanup
```

### **2. Dependency-Aware Task Ordering**
```python
# Planning Agent automatically determines optimal order:
dependency_order = [
    "requirements.txt",           # Fix deps first
    "backend/user_service.py",    # Core service  
    "backend/product_service.js", # Dependent service
    "k8s/services.yaml",          # Service definitions
    "k8s/deployment.yaml",        # Deployments
    "docker-compose.yml"          # Orchestration last
]

# Tasks have prerequisites:
task_3.prerequisites = ["task_1_syntax", "task_2_imports"]
```

### **3. Adaptive Complexity & Success Estimation**
```python
def _estimate_success_probability(tasks):
    complexity_factors = {
        "Low": 0.9,     # 90% success rate
        "Medium": 0.75, # 75% success rate  
        "High": 0.6     # 60% success rate
    }
    # Combined probability across all tasks
    return product(complexity_factors[task.complexity] for task in tasks)
```

### **4. Iterative Feedback Integration**
- **Iteration 1**: Full analysis, comprehensive planning
- **Iteration 2**: Focus on verification failures, update priorities  
- **Iteration 3**: Surgical fixes for remaining issues

This is exactly how your auto-healing agent uses strategic planning to systematically resolve issues across multiple iterations! 🚀