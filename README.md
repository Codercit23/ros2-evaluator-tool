# ROS 2 Code Evaluator & Simulator 🤖

A full-stack tool that evaluates ROS 2 Python nodes for style/syntax errors and executes them in a Gazebo simulation to verify functionality.

## 🚀 Features
* **Static Code Analysis:** Checks `package.xml`, `setup.py`, and Python syntax using `flake8`.
* **Automated Simulation:** Launches Gazebo, spawns a UR5e robot, and executes the user's node.
* **Web Interface:** Simple Flask-based UI for uploading zips and viewing results.

## 🛠️ Installation

1.  **Clone the repository**
    ```bash
    git clone <YOUR_REPO_URL>
    cd ros_evaluator_tool
    ```

2.  **Install Dependencies**
    ```bash
    pip3 install flask flake8
    sudo apt install ros-humble-gazebo-ros-pkgs ros-humble-ros2-control ros-humble-ros2-controllers
    ```

3.  **Build the Simulation Workspace**
    ```bash
    cd sim_ws
    colcon build
    source install/setup.bash
    ```

## ▶️ Usage

1.  **Start the Web Server**
    ```bash
    cd ~/ros_evaluator_tool
    source /opt/ros/humble/setup.bash
    python3 backend/app.py
    ```

2.  **Open Browser**
    Go to `http://127.0.0.1:5000`

3.  **Upload & Test**
    * Upload a zipped ROS 2 package (e.g., `test_packages/correct_pkg.zip`).
    * Click **Check Code** to see the quality score.
    * Click **Run Simulation** to see the robot move.

## 📂 Project Structure
* `backend/`: Contains `app.py` (Flask), `checker.py` (Static Analysis), and `runner.py` (Simulation Logic).
* `sim_ws/`: The ROS 2 workspace containing the simulation environment.
* `templates/`: HTML frontend.
* `test_packages/`: Sample correct and faulty packages for testing.
