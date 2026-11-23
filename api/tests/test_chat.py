"""Pruebas de la logica RAG de `app.chat` (sin red ni credenciales)."""

from unittest.mock import MagicMock

import pytest

from app import chat

SEPARADOR = "\n\n---\n\n"


def _coincidencia(texto=None, fuente=None):
    """Construye una coincidencia de Pinecone con metadatos opcionales."""
    metadata = {}
    if texto is not None:
        metadata["text"] = texto
    if fuente is not None:
        metadata["source"] = fuente
    return {"metadata": metadata}


@pytest.fixture
def pinecone_falso(monkeypatch):
    """Reemplaza embeddings y busqueda; devuelve un setter de coincidencias."""
    estado = {"matches": []}
    monkeypatch.setattr(chat, "vectorize_text", lambda texto: [0.0, 1.0])
    monkeypatch.setattr(
        chat, "search_in_pinecone", lambda vector, indice: {"matches": estado["matches"]}
    )
    return lambda matches: estado.update(matches=matches)


class TestHistorial:
    def test_conserva_el_orden_cronologico(self):
        historial = [
            {"role": "user", "content": "hola"},
            {"role": "assistant", "content": "buenas"},
        ]
        assert chat.get_conversation_log(historial, "idx") == "user: hola\nassistant: buenas"

    def test_historial_vacio(self):
        assert chat.get_conversation_log([], "idx") == ""

    def test_al_truncar_conserva_los_mensajes_mas_recientes(self, monkeypatch):
        monkeypatch.setattr(chat, "MAX_HISTORY_LENGTH", 30)
        historial = [
            {"role": "user", "content": "mensaje antiguo muy largo"},
            {"role": "user", "content": "reciente"},
        ]
        registro = chat.get_conversation_log(historial, "idx")
        assert registro == "user: reciente"
        assert len(registro) <= 30


class TestContexto:
    def test_una_sola_coincidencia_se_usa_como_contexto(self, pinecone_falso):
        # Regresion: con un unico fragmento el contexto quedaba vacio.
        pinecone_falso([_coincidencia("unico fragmento", "a.pdf")])
        contexto, referencias = chat.retrieve_context("pregunta")
        assert contexto == "unico fragmento"
        assert referencias == [{"source": "a.pdf"}]

    def test_une_los_fragmentos_con_separador(self, pinecone_falso):
        pinecone_falso([_coincidencia("uno", "a.pdf"), _coincidencia("dos", "b.pdf")])
        contexto, _ = chat.retrieve_context("pregunta")
        assert contexto == f"uno{SEPARADOR}dos"

    def test_respeta_el_largo_maximo(self, pinecone_falso, monkeypatch):
        monkeypatch.setattr(chat, "MAX_CONTEXT_LENGTH", 12)
        pinecone_falso([_coincidencia("a" * 10), _coincidencia("b" * 10), _coincidencia("c")])
        contexto, _ = chat.retrieve_context("pregunta")
        assert contexto == "a" * 10
        assert len(contexto) <= 12

    def test_sin_coincidencias_devuelve_contexto_vacio(self, pinecone_falso):
        pinecone_falso([])
        assert chat.retrieve_context("pregunta") == ("", [])

    def test_fuentes_sin_duplicados_e_ignora_coincidencias_sin_texto(self, pinecone_falso):
        pinecone_falso(
            [
                _coincidencia("uno", "a.pdf"),
                _coincidencia("dos", "a.pdf"),
                _coincidencia(None, None),
            ]
        )
        contexto, referencias = chat.retrieve_context("pregunta")
        assert contexto == f"uno{SEPARADOR}dos"
        assert referencias == [{"source": "a.pdf"}]


class TestGeneracion:
    def test_el_prompt_ancla_la_respuesta_en_el_contexto(self, monkeypatch):
        cliente = MagicMock()
        cliente.chat.completions.create.return_value.choices = [
            MagicMock(message=MagicMock(content="respuesta"))
        ]
        monkeypatch.setattr(chat, "client", cliente)

        respuesta = chat.get_completion("que dice?", "CONTEXTO-X", "user: hola")

        assert respuesta == "respuesta"
        argumentos = cliente.chat.completions.create.call_args.kwargs
        prompt = argumentos["messages"][1]["content"]
        assert "CONTEXTO-X" in prompt
        assert "user: hola" in prompt
        assert "QUERY: que dice?" in prompt
        assert "based solely on the available context" in prompt
        assert argumentos["temperature"] == 0

    def test_consulta_vacia_se_rechaza(self, monkeypatch):
        monkeypatch.setattr(chat, "initialize_pinecone", lambda: None)
        with pytest.raises(ValueError):
            chat.process_user_query("")
