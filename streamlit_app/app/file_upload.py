import requests
import logging
from typing import List, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def send_files_to_api(files: List[Tuple[str, bytes, str]], api_url: str) -> int:
    """
    Sends files to the API for processing.

    Parameters:
    - files : List[Tuple[str, bytes, str]]
        List of files to be sent to the API.
    - api_url : str
        The URL of the API to which the files will be sent.

    Returns:
    - int
        HTTP status code received from the API.
    """
    try:
        response = requests.post(f"{api_url}/multipleupload/", files=files)
        response.raise_for_status()  # Raise HTTPError for bad responses
        logger.info(
            f"Successfully sent files to {api_url}. Status code: {response.status_code}")
        return response.status_code
    except requests.RequestException as e:
        # Handle exceptions related to the HTTP request
        logger.error(f"An error occurred while sending files to API: {e}")
        return None  # or you could re-raise the exception: raise e
