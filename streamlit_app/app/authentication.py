from dotenv import load_dotenv
import os
import json
import logging
import requests
from firebase_admin import auth, credentials, initialize_app
from typing import Optional, Dict, Any
import streamlit as st
import firebase_admin

# Initialize logging
logging.basicConfig(level=logging.INFO)

# Load environment variables
load_dotenv()


def get_token(email: str, password: str) -> Optional[str]:
    """
    Authenticate a user with Firebase and get an authentication token.

    Parameters:
        email (str): The email of the user.
        password (str): The password of the user.

    Returns:
        Optional[str]: The authentication token if successful, None otherwise.
    """
    API_KEY = os.environ.get("FIREBASE_API_KEY")
    if API_KEY is None:
        logging.error("FIREBASE_API_KEY is not set in environment variables.")
        return None

    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={API_KEY}"
    data = {
        "email": email,
        "password": password,
        "returnSecureToken": True
    }
    r = requests.post(url, json=data)
    if r.status_code == 200:
        return r.json().get("idToken")
    else:
        logging.error(
            f"Failed to get token. Status code: {r.status_code}, Reason: {r.reason}")
        return None


def initialize_firebase() -> str:
    """
    Initialize Firebase using environmental credentials.
    """
    try:
        # Check if the Firebase app has already been initialized
        firebase_admin.get_app()
        logging.info("Firebase already initialized.")
        return "Firebase already initialized."

    except ValueError as e:
        try:
            required_env_vars = [
                "FIREBASE_TYPE",
                "FIREBASE_PROJECT_ID",
                "FIREBASE_PRIVATE_KEY_ID",
                "FIREBASE_PRIVATE_KEY",
                "FIREBASE_CLIENT_EMAIL",
                "FIREBASE_CLIENT_ID",
                "FIREBASE_AUTH_URI",
                "FIREBASE_TOKEN_URI",
                "FIREBASE_AUTH_PROVIDER_X509_CERT_URL",
                "FIREBASE_CLIENT_X509_CERT_URL",
                "FIREBASE_UNIVERSE_DOMAIN"
            ]

            missing_vars = [
                var for var in required_env_vars if os.environ.get(var) is None]

            if missing_vars:
                raise EnvironmentError(
                    f"Missing environment variables: {', '.join(missing_vars)}")

            cred_dict: Dict[str, Optional[str]] = {
                "type": os.environ["FIREBASE_TYPE"],
                "project_id": os.environ["FIREBASE_PROJECT_ID"],
                "private_key_id": os.environ["FIREBASE_PRIVATE_KEY_ID"],
                "private_key": os.environ["FIREBASE_PRIVATE_KEY"].replace("\\n", "\n"),
                "client_email": os.environ["FIREBASE_CLIENT_EMAIL"],
                "client_id": os.environ["FIREBASE_CLIENT_ID"],
                "auth_uri": os.environ["FIREBASE_AUTH_URI"],
                "token_uri": os.environ["FIREBASE_TOKEN_URI"],
                "auth_provider_x509_cert_url": os.environ["FIREBASE_AUTH_PROVIDER_X509_CERT_URL"],
                "client_x509_cert_url": os.environ["FIREBASE_CLIENT_X509_CERT_URL"],
                "universe_domain": os.environ["FIREBASE_UNIVERSE_DOMAIN"]
            }

            cred: credentials.Certificate = credentials.Certificate(cred_dict)
            initialize_app(cred)
            logging.info("Firebase initialized successfully.")
            return "Firebase initialized successfully."

        except EnvironmentError as ee:
            logging.error(
                f"Failed to initialize Firebase due to missing environment variables: {ee}")
            return "Failed to initialize Firebase. Check that all required environment variables are set."

        except Exception as e:
            logging.error(f"Failed to initialize Firebase: {e}")
            return "Failed to initialize Firebase. Check the logs for more details."


def login_user(email: str, password: str) -> str:
    """
    Log in to Firebase and get the token.
    """
    try:
        # Initialize Firebase
        initialize_status = initialize_firebase()

        if "successfully" not in initialize_status.lower():
            logging.warning(
                f"Firebase initialization failed: {initialize_status}")
            return "Firebase initialization failed."

        # Use the get_token function here
        token: str = get_token(email, password)
        if token:
            logging.info("User logged in successfully.")
            return f"Successfully authenticated: {token}"
        else:
            logging.warning("User login failed.")
            return "Authentication failed."

    except Exception as e:
        logging.error(f"An exception occurred during login: {e}")
        return "An exception occurred during login."


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
    Custom Streamlit component to verify the authentication token entered by the user.

    Asks the user to input a token and verifies it. Streamlit will display a success or failure message.
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
