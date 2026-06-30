import streamlit as st
import os
import requests
from github import Github

# Configuración inicial de la cabina
st.set_page_config(page_title="Copiloto de Desarrollo", page_icon="🤖", layout="wide")
st.title("🤖 Mi Copiloto de Agentes (DeepSeek)")
st.subheader("Modificación autónoma de código en la nube")

# 1. Función para conectarse a GitHub y traer tu código actual
@st.cache_data
def obtener_codigo_actual():
    try:
        token = os.environ.get("GITHUB_TOKEN")
        repo_name = os.environ.get("GITHUB_REPO") # Ejemplo: "tu-usuario/CFIbot"
        
        if not token or not repo_name:
            return "Faltan configurar las variables GITHUB_TOKEN o GITHUB_REPO en Railway."
            
        g = Github(token)
        repo = g.get_repo(repo_name)
        
        # Intentamos buscar el archivo principal de tu bot (ajusta el nombre si es necesario)
        for archivo_posible in ["main.py", "bot.py", "app.py"]:
            try:
                contenido = repo.get_contents(archivo_posible)
                return contenido.decoded_content.decode("utf-8"), archivo_posible
            except:
                continue
        return "No se encontró el archivo principal (main.py, bot.py) en tu repositorio.", None
    except Exception as e:
        return f"Error de conexión con GitHub: {e}", None

# Cargar el código del bot en periodo de prueba de forma transparente
codigo_actual, nombre_archivo = obtener_codigo_actual()

# Mostrar estado en la barra lateral
with st.sidebar:
    st.header("🗂️ Conexión del Repositorio")
    if nombre_archivo:
        st.success(f"✅ Conectado a: {nombre_archivo}")
        with st.expander("Ver código actual en prueba"):
            st.code(codigo_actual, language="python")
    else:
        st.error(codigo_actual)

# 2. Historial del chat visual
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "¡Listo en la cabina Arturo! He leído tu código en periodo de prueba con éxito. ¿Qué cambio o nueva lógica basada en tus manuales de vuelo vamos a programar hoy?"}
    ]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# 3. Interacción y envío al cerebro (DeepSeek)
if user_input := st.chat_input("Escribe tu instrucción de modificación aquí..."):
    with st.chat_message("user"):
        st.write(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Llamada a la API de DeepSeek
    with st.chat_message("assistant"):
        with st.spinner("Copiloto analizando y estructurando el código..."):
            api_key = os.environ.get("DEEPSEEK_API_KEY")
            
            if not api_key:
                st.error("Por favor, configura la variable DEEPSEEK_API_KEY en Railway.")
            else:
                try:
                    # Preparar el prompt del sistema para que actúe como un agente de código preciso
                    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                    payload = {
                        "model": "deepseek-chat",
                        "messages": [
                            {"role": "system", "content": "Eres un agente experto en programación en Python y bots de Telegram. Tu tarea es reescribir y mejorar el código del usuario basado en sus instrucciones específicas. Devuelve siempre el código completo y listo para producción."},
                            {"role": "user", "content": f"Código Actual:\n
http://googleusercontent.com/immersive_entry_chip/0

Guarda los cambios en GitHub presionando **`Commit changes`**. Railway detectará el cambio automáticamente, compilará la versión final y, cuando entres a tu nuevo dominio generado, ¡tu agente local en la nube estará completamente vivo! 

Presiona el botón de generar dominio y me cuentas si logras ver la interfaz activa en tu navegador.
