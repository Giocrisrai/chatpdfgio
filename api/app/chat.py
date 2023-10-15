import os
import openai
import pinecone
from dotenv import load_dotenv
from typing import List, Dict, Union, Tuple

# Load environment variables from the .env file
load_dotenv()

# Set up OpenAI API key
openai.api_key = os.environ.get('OPENAI_API_KEY')

# Limit text length for the prompt
limit = 3750

# Name of your Pinecone index
index_name = os.environ.get('YOUR_INDEX_NAME')

# Define OpenAI embedding model
embed_model = "text-embedding-ada-002"


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
    res = openai.Embedding.create(input=[text], engine=embed_model)
    vector = res['data'][0]['embedding']
    return vector


def search_in_pinecone(query_vector: List[float]) -> Dict[str, Union[str, List[Dict[str, Union[str, float]]]]]:
    """
    Search the Pinecone index using the given query vector.

    Parameters:
    query_vector (List[float]): The vector representation of the query.

    Returns:
    Dict: The search results from Pinecone.
    """
    if not index_name:
        raise ValueError("Index name is not set in environment variables")
    try:
        index = pinecone.Index(index_name)
        results = index.query(
            vector=query_vector,
            top_k=3,
            include_metadata=True
        )
    except Exception as e:
        print(f"Error: {e}")
        raise
    return results


def retrieve(query: str) -> str:
    """
    Retrieve relevant contexts based on the query, and construct a prompt.

    Parameters:
    query (str): The user's query.

    Returns:
    str: The constructed prompt.
    """
    # Vectorize the query
    xq = vectorize_text(query)
    # Get relevant contexts
    res = search_in_pinecone(xq)
    contexts = [x['metadata']['text'] if 'metadata' in x and 'text' in x['metadata']
                else '' for x in res['matches']]
    # Build the prompt with the retrieved contexts included
    prompt_start = "Answer the question based on the context below.\n\nContext:\n"
    prompt_end = f"\n\nQuestion: {query}\nAnswer:"
    # Add contexts until reaching the limit
    for i in range(1, len(contexts)):
        if len("\n\n---\n\n".join(contexts[:i])) >= limit:
            prompt = prompt_start + \
                "\n\n---\n\n".join(contexts[:i-1]) + prompt_end
            break
        elif i == len(contexts)-1:
            prompt = prompt_start + "\n\n---\n\n".join(contexts) + prompt_end
    return prompt


def complete(prompt: str) -> str:
    """
    Get a completion based on the prompt using OpenAI's text-davinci-003 model.

    Parameters:
    prompt (str): The constructed prompt.

    Returns:
    str: The generated answer.
    """
    # Make the query to text-davinci-003
    res = openai.Completion.create(
        engine='text-davinci-003',
        prompt=prompt,
        temperature=0,
        max_tokens=400,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None
    )
    return res['choices'][0]['text'].strip()


def process_user_query(user_query: str) -> str:
    """
    Process the user's query, retrieve relevant contexts, and get a completion.

    Parameters:
    user_query (str): The user's query.

    Returns:
    str: The generated answer.
    """
    if not user_query:
        raise ValueError("User query is empty")
    query_with_contexts = retrieve(user_query)
    answer = complete(query_with_contexts)
    return answer
