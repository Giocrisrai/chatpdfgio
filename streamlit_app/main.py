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


def display_description() -> None:
    """Display the description and the 'Start' button on the UI."""
    st.markdown(
        "<div style='background: linear-gradient(to right, #a377db, #7da3d9); padding: 20px; border-radius: 10px;'>"
        "<h2 style='color: white; font-size: 28px;'>¿Qué hace nuestro motor de búsqueda inteligente?</h2>"
        "<div style='font-size: 20px; color: white;'>"
        "Búsqueda eficiente: Encuentra lo que necesitas en segundos.<br>"
        "Inteligencia Artificial: Respuestas precisas y naturales.<br>"
        "Multilingüe: Busca en varios idiomas.<br>"
        "</div>"
        "<hr style='border-color: white;'>"
        "<h3 style='color: white; font-size: 24px;'>¿Listo para empezar?</h3>"
        "</div>",
        unsafe_allow_html=True
    )
    if st.button('Iniciar', key='start_button'):
        st.session_state.show_sections = True


def handle_file_upload(api_url: str) -> None:
    """Handle file uploading and API interaction for file processing."""
    st.markdown(
        "<div style='background: linear-gradient(to right, #89a8cc, #a377db); padding: 20px; border-radius: 10px;'>"
        "<h2 style='color: white; font-size: 28px;'>1. Sube tus archivos</h2>"
        "</div>",
        unsafe_allow_html=True
    )

    uploaded_files = st.file_uploader(
        "Sube tus archivos PDF aquí", type="pdf", accept_multiple_files=True)

    if uploaded_files:
        files_to_send = [
            ("files", (file.name, file.read(), "application/pdf")) for file in uploaded_files]
        try:
            status_code = send_files_to_api(files_to_send, api_url)
            if status_code == 200:
                st.session_state.files_processed = True
                st.success(
                    "Los archivos se han cargado y procesado con éxito.")
                logging.info("Files successfully processed.")
            else:
                logging.error(
                    f"Error en el procesamiento de archivos. Código de estado: {status_code}")
                st.error(
                    f"Ocurrió un error al procesar los archivos. Código de estado: {status_code}")
        except requests.exceptions.ConnectionError as e:
            logging.error(f"Error de conexión: {e}")
            st.error(
                "Error en la conexión con el servidor. Intente de nuevo más tarde.")


def handle_chat(api_url: str) -> None:
    """Handle user interaction for the chat widget."""
    st.markdown(
        "<div style='background: linear-gradient(to right, #967bb6, #89a8cc); padding: 20px; border-radius: 10px;'>"
        "<h2 style='color: white; font-size: 28px;'>2. Interactúa con la búsqueda inteligente</h2>"
        "</div>",
        unsafe_allow_html=True
    )

    user_input = st.text_input("Haz una pregunta:")

    if st.button('Enviar pregunta'):
        if user_input:
            chat_widget(api_url, user_input)


def main() -> None:
    """
    Main function to run the Streamlit application.
    This function initializes session states, sets up the UI,
    and handles file uploads and chat interactions.
    """
    # Initialize session state
    initialize_session_state()

    # Retrieve API URL and Logo URL from environment variables
    api_url = os.environ.get('API_URL')
    logo_url = os.environ.get('LOGO_URL')

    # UI setup: Display logo
    st.image(logo_url, width=700)

    # UI setup: Description and Start Button
    display_description()

    if st.session_state.show_sections:
        handle_file_upload(api_url)
        handle_chat(api_url)


if __name__ == "__main__":
    main()
