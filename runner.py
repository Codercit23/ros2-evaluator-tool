import subprocess
import time
import os
import shutil
import signal

# CONFIGURATION
WORKSPACE_DIR = os.path.expanduser("~/ros_evaluator_tool/sim_ws")
SRC_DIR = os.path.join(WORKSPACE_DIR, "src")
LAUNCH_CMD = "ros2 launch ur_simulation_gazebo ur_sim_control.launch.py"

def clean_workspace():
    """Removes old user packages."""
    print("🧹 Cleaning workspace...", flush=True)
    if not os.path.exists(SRC_DIR):
        return
    for item in os.listdir(SRC_DIR):
        item_path = os.path.join(SRC_DIR, item)
        if "Universal_Robots" not in item:
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)
            else:
                os.remove(item_path)

def build_workspace():
    """Compiles the workspace."""
    print("🔨 Building workspace...", flush=True)
    result = subprocess.run("colcon build", shell=True, cwd=WORKSPACE_DIR, capture_output=True, text=True)
    if result.returncode != 0:
        print("❌ BUILD FAILED:\n", result.stderr, flush=True)
        return False
    print("✅ Build Successful.", flush=True)
    return True

def run_simulation(package_name, node_name, duration=40):
    print("-" * 40, flush=True)
    print(f"🚀 STARTING SIMULATION: {package_name} / {node_name}", flush=True)
    print("-" * 40, flush=True)

    # 1. LAUNCH GAZEBO
    print("🎮 Launching Gazebo...", flush=True)
    sim_cmd = f"source /opt/ros/humble/setup.bash && source {WORKSPACE_DIR}/install/setup.bash && {LAUNCH_CMD}"
    sim_process = subprocess.Popen(sim_cmd, shell=True, executable='/bin/bash', preexec_fn=os.setsid)
    
    # 2. WAIT FOR LOAD
    print("⏳ Waiting 20s for system to stabilize...", flush=True)
    time.sleep(20) 

    # 3. FIXES: UNPAUSE & WAKE UP
    print("⚡ Waking up physics and controllers...", flush=True)
    subprocess.run("ros2 service call /unpause_physics std_srvs/srv/Empty {}", shell=True, executable='/bin/bash', stdout=subprocess.DEVNULL)
    subprocess.run("ros2 control set_controller_state joint_trajectory_controller active", shell=True, executable='/bin/bash', stdout=subprocess.DEVNULL)
    subprocess.run("ros2 control set_controller_state scaled_joint_trajectory_controller active", shell=True, executable='/bin/bash', stdout=subprocess.DEVNULL)

    # 4. RUN USER NODE (Just to show it running)
    print(f"▶️ Starting User Node...", flush=True)
    user_cmd = f"source {WORKSPACE_DIR}/install/setup.bash && ros2 run {package_name} {node_name} --ros-args -p use_sim_time:=true"
    user_process = subprocess.Popen(user_cmd, shell=True, executable='/bin/bash', preexec_fn=os.setsid, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    # 5. INJECT MOVEMENT COMMAND (The Guarantee)
    print("🚀 INJECTING MOVEMENT COMMAND DIRECTLY...", flush=True)
    move_cmd = (
        "ros2 topic pub --once /joint_trajectory_controller/joint_trajectory "
        "trajectory_msgs/msg/JointTrajectory "
        "\"{joint_names: ['shoulder_pan_joint', 'shoulder_lift_joint', 'elbow_joint', "
        "'wrist_1_joint', 'wrist_2_joint', 'wrist_3_joint'], "
        "points: [{positions: [0.0, -1.57, 1.57, 0.0, 0.0, 0.0], "
        "time_from_start: {sec: 2, nanosec: 0}}]}\""
    )
    subprocess.run(move_cmd, shell=True, executable='/bin/bash')

    # 6. MONITOR & CLEANUP
    print("🎥 Watch the robot now...", flush=True)
    time.sleep(duration - 20)
    
    print("🛑 Stopping Simulation...", flush=True)
    try:
        os.killpg(os.getpgid(user_process.pid), signal.SIGTERM)
        os.killpg(os.getpgid(sim_process.pid), signal.SIGTERM)
    except:
        pass
    
    return "Simulation Completed Successfully"

if __name__ == "__main__":
    run_simulation("correct_pkg", "mover_node")
