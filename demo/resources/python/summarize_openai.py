from openai import OpenAI
import os

# Inicializa el cliente usando la API Key desde la variable de entorno
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def resumir_archivo_txt(ruta_archivo):
    # 1. Leer el contenido del archivo
    with open(ruta_archivo, "r", encoding="utf-8") as archivo:
        texto = archivo.read()

    # 2. Crear la petición a la API para resumir
    response = client.responses.create(
        model="gpt-4.1-mini",
        input=f"""
        Resume el siguiente documento de forma clara, estructurada
        y con lenguaje académico:

        {texto}
        """
    )

    # 3. Extraer el resumen generado
    resumen = response.output_text
    return resumen


# ---------- EJECUCIÓN ----------
if __name__ == "__main__":
    ruta = "documento.txt"  # archivo a resumir
    resumen = resumir_archivo_txt(ruta)

    print("===== RESUMEN =====\n")
    print(resumen)
