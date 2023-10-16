
# Streamlit Application for Intelligent Search with FastAPI Backend

![Python](https://img.shields.io/badge/Python-3.9-green.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.x-orange.svg)
![Documentation](https://img.shields.io/badge/documentation-yes-green.svg)

This is a frontend application built using Streamlit to interact with an Intelligent Search backend using FastAPI and OpenAI.

## Setup & Installation

### Pre-requisites
- Python 3.x
- Virtual Environment

### Steps

1. **Clone the Repository**

    ```sh
    git clone https://github.com/YourGithubUsername/YourRepoName.git
    cd YourRepoName/streamlit_app
    ```

2. **Create Virtual Environment**

    ```sh
    python -m venv venv
    ```

3. **Activate Virtual Environment**

    On Windows,
    ```sh
    .\venv\Scripts\activate
    ```
    On macOS/Linux,
    ```sh
    source venv/bin/activate
    ```

4. **Install Dependencies**

    ```sh
    pip install -r requirements.txt
    ```

5. **Run Streamlit App**

    ```sh
    streamlit run main.py
    ```

## Features

- File Upload: Upload PDF files that you want to search through.
- Intelligent Search: Ask natural language questions and get precise answers from the uploaded documents.
- Multilingual Support: Supports multiple languages for searching.

## File Structure

- `main.py`: The main Streamlit application.
- `app/`: Contains helper modules.
    - `file_upload.py`: Handles file uploads and processing.
    - `chat.py`: Manages the chat interactions.
    - `utils.py`: Utility functions.

## Author

👤 **Your Name**

- Website: [Your Personal Website](#)
- LinkedIn: [Your LinkedIn](https://www.linkedin.com/in/your-linkedin/)
- Github: [@YourGithubUsername](https://github.com/YourGithubUsername)

