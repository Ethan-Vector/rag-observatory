from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from .config import EnvSettings, load_config
from .pipeline import RagPipeline
from .schemas import QueryRequest, QueryResponse


env = EnvSettings()
cfg = load_config(env.config_path)
pipeline = RagPipeline.from_config(cfg)

app = FastAPI(title="ethan-rag-observatory", version="0.1.0")


@app.get("/healthz")
async def healthz():
    return {"ok": True, "config_version": cfg.version_hash, "rag": cfg.config.rag}


@app.post("/v1/ingest")
async def ingest():
    stats = pipeline.ingest()
    return stats


@app.post("/v1/query", response_model=QueryResponse)
async def query(req: QueryRequest):
    out = pipeline.query(route=req.route, query=req.query, top_k=req.top_k)
    return QueryResponse(**out)


def main():
    import uvicorn

    uvicorn.run(
        "rag_observatory.api:app",
        host=os.getenv("APP_HOST", "0.0.0.0"),
        port=int(os.getenv("APP_PORT", "8090")),
        reload=False,
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
    )


if __name__ == "__main__":
    main()
