# Production Deployment Guide

This document describes how to deploy the SHL Conversational Assessment Recommender platform in a production environment.

## Architecture Summary
- **Backend**: FastAPI web service using hybrid BM25 and FAISS search with LLM reranking. Packaged as a Docker container. Deployed on **Railway**.
- **Frontend**: Single Page React Application built with Vite and Tailwind CSS. Deployed on **Vercel**.

---

## 1. Backend Deployment (Railway)

The backend is configured with production-ready settings in [Dockerfile](file:///c:/Users/roysa/OneDrive/Desktop/shl-assessment-recommender/Dockerfile) and [railway.json](file:///c:/Users/roysa/OneDrive/Desktop/shl-assessment-recommender/railway.json).

### Steps to Deploy:
1. Sign in to your [Railway Account](https://railway.app/).
2. Create a **New Project** and select **Deploy from GitHub repo**.
3. Choose the repository for the SHL Assessment Recommender.
4. Railway will automatically detect the root `Dockerfile` and configure a Docker builder.
5. In the service settings, configure the **Environment Variables** (see below).
6. Under **Settings**, ensure that:
   - Port is set to `8000`.
   - Healthcheck Path is set to `/health`.
7. Once variables are set, deploy the service. Railway will output a public URL (e.g. `https://your-backend.railway.app`).

### Required Environment Variables:
| Variable Name | Description | Example / Recommended Value |
| :--- | :--- | :--- |
| `PORT` | Container binding port | `8000` |
| `HOST` | Container binding host | `0.0.0.0` |
| `LOG_LEVEL` | Production loguru logging level | `INFO` |
| `CORS_ORIGINS` | Permitted frontend origins (comma-separated) | `https://your-frontend.vercel.app` |
| `OPENROUTER_API_KEY` | OpenRouter access token | `sk-or-v1-...` |
| `OPENROUTER_MODEL` | DeepSeek LLM for reranking | `deepseek/deepseek-v4-flash` |
| `EMBEDDING_MODEL_NAME` | SentenceTransformer model | `all-MiniLM-L6-v2` |
| `CATALOG_PATH` | Path to Markdown catalog | `data/shl_assessment_catalog.md` |
| `FAISS_INDEX_PATH` | Path to FAISS search index file | `indexes/faiss.index` |
| `BM25_INDEX_PATH` | Path to BM25 search index file | `indexes/bm25.pkl` |

---

## 2. Frontend Deployment (Vercel)

The React frontend is deployed as a static site built on Vite.

### Steps to Deploy:
1. Sign in to your [Vercel Account](https://vercel.com/).
2. Import the project repository.
3. Set the **Root Directory** configuration to `frontend`.
4. Configure the **Build Settings**:
   - **Framework Preset**: `Vite` (automatically detected).
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
5. Configure the **Environment Variables**:
   - `VITE_API_URL`: Set this to the public URL of your deployed Railway backend (e.g. `https://your-backend.railway.app`).
6. Click **Deploy**. Vercel will build the frontend assets and provision a public URL.

---

## 3. Verification & Health Checks

Once both services are deployed, perform these validation steps:

### Backend Health Check:
Send a `GET` request to your backend's `/health` endpoint:
```bash
curl -i https://your-backend.railway.app/health
```
**Expected Response (HTTP 200):**
```json
{
  "status": "ok"
}
```

### Backend Chat Endpoint check:
Verify dialogue turns and catalog recommendations:
```bash
curl -i -X POST https://your-backend.railway.app/chat \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "I want an entry-level test for a Python dev."}]}'
```
**Expected Response:**
- Returns `reply` containing a job-level clarification question or recommended tests.
- Contains valid SHL catalog URLs under `recommendations`.
- Sets `end_of_conversation` to `false` (during clarification) or `true` (when recommendations are presented).

---

## 4. Troubleshooting

### 1. Backend container startup failure:
- **Symptom**: Railway log prints "Lifespan startup failure during model preloading" or "Index build failed".
- **Reason**: The SentenceTransformer model could not download due to network issues, or indices could not be written to disk.
- **Solution**: Ensure Railway has outbound internet access enabled. Verify directories `indexes` and `data` exist and have write permissions.

### 2. CORS Issues:
- **Symptom**: Frontend console shows CORS errors when calling `/chat`.
- **Solution**: Check that the `CORS_ORIGINS` environment variable on Railway includes the exact URL of the Vercel frontend (without trailing slash).

### 3. API key errors:
- **Symptom**: Chat calls fail with 500 status code.
- **Solution**: Check backend logs. If `OPENROUTER_API_KEY` is invalid or expired, the LLM provider will fail. Verify it is set correctly in Railway settings.
