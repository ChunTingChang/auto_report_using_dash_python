FROM python:3.9.7

WORKDIR /code

COPY ./requirements.txt /code
RUN pip install -r requirements.txt

COPY ./app.py /code/app.py
COPY ./assets /code/assets
COPY ./resources /code/resources

CMD ["sh", "-c", "python /code/app.py"]