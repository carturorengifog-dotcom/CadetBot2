import streamlit as st
import requests
import os
import re

# Configuración de la página
st.set_page_config(page_title="CadetBot2 - Copiloto Autónomo", page_icon="🤖", layout="wide")
st.title("🤖 CadetBot2: Panel Autónomo del Bot")

# Variables de entorno
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_REPO = os.environ.get("GITHUB_REPO")
GITHUB_USERNAME = os.environ.get("GITHUB_USERNAME")
FILE_PATH = "bot.py" # El archivo del bot de Telegram que modificará la IA

# Función para obtener el código actual directamente desde la API de GitHub
def obtener_codigo_actual_github():
    if not all([GITHUB_TOKEN, GITHUB_REPO, GITHUB_USERNAME]):
        return "# Error: Faltan configurar las variables de GitHub en Railway."
    
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        import base64
        datos = response.json()
        # Guardamos el SHA para poder actualizarlo luego
        st.session_state.file_sha = datos["sha"]
        codigo_decodificado = base64.b64decode(datos["content"]).decode("utf-8")
        return codigo_decodificado
    elif response.status_code == 404:
        # Si el archivo no existe en el repositorio, inicializamos con una plantilla vacía
        st.session_state.file_sha = None
        return "# Archivo nuevo para tu bot de Telegram\n"
    else:
        return f"# No se pudo obtener el código. Error {response.status_code}"

# Función para subir el nuevo código automáticamente a GitHub
def subir_codigo_a_github(nuevo_codigo, instruccion):
    import base64
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    
    # Codificar el contenido en Base64 requerido por GitHub
    codigo_bytes = nuevo_codigo.encode("utf-8")
    codigo_base64 = base64.b64encode(codigo_bytes).decode("utf-8")
    
    payload = {
        "message": f"🤖 CadetBot2: {instruccion[:50]}...",
        "content": codigo_base64
    }
    
    # Si el archivo ya existía, necesitamos incluir el SHA para sobreescribirlo
    if "file_sha" in st.session_state and st.session_state.file_sha:
        payload["sha"] = st.session_state.file_sha

    response = requests.put(url, json=payload, headers=headers)
    return response.status_code in [200, 201]

# Inicializar historial de chat
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "¡Listo Arturo! Conexión con GitHub y DeepSeek establecida. Pídeme cualquier cambio y lo subiré al repositorio directamente."}
    ]

# Mostrar historial
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Interacción
if user_input := st.chat_input("Escribe tu instrucción de modificación aquí..."):
    with st.chat_message("user"):
        st.write(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    with st.chat_message("assistant"):
        with st.spinner("Leyendo repositorio y analizando con DeepSeek..."):
            
            if not DEEPSEEK_API_KEY or not GITHUB_TOKEN:
                st.error("Asegúrate de tener DEEPSEEK_API_KEY y GITHUB_TOKEN configurados en Railway.")
            else:
                try:
                    # 1. Traer el código actual desde GitHub en tiempo real
                    codigo_actual = obtener_codigo_actual_github()
                    
                    # 2. Llamar a DeepSeek
                    url_ds = "https://api.deepseek.com/v1/chat/completions"
                    headers_ds = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
                    
                    payload_ds = {
                        "model": "deepseek-chat",
                        "messages": [
                            {
                                "role": "system", 
                                "content": "Eres un agente experto en Python y Telegram. Tu tarea es recibir el código actual, aplicar las modificaciones solicitadas y responder SIEMPRE incluyendo el código completo modificado dentro de un bloque de código markdown conteniendo únicamente Python (usando ```python y ```)."
                            },
                            {
                                "role": "user", 
                                "content": f"Código Original en GitHub:\n
http://googleusercontent.com/immersive_entry_chip/0

---

### ¿Cómo va a funcionar ahora?
Cuando guardes este archivo en GitHub y Railway se redespliegue:
1. Al escribirle algo en el chat (por ejemplo: *"Agrega un comando `/start` que salude en español"*), CadetBot2 leerá el archivo `bot.py` actual de tu repositorio.
2. Le mandará ese código junto con tu instrucción a DeepSeek.
3. La IA reescribirá el código.
4. Tu backend extraerá de forma automática el bloque generado y ejecutará un **Commit e inyección directa en GitHub** sin que tengas que tocar una sola tecla.

Haz los commits de los archivos, coloca las variables en Railway y pruébalo. ¿Qué comando o función quieres que probemos añadir primero al bot una vez que cargue?
