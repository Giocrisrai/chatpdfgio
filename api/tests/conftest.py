"""Configuracion de pruebas.

Las pruebas cubren la logica RAG (historial, seleccion de contexto, prompt) sin
red ni credenciales: los SDK externos (OpenAI, Pinecone) se reemplazan por
dobles antes de importar la aplicacion.
"""

import sys
import types
from pathlib import Path
from unittest.mock import MagicMock

API_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(API_DIR))

# Dobles de los SDK externos: `app.chat` crea un cliente al importarse.
openai_stub = types.ModuleType("openai")
openai_stub.OpenAI = MagicMock(name="OpenAI")
sys.modules.setdefault("openai", openai_stub)
sys.modules.setdefault("pinecone", MagicMock(name="pinecone"))

dotenv_stub = types.ModuleType("dotenv")
dotenv_stub.load_dotenv = lambda *args, **kwargs: None
sys.modules.setdefault("dotenv", dotenv_stub)
sys.modules.setdefault("pytz", types.ModuleType("pytz"))
