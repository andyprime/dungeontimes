FROM python:3.12

WORKDIR /code

VOLUME /code

# for the moment we're voluming the whole repo so put the container specific file in /tmp
COPY containers/dev/dm/requirements.txt /tmp/requirements.txt

# strictly speaking this isn't needed yet since it will be inherited from the volume
#COPY $SETTINGS_FILE .env 

RUN pip install --no-cache-dir --upgrade -r /tmp/requirements.txt

CMD ["python", "demoloop.py"]