import logging
from typing import List, Optional, Tuple

import requests

logger = logging.getLogger(__name__)

# Content types by extension. Audio only works on the cloud backend of the API.
CONTENT_TYPES = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "txt": "text/plain",
    "md": "text/markdown",
    "mp3": "audio/mpeg",
    "m4a": "audio/mp4",
    "wav": "audio/wav",
}


def send_files_to_api(
    files: List[Tuple[str, Tuple[str, bytes, str]]], api_url: str, timeout: float = 300.0
) -> Optional[List[dict]]:
    """Send files to the API and return one result per file.

    Each result has ``filename``, ``status`` ("Success" or "Failed") and ``message``.
    Returns ``None`` when the request itself failed.
    """
    try:
        response = requests.post(f"{api_url}/multipleupload/", files=files, timeout=timeout)
        response.raise_for_status()
        return response.json().get("results", [])
    except requests.RequestException as error:
        logger.error("An error occurred while sending files to the API: %s", error)
        return None
