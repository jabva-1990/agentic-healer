from flask import Flask, render_template, jsonify, request
import subprocess
import threading
import time
import os
import sys
import json

app = Flask(__name__)

# Simple global state
output_lines = []
current_status = "idle"
process_running = False

@app.route('/')
def index():
    return render_template('basic.html')

@app.route('/start', methods=['POST'])
def start_healing():
    global current_status, output_lines, process_running
    
    if process_running:
        return jsonify({"error": "Healing already in progress"}), 400
    
    # Get all parameters from form
    repo_path = request.form.get('repo_path', 'test_repo')
    issue_description = request.form.get('issue_description', 'Auto-healing session')
    iterations = int(request.form.get('iterations', 3))
    timeout = int(request.form.get('timeout', 120))
    service_account = request.form.get('service_account', 'prj-mm-genai-qa-001_sa-notebook-1c2123a13a2a.json')
    verbose = request.form.get('verbose', 'true').lower() == 'true'
    ui_mode = request.form.get('ui_mode', 'true').lower() == 'true'
    
    # Validate parameters
    if not repo_path.strip():
        return jsonify({"error": "Repository path is required"}), 400
    
    if not issue_description.strip():
        return jsonify({"error": "Issue description is required"}), 400
    
    if iterations < 1 or iterations > 10:
        return jsonify({"error": "Iterations must be between 1 and 10"}), 400
    
    if timeout < 30 or timeout > 600:
        return jsonify({"error": "Timeout must be between 30 and 600 seconds"}), 400
    
    current_status = "running"
    output_lines = []
    process_running = True
    
    # Start healing in background with all parameters
    thread = threading.Thread(
        target=run_healing, 
        args=(repo_path, issue_description, iterations, timeout, service_account, verbose, ui_mode)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({"status": "started"})

@app.route('/status')
def get_status():
    return jsonify({
        "status": current_status,
        "output": output_lines,  # All lines instead of just last 50
        "total_lines": len(output_lines)
    })

def run_healing(repo_path, issue_description, iterations, timeout, service_account, verbose, ui_mode):
    global current_status, output_lines, process_running
    
    try:
        output_lines.append(f"[*] Starting healing for repository: {repo_path}")
        output_lines.append("=" * 50)
        output_lines.append(f"Issue: {issue_description}")
        output_lines.append(f"Iterations: {iterations}")
        output_lines.append(f"Timeout: {timeout}s")
        output_lines.append(f"Service Account: {service_account}")
        output_lines.append(f"Verbose: {verbose}")
        output_lines.append(f"UI Mode: {ui_mode}")
        output_lines.append("=" * 50)
        
        # Check if real_heal.py exists
        if not os.path.exists('real_heal.py'):
            output_lines.append("[ERROR] real_heal.py not found in current directory")
            current_status = "error"
            process_running = False
            return
        
        # Build command with all parameters
        cmd = [
            sys.executable, 'real_heal.py', 
            repo_path, 
            issue_description,
            '--iterations', str(iterations),
            '--timeout', str(timeout)
        ]
        
        # Add optional parameters
        if verbose:
            cmd.append('--verbose')
        
        output_lines.append(f"💻 Running command: {' '.join(cmd)}")
        output_lines.append("-" * 50)
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Read output line by line with better buffering
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                line = output.strip()
                if line:  # Only add non-empty lines
                    output_lines.append(line)
                    # Log for debugging
                    print(f"Captured line {len(output_lines)}: {line[:50]}...")
        
        # Ensure we capture any remaining output
        remaining_output, _ = process.communicate()
        if remaining_output:
            for line in remaining_output.strip().split('\n'):
                if line.strip():
                    output_lines.append(line.strip())
        
        # Wait for process to complete
        process.wait()
        
        if process.returncode == 0:
            current_status = "completed"
            output_lines.append("=" * 50)
            output_lines.append("✅ Healing completed successfully!")
        else:
            current_status = "failed"
            output_lines.append("=" * 50)
            output_lines.append(f"❌ Healing failed with exit code: {process.returncode}")
            
    except Exception as e:
        current_status = "error"
        output_lines.append("=" * 50)
        output_lines.append(f"💥 ERROR: {str(e)}")
    
    finally:
        process_running = False

if __name__ == '__main__':
    print("🚀 Basic Healing UI starting...")
    print("📊 Dashboard: http://localhost:5001")
    app.run(debug=True, host='0.0.0.0', port=5001)