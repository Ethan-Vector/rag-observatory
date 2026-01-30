# ethan-rag-observatory

RAG “operato” come knowledge layer: ingest → chunk → embed → index → retrieve → rerank → answer (con **evidence contract**) + **trace bundle** riproducibile.

Questo repo è pensato per il libro: non è un “chatbot demo”, è una base per **debug** e **regression testing** di un sistema RAG.

## Caratteristiche chiave

- **Vector store locale (SQLite)** con embedding deterministico (hashing) → zero dipendenze ML
- Retrieval + rerank lessicale (baseline robusta e comprensibile)
- **Evidence contract**: l’output include sempre `citations[]` (chunk ids) + `trace_id`
- **Trace bundle**: ogni query salva un JSON in `./traces/` con snapshot, scores, top-k, config hash
- **RAG regression tests**: golden set in `data/golden.jsonl`

> Nota: la generazione della “answer” qui è volutamente semplice e grounded: usa solo i chunk recuperati. Puoi sostituirla con un LLM quando vuoi; l’osservabilità rimane.

---

## Quickstart

### 1) Setup
```bash
cp .env.example .env
cp configs/rag.example.yaml configs/rag.yaml

python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 2) Ingest corpus demo
```bash
ragobs ingest --config configs/rag.yaml
```

### 3) Query (CLI)
```bash
ragobs query --config configs/rag.yaml --route default --q "How do I reset my password?"
```

### 4) Run API
```bash
make dev
# http://localhost:8090/healthz
```

Esempio request:
```bash
curl -s http://localhost:8090/v1/query \
  -H 'content-type: application/json' \
  -d '{"route":"default","query":"How do I reset my password?","top_k":5}' | jq
```

---

## Evidence contract (output)

Risposta tipica:
- `answer`: testo grounded (solo evidence)
- `citations`: lista di chunk IDs (es. `doc:passwords.md#chunk:2`)
- `trace_id`: id del bundle salvato in `./traces/<trace_id>.json`

---

## Regression evals

Golden file: `data/golden.jsonl` (1 riga = 1 caso).
```bash
ragobs eval --config configs/rag.yaml --golden data/golden.jsonl
```

Metriche:
- recall@k (citazioni attese nei top-k)
- hit@k
- “no-answer” rate (se confidence < threshold)

---

## Struttura

- `src/rag_observatory/` core library + FastAPI
- `data/corpus/` corpus demo
- `data/golden.jsonl` golden set
- `traces/` trace bundles (auto-creati)

---

## License
MIT
