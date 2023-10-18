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
        firebase_admin.get_app()
        logging.info("Firebase already initialized.")
        return "Firebase already initialized."
    except ValueError as e:
        try:
            cred_dict = {
                "type": os.environ.get("FIREBASE_TYPE"),
                "project_id": os.environ.get("FIREBASE_PROJECT_ID"),
                "private_key_id": os.environ.get("FIREBASE_PRIVATE_KEY_ID"),
                "private_key": os.environ.get("FIREBASE_PRIVATE_KEY").replace("\\n", "\n"),
                "client_email": os.environ.get("FIREBASE_CLIENT_EMAIL"),
                "client_id": os.environ.get("FIREBASE_CLIENT_ID"),
                "auth_uri": os.environ.get("FIREBASE_AUTH_URI"),
                "token_uri": os.environ.get("FIREBASE_TOKEN_URI"),
                "auth_provider_x509_cert_url": os.environ.get("FIREBASE_AUTH_PROVIDER_X509_CERT_URL"),
                "client_x509_cert_url": os.environ.get("FIREBASE_CLIENT_X509_CERT_URL")
            }

            cred = credentials.Certificate(cred_dict)
            initialize_app(cred)
            logging.info("Firebase initialized successfully.")
            return "Firebase initialized successfully."
        except Exception as e:
            logging.error(f"Failed to initialize Firebase: {e}")
            return "Failed to initialize Firebase. Check the logs for more details."


def login_user(email: str, password: str) -> str:
    """
    Log in to Firebase and get the token.

    Parameters:
        email (str): The email of the user.
        password (str): The password of the user.

    Returns:
        str: Authentication status message.
    """
    try:
        initialize_status = initialize_firebase()
        if "successfully" not in initialize_status.lower():
            logging.warning(
                f"Firebase initialization failed: {initialize_status}")
            return "Firebase initialization failed."

        token = get_token(email, password)
        if token:
            logging.info("User logged in successfully.")
            return f"Successfully authenticated: {token}"
        else:
            logging.warning("User login failed.")
            return "Authentication failed."
    except Exception as e:
        logging.error(f"An exception occurred during login: {e}")
        return "An exception occurred during login."
