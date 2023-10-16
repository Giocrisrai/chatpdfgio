
# ChatPDFGio: Intelligent Chatbot with PDF Processing

[![Python Version](https://img.shields.io/badge/Python-3.9-green.svg)](https://www.python.org/)
[![Documentation](https://img.shields.io/badge/documentation-yes-green.svg)](https://github.com/Giocrisrai/chatpdfgio#readme)

## Overview

ChatPDFGio is an intelligent chatbot application that leverages machine learning for natural language processing and file handling capabilities for PDFs. It consists of a FastAPI backend for processing and a Streamlit frontend for user interaction.

## Architecture

- `api/`: Backend API built with FastAPI
- `streamlit_app/`: Frontend application built with Streamlit
- `Dockerfiles`: For containerizing the application

## Getting Started

### Prerequisites

- Python 3.9+
- Docker (Optional)

### Clone the Repository

```bash
git clone https://github.com/Giocrisrai/chatpdfgio.git
cd chatpdfgio
```

### Backend Setup

1. Navigate to `api/` directory
2. Install the dependencies:

    ```bash
    pip install -r requirements.txt
    ```

3. Run the FastAPI server:

    ```bash
    uvicorn main:app --reload
    ```

4. (Optional) To containerize the backend, check the README in `api/` directory.

### Frontend Setup

1. Navigate to `streamlit_app/` directory
2. Install the dependencies:

    ```bash
    pip install -r requirements.txt
    ```

3. Run the Streamlit app:

    ```bash
    streamlit run main.py
    ```

4. (Optional) To containerize the frontend, check the README in `streamlit_app/` directory.

## Environmental Variables

Both the frontend and backend use environmental variables for configuration. Check the respective README files in their directories for more details.

## Author

👤 **Giocrisrai Godoy**

- [Website](https://www.giocrisrai.com/)
- [GitHub](https://github.com/giocrisrai)
- [LinkedIn](https://www.linkedin.com/in/giocrisrai)

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.
