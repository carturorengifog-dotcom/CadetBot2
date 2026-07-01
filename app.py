import streamlit as st
import requests
import os
import re
import base64

# Configuración de la página de Streamlit
st.set_page_config(page_title="CadetBot2 - Copiloto Autónomo", page_icon="🤖", layout="wide")
st.title("🤖 CadetBot2: Panel Autónomo del Bot")

# Variables de entorno obtenidas desde Railway
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_REPO = os.environ.get("GITHUB_REPO")
GITHUB_USERNAME = os.environ.get("GITHUB_USERNAME")
FILE_PATH = "bot.py"  # El archivo de tu bot de Telegram que modificará la IA

# Función para obtener el código actual de bot.py directamente desde GitHub
def obtener_codigo_actual_github():
    if not all([GITHUB_TOKEN, GITHUB_REPO, GITHUB_USERNAME]):
        return "# Error: Faltan configurar las variables de GitHub en Railway."
    
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/contents/{FILE_PATH}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            datos = response.json()
            # Guardamos el identificador SHA en el estado de la sesión para poder actualizarlo después
            st.session_state.file_sha = datos["sha"]
            codigo_decodificado = base64.b64decode(datos["content"]).decode("utf-8")
            return codigo_decodificado
        elif response.status_code == 404:
            # Si el archivo aún no existe en GitHub, empezamos con una plantilla en blanco
            st.session_state.file_sha = None
            return "# Archivo nuevo para tu bot de Telegram\n"
        else:
            return f"# No se pudo obtener el código. Código de Estado: {response.status_code}"
    except Exception as e:
        return f"# Error de conexión al leer GitHub: {str(e)}"

# Función para subir el código nuevo directamente a tu repositorio de GitHub
def subir_codigo_a_github(nuevo_codigo, instruccion):
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/contents/{FILE_PATH}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # El contenido debe estar codificado en Base64 para la API de GitHub
    codigo_bytes = nuevo_codigo.encode("utf-8")
    codigo_base64 = base64.b64encode(codigo_bytes).decode("utf-8")
    
    payload = {
        "message": f"🤖 CadetBot2: {instruccion[:50]}...",
        "content": codigo_base64
    }
    
    # Si el archivo ya existía, adjuntamos el SHA para autorizar la sobreescritura
    if "file_sha" in st.session_state and st.session_state.file_sha:
        payload["sha"] = st.session_state.file_sha

    try:
        response = requests.put(url, json=payload, headers=headers)
        return response.status_code in [200, 201]
    except Exception:
        return False

# Función para extraer código de un bloque markdown
def extraer_codigo_del_bloque(respuesta_texto):
    patron = r"```python\n(.*?)\n```"
    match = re.search(patron, respuesta_texto, re.DOTALL)
    if match:
        return match.group(1)
    return None

# Inicializar el historial de mensajes de chat en la sesión
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "¡Listo Arturo! Conexión con GitHub y DeepSeek establecida. Pídeme cualquier cambio y lo subiré al repositorio directamente."}
    ]

# Dibujar el historial de mensajes en la interfaz de Streamlit
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Capturar la entrada de texto del usuario
if user_input := st.chat_input("Escribe tu instrucción de modificación aquí..."):
    # Mostrar el mensaje del usuario inmediatamente
    with st.chat_message("user"):
        st.write(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Generar la respuesta del asistente
    with st.chat_message("assistant"):
        with st.spinner("Leyendo repositorio y analizando con DeepSeek..."):
            
            # Verificar que todas las variables de entorno estén configuradas
            if not all([DEEPSEEK_API_KEY, GITHUB_TOKEN, GITHUB_REPO, GITHUB_USERNAME]):
                error_msg = "❌ Faltan variables de entorno en Railway. Asegúrate de tener: DEEPSEEK_API_KEY, GITHUB_TOKEN, GITHUB_REPO, GITHUB_USERNAME"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
            else:
                try:
                    # 1. Obtener el código actual de bot.py desde GitHub
                    codigo_actual = obtener_codigo_actual_github()
                    
                    # 2. Configurar la llamada a la API de DeepSeek
                    url_ds = "https://api.deepseek.com/v1/chat/completions"
                    headers_ds = {
                        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                        "Content-Type": "application/json"
                    }
                    
                    # CORREGIDO: Aquí estaba el error de la f-string
                    payload_ds = {
                        "model": "deepseek-chat",
                        "messages": [
                            {
                                "role": "system", 
                                "content": "Eres un agente experto en Python y Telegram. Tu tarea es recibir el código actual, aplicar las modificaciones solicitadas y responder SIEMPRE incluyendo el código completo modificado dentro de un bloque de código markdown conteniendo únicamente Python (usando ```python y ```)."
                            },
                            {
                                "role": "user", 
                                "content": f"Código Original en GitHub:\n{codigo_actual}\n\nInstrucción del usuario: {user_input}"
                            }
                        ]
                    }
                    
                    # 3. Hacer la llamada a DeepSeek
                    response_ds = requests.post(url_ds, json=payload_ds, headers=headers_ds)
                    
                    if response_ds.status_code == 200:
                        respuesta_json = response_ds.json()
                        respuesta_completa = respuesta_json["choices"][0]["message"]["content"]
                        
                        # 4. Extraer el código modificado del bloque markdown
                        codigo_modificado = extraer_codigo_del_bloque(respuesta_completa)
                        
                        if codigo_modificado:
                            # 5. Subir el código modificado a GitHub
                            if subir_codigo_a_github(codigo_modificado, user_input):
                                mensaje_exito = "✅ **Código actualizado en GitHub exitosamente!**\n\nEl bot de Telegram se actualizará en breve."
                                st.success(mensaje_exito)
                                st.session_state.messages.append({"role": "assistant", "content": mensaje_exito})
                                
                                # Mostrar el código modificado (opcional)
                                with st.expander("📄 Ver código modificado"):
                                    st.code(codigo_modificado, language="python")
                            else:
                                error_msg = "❌ Error al subir el código a GitHub. Verifica los permisos del token."
                                st.error(error_msg)
                                st.session_state.messages.append({"role": "assistant", "content": error_msg})
                        else:
                            error_msg = "⚠️ No se encontró un bloque de código en la respuesta de DeepSeek. La IA no generó código válido."
                            st.warning(error_msg)
                            st.session_state.messages.append({"role": "assistant", "content": error_msg})
                            
                            # Mostrar la respuesta completa para depuración
                            with st.expander("🔍 Ver respuesta completa de DeepSeek"):
                                st.text(respuesta_completa)
                    else:
                        error_msg = f"❌ Error al comunicarse con DeepSeek. Código: {response_ds.status_code}\n{response_ds.text}"
                        st.error(error_msg)
                        st.session_state.messages.append({"role": "assistant", "content": error_msg})
                        
                except Exception as e:
                    error_msg = f"❌ Error inesperado: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})

# Sidebar con información
with st.sidebar:
    st.header("📊 Estado del Sistema")
    
    # Mostrar estado de las variables de entorno
    st.subheader("🔑 Configuración")
    st.write(f"• GitHub Repo: {'✅' if GITHUB_REPO else '❌'}")
    st.write(f"• GitHub User: {'✅' if GITHUB_USERNAME else '❌'}")
    st.write(f"• GitHub Token: {'✅' if GITHUB_TOKEN else '❌'}")
    st.write(f"• DeepSeek API: {'✅' if DEEPSEEK_API_KEY else '❌'}")
    
    # Mostrar SHA del archivo si existe
    if "file_sha" in st.session_state and st.session_state.file_sha:
        st.write(f"• Archivo SHA: `{st.session_state.file_sha[:8]}...`")
    
    # Botón para ver el código actual
    if st.button("📖 Ver código actual"):
        with st.spinner("Cargando código..."):
            codigo = obtener_codigo_actual_github()
            st.code(codigo, language="python")
    
    # Botón para limpiar el chat
    if st.button("🗑️ Limpiar chat"):
        st.session_state.messages = [
            {"role": "assistant", "content": "🧹 Chat limpiado. ¿En qué más puedo ayudarte Arturo?"}
        ]
        st.rerun()
