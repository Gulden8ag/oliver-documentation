# Instalación de ROS 2 Jazzy Jalisco (WSL2 + WSLg)

## ¿Qué es ROS?

Aunque se llame “sistema operativo”, en realidad es un conjunto de herramientas y librerías que te ayudan a conectar y coordinar los distintos bloques de tu robot.

Define cómo intercambian información las partes (por ejemplo, tu módulo de visión envía “veo un obstáculo” y tu módulo de movimiento recibe ese mensaje y frena).

Cuenta con cientos de paquetes que ya resuelven tareas comunes (planificar rutas, procesar imágenes, simular en ordenador…), de modo que no tienes que escribir todo desde cero.

Al dia de actualizacion de esta pagina 21 de mayo de 2025 Jazzy Jalisco es la distribucion mas moderna estable sacada en mayo 23, 2024 con soporte hasta Mayo 2029. Revisar la [documentacion de ROS](https://docs.ros.org/en/rolling/Releases.html "ROS2 Distributions") Para mas informacion.

ROS es nativo a Linux, el cual deberia ser usado en proceso de alto rendimiento. Sin embargo para experimentacion o si no se quiere sacar una particion de Linux WSL2 es una mejora del Subsistema de Windows para Linux (WSL), que permite ejecutar distribuciones Linux nativas en Windows sin necesidad de máquinas virtuales tradicionales.

## 1. Instalar WSL2 y Ubuntu 24.04  
- **Si ya estás en Ubuntu nativo:**  Omite este **Paso 1** completo (instalación de WSL2 y Ubuntu)
- **Si estás en Windows 11:**  Sigue todos los pasos. 

WSL2 (Windows Subsystem for Linux 2) es una mejora del Subsistema de Windows para Linux (WSL), que permite ejecutar distribuciones Linux nativas en Windows sin necesidad de máquinas virtuales tradicionales.

Abre **powershell** como administrador 
```powershell
wsl --install -d Ubuntu-24.04
```
Este comando:

- Habilita el Subsistema de Windows para Linux (WSL) y la plataforma de maquina virtual
- Configura WSL2 comola version default
- Descarga e instala Ubuntu 24.04 LTS (Noble Numbat es el distro estable actual)

## 2.  Primer arranque y actualización del sistema

Si estas en windows inicia Ubuntu (Desdes inicio) y crea un usuario/contrasena de UNIX(La contrasena no mostrara caracteres cuando escribes), posteriormente en el shell corre los siguientes comandos:

```bash
sudo apt update
sudo apt full-upgrade -y
```
Esto actualizara to Ubuntu

## 3. Configuración del sistema para ROS 2

Antes de instalar ROS, debemos configurar nuestro sistema para hacerlo compatible.

### 3.1 Configurar el locale (codificación de texto)

Primero debemos configurar el locale que se refiere a los ajutes de un sistema para un idioma, ROS utiliza **UTF-8**.  Evitando problemas con caracteres especiales en ROS y otros programas.

```bash
sudo apt update && sudo apt install locales
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8
```
Estos settings utilizan ingles estados unidos, sin embargo cualquier esta bien UTF-8 sirve.

```bash
locale # Verificamos que sea UTF-8
```

### 3.2 Habilitar “universe” y añadir el repositorio de ROS 2

Primero debemos asegurar que el repositorio de [Ubuntu Universe](https://docs.ros.org/en/rolling/Releases.html "Ubuntu Repositories") este habilitado. 

```bash
sudo apt install -y software-properties-common
sudo add-apt-repository universe
```

Ahora agreguemos la clave [GPG](https://es.wikipedia.org/wiki/GNU_Privacy_Guard "GNU Privacy Guard (GnuPG o GPG)") ROS 2 con [apt](https://es.wikipedia.org/wiki/GNU_Privacy_Guard "Advanced Packaging Tool").

```bash
sudo apt update
sudo apt install -y curl
curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
  | sudo tee /usr/share/keyrings/ros-archive-keyring.gpg
```

Finalmente agregemos el repositorio a tu lista de sources para instalar.

```bash
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] \
  http://packages.ros.org/ros2/ubuntu \
  $(. /etc/os-release && echo $UBUNTU_CODENAME) main" \
  | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null
```

## 4. Instalar ROS 2 Jazzy Desktop

Primero actualiza tu repositorio de apt para tomar en cuenta los cambios que hicimos.
```bash
sudo apt update
sudo apt upgrade
```

Realizamos la instalacion completa

```bash
sudo apt install ros-jazzy-desktop
```

## 5. Verifica instalacion con un ejemplo

Para esta prueba necesitaras dos terminales porque lo que abre una segunda terminal.

En una terminal vamos a correr un codigo sencillo en C++ llamado talker:

```bash
source /opt/ros/jazzy/setup.bash
ros2 run demo_nodes_cpp talker
```

En otra terminal vamos correr un codigo en python llamado Listener:

```bash
source /opt/ros/jazzy/setup.bash
ros2 run demo_nodes_py listener
```

Deberias ver que talker imprime en consola, **Publishing: numbers** y en la consola on listener se imprime **I heard: numbers** coincidiendo el mensaje. Verificando que los APIs de C++ y python funcionan.

Felicidades has isntalado ROS.