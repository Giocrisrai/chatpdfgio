import logging
import streamlit as st
import requests
from app.file_upload import send_files_to_api
from app.chat import chat_widget
from app.utils import initialize_session_state
import os
from dotenv import load_dotenv


load_dotenv()
logging.basicConfig(level=logging.INFO)


def main() -> None:
    """
    The main function for running the Streamlit application.
    This function initializes session states, sets up the UI,
    and handles file uploads and chat interactions.
    """
    # Initialize session state
    initialize_session_state()

    # API URL and Logo URL
    api_url = os.environ.get('API_URL')
    logo_url = os.environ.get('LOGO_URL')

    # UI setup
    col1, col2 = st.columns([1, 2])
    with col1:
        st.image(logo_url, width=345)
    with col2:
        st.markdown(
            "<div style='margin-left: 100px; background-color: #a377db; padding: 14px; border-radius: 10px;'>"
            "<h1 style='text-align: center; color: white; font-size: 40px;'>Demo de Buscador Inteligente FOCUSTECH</h1>"
            "</div>",
            unsafe_allow_html=True
        )

    # Description and Start Button
    st.markdown(
        "<div style='background: linear-gradient(to right, #a377db, #7da3d9); padding: 20px; border-radius: 10px;'>"
        "<h2 style='color: white; font-size: 28px;'>🌟 ¿Qué hace nuestro Buscador Inteligente?</h2>"
        "<div style='font-size: 20px; color: white;'>"
        "🚀 **Búsqueda Eficiente**: Encuentra lo que necesitas en segundos.<br>"
        "🤖 **Inteligencia Artificial**: Respuestas precisas y naturales.<br>"
        "🌐 **Multilingüe**: Busca en varios idiomas.<br>"
        "</div>"
        "<hr style='border-color: white;'>"
        "<h3 style='color: white; font-size: 24px;'>🌈 ¿Listo para empezar?</h3>"
        "</div>",
        unsafe_allow_html=True
    )

    if st.button('🌟 Empezar 🌟', key='start_button'):
        st.session_state.show_sections = True

    if st.session_state.show_sections:
        # File Upload Section
        st.markdown(
            "<div style='background: linear-gradient(to right, #89a8cc, #a377db); padding: 20px; border-radius: 10px;'>"
            "<h2 style='color: white; font-size: 28px;'>📁 1. Carga tus archivos PDF</h2>"
            "</div>",
            unsafe_allow_html=True
        )

        uploaded_files = st.file_uploader(
            "📤 Carga tus archivos PDF aquí", type="pdf", accept_multiple_files=True)

        if uploaded_files:
            files_to_send = [
                ("files", (file.name, file.read(), "application/pdf")) for file in uploaded_files]
            try:
                status_code = send_files_to_api(files_to_send, api_url)
                if status_code == 200:
                    st.session_state.files_processed = True
                    st.success(
                        "✅ Los archivos se han cargado y procesado correctamente.")
                    logging.info("Files successfully processed.")
                else:
                    logging.error(
                        f"Error in file processing. Status code: {status_code}")
            except requests.exceptions.ConnectionError as e:
                logging.error(f"Connection Error: {e}")
                st.error(
                    "Error en la conexión con el servidor. Por favor, inténtelo de nuevo más tarde.")

        # Chat Section
        st.markdown(
            "<div style='background: linear-gradient(to right, #967bb6, #89a8cc); padding: 20px; border-radius: 10px;'>"
            "<h2 style='color: white; font-size: 28px;'>💬 2. Interactúa con la Búsqueda Inteligente</h2>"
            "</div>",
            unsafe_allow_html=True
        )

        user_input = st.text_input("❓ Haz una pregunta:")

        if st.button('🔍 Enviar pregunta'):
            if user_input:
                chat_widget(api_url, user_input)

        # Contact Section
        st.markdown(
            "<div style='background: linear-gradient(to right, #7da3d9, #967bb6); padding: 20px; border-radius: 10px;'>"
            "<h3 style='color: white; font-size: 24px;'><a href='mailto:contacto@focus-tech.cl' style='color: white; text-decoration: none;'>📧 ¿Te interesa? Contacta con nosotros</a></h3>"
            "</div>",
            unsafe_allow_html=True
        )


if __name__ == "__main__":
    main()
