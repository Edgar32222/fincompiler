FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY fincompiler ./fincompiler
COPY apps ./apps
COPY demo ./demo
COPY .streamlit ./.streamlit
RUN pip install --no-cache-dir ".[web,excel]"

EXPOSE 8501
CMD ["fincompiler-web", "--server.address=0.0.0.0", "--server.port=8501"]
