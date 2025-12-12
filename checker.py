import os
import subprocess
import ast
import logging

class ROSCodeChecker:
    def __init__(self, package_path):
        self.path = package_path
        self.report = {
            "structure_errors": [],
            "syntax_warnings": [],
            "safety_warnings": [],
            "score": 100
        }

    def check_structure(self):
        """Checks for essential ROS 2 files."""
        files = os.listdir(self.path)
        
        # Check 1: package.xml
        if "package.xml" not in files:
            self.report["structure_errors"].append("Critical: Missing 'package.xml'. This is not a valid ROS package.")
            self.report["score"] -= 50
        
        # Check 2: Build system
        if "CMakeLists.txt" not in files and "setup.py" not in files:
            self.report["structure_errors"].append("Critical: Missing build file (CMakeLists.txt or setup.py).")
            self.report["score"] -= 30

    def check_syntax(self):
        """Runs flake8 on all Python files to find syntax errors."""
        for root, _, files in os.walk(self.path):
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    try:
                        # Run flake8 and capture output
                        result = subprocess.run(
                            ["flake8", file_path, "--select=E9,F63,F7,F82"], # Only critical errors
                            capture_output=True, text=True
                        )
                        if result.stdout:
                            self.report["syntax_warnings"].append(f"Syntax Error in {file}: {result.stdout.strip()}")
                            self.report["score"] -= 10
                    except Exception as e:
                        self.report["syntax_warnings"].append(f"Could not analyze {file}: {str(e)}")

    def check_safety_heuristics(self):
        """Scans code for dangerous patterns (loops without sleep)."""
        for root, _, files in os.walk(self.path):
            for file in files:
                if file.endswith(".py"):
                    self._analyze_python_safety(os.path.join(root, file))

    def _analyze_python_safety(self, file_path):
        with open(file_path, "r") as f:
            try:
                tree = ast.parse(f.read())
            except SyntaxError:
                return # Syntax check handles this

        # 1. Check for While Loops
        has_loop = False
        has_sleep = False
        
        for node in ast.walk(tree):
            if isinstance(node, ast.While):
                has_loop = True
                # Look for sleep inside the loop body
                for subnode in ast.walk(node):
                    if isinstance(subnode, ast.Call):
                        # crude check for time.sleep or rate.sleep
                        if getattr(subnode.func, 'attr', '') == 'sleep':
                            has_sleep = True
        
        if has_loop and not has_sleep:
            self.report["safety_warnings"].append(f"Safety Warning: {os.path.basename(file_path)} has a 'while' loop without a detected sleep(). This can crash the CPU.")
            self.report["score"] -= 15

    def generate_report(self):
        self.check_structure()
        self.check_syntax()
        self.check_safety_heuristics()
        
        # Normalize score
        self.report["score"] = max(0, self.report["score"])
        return self.report

# Simple test if run directly
if __name__ == "__main__":
    # Create a dummy folder to test if it works
    print("Checker module is ready. Import this in app.py")
