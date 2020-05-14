FROM python

WORKDIR /usr/local/

RUN git clone --single-branch --branch feature/refactor-code https://$GIT_OAUTH_KEY@github.com/belmegatron/OneHead.git

COPY .env ./OneHead/.env

RUN pip install virtualenv

ENV VIRTUAL_ENV=/opt/venv

RUN python -m venv $VIRTUAL_ENV

ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN pip install --upgrade pip setuptools wheel

WORKDIR /usr/local/OneHead

RUN python setup.py bdist_wheel

RUN python -m pip install --no-index --find-links=dist/ OneHead

ENTRYPOINT python run.py