import os
import openai
import pinecone
from dotenv import load_dotenv
from typing import List, Dict, Union, Tuple
from collections import defaultdict, namedtuple
import datetime
import pytz

from app.utils import initialize_openai
# Load environment variables from the .env file
load_dotenv()

# Set up OpenAI API key
client = initialize_openai()

# Max number of tokens allowed by OpenAI and "text-davinci-003"
MAX_TOKENS = 8000
MAX_RESPONSE_TOKENS = 800
MAX_QUERY_TOKENS = MAX_TOKENS - MAX_RESPONSE_TOKENS
MAX_CONTEXT_TOKENS = int(0.3 * MAX_QUERY_TOKENS)
MAX_HISTORY_TOKENS = int(0.6 * MAX_QUERY_TOKENS)

# Max character length for prompt
CHARACTERS_PER_TOKEN = 4
MAX_CONTEXT_LENGTH = MAX_CONTEXT_TOKENS * CHARACTERS_PER_TOKEN
MAX_HISTORY_LENGTH = MAX_HISTORY_TOKENS * CHARACTERS_PER_TOKEN

# Name of your Pinecone index
index_name = os.environ.get('YOUR_INDEX_NAME')

# Define OpenAI embedding model
embed_model = "text-embedding-ada-002"

# Define OpenAI completion model
completion_model = "gpt-4-1106-preview"


def initialize_pinecone() -> None:
    """
    Initialize Pinecone with API key and environment variables from .env file.
    """
    pinecone_api_key = os.environ.get('PINECONE_API_KEY')
    pinecone_env = os.environ.get('PINECONE_API_ENV')
    pinecone.init(
        api_key=pinecone_api_key,
        environment=pinecone_env
    )


def vectorize_text(text: str) -> List[float]:
    """
    Vectorize the given text using OpenAI's embedding model.

    Parameters:
    text (str): The text to be vectorized.

    Returns:
    List[float]: The vector representation of the text.
    """
    text = text.replace("\n", " ")

    res = client.embeddings.create(
        input=[text], model=embed_model).data[0].embedding
    return res


def search_in_pinecone(query_vector: List[float], index_name: str) -> Dict[str, Union[str, List[Dict[str, Union[str, float]]]]]:
    """
    Search the Pinecone index using the given query vector.

    Parameters:
    query_vector (List[float]): The vector representation of the query.

    Returns:
    Dict: The search results from Pinecone.
    """
    try:
        index = pinecone.Index(index_name)
        results = index.query(
            vector=query_vector,
            top_k=6,
            include_metadata=True
        )
    except Exception as e:
        print(f"Error: {e}")
        raise
    return results


def get_conversation_log(history_buffer: List[Dict[str, str]], index_name: str) -> str:
    ''' Get the conversation log from the history buffer such that the length of the conversation log is <= MAX_HISTORY_LENGTH.'''

    conversation_log = ""
    for message in history_buffer[::-1]:
        conversation_log_temp = f"{message['role']}: {message['content']}\n" + \
            conversation_log
        if len(conversation_log_temp) > MAX_HISTORY_LENGTH:
            break
        conversation_log = conversation_log_temp
    return conversation_log.strip()


def query_refiner(query: str, conversation_log: str) -> Tuple[str, Dict[str, int]]:
    ''' Refine the user query based on the conversation log. '''

    prompt = "Given the following user query and conversation log, formulate a question that would be the most relevant to provide the user with " \
        + f"an answer from a knowledge base.\n\nCONVERSATION LOG:\n{conversation_log}\n\nQUERY:{query}\n\nREFINED QUERY:"

    system_prompt = "You are a knowledge management assistant, respond in a polite and direct manner, and always respond in the language of the QUERY"
    response = client.chat.completions.create(
        model=completion_model,
        messages=[{"role": "system", "content": system_prompt},
                  {"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=MAX_RESPONSE_TOKENS,
        frequency_penalty=0.2,
        presence_penalty=0
    )
    return response.choices[0].message.content, response.usage


def retrieve_context(query: str) -> Tuple[str, List[Dict[str, str]]]:
    '''
    Retrieve the most relevant context based on the query in adition
    to the filename of the source documents
    '''

    query_vector = vectorize_text(query)
    res = search_in_pinecone(query_vector, index_name)

    # Save the contexts
    contexts = []
    for x in res['matches']:
        if 'metadata' in x and 'text' in x['metadata']:
            contexts.append(x['metadata']['text'])

    # Save the reference of the contexts
    sources = set([])
    for x in res['matches']:
        if 'metadata' in x and 'source' in x['metadata']:
            sources.add(x['metadata']['source'])
    reference = [{'source': source} for source in sources]

    # Add context until reaching MAX_CONTEXT_LENGTH
    context = ''
    for i in range(1, len(contexts)):
        if len("\n\n---\n\n".join(contexts[:i])) > MAX_CONTEXT_LENGTH:
            context = "\n\n---\n\n".join(contexts[:i-1])
            break
        elif i == len(contexts)-1:
            context = "\n\n---\n\n".join(contexts)

    return context, reference


def get_completion(query: str, context: str, conversation_log: str) -> str:
    ''' Get a completion based on the query, context, and conversation log. '''

    prompt = ("Please provide an answer based solely on the available context and conversation history. "
              "Do not include information beyond what is provided in the context. "
              "If the context or conversation log does not contain the necessary information for a response, "
              "kindly state that you don't have the answer.\n\n"
              "CONTEXT:\n"
              f"{context}\n\n"
              "CONVERSATION LOG:\n"
              f"{conversation_log}\n\n"
              f"QUERY: {query}\n\n"
              "ANSWER:")

    system_prompt = "You are a knowledge management assistant, respond in a polite and detailed manner, and always respond in spanish"

    response = client.chat.completions.create(
        model=completion_model,
        messages=[{"role": "system", "content": system_prompt},
                  {"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=MAX_RESPONSE_TOKENS,
        frequency_penalty=0.6,
        presence_penalty=0
    )

    return response.choices[0].message.content


def process_user_query(user_query: str) -> Tuple[str, List[Dict[str, str]]]:
    """
    Process the user's query and return a response.

    Parameters:
        user_query (str): The user's query.

    Returns:
        Tuple[str, List[Dict[str, str]]]: The generated answer and an empty reference list.
    """

    # Define el nombre de tu índice Pinecone y las variables de entorno
    index_name = os.environ.get('YOUR_INDEX_NAME')
    pinecone_api_key_token = os.environ.get('PINECONE_API_KEY')
    pinecone_api_env_token = os.environ.get('PINECONE_API_ENV')
    user_rut = os.environ.get('USER_RUT')
    s3_bucket_name = os.environ.get('S3_BUCKET_NAME')

    # Inicializa Pinecone
    initialize_pinecone()

    if not user_query:
        raise ValueError("User query is empty")

    # Obtiene el contexto y la respuesta basada en la consulta del usuario
    context, reference = retrieve_context(user_query)
    answer = get_completion(user_query, context, "")

    # Crea una lista de referencia vacía
    reference = []

    if not answer:
        answer = ''

    return answer
