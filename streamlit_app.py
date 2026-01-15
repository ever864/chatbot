import streamlit as st
import google.generativeai as genai
from PIL import Image
import io

# Show title and description.
st.title("Beauty & Barber - Generador de Imagen")
st.write(
    "Generá imágenes personalizadas para tu barbería con Gemini 3 Pro. "
    "Subí una o más imágenes, agregá un prompt y generá nuevas imágenes. "
    "Necesitás una Google API key, que podés conseguir [aquí](https://makersuite.google.com/app/apikey). "
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
        if "images" in message:
            for img in message["images"]:
                st.image(img)
        elif "image" in message:  # for old single images
            st.image(message["image"])

# Image uploader - allow multiple
uploaded_images = st.file_uploader("Subí una o más imágenes (opcional)", type=["png", "jpg", "jpeg"], accept_multiple_files=True, key="image_uploader")

# Create a chat input field.
prompt = st.text_input("Describí qué querés generar (ej: 'creá un logo moderno para barbería')", key="prompt_input")

# Button to generate
generate_button = st.button("Generar Imagen", type="primary")

if generate_button and (prompt or uploaded_images):
    images = []
    if uploaded_images:
        for uploaded_file in uploaded_images:
            img = Image.open(uploaded_file)
            images.append(img)

    message = {"role": "user"}
    if images:
        message["images"] = images
    if prompt:
        message["text"] = prompt

    # Display the message
    with st.chat_message("user"):
        if images:
            for img in images:
                st.image(img)
        if prompt:
            st.markdown(prompt)

    # Store the message
    st.session_state.messages.append(message)

    # Generate response using Gemini with spinner
    with st.spinner("Generando imagen... Esperá un momento"):
        try:
            content = []
            if prompt:
                content.append(prompt)
            for img in images:
                content.append(img)
            response = model.generate_content(content)

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
                            # Store the last generated image for refinement
                            st.session_state.last_generated_image = image
                except Exception as e:
                    st.error(f"Error procesando respuesta: {e}")
        except Exception as e:
            st.error(f"Error: {e}")

# Refinement section
if "last_generated_image" in st.session_state:
    st.subheader("Refinar Imagen Generada")
    refine_prompt = st.text_input("Agregá más detalles para editar la imagen (ej: 'agregá colores rojos')", key="refine_input")
    refine_button = st.button("Refinar Imagen", type="secondary")

    if refine_button and refine_prompt:
        # Use the last generated image + new prompt
        with st.spinner("Refinando imagen... Esperá un momento"):
            try:
                content = [refine_prompt, st.session_state.last_generated_image]
                response = model.generate_content(content)

                # Display and store new response
                with st.chat_message("assistant"):
                    try:
                        for part in response.candidates[0].content.parts:
                            if part.text:
                                st.markdown(part.text)
                                st.session_state.messages.append({"role": "assistant", "text": part.text})
                            elif part.inline_data:
                                image_data = part.inline_data.data
                                image = Image.open(io.BytesIO(image_data))
                                st.image(image)
                                st.session_state.messages.append({"role": "assistant", "image": image})
                                # Update last generated
                                st.session_state.last_generated_image = image
                    except Exception as e:
                        st.error(f"Error procesando respuesta: {e}")
            except Exception as e:
                st.error(f"Error: {e}")
