import streamlit as st
import google.generativeai as genai
from PIL import Image
import io

# Configure page
st.set_page_config(
    page_title="Beauty & Barber - Generador de Imagen",
    page_icon="✂️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar
with st.sidebar:
    st.title("✂️ Beauty & Barber")
    st.markdown("Generá imágenes personalizadas para tu barbería con IA.")
    st.markdown("---")
    if st.button("🗑️ Limpiar Chat"):
        st.session_state.messages = []
        if "last_generated_image" in st.session_state:
            del st.session_state.last_generated_image
        st.rerun()
    st.markdown("---")
    st.markdown("**Consejos:**")
    st.markdown("- Subí imágenes de referencia")
    st.markdown("- Sé específico en los prompts")
    st.markdown("- Usá refinamiento para editar")
    st.markdown("---")
    st.markdown("[Obtener Google API Key](https://makersuite.google.com/app/apikey)")

# Main content
st.title("🎨 Generador de Imágenes con Gemini")
st.markdown("Subí imágenes, escribí prompts y generá o refiná imágenes para tu barbería.")

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

# Input area
st.markdown("### Crea tu Imagen")
col1, col2 = st.columns([3, 1])
with col1:
    prompt = st.text_area(
        "Describí qué querés generar",
        placeholder="Ej: 'Crea un logo moderno para una barbería con tijeras estilizadas y colores negro y rojo'",
        height=100,
        key="prompt_input"
    )
with col2:
    generate_button = st.button("🎨 Generar Imagen", type="primary", use_container_width=True)

# Examples
with st.expander("💡 Ejemplos de Prompts (Sé específico para mejor calidad)"):
    st.markdown("""
    - "Logo minimalista para barbería con barba estilizada, tijeras doradas, colores negro y rojo, fondo blanco, alta resolución"
    - "Imagen realista de salón de belleza moderno con luces LED azules, sillas de cuero negro, espejos grandes, atmósfera elegante"
    - "Diseño de tarjeta de visita para peluquero: nombre 'Barber King', teléfono, dirección, con imagen de tijeras y peine, estilo vintage"
    - "Ilustración digital de corte de cabello masculino moderno, modelo con barba, colores vibrantes, estilo artístico"
    """)

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
            # Config for high quality square images
            response = model.generate_content(
                content,
                generation_config=genai.GenerationConfig(temperature=1.0),
                # Aspect ratio for image generation
            )

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
                            # Resize to max 1024x1024 if larger
                            max_size = 1024
                            if image.width > max_size or image.height > max_size:
                                image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                                # Convert back to bytes
                                img_byte_arr = io.BytesIO()
                                image.save(img_byte_arr, format='PNG')
                                image_data = img_byte_arr.getvalue()
                            st.image(image)
                            # Download button
                            st.download_button(
                                label="📥 Descargar Imagen",
                                data=image_data,
                                file_name="generated_image.png",
                                mime="image/png",
                                key=f"download_{len(st.session_state.messages)}"
                            )
                            # Regenerate button
                            if st.button("🔄 Regenerar", key=f"regenerate_{len(st.session_state.messages)}"):
                                with st.spinner("Regenerando..."):
                                    try:
                                        response = model.generate_content(content)  # Reuse last content
                                        # For simplicity, rerun the page
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error regenerando: {e}")
                            st.session_state.messages.append({"role": "assistant", "image": image})
                            # Store the last generated image for refinement
                            st.session_state.last_generated_image = image
                except Exception as e:
                    st.error(f"Error procesando respuesta: {e}")
        except Exception as e:
            st.error(f"Error: {e}")

# Refinement section
if "last_generated_image" in st.session_state:
    st.markdown("---")
    st.subheader("🔧 Refinar Imagen Generada")
    st.image(st.session_state.last_generated_image, caption="Imagen actual", width=200)
    refine_prompt = st.text_input("Agregá instrucciones para editar (ej: 'cambiá el color a azul, agregá texto')", key="refine_input")
    refine_button = st.button("✨ Aplicar Cambios", type="secondary")

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
                                # Resize to max 1024x1024 if larger
                                max_size = 1024
                                if image.width > max_size or image.height > max_size:
                                    image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                                    # Convert back to bytes
                                    img_byte_arr = io.BytesIO()
                                    image.save(img_byte_arr, format='PNG')
                                    image_data = img_byte_arr.getvalue()
                                st.image(image)
                                st.download_button(
                                    label="📥 Descargar Imagen",
                                    data=image_data,
                                    file_name="refined_image.png",
                                    mime="image/png",
                                    key=f"download_refine_{len(st.session_state.messages)}"
                                )
                                st.session_state.messages.append({"role": "assistant", "image": image})
                                # Update last generated
                                st.session_state.last_generated_image = image
                    except Exception as e:
                        st.error(f"Error procesando respuesta: {e}")
            except Exception as e:
                st.error(f"Error: {e}")
