import logging
import streamlit as st
import requests
from app.file_upload import send_files_to_api
from app.chat import chat_widget
from app.utils import initialize_session_state
from app.authentication import initialize_firebase, login_user, check_auth
import os
import time
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


def handle_file_upload(api_url: str) -> None:
    """
    Handle the file upload and API interaction for file processing.

    Parameters:
    - api_url (str): The API URL for backend processing.

    This function will:
    - Display the file uploader widget.
    - Send the files to the backend API for processing.
    - Update the UI based on the API response.
    """
    if 'files_uploaded' not in st.session_state:
        st.session_state.files_uploaded = False

    # Show only if files have not been uploaded and sections should be shown
    if not st.session_state.files_uploaded and st.session_state.show_sections:
        st.markdown(
            "<div style='background: linear-gradient(to right, #89a8cc, #a377db); padding: 20px; border-radius: 10px;'>"
            "<h2 style='color: white; font-size: 28px;'>1. Sube tus archivos</h2>"
            "</div>",
            unsafe_allow_html=True
        )

        uploaded_files = st.file_uploader(
            "Sube tus archivos PDF aquí", type="pdf", accept_multiple_files=True)

        if uploaded_files:
            with st.spinner('Procesando archivos...'):
                files_to_send = [
                    ("files", (file.name, file.read(), "application/pdf")) for file in uploaded_files]
                try:
                    status_code = send_files_to_api(files_to_send, api_url)
                    if status_code == 200:
                        st.success(
                            "Los archivos se han cargado y procesado con éxito.")
                        logging.info("Files successfully processed.")
                        st.session_state.files_uploaded = True  # Actualizar el estado de la sesión
                    else:
                        st.error(
                            f"Ocurrió un error al procesar los archivos. Código de estado: {status_code}")
                        logging.error(
                            f"Error en el procesamiento de archivos. Código de estado: {status_code}")
                except requests.exceptions.ConnectionError as e:
                    st.error(
                        "Error en la conexión con el servidor. Intente de nuevo más tarde.")
                    logging.error(f"Error de conexión: {e}")


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
            with st.spinner('Procesando pregunta...'):
                chat_widget(api_url, user_input)


def main() -> None:
    # Initialize session state variables
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'show_sections' not in st.session_state:
        st.session_state.show_sections = False
    if 'user_email' not in st.session_state:
        st.session_state.user_email = None

    # Always display logo and description at the top
    api_url = os.environ.get('API_URL')
    logo_url = os.environ.get('LOGO_URL')
    st.image(logo_url, width=700)
    display_description()

    # Sidebar section
    st.sidebar.header("Control Panel")

    # Placeholder for user info and Logout button
    user_info_placeholder = st.sidebar.empty()

    if st.session_state.authenticated:
        user_info_placeholder.write(
            f"Logged in as: {st.session_state.user_email}")
        if st.sidebar.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.show_sections = False
            st.session_state.user_email = None
            user_info_placeholder.empty()

    if not st.session_state.authenticated:
        st.sidebar.subheader("User Authentication")
        email = st.sidebar.text_input("Email")
        password = st.sidebar.text_input("Password", type="password")

        if st.sidebar.button("Log In"):
            firebase_status = initialize_firebase()
            if "successfully" in firebase_status.lower():
                token = login_user(email, password)
                if token:
                    st.session_state.authenticated = True
                    st.session_state.user_email = email
                    st.sidebar.success("Successfully authenticated.")
                else:
                    st.sidebar.error("Authentication failed.")

    if st.session_state.authenticated:
        if st.button("Iniciar"):
            st.session_state.show_sections = True

    if st.session_state.show_sections:
        handle_file_upload(api_url)
        handle_chat(api_url)


if __name__ == "__main__":
    main()
