FROM python:3.13.17-slim

WORKDIR /fts

# Dependencies are installed before the application source so edits to
# the app do not rebuild the package layer.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && useradd --create-home --uid 1000 appuser

COPY . .

# The process writes the local database and exports under /fts/data.
# Secrets are not copied into the image; pass them at runtime:
#   docker run --env-file .env -p 8501:8501 <image>
RUN mkdir -p /fts/data \
    && chown -R appuser:appuser /fts

USER appuser

EXPOSE 8501

CMD ["streamlit", "run", "./fTrees.py", "--server.address=0.0.0.0", "--server.port=8501"]
