# API

FastAPI service that ingests documents and answers questions from their content.
Setup, configuration and the endpoint list are in the [main README](../README.md).

```bash
pip install -r requirements-dev.txt
uvicorn main:app --reload      # http://localhost:8000/docs
pytest tests -q
```
