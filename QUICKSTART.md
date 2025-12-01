# 🚀 Quick Start Guide

Simple guide to set up environment variables and run the auto-healing agent.

## 📋 Prerequisites

- Python 3.8 or higher
- Google Cloud Service Account JSON file (already included: `prj-mm-genai-qa-001_sa-notebook-1c2123a13a2a.json`)

## ⚙️ Environment Setup

### Option 1: Set Environment Variables (Recommended)

**For Windows PowerShell:**
```powershell
# Set Google API key (if you have one)
$env:GOOGLE_API_KEY="your-google-api-key-here"

# Verify it's set
echo $env:GOOGLE_API_KEY
```

**For Windows Command Prompt:**
```cmd
set GOOGLE_API_KEY=your-google-api-key-here
echo %GOOGLE_API_KEY%
```

**For Linux/Mac:**
```bash
export GOOGLE_API_KEY="your-google-api-key-here"
echo $GOOGLE_API_KEY
```

### Option 2: Use Service Account (Default)

The repo already includes a service account file, so you can skip environment variables and use the default configuration.

## 📦 Install Dependencies

```bash
pip install -r requirements.txt
```

## 🚀 Running the Auto-Healing Agent

### Basic Usage
```bash
python auto_heal.py sample_repo "Performance issues and syntax errors preventing proper execution"
```

### Full Command with Options
```bash
python auto_heal.py sample_repo "Performance issues and syntax errors preventing proper execution" --iterations 3 --timeout 60 --verbose
```

### Command Breakdown

| Parameter | Description | Example |
|-----------|-------------|---------|
| `sample_repo` | Path to repository to analyze | `sample_repo` or `/path/to/your/project` |
| `"Issue description"` | Description of what to fix | `"Performance issues and syntax errors"` |
| `--iterations 3` | Maximum fix attempts (optional) | `--iterations 5` |
| `--timeout 60` | Timeout in seconds (optional) | `--timeout 120` |
| `--verbose` | Detailed output (optional) | `--verbose` |

## 📝 Example Commands

### Fix Syntax Errors
```bash
python auto_heal.py sample_repo "Fix syntax errors in Python files"
```

### Fix Performance Issues
```bash
python auto_heal.py sample_repo "Optimize performance and remove bottlenecks" --timeout 120
```

### Fix Memory Issues
```bash
python auto_heal.py sample_repo "OutOfMemoryError in data processing" --iterations 5
```

### Custom Repository
```bash
python auto_heal.py /path/to/your/project "Fix import errors" --verbose
```

## 🎯 Expected Output

When you run the command, you'll see:

```
🚀 Auto-Healing Repository Agent
==================================================
📁 Repository: C:\...\sample_repo
🎯 Issue: Performance issues and syntax errors preventing proper execution
🔄 Max iterations: 3
⏰ Timeout: 60s
🕐 Started: 14:30:25

🔧 Stage 1: Initialization and Validation
----------------------------------------
✅ Repository path validated
✅ Service account file found
✅ Intelligence modules available

🧠 Stage 2: Building Repository Analysis
----------------------------------------
📊 Building file index and dependency analysis...
✅ Repository analysis complete
   📁 Files analyzed: 6

🕸️ Stage 3: Building Knowledge Graph
----------------------------------------
🔗 Building knowledge graph and relationships...
✅ Knowledge graph built successfully
   📊 Indexed files: 6
   🕸️ Graph nodes: 13

🤖 Stage 4: Initializing LLM Client
----------------------------------------
✅ LLM client initialized

🛠️ Stage 5: Intelligent Issue Healing
----------------------------------------
🔍 Detecting and fixing issues...
📊 Found 22 issues to fix
✅ Applied 3 fixes successfully

✅ Stage 6: Final Validation
----------------------------------------
🔍 Issues before healing: 22
🔍 Issues after healing: 19
🔧 Fixes applied: 3

🎯 Auto-Healing Complete
==================================================
📊 Status: SUCCESS
⏱️ Total time: 72.4s
📝 Files modified: 3
💬 Result: Repository successfully healed
```

## 🛠️ Troubleshooting

### Common Issues

**Issue:** `ModuleNotFoundError`
```bash
# Solution: Install dependencies
pip install -r requirements.txt
```

**Issue:** `Repository not found`
```bash
# Solution: Use correct path
python auto_heal.py ./sample_repo "your issue description"
# or absolute path
python auto_heal.py "C:\full\path\to\repo" "your issue description"
```

**Issue:** `Intelligence modules not available`
```bash
# Solution: Check file structure - ensure agents/ and core/ folders exist
ls agents/
ls core/
```

### Service Account Issues

If you get authentication errors:
1. Make sure `prj-mm-genai-qa-001_sa-notebook-1c2123a13a2a.json` exists
2. Use custom service account: `python auto_heal.py sample_repo "issue" --service-account /path/to/your/service-account.json`

## 📁 File Structure

Your workspace should look like:
```
healing_agent/
├── auto_heal.py                    # 🚀 Main script
├── agents/                         # 🤖 AI agents
├── core/                           # ⚙️ Core functionality  
├── sample_repo/                    # 🧪 Test repository
├── dependency_analysis/            # 📊 Analysis results
├── prj-mm-genai-qa-001_sa-notebook-1c2123a13a2a.json  # 🔑 Service account
└── requirements.txt                # 📦 Dependencies
```

## ⚡ Quick Test

Test if everything works:
```bash
python auto_heal.py sample_repo "Test the system" --timeout 30
```

If you see success output, you're ready to use the auto-healing agent! 🎉