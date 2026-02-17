# convertiremos el audio a texto sin identificar los speakers usando OpenAI Whisper
import whisper
import torch
import gc
import os
from typing import Optional

# Modelos ordenados por calidad (mayor a menor) y una estimación conservadora de VRAM/recursos en GB
_MODEL_CANDIDATES = [
    ("large-v2", 16),
    ("large", 12),
    ("medium", 6),
    ("small", 2),
    ("base", 1),
    ("tiny", 0.5),
]

CACHE_DIR = os.path.expanduser("~/.cache/whisper")
print("inicio de comvercion")

def _get_total_memory_gb():
    # Intentar psutil si está disponible, si no usar sysconf (Unix)
    try:
        import psutil
        return psutil.virtual_memory().total / (1024 ** 3)
    except Exception:
        try:
            if hasattr(os, "sysconf"):
                pages = os.sysconf("SC_PHYS_PAGES")
                page_size = os.sysconf("SC_PAGE_SIZE")
                return (pages * page_size) / (1024 ** 3)
        except Exception:
            return None


def _get_cuda_mem_gb():
    if not torch.cuda.is_available():
        return 0
    try:
        prop = torch.cuda.get_device_properties(0)
        return prop.total_memory / (1024 ** 3)
    except Exception:
        return 0


def _choose_model_for_device(device: str):
    """Elige el modelo más grande que parezca caber en el dispositivo.
    Devuelve (model_name, reason)
    """
    cuda_mem = _get_cuda_mem_gb()
    total_mem = _get_total_memory_gb() or 0

    # Si CUDA disponible, priorizar VRAM
    if device == "cuda" and cuda_mem > 0:
        for name, req in _MODEL_CANDIDATES:
            if cuda_mem >= req:
                return name, f"cuda ({cuda_mem:.1f}GB) >= required {req}GB"
        # si ninguno cabe, volver al más pequeño
        return _MODEL_CANDIDATES[-1][0], f"cuda pero insuficiente VRAM ({cuda_mem:.1f}GB); usar tiny"

    # Para mps y CPU usar memoria total como heurística
    if device == "mps":
        for name, req in _MODEL_CANDIDATES:
            # asumimos que MPS tiene acceso a memoria total del sistema; ser conservadores
            if total_mem >= req * 1.0:
                return name, f"mps (RAM {total_mem:.1f}GB) >= required {req}GB"
        return _MODEL_CANDIDATES[-1][0], f"mps pero poca RAM ({total_mem:.1f}GB); usar tiny"

    # CPU: elegir según RAM y número de cores
    if device == "cpu":
        if total_mem is None:
            # no sabemos, elegir medium por defecto
            return "medium", "RAM desconocida; elegir medium por defecto"
        if total_mem >= 16:
            return "medium", f"CPU con RAM {total_mem:.1f}GB -> medium"
        if total_mem >= 8:
            return "small", f"CPU con RAM {total_mem:.1f}GB -> small"
        if total_mem >= 4:
            return "base", f"CPU con RAM {total_mem:.1f}GB -> base"
        return "tiny", f"CPU con RAM {total_mem:.1f}GB -> tiny"

    # fallback
    return "small", "fallback small"


def _delete_corrupt_cache(model_name: str):
    # intenta borrar el archivo de cache típico
    candidate = os.path.join(CACHE_DIR, f"{model_name}.pt")
    if os.path.exists(candidate):
        try:
            os.remove(candidate)
            print(f"Borrado cache corrupto: {candidate}")
            return True
        except Exception as e:
            print("No se pudo borrar cache corrupto:", e)
            return False
    return False


def _load_model_with_fallbacks(preferred_model: Optional[str], device: str):
    """Intentar cargar modelos empezando por preferred_model y cayendo a modelos más pequeños si hay OOM o errores.
    Retorna (model, model_name)
    """
    # Construir lista de candidatos empezando por preferred_model si está
    candidates = [m for m, _ in _MODEL_CANDIDATES]
    if preferred_model and preferred_model in candidates:
        # reorder
        candidates.remove(preferred_model)
        candidates.insert(0, preferred_model)

    last_exc = None
    for model_name in candidates:
        try:
            print(f"Intentando cargar modelo: {model_name} en dispositivo {device}")
            model = whisper.load_model(model_name, device=device)
            # si estamos en CUDA, intentar usar half para ahorrar memoria
            if device == "cuda":
                try:
                    model.half()
                    print("Modelo convertido a half (fp16) para ahorrar memoria en CUDA")
                except Exception:
                    pass
            return model, model_name
        except Exception as e:
            msg = str(e).lower()
            print(f"Error cargando modelo {model_name}: {e}")
            last_exc = e
            # caso checksum/corrupto: intentar borrar cache y reintentar una vez
            if "checksum" in msg or "sha256" in msg or "downloaded but the sha256" in msg:
                deleted = _delete_corrupt_cache(model_name)
                if deleted:
                    try:
                        print(f"Reintentando descarga para {model_name} tras borrar cache...")
                        model = whisper.load_model(model_name, device=device)
                        if device == "cuda":
                            try:
                                model.half()
                            except Exception:
                                pass
                        return model, model_name
                    except Exception as e2:
                        print(f"Reintento fallido para {model_name}: {e2}")
                        last_exc = e2
                        continue
            # caso OOM: intentar siguiente modelo más pequeño
            if "cuda out of memory" in msg or "out of memory" in msg or "oom" in msg:
                print(f"OOM al cargar {model_name}; intentando modelo más pequeño...")
                # limpiar caches y continuar
                try:
                    gc.collect()
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                except Exception:
                    pass
                continue
            # caso otro tipo de error: registrar y probar siguiente
            continue
    # si ninguno funcionó, relanzar último error
    raise last_exc if last_exc is not None else RuntimeError("No se pudo cargar ningún modelo")


def convertir_audio_sin_identificar(audio_path: str, device: Optional[str] = None, model_name: Optional[str] = None, language: str = "es"):
    try:
        # Detectar device si no se especifica
        if device is None:
            if torch.cuda.is_available():
                device = "cuda"
            else:
                device = "cpu"
           

        # Elegir modelo según recursos
        chosen_model = model_name
        reason = ""
        if not chosen_model:
            chosen_model, reason = _choose_model_for_device(device)
        print(f"Device: {device} | Modelo elegido: {chosen_model} ({reason})")

        # Intentar cargar el modelo con fallback
        model, used_model = _load_model_with_fallbacks(chosen_model, device)
        print(f"Modelo cargado: {used_model}")

        # Transcribir; el método acepta directamente la ruta del archivo
        result = model.transcribe(audio_path, language=language)
        return result

    except Exception as e:
        print("Error durante la conversión de audio a texto:", str(e))
        return None

    finally:
        # Limpieza de memoria
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        if 'model' in locals():
            try:
                del model
            except Exception:
                pass


def ejecutar_conversion(audio_path: str):
    resultado = convertir_audio_sin_identificar(audio_path)
    if (not resultado) and (resultado == ""):
        print("No se obtuvo resultado de la transcripción.")
        return None

    print("Resultado final:", resultado.get("text", "")[:200])
    output_file = "conversacion.txt"
    # se guardaran los resultados en un archivo de texto
    # sin sobre escribir los que ya existan
    with open(output_file, "a", encoding="utf-8") as f:
        segments = resultado.get("segments", [])
        for segment in segments:
            start = segment.get("start", 0.0)
            end = segment.get("end", 0.0)
            text = segment.get("text", "").strip()
            f.write(f"[{start:.2f} - {end:.2f}] {text}\n")
    return resultado
