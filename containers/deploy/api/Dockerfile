FROM python:3.12

WORKDIR /code

COPY containers/deploy/api/requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./api /code/api

COPY $SETTINGS_FILE .env 

CMD ["fastapi", "run", "api/main.py", "--port", "80"]