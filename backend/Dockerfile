FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml .
COPY app ./app
COPY seed ./seed
COPY alembic ./alembic
COPY alembic.ini .
# Optional dependency groups from pyproject.toml, e.g. EXTRAS=azure for Azure Blob media storage.
ARG EXTRAS=""
RUN if [ -n "$EXTRAS" ]; then pip install --no-cache-dir ".[$EXTRAS]"; else pip install --no-cache-dir .; fi
EXPOSE 8000
# Local default. In production, deploy/compose.prod.yaml overrides this command to trust
# X-Forwarded-For from the nginx container and to run two workers.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-proxy-headers"]
