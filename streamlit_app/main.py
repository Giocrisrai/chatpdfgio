"""
Streamlit App for interacting with Document and Chat API.

This application allows users to:
1. Check the status of documents loaded into the system.
2. Upload PDF files for processing.
3. Interact with a chatbot that answers questions based on the uploaded documents.

To run this application, use the following command:
$ streamlit run app_streamlit.py
"""

import streamlit as st
import requests
import json


def main():
    st.title('Document and Chat API Demo Interface')

    # Update with the URL of your hosted API
    api_url = 'https://chatbot-gpt-app-yr2m2.ondigitalocean.app'

    # Verify API connection
    try:
        response = requests.get(f'{api_url}/')
        if response.status_code == 200:
            st.sidebar.success('Connected to API')
        else:
            st.sidebar.error('Failed to connect to API')
    except Exception as e:
        st.sidebar.error(f'Error connecting to API: {e}')

    # Check documents
    if st.button('Check Documents'):
        response = requests.get(f"{api_url}/check-documents/")
        if response.status_code == 200:
            docs_status = json.loads(response.text)
            st.write(docs_status['message'])
        else:
            st.error("Error checking documents")

    # Upload a PDF
    uploaded_file = st.file_uploader("Upload a PDF File", type="pdf")
    if uploaded_file is not None:
        files = {'file': uploaded_file.read()}
        try:
            response = requests.post(f"{api_url}/upload/", files=files)
            if response.status_code == 200:
                upload_status = json.loads(response.text)
                if upload_status['status'] == 'Success':
                    st.success("File successfully uploaded and processed.")
                else:
                    st.error(
                        f"Error uploading file: {upload_status['message']}")
            else:
                st.error(
                    f"Failed to communicate with API. Status code: {response.status_code}")
        except json.JSONDecodeError:
            st.error("Server response is not valid JSON.")
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")

    # Chat interface
    user_input = st.text_input("Ask a Question:")
    if st.button('Submit Question'):
        response = requests.post(
            f"{api_url}/chat/", params={"query": user_input})
        if response.status_code == 200:
            try:
                chat_response = json.loads(response.text)
                st.write(f"Answer: {chat_response['response']}")
            except json.JSONDecodeError:
                st.error("Server response is not valid JSON.")
        else:
            st.error("Failed to get chat response")


if __name__ == "__main__":
    main()
