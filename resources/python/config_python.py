import sys
import os
import subprocess
from pathlib import Path
import shutil

# --- Gestión automática del virtualenv ---
# Comportamiento: Si no estamos ejecutando dentro del venv del proyecto (.venv),
# intentamos crear el venv con una versión compatible de Python (p. ej. python3.11),
# instalar dependencias desde `requirements.txt`, y volver a ejecutar este script
# con el intérprete del venv.

PROJECT_ROOT = Path(__file__).resolve().parents[2]  # repo root
VENV_PATH = PROJECT_ROOT / ".venv"
REQUIREMENTS_FILE = PROJECT_ROOT / "requirements.txt"
PYTHON_CANDIDATES = ["python3.11", "python3.10", "python3", "/usr/bin/python3"]

# BANDERA DE PROTECCIÓN: Si estamos dentro del venv re-ejecutado, esta variable está definida
def is_running_in_project_venv(venv_path: Path):
    # Primero: verificar si la bandera de seguridad está establecida
    if os.environ.get("PROJECT_VENV_ACTIVE") == "1":
        return True
    
    # Segundo: verificar VIRTUAL_ENV (usado por venv activado)
    venv_env = os.environ.get("VIRTUAL_ENV")
    if venv_env:
        try:
            if Path(venv_env).resolve() == venv_path.resolve():
                return True
        except Exception:
            pass

    # Tercero: verificar sys.executable
    try:
        exe = Path(sys.executable).resolve()
        if venv_path.resolve() in exe.parents:
            return True
    except Exception:
        pass

    return False


def find_available_python():
    for p in PYTHON_CANDIDATES:
        path = shutil.which(p)
        if path:
            try:
                # asegurar que es un ejecutable válido
                res = subprocess.run([path, "-V"], capture_output=True, text=True)
                if res.returncode == 0:
                    return path
            except Exception:
                continue
    return None


def create_venv(python_executable: str, venv_path: Path):
    print(f"Creando venv en {venv_path} usando {python_executable}...")
    subprocess.check_call([python_executable, "-m", "venv", str(venv_path)])


def install_requirements(venv_path: Path, requirements_file: Path):
    pip_exe = venv_path / "bin" / "pip"
    if not pip_exe.exists():
        raise RuntimeError("pip no encontrado en el virtualenv recién creado")
    # Actualizar pip y wheel, luego instalar requirements
    subprocess.check_call([str(pip_exe), "install", "--upgrade", "pip", "wheel", "setuptools"])
    if requirements_file.exists():
        subprocess.check_call([str(pip_exe), "install", "-r", str(requirements_file)])
    else:
        print("Advertencia: requirements.txt no encontrado; no se instalaron dependencias.")

print("inicio de config")
# Si no estamos dentro del venv del proyecto, intentar crear/instalar y re-ejecutar
if not is_running_in_project_venv(VENV_PATH):
    print("No se ejecuta en el venv del proyecto (.venv). Verificando/creando...")
    if not VENV_PATH.exists():
        python_exec = find_available_python()
        if python_exec is None:
            print("No se encontró un intérprete Python compatible en el sistema. Instala Python 3.11 o similar.")
            sys.exit(1)
        try:
            create_venv(python_exec, VENV_PATH)
        except subprocess.CalledProcessError as e:
            print("Error creando el virtualenv:", str(e))
            sys.exit(1)
        try:
            install_requirements(VENV_PATH, REQUIREMENTS_FILE)
            (VENV_PATH / ".venv_installed").write_text("installed\n")
        except subprocess.CalledProcessError as e:
            print("Error instalando requirements:", str(e))
            sys.exit(1)
    else:
        # venv existe, asegurarnos de que las dependencias estén instaladas (solo si no se hizo antes)
        init_flag = VENV_PATH / ".venv_installed"
        if not init_flag.exists():
            print("El venv ya existe; instalando requisitos (primera vez)...")
            try:
                install_requirements(VENV_PATH, REQUIREMENTS_FILE)
                init_flag.write_text("installed\n")
            except subprocess.CalledProcessError as e:
                print("Error instalando requirements en venv existente:", str(e))
                sys.exit(1)
        else:
            print("El venv ya está inicializado; saltando instalación de dependencias.")

    # Re-ejecutar este script con el Python del venv (estableciendo PROJECT_VENV_ACTIVE para evitar bucles)
    venv_python = str(VENV_PATH / "bin" / "python")
    if not Path(venv_python).exists():
        print("Error: no se encontró el intérprete del venv en:", venv_python)
        sys.exit(1)
    print(f"Re-ejecutando con: {venv_python}")
    new_env = os.environ.copy()
    new_env["PROJECT_VENV_ACTIVE"] = "1"
    os.execve(venv_python, [venv_python] + sys.argv, new_env)

# Si llegamos aquí, estamos en el venv del proyecto y podemos importar dependencias

import comvertir_sin_indentificar
import cortar_audio

print("input desde java: ", sys.argv[1])
print("input desde java: ", sys.argv[2])

input_type_progres = sys.argv[1]
type_of_input = type(input_type_progres)
print("tipo de input desde java: ", type_of_input)
dato_proporcionado = sys.argv[2]
type_of_java_data = type(dato_proporcionado)
print("tipo de input desde java: ", type_of_java_data)
if not isinstance(input_type_progres, str):
    print("Error: input_type_progres no es una cadena de texto")
    sys.exit(1)


if input_type_progres == "generar_mensage":
    print("Generando mensaje...")
    mensaje_generado = comvertir_sin_indentificar.ejecutar_conversion(dato_proporcionado)
    print("Mensaje generado: ", mensaje_generado)
    sys.stdout.flush()
    sys.exit(0)

if input_type_progres == "recortar_audio":
    print("Recortando audio: ", dato_proporcionado)
    audio_path = dato_proporcionado

    # Intentar recortar basado en actividad de audio (sin silencios largos)
    try:
        fragmentos = cortar_audio.cortar_audio_en_fragmentos(audio_path)
    except Exception as e:
        print("Error al recortar con pydub:", str(e))
        print("Intentando segmentación por tiempo usando ffmpeg como fallback...")

        out_dir = os.path.join("input", "segments")
        os.makedirs(out_dir, exist_ok=True)
        # mantener extensión
        _, ext = os.path.splitext(audio_path)
        out_pattern = os.path.join(out_dir, f"segment_%03d{ext}")
        cmd = ["ffmpeg", "-y", "-i", audio_path, "-f", "segment", "-segment_time", "600", "-c", "copy", out_pattern]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode != 0:
                print(res.stderr)
                sys.exit(1)
        except FileNotFoundError:
            print("ffmpeg no está instalado o no está en PATH")
            sys.exit(1)

        files = sorted([os.path.join(out_dir, f) for f in os.listdir(out_dir) if f.startswith("segment_") and f.endswith(ext)])
        for f in files:
            print(f)
        sys.stdout.flush()
        sys.exit(0)
    else:
        # imprimir los fragmentos procesados por pydub
        for f in fragmentos:
            print(f)
        sys.stdout.flush()
        sys.exit(0)
        

if input_type_progres == "resumir_texto":
    print("Resumiendo texto...")
    import summarize_openai
    resumen_generado = summarize_openai.resumir_archivo_txt(dato_proporcionado)
    print("Resumen generado: ", resumen_generado)
    sys.stdout.flush()
    sys.exit(0)
  

print("No se reconoció el tipo de operación solicitado.")
sys.exit(1)