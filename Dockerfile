FROM python

WORKDIR /usr/local/

COPY onehead onehead/onehead

COPY config.json requirements.txt run.py setup.py version.py ./onehead/

RUN pip install virtualenv

ENV VIRTUAL_ENV=/opt/venv

RUN python -m venv $VIRTUAL_ENV

ENV PATH="$VIRTUAL_ENV/bin:$PATH"

WORKDIR /usr/local/onehead

RUN pip install -e .

ENTRYPOINT python run.py
