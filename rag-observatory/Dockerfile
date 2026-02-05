FROM python:3.11-slim

WORKDIR /app
COPY pyproject.toml README.md INSTRUCTIONS.md /app/
COPY src /app/src
COPY evals /app/evals
COPY docs /app/docs
RUN pip install --no-cache-dir -e ".[dev]"

ENV RAGOBS_TRACE_DIR=/app/workspace/traces
CMD ["ragobs", "demo"]
