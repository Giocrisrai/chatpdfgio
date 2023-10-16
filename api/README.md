
# Welcome to chatpdfgio with Fastapi Backend IA 👋
[![Python](https://img.shields.io/badge/Python-3.9-green.svg)](https://github.com/Giocrisrai/chatpdfgio#readme)
[![Documentation](https://img.shields.io/badge/documentation-yes-green.svg)](https://github.com/Giocrisrai/chatpdfgio#readme)

> Backend Chat bot IA with OpenAI, AWS S3, and Pinecone integration.

## Table of Contents
1. [Installation](#installation)
2. [Usage](#usage)
3. [Environment Variables](#environment-variables)
4. [File Structure](#file-structure)
5. [Docker](#docker)
6. [Author](#author)

## Installation

### Create Virtual Environment

```bash
python -m venv venv
```

### Activate Environment

```bash
source venv/bin/activate
```
or
```
source venv/Scripts/activate
```

### Install Dependencies

```bash
pip install -r api/requirements.txt
```

## Usage

### Start the server

Navigate to the `api/` folder and run:

```bash
uvicorn main:app --reload
```

## Environment Variables

Create a `.env` file in the `api/` directory and add the following:

```env
OPENAI_API_KEY=
AWS_ACCESS_KEY=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=
YOUR_BUCKET_NAME=
PINECONE_API_KEY=
PINECONE_API_ENV=
YOUR_INDEX_NAME=
```

## File Structure

- `api/`
  - `requirements.txt`
  - `main.py`
  - `Dockerfile`
  - `app/`
    - `pdf_preprocessing.py`
    - `pinecone_ops.py`
    - `s3_operations.py`

## Docker

A `Dockerfile` is provided if you prefer to build a docker image. To build:

```bash
docker build -t your-image-name .
```

## Author

👤 **Giocrisrai Godoy**

- [Website](https://www.giocrisrai.com/)
- [Github](https://github.com/giocrisrai)
- [LinkedIn](https://www.linkedin.com/in/giocrisrai)
