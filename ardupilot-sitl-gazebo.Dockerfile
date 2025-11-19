FROM ardupilot/ardupilot-dev-ros:latest

LABEL one.project="multiple" \
      one.type="devcontainer" \
      one.environment="dogfood" \
      one.owner="robocin@cin.ufpe.br, fnap@cin.ufpe.br" \
      one.version="1.0.0" \
      one.description="This image is RobôCIn's base image for running \
      ardupilot sitl + gazebo + ros2."

SHELL ["/bin/bash", "-c"]

WORKDIR /root/ardu_ws/src
RUN vcs import --recursive --input https://raw.githubusercontent.com/ArduPilot/ardupilot/master/Tools/ros2/ros2.repos

WORKDIR /root/ardu_ws
RUN apt-get update && \
    rosdep update && \
    . /opt/ros/humble/setup.bash && \
    rosdep install --from-paths src --ignore-src -r -y

RUN git clone --recurse-submodules https://github.com/ardupilot/Micro-XRCE-DDS-Gen.git
WORKDIR /root/ardu_ws/Micro-XRCE-DDS-Gen
RUN ./gradlew assemble
ENV PATH=/root/ardu_ws/Micro-XRCE-DDS-Gen/scripts:$PATH

WORKDIR /root/ardu_ws
RUN . /opt/ros/humble/setup.bash && \
    colcon build --packages-up-to ardupilot_dds_tests ardupilot_sitl && \
    . ./install/setup.bash

RUN pip install -U MAVProxy

RUN curl https://packages.osrfoundation.org/gazebo.gpg --output /usr/share/keyrings/pkgs-osrf-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg] https://packages.osrfoundation.org/gazebo/ubuntu-stable $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/gazebo-stable.list > /dev/null && \
    apt-get update && \
    apt-get install -y gz-harmonic ros-humble-ros-gzharmonic ros-humble-mavros ros-humble-mavros-extras

RUN wget https://raw.githubusercontent.com/mavlink/mavros/master/mavros/scripts/install_geographiclib_datasets.sh && \
    chmod +x install_geographiclib_datasets.sh && \
    ./install_geographiclib_datasets.sh

WORKDIR /root/ardu_ws/src
RUN vcs import --input https://raw.githubusercontent.com/droneswarmufpe/ardupilot_gz/iris-depth-cbr/ros2_gz.repos --recursive 

ENV GZ_VERSION=harmonic

RUN wget https://packages.osrfoundation.org/gazebo.gpg -O /usr/share/keyrings/pkgs-osrf-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg] http://packages.osrfoundation.org/gazebo/ubuntu-stable $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/gazebo-stable.list > /dev/null && \
    apt-get update

RUN wget https://raw.githubusercontent.com/osrf/osrf-rosdep/master/gz/00-gazebo.list -O /etc/ros/rosdep/sources.list.d/00-gazebo.list && \
    rosdep update

WORKDIR /root/ardu_ws
RUN . /opt/ros/humble/setup.bash && \
    apt-get update && \
    rosdep update && \
    rosdep install --from-paths src --ignore-src -y

RUN . /opt/ros/humble/setup.bash && \
    colcon build --packages-up-to ardupilot_gz_bringup && \
    . ./install/setup.bash

RUN mkdir -p /tmp/runtime-root && chmod 700 /tmp/runtime-root
ENV XDG_RUNTIME_DIR=/tmp/runtime-root

CMD ["bash"]