import streamlit as st
from app.authentication import initialize_firebase, login_user
import logging

logger = logging.getLogger(__name__)


def show_login():
    """
    Display the login page.

    This function allows users to log in using their email and password.

    Raises:
        Exception: If Firebase initialization fails.
    """
    try:
        st.title("Login")

        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        if st.button("Log In"):
            firebase_status = initialize_firebase()
            if "successfully" in firebase_status.lower():
                token = login_user(email, password)
                if token:
                    st.success("Login successful.")
                    # Redirection logic here
                else:
                    st.error("Authentication failed.")
            else:
                st.error("Firebase initialization failed.")
                logger.error("Firebase initialization failed.")
    except Exception as e:
        st.error("An error occurred during login.")
        logger.error(f"Error during login: {e}")


if __name__ == "__main__":
    show_login()
