from flask import Flask, request, render_template, jsonify
import os
import zipfile
import shutil
import time

# Import your scripts
# Ensure checker.py and runner.py are in the same folder as app.py
from checker import ROSCodeChecker
from runner import run_simulation, build_workspace, clean_workspace

app = Flask(__name__, template_folder='../templates', static_folder='../static')

# --- CONFIGURATION ---
BASE_DIR = os.path.expanduser('~/ros_evaluator_tool')
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
SIM_WS_SRC = os.path.join(BASE_DIR, 'sim_ws/src')


os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handles ZIP upload and runs the code checker."""
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    # 1. Save and Unzip
    zip_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(zip_path)

    extract_path = os.path.join(UPLOAD_FOLDER, "current_upload")
    if os.path.exists(extract_path):
        shutil.rmtree(extract_path)
    
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_path)

    # 2. Find the actual package folder (in case of nested folders)
    package_path = extract_path
    found_pkg = False
    for root, dirs, files in os.walk(extract_path):
        if "package.xml" in files:
            package_path = root
            found_pkg = True
            break
            
    if not found_pkg:
        return jsonify({
            "score": 0, 
            "structure_errors": ["No package.xml found. Is this a valid ROS 2 package?"],
            "syntax_warnings": [],
            "safety_warnings": []
        })

    # 3. Run Checker
    checker = ROSCodeChecker(package_path)
    report = checker.generate_report()
    
    # Save path for the simulation step
    app.config['PKG_PATH'] = package_path
    app.config['PKG_NAME'] = os.path.basename(package_path) # Assumes folder name = package name
    
    return jsonify(report)

@app.route('/simulate', methods=['POST'])
def simulate():
    """Builds the package and runs the simulation."""
    pkg_path = app.config.get('PKG_PATH')
    if not pkg_path:
        return jsonify({"status": "Error: Please upload a package first."})

    # 1. Clean Workspace
    clean_workspace()

    # 2. Copy to Workspace
    pkg_name = os.path.basename(pkg_path)
    dest_path = os.path.join(SIM_WS_SRC, pkg_name)
    
    if os.path.exists(dest_path):
        shutil.rmtree(dest_path)
    shutil.copytree(pkg_path, dest_path)

    # 3. Build
    if not build_workspace():
        return jsonify({"status": "Build Failed! Check terminal for details."})

    # 4. Run Simulation
    # Note: We assume the user's node is named 'mover_node' for this assignment.
    # In a real tool, you'd parse package.xml or setup.py to find the node name.
    run_simulation(pkg_name, "mover_node", duration=25)
    
    return jsonify({"status": "Simulation Completed Successfully"})

if __name__ == '__main__':
    print("Starting ROS Tool Web Server...")
    app.run(debug=True, use_reloader=False, port=5000)
