#!/bin/bash
# Script para ejecutar la aplicación JavaFX

cd "$(dirname "$0")"

# Compilar primero
mvn clean compile

# Obtener el path de JavaFX
JAVAFX_PATH="/Users/astro/.m2/repository/org/openjfx"
JAVAFX_MODULES="$JAVAFX_PATH/javafx-graphics/21/javafx-graphics-21-mac-aarch64.jar:$JAVAFX_PATH/javafx-controls/21/javafx-controls-21-mac-aarch64.jar:$JAVAFX_PATH/javafx-fxml/21/javafx-fxml-21-mac-aarch64.jar:$JAVAFX_PATH/javafx-base/21/javafx-base-21-mac-aarch64.jar"

# Ejecutar la aplicación
java --module-path "$JAVAFX_MODULES" --add-modules javafx.controls,javafx.fxml -cp "target/classes:$(mvn dependency:build-classpath -q -Dmdep.outputFile=/dev/stdout)" com.example.App
