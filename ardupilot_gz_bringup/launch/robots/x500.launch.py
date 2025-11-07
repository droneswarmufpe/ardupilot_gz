# Copyright 2024 ArduPilot.org.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

"""
Launch an x500 quadcopter in Gazebo.
"""
import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction, LogInfo, IncludeLaunchDescription, RegisterEventHandler
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessStart
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

def launch_spawn_robot(context):
    """Return a Gazebo spawn robot launch description"""
    name = LaunchConfiguration("name")
    pos_x = LaunchConfiguration("x")
    pos_y = LaunchConfiguration("y")
    pos_z = LaunchConfiguration("z")
    rot_r = LaunchConfiguration("R")
    rot_p = LaunchConfiguration("P")
    rot_y = LaunchConfiguration("Y")

    spawn_robot =  Node(
        package="ros_gz_sim",
        executable="create",
        namespace=name,
        arguments=[
            "-  ",
            "",
            "-param",
            "",
            "-name",
            name,
            "-topic",
            "/robot_description",
            "-x",
            pos_x,
            "-y",
            pos_y,
            "-z",
            pos_z,
            "-R",
            rot_r,
            "-P",
            rot_p,
            "-Y",
            rot_y,
        ],
        output="screen",
    )
    return [spawn_robot]


def launch_state_pub_with_bridge(context):
    pkg_ardupilot_gz_description = get_package_share_directory("ardupilot_gz_description")
    pkg_project_bringup = get_package_share_directory("ardupilot_gz_bringup")
    
    # Path to the X500 SDF model
    sdf_file = os.path.join(
        pkg_ardupilot_gz_description, "models", "x500_with_ardupilot", "model.sdf"
    )

    with open(sdf_file, "r") as infp:
        robot_desc = infp.read()

    ros_gz_bridge_config = "x500_bridge.yaml"
    
    log = LogInfo(msg="Using x500_with_ardupilot model and x500_bridge.yaml")

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        output="both",
        parameters=[
            {"robot_description": robot_desc},
            {"frame_prefix": ""}, #LaunchConfiguration('name'), "/"}, # Potential: add namespace
        ],
    )

    bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        name="x500_bridge",
        parameters=[
            {
                "config_file": os.path.join(
                    pkg_project_bringup, "config", ros_gz_bridge_config
                ),
                "qos_overrides./tf_static.publisher.durability": "transient_local",
            }
        ],
        output="screen",
    )

    topic_tools_tf = Node(
        package="topic_tools",
        executable="relay",
        arguments=[
            "/gz/tf", # Consider namespacing if multiple robots: /<robot_name>/gz/tf
            "/tf",
        ],
        output="screen",
        respawn=False,
        condition=IfCondition(LaunchConfiguration("use_gz_tf")),
    )

    event = RegisterEventHandler(
                OnProcessStart(
                    target_action=bridge,
                    on_start=[
                        topic_tools_tf
                    ]
                )
            )

    return [log, robot_state_publisher, bridge, event]

def generate_launch_arguments():
    """Generate a list of launch arguments"""
    return [
        DeclareLaunchArgument(
                "use_gz_tf", 
                default_value="true", 
                description="Use Gazebo TF."
            ),
        DeclareLaunchArgument(
            "model", # This argument is kept for consistency but sdf is hardcoded for x500
            default_value="x500_with_ardupilot",
            description="Model name (used by robot_state_publisher, but SDF is fixed for this launch file).",
        ),
        DeclareLaunchArgument(
            "name",
            default_value="x500",
            description="Name for the model instance in Gazebo.",
        ),
        DeclareLaunchArgument("x", default_value="0", description="Initial 'x' position (m)."),
        DeclareLaunchArgument("y", default_value="0", description="Initial 'y' position (m)."),
        DeclareLaunchArgument("z", default_value="0.3", description="Initial 'z' position (m)."), # Adjusted for X500
        DeclareLaunchArgument("R", default_value="0", description="Initial roll angle (radians)."),
        DeclareLaunchArgument("P", default_value="0", description="Initial pitch angle (radians)."),
        DeclareLaunchArgument("Y", default_value="0", description="Initial yaw angle (radians)."),
    ]

def generate_launch_description():
    launch_arguments = generate_launch_arguments()
    pkg_ardupilot_sitl = get_package_share_directory("ardupilot_sitl")

    # ArduPilot SITL specific launch
    # TODO: Create or verify existence of 'gazebo-x500.parm'
    # For now, using gazebo-iris.parm as a placeholder if x500 specific one is not available
    x500_params_file = os.path.join(pkg_ardupilot_sitl, "config", "default_params", "x500-sitl.param")
    if not os.path.exists(x500_params_file):
        x500_params_file = os.path.join(pkg_ardupilot_sitl, "config", "default_params", "gazebo-iris.param")
        print(f"Warning: gazebo-x500.parm not found, using {x500_params_file} as fallback.")


    sitl_dds = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                PathJoinSubstitution(
                    [
                        FindPackageShare("ardupilot_sitl"),
                        "launch",
                        "sitl_dds_udp.launch.py",
                    ]
                ),
            ]
        ),
        launch_arguments={
            "transport": "udp4",
            "port": "2019", # Ensure this doesn't clash if running multiple SITL instances
            "synthetic_clock": "True",
            "wipe": "False",
            "model": "json", # ArduPilot model type
            "speedup": "1",
            "slave": "0", # SITL slave index
            "instance": "0", # SITL instance number
            "defaults": x500_params_file
            + ","
            + os.path.join(
                pkg_ardupilot_sitl,
                "config",
                "default_params",
                "dds_udp.parm",
            ),
            "sim_address": "127.0.0.1",
            "master": "tcp:127.0.0.1:5760", # Ensure SITL ports are unique per instance
            "sitl": "127.0.0.1:5501",
        }.items(),
    )

    if "GZ_SIM_RESOURCE_PATH" in os.environ:
        gz_sim_resource_path = os.environ["GZ_SIM_RESOURCE_PATH"]
        if "SDF_PATH" in os.environ:
            sdf_path = os.environ["SDF_PATH"]
            if gz_sim_resource_path not in sdf_path:
                 os.environ["SDF_PATH"] = sdf_path + ":" + gz_sim_resource_path
        else:
            os.environ["SDF_PATH"] = gz_sim_resource_path

    opfunc_robot_state_publisher = OpaqueFunction(function=launch_state_pub_with_bridge)
    opfunc_spawn_robot = OpaqueFunction(function=launch_spawn_robot)
    
    ld = LaunchDescription(launch_arguments)
    ld.add_action(sitl_dds)
    ld.add_action(opfunc_robot_state_publisher)
    ld.add_action(opfunc_spawn_robot)

    return ld