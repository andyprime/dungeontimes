FROM python:3.12

WORKDIR /code

COPY ./core /code/core
COPY ./definitions /code/definitions
COPY ./strings /code/strings
COPY ./demoloop.py /code

COPY containers/deploy/dm/requirements.txt /tmp/requirements.txt

COPY $SETTINGS_FILE .env 

RUN pip install --no-cache-dir --upgrade -r /tmp/requirements.txt

CMD ["python", "demoloop.py"]