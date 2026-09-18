CHILALA VS JEYSON - PAQUETE ANDROID

Este proyecto prepara el juego Pygame para Android.

Incluye:
- 10 niveles de dificultad
- Chilala vs Jeyson
- Audio y soundtrack
- Controles táctiles en pantalla
- Orientación horizontal
- Guardado del progreso en almacenamiento privado de la app

OPCIÓN A: COMPILAR EN LINUX / WSL2
Buildozer crea el APK de depuración automáticamente. La primera compilación
puede descargar el Android SDK, NDK y demás herramientas.

1) Instala Python 3.12, Git y las dependencias del sistema.
2) En la carpeta del proyecto:
   python3 -m venv .venv
   source .venv/bin/activate
   pip install buildozer setuptools cython==0.29.34
3) Compila:
   buildozer -v android debug
4) El APK aparecerá en bin/.

OPCIÓN B: GITHUB ACTIONS
Sube este proyecto a un repositorio de GitHub. El archivo
.github/workflows/build-apk.yml compila el APK en un runner de Ubuntu y lo
publica como artefacto descargable del workflow.

NOTA
La receta de pygame-ce va incluida en p4a-recipes/ porque el soporte Android
de pygame-ce puede requerir una receta específica de python-for-android.

El APK final debe compilarse con una máquina que disponga del SDK/NDK de
Android o con un runner CI. Este entorno de ChatGPT no trae ese toolchain.
