# Agentic Healer - Basic UI

Simple web interface for the Auto-Healing Repository Agent that works reliably on Windows.

## Files

### Required Files:
- `basic_ui.py` - Main Flask web server (runs on port 5001)
- `templates/basic.html` - Web dashboard interface
- `heal_safe.py` - Windows-compatible healing script (no Unicode issues)

### Usage:

1. **Start the UI:**
   ```bash
   python basic_ui.py
   ```

2. **Open Browser:**
   Go to: http://localhost:5001

3. **Run Healing:**
   - Repository Path: `test_repo` (or any other repo path)
   - Click "🚀 Start Healing"
   - Watch detailed planning and progress in real-time

## Features

✅ **Real-time Progress** - Live updates via polling (no WebSocket complexity)  
✅ **Windows Compatible** - No Unicode encoding errors  
✅ **Detailed Planning** - Shows issues found and planned fixes for each iteration  
✅ **Color-coded Output** - Planning (gold), Issues (red), Fixes (cyan), Success (green)  
✅ **Auto Test Repo** - Creates sample files automatically if needed  
✅ **Simple & Reliable** - Minimal dependencies, just Flask  

## Dependencies

Only requires Flask (no SocketIO or complex dependencies):
```bash
pip install flask
```

## Output Format

Each iteration shows:
1. **Planning Phase** - Issues identified and planned fixes
2. **Healing Phase** - Implementation of fixes  
3. **Verification Phase** - Testing and validation

Perfect for demonstrating the self-healing process with clear visibility into the AI's decision-making process.