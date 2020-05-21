FROM python

WORKDIR /usr/local/

RUN git clone https://github.com/belmegatron/OneHead.git

COPY config.json ./OneHead/config.json

RUN pip install virtualenv

ENV VIRTUAL_ENV=/opt/venv

RUN python -m venv $VIRTUAL_ENV

ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN pip install --upgrade pip setuptools wheel

WORKDIR /usr/local/OneHead

RUN python setup.py bdist_wheel

RUN python -m pip install --find-links=dist/ OneHead

ENTRYPOINT python run.py