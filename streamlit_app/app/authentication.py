from dotenv import load_dotenv
import os
import json
import logging
from firebase_admin import auth, credentials, App
from typing import Optional, Dict, Any
import streamlit as st

# Initialize logging
logging.basicConfig(level=logging.INFO)

load_dotenv()


def initialize_firebase() -> None:
    """
    Initialize Firebase using environmental credentials.
    """
    try:
        # Build the credentials dictionary from environment variables
        cred_dict: Dict[str, Optional[str]] = {
            "type": os.environ.get("FIREBASE_TYPE"),
            "project_id": os.environ.get("FIREBASE_PROJECT_ID"),
            "private_key_id": os.environ.get("FIREBASE_PRIVATE_KEY_ID"),
            "private_key": os.environ.get("FIREBASE_PRIVATE_KEY").replace("\\n", "\n"),
            "client_email": os.environ.get("FIREBASE_CLIENT_EMAIL"),
            "client_id": os.environ.get("FIREBASE_CLIENT_ID"),
            "auth_uri": os.environ.get("FIREBASE_AUTH_URI"),
            "token_uri": os.environ.get("FIREBASE_TOKEN_URI"),
            "auth_provider_x509_cert_url": os.environ.get("FIREBASE_AUTH_PROVIDER_X509_CERT_URL"),
            "client_x509_cert_url": os.environ.get("FIREBASE_CLIENT_X509_CERT_URL"),
            "universe_domain": os.environ.get("FIREBASE_UNIVERSE_DOMAIN")
        }
        # Convert the dictionary to a credentials object
        cred: credentials.Certificate = credentials.Certificate(cred_dict)
        # Initialize Firebase with the credentials
        initialize_app(cred)
        logging.info("Firebase initialized successfully.")
    except Exception as e:
        logging.error(f"Failed to initialize Firebase: {e}")
        st.error("Failed to initialize Firebase. Check the logs for more details.")


def login_user(email: str, password: str) -> Optional[str]:
    """
    Log in to Firebase and get the token.
    """
    try:
        user: auth.UserRecord = auth.get_user_by_email(email)
        if user:
            token: str = "some_client_side_generated_token"  # Placeholder
            logging.info("User logged in successfully.")
            return token
    except auth.UserNotFoundError:
        logging.warning("User not found.")
        st.warning("User not found.")
        return None


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify the token using Firebase Admin SDK.
    """
    try:
        decoded_token: Dict[str, Any] = auth.verify_id_token(token)
        logging.info("Token verified successfully.")
        return decoded_token
    except ValueError:
        logging.warning("Invalid token.")
        st.warning("Invalid token.")
        return None


def check_auth() -> None:
    """
    Custom component to verify the token from the browser.
    """
    token: str = st.text_input("Enter your token for authentication:")
    if token:
        decoded_token: Optional[Dict[str, Any]] = verify_token(token)
        if decoded_token:
            logging.info("Authentication successful.")
            st.success("Authentication successful.")
        else:
            logging.warning("Authentication failed.")
            st.warning("Authentication failed.")
