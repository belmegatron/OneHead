FROM python:3.13-slim-trixie

RUN apt update && apt upgrade -y && apt install ffmpeg -y

RUN apt install -y --no-install-recommends curl ca-certificates
ADD https://astral.sh/uv/install.sh /uv-installer.sh
RUN sh /uv-installer.sh && rm /uv-installer.sh
ENV PATH="/root/.local/bin/:$PATH"

WORKDIR /app
COPY onehead onehead/
COPY uv.lock pyproject.toml run.py .
RUN uv sync --frozen --no-dev

ENTRYPOINT uv run run.py
