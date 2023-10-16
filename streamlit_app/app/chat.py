import logging
import requests
from typing import Optional
import streamlit as st

# Initialize logging
logging.basicConfig(level=logging.INFO)


def chat_widget(api_url: str, user_input: Optional[str]) -> None:
    """
    A Streamlit widget for chatting through a specified API.

    Parameters:
    - api_url: str, The URL of the API endpoint where the chat request will be sent.
    - user_input: Optional[str], The user's question to the chatbot.

    Raises:
    - Exception: Any exception raised during the chat request will be caught and logged.
    """
    try:
        payload = {'query': user_input}
        response = requests.post(f"{api_url}/chat/", params=payload)

        if response.status_code == 200:
            chat_response = response.json()['response']
            st.write(f"📘 **Respuesta**: {chat_response}")
        else:
            logging.error(
                f"Failed to get chat response. Status code: {response.status_code}")
            st.error("Error al obtener la respuesta de la búsqueda inteligente.")
    except Exception as e:
        logging.error(f"An error occurred in chat_widget: {e}")
        st.error(
            "Ocurrió un error al interactuar con la Búsqueda Inteligente. Inténtelo de nuevo más tarde.")
