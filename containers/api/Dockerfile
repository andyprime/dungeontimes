FROM python:3.12

WORKDIR /code

COPY containers/api/requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./api /code/api

CMD ["fastapi", "run", "api/main.py", "--port", "80"]