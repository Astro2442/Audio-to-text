# se recortara el audio dado en fragmentos cuya duracion maxima sera de 10 minutos
# cada fragmento se guardara en un archivo separado
# y cada corte se realizara en silencio para evitar cortes bruscos
import sys
# Asegurarse de que 'audioop' esté disponible (es una extensión en C que algunas builds no incluyen).
# Intentamos usar 'pyaudioop' como fallback y lo inyectamos en sys.modules si está disponible.
try:
    import audioop  # type: ignore
except ModuleNotFoundError:
    try:
        import pyaudioop as audioop  # type: ignore
        sys.modules['audioop'] = audioop
    except ModuleNotFoundError:
        raise ModuleNotFoundError(
            "El módulo 'audioop' no está disponible en esta build de Python y 'pyaudioop' no está instalado (no está disponible para este intérprete). "
            "Opciones:\n"
            "  1) Instalar una build de Python que incluya 'audioop' (recomendada): descarga e instala Python desde https://www.python.org/downloads/ o usa 'pyenv install 3.13.0'.\n"
            "  2) Crear un virtualenv con una versión de Python que incluya 'audioop'.\n"
            "  3) Si 'pyaudioop' estuviera disponible, se podría instalar con: python3 -m pip install pyaudioop\n"
            "Si quieres, puedo ayudarte a crear un venv o reinstalar Python para resolverlo."
        )

from pydub import AudioSegment
from pydub.silence import split_on_silence
import os

def cortar_audio_en_fragmentos(audio_path, duracion_maxima_ms=10*60*1000, silencio_minimo_ms=500, umbral_silencio_dBFS=-40):
    # Cargar el archivo de audio
    audio = AudioSegment.from_file(audio_path)
    
    # Dividir el audio en fragmentos basados en silencio
    fragmentos = split_on_silence(
        audio,
        min_silence_len=silencio_minimo_ms,
        silence_thresh=umbral_silencio_dBFS,
        keep_silence=200  # Mantener un poco de silencio al inicio y final de cada fragmento
    )
    
    # Crear un directorio en la carpeta del audio para guardar los fragmentos si no existe
    directorio_fragmentos = os.path.join(os.path.dirname(audio_path), "fragmentos_audio")
    os.makedirs(directorio_fragmentos, exist_ok=True)
    
    fragmentos_guardados = []
    fragmento_actual = AudioSegment.empty()
    contador_fragmentos = 0
    
    for fragmento in fragmentos:
        if len(fragmento_actual) + len(fragmento) <= duracion_maxima_ms:
            fragmento_actual += fragmento
        else:
            # Guardar el fragmento actual
            nombre_fragmento = os.path.join(directorio_fragmentos, f"fragmento_{contador_fragmentos}.wav")
            fragmento_actual.export(nombre_fragmento, format="wav")
            fragmentos_guardados.append(nombre_fragmento)
            contador_fragmentos += 1
            
            # Empezar un nuevo fragmento con el fragmento actual
            fragmento_actual = fragmento
    
    # Guardar el último fragmento si tiene contenido
    if len(fragmento_actual) > 0:
        nombre_fragmento = os.path.join(directorio_fragmentos, f"fragmento_{contador_fragmentos}.wav")
        fragmento_actual.export(nombre_fragmento, format="wav")
        fragmentos_guardados.append(nombre_fragmento)
    
    return fragmentos_guardados