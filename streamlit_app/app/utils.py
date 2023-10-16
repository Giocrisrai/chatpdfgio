import streamlit as st


def initialize_session_state():
    """
    Initialize session state variables.
    """
    if 'show_sections' not in st.session_state:
        st.session_state.show_sections = False
    if 'files_processed' not in st.session_state:
        st.session_state.files_processed = False
    if 'submit' not in st.session_state:
        st.session_state.submit = False
