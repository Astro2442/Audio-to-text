package com.example;

import java.net.HttpURLConnection;
import java.net.URI;
import java.net.URL;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.io.*;
import java.util.*;
import java.util.stream.Collectors;

import javax.swing.Renderer;

import com.google.gson.*;
import org.apache.commons.lang3.StringUtils;
import org.apache.poi.xwpf.usermodel.*;
import org.apache.xmlbeans.XmlCursor;

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;

/**
 * Hello world!
 *
 */
public class App {
    // creamos todas la variables comunes
    private static final String TEMPLATE_PATH = "resources/template.docx";
    private static final String FORMAT = "yyyy-MM-dd";
    private static final String COMBERSACION_PATH = "conversacion.txt";
    private static final String OUTPUT_FILE = "output/";
    private static final String INPUT_FILE = "input/";
    private static final String SCRIPT_PY_PATH = "resources/python/config_python.py";
    private static final Gson gson = new GsonBuilder().setPrettyPrinting().create();
    private static final String API_URL = "https://api.deepai.org/api/summarization";
    private static final String API_KEY = "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";
    private String inputPath = "input/";
    private String titulo;
    private String fecha = new Date().toString();
    private String maestro;
    private String materia;
    private String combersacion;
    private String resumen;
    private HttpClient client = HttpClient.newHttpClient();

    public static boolean esWindows() {
        return System.getProperty("os.name").toLowerCase().contains("win");
    }

    public String python = esWindows() ? "python" : "python3"; // detectar si es windows o linux/macOS

    // metodo para agregar el encabesado al documento (usa Apache POI XWPF para
    // .docx)
    private XWPFDocument crearDocument(String titulo, String maestro, String materia) throws FileNotFoundException, IOException {
        this.titulo = titulo;
        this.maestro = maestro;
        this.materia = materia;

        Map<String, String> placeholders = new LinkedHashMap<>();
        placeholders.put("{{TITULO}}", titulo != null ? titulo : "");
        placeholders.put("{{FECHA}}", this.fecha != null ? this.fecha : "");
        placeholders.put("{{MATERIA}}", materia != null ? materia : "");
        placeholders.put("{{MAESTRO}}", maestro != null ? maestro : "");
        placeholders.put("{{CONVERSACIONES}}", this.combersacion != null ? this.combersacion : "");
        placeholders.put("{{RESUMEN}}", this.resumen != null ? this.resumen : "");
        try (FileInputStream fis = new FileInputStream(TEMPLATE_PATH)) {
            XWPFDocument doc = new XWPFDocument(fis);

            // -------- PÁRRAFOS --------
            for (int i = 0; i < doc.getParagraphs().size(); i++) {
                XWPFParagraph p = doc.getParagraphs().get(i);
                String text = p.getText();

                if (text == null)
                    continue;

                for (Map.Entry<String, String> e : placeholders.entrySet()) {
                    if (!text.contains(e.getKey()))
                        continue;

                    // ----- CASO MULTILÍNEA -----
                    if (e.getKey().equals("{{CONVERSACIONES}}") || e.getKey().equals("{{RESUMEN}}")) {

                        int pos = doc.getPosOfParagraph(p);

                        // eliminar párrafo placeholder
                        doc.removeBodyElement(pos);
                        i--; // 🔥 IMPORTANTE: ajustar índice

                        String[] bloques = e.getValue().split("\\n\\n");

                        for (String bloque : bloques) {
                            XWPFParagraph ref = doc.getParagraphArray(pos);
                            XmlCursor cursor = ref.getCTP().newCursor();

                            XWPFParagraph nuevo = doc.insertNewParagraph(cursor);
                            XWPFRun run = nuevo.createRun();
                            run.setText(bloque.trim());

                            cursor.dispose();
                            pos++;
                        }

                    } else {
                        // ----- TEXTO SIMPLE -----
                        String nuevoTexto = StringUtils.replace(text, e.getKey(), e.getValue());

                        // eliminar runs de forma SEGURA
                        for (int r = p.getRuns().size() - 1; r >= 0; r--) {
                            p.removeRun(r);
                        }

                        p.createRun().setText(nuevoTexto);
                    }
                    break;
                }
            }

            // -------- TABLAS --------
            for (XWPFTable table : doc.getTables()) {
                for (XWPFTableRow row : table.getRows()) {
                    for (XWPFTableCell cell : row.getTableCells()) {
                        for (XWPFParagraph p : cell.getParagraphs()) {
                            String text = p.getText();
                            if (text == null)
                                continue;

                            for (Map.Entry<String, String> e : placeholders.entrySet()) {
                                if (text.contains(e.getKey())) {

                                    String nuevoTexto = StringUtils.replace(text, e.getKey(), e.getValue());

                                    for (int r = p.getRuns().size() - 1; r >= 0; r--) {
                                        p.removeRun(r);
                                    }

                                    p.createRun().setText(nuevoTexto);
                                    break;
                                }
                            }
                        }
                    }
                }
            }

            return doc;
        }
    }

    // se guarda el documento en la ruta especificada
    public void guardar(XWPFDocument document, Path outputPath) {
        Path carpeta = outputPath;
        Path archivo = carpeta.resolve(titulo + ".docx");
        try (FileOutputStream out = new FileOutputStream(archivo.toFile() + "")) {
            document.write(out);
        } catch (IOException e) {
            throw new RuntimeException(
                    "Error al guardar el documento Word: " + outputPath, e);
        }
    }

    // se genera el mensaje llamando al script de python para convertir UN archivo
    // concreto
    private void generarMensajeParaArchivo(String archivo) {
        System.out.println("Generando mensaje para: " + archivo);
        File script = new File(SCRIPT_PY_PATH);
        if (!script.exists()) {
            System.err.println("Script no encontrado: " + SCRIPT_PY_PATH);
            return;
        }

        ProcessBuilder processBuilder = new ProcessBuilder(python, SCRIPT_PY_PATH, "generar_mensage", archivo);
        processBuilder.redirectErrorStream(true);

        try {
            Process process = processBuilder.start();
            try (BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()))) {
                StringBuilder output = new StringBuilder();
                String line;
                while ((line = reader.readLine()) != null) {

                    output.append(line).append("\n");
                    System.out.println(line);
                }
                int exitCode = process.waitFor();
                if (exitCode == 0) {
                    String mensaje = output.toString().trim();
                    System.out.println("Mensaje generado:\n" + mensaje);
                } else {
                    System.err.println("Error al ejecutar el script. Código de salida: " + exitCode);
                    System.err.println("Salida: " + output.toString());
                }
            }
        } catch (IOException | InterruptedException e) {
            System.err.println("Error al ejecutar el proceso: " + e.getMessage());
            e.printStackTrace();
        }
    }

    // obtiene la duración del audio en segundos usando ffprobe; devuelve -1 si no
    // disponible
    private long getAudioDurationSeconds(String path) {
        try {
            ProcessBuilder pb = new ProcessBuilder("ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                    "default=noprint_wrappers=1:nokey=1", path);
            Process p = pb.start();
            try (BufferedReader reader = new BufferedReader(new InputStreamReader(p.getInputStream()))) {
                String out = reader.readLine();
                p.waitFor();
                if (out != null && !out.isBlank()) {
                    double d = Double.parseDouble(out.trim());
                    return (long) Math.round(d);
                }
            }
        } catch (IOException | InterruptedException | NumberFormatException e) {
            System.err.println("No se pudo determinar duración con ffprobe: " + e.getMessage());
        }
        return -1;
    }

    // recorta el audio y devuelve la lista de segmentos (paths), o null si falla
    private List<String> recortarAudioAndGetSegments() {
        System.out.println("Solicitando recorte de: " + this.inputPath);
        File script = new File(SCRIPT_PY_PATH);
        if (!script.exists()) {
            System.err.println("Script no encontrado: " + SCRIPT_PY_PATH);
            return null;
        }

        ProcessBuilder processBuilder = new ProcessBuilder(python, SCRIPT_PY_PATH, "recortar_audio", this.inputPath);
        processBuilder.redirectErrorStream(true);

        try {
            Process process = processBuilder.start();
            List<String> segments = new ArrayList<>();
            try (BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()))) {
                String line;
                while ((line = reader.readLine()) != null) {
                    System.out.println(line);
                    // asumimos que cada línea con ruta es un segmento
                    if (line.trim().length() > 0 && (line.trim().startsWith("input/") || line.trim().startsWith("/"))) {
                        segments.add(line.trim());
                        
                    }
                }
                int exitCode = process.waitFor();
                if (exitCode != 0) {
                    System.err.println("Recorte falló con código: " + exitCode);
                    return null;
                }
            }
            return segments;
        } catch (IOException | InterruptedException e) {
            System.err.println("Error al ejecutar recorte: " + e.getMessage());
            e.printStackTrace();
            return null;
        }
    }

    // procesa el audio: si dura > 20 minutos lo recorta y convierte cada segmento a
    // texto
    private void procesarAudio() {
        if (this.inputPath == null) {
            System.err.println("No hay inputPath identificado.");
            return;
        }
        long duration = getAudioDurationSeconds(this.inputPath);
        if (duration == -1) {
            System.out.println("Duración desconocida; procederé a convertir el archivo directamente.");
            generarMensajeParaArchivo(this.inputPath);
            return;
        }

        System.out.println("Duración del audio (s): " + duration);
        long limit = 20 * 60; // 20 minutos en segundos
        if (duration > limit) {
            System.out.println("Audio mayor a 20 minutos; recortando...");
            List<String> segments = recortarAudioAndGetSegments();
            if (segments == null || segments.isEmpty()) {
                System.err.println("No se obtuvieron segmentos; abortando conversión.");
                return;
            }
            for (String seg : segments) {
                System.out.println("Convirtiendo segmento: " + seg);
                generarMensajeParaArchivo(seg);
            }
        } else {
            System.out.println("Audio menor a 20 minutos; convirtiendo directamente.");
            generarMensajeParaArchivo(this.inputPath);
        }
    }

    // se lee la combersacion desde el archovo que genero el script de python
    private String leerCombersacionDesdeArchivo(String path) {
        // leer la combersacion desde un archivo de texto
        File f = new File(path);
        if (!f.exists()) {
            System.err.println("Archivo de conversación no encontrado: " + path);
            return "";
        }
        StringBuilder sb = new StringBuilder();
        try (BufferedReader br = new BufferedReader(new FileReader(f))) {
            String line;
            while ((line = br.readLine()) != null) {
                sb.append(line).append("\n");

            }
        } catch (IOException e) {
            e.printStackTrace();
        }
        this.combersacion = sb.toString();
        return sb.toString();
    }

    private String identificarInputPath() {
        // identificar el input path
        File inputDir = new File(INPUT_FILE);
        if (inputDir.exists() && inputDir.isDirectory()) {
            File[] files = inputDir.listFiles((dir, name) -> name.toLowerCase().endsWith(".mp3")
                    || name.toLowerCase().endsWith(".m4a") || name.toLowerCase().endsWith(".wav"));
            if (files != null && files.length > 0) {
                this.inputPath = INPUT_FILE + files[0].getName();
                System.out.println("Input path identificado: " + this.inputPath);
            } else {
                System.err.println("No se encontraron archivos de audio en el directorio de entrada.");
            }
        } else {
            System.err.println("Directorio de entrada no encontrado: " + INPUT_FILE);
        }
        // retornamos la ruta de el archivo de audio encontrado
        return this.inputPath;
    }

    private static boolean ollamaInstalado() {
        try {
            Process p = new ProcessBuilder("ollama", "--version")
                    .redirectErrorStream(true)
                    .start();
            p.waitFor();
            return p.exitValue() == 0;
        } catch (Exception e) {
            return false;
        }
    }

    private static void instalarOllamaMac() throws Exception {
        new ProcessBuilder(
                "bash",
                "-c",
                "brew install ollama").inheritIO().start().waitFor();
    }

    private static void iniciarOllama() throws Exception {
        new ProcessBuilder("ollama", "serve")
                .inheritIO()
                .start();
    }

    private static void asegurarModelo() throws Exception {
        new ProcessBuilder("ollama", "pull", "mistral")
                .inheritIO()
                .start()
                .waitFor();
    }

    private void crearResumenEnLocal() {
        String combersacion = leerCombersacionDesdeArchivo(COMBERSACION_PATH);
        if (!ollamaInstalado()) {
            System.out.println("Ollama no está instalado. Iniciando instalación...");
            try {
                instalarOllamaMac();
                System.out.println("Ollama instalado correctamente.");
            } catch (Exception e) {
                System.err.println("Error al instalar Ollama: " + e.getMessage());
                return;
            }
        }
        try {
            iniciarOllama();
            asegurarModelo();
        } catch (Exception e) {
            System.err.println("Error al iniciar Ollama o asegurar el modelo: " + e.getMessage());
            return;
        }

        JsonObject root = new JsonObject();
        root.addProperty("model", "mistral");
        root.addProperty("prompt",
                "Eres un asistente que resume conversaciones de clases. " +
                        "Resumes de forma clara y concisa, destacando puntos clave, " +
                        "temas tratados, tareas asignadas e información importante. " +
                        "el resumen tiene que estar en español, " +
                        "este es el texto a resumir: \n" + combersacion);
        root.addProperty("stream", false);

        String requestBody = root.toString();
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create("http://localhost:11434/api/generate"))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(requestBody))
                .build();
        try {
            HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
            if (response.statusCode() == 200) {
                JsonObject json = JsonParser
                        .parseString(response.body())
                        .getAsJsonObject();

                String resumen = json.get("response").getAsString();
                this.resumen = resumen;
                System.out.println("Resumen generado:\n" + resumen);
            } else {
                System.err.println("Error al generar resumen. Código: " + response.statusCode());
                System.err.println("Respuesta: " + response.body());
            }
        } catch (IOException | InterruptedException e) {
            System.err.println("Error al enviar solicitud a Ollama: " + e.getMessage());
            e.printStackTrace();
        }
    }

    public String convertirATextoEntendible(Path archivoEntrada) {

        try {
            // 1. Leer archivo original
            String textoOriginal = Files.lines(archivoEntrada)
                    .map(linea -> linea.replaceAll("\\[.*?\\]", "").trim())
                    .collect(Collectors.joining(" "));

            // 2. Crear prompt
            String prompt = """
                    El siguiente texto es una transcripción cruda de una conversación de una clase.
                    Contiene errores, frases incompletas y marcas de tiempo.

                    Tu tarea es:
                    - Reescribir el contenido como un texto claro y coherente
                    - Mantener TODAS las ideas originales
                    - No resumir
                    - Estructurar el texto como si fuera un documento para repasar lo hablado en clase
                    - Usar un lenguaje natural, explicativo y entendible
                    - El resultado deve de estar en español

                    Texto original:
                    """ + textoOriginal;

            // 3. Preparar petición HTTP a Ollama
            URL url = new URL("http://localhost:11434/api/generate");
            HttpURLConnection conn = (HttpURLConnection) url.openConnection();
            conn.setRequestMethod("POST");
            conn.setRequestProperty("Content-Type", "application/json");
            conn.setDoOutput(true);

            String body = """
                    {
                      "model": "mistral",
                      "prompt": %s,
                      "stream": false
                    }
                    """.formatted(escapeJson(prompt));

            // 4. Enviar request
            try (OutputStream os = conn.getOutputStream()) {
                os.write(body.getBytes());
            }

            // 5. Leer respuesta
            try (BufferedReader br = new BufferedReader(
                    new InputStreamReader(conn.getInputStream()))) {

                String response = br.lines().collect(Collectors.joining());
                return extraerRespuesta(response);
            }

        } catch (Exception e) {
            throw new RuntimeException("Error al procesar el texto con IA", e);
        }
    }

    // ---- helpers ----

    private static String escapeJson(String texto) {
        return "\"" + texto
                .replace("\\", "\\\\")
                .replace("\"", "\\\"")
                .replace("\n", "\\n") + "\"";
    }

    private static String extraerRespuesta(String json) {
        int index = json.indexOf("\"response\":\"");
        if (index == -1)
            return "";
        int start = index + 12;
        int end = json.indexOf("\"", start);
        return json.substring(start, end).replace("\\n", "\n");
    }

    private static String comversacionajustada(Path archivoEntrada) throws IOException {
        String areglado;
        String textoOriginal = Files.lines(archivoEntrada)
                .map(linea -> linea.replaceAll("\\[.*?\\]", "").trim())
                .collect(Collectors.joining(" "))
                .replaceAll("\\.\\s*", ".\n");
        areglado = textoOriginal;
        return areglado;
    }

    public String formatearTextoParaDocumento(String textoIA) {

        // 1. Normalizar espacios
        String texto = textoIA
                .replaceAll("\\s+", " ")
                .trim();

        // 2. Separar listas con saltos de línea
        texto = texto.replaceAll("\\s-\\s", "\n- ");

        // 3. Crear saltos de párrafo después de oraciones largas
        texto = texto.replaceAll("\\.\\s+", ".\n\n");

        // 4. Evitar demasiados saltos seguidos
        texto = texto.replaceAll("\\n{3,}", "\n\n");

        return texto.trim();
    }

    public static void main(String[] args) throws FileNotFoundException, IOException {
        App app = new App();

        System.out.println("inicio de programa");
        Scanner imput = new Scanner(System.in);
        System.out.println("que materia?:");
        String materia = imput.nextLine();
        System.out.println("que maestro?:");
        String maestro = imput.nextLine();

        System.out.println("dame el titulo de la clase:");
        String titulo = imput.nextLine();
        imput.close();
        
         app.identificarInputPath();
         app.procesarAudio();
         
        app.crearResumenEnLocal();

        try {
            app.combersacion = app.convertirATextoEntendible(Paths.get(COMBERSACION_PATH)) + "\n" +
                    "comversacion: \n" +
                    comversacionajustada(Paths.get(COMBERSACION_PATH));
        } catch (IOException e) {
            System.err.println("Error al procesar la conversación: " + e.getMessage());
            e.printStackTrace();
        }
        app.combersacion = app.formatearTextoParaDocumento(app.combersacion);
        app.resumen = app.formatearTextoParaDocumento(app.resumen);
        app.guardar(app.crearDocument(titulo, maestro, materia), Path.of(OUTPUT_FILE));

    }

}
