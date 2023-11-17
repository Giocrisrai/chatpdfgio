from fastapi import FastAPI, File, UploadFile, HTTPException, Query, Body
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from app.s3_operations import upload_pdf, check_documents, initialize_s3_client, s3_object_exists, upload_file
from app.pdf_processing import process_pdf
from app.pinecone_ops import generate_and_store_embeddings
from app.chat import process_user_query, initialize_pinecone
from app.docx_processing import process_docx
from app.pptx_processing import process_pptx
from app.audio_processing import process_audio
from app.utils import initialize_openai
from typing import List, Dict, Union
import os
import uuid
import logging
import traceback


# Initialize Pinecone
initialize_pinecone()

client = initialize_openai()
if not client:
    logging.error("Failed to initialize OpenAI client.")

# Configure logging
logging.basicConfig(level=logging.INFO)

app = FastAPI()
# Configuración de CORS

origins = [

    "*"

]

app.add_middleware(

    CORSMiddleware,

    allow_origins=origins,

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],

)
# Fetch bucket name from environment variables
your_bucket_name = os.environ.get('YOUR_BUCKET_NAME')

# Initialize the S3 client once
s3 = initialize_s3_client()
if not s3:
    logging.error("Failed to initialize S3 client.")


@app.get("/", tags=["Root"])
def read_root() -> RedirectResponse:
    """Redirect to the API documentation."""
    return RedirectResponse(url="/docs/")


@app.get("/check-documents/", tags=["Documents"], response_description="Check if documents are loaded")
async def check_docs() -> Dict[str, Union[str, bool]]:
    """Check the current status of documents loaded in the system."""
    current_status = check_documents(your_bucket_name)
    return {"status": "Success", "message": "Documents loaded." if current_status else "No documents loaded."}


@app.post("/upload/", tags=["Documents"])
async def upload_pdf_route(file: UploadFile = File(..., description="A PDF file to be uploaded", example="example.pdf")) -> Dict[str, Union[str, bool]]:
    """
    Upload a single PDF file, process it, and store its embeddings.

    **Arguments**:
    - `file`: A PDF file to be uploaded.

    **Returns**:
    - A dictionary with the status, message, and filename.
    """
    logging.info("Starting upload process...")
    unique_filename = file.filename
    file_bytes = file.file.read()
    try:
        # Use upload_pdf function instead of s3.put_object directly
        upload_response = upload_pdf(file_bytes, unique_filename)
        if upload_response['status'] != "Success":
            return upload_response  # Return the error response directly if upload fails

        # Call process_pdf with all necessary arguments and capture the returned tuple
        data, temp_pdf_path = process_pdf(
            s3, your_bucket_name, unique_filename)

        # For debugging
        logging.info(f"Data type from process_pdf: {type(data)}, Data: {data}")
        logging.info(f"Temp PDF path: {temp_pdf_path}")

        # Call generate_and_store_embeddings instead of generate_embeddings and store_embeddings
        generate_and_store_embeddings(data, temp_pdf_path)

        return {
            "status": "Success",
            "message": "File uploaded, processed, and embeddings stored successfully",
            "filename": unique_filename
        }
    except Exception as e:
        # Added for debugging
        logging.error(f"Error type: {type(e)}, Error: {e}")
        return {"status": "Failed", "message": str(e)}


@app.post("/multipleupload/", tags=["Documents"])
async def multiple_upload_route(files: List[UploadFile] = File(..., description="A list of files to be uploaded", examples=[{"filename": "example1.pdf"}, {"filename": "example2.docx"}])) -> Dict[str, List[Dict[str, Union[str, bool]]]]:
    """
    Upload multiple files, process them, and store their embeddings.

    **Arguments**:
    - `files`: A list of files to be uploaded. The supported file types are PDF, DOCX, PPTX, MP3, M4A.

    **Returns**:
    - A dictionary with a list of result dictionaries, each containing the status, message, and filename.
    """
    results = []
    for file in files:
        unique_filename = file.filename
        file_bytes = file.file.read()
        file_extension = unique_filename.split(".")[-1].lower()

        try:
            # Upload the file to S3
            upload_response = upload_file(
                file_bytes, unique_filename)
            if upload_response['status'] != "Success":
                results.append({
                    "filename": unique_filename,
                    "status": "Failed",
                    "message": upload_response['message'],
                })
                continue  # Skip to the next file if the upload fails

            # Process the file depending on its extension
            if file_extension == "pdf":
                data, temp_path = process_pdf(
                    s3, your_bucket_name, unique_filename)
            elif file_extension == "docx":
                data, temp_path = process_docx(
                    s3, your_bucket_name, unique_filename)
            elif file_extension == "pptx":
                data, temp_path = process_pptx(
                    s3, your_bucket_name, unique_filename)
            elif file_extension in ["mp3", "m4a"]:
                # Assuming process_audio function exists and is imported
                data, temp_path = process_audio(
                    s3, your_bucket_name, unique_filename, client)
            else:
                raise HTTPException(
                    status_code=400, detail=f"Unsupported file type: {file_extension}")

            # Generate and store embeddings
            generate_and_store_embeddings(data, temp_path)

            results.append({
                "filename": unique_filename,
                "status": "Success",
                "message": "File uploaded, processed, and embeddings stored successfully",
            })
        except HTTPException as http_exception:
            raise http_exception
        except Exception as e:
            logging.error(f"Error processing file {unique_filename}: {e}")
            results.append({
                "filename": unique_filename,
                "status": "Failed",
                "message": str(e),
            })

    return {"results": results}


@app.post("/chat/", tags=["Chat"])
async def chat_endpoint(query: str = Query(..., description="The user's text query", examples="What is a PDF file?")) -> Dict[str, str]:
    """
    Handle a user's text query and return a response.

    **Arguments**:
    - `query`: A string containing the user's text query.

    **Returns**:
    - A dictionary with a response string.
    """
    try:
        response = process_user_query(query)
        return {"response": response}
    except Exception as e:
        print(traceback.format_exc())  # Print the full traceback
        raise HTTPException(status_code=500, detail=str(e))
