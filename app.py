import streamlit as st

st.set_page_config(page_title="Copiloto de Desarrollo", page_icon="🤖", layout="wide")

st.title("🤖 Mi Copiloto de Agentes (DeepSeek)")
st.subheader("Modificación autónoma de código en la nube")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "¡Hola Arturo! Listo en la cabina. Ya estoy conectado a tu cuenta. ¿Qué lógica o función vamos a modificar en tus bots hoy?"}
    ]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

if user_input := st.chat_input("Escribe tu instrucción aquí..."):
    with st.chat_message("user"):
        st.write(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    with st.chat_message("assistant"):
        respuesta = f"Recibido. Analizando la instrucción para tu bot en periodo de prueba: '{user_input}'."
        st.write(respuesta)
    st.session_state.messages.append({"role": "assistant", "content": respuesta})
