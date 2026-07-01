import streamlit as st
import requests
import os
import re
import base64

# Configuración de la página
st.set_page_config(page_title="CadetBot2 - Copiloto Autónomo", page_icon="🤖", layout="wide")
st.title("🤖 CadetBot2: Panel Autónomo del Bot")

# Variables de entorno
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_REPO = os.environ.get("GITHUB_REPO")
GITHUB_USERNAME = os.environ.get("GITHUB_USERNAME")
FILE_PATH = "bot.py"

# Función para obtener código de GitHub
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
            st.session_state.file_sha = datos["sha"]
            codigo_decodificado = base64.b64decode(datos["content"]).decode("utf-8")
            return codigo_decodificado
        elif response.status_code == 404:
            st.session_state.file_sha = None
            # Código base para un bot de Telegram
            return """import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.environ.get("TELEGRAM_TOKEN", "TU_TOKEN_AQUI")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("¡Hola! Soy tu bot de Telegram 🤖")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Comandos disponibles:\\n/start - Iniciar\\n/help - Ayuda")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.run_polling()

if __name__ == "__main__":
    main()"""
        else:
            return f"# Error: {response.status_code}"
    except Exception as e:
        return f"# Error: {str(e)}"

# Función para subir a GitHub
def subir_codigo_a_github(nuevo_codigo, instruccion):
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/contents/{FILE_PATH}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    codigo_base64 = base64.b64encode(nuevo_codigo.encode("utf-8")).decode("utf-8")
    
    payload = {
        "message": f"🤖 CadetBot2: {instruccion[:50]}...",
        "content": codigo_base64
    }
    
    if "file_sha" in st.session_state and st.session_state.file_sha:
        payload["sha"] = st.session_state.file_sha

    try:
        response = requests.put(url, json=payload, headers=headers)
        # Actualizar el SHA después de subir
        if response.status_code in [200, 201]:
            st.session_state.file_sha = response.json().get("content", {}).get("sha")
        return response.status_code in [200, 201]
    except Exception:
        return False

# Función mejorada para extraer código
def extraer_codigo_del_bloque(respuesta_texto):
    # Buscar bloques de código Python
    patrones = [
        r"```python\n(.*?)\n```",  # Bloque python estándar
        r"```\n(.*?)\n```",        # Bloque genérico
        r"```python(.*?)```",      # Sin saltos de línea
        r"```(.*?)```"             # Cualquier bloque
    ]
    
    for patron in patrones:
        match = re.search(patron, respuesta_texto, re.DOTALL)
        if match:
            codigo = match.group(1).strip()
            # Verificar que parece código Python
            if codigo and ("import" in codigo or "def " in codigo or "class " in codigo):
                return codigo
    
    # Si no hay bloque, intentar extraer código directamente
    lineas = respuesta_texto.split('\n')
    codigo_lineas = []
    en_codigo = False
    
    for linea in lineas:
        if linea.strip().startswith(('import', 'from', 'def ', 'class ', '@')):
            en_codigo = True
            codigo_lineas.append(linea)
        elif en_codigo and linea.strip():
            codigo_lineas.append(linea)
        elif en_codigo and not linea.strip():
            codigo_lineas.append(linea)
    
    if codigo_lineas:
        return '\n'.join(codigo_lineas)
    
    return None

# Inicializar historial
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "¡Listo Arturo! 🚀\n\nSoy tu copiloto autónomo. Puedo modificar el código de tu bot de Telegram en GitHub.\n\n**Para empezar, dime qué quieres hacer, por ejemplo:**\n• Crear un bot básico\n• Añadir el comando /start\n• Agregar un handler para mensajes de texto\n• Implementar una función de eco"}
    ]

# Mostrar mensajes
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Input del usuario
if user_input := st.chat_input("¿Qué modificación quieres hacer en tu bot?"):
    with st.chat_message("user"):
        st.write(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    with st.chat_message("assistant"):
        with st.spinner("🤔 Analizando y generando código..."):
            
            if not all([DEEPSEEK_API_KEY, GITHUB_TOKEN, GITHUB_REPO, GITHUB_USERNAME]):
                error_msg = "❌ Faltan variables de entorno. Configura: DEEPSEEK_API_KEY, GITHUB_TOKEN, GITHUB_REPO, GITHUB_USERNAME"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
            else:
                try:
                    # Obtener código actual
                    codigo_actual = obtener_codigo_actual_github()
                    
                    # Llamar a DeepSeek
                    url_ds = "https://api.deepseek.com/v1/chat/completions"
                    headers_ds = {
                        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                        "Content-Type": "application/json"
                    }
                    
                    # System prompt mejorado
                    system_prompt = """Eres un experto en Python y desarrollo de bots para Telegram usando python-telegram-bot.

REGLAS IMPORTANTES:
1. **SIEMPRE** responde con el código COMPLETO del archivo bot.py
2. El código debe estar dentro de un bloque ```python
3. NO incluyas explicaciones fuera del bloque de código
4. El código debe ser funcional y ejecutable
5. Mantén la estructura del código original si no se pide cambiar
6. Usa variables de entorno para datos sensibles (TOKEN, etc.)

Si no hay código existente, crea un bot básico con:
- Comando /start
- Comando /help
- Manejador para mensajes de texto

RESPONDE SOLO CON EL CÓDIGO COMPLETO."""
                    
                    payload_ds = {
                        "model": "deepseek-chat",
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": f"Código actual:\n{codigo_actual}\n\nInstrucción: {user_input}\n\nGenera el código completo modificado."}
                        ],
                        "temperature": 0.3,  # Reducir creatividad para código más consistente
                        "max_tokens": 2000
                    }
                    
                    response_ds = requests.post(url_ds, json=payload_ds, headers=headers_ds, timeout=30)
                    
                    if response_ds.status_code == 200:
                        respuesta_json = response_ds.json()
                        respuesta_completa = respuesta_json["choices"][0]["message"]["content"]
                        
                        # Extraer código
                        codigo_modificado = extraer_codigo_del_bloque(respuesta_completa)
                        
                        if codigo_modificado:
                            # Subir a GitHub
                            if subir_codigo_a_github(codigo_modificado, user_input):
                                mensaje = "✅ **¡Código actualizado exitosamente!**\n\nEl bot se actualizará automáticamente."
                                st.success(mensaje)
                                st.session_state.messages.append({"role": "assistant", "content": mensaje})
                                
                                with st.expander("📄 Ver código nuevo"):
                                    st.code(codigo_modificado, language="python")
                            else:
                                error_msg = "❌ Error al subir a GitHub. Verifica el token de acceso."
                                st.error(error_msg)
                                st.session_state.messages.append({"role": "assistant", "content": error_msg})
                        else:
                            # Mostrar la respuesta de DeepSeek para depuración
                            st.warning("⚠️ No se encontró código válido en la respuesta")
                            with st.expander("🔍 Ver respuesta de DeepSeek"):
                                st.text(respuesta_completa)
                            
                            # Intentar extraer solo el código si hay alguna mención
                            if "import" in respuesta_completa or "def " in respuesta_completa:
                                st.info("💡 La respuesta contiene código pero no está en el formato esperado. Intenta ser más específico.")
                            
                            st.session_state.messages.append({
                                "role": "assistant", 
                                "content": "No pude generar código válido. Por favor, sé más específico con tu instrucción o reformula tu petición."
                            })
                    else:
                        error_msg = f"❌ Error con DeepSeek: {response_ds.status_code}\n{response_ds.text[:200]}"
                        st.error(error_msg)
                        st.session_state.messages.append({"role": "assistant", "content": error_msg})
                        
                except Exception as e:
                    error_msg = f"❌ Error inesperado: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})

# Sidebar
with st.sidebar:
    st.header("📊 Estado del Sistema")
    st.write(f"• GitHub Repo: {'✅' if GITHUB_REPO else '❌'}")
    st.write(f"• GitHub User: {'✅' if GITHUB_USERNAME else '❌'}")
    st.write(f"• GitHub Token: {'✅' if GITHUB_TOKEN else '❌'}")
    st.write(f"• DeepSeek API: {'✅' if DEEPSEEK_API_KEY else '❌'}")
    
    if "file_sha" in st.session_state and st.session_state.file_sha:
        st.write(f"• Archivo SHA: `{st.session_state.file_sha[:8]}...`")
    
    st.divider()
    
    if st.button("📖 Ver código actual"):
        with st.spinner("Cargando..."):
            codigo = obtener_codigo_actual_github()
            st.code(codigo, language="python")
    
    if st.button("🗑️ Limpiar conversación"):
        st.session_state.messages = [
            {"role": "assistant", "content": "🧹 Conversación limpiada. ¿En qué puedo ayudarte?"}
        ]
        st.rerun()
    
    st.divider()
    st.caption("💡 **Sugerencias de comandos:**")
    st.caption("• 'Crea un bot básico'")
    st.caption("• 'Añade el comando /start'")
    st.caption("• 'Agrega un handler para mensajes'")
    st.caption("• 'Implementa una función de eco'")
