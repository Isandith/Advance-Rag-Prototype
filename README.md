---
title: Advance Rag Prototype
emoji: 🔎
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
---

# Advance RAG Prototype

FastAPI backend for a RAG-based chat system using MongoDB Atlas and Google Gemini.

## Running locally

```bash
docker build -t advance-rag-prototype .
docker run -p 7860:7860 --env-file .env advance-rag-prototype
```

## Required environment variables

Set these as secrets in the Space settings (Settings -> Variables and secrets):

- `GEMINI_API_KEY`
- `GEMINI_MODEL`
- `GEMINI_EMBEDDING_MODEL`
- `MONGODB_URI`
- `DB_NAME`
