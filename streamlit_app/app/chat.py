import logging
from typing import Optional

import requests
import streamlit as st

logger = logging.getLogger(__name__)


def chat_widget(api_url: str, user_input: Optional[str], timeout: float = 120.0) -> None:
    """Ask the API a question and show the answer with the documents it came from."""
    try:
        response = requests.post(
            f"{api_url}/chat/", params={"query": user_input}, timeout=timeout
        )
        if response.status_code != 200:
            logger.error("Failed to get chat response. Status code: %s", response.status_code)
            st.error("Error al obtener la respuesta de la búsqueda inteligente.")
            return
        body = response.json()
        st.write(f"📘 **Respuesta**: {body['response']}")
        sources = body.get("sources", [])
        if sources:
            st.caption(
                "Fuentes: "
                + " · ".join(f"{item['source']} ({item['location']})" for item in sources)
            )
    except Exception as error:
        logger.error("An error occurred in chat_widget: %s", error)
        st.error(
            "Ocurrió un error al interactuar con la Búsqueda Inteligente. "
            "Inténtelo de nuevo más tarde."
        )
