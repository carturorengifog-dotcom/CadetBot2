import streamlit as st
import requests
import os

# Configuración de la página
st.set_page_config(page_title="CadetBot2 - Copiloto de Telegram", page_icon="🤖", layout="wide")
st.title("🤖 CadetBot2: Panel de Control del Bot")

# Función para simular u obtener el código actual del bot de Telegram
def obtener_codigo_actual():
    # Intenta leer el archivo del bot si existe, de lo contrario devuelve un string base
    if os.path.exists("bot.py"):
        with open("bot.py", "r", encoding="utf-8") as f:
            return f.read()
    return "# Aquí va el código actual de tu bot de Telegram\n# Define tus handlers y comandos aquí."

# 1. Inicializar el historial de mensajes en la sesión si no existe
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "¡Hola Arturo! Soy tu agente de desarrollo. Pásame instrucciones para modificar o mejorar tu bot de Telegram."}
    ]

# 2. Mostrar el historial de chat en la interfaz
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# 3. Interacción y envío al cerebro (DeepSeek)
if user_input := st.chat_input("Escribe tu instrucción de modificación aquí..."):
    # Mostrar el mensaje del usuario en la pantalla
    with st.chat_message("user"):
        st.write(user_input)
    
    # Guardar en el historial de la sesión
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # 4. Llamada a la API de DeepSeek
    with st.chat_message("assistant"):
        with st.spinner("Copiloto analizando y estructurando el código..."):
            api_key = os.environ.get("DEEPSEEK_API_KEY")
            
            if not api_key:
                st.error("Por favor, configura la variable DEEPSEEK_API_KEY en Railway.")
            else:
                try:
                    # Preparar la petición
                    url = "https://api.deepseek.com/v1/chat/completions" # URL estándar de DeepSeek
                    headers = {
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    }
                    
                    # Obtenemos el código actual para dárselo como contexto a la IA
                    codigo_contexto = obtener_codigo_actual()
                    
                    # Construimos el payload de manera limpia y corregida
                    payload = {
                        "model": "deepseek-chat",
                        "messages": [
                            {
                                "role": "system", 
                                "content": "Eres un agente experto en programación en Python y bots de Telegram. Tu tarea es reescribir y mejorar el código basándote estrictamente en las instrucciones del usuario."
                            },
                            {
                                "role": "user", 
                                "content": f"Código Actual:\n{codigo_contexto}\n\nInstrucción del usuario: {user_input}"
                            }
                        ],
                        "temperature": 0.2
                    }
                    
                    # Realizar la solicitud HTTP POST
                    response = requests.post(url, json=payload, headers=headers)
                    
                    if response.status_code == 200:
                        resultado = response.json()
                        respuesta_ia = resultado["choices"][0]["message"]["content"]
                        
                        # Mostrar respuesta en pantalla y guardar en historial
                        st.write(respuesta_ia)
                        st.session_state.messages.append({"role": "assistant", "content": respuesta_ia})
                    else:
                        st.error(f"Error de la API de DeepSeek (Status {response.status_code}): {response.text}")
                        
                except Exception as e:
                    st.error(f"Ocurrió un error al procesar la solicitud: {str(e)}")
