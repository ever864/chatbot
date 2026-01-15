import streamlit as st
import google.generativeai as genai
from PIL import Image
import io

# Show title and description.
st.title("💬 Chatbot con Gemini")
st.write(
    "Este es un chatbot simple que usa Gemini 1.5 Pro para generar respuestas, incluyendo soporte para imágenes. "
    "Necesitás una Google API key, que podés conseguir [aquí](https://makersuite.google.com/app/apikey). "
    "Podés subir imágenes y hacer prompts sobre ellas."
)

# Hardcoded Google API key (WARNING: Not secure for production!)
google_api_key = "AIzaSyD4bGjr4thcFNwZu77yWNMhwQ9Rn-jntQA"  # Reemplaza con tu API key real

# Configure Gemini
genai.configure(api_key=google_api_key)
model = genai.GenerativeModel("gemini-3-pro-image-preview")

# Create a session state variable to store the chat messages.
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display the existing chat messages via `st.chat_message`.
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if "text" in message:
            st.markdown(message["text"])
        if "image" in message:
            st.image(message["image"])

# Image uploader
uploaded_image = st.file_uploader("Subí una imagen (opcional)", type=["png", "jpg", "jpeg"], key="image_uploader")

# Create a chat input field.
prompt = st.chat_input("¿Qué querés decir?")

if prompt or uploaded_image:
    message = {"role": "user"}
    image = None
    if uploaded_image:
        image = Image.open(uploaded_image)
        message["image"] = image
    if prompt:
        message["text"] = prompt

    # Display the message
    with st.chat_message("user"):
        if image:
            st.image(image)
        if prompt:
            st.markdown(prompt)

    # Store the message
    st.session_state.messages.append(message)

    # Generate response using Gemini
    try:
        if image:
            # Multimodal content
            content = []
            if prompt:
                content.append(prompt)
            content.append(image)
            response = model.generate_content(content)
        else:
            # Text only - start new chat each time for simplicity
            # To maintain history, we'd need to build proper history
            response = model.generate_content(prompt)

        # Display and store response
        with st.chat_message("assistant"):
            try:
                # Handle response parts
                for part in response.candidates[0].content.parts:
                    if part.text:
                        st.markdown(part.text)
                        st.session_state.messages.append({"role": "assistant", "text": part.text})
                    elif part.inline_data:
                        # It's an image
                        image_data = part.inline_data.data
                        image = Image.open(io.BytesIO(image_data))
                        st.image(image)
                        st.session_state.messages.append({"role": "assistant", "image": image})
            except Exception as e:
                st.error(f"Error procesando respuesta: {e}")
    except Exception as e:
        st.error(f"Error: {e}")
