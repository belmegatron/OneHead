FROM python

RUN apt update && apt upgrade -y && apt install ffmpeg -y

WORKDIR /app

COPY onehead onehead/
COPY pyproject.toml .
COPY run.py .

RUN pip install virtualenv
ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN pip install .

ENTRYPOINT python run.py
