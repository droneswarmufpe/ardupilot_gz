# Clone repo

```
git clone git@github.com:droneswarmufpe/ardupilot_gz.git
```

## Build docker images

### GPU
```
docker build -f ardupilot-sitl-gazebo-gpu.Dockerfile -t ardupilot-sitl-gazebo:gpu .
```
### CPU
```
docker build -f ardupilot-sitl-gazebo.Dockerfile -t ardupilot-sitl-gazebo .
```

## Run docker container

### GPU
```
docker compose -f 'docker-compose.dev.yaml' up -d --build 'sim-gpu'
```

### CPU
```
docker compose -f 'docker-compose.dev.yaml' up -d --build 'sim'
```

Warning:
> Sistemas mais recentes (especialmente Ubuntu 22+) podem exigir o compartilhamento do seu arquivo `Xauthority` para que a interface gráfica do Gazebo seja renderizada corretamente. O arquivo `docker-compose.dev.yaml` já está configurado para isso.
> 
> 
> Se encontrar erros relacionados a `QT_X11_NO_MITSHM=1`, você pode tentar comentar essa variável de ambiente no `docker-compose.dev.yaml` para o serviço que estiver usando (`sim` ou `sim-gpu`).
>

## Running simulation

### Enter the docker container
```
docker exec -it pds-sim-gpu bash
```

### Terminal 1: Run gazebo with ardupilot
```
ros2 launch ardupilot_gz_bringup iris_depth_baylands.launch.py
```

### Terminal 2: Run maxproxy
```
mavproxy.py --master tcp:127.0.0.1:5760 --out udp:127.0.0.1:14550 --out udp:127.0.0.1:14562 --out udp:127.0.0.1:14552
```

### Terminal 3: Visualize data in Rviz2 (optional)
```
ros2 run tf2_ros static_transform_publisher 0 0 0 0 1.5708 0 base_link iris_depth/camera_link/StereoOV7251
```

# Changing parameters

If you make any changes to the repo, ROS2 needs to be built again.

Do this by running:
```
cd /root/ardu_ws/ &&
colcon build --packages-up-to ardupilot_gz_bringup
```

