---

CONVERTIDOR DE AUDIO A TEXTO CON GENERACIÓN DE RESÚMENES Y DOCUMENTOS WORD

Aplicación de escritorio desarrollada en Java + JavaFX que permite convertir archivos de audio en texto, mejorar automáticamente la transcripción mediante IA local y generar documentos Word profesionales con resumen incluido.

---

DESCRIPCIÓN GENERAL

Este sistema automatiza el flujo completo:

Audio → Transcripción → Mejora con IA → Resumen → Documento Word (.docx)

Permite:

* Convertir archivos MP3, M4A y WAV a texto
* Dividir automáticamente audios largos en segmentos
* Mejorar coherencia del texto usando IA local (Ollama + Mistral)
* Generar resúmenes ejecutivos automáticos
* Crear documentos Word formateados usando una plantilla
* Procesar todo de manera local (sin enviar datos a la nube)

---

TECNOLOGÍAS UTILIZADAS

* Java 17
* JavaFX 21
* Maven
* Apache POI (manipulación de .docx)
* Python 3
* FFprobe / FFmpeg
* Ollama + modelo Mistral (IA local)

Arquitectura modular orientada a procesos con integración entre Java y Python.

---

ARQUITECTURA GENERAL

El sistema está dividido en:

1. Capa de presentación
   Interfaz gráfica JavaFX (FXML)

2. Capa de lógica
   Orquestación principal en App.java

3. Capa de procesamiento
   Scripts Python + herramientas del sistema

4. Capa de IA
   Ollama ejecutándose en localhost

5. Capa de persistencia
   Archivos de entrada y salida

---

REQUISITOS

Antes de ejecutar el proyecto necesitas:

* Java 17 o superior
* Maven
* Python 3
* ffmpeg (incluye ffprobe)

Opcional para generación de resúmenes locales:

* Ollama
* Modelo Mistral (ejecutar: ollama pull mistral)

---

CÓMO EJECUTAR

Compilar el proyecto:

mvn clean compile

Ejecutar la aplicación:

mvn javafx:run

---

PRIVACIDAD

El procesamiento de IA se realiza de forma local mediante Ollama.
No se envía información a servicios externos.

---

CASOS DE USO

* Documentación automática de clases
* Generación de actas de reunión
* Transcripción de entrevistas
* Procesamiento de contenido educativo
* Creación de documentos estructurados desde audio

---

MEJORAS FUTURAS

* Procesamiento paralelo de segmentos
* Barra de progreso en la interfaz gráfica
* Soporte multiidioma
* Base de datos para histórico de documentos
* Transcripción en tiempo real

---

ESTADO DEL PROYECTO

Versión: 1.0
Estado: En desarrollo (funcionalidad principal implementada)

---

Autor: Astro

Proyecto académico y experimental enfocado en automatización documental mediante IA local.
