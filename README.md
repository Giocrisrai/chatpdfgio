# ChatPDFGio — Chatea con tus documentos PDF (RAG full-stack)

> **English summary.** End-to-end RAG application: upload one or more PDFs and chat with them in natural language. Documents are parsed and chunked, embedded with OpenAI and indexed in Pinecone; each question is answered by an LLM grounded on the retrieved chunks, not on the model's memory. FastAPI backend, Streamlit frontend, LangChain orchestration, Docker. The rest of this document is in Spanish.

Aplicación **RAG (Retrieval-Augmented Generation)** de extremo a extremo: sube uno o varios PDF y conversa con ellos en lenguaje natural. La respuesta se construye a partir del contenido real de tus documentos —con recuperación semántica sobre una base vectorial— no de la memoria del modelo.

[![Python](https://img.shields.io/badge/Python-3.9%2B-3670A0?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![LangChain](https://img.shields.io/badge/LangChain-1C3C3C?style=flat-square&logo=langchain&logoColor=white)](https://www.langchain.com/)
[![Pinecone](https://img.shields.io/badge/Pinecone-Vector%20DB-000000?style=flat-square)](https://www.pinecone.io/)
[![OpenAI](https://img.shields.io/badge/OpenAI-Embeddings%20%2B%20LLM-412991?style=flat-square&logo=openai&logoColor=white)](https://openai.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg?style=flat-square)](LICENSE.md)

**[▶ Demo en vivo](https://giocrisrai.github.io/chatpdfgio/)** — búsqueda semántica sobre un documento, corriendo entera en tu navegador: sin servidor y sin claves.

![Demo: se indexa un documento y una pregunta recupera los fragmentos más cercanos con su similitud](docs/demo.gif)

> La demo cubre la **mitad de recuperación** del pipeline RAG (fragmentación, embeddings con `all-MiniLM-L6-v2` y similitud coseno). La aplicación completa añade la generación con FastAPI, OpenAI y Pinecone, que necesita claves de pago y por eso no está alojada.

---

## Qué resuelve

Leer y consultar documentos largos (informes, contratos, papers, manuales) es lento. ChatPDFGio convierte cualquier PDF en una base de conocimiento consultable: haces las preguntas, obtienes respuestas **fundamentadas en el documento** y reduces las alucinaciones al anclar la generación en los fragmentos recuperados.

## Cómo funciona (pipeline RAG)

```
PDF  ─►  Extracción           ─►  Chunking        ─►  Embeddings        ─►  Índice vectorial
         (pypdf, unstructured)     (segmentación)      (OpenAI)              (Pinecone)
                                                                                  │
Pregunta del usuario  ─►  Embedding de la consulta  ─►  Búsqueda por similitud ◄──┘
                                                              │
                                                              ▼
                                          Contexto recuperado  ─►  LLM (OpenAI)  ─►  Respuesta fundamentada
```

1. **Ingesta:** el PDF se procesa con `pypdf` / `unstructured` y se divide en fragmentos manejables.
2. **Indexación:** cada fragmento se vectoriza con embeddings de OpenAI y se almacena en **Pinecone**.
3. **Recuperación:** la pregunta se vectoriza y se buscan los fragmentos más similares (búsqueda semántica).
4. **Generación:** el LLM responde usando *solo* el contexto recuperado, anclado en el material fuente.

## Arquitectura

| Capa | Tecnología | Rol |
|------|-----------|-----|
| **Frontend** | Streamlit | Carga de PDF y chat interactivo |
| **Backend** | FastAPI + Uvicorn | API de ingesta, embeddings y consulta |
| **Orquestación LLM** | LangChain | Pipeline RAG (loaders, splitters, chains) |
| **Base vectorial** | Pinecone | Almacenamiento y recuperación semántica |
| **Modelos** | OpenAI | Embeddings + generación |
| **Auth / datos** | Firebase | Gestión de usuarios y sesiones |
| **Despliegue** | Docker Compose | `fastapi_backend` + `streamlit_frontend` |

```
chatpdfgio/
├── api/                # Backend FastAPI (ingesta, embeddings, RAG)
├── streamlit_app/      # Frontend Streamlit (UI de chat)
├── docker-compose.yml  # Orquesta backend + frontend
└── .devcontainer/      # Entorno de desarrollo reproducible
```

## Características

- 📄 **Multi-PDF** — sube varios documentos y consúltalos en conjunto.
- 🔎 **Recuperación semántica** — respuestas ancladas al contenido real (menos alucinaciones).
- ⚡ **API REST** — backend FastAPI desacoplado, consumible desde cualquier cliente.
- 🐳 **Contenerizado** — `docker compose up` levanta todo el stack.
- 🔐 **Autenticación** — gestión de usuarios vía Firebase.

## Inicio rápido

### Con Docker (recomendado)

```bash
git clone https://github.com/Giocrisrai/chatpdfgio.git
cd chatpdfgio
# Configura las variables de entorno (OpenAI, Pinecone, Firebase) — ver READMEs en api/ y streamlit_app/
docker compose up --build
```

### Manual

**Backend**
```bash
cd api
pip install -r requirements.txt
uvicorn main:app --reload
```

**Frontend**
```bash
cd streamlit_app
pip install -r requirements.txt
streamlit run main.py
```

## Variables de entorno

El backend y el frontend se configuran por variables de entorno (claves de **OpenAI**, **Pinecone** y **Firebase**). Consulta los `README` de `api/` y `streamlit_app/` para el detalle. **Nunca** comitees tus claves.

## Autor

👤 **Giocrisrai Godoy Bonillo** — AI Engineer · LLM Security & Assurance

- 🌐 [giocrisrai.com](https://www.giocrisrai.com/)
- 💻 [github.com/Giocrisrai](https://github.com/Giocrisrai)
- 💼 [linkedin.com/in/giocrisrai](https://www.linkedin.com/in/giocrisrai)

> Proyecto de demostración de un pipeline RAG. Para auditoría de seguridad de aplicaciones y agentes LLM como este (OWASP Top 10 for LLM Applications), ver [**agent-assurance**](https://github.com/Giocrisrai/agent-assurance).

## Licencia

MIT — ver [LICENSE.md](LICENSE.md).

## Pruebas

La lógica RAG (historial de conversación, selección de contexto y construcción del prompt) tiene pruebas que corren sin red ni credenciales: los SDK de OpenAI y Pinecone se reemplazan por dobles.

```bash
pip install pytest
pytest api/tests -q
```
