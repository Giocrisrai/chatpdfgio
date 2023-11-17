from openai import OpenAI
import os


def initialize_openai():
    """
    Initialize the OpenAI client.

    Returns:
    OpenAI: An OpenAI client object.
    """
    return OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
