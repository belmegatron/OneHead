FROM python

WORKDIR /usr/local/

ARG GIT_OAUTH_KEY

RUN git clone https://$GIT_OAUTH_KEY@github.com/belmegatron/OneHead.git

COPY .env ./OneHead/.env

RUN pip install virtualenv

ENV VIRTUAL_ENV=/opt/venv

RUN python -m venv $VIRTUAL_ENV

ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN pip install --upgrade pip setuptools wheel

WORKDIR /usr/local/OneHead

RUN python setup.py bdist_wheel

RUN python -m pip install dist/OneHead-1.14-py3-none-any.whl

ENTRYPOINT python run.py