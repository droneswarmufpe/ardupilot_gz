# Use the ArduPilot ROS 2 development image as the base environment
FROM ardupilot/ardupilot-dev-ros:latest

# Use bash as the default shell for all following RUN commands
SHELL ["/bin/bash", "-c"]

# Create a runtime directory required for graphical applications
RUN mkdir -p /tmp/runtime-root && chmod 700 /tmp/runtime-root
ENV XDG_RUNTIME_DIR=/tmp/runtime-root

# Select which version of Gazebo (Ignition) will be used -> harmonic
ENV GZ_VERSION=harmonic

# Set workspace source directory and copy project files inside the container
WORKDIR /root/ardu_ws/src/
COPY . /root/ardu_ws/src/ardupilot_gz

# Import dependencies defined in ros2_gz.repos using vcs (version control system)
RUN vcs import --input ardupilot_gz/ros2_gz.repos --recursive

# Clone Micro XRCE-DDS generator (required for fast communication with ArduPilot)
WORKDIR /root/ardu_ws/
RUN git clone --recurse-submodules https://github.com/ardupilot/Micro-XRCE-DDS-Gen.git

# Build Micro XRCE-DDS Gen using Gradle
WORKDIR /root/ardu_ws/Micro-XRCE-DDS-Gen
RUN ./gradlew assemble

# Add Micro XRCE-DDS script tools to PATH
ENV PATH=/root/ardu_ws/Micro-XRCE-DDS-Gen/scripts:$PATH

# Install MAVProxy ground station software
RUN pip install -U MAVProxy

# Install Gazebo Harmonic + ROS2 Gazebo bridge + MAVROS packages
RUN curl https://packages.osrfoundation.org/gazebo.gpg --output /usr/share/keyrings/pkgs-osrf-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg] https://packages.osrfoundation.org/gazebo/ubuntu-stable $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/gazebo-stable.list > /dev/null && \
    apt-get update && \
    apt-get install -y gz-harmonic ros-humble-ros-gzharmonic ros-humble-mavros ros-humble-mavros-extras

# Add additional rosdep source list for Gazebo packages
RUN wget https://raw.githubusercontent.com/osrf/osrf-rosdep/master/gz/00-gazebo.list -O /etc/ros/rosdep/sources.list.d/00-gazebo.list

# Install MAVROS geographiclib datasets for proper GPS/coordinate system support
RUN wget https://raw.githubusercontent.com/mavlink/mavros/master/mavros/scripts/install_geographiclib_datasets.sh && \
    chmod +x install_geographiclib_datasets.sh && \
    ./install_geographiclib_datasets.sh

# Resolve and install ROS 2 package dependencies inside the workspace
WORKDIR /root/ardu_ws
RUN . /opt/ros/humble/setup.bash && \
    apt-get update && \
    rosdep update && \
    rosdep install --from-paths src --ignore-src -r -y

# Build the ROS2 workspace using colcon
RUN . /opt/ros/humble/setup.bash && \
    colcon build && \
    . ./install/setup.bash

# Default command when container starts
CMD ["bash"]
